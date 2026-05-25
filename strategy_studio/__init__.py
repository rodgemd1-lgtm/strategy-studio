"""Strategy Studio - RIG deterministic strategy engine."""

# Core components
from strategy_studio.core.types import (
    Evidence,
    StructuredQuery,
    ResearchPack,
    Synthesis,
    Option,
    WargameScenario,
    Forecast,
    Segment,
    Channel,
    GTMPlan,
    FalsificationPacket,
    QualityResult,
    ProofPacket,
    Action,
    AuditRow,
    IntentKey,
)

# A1 archetypes
from strategy_studio.archetypes.a1.a1_1_intent import *
from strategy_studio.archetypes.a1.a1_2_question import *
from strategy_studio.archetypes.a1.a1_3_research import *
from strategy_studio.archetypes.a1.a1_4_solution import *
from strategy_studio.archetypes.a1.a1_5_quality import *
from strategy_studio.archetypes.a1.a1_6_proof import *
from strategy_studio.archetypes.a1.a1_7_integrate import *

# B-engines
from strategy_studio.engines.b29_synthesize import *
from strategy_studio.engines.b33_falsify import *
from strategy_studio.engines.b34_predict import *
from strategy_studio.engines.b36_wargame import *
from strategy_studio.engines.b31_consensus_delta import *
from strategy_studio.engines.b37_risk_assessment import *
from strategy_studio.engines.b40_market_sizing import *
from strategy_studio.engines.b43_competitive_positioning import *
from strategy_studio.engines.b44_timeline_planning import *
from strategy_studio.engines.b45_budget_allocation import *
from strategy_studio.engines.b46_impact_assessment import *

# Teaser system
from strategy_studio.teaser import generate_teaser, TeaserInput, run_batch

# Server and CLI
from strategy_studio.server import app
from strategy_studio.cli import cli

__version__ = "0.1.0"
__all__ = [
    # Core types
    "Evidence",
    "StructuredQuery",
    "ResearchPack",
    "Synthesis",
    "Option",
    "WargameScenario",
    "Forecast",
    "Segment",
    "Channel",
    "GTMPlan",
    "FalsificationPacket",
    "QualityResult",
    "ProofPacket",
    "Action",
    "AuditRow",
    "IntentKey",
    
    # A1 archetypes
    "execute_intent",
    "formulate_question",
    "execute_research",
    "synthesize",
    "validate",
    "build_proof",
    "integrate",
    
    # B-engines
    "synthesize_evidence",
    "falsify_claim",
    "build_forecast",
    "run_wargame",
    "calculate_consensus_delta",
    "assess_risks",
    "size_market",
    "position_competitively",
    "plan_timeline",
    "allocate_budget",
    "assess_impact",
    
    # Teaser system
    "generate_teaser",
    "TeaserInput",
    "run_batch",
    
    # Server and CLI
    "app",
    "cli",
]