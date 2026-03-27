#!/usr/bin/env bash
# QuantClaw Data — Nightly Composer 2 Builder
# Replaces old NightBuilder. Uses Grok for scouting + Cursor Composer 2 for development.
# Builds modules_v2/ (BaseModule pipeline-compatible), not legacy modules/.
set -euo pipefail

REPO_DIR="/home/quant/apps/quantclaw-data"
MODULES_DIR="${REPO_DIR}/modules_v2"
LOG="/tmp/quantclaw-nightly-c2.log"
XAI_KEY=$(python3 -c "import json; print(json.load(open('/home/quant/.openclaw/workspace/.credentials/xai.json'))['apiKey'])")
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M UTC")
BATCH_SIZE=${1:-10}
BUILT=0
FAILED=0
SKIPPED=0
MAX_BUILD_TIME=180

cd "$REPO_DIR"

log() { echo "$(date -u +%H:%M:%S) $*" | tee -a "$LOG"; }
log "=== Nightly Composer 2 starting — ${TIMESTAMP} (batch=${BATCH_SIZE}) ==="

EXISTING_V2=$(ls "${MODULES_DIR}"/*.py 2>/dev/null | xargs -I{} basename {} .py | sort | tr '\n' ', ')
EXISTING_V1=$(ls modules/*.py 2>/dev/null | xargs -I{} basename {} .py | sort | tr '\n' ', ')
EXISTING_V2_COUNT=$(ls "${MODULES_DIR}"/*.py 2>/dev/null | wc -l)

# ============================
# Phase 1: SCOUT — Grok finds data sources (APIs + scrapable sites)
# ============================
log "Phase 1: Scouting ${BATCH_SIZE} new data sources..."

SCOUT_PROMPT="You are a quant data module architect. We have a data platform with ${EXISTING_V2_COUNT} v2 modules.

EXISTING V2 MODULES (do NOT duplicate): ${EXISTING_V2}
EXISTING V1 MODULES (also avoid): ${EXISTING_V1:0:3000}

Find exactly ${BATCH_SIZE} NEW data sources for quantitative trading. Mix of:
- REST APIs (free, no auth or free tier key)
- Server-rendered websites with tables/structured data (scrapable)
- Government/institutional data portals

Good targets:
- Central bank data (rates, reserves, money supply, FX intervention)
- Commodity exchanges (LME, CME settlement, ICE)
- Government statistics (BLS, Census, Eurostat, OECD, IMF)
- Shipping/logistics (AIS, port data, container rates)
- Credit/bond markets (spreads, CDS, yield curves)
- Alternative data (patent filings, job postings, app downloads, web traffic)
- Crypto on-chain (mempool, gas, whale movements)
- Earnings/SEC filings (8-K, 10-Q parser)
- Social/sentiment aggregators
- ETF flows and fund positioning
- Volatility surfaces and options data
- FX carry, rate differentials

Requirements:
- Must be publicly accessible (no login/paywall)
- Must update at least weekly
- Must provide data useful for trading signals
- For websites: must have HTML tables or structured data
- For APIs: must return JSON and not require paid keys

Output ONLY a JSON array — no markdown fences, no explanation:
[{\"name\": \"snake_case_name\", \"type\": \"api|scrape\", \"url\": \"https://...\", \"description\": \"what to extract\", \"category\": \"macro|equity|commodities|fx|alt_data|fixed_income|crypto|derivatives\", \"signal_value\": \"how this feeds trading decisions\", \"selectors_hint\": \"CSS selectors or API endpoint path\"}]"

SCOUT_PAYLOAD=$(python3 -c "
import json, sys
print(json.dumps({
    'model': 'grok-3-mini-fast',
    'messages': [{'role': 'user', 'content': sys.stdin.read()}],
    'temperature': 0.95,
    'max_tokens': 3000
}))
" <<< "$SCOUT_PROMPT")

SCOUT_RESPONSE=$(echo "$SCOUT_PAYLOAD" | curl -s --max-time 60 https://api.x.ai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_KEY" \
  -d @- | python3 -c "
import sys, json
r = json.load(sys.stdin)
content = r.get('choices', [{}])[0].get('message', {}).get('content', '')
content = content.strip()
if content.startswith('\`\`\`'):
    content = content.split('\n', 1)[1] if '\n' in content else content[3:]
if content.endswith('\`\`\`'):
    content = content[:content.rfind('\`\`\`')]
print(content.strip())
")

if ! python3 -c "import json,sys; json.loads(sys.stdin.read())" <<< "$SCOUT_RESPONSE" 2>/dev/null; then
  log "ERROR: Failed to parse scout response: ${SCOUT_RESPONSE:0:300}"
  exit 1
fi

IDEA_COUNT=$(python3 -c "import json,sys; print(len(json.loads(sys.stdin.read())))" <<< "$SCOUT_RESPONSE")
log "Scout found ${IDEA_COUNT} targets"

# ============================
# Phase 2+3: BUILD + TEST each module with Composer 2
# ============================
for i in $(seq 0 $((IDEA_COUNT - 1))); do
  IDEA=$(python3 -c "import json,sys; print(json.dumps(json.loads(sys.stdin.read())[$i]))" <<< "$SCOUT_RESPONSE")
  MODULE_NAME=$(python3 -c "import json; print(json.loads('$IDEA')['name'])")
  MODULE_TYPE=$(python3 -c "import json; print(json.loads('$IDEA').get('type','api'))")
  MODULE_URL=$(python3 -c "import json; print(json.loads('$IDEA').get('url',''))")
  MODULE_DESC=$(python3 -c "import json; print(json.loads('$IDEA').get('description',''))")
  MODULE_CAT=$(python3 -c "import json; print(json.loads('$IDEA').get('category','alt_data'))")
  MODULE_SELECTORS=$(python3 -c "import json; print(json.loads('$IDEA').get('selectors_hint',''))")
  MODULE_SIGNAL=$(python3 -c "import json; print(json.loads('$IDEA').get('signal_value',''))")
  TARGET="${MODULES_DIR}/${MODULE_NAME}.py"

  if [ -f "$TARGET" ]; then
    log "SKIP: ${MODULE_NAME} already exists"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  if [ -f "modules/${MODULE_NAME}.py" ]; then
    log "SKIP: ${MODULE_NAME} exists in V1"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  CLASS_NAME=$(python3 -c "print(''.join(w.capitalize() for w in '${MODULE_NAME}'.split('_')))")

  log "Phase 2: Building ${MODULE_NAME} (${MODULE_TYPE}, ${MODULE_CAT}) with Composer 2..."

  if [ "$MODULE_TYPE" = "scrape" ]; then
    FETCHER_GUIDE="SCRAPLING USAGE:
- from scrapling import Fetcher (simple sites) or StealthyFetcher (Cloudflare/JS)
- Fetcher: page = Fetcher().get(url, headers={'User-Agent': '...'})
- StealthyFetcher: page = StealthyFetcher().fetch(url)
- CSS selectors: page.css('table tr'), row.css('td::text')
- Try import with fallback: try: from scrapling import Fetcher; except: Fetcher = None"
  else
    FETCHER_GUIDE="HTTP USAGE:
- import requests
- Use requests.get(url, timeout=15, headers={'User-Agent': '...'})
- Handle resp.raise_for_status() in try/except
- Parse JSON: resp.json() or HTML with scrapling if needed"
  fi

  DEVELOP_PROMPT="Build a QuantClaw Data v2 module: ${MODULE_NAME}

TARGET: ${MODULE_URL}
DESCRIPTION: ${MODULE_DESC}
CATEGORY: ${MODULE_CAT}
TYPE: ${MODULE_TYPE}
SELECTORS: ${MODULE_SELECTORS}
SIGNAL VALUE: ${MODULE_SIGNAL}

Create file: modules_v2/${MODULE_NAME}.py

Follow this EXACT pattern (see modules_v2/scrapling_short_interest.py for reference):

1. Module docstring with Source URL, Cadence, Granularity, Tags
2. sys.path insert for base module import:
   sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
3. Import: from qcd_platform.pipeline.base_module import BaseModule, DataPoint, QualityReport
4. ${FETCHER_GUIDE}
5. Class ${CLASS_NAME} inheriting BaseModule with: name='${MODULE_NAME}', display_name, cadence, granularity, tags
6. fetch() method: fetches data, returns List[DataPoint]. Each DataPoint(symbol=str, timestamp=datetime, payload=dict, source='${MODULE_NAME}')
7. clean() method: validate/deduplicate bronze data -> silver
8. validate() method: return QualityReport with completeness/timeliness scores

CRITICAL:
- Return DataPoint objects, not raw dicts
- Always handle network errors gracefully (return empty list on failure)
- Use real URLs that actually serve data
- datetime.now(timezone.utc) for timestamps

After creating the file, TEST it:
cd /home/quant/apps/quantclaw-data && python3 -c \"
import sys; sys.path.insert(0, '.')
from modules_v2.${MODULE_NAME} import ${CLASS_NAME}
m = ${CLASS_NAME}()
pts = m.fetch()
print(f'Fetched {len(pts)} data points')
for p in pts[:3]:
    print(f'  {p.symbol}: {p.payload}')
\"

If the test fails (network error, wrong selectors, import error), diagnose and fix. Try alternative URLs if the primary one doesn't work."

  RESULT=$(timeout ${MAX_BUILD_TIME} agent --print --trust --yolo --model composer-2 \
    --workspace "$REPO_DIR" \
    "$DEVELOP_PROMPT" 2>&1) || true

  if [ ! -f "$TARGET" ]; then
    log "FAIL: ${MODULE_NAME} — file not created by Composer 2"
    FAILED=$((FAILED + 1))
    continue
  fi

  # Phase 3: Independent test
  log "Phase 3: Testing ${MODULE_NAME}..."

  TEST_RESULT=$(timeout 60 python3 -c "
import sys
sys.path.insert(0, '${REPO_DIR}')
try:
    mod = __import__('modules_v2.${MODULE_NAME}', fromlist=['${CLASS_NAME}'])
    cls = getattr(mod, '${CLASS_NAME}')
    m = cls()
    pts = m.fetch()
    print(f'OK:{len(pts)}')
except Exception as e:
    print(f'FAIL:{e}')
" 2>&1) || TEST_RESULT="FAIL:timeout"

  if echo "$TEST_RESULT" | grep -q "^OK:"; then
    POINTS=$(echo "$TEST_RESULT" | sed -n 's/^OK:\([0-9]*\)/\1/p' | head -1)
    POINTS=${POINTS:-0}
    if [ "$POINTS" -gt 0 ] 2>/dev/null; then
      BUILT=$((BUILT + 1))
      log "OK: ${MODULE_NAME} — ${POINTS} data points"
    else
      log "FAIL: ${MODULE_NAME} — 0 data points (empty result)"
      rm -f "$TARGET"
      FAILED=$((FAILED + 1))
    fi
  else
    log "FAIL: ${MODULE_NAME} — ${TEST_RESULT}"
    rm -f "$TARGET"
    FAILED=$((FAILED + 1))
  fi

  sleep 2
done

if [ $BUILT -eq 0 ]; then
  log "No modules built this cycle, skipping commit"
  log "=== Nightly Composer 2 done: ${BUILT} built, ${FAILED} failed, ${SKIPPED} skipped ==="
  exit 0
fi

# ============================
# Phase 4: VERSION BUMP + COMMIT + PUSH
# ============================
MODULES_V2_AFTER=$(ls "${MODULES_DIR}"/*.py 2>/dev/null | wc -l)

git add "${MODULES_DIR}"/*.py
git commit -m "nightly-c2: +${BUILT} modules (${EXISTING_V2_COUNT}→${MODULES_V2_AFTER}) — ${TIMESTAMP}" || true
git push --no-verify origin main 2>&1 | tail -2 || log "WARN: git push failed"

log "=== Nightly Composer 2 done: ${BUILT} built, ${FAILED} failed, ${SKIPPED} skipped, ${MODULES_V2_AFTER} total v2 modules ==="
