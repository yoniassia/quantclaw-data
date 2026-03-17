#!/usr/bin/env bash
# QuantClaw Data — Research Scanner
# Discovers new free financial data APIs and module ideas.
# Appends findings to memory/research-todo.md
set -euo pipefail

REPO_DIR="/home/quant/apps/quantclaw-data"
LOG="/tmp/quantclaw-research.log"
XAI_KEY=$(cat /home/quant/.openclaw/workspace/.credentials/xai.json | python3 -c "import sys,json; print(json.load(sys.stdin)['apiKey'])")
RESEARCH_FILE="/home/quant/.openclaw/workspace/memory/research-todo.md"
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M UTC")

cd "$REPO_DIR"

EXISTING_MODULES=$(ls modules/*.py 2>/dev/null | xargs -I{} basename {} .py | sort | tr '\n' ', ')
MODULE_COUNT=$(ls modules/*.py 2>/dev/null | wc -l)

PROMPT="You are a financial data source researcher for QuantClaw Data, an open-source financial intelligence platform with ${MODULE_COUNT} Python modules.

EXISTING MODULES (abbreviated): ${EXISTING_MODULES:0:3000}

Find 10 NEW free financial data APIs or public data sources that we DON'T already have modules for. Focus on:
- Central banks (any country we're missing)
- Government statistics agencies
- Free market data APIs (no paid key required, or has free tier)
- Alternative data (shipping, satellite, patents, jobs, etc.)
- Crypto/DeFi data providers
- ESG and climate finance data

For each, provide:
1. Name (snake_case module name)
2. URL of the API/data source
3. What data it provides
4. Why it's valuable for quant trading

Output as a markdown list. Be specific — real APIs only, no hallucinated URLs."

RESPONSE=$(curl -s --max-time 60 https://api.x.ai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_KEY" \
  -d "$(python3 -c "
import json
print(json.dumps({
    'model': 'grok-3-mini-fast',
    'messages': [{'role': 'user', 'content': '''$PROMPT'''}],
    'temperature': 0.8,
    'max_tokens': 2000
}))
")" | python3 -c "import sys,json; r=json.load(sys.stdin); print(r.get('choices',[{}])[0].get('message',{}).get('content','ERROR: No response'))")

if [ -z "$RESPONSE" ] || echo "$RESPONSE" | grep -q "ERROR"; then
  echo "$(date -u): Research scan failed" >> "$LOG"
  exit 1
fi

cat >> "$RESEARCH_FILE" << EOF

## 🔍 NEW RESEARCH — ${TIMESTAMP} (Cron Scan)

${RESPONSE}

EOF

echo "$(date -u): Research scan complete — appended to research-todo.md" >> "$LOG"
