#!/usr/bin/env bash
# QuantClaw Data — Scrapling Scout Pipeline
# Phase 1: Scout — Grok identifies scrapable financial data sources
# Phase 2: Develop — Cursor Composer 2 builds the module
# Phase 3: Test — Run module, validate output, commit if passing
set -euo pipefail

REPO_DIR="/home/quant/apps/quantclaw-data"
MODULES_DIR="${REPO_DIR}/modules_v2"
LOG="/tmp/quantclaw-scout.log"
XAI_KEY=$(python3 -c "import json; print(json.load(open('/home/quant/.openclaw/workspace/.credentials/xai.json'))['apiKey'])")
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M UTC")
BATCH_SIZE=${1:-3}
BUILT=0
FAILED=0

cd "$REPO_DIR"

log() { echo "$(date -u +%H:%M:%S) $*" | tee -a "$LOG"; }
log "=== Scrapling Scout starting — ${TIMESTAMP} (batch=${BATCH_SIZE}) ==="

EXISTING=$(ls "${MODULES_DIR}"/scrapling_*.py 2>/dev/null | xargs -I{} basename {} .py | sort | tr '\n' ', ')
EXISTING_COUNT=$(ls "${MODULES_DIR}"/scrapling_*.py 2>/dev/null | wc -l)

# ============================
# Phase 1: SCOUT — Find scrapable data sources
# ============================
log "Phase 1: Scouting ${BATCH_SIZE} new web data sources..."

SCOUT_PROMPT="You are a quant data scout. We use Scrapling (Python web scraper) to extract financial data from websites.

EXISTING SCRAPLING MODULES (do NOT duplicate): ${EXISTING}

Find exactly ${BATCH_SIZE} NEW financial websites with server-rendered data (no heavy JS SPAs) that can be scraped for quantitative trading signals. Good targets:
- Government agency statistical pages (BLS, Census, etc.)
- Central bank data pages (rates, reserves, monetary base)
- Shipping/logistics trackers (Baltic Dry Index, port congestion)
- Patent filing databases
- Congressional/political action data
- Commodity spot prices from exchange websites
- Credit default swap spreads
- Insider ownership aggregators
- ETF flow trackers
- Bond yield pages
- Economic indicator dashboards
- Social sentiment aggregators

Requirements per source:
- Must have HTML tables or structured data (not just text paragraphs)
- Must be publicly accessible (no login/paywall)
- Must update at least weekly
- Must provide data useful for trading signals

Output ONLY a JSON array:
[{\"name\": \"scrapling_snake_case\", \"url\": \"https://...\", \"description\": \"what to scrape\", \"selectors_hint\": \"table.class or div#id to target\", \"category\": \"macro|equity|commodities|fx|alt_data|fixed_income|crypto\", \"signal_value\": \"how this feeds trading decisions\"}]

No markdown fences. Real URLs only."

SCOUT_PAYLOAD=$(python3 -c "
import json
print(json.dumps({
    'model': 'grok-3-mini-fast',
    'messages': [{'role': 'user', 'content': '''${SCOUT_PROMPT}'''}],
    'temperature': 0.9,
    'max_tokens': 2000
}))
")

IDEAS_JSON=$(echo "$SCOUT_PAYLOAD" | curl -s --max-time 45 https://api.x.ai/v1/chat/completions \
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

if ! python3 -c "import json,sys; json.loads(sys.stdin.read())" <<< "$IDEAS_JSON" 2>/dev/null; then
  log "ERROR: Failed to parse scout ideas: ${IDEAS_JSON:0:300}"
  exit 1
fi

IDEA_COUNT=$(python3 -c "import json,sys; print(len(json.loads(sys.stdin.read())))" <<< "$IDEAS_JSON")
log "Scout found ${IDEA_COUNT} targets"

# ============================
# Phase 2: DEVELOP — Cursor Composer 2 builds each module
# ============================
for i in $(seq 0 $((IDEA_COUNT - 1))); do
  MODULE_NAME=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read())[$i]['name'])" <<< "$IDEAS_JSON")
  MODULE_DESC=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read())[$i]['description'])" <<< "$IDEAS_JSON")
  MODULE_URL=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read())[$i].get('url',''))" <<< "$IDEAS_JSON")
  MODULE_CAT=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read())[$i].get('category','alt_data'))" <<< "$IDEAS_JSON")
  MODULE_SELECTORS=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read())[$i].get('selectors_hint',''))" <<< "$IDEAS_JSON")
  MODULE_SIGNAL=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read())[$i].get('signal_value',''))" <<< "$IDEAS_JSON")
  TARGET="${MODULES_DIR}/${MODULE_NAME}.py"

  if [ -f "$TARGET" ]; then
    log "SKIP: ${MODULE_NAME} already exists"
    continue
  fi

  CLASS_NAME_DEV=$(python3 -c "print(''.join(w.capitalize() for w in '${MODULE_NAME}'.split('_')))")

  log "Phase 2: Building ${MODULE_NAME} (class: ${CLASS_NAME_DEV}) with Cursor Composer 2..."

  DEVELOP_PROMPT="Build a Scrapling data module: ${MODULE_NAME}

TARGET: ${MODULE_URL}
DESCRIPTION: ${MODULE_DESC}
SELECTORS HINT: ${MODULE_SELECTORS}
CATEGORY: ${MODULE_CAT}
SIGNAL VALUE: ${MODULE_SIGNAL}

Create file: modules_v2/${MODULE_NAME}.py

Follow this EXACT pattern (see modules_v2/scrapling_short_interest.py for reference):
1. Module docstring with Source URL, Cadence, Granularity, Tags
2. sys.path insert for base module import
3. Import from qcd_platform.pipeline.base_module: BaseModule, DataPoint, QualityReport
4. Try import Scrapling: from scrapling import Fetcher (or StealthyFetcher for Cloudflare sites)
5. Class inheriting BaseModule with: name, display_name, cadence, granularity, tags
6. fetch() method: uses Scrapling to GET the URL, parse HTML with css selectors, return List[DataPoint]
7. clean() method: validate/deduplicate bronze data -> silver
8. validate() method: return QualityReport with completeness/timeliness scores

SCRAPLING USAGE:
- Fetcher for simple sites: fetcher = Fetcher(); page = fetcher.get(url)
- StealthyFetcher for Cloudflare: fetcher = StealthyFetcher(); page = fetcher.fetch(url)
- CSS selectors: page.css('table.data tr'), row.css('td::text')
- Attribute access: element.attrib.get('data-value')

After creating the file, TEST it by running:
cd /home/quant/apps/quantclaw-data && python3 -c \"from modules_v2.${MODULE_NAME} import ${CLASS_NAME_DEV}; m = ${CLASS_NAME_DEV}(); pts = m.fetch(); print(f'Fetched {len(pts)} data points'); [print(f'  {p.payload}') for p in pts[:3]]\"

If the test fails, fix the selectors by inspecting the actual HTML and retry."

  RESULT=$(timeout 120 agent --print --trust --yolo --model composer-2 \
    --workspace "$REPO_DIR" \
    "$DEVELOP_PROMPT" 2>&1) || true

  if [ ! -f "$TARGET" ]; then
    log "FAIL: ${MODULE_NAME} — file not created by Composer 2"
    FAILED=$((FAILED + 1))
    continue
  fi

  # ============================
  # Phase 3: TEST — Validate the module actually works
  # ============================
  log "Phase 3: Testing ${MODULE_NAME}..."

  CLASS_NAME=$(python3 -c "
import re
name = '${MODULE_NAME}'
print(''.join(w.capitalize() for w in name.split('_')))
")

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
      log "FAIL: ${MODULE_NAME} — 0 data points (empty scrape)"
      rm -f "$TARGET"
      FAILED=$((FAILED + 1))
    fi
  else
    log "FAIL: ${MODULE_NAME} — ${TEST_RESULT}"
    rm -f "$TARGET"
    FAILED=$((FAILED + 1))
  fi

  sleep 3
done

if [ $BUILT -eq 0 ]; then
  log "No modules built this cycle, skipping commit"
  log "=== Scrapling Scout done: ${BUILT} built, ${FAILED} failed ==="
  exit 0
fi

# ============================
# Phase 4: COMMIT + PUSH
# ============================
MODULES_AFTER=$(ls "${MODULES_DIR}"/scrapling_*.py 2>/dev/null | wc -l)

git add "${MODULES_DIR}"/scrapling_*.py
git commit -m "scout: +${BUILT} scrapling modules (${EXISTING_COUNT}→${MODULES_AFTER}) — ${TIMESTAMP}" || true
git push --no-verify origin main 2>&1 | tail -2 || log "WARN: git push failed"

log "=== Scrapling Scout done: ${BUILT} built, ${FAILED} failed, ${MODULES_AFTER} total scrapling modules ==="
