"""Strategy Studio — Complete strategy synthesis platform."""
from __future__ import annotations

# Core types
from strategy_studio.core.types import (
    Action,
    AuditRow,
    Evidence,
    FalsificationPacket,
    Forecast,
    GTMPlan,
    InboundPayload,
    IntentKey,
    Option,
    ProofPacket,
    QualityResult,
    ResearchPack,
    Segment,
    StructuredQuery,
    Synthesis,
    WargameScenario,
)

# Extended types
from strategy_studio.core.types_extended import (
    ArchetypeResult,
    BoardDeck,
    BoardSlide,
    Contradiction,
    CrossArchetypeConsensus,
    DecisionMatrix,
    DecisionRoomResult,
    ExecutiveSummary,
    MetaAnalysis,
    MonteCarloResult,
    OptionScore,
    PredictionResult,
    Scenario,
    SensitivityResult,
    SourceScore,
    StrategyReport,
    WargameResult,
    EvidenceGraph,
)

# Archetypes
from strategy_studio.archetypes import run_a1, run_a2, run_a3, run_a4

# B-Engines
from strategy_studio.engines import (
    synthesize_evidence,
    calculate_consensus_delta,
    falsify_claim,
    build_forecast,
    run_wargame,
    assess_risks,
    size_market,
    position_competitively,
    plan_timeline,
    allocate_budget,
    assess_impact,
)
from strategy_studio.engines.b41_client_intel import generate_wedge
from strategy_studio.engines.b42_competitor_intel import analyze_competitor