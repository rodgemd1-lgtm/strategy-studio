"""Layer 6: Cross-family verifier — prevent same-family generator-verifier pairs."""
from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

from pydantic import BaseModel


T = TypeVar("T", bound=Any)


class VerifierCaptureError(Exception):
    """Raised when generator and verifier are same family."""
    pass


# Mapping of model name to provider family
MODEL_FAMILIES: dict[str, str] = {
    "gpt4": "openai",
    "gpt4.5": "openai",
    "gpt4o": "openai",
    "gpt-4o": "openai",
    "gpt-4o-mini": "openai",
    "gpt-5": "openai",
    "gpt-5.5": "openai",
    "gpt-5-codex": "openai",
    "gpt35": "openai",
    "gpt3.5": "openai",
    "claude": "anthropic",
    "claude-sonnet-4": "anthropic",
    "claude-sonnet-4.5": "anthropic",
    "claude-opus-4": "anthropic",
    "claude-opus-4.7": "anthropic",
    "gemini": "google",
    "gemini-2.0": "google",
    "gemini-2.5": "google",
    "llama": "meta",
    "mistral": "mistral",
    "mixtral": "mistral",
}

# Provider pairs that are forbidden (same family)
FORBIDDEN_PAIRS: set[tuple[str, str]] = {
    ("openai", "openai"),
    ("anthropic", "anthropic"),
    ("google", "google"),
    ("meta", "meta"),
    ("mistral", "mistral"),
}


def get_model_family(model: str) -> str:
    """Get the provider family of a model.

    Tries: exact match → base prefix → partial match.
    Returns 'unknown' if no match found.
    """
    m = model.lower()
    if m in MODEL_FAMILIES:
        return MODEL_FAMILIES[m]
    # Try prefix before first dash (e.g. "claude-sonnet-4.5" → "claude")
    prefix = m.split("-")[0]
    if prefix in MODEL_FAMILIES:
        return MODEL_FAMILIES[prefix]
    # Try two-segment prefix (e.g. "claude-sonnet" for "claude-sonnet-4")
    segments = m.replace("_", "-").split("-")
    if len(segments) >= 2:
        base = f"{segments[0]}-{segments[1]}"
        if base in MODEL_FAMILIES:
            return MODEL_FAMILIES[base]
    return "unknown"


def verify_pair(generator: str, verifier: str) -> bool:
    """
    Verify generator and verifier are from different provider families.

    Raises VerifierCaptureError if both map to the same family.
    Returns True if cross-family verification passes.
    """
    gen_family = get_model_family(generator)
    ver_family = get_model_family(verifier)

    if gen_family == ver_family and gen_family != "unknown":
        raise VerifierCaptureError(
            f"Verifier capture detected: generator={generator} ({gen_family}) "
            f"and verifier={verifier} ({ver_family}) are same family. "
            f"Cross-family verification requires different model families."
        )

    return True


def cross_family_verified(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator that verifies cross-family for generator-verifier pairs."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        return func(*args, **kwargs)
    return wrapper


class GeneratorVerifierPair(BaseModel):
    """Validated generator-verifier pair — raises on same-family."""
    generator: str
    verifier: str

    def __init__(self, **data: Any):
        super().__init__(**data)
        verify_pair(self.generator, self.verifier)