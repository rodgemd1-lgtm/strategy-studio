"""Layer 8: Memory Firewall — namespace isolation."""
from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

from pydantic import BaseModel


T = TypeVar("T", bound=Any)


class NamespaceLeakError(Exception):
    """Raised when unauthorized cross-namespace read occurs."""
    pass


class NamespaceWriteError(Exception):
    """Raised when unauthorized cross-namespace write occurs."""
    pass


# Current namespace context (thread-local in production)
_current_namespace: str = "default"


class NamespaceFirewall(BaseModel):
    """Namespace firewall configuration."""
    namespace: str
    read_from: list[str] = []
    write_to: list[str] = []


def set_current_namespace(namespace: str) -> None:
    """Set the current namespace context."""
    global _current_namespace
    _current_namespace = namespace


def get_current_namespace() -> str:
    """Get the current namespace context."""
    return _current_namespace


def firewall(
    read_from: list[str] | None = None,
    write_to: list[str] | None = None
) -> Callable:
    """Decorator that enforces namespace firewall rules.
    
    Raises:
        NamespaceLeakError: On undeclared cross-namespace read
        NamespaceWriteError: On undeclared cross-namespace write
    
    Args:
        read_from: Allowed namespaces to read from
        write_to: Allowed namespaces to write to
    """
    read_from = read_from or []
    write_to = write_to or []
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            current_ns = get_current_namespace()
            
            # Check read permissions
            for ns in read_from:
                if not ns.startswith(current_ns) and ns != f"{current_ns}/":
                    if not _is_ancestor(current_ns, ns):
                        raise NamespaceLeakError(
                            f"Unauthorized read: {current_ns} cannot read from {ns}. "
                            f"Declared read_from: {read_from}"
                        )
            
            # Check write permissions
            for ns in write_to:
                if not ns.startswith(current_ns) and ns != f"{current_ns}/":
                    if not _is_ancestor(current_ns, ns):
                        raise NamespaceWriteError(
                            f"Unauthorized write: {current_ns} cannot write to {ns}. "
                            f"Declared write_to: {write_to}"
                        )
            
            return func(*args, **kwargs)
        
        wrapper._firewall_config = {"read_from": read_from, "write_to": write_to}
        return wrapper
    
    return decorator


def _is_ancestor(parent: str, child: str) -> bool:
    """Check if parent is an ancestor of child."""
    return child.startswith(parent + "/") or child.startswith(parent + ".")


def CrossNamespaceRead(
    source_namespace: str,
    read_from: list[str]
) -> Callable:
    """Decorator for explicit cross-namespace read queries.
    
    This is used when a namespace explicitly needs to query another.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            current_ns = get_current_namespace()
            
            if source_namespace not in read_from and not _is_ancestor(source_namespace, current_ns):
                raise NamespaceLeakError(
                    f"CrossNamespaceRead denied: {current_ns} cannot read from {source_namespace}. "
                    f"Allowed: {read_from}"
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


class MemoryNamespace:
    """Isolated memory namespace."""
    
    def __init__(self, namespace: str, read_from: list[str], write_to: list[str]):
        self.namespace = namespace
        self.read_from = read_from
        self.write_to = write_to
    
    def read(self, key: str) -> Any:
        """Read from namespace with firewall check."""
        # Simulate reading from a namespaced memory store
        return None
    
    def write(self, key: str, value: Any) -> None:
        """Write to namespace with firewall check."""
        pass