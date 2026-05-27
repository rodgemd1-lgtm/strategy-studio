"""Layer 7: Output Guardrails — trust levels and quarantine."""
from __future__ import annotations

import os
import shutil
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class TrustLevel(str, Enum):
    """Output trust level."""
    TRUSTED = "TRUSTED"
    UNTRUSTED = "UNTRUSTED"


# Tools that produce trusted output
TRUSTED_TOOLS: set[str] = {
    "terminal",
    "read_file",
    "write_file",
    "generic_image_gen",
    "vision_analyze",
}

# Directory for quarantined outputs
QUARANTINE_DIR = ".rig/quarantine"


class SafeOutput(BaseModel):
    """Output wrapped with trust level."""
    raw_output: str
    trust_level: TrustLevel
    tool_name: str | None = None
    timestamp: datetime = datetime.now()
    
    def __str__(self) -> str:
        """Return raw output or quarantined version based on trust."""
        if self.trust_level == TrustLevel.UNTRUSTED:
            return f"<UNTRUSTED_DATA>\n{self.raw_output}\n</UNTRUSTED_DATA>"
        return self.raw_output


def get_trust_level(tool_name: str) -> TrustLevel:
    """Determine trust level based on tool name."""
    if tool_name in TRUSTED_TOOLS:
        return TrustLevel.TRUSTED
    return TrustLevel.UNTRUSTED


def receive_tool_output(raw_output: Any, tool_name: str) -> SafeOutput:
    """Wrap raw output in SafeOutput with appropriate trust level.
    
    Untrusted outputs are tagged and potentially quarantined.
    """
    output_str = str(raw_output)
    trust_level = get_trust_level(tool_name)
    
    safe_output = SafeOutput(
        raw_output=output_str,
        trust_level=trust_level,
        tool_name=tool_name,
    )
    
    # Quarantine untrusted outputs
    if trust_level == TrustLevel.UNTRUSTED:
        _quarantine_output(safe_output)
    
    return safe_output


def _quarantine_output(output: SafeOutput) -> None:
    """Move untrusted output to quarantine directory."""
    quarantine_path = Path(QUARANTINE_DIR)
    quarantine_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output.tool_name or 'unknown'}_{timestamp}.txt"
    filepath = quarantine_path / filename
    
    with open(filepath, "w") as f:
        f.write(f"Tool: {output.tool_name}\n")
        f.write(f"Trust Level: {output.trust_level}\n")
        f.write(f"Timestamp: {output.timestamp.isoformat()}\n")
        f.write(f"\n---\n")
        f.write(output.raw_output)
    
    # Update quarantine log
    log_path = quarantine_path / "quarantine.log"
    with open(log_path, "a") as f:
        f.write(f"{output.timestamp.isoformat()} | {output.tool_name} | {filepath}\n")


def is_quarantined(output_id: str) -> bool:
    """Check if an output is in quarantine."""
    quarantine_path = Path(QUARANTINE_DIR)
    log_path = quarantine_path / "quarantine.log"
    
    if not log_path.exists():
        return False
    
    return output_id in log_path.read_text()


def release_from_quarantine(output_id: str) -> bool:
    """Manually release an output from quarantine (requires approval)."""
    quarantine_path = Path(QUARANTINE_DIR)
    log_path = quarantine_path / "quarantine.log"
    
    if not log_path.exists():
        return False
    
    # This would require explicit approval workflow
    # For now, just log the request
    approval_log = quarantine_path / "release_requests.log"
    with open(approval_log, "a") as f:
        f.write(f"{datetime.now().isoformat()} | {output_id} | PENDING_APPROVAL\n")
    
    return False  # Always return False until approved