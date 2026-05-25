"""Strategy Teaser — light wedge artifact for prospect cloned websites.

Generates a 1-page HTML/markdown teaser that lives on a prospect's cloned site.
Reverse-engineers what worked for HED into a deterministic A1 template.

Structure (10 sections, all required):
1. Wound naming — "You are X months from being locked out of Y"
2. Mirror — "We see N capabilities. None productized as intelligence yet."
3. Named mechanism — specific to industry (NVIS Gate, Helios Curve, etc.)
4. Three structural advantages (unrecognized by prospect)
5. Comparable transaction — analog company that grew via similar pivot
6. Three category engines (their product lines as data flywheels)
7. Competitive threat tiers (Tier 1 6-12mo, Tier 2 12-24mo, Tier 3 24-36mo)
8. Three RIG OS tiers — what's possible (Solo / Activation / Transformation)
9. Disqualifiers — three reasons RIG would say no
10. Open loop — single CTA, no calendar link

Output: HTML page + markdown + PDF-ready package.
"""
from strategy_studio.teaser.generator import generate_teaser
from strategy_studio.teaser.schema import TeaserInput


def run_batch(*args, **kwargs):
    """Lazy import so `python -m strategy_studio.teaser.batch` runs without module preloading warnings."""
    from strategy_studio.teaser.batch import run_batch as _run_batch

    return _run_batch(*args, **kwargs)

__all__ = ["generate_teaser", "TeaserInput", "run_batch"]
