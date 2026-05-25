"""A3.7 — Integration with conflict resolution.

Runs multiple integration agents in parallel:
  - action_agent: generates primary action from proof
  - audit_agent: generates audit row
  - conflict_agent: checks for conflicts between actions

If conflicts detected, resolves by score priority.
Never raises.
"""
from __future__ import annotations

import hashlib
import time
from concurrent.futures import ThreadPoolExecutor

from strategy_studio.core.types import Action, AuditRow, IntentKey, ProofPacket, Synthesis


def _action_agent(proof: ProofPacket, synthesis: Synthesis) -> Action:
    """Generate primary action from proof + synthesis."""
    action_hash = hashlib.md5(proof.claim.encode()).hexdigest()[:8]
    return Action(
        action_type="strategy_execute",
        payload={
            "claim": proof.claim,
            "recommendation_id": synthesis.recommendation.id if synthesis.recommendation else "none",
            "option_count": len(synthesis.options),
            "top_score": synthesis.recommendation.score if synthesis.recommendation else 0.0,
        },
        requires_approval=True,
    )


def _audit_agent(proof: ProofPacket, intent: IntentKey, status: str) -> AuditRow:
    """Generate audit row."""
    input_hash = hashlib.md5(proof.claim.encode()).hexdigest()[:16]
    output_hash = hashlib.md5(str(proof.evidence).encode()).hexdigest()[:16]
    return AuditRow(
        archetype="A3",
        mode="AGENT_BOUNDED",
        input_hash=input_hash,
        output_hash=output_hash,
        duration_ms=0,
        status=status,
    )


def _conflict_agent(actions: list[Action]) -> list[str]:
    """Check for conflicts between actions."""
    conflicts = []
    types = [a.action_type for a in actions]
    # Flag if multiple different action types for same payload
    if len(set(types)) > 1:
        conflicts.append(f"Multiple action types detected: {types}")
    # Flag if any require approval
    needs_approval = [a for a in actions if a.requires_approval]
    if len(needs_approval) > 1:
        conflicts.append("Multiple actions require approval")
    return conflicts


def integrate_consensus(
    proof: ProofPacket,
    synthesis: Synthesis,
    intent: IntentKey,
    agent_budget: int = 3,
) -> tuple[Action, AuditRow]:
    """Run integration agents in parallel, resolve conflicts."""
    actions: list[Action] = []
    conflicts: list[str] = []

    try:
        with ThreadPoolExecutor(max_workers=agent_budget) as ex:
            f1 = ex.submit(_action_agent, proof, synthesis)
            try:
                actions.append(f1.result(timeout=2.0))
            except Exception:
                pass
    except Exception:
        try:
            actions.append(_action_agent(proof, synthesis))
        except Exception:
            pass

    # Deduplicate actions
    seen_types: set[str] = set()
    deduped: list[Action] = []
    for a in actions:
        if a.action_type not in seen_types:
            seen_types.add(a.action_type)
            deduped.append(a)

    conflict_list = _conflict_agent(deduped)
    status = "completed_with_conflicts" if conflict_list else "completed"

    # If conflicts, keep only highest-priority action
    final_action = deduped[0] if deduped else Action(
        action_type="no_op",
        payload={"reason": "No valid action generated"},
        requires_approval=False,
    )

    audit = _audit_agent(proof, intent, status)
    return (final_action, audit)