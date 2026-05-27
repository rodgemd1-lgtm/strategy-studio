"""Layer 2: Verify build card markdown matches workflow YAML."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import NamedTuple


class VerificationResult(NamedTuple):
    """Result of card-workflow verification."""
    passed: bool
    card_steps: set[str]
    workflow_nodes: set[str]
    missing_in_workflow: set[str]
    missing_in_card: set[str]
    extra_in_workflow: set[str]


def parse_build_card_steps(markdown_path: str | Path) -> set[str]:
    """Parse build card markdown for step IDs (L0, L1, etc.)."""
    content = Path(markdown_path).read_text()
    # Match stage prefix (S, L, or E) followed by digits: S0, L1, E2, S99
    pattern = r'\b[SLE]\d+\b'
    steps = set(re.findall(pattern, content))
    return steps


def parse_workflow_nodes(yaml_path: str | Path) -> set[str]:
    """Parse workflow YAML for node IDs."""
    import yaml
    
    content = Path(yaml_path).read_text()
    data = yaml.safe_load(content)
    
    if not isinstance(data, dict) or "stages" not in data:
        return set()
    
    nodes = set()
    for node in data.get("stages", []):
        if isinstance(node, dict) and "id" in node:
            nodes.add(node["id"])
        elif isinstance(node, dict) and "name" in node:
            nodes.add(node["name"])
    
    return nodes


def verify_card_workflow_match(
    card_path: str | Path,
    workflow_path: str | Path
) -> VerificationResult:
    """Verify build card steps match workflow nodes.
    
    Set difference MUST be empty for pass.
    """
    card_steps = parse_build_card_steps(card_path)
    workflow_nodes = parse_workflow_nodes(workflow_path)
    
    # Normalize to same format
    card_steps_norm = {s.upper() for s in card_steps}
    workflow_nodes_norm = {n.upper() for n in workflow_nodes}
    
    missing_in_workflow = card_steps_norm - workflow_nodes_norm
    missing_in_card = workflow_nodes_norm - card_steps_norm
    extra_in_workflow = workflow_nodes_norm - card_steps_norm
    
    passed = len(missing_in_workflow) == 0 and len(missing_in_card) == 0
    
    return VerificationResult(
        passed=passed,
        card_steps=card_steps,
        workflow_nodes=workflow_nodes,
        missing_in_workflow=missing_in_workflow,
        missing_in_card=missing_in_card,
        extra_in_workflow=extra_in_workflow,
    )


def main() -> int:
    """CLI entry point."""
    if len(sys.argv) < 3:
        print("Usage: verify_card_workflow_match.py <card.md> <workflow.yaml>")
        return 1
    
    card_path = Path(sys.argv[1])
    workflow_path = Path(sys.argv[2])
    
    if not card_path.exists():
        print(f"ERROR: Card file not found: {card_path}")
        return 1
    
    if not workflow_path.exists():
        print(f"ERROR: Workflow file not found: {workflow_path}")
        return 1
    
    result = verify_card_workflow_match(card_path, workflow_path)
    
    print(f"\n=== Card-Workflow Verification ===")
    print(f"Card steps:       {sorted(result.card_steps)}")
    print(f"Workflow nodes:   {sorted(result.workflow_nodes)}")
    
    if result.passed:
        print(f"\n✓ PASSED — All card steps have matching workflow nodes")
        return 0
    else:
        print(f"\n✗ FAILED — Mismatch detected:")
        if result.missing_in_workflow:
            print(f"  Missing in workflow: {sorted(result.missing_in_workflow)}")
        if result.missing_in_card:
            print(f"  Missing in card: {sorted(result.missing_in_card)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())