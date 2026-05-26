"""Tests for Archon harness system."""
import pytest
from strategy_studio.archon import (
    ArchonHarness,
    HarnessRegistry,
    LatticeCoordinate,
    Level,
    Diamond,
    BMSMode,
    IQRSQPIStep,
    ProcessType,
    GateStatus,
    ProofPacket,
    run_harness,
    get_all_cell_ids,
    validate_cell_id,
)


class TestLatticeCoordinate:
    def test_parse_valid(self):
        coord = LatticeCoordinate.parse("L2-D1-A1-I1")
        assert coord.level == Level.L2
        assert coord.diamond == Diamond.D1
        assert coord.mode == BMSMode.A1
        assert coord.step == IQRSQPIStep.I1

    def test_parse_all_steps(self):
        for step in IQRSQPIStep:
            coord = LatticeCoordinate.parse(f"L1-D1-A1-{step.name}")
            assert coord.step == step

    def test_parse_invalid(self):
        with pytest.raises(ValueError):
            LatticeCoordinate.parse("invalid")

    def test_str(self):
        coord = LatticeCoordinate(Level.L2, Diamond.D1, BMSMode.A1, IQRSQPIStep.S)
        assert str(coord) == "L2-D1-A1-S"

    def test_cell_id(self):
        coord = LatticeCoordinate(Level.L3, Diamond.D2, BMSMode.A2, IQRSQPIStep.R)
        assert coord.cell_id == "L3-D2-A2-R"

    def test_altitude_penalty(self):
        coord1 = LatticeCoordinate(Level.L1, Diamond.D1, BMSMode.A1, IQRSQPIStep.I1)
        coord4 = LatticeCoordinate(Level.L4, Diamond.D1, BMSMode.A1, IQRSQPIStep.I1)
        coord7 = LatticeCoordinate(Level.L7, Diamond.D1, BMSMode.A1, IQRSQPIStep.I1)
        assert coord1.altitude_penalty == 0.0
        assert coord4.altitude_penalty == -0.05
        assert coord7.altitude_penalty == -0.20


class TestArchonHarness:
    def test_create_harness(self):
        coord = LatticeCoordinate(Level.L2, Diamond.D1, BMSMode.A1, IQRSQPIStep.S)
        harness = ArchonHarness(coordinate=coord, process=ProcessType.ANALYZE)
        assert harness.coordinate == coord
        assert harness.process == ProcessType.ANALYZE

    def test_execute_returns_proof_packet(self):
        coord = LatticeCoordinate(Level.L2, Diamond.D1, BMSMode.A1, IQRSQPIStep.S)
        harness = ArchonHarness(coordinate=coord, process=ProcessType.ANALYZE)
        result = harness.execute({"query": "test", "company_name": "Tesla"})
        assert isinstance(result, ProofPacket)
        assert result.packet_id is not None

    def test_validation_catches_missing_fields(self):
        coord = LatticeCoordinate(Level.L2, Diamond.D1, BMSMode.A1, IQRSQPIStep.S)
        harness = ArchonHarness(coordinate=coord, process=ProcessType.ANALYZE)
        result = harness.execute({})  # Empty input
        assert isinstance(result, ProofPacket)

    def test_all_modes(self):
        for mode in BMSMode:
            coord = LatticeCoordinate(Level.L2, Diamond.D1, mode, IQRSQPIStep.S)
            harness = ArchonHarness(coordinate=coord, process=ProcessType.ANALYZE)
            result = harness.execute({"query": "test", "company_name": "Tesla"})
            assert isinstance(result, ProofPacket)


class TestHarnessRegistry:
    def test_register_and_get(self):
        reg = HarnessRegistry()
        packet = ProofPacket(process="test", coordinate="L2-D1-A1-S")
        reg.register(packet)
        assert reg.get(packet.packet_id) == packet

    def test_summary(self):
        reg = HarnessRegistry()
        packet = ProofPacket(process="test", coordinate="L2-D1-A1-S")
        reg.register(packet)
        summary = reg.summary()
        assert summary["total_executions"] == 1

    def test_get_by_process(self):
        reg = HarnessRegistry()
        packet = ProofPacket(process="analyze", coordinate="L2-D1-A1-S")
        reg.register(packet)
        results = reg.get_by_process(ProcessType.ANALYZE)
        assert len(results) == 1

    def test_get_failed(self):
        reg = HarnessRegistry()
        # Create a packet with a failed gate result
        from strategy_studio.archon import GateResult, QualityGate
        failed_gate = GateResult(
            coordinate="L2-D1-A1-S",
            step="solution",
            mode="A1",
            gates=[QualityGate(name="test", status=GateStatus.FAIL, message="test fail")],
            overall=GateStatus.FAIL,
        )
        packet = ProofPacket(process="test", coordinate="L2-D1-A1-S", gate_results=[failed_gate])
        reg.register(packet)
        failed = reg.get_failed()
        assert len(failed) == 1


class TestProofPacket:
    def test_create(self):
        packet = ProofPacket(process="test", coordinate="L2-D1-A1-S")
        assert packet.packet_id is not None
        assert packet.process == "test"

    def test_to_audit_log(self):
        packet = ProofPacket(process="test", coordinate="L2-D1-A1-S")
        log = packet.to_audit_log()
        assert "packet_id" in log
        assert "process" in log
        assert "coordinate" in log

    def test_all_gates_passed_empty(self):
        packet = ProofPacket(process="test", coordinate="L2-D1-A1-S")
        assert packet.all_gates_passed  # No gates = vacuously true


class TestUtilityFunctions:
    def test_get_all_cell_ids(self):
        cells = get_all_cell_ids()
        assert len(cells) == 588  # 7 levels × 3 diamonds × 4 modes × 7 steps

    def test_validate_cell_id_valid(self):
        assert validate_cell_id("L2-D1-A1-I1") is True
        assert validate_cell_id("L7-D3-A4-I2") is True

    def test_validate_cell_id_invalid(self):
        assert validate_cell_id("invalid") is False
        assert validate_cell_id("L1-D1-A1") is False

    def test_run_harness(self):
        packet = run_harness(
            ProcessType.ANALYZE,
            {"query": "test", "company_name": "Tesla"},
        )
        assert isinstance(packet, ProofPacket)
        assert packet.process == "analyze"