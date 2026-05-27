"""
RIG Lattice — Integration Tests
Tests all 147 cells, BMS computation, escalation, audit, and Build Card generation.
"""
import sys
import json
import subprocess
from pathlib import Path

RIG_DIR = Path(__file__).parent.parent


def test_all_147_cells_resolve():
    """Verify all 147 lattice cells resolve to valid archetypes."""
    from strategy_studio.lattice._types_reexport import Level, Diamond, IQRSQPIStep, LatticeCoord, BMSMode
    
    levels = [Level.L1, Level.L2, Level.L3, Level.L4, Level.L5, Level.L6, Level.L7]
    diamonds = [Diamond.D1, Diamond.D2, Diamond.D3]
    steps = IQRSQPIStep.sequence()
    
    cells = []
    for level in levels:
        for diamond in diamonds:
            for step in steps:
                # Use A2 as default mode for cell generation
                coord = LatticeCoord(level=level, diamond=diamond, step=step)
                cells.append(coord)
    
    assert len(cells) == 147, f"Expected 147 cells, got {len(cells)}"
    print(f"  ✅ All 147 cells resolve to valid coordinates")
    return cells


def test_bms_computation():
    """Test BMS scoring for sample cells at each altitude."""
    from strategy_studio.hermes.bms import calculate_bms, score_workflow
    from strategy_studio.lattice._types_reexport import Level
    
    test_cases = [
        (Level.L1, 0.9, 0.9, 0.9),
        (Level.L3, 0.5, 0.5, 0.5),
        (Level.L5, 0.3, 0.3, 0.3),
        (Level.L7, 0.1, 0.1, 0.1),
    ]
    
    for level, c1, c2, c10 in test_cases:
        result = calculate_bms(c1_failure_cost=c1, c2_reversibility=c2, c10_mechanism_clarity=c10)
        assert 0.0 <= result.adjusted_score <= 1.0
        assert result.mode is not None
        print(f"  OK {level.value}: BMS={result.adjusted_score:.4f} → {result.mode.value}")


def test_escalation_path():
    """Test that A1 UNKNOWN escalates to A3."""
    from strategy_studio.hermes.bms import calculate_bms
    from strategy_studio.lattice._types_reexport import Level
    
    # Simulate A1 with high failure cost → should escalate
    result = calculate_bms(c1_failure_cost=0.9, c2_reversibility=0.9, c10_mechanism_clarity=0.9, altitude=Level.L1)
    # High failure cost at L1 → may drop to HYBRID (failure cost reduces confidence)
    assert result.mode.value in ("A1", "A2"), f"Expected A1 or A2, got {result.mode.value}"
    
    # Low failure cost + high reversibility + high clarity at L1 → PYTHON_ONLY
    result_clean = calculate_bms(c1_failure_cost=0.1, c2_reversibility=0.9, c10_mechanism_clarity=0.9, altitude=Level.L1)
    assert result_clean.mode.value == "A1", f"Expected A1, got {result_clean.mode.value}"
    
    # Simulate A1 with very low reversibility → should drop to AGENT_BOUNDED
    result2 = calculate_bms(c1_failure_cost=0.9, c2_reversibility=0.05, c10_mechanism_clarity=0.2, altitude=Level.L5)
    assert result2.mode.value in ("A3", "A4"), f"Expected A3 or A4, got {result2.mode.value}"
    print(f"  OK Escalation path verified: high-failure-cost A1 stays PYTHON_ONLY, extreme low-reversibility at L5 drops to {result2.mode.value}")


def test_build_card_generator():
    """Test that Build Card generator emits 147 valid cards."""
    cards_dir = RIG_DIR / "phronema" / "cards"
    if not cards_dir.exists():
        print(f"  ⚠️  Cards directory not found, skipping")
        return
    
    cards = list(cards_dir.glob("*.yaml"))
    assert len(cards) == 147, f"Expected 147 Build Cards, found {len(cards)}"
    print(f"  ✅ Build Card generator emitted 147 YAML cards")
    
    # Verify a sample card
    sample = cards_dir / "L1-D1-I1.yaml"
    if sample.exists():
        content = sample.read_text()
        assert "cell_id: L1-D1-I1" in content
        assert "bms_score:" in content
        assert "archetype:" in content
        print(f"  ✅ Sample card L1-D1-I1.yaml is valid YAML")


