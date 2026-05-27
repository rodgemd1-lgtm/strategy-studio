"""
Strategy Studio — RIG Deviator strategy synthesis, wargame, forecasting, and lattice engine.

4 BMS build modes x 7 IQRSQPI steps = 28 archetypes.
Coordinate system: 7 Levels x 3 Diamonds x 4 BMS Modes = 84 primary coordinates
Process-expanded: 84 x 7 IQRSQPI steps = 588 execution cells

A1.1-A1.7: PYTHON_ONLY (zero model, deterministic)
A2.1-A2.7: HYBRID (Python-gated LLM)
A3.1-A3.7: AGENT_BOUNDED (LangGraph state machines)
A4.1-A4.7: LLM_AGENT_FREE (hierarchical CrewAI)
"""

# Core types — all importable from strategy_studio.core.types
from strategy_studio.core.types import (
    InboundPayload,
    IntentKey,
    StructuredQuery,
    Source,
    ResearchPack,
    Draft,
    QualityResult,
    ProofPacket,
    Action,
    AuditRow,
    QualityGateResult,
    ActionResult,
)

# Lattice types — canonical home is strategy_studio.lattice._types_reexport
from strategy_studio.lattice._types_reexport import (
    Level,
    Diamond,
    BMSMode,
    IQRSQPIStep,
    LatticeCoordinate,
    LatticeCoord,
    LATTICE_VERSION,
)

from strategy_studio.resolve_archetype import (
    resolve_archetype,
    resolve_file,
    resolve_cell_id,
    get_all_cell_ids,
    check_all_files_exist,
)

# Lazy imports for mode-specific pipelines
def run_a1(payload: InboundPayload, **kwargs) -> AuditRow:
    from strategy_studio.archetypes.a1 import run_iqrsqpi
    return run_iqrsqpi(payload, **kwargs)

def run_a2(payload: InboundPayload, **kwargs) -> AuditRow:
    from strategy_studio.archetypes.a2 import run_hybrid
    return run_hybrid(payload, **kwargs)

def run_a3(payload: InboundPayload, **kwargs) -> AuditRow:
    from strategy_studio.archetypes.a3 import run_agent_bounded
    return run_agent_bounded(payload, **kwargs)

def run_a4(payload: InboundPayload, **kwargs) -> AuditRow:
    from strategy_studio.archetypes.a4 import run_llm_free
    return run_llm_free(payload, **kwargs)


def run_cell(coordinate: LatticeCoordinate, payload: InboundPayload, **kwargs) -> AuditRow:
    """Run the correct archetype pipeline based on BMS mode."""
    mode_runners = {
        BMSMode.A1: run_a1,
        BMSMode.A2: run_a2,
        BMSMode.A3: run_a3,
        BMSMode.A4: run_a4,
    }
    runner = mode_runners.get(coordinate.bms_mode, run_a1)
    return runner(payload, **kwargs)