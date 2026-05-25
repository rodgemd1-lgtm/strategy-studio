"""B41 — Client intelligence / wedge generator."""
from __future__ import annotations

from strategy_studio.core.types import Segment


def generate_wedge(prospect_data: dict) -> Segment:
    """Extract ICP, entry_wedge, sizing from prospect data."""
    icp = prospect_data.get("icp") or prospect_data.get("ideal_customer_profile", "")
    if not icp:
        title = prospect_data.get("title", "")
        dept = prospect_data.get("department", "")
        company_size = prospect_data.get("company_size", "")
        parts = [p for p in (title, dept, company_size) if p]
        icp = "; ".join(parts) if parts else "Unspecified ICP"

    entry = prospect_data.get("entry_wedge") or prospect_data.get("pain_point", "")
    if not entry:
        entry = "Operational inefficiency or compliance gap"

    sizing = prospect_data.get("sizing") or prospect_data.get("tam", "")
    if not sizing:
        employees = prospect_data.get("employees")
        if employees and str(employees).isdigit():
            sizing = f"~{int(employees) * 1200} ARR potential"
        else:
            sizing = "Sizing undefined"

    sources = prospect_data.get("sources", [])
    if isinstance(sources, str):
        sources = [sources]

    return Segment(
        icp=icp,
        entry_wedge=entry,
        sizing=sizing,
        sources=sources,
    )
