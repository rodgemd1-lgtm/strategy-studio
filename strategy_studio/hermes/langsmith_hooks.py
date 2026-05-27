"""
RIG Lattice — LangSmith Observability Hooks
Traces every cell invocation, checkpoints LangGraph state, and tracks per-cell cost.
Wired to: LangSmith client (when available), Phronema Build Cards, and BMS scoring.
"""
from __future__ import annotations
import os
import json
import hashlib
import time
from datetime import datetime, timezone
from functools import wraps
from typing import Optional, Any, Callable
from pathlib import Path

# Optional LangSmith import — graceful degrade if unavailable
LANGSMITH_AVAILABLE = False
try:
    from langsmith import Client as LangSmithClient
    from langsmith.run_trees import RunTree
    LANGSMITH_AVAILABLE = True
except ImportError:
    LangSmithClient = None
    RunTree = None


# ─────────────────────────────────────────────
# Cost tracking constants
# ─────────────────────────────────────────────

COST_PER_1K_TOKENS = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "claude-sonnet-4": {"input": 0.003, "output": 0.015},
    "claude-haiku-3": {"input": 0.00025, "output": 0.00125},
    "default": {"input": 0.005, "output": 0.015},
}


# ─────────────────────────────────────────────
# State checkpoint helpers
# ─────────────────────────────────────────────

class CheckpointStore:
    """File-based checkpoint store for LangGraph resume."""

    def __init__(self, base_dir: str | Path | None = None):
        self.base_dir = Path(base_dir or os.path.join(Path(__file__).parent.parent.parent, "logs", "checkpoints"))
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, checkpoint_id: str) -> Path:
        return self.base_dir / f"{checkpoint_id}.json"

    def write(self, checkpoint_id: str, graph_state: dict, metadata: dict | None = None) -> Path:
        """Serialize graph_state to disk for LangGraph resume."""
        payload = {
            "checkpoint_id": checkpoint_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state": graph_state,
            "metadata": metadata or {},
        }
        path = self._path(checkpoint_id)
        with open(path, "w") as f:
            json.dump(payload, f, indent=2, default=str)
        return path

    def read(self, checkpoint_id: str) -> dict:
        """Deserialize graph_state from disk."""
        path = self._path(checkpoint_id)
        with open(path, "r") as f:
            return json.load(f)

    def list_checkpoints(self, prefix: str = "") -> list[str]:
        """List checkpoint IDs matching prefix."""
        return sorted(
            [p.stem for p in self.base_dir.glob(f"{prefix}*.json")]
        )


# ─────────────────────────────────────────────
# Tracer core
# ─────────────────────────────────────────────

