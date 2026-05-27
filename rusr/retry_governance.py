"""Layer 5: Logged Retry — governance for tool call retries."""
from __future__ import annotations

import functools
import time
from datetime import datetime
from typing import Any, Callable, TypeVar

from pydantic import BaseModel


class RetryLogEntry(BaseModel):
    """Audit log entry for retry attempts."""
    timestamp: datetime
    attempt: int
    max_attempts: int
    function_name: str
    delta_ms: float
    status: str  # "attempt", "escalate", "blocker"


# Global log storage for audit
RETRY_LOG: list[RetryLogEntry] = []


class RetryEscalatedError(Exception):
    """Raised when retry attempts have been exhausted."""
    pass


class RetryBlockerError(Exception):
    """Raised when retry attempts have triggered a blocker."""
    pass


def logged_retry(
    max_attempts: int = 3,
    escalate_after: int = 3,
    log: bool = True
) -> Callable:
    """Decorator that logs every retry attempt and escalates on failure.
    
    - Logs every attempt with delta time
    - On attempt escalate_after+1: writes BLOCKER, raises RetryBlockerError
    - The decorator WRAPS tool calls (not just retries)
    
    Args:
        max_attempts: Maximum number of retry attempts
        escalate_after: After this many failures, write BLOCKER
        log: Whether to log attempts
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                attempt_start = time.perf_counter()
                
                try:
                    result = func(*args, **kwargs)
                    
                    if log:
                        delta_ms = (time.perf_counter() - attempt_start) * 1000
                        total_delta_ms = (time.perf_counter() - start_time) * 1000
                        entry = RetryLogEntry(
                            timestamp=datetime.now(),
                            attempt=attempt,
                            max_attempts=max_attempts,
                            function_name=func.__name__,
                            delta_ms=delta_ms,
                            status="attempt" if attempt < max_attempts else "success",
                        )
                        RETRY_LOG.append(entry)
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    delta_ms = (time.perf_counter() - attempt_start) * 1000
                    total_delta_ms = (time.perf_counter() - start_time) * 1000
                    
                    if log:
                        entry = RetryLogEntry(
                            timestamp=datetime.now(),
                            attempt=attempt,
                            max_attempts=max_attempts,
                            function_name=func.__name__,
                            delta_ms=delta_ms,
                            status="attempt",
                        )
                        RETRY_LOG.append(entry)
                    
                    if attempt < max_attempts:
                        continue
                    else:
                        # Attempts exhausted
                        if attempt >= escalate_after:
                            blocker_entry = RetryLogEntry(
                                timestamp=datetime.now(),
                                attempt=attempt,
                                max_attempts=max_attempts,
                                function_name=func.__name__,
                                delta_ms=total_delta_ms,
                                status="blocker",
                            )
                            RETRY_LOG.append(blocker_entry)
                            
                            # Write BLOCKER flag
                            _write_blocker(func.__name__, attempt, escalate_after)
                            
                            raise RetryBlockerError(
                                f"BLOCKER: {func.__name__} failed after {attempt} attempts. "
                                f"Exceeding escalate threshold ({escalate_after}). "
                                f"Original error: {last_exception}"
                            ) from last_exception
                        else:
                            raise RetryEscalatedError(
                                f"Escalated: {func.__name__} failed after {attempt} attempts"
                            ) from last_exception
            
            # Should not reach here
            if last_exception:
                raise last_exception
            raise RetryEscalatedError(f"{func.__name__} failed unexpectedly")
        
        return wrapper
    return decorator


def _write_blocker(function_name: str, attempt: int, threshold: int) -> None:
    """Write BLOCKER to audit log."""
    import os
    blocker_file = ".rig/blockers.log"
    os.makedirs(".rig", exist_ok=True)
    
    with open(blocker_file, "a") as f:
        f.write(
            f"BEGIN_BLOCKER {datetime.now().isoformat()} | "
            f"function={function_name} | "
            f"attempt={attempt}/{threshold} | "
            f"reason=retry_exhausted\n"
        )


def get_retry_log() -> list[RetryLogEntry]:
    """Get the global retry log."""
    return RETRY_LOG.copy()


def clear_retry_log() -> None:
    """Clear the retry log (for testing)."""
    RETRY_LOG.clear()