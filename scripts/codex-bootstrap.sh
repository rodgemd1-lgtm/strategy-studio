#!/usr/bin/env bash
# ── codex-bootstrap.sh ────────────────────────────────────────────────
# Single command for Codex to start the 2000-prospect run.
#
# Usage:
#   ./scripts/codex-bootstrap.sh inputs/prospect_list.csv
#
# What this does:
#   1. Verifies the strategy-studio package imports cleanly
#   2. Confirms LakeOS + recall.it endpoints are reachable
#   3. Loads the Codex prompt and pipes it to the codex CLI
#   4. Codex then processes the CSV, builds prospects_2000.jsonl,
#      and runs the batch generator
# ──────────────────────────────────────────────────────────────────────

set -euo pipefail

INPUT_CSV="${1:-inputs/prospect_list.csv}"
WORKDIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$WORKDIR"

echo "─────────────────────────────────────────────────────────────────"
echo "RIG Strategy Teaser — Codex Bootstrap"
echo "─────────────────────────────────────────────────────────────────"
echo "Workdir:   $WORKDIR"
echo "Input CSV: $INPUT_CSV"
echo ""

# ── 1. Verify the package imports ────────────────────────────────────
echo "[1/4] Verifying strategy_studio package..."
python3 -c "
from strategy_studio.teaser.schema import TeaserInput
from strategy_studio.teaser.generator import generate_teaser
from strategy_studio.teaser.batch import run_batch
print('  ✓ teaser package OK')
" || { echo "  ✗ Package import failed. Run: pip install -e ."; exit 1; }

# ── 2. Verify endpoints ──────────────────────────────────────────────
echo ""
echo "[2/4] Verifying LakeOS and recall.it endpoints..."
if curl -s --max-time 5 "http://127.0.0.1:8788/health" > /dev/null 2>&1; then
    echo "  ✓ LakeOS reachable at http://127.0.0.1:8788"
else
    echo "  ⚠ LakeOS not running. Start it:"
    echo "    cd ~/rig-lab/phronema && python3 scripts/lakeos_server.py &"
fi

if curl -s --max-time 5 -H "Authorization: Bearer ${RECALL_API_KEY:-sk_b2cf9f1fcf737f37b2bafb6830c1f846}" \
    "https://backend.getrecall.ai/api/v1/cards?limit=1" | grep -q "id\|error"; then
    echo "  ✓ recall.it API reachable"
else
    echo "  ⚠ recall.it API unreachable — check RECALL_API_KEY"
fi

# ── 3. Verify input CSV ──────────────────────────────────────────────
echo ""
echo "[3/4] Verifying input CSV..."
if [ ! -f "$INPUT_CSV" ]; then
    echo "  ✗ Input CSV not found: $INPUT_CSV"
    exit 1
fi

ROW_COUNT=$(($(wc -l < "$INPUT_CSV") - 1))  # subtract header
echo "  ✓ $ROW_COUNT prospects to process"

# ── 4. Pipe the Codex prompt ─────────────────────────────────────────
echo ""
echo "[4/4] Launching Codex with the runbook prompt..."
echo "  Prompt: docs/codex-prompt.md"
echo "  Input:  $INPUT_CSV"
echo "  Output: prospects_2000.jsonl + out/teasers_2000/"
echo ""

# If 'codex' CLI is available, pipe to it; otherwise print instructions
if command -v codex > /dev/null 2>&1; then
    cat docs/codex-prompt.md | codex --workdir "$WORKDIR" --input-csv "$INPUT_CSV"
else
    echo "─────────────────────────────────────────────────────────────────"
    echo "Codex CLI not installed. Manual launch:"
    echo "─────────────────────────────────────────────────────────────────"
    echo ""
    echo "1. Open Codex:    codex"
    echo "2. cd $WORKDIR"
    echo "3. Paste the contents of docs/codex-prompt.md"
    echo "4. Provide $INPUT_CSV as the input"
    echo ""
    echo "Or copy the prompt to clipboard:"
    echo "  pbcopy < docs/codex-prompt.md"
    echo ""
fi
