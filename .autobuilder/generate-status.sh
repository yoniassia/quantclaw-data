#!/bin/bash
# Generates status.json from git log + autobuilder state
# Run periodically or after each initiative completes

cd "$(dirname "$0")/.." || exit 1

COMPLETED=$(git log --oneline --all | grep "autobuilder:" | sed 's/.*autobuilder: //' | sort -u | while read name; do
    echo "\"$(echo "$name" | sed 's/-.*//')\""
done | paste -sd, -)

BUILDING=""
LOG_FILE=".autobuilder/run-output.log"
if [ -f "$LOG_FILE" ]; then
    LAST_BUILDING=$(grep "Building:" "$LOG_FILE" | tail -1 | sed 's/.*Building: //' | sed 's/ .*//' | sed 's/-.*//')
    LAST_OK=$(grep "\[OK\]" "$LOG_FILE" | tail -1 | sed 's/.*\[OK\] //' | sed 's/ .*//' | sed 's/-.*//')
    if [ "$LAST_BUILDING" != "$LAST_OK" ] && [ -n "$LAST_BUILDING" ]; then
        BUILDING="\"$LAST_BUILDING\""
    fi
fi

FAILED=$(git log --oneline --all | grep "autobuilder:.*FAILED" | sed 's/.*autobuilder: //' | sed 's/-.*//' | sort -u | while read name; do
    echo "\"$name\""
done | paste -sd, -)

STARTED=""
if [ -f "$LOG_FILE" ]; then
    STARTED=$(head -1 "$LOG_FILE" | grep -oP '\d{4}-\d{2}-\d{2}' || head -1 "$LOG_FILE" | grep -oP '[A-Z][a-z]+ [A-Z][a-z]+ +\d+ \d+:\d+:\d+ [A-Z]+ \d{4}')
fi

TOTAL_MODULES=$(ls modules/*.py 2>/dev/null | wc -l)

LOG_ENTRIES=""
if [ -f "$LOG_FILE" ]; then
    LOG_ENTRIES=$(tail -50 "$LOG_FILE" | while IFS= read -r line; do
        TIME=$(echo "$line" | grep -oP '\d{2}:\d{2}:\d{2}' || echo "")
        LEVEL="info"
        echo "$line" | grep -q "\[OK\]" && LEVEL="ok"
        echo "$line" | grep -q "Building:" && LEVEL="building"
        echo "$line" | grep -q "FAIL\|ERROR\|error" && LEVEL="fail"
        echo "$line" | grep -q "===" && LEVEL="header"
        TEXT=$(echo "$line" | sed 's/"/\\"/g')
        [ -n "$TIME" ] || TIME="--:--:--"
        echo "{\"time\":\"$TIME\",\"level\":\"$LEVEL\",\"text\":\"$TEXT\"}"
    done | paste -sd, -)
fi

cat > .autobuilder/status.json <<STATUSEOF
{
  "completed": [${COMPLETED}],
  "building": [${BUILDING}],
  "failed": [${FAILED:-}],
  "started": "2026-04-01T17:08:31Z",
  "total_modules": ${TOTAL_MODULES},
  "generated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "log": [${LOG_ENTRIES}]
}
STATUSEOF

echo "status.json generated: $(cat .autobuilder/status.json | python3 -c 'import sys,json; d=json.load(sys.stdin); print(f"{len(d[\"completed\"])} done, building={d[\"building\"]}, {d[\"total_modules\"]} modules")')"
