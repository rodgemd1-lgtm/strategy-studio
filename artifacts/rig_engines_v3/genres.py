"""Genre presets for the v3 strict auditor.

Maps a `--genre` flag to a subset of engine slugs. Calibration is tuned for
HED-style sales proposals; running the full 40 against an internal infra plan
produces noise. Genres scope the audit to engines that actually apply.

Add a new genre by adding a key here and listing the relevant engine slugs.
"""

from __future__ import annotations

# Universal engines — apply to any written artifact.
UNIVERSAL = [
    "signal_to_noise",          # PRISM
    "fine_structure",           # PARSEC
    "gravity_escape",           # GRAVITON
    "absolute_zero",            # KELVIN
    "pauli_exclusion",          # PAULI
    "speed_of_lumen",           # LUMEN
    "mechanism_furnace",        # FORGE
    "reality_anchor",           # ANCHOR
    "temporal_horizon_integrity",  # HORIZON
    "rupture",                  # BREAKER
    "bayesian_calibration",     # BAYES
    "feynman_xray",             # XRAY
    "darwinian_selection",      # DARWIN
    "opponent_process",         # REBOUND
    "physarum_prune",           # SLIME
    "zeigarnik_residue",        # LOOP
    "hermeneutic_density",      # WELLSPRING
    "kolmogorov_originality",   # GLYPH
    "humpback_spiral",          # HUMPBACK
    "pheromone_swarm",          # SWARM
]

# Engines that only make sense for external sales proposals (HED-style).
SALES_ONLY = [
    "cuckoo_parasitic",
    "cognitive_sovereignty",
    "coral_reef_synthesis",
    "critical_phase",
    "frame_collision",
    "hawking_horizon",
    "memory_residue",
    "mycorrhizal_root",
    "predictive_surprise",
    "quantum_tunnel",
    "somatic_stakes",
    "vacuum_zeropoint",
    "voltage",
    "levy_flight",
    "autonomy_calibration",
    "bell_entanglement",
    "bioluminescent_attraction",
    "casimir_force",
    "chemotaxis_gradient",
    "clonal_refinement",
]

GENRES: dict[str, list[str]] = {
    "all": [],  # empty → no filter → all 40 engines (existing default)
    "internal": UNIVERSAL,
    "internal-plan": UNIVERSAL,
    "engineering": UNIVERSAL,
    "sales": UNIVERSAL + SALES_ONLY,
    "proposal": UNIVERSAL + SALES_ONLY,
}


def resolve(genre: str | None, explicit_engines: str | None) -> list[str] | None:
    """Return the engine-slug list (or None for 'all 40')."""
    if explicit_engines:
        return [e.strip() for e in explicit_engines.split(",") if e.strip()]
    if not genre or genre == "all":
        return None
    if genre not in GENRES:
        raise SystemExit(f"unknown genre: {genre}. Options: {', '.join(GENRES)}")
    return GENRES[genre] or None
