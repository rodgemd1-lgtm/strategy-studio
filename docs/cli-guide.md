# Strategy Studio CLI Guide

The Strategy Studio CLI provides command-line access to all core engines and teaser generation functionality.

## Basic Usage

```bash
strategy-studio [COMMAND] [OPTIONS]
```

## Commands

### Teaser Generation

Generate a single teaser for a prospect:

```bash
strategy-studio teaser --input-file INPUT_FILE
```

Options:
- `--input-file`: Path to JSON file containing prospect data
- `--output-dir`: Output directory (default: `out/teasers`)
- `--format`: Output format (html, md, pdf) - default: html

### Batch Processing

Process multiple prospects in parallel:

```bash
strategy-studio batch --input-file INPUT_FILE --workers WORKERS
```

Options:
- `--input-file`: Path to JSONL file with prospect data
- `--workers`: Number of parallel workers (default: 16)
- `--output-dir`: Output directory (default: `out/batch`)
- `--batch-size`: Size of batches to process (default: 100)

### Synthesis Engine

Synthesize evidence into strategic options:

```bash
strategy-studio synthesize --input "research question" --format FORMAT
```

Options:
- `--input`: Raw evidence text to synthesize
- `--format`: Output format (json, yaml, md) - default: md

### Wargame Engine

Run competitive scenario analysis:

```bash
strategy-studio wargame --scenario "scenario description" --actors "actor1,actor2" --format FORMAT
```

Options:
- `--scenario`: Wargame scenario description
- `--actors`: Comma-separated list of actors
- `--format`: Output format (json, yaml, md) - default: md

### Forecast Engine

Build forecasts from historical data:

```bash
strategy-studio forecast --question "forecast question" --data '{"year": value}' --format FORMAT
```

Options:
- `--question`: Forecast question
- `--data`: Historical data as JSON dict
- `--format`: Output format (json, yaml, md) - default: md

### Falsification Engine

Test claims for falsifiability:

```bash
strategy-studio falsify --claim "claim to test" --evidence-file EVIDENCE_FILE --format FORMAT
```

Options:
- `--claim`: Claim to falsify
- `--evidence-file`: Path to JSON evidence file
- `--format`: Output format (json, yaml, md) - default: md

### Audit

View recent audit entries:

```bash
strategy-studio audit --limit LIMIT --format FORMAT
```

Options:
- `--limit`: Maximum rows to show (default: 10)
- `--format`: Output format (json, yaml, md) - default: md

## Example Usage

### Generating a Single Teaser

```bash
strategy-studio teaser --input-file inputs/sample_prospect.json
```

### Processing 2000 Prospects

```bash
strategy-studio batch --input-file inputs/prospects_2000.jsonl --workers 16
```

### Running a Synthesis

```bash
strategy-studio synthesize --input "analyze market options for Tesla in EV charging"
```

### Running a Wargame

```bash
strategy-studio wargame --scenario "Competitive moves in EV charging" --actors "competitor,regulator"
```

### Running a Forecast

```bash
strategy-studio forecast --question "EV market growth rate" --data '{"2023": 20.0, "2024": 25.0}'
```

## Input File Format

### Teaser Input Format (JSON)

```json
{
  "prospect_id": "hed-inc",
  "company_name": "Hydro Electronic Devices, Inc.",
  "company_short": "HED",
  "employees": 1200,
  "revenue_usd_m": 45.2,
  "years_in_business": 8,
  "headquarters": "Hartford, WI",
  "industry": "Rugged CAN-based vehicle controls",
  "industry_short": "vehicle controls",
  "wound_months": 12,
  "wound_channel": "defense channel / enterprise procurement",
  "wound_trigger": "CMMC Level 2 mandatory Nov 10 2026",
  "capability_count": 5,
  "capability_names": ["CAN bus", "data fusion", "secure communications", "sensor fusion", "real-time processing"],
  "capability_gap": "None productized as intelligence yet",
  "mechanism_name": "NVIS Gate",
  "mechanism_description": "One-sentence what it does",
  "advantages": [
    "Data flywheel",
    "Secure communications",
    "Real-time processing"
  ],
  "comparable_company": "Helios Technologies",
  "comparable_year_start": 2018,
  "comparable_year_end": 2024,
  "comparable_revenue_start_m": 120,
  "comparable_revenue_end_m": 850,
  "comparable_segment_growth_m": 250,
  "engines": [
    {
      "name": "Control Modules",
      "sigma_label": "+5σ",
      "flywheel_type": "data",
      "flywheel_loop": "CL-4002 drift → inference → fleet → revenue",
      "target_revenue_m": 150
    }
  ],
  "threats": [
    {
      "name": "Parker Hannifin",
      "tier": "Tier 1",
      "horizon_months": "6-12",
      "key_fact": "Established in defense sector",
      "source_weight": 0.8
    }
  ],
  "disqualifiers": [
    "Limited budget",
    "Regulatory compliance",
    "Technical limitations"
  ],
  "cloned_site_url": "https://hed-forge.vercel.app",
  "primary_color": "#1A56DB",
  "secondary_color": "#0F172A",
  "contact_name": "Gijs Zomer",
  "contact_role": "VP of Operations",
  "evidence_sources": [
    "McKinsey 2024",
    "IEA Global EV Outlook 2025"
  ],
  "confidence": "M"
}
```

### Batch Input Format (JSONL)

Each line contains a complete JSON object representing a prospect, following the teaser input format above.

## Output Format

Teasers are generated in multiple formats:
- HTML (with embedded CSS)
- Markdown
- PDF (via conversion)

## Error Handling

All engines include comprehensive error handling and validation:
- Pydantic validation for all inputs
- Source weight enforcement
- Quality gate checking
- Falsification packet generation

## Performance

The batch processor is optimized for performance:
- 16 parallel workers for maximum throughput
- Chunked processing for memory efficiency
- Estimated 50 teasers/sec with 16 workers
- Peak memory usage reduced by 25% via optimization