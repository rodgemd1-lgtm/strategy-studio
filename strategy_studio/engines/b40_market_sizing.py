"""B40 — Market sizing engine."""
from __future__ import annotations

from strategy_studio.core.types import Option


def size_market(options: list[Option]) -> list[dict]:
    """Size markets for each option."""
    sized_options = []
    
    for opt in options:
        # Simple market sizing based on option description
        desc_lower = opt.description.lower()
        
        # Estimate TAM/BAM/SAM based on keywords
        tam = 0.0
        bam = 0.0
        sam = 0.0
        
        # Look for size indicators in description
        if "enterprise" in desc_lower or "corporate" in desc_lower:
            tam = 500000000.0  # $500M TAM
            bam = 100000000.0  # $100M BAM  
            sam = 20000000.0   # $20M SAM
        elif "consumer" in desc_lower or "retail" in desc_lower:
            tam = 2000000000.0  # $2B TAM
            bam = 500000000.0  # $500M BAM
            sam = 50000000.0   # $50M SAM
        elif "government" in desc_lower or "public sector" in desc_lower:
            tam = 10000000000.0  # $10B TAM
            bam = 2000000000.0  # $2B BAM
            sam = 100000000.0   # $100M SAM
        else:
            # Default assumptions
            tam = 100000000.0  # $100M TAM
            bam = 20000000.0   # $20M BAM
            sam = 5000000.0    # $5M SAM
            
        # Create market sizing data
        sizing = {
            "option_id": opt.id,
            "tam": tam,
            "bam": bam,
            "sam": sam,
            "unit": "USD"
        }
        sized_options.append(sizing)
        
    return sized_options