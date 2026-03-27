#!/usr/bin/env bash
# QuantClaw Data — Tester
# Validates 10 random modules (static + AST) and checks 5 API routes.
set -euo pipefail

REPO_DIR="/home/quant/apps/quantclaw-data"
LOG="/tmp/quantclaw-tester.log"
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M UTC")
SAMPLE_SIZE=10
ROUTE_CHECKS=5

cd "$REPO_DIR"

log() { echo "$(date -u +%H:%M:%S) $*" | tee -a "$LOG"; }
log "=== Tester starting — ${TIMESTAMP} ==="

# --- Phase 1: Validate random modules ---
TOTAL=$(ls modules/*.py 2>/dev/null | wc -l)
PASSED=0
FAILED=0
CRITICALS=""

for MOD in $(ls modules/*.py | shuf -n $SAMPLE_SIZE); do
  NAME=$(basename "$MOD" .py)
  RESULT=$(python3 scripts/tests/validate_module.py "$MOD" 2>&1 || true)

  if echo "$RESULT" | grep -q "FAIL"; then
    FAILED=$((FAILED + 1))
    CRITICALS="${CRITICALS}\n  ❌ ${NAME}: $(echo "$RESULT" | grep CRITICAL | head -1)"
    log "FAIL: ${NAME}"
  else
    PASSED=$((PASSED + 1))
  fi
done

log "Validation: ${PASSED}/${SAMPLE_SIZE} passed, ${FAILED} failed (${TOTAL} total modules)"

# --- Phase 2: Check API routes (if server is running) ---
PORT=3055
ROUTES_OK=0
ROUTES_FAIL=0

if curl -s --max-time 3 "http://localhost:${PORT}" > /dev/null 2>&1; then
  ROUTES=$(curl -s --max-time 5 "http://localhost:${PORT}/api/modules" 2>/dev/null | \
    python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    routes = data if isinstance(data, list) else data.get('modules', data.get('routes', []))
    import random
    sample = random.sample(routes, min(${ROUTE_CHECKS}, len(routes))) if routes else []
    for r in sample:
        name = r if isinstance(r, str) else r.get('name', r.get('route', ''))
        print(name)
except: pass
" 2>/dev/null)

  if [ -n "$ROUTES" ]; then
    while IFS= read -r route; do
      [ -z "$route" ] && continue
      STATUS=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "http://localhost:${PORT}/api/modules/${route}" 2>/dev/null || echo "000")
      if [ "$STATUS" = "200" ]; then
        ROUTES_OK=$((ROUTES_OK + 1))
      else
        ROUTES_FAIL=$((ROUTES_FAIL + 1))
        log "ROUTE FAIL: /api/modules/${route} → HTTP ${STATUS}"
      fi
    done <<< "$ROUTES"
    log "Routes: ${ROUTES_OK}/${ROUTE_CHECKS} OK"
  else
    log "No routes to test (modules endpoint returned empty)"
  fi
else
  log "Server not running on port ${PORT} — skipping route checks"
fi

# --- Phase 3: Write summary ---
SUMMARY="Tester ${TIMESTAMP}: modules ${PASSED}/${SAMPLE_SIZE} pass, routes ${ROUTES_OK}/${ROUTE_CHECKS} ok"
if [ $FAILED -gt 0 ]; then
  SUMMARY="${SUMMARY} — ${FAILED} FAILURES:${CRITICALS}"
fi

log "$SUMMARY"
log "=== Tester done ==="