class LangSmithTracer:
    """Lightweight trace logger for RIG Lattice cell invocations."""

    def __init__(self, project_name: str = "rig-lattice", log_dir: str | None = None):
        self.project_name = project_name
        self.log_dir = Path(log_dir or os.path.join(Path(__file__).parent.parent.parent, "logs", "langsmith"))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.traces: list[dict] = []
        self.checkpoint_store = CheckpointStore()
        self._langsmith_client: Any = None
        if LANGSMITH_AVAILABLE and LangSmithClient:
            self._langsmith_client = LangSmithClient()

    # ── Decorator ──

    def trace_cell_invocation(self, cell: str, payload: dict | None = None) -> Callable:
        """Decorator that traces a cell invocation, its payload, result, cost, and timing.

        Usage:
            @tracer.trace_cell_invocation(cell="L1-D1-A1", payload={"model": "gpt-4o"})
            def my_cell_fn(x):
                return x * 2
        """
        def decorator(fn: Callable) -> Callable:
            @wraps(fn)
            def wrapper(*args, **kwargs):
                start = time.perf_counter()
                execution_id = kwargs.get("execution_id") or hashlib.sha256(
                    f"{cell}:{time.time()}".encode()
                ).hexdigest()[:16]

                # Estimate cost before run
                model = (payload or {}).get("model", "default")
                estimated_input_tokens = (payload or {}).get("input_tokens", 0)
                estimated_output_tokens = (payload or {}).get("output_tokens", 0)
                cost_before = self._estimate_cost(model, estimated_input_tokens, estimated_output_tokens)

                # Execute
                result = None
                status = "completed"
                error = None
                try:
                    result = fn(*args, **kwargs)
                except Exception as e:
                    status = "failed"
                    error = str(e)
                    raise
                finally:
                    duration_ms = int((time.perf_counter() - start) * 1000)

                    # Re-estimate from actual result if it carries token metadata
                    actual_tokens = self._extract_tokens(result)
                    cost_usd = self._estimate_cost(
                        model,
                        actual_tokens.get("input_tokens", estimated_input_tokens),
                        actual_tokens.get("output_tokens", estimated_output_tokens),
                    )

                    trace = self.trace_cell(
                        execution_id=execution_id,
                        cell_id=cell,
                        altitude=(payload or {}).get("altitude", "L1"),
                        diamond=(payload or {}).get("diamond", "D1"),
                        step=(payload or {}).get("step", "I1"),
                        bms_score=(payload or {}).get("bms_score", 0.0),
                        bms_mode=(payload or {}).get("bms_mode", "UNKNOWN"),
                        archetype=(payload or {}).get("archetype", "A1.1"),
                        status=status,
                        cost_usd=cost_usd,
                        duration_ms=duration_ms,
                        escalated=(payload or {}).get("escalated", False),
                        input_payload=payload,
                        result_summary=self._summarize_result(result),
                        error=error,
                    )

                    # If LangSmith client is live, push the run tree
                    if self._langsmith_client and RunTree:
                        try:
                            run_tree = RunTree(
                                name=f"cell-{cell}",
                                run_type="chain",
                                inputs={"payload": payload, "args": str(args), "kwargs": str(kwargs)},
                                outputs={"result": self._summarize_result(result)},
                                extra={"cost_usd": cost_usd, "duration_ms": duration_ms},
                            )
                            run_tree.post()
                        except Exception:
                            pass  # degrade gracefully
                return result
            return wrapper
        return decorator

    # ── Low-level trace entry ──

    def trace_cell(self, execution_id: str, cell_id: str, altitude: str, diamond: str, step: str,
                   bms_score: float, bms_mode: str, archetype: str, status: str,
                   cost_usd: float, duration_ms: int, escalated: bool = False,
                   input_payload: dict | None = None,
                   result_summary: str | None = None,
                   error: str | None = None) -> dict:
        trace = {
            "trace_id": hashlib.sha256(f"{execution_id}:{cell_id}".encode()).hexdigest()[:16],
            "execution_id": execution_id,
            "project": self.project_name,
            "cell_id": cell_id,
            "altitude": altitude,
            "diamond": diamond,
            "step": step,
            "bms_score": bms_score,
            "bms_mode": bms_mode,
            "archetype": archetype,
            "status": status,
            "cost_usd": round(cost_usd, 6),
            "duration_ms": duration_ms,
            "escalated": escalated,
            "input_payload": input_payload or {},
            "result_summary": result_summary,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.traces.append(trace)
        return trace

    def trace_escalation(self, execution_id: str, from_cell: str, to_cell: str, reason: str) -> dict:
        trace = {
            "trace_id": hashlib.sha256(f"esc:{execution_id}:{from_cell}".encode()).hexdigest()[:16],
            "execution_id": execution_id,
            "project": self.project_name,
            "event": "escalation",
            "from_cell": from_cell,
            "to_cell": to_cell,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.traces.append(trace)
        return trace

    # ── Checkpointing ──

    def checkpoint_state(self, checkpoint_id: str, graph_state: dict, metadata: dict | None = None) -> Path:
        """Serialize graph state for LangGraph resume. Returns the written path."""
        return self.checkpoint_store.write(checkpoint_id, graph_state, metadata)

    def resume_state(self, checkpoint_id: str) -> dict:
        """Read graph state back for LangGraph resume."""
        return self.checkpoint_store.read(checkpoint_id)

    # ── Cost helpers ──

    @staticmethod
    def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        rates = COST_PER_1K_TOKENS.get(model, COST_PER_1K_TOKENS["default"])
        return (input_tokens / 1000.0) * rates["input"] + (output_tokens / 1000.0) * rates["output"]

    @staticmethod
    def _extract_tokens(result: Any) -> dict:
        """Try to read token usage from a result object/dict."""
        if isinstance(result, dict):
            return {
                "input_tokens": result.get("input_tokens", 0) or result.get("usage", {}).get("input_tokens", 0),
                "output_tokens": result.get("output_tokens", 0) or result.get("usage", {}).get("output_tokens", 0),
            }
        return {"input_tokens": 0, "output_tokens": 0}

    @staticmethod
    def _summarize_result(result: Any, max_len: int = 500) -> str:
        """Serialize a result snippet for trace storage."""
        try:
            text = json.dumps(result, default=str)
        except Exception:
            text = str(result)
        return text[:max_len] + ("..." if len(text) > max_len else "")

    # ── Persistence ──

    def flush(self) -> str:
        if not self.traces:
            return ""
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_path = self.log_dir / f"traces_{ts}.jsonl"
        with open(out_path, "w") as f:
            for t in self.traces:
                f.write(json.dumps(t) + "\n")
        count = len(self.traces)
        self.traces.clear()
        return str(out_path)

    def summary(self) -> dict:
        total = len(self.traces)
        escalated = sum(1 for t in self.traces if t.get("escalated"))
        total_cost = sum(t.get("cost_usd", 0.0) for t in self.traces)
        by_mode: dict[str, int] = {}
        for t in self.traces:
            mode = t.get("bms_mode", "UNKNOWN")
            by_mode[mode] = by_mode.get(mode, 0) + 1
        return {
            "total_traces": total,
            "escalated": escalated,
            "total_cost_usd": round(total_cost, 6),
            "by_mode": by_mode,
        }


# ─── Global tracer instance ───

_tracer = LangSmithTracer()


def get_tracer() -> LangSmithTracer:
    return _tracer


def trace_cell(*args, **kwargs) -> dict:
    return _tracer.trace_cell(*args, **kwargs)


def trace_escalation(*args, **kwargs) -> dict:
    return _tracer.trace_escalation(*args, **kwargs)


def checkpoint_state(checkpoint_id: str, graph_state: dict, metadata: dict | None = None) -> Path:
    return _tracer.checkpoint_state(checkpoint_id, graph_state, metadata)


def resume_state(checkpoint_id: str) -> dict:
    return _tracer.resume_state(checkpoint_id)


# ─── CLI ───

if __name__ == "__main__":
    tracer = LangSmithTracer()

    # 1. Demo trace_cell_invocation decorator
    @tracer.trace_cell_invocation(
        cell="L1-D1-A1",
        payload={"model": "gpt-4o", "input_tokens": 1200, "output_tokens": 400, "bms_score": 0.95, "bms_mode": "PYTHON_ONLY", "archetype": "A1.1"},
    )
    def demo_python_cell(x: int) -> dict:
        return {"solution": x * 2, "usage": {"input_tokens": 1200, "output_tokens": 400}}

    result = demo_python_cell(21)
    print("Decorator result:", result)

    # 2. Demo checkpoint
    cp_path = tracer.checkpoint_state("demo-cp-001", {"step": 3, "data": [1, 2, 3]}, metadata={"run_id": "r1"})
    print("Checkpoint written:", cp_path)
    loaded = tracer.resume_state("demo-cp-001")
    print("Checkpoint loaded:", loaded)

    # 3. Demo escalation trace
    tracer.trace_escalation("exec-004", "L1-D1-I1", "L3-D1-I1", "A1 returned UNKNOWN, escalated to A3")

    out = tracer.flush()
    print("LangSmith Tracer —", tracer.summary())
    if out:
        print("Traces written:", out)
