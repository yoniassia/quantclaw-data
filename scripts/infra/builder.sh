#!/usr/bin/env bash
# QuantClaw Data — NightBuilder
# Builds 5 new modules per cycle using AI, validates them,
# bumps version, updates README stats, commits + pushes to GitHub.
set -euo pipefail

REPO_DIR="/home/quant/apps/quantclaw-data"
SCRIPTS_DIR="${REPO_DIR}/scripts"
LOG="/tmp/quantclaw-builder.log"
XAI_KEY=$(python3 -c "import json; print(json.load(open('/home/quant/.openclaw/workspace/.credentials/xai.json'))['apiKey'])")
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M UTC")
BATCH_SIZE=5
BUILT=0
FAILED=0

cd "$REPO_DIR"

log() { echo "$(date -u +%H:%M:%S) $*" | tee -a "$LOG"; }
log "=== NightBuilder starting — ${TIMESTAMP} ==="

MODULE_COUNT_BEFORE=$(ls modules/*.py 2>/dev/null | wc -l)

# --- Phase 1: Pick module ideas ---
EXISTING=$(ls modules/*.py 2>/dev/null | xargs -I{} basename {} .py | sort | tr '\n' ', ')

python3 -c "
import json
prompt = '''You are a financial data module architect. We have ${MODULE_COUNT_BEFORE} modules already.

EXISTING (abbreviated): ${EXISTING:0:2000}

Generate exactly ${BATCH_SIZE} NEW module ideas. Each must:
- Use a REAL, FREE, public financial data API (no paid keys or fake URLs)
- NOT duplicate any existing module
- Cover diverse categories (macro, equity, commodities, crypto, alt-data, etc.)

Output ONLY a JSON array of objects:
[{\"name\": \"snake_case_name\", \"api_url\": \"https://...\", \"description\": \"what it does\", \"category\": \"macro|equity|crypto|commodities|fx|alt_data|quant|derivatives|fixed_income|ml_ai\"}]

No markdown fences, no explanation — just the JSON array.'''

print(json.dumps({
    'model': 'grok-3-mini-fast',
    'messages': [{'role': 'user', 'content': prompt}],
    'temperature': 0.9,
    'max_tokens': 1500
}))
" > /tmp/qcd_ideas_payload.json

IDEAS_JSON=$(curl -s --max-time 45 https://api.x.ai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_KEY" \
  -d @/tmp/qcd_ideas_payload.json | python3 "${SCRIPTS_DIR}/strip_fences.py")

if ! python3 -c "import json,sys; json.loads(sys.stdin.read())" <<< "$IDEAS_JSON" 2>/dev/null; then
  log "ERROR: Failed to parse module ideas JSON: ${IDEAS_JSON:0:200}"
  exit 1
fi

IDEA_COUNT=$(python3 -c "import json,sys; print(len(json.loads(sys.stdin.read())))" <<< "$IDEAS_JSON")
log "Got ${IDEA_COUNT} module ideas"

# --- Phase 2: Build each module ---
for i in $(seq 0 $((IDEA_COUNT - 1))); do
  MODULE_NAME=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read())[$i]['name'])" <<< "$IDEAS_JSON")
  MODULE_DESC=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read())[$i]['description'])" <<< "$IDEAS_JSON")
  MODULE_URL=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read())[$i].get('api_url',''))" <<< "$IDEAS_JSON")
  MODULE_CAT=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read())[$i].get('category','other'))" <<< "$IDEAS_JSON")
  TARGET="modules/${MODULE_NAME}.py"

  if [ -f "$TARGET" ]; then
    log "SKIP: ${MODULE_NAME} already exists"
    continue
  fi

  log "Building: ${MODULE_NAME} (${MODULE_CAT})"

  python3 << PYEOF > /tmp/qcd_build_payload.json
import json

prompt = """Write a complete Python module for QuantClaw Data: '${MODULE_NAME}'.

PURPOSE: ${MODULE_DESC}
API/SOURCE: ${MODULE_URL}
CATEGORY: ${MODULE_CAT}

REQUIREMENTS:
1. Start with #!/usr/bin/env python3
2. Module docstring with Data Source URL, Update frequency, Auth info
3. At least 5 well-typed functions with docstrings (return dicts/lists, never just print)
4. Use requests for HTTP. Handle errors with try/except returning error dicts.
5. Include a main() function that demos 2-3 key functions
6. NO paid API keys — free tiers, demo keys, or public endpoints only
7. Cache responses in /home/quant/apps/quantclaw-data/cache/${MODULE_NAME}/ with 1h TTL
8. Standard cache helper pattern:

import requests, os, json, time
from pathlib import Path

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/${MODULE_NAME}')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600

def _cached_get(url, cache_key, params=None, headers=None):
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return json.loads(cache_file.read_text())
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    cache_file.write_text(json.dumps(data, indent=2))
    return data

Output ONLY the complete Python code. No markdown fences, no explanation text before or after."""

print(json.dumps({
    "model": "grok-3-mini-fast",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.3,
    "max_tokens": 4000
}))
PYEOF

  MODULE_CODE=$(curl -s --max-time 90 https://api.x.ai/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $XAI_KEY" \
    -d @/tmp/qcd_build_payload.json | python3 "${SCRIPTS_DIR}/strip_fences.py")

  if [ -z "$MODULE_CODE" ] || [ ${#MODULE_CODE} -lt 200 ]; then
    log "FAIL: ${MODULE_NAME} — empty or too short (${#MODULE_CODE} chars)"
    FAILED=$((FAILED + 1))
    continue
  fi

  echo "$MODULE_CODE" > "$TARGET"

  # Static + AST validation only (skip import to avoid sys.path issues)
  VALIDATION=$(python3 -c "
import sys; sys.path.insert(0, '.')
from scripts.validate_module import validate
r = validate('$TARGET', do_import=False)
status = 'PASS' if r['pass'] else 'FAIL'
issues = []
for layer, ii in r['layers'].items():
    issues.extend(ii)
print(f'{status}: {\" | \".join(issues) if issues else \"clean\"}')" 2>&1 || echo "FAIL: script error")
  if echo "$VALIDATION" | grep -q "^FAIL"; then
    log "FAIL: ${MODULE_NAME} — ${VALIDATION}"
    rm -f "$TARGET"
    FAILED=$((FAILED + 1))
    continue
  fi

  BUILT=$((BUILT + 1))
  log "OK: ${MODULE_NAME} — built and validated"
  sleep 2
done

if [ $BUILT -eq 0 ]; then
  log "No modules built this cycle, skipping commit"
  exit 0
fi

# --- Phase 3: Bump version ---
MODULE_COUNT_AFTER=$(ls modules/*.py 2>/dev/null | wc -l)
TOTAL_LOC=$(wc -l modules/*.py 2>/dev/null | tail -1 | awk '{print $1}')
DATA_SOURCES=$(grep -roh 'https://[a-zA-Z0-9._/-]*' modules/*.py 2>/dev/null | awk -F/ '{print $3}' | sort -u | wc -l || echo "0")

python3 << PYEOF
import json
p = json.load(open("package.json"))
v = p["version"].split(".")
v[2] = str(int(v[2]) + ${BUILT})
p["version"] = ".".join(v)
json.dump(p, open("package.json", "w"), indent=2)
print(f"Version: {'.'.join(v)}")
PYEOF

NEW_VERSION=$(python3 -c "import json; print(json.load(open('package.json'))['version'])")
log "Version bumped to ${NEW_VERSION}"

# --- Phase 4: Update README ---
python3 << PYEOF
import re
from pathlib import Path

readme = Path("README.md")
if not readme.exists():
    exit(0)

text = readme.read_text()
mc = ${MODULE_COUNT_AFTER}
loc = ${TOTAL_LOC}
ds = ${DATA_SOURCES}

text = re.sub(r'(\*\*Python Modules\*\*\s*\|\s*)\d+', f'\\1{mc}', text)
text = re.sub(r'(\*\*Lines of Code\*\*\s*\|\s*)[\d,]+\+?', f'\\1{loc:,}+', text)
text = re.sub(r'(\*\*Data Source Domains\*\*\s*\|\s*)\d+', f'\\1{ds}', text)

readme.write_text(text)
print(f"README: {mc} modules, {loc:,}+ LOC, {ds} sources")
PYEOF

# --- Phase 5: Regenerate index ---
python3 scripts/infra/generate_index.py 2>/dev/null || log "WARN: index generation failed"

# --- Phase 6: Git commit + push ---
git add -A
git commit -m "build: +${BUILT} modules (${MODULE_COUNT_BEFORE}→${MODULE_COUNT_AFTER}) v${NEW_VERSION} — ${TIMESTAMP}" || true
git push origin main 2>&1 | tail -2 || log "WARN: git push failed"

log "=== NightBuilder done: ${BUILT} built, ${FAILED} failed, ${MODULE_COUNT_AFTER} total, v${NEW_VERSION} ==="
