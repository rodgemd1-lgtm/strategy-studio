"""Strategy Studio runtime configuration."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field, model_validator


class RuntimeConfig(BaseModel):
    """Runtime configuration for Strategy Studio."""

    lakeos_cli_path: Path = Path(
        "/Users/mikerodgers/rig-lab/phronema/scripts/lakeos_cli.py"
    )
    lakeos_rest_url: str = "http://127.0.0.1:8788"
    recall_api_base: str = "https://backend.getrecall.ai/api/v1"
    recall_api_key: str = Field(default_factory=lambda: os.environ.get("RECALL_API_KEY", ""))
    rig_home: Path = Field(default_factory=lambda: Path.home() / ".rig")
    audit_db_path: Path | None = None
    output_dir: Path = Field(default_factory=lambda: Path.home() / "rig-output")
    log_level: str = "INFO"

    @model_validator(mode="after")
    def _set_derived_paths(self) -> "RuntimeConfig":
        if self.audit_db_path is None:
            self.audit_db_path = self.rig_home / "audit.sqlite"
        return self