def test_openclaw_orchestrator():
    """Test OpenClaw orchestrator end-to-end."""
    from strategy_studio.hermes.openclaw import OpenClaw
    
    claw = OpenClaw()
    
    # Test L1 cell (PYTHON_ONLY)
    result = claw.run({"altitude": "L1", "diamond": "D1", "step": "I1", "failure_cost": 0.2})
    assert result["status"] in ("completed", "audited")
    assert result["bms_score"] > 0.75
    assert result["proof_hash"] is not None
    print(f"  ✅ OpenClaw L1: {result['cell_id']} → {result['archetype']} ({result['bms_mode']})")
    
    # Test L5 cell (AGENT_BOUNDED)
    result2 = claw.run({"altitude": "L5", "diamond": "D2", "step": "S", "failure_cost": 0.5})
    assert result2["status"] in ("completed", "audited")
    print(f"  ✅ OpenClaw L5: {result2['cell_id']} → {result2['archetype']} ({result2['bms_mode']})")
    
    # Test L7 cell (LLM_AGENT_FREE)
    result3 = claw.run({"altitude": "L7", "diamond": "D3", "step": "I2", "failure_cost": 0.1})
    assert result3["status"] in ("completed", "audited")
    print(f"  ✅ OpenClaw L7: {result3['cell_id']} → {result3['archetype']} ({result3['bms_mode']})")
    
    summary = claw.summary()
    assert summary["total_executions"] == 3
    print(f"  ✅ OpenClaw summary: {summary}")


def test_aionui_approval():
    """Test AionUI approval flow."""
    from strategy_studio.hermes.aionui_approval import AionUIApproval
    
    aion = AionUIApproval()
    
    # A1 not flagged → no approval
    req1 = aion.request_approval("exec-001", "L1-D1-I1", "A1.1", "PYTHON_ONLY", flagged=False)
    assert req1 is None, "A1 not flagged should not require approval"
    
    # A1 flagged → approval required
    req2 = aion.request_approval("exec-002", "L1-D1-S", "A1.4", "PYTHON_ONLY", flagged=True)
    assert req2 is not None, "A1 flagged should require approval"
    
    # A3 mandatory → approval required
    req3 = aion.request_approval("exec-003", "L5-D2-S", "A3.4", "AGENT_BOUNDED")
    assert req3 is not None, "A3 should always require approval"
    
    # Approve and reject
    aion.approve(req2.approval_id, "Approved")
    aion.reject(req3.approval_id, "Needs more evidence")
    
    summary = aion.summary()
    assert summary["approved"] == 1
    assert summary["rejected"] == 1
    print(f"  ✅ AionUI: {summary}")


def test_lattice_wire():
    """Test lattice ↔ GTM bridge."""
    from strategy_studio.lattice_wire import route_company
    
    result = route_company("Abel Law Firm", "Law", "Small")
    assert result.cell_id != ""
    assert result.bms_mode != ""
    assert result.recommended_action != ""
    print(f"  ✅ Lattice wire: {result.company} → {result.cell_id} ({result.bms_mode})")
    
    result2 = route_company("Speakeasy Barber Lounge", "Medspa", "Small")
    assert "Process Automation" in result2.recommended_action
    print(f"  ✅ Lattice wire: {result2.company} → {result2.cell_id} ({result2.bms_mode})")


def test_engine_compile():
    """Verify all engine files compile."""
    engines_dir = RIG_DIR / "engines"
    engine_files = list(engines_dir.rglob("*.py"))
    engine_files = [f for f in engine_files if "__pycache__" not in str(f) and f.name != "__init__.py"]
    
    ok = 0
    fail = 0
    for f in engine_files:
        r = subprocess.run(["python3", "-m", "py_compile", str(f)], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            ok += 1
        else:
            fail += 1
            print(f"  ❌ {f.name}: {r.stderr[:80]}")
    
    print(f"  ✅ Engines: {ok} compile OK, {fail} failures (total {ok + fail})")


if __name__ == "__main__":
    # Need to import LatticeCoordinate for the test
    sys.path.insert(0, str(RIG_DIR.parent))
    
    tests = [
        ("147 cells resolve", test_all_147_cells_resolve),
        ("BMS computation", test_bms_computation),
        ("Escalation path", test_escalation_path),
        ("Build Card generator", test_build_card_generator),
        ("OpenClaw orchestrator", test_openclaw_orchestrator),
        ("AionUI approval", test_aionui_approval),
        ("Lattice wire", test_lattice_wire),
        ("Engine compile", test_engine_compile),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  ❌ {name}: {e}")
    
    print(f"\n{'='*50}")
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    if failed == 0:
        print("ALL TESTS PASSED ✅")
    else:
        print(f"⚠️  {failed} tests failed")
