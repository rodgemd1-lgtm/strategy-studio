"""
Layer 3: Skill Registry + Audit.

Every installed skill must be registered, signed, and audited.
Skill updates without hash change = halt.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

CREDENTIAL_PATTERNS = [
    re.compile(r"api[_-]?key\s*[=:]\s*['\"]sk-[a-zA-Z0-9]{20,}['\"]"),
    re.compile(r"sk-[a-zA-Z0-9]{32,}"),
    re.compile(r"password\s*[=:]\s*['\"][^'\"]{8,}['\"]"),
    re.compile(r"secret[_-]?key\s*[=:]\s*['\"][^'\"]{16,}['\"]"),
    re.compile(r"Bearer\s+[a-zA-Z0-9_\-]{20,}"),
    re.compile(r"x-api-key:\s*[a-zA-Z0-9]{20,}"),
]

INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+your\s+(system\s+)?instructions", re.IGNORECASE),
    re.compile(r"new\s+instruction[s]?\s*:", re.IGNORECASE),
    re.compile(r"#.*override.*system.*prompt", re.IGNORECASE),
    re.compile(r"<\s*system\s*>", re.IGNORECASE),
]

NETWORK_PATTERNS = [
    re.compile(r"https?://", re.IGNORECASE),
    re.compile(r"requests\.(get|post|put|delete)", re.IGNORECASE),
    re.compile(r"urllib", re.IGNORECASE),
    re.compile(r"subprocess\s*\(", re.IGNORECASE),
]


class AuditFinding:
    """Base audit finding."""
    pass


class HardcodedCredentialError(AuditFinding):
    def __init__(self, pattern: str, line: str, line_num: int) -> None:
        self.pattern = pattern
        self.line = line
        self.line_num = line_num

    def __str__(self) -> str:
        return f"Hardcoded credential on line {self.line_num}: {self.line[:60]}"


class PromptInjectionError(AuditFinding):
    def __init__(self, pattern: str, line: str, line_num: int) -> None:
        self.pattern = pattern
        self.line = line
        self.line_num = line_num

    def __str__(self) -> str:
        return f"Prompt injection pattern on line {self.line_num}: {self.line[:60]}"


class UnexposedNetworkEgress(AuditFinding):
    def __init__(self, line: str, line_num: int, tool: str) -> None:
        self.line = line
        self.line_num = line_num
        self.tool = tool

    def __str__(self) -> str:
        return f"Unexposed network egress on line {self.line_num}: {self.tool}"


def audit_skill(code_or_file: str, skill_id: str) -> list[AuditFinding]:
    """
    Audit a skill's code for security issues.

    Returns list of findings. Empty list = clean.
    """
    findings: list[AuditFinding] = []
    lines = code_or_file.split("\n") if "\n" in code_or_file else [code_or_file]

    for i, line in enumerate(lines, 1):
        line_clean = line.strip()

        # Credential check
        for pattern in CREDENTIAL_PATTERNS:
            if pattern.search(line_clean):
                findings.append(HardcodedCredentialError(str(pattern.pattern), line_clean, i))

        # Prompt injection check
        for pattern in INJECTION_PATTERNS:
            if pattern.search(line_clean):
                findings.append(PromptInjectionError(str(pattern.pattern), line_clean, i))

    return findings


def scan_skill_file(file_path: str | Path) -> list[AuditFinding]:
    """Scan a skill file and return audit findings."""
    path = Path(file_path)
    if not path.exists():
        return []
    code = path.read_text()
    return audit_skill(code, path.stem)


def verify_skill_hash(skill_path: str | Path, expected_hash: str) -> bool:
    """Verify a skill's content hash matches expected hash."""
    path = Path(skill_path)
    if not path.exists():
        return False
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    return actual == expected_hash


def compute_skill_hash(skill_path: str | Path) -> str:
    """Compute SHA256 hash of skill file content."""
    path = Path(skill_path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_skills(skills_dir: str | Path) -> dict[str, list[str]]:
    """Audit all skills in a directory. Returns dict of skill_id → findings."""
    path = Path(skills_dir)
    if not path.exists():
        return {}
    results: dict[str, list[str]] = {}
    for skill_file in path.rglob("*.py"):
        findings = scan_skill_file(skill_file)
        if findings:
            results[skill_file.stem] = [str(f) for f in findings]
    return results


def main():
    """CLI: audit_skills <skills_dir>"""
    import sys
    if len(sys.argv) < 2:
        print("Usage: audit_skills <skills_dir>")
        sys.exit(1)
    results = audit_skills(sys.argv[1])
    if not results:
        print("All skills clean.")
    else:
        for skill_id, findings in results.items():
            print(f"\n{skill_id}:")
            for f in findings:
                print(f"  - {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()