#!/bin/bash
set -euo pipefail

cd /home/quant/apps/quantclaw-data

LOG=".autobuilder/run.log"
OUTPUT_LOG=".autobuilder/run-output.log"
INIT_DIR=".autobuilder/initiatives"
SCOPE=".autobuilder/scope.md"
COMPLETED=0
FAILED=0
SKIPPED=0
EXPAND_EVERY=11
UPDATE_EVERY=4
WHATSAPP_GROUP="120363423165669711@g.us"

echo "=== QuantClaw AutoBuilder Started: $(date -u) ===" | tee "$OUTPUT_LOG" "$LOG"

run_initiative() {
  local file="$1"
  local name
  name=$(basename "$file" .md)

  if git log --oneline | grep -q "autobuilder: $name"; then
    echo "[SKIP] $name — already committed" | tee -a "$OUTPUT_LOG" "$LOG"
    SKIPPED=$((SKIPPED + 1))
    return 0
  fi

  echo "" | tee -a "$OUTPUT_LOG" "$LOG"
  echo "=== [$((COMPLETED + FAILED + SKIPPED + 1))] Building: $name — $(date -u) ===" | tee -a "$OUTPUT_LOG" "$LOG"

  local prompt
  prompt="You are the QuantClaw AutoBuilder. Build ONE data module for quantclaw-data.

RULES (CRITICAL):
- NEVER modify mcp_server.py, api_server.py, or any existing module
- ONLY create NEW files in modules/
- Follow the exact module pattern from .autobuilder/scope.md

STEPS:
1. Read .autobuilder/scope.md for the module pattern and rules
2. Read .autobuilder/initiatives/${name}.md for this specific initiative
3. Build the module in modules/ following the pattern exactly
4. Test it: run python3 modules/<your_new_module>.py and verify it returns real data
5. VALIDATE: Check that returned data has actual values (not empty, not None, not error)
6. If the API returns errors, try alternative endpoints from the initiative doc
7. If still failing, document what works/doesn't in the module docstring
8. Git add ONLY your new module file(s) and commit: \"autobuilder: ${name}\"

VALIDATION CHECKLIST (must pass before committing):
- Module runs without exceptions
- Returns JSON with real data points (dates, numbers, not placeholders)
- At least one indicator returns live data
- Error handling works (try invalid input, should return graceful error)"

  if timeout 300 cursor agent --print --force "$prompt" >> "$LOG" 2>&1; then
    if git log -1 --oneline | grep -q "$name"; then
      echo "[OK] $name — committed successfully" | tee -a "$OUTPUT_LOG" "$LOG"
      COMPLETED=$((COMPLETED + 1))
    else
      echo "[WARN] $name — cursor ran but no commit found" | tee -a "$OUTPUT_LOG" "$LOG"
      FAILED=$((FAILED + 1))
    fi
  else
    echo "[FAIL] $name — cursor agent failed or timed out" | tee -a "$OUTPUT_LOG" "$LOG"
    FAILED=$((FAILED + 1))
  fi

  bash .autobuilder/generate-status.sh 2>/dev/null || true
  sleep 3
}

update_docs_and_push() {
  local batch="$1"
  echo "" | tee -a "$OUTPUT_LOG" "$LOG"
  echo "=== DOCS UPDATE + PUSH (after $COMPLETED modules) — $(date -u) ===" | tee -a "$OUTPUT_LOG" "$LOG"

  local new_modules
  new_modules=$(git log --oneline | grep "autobuilder:" | sed 's/.*autobuilder: //' | paste -sd', ' -)

  local total_modules
  total_modules=$(ls modules/*.py 2>/dev/null | wc -l)

  local update_prompt
  update_prompt="You are updating QuantClaw Data documentation after new autobuilder modules were added.

NEW MODULES ADDED: ${new_modules}
TOTAL MODULES NOW: ${total_modules}

TASKS:
1. Read the current README.md
2. Update the module count numbers throughout README.md to reflect ${total_modules} total modules
3. List the new autobuilder modules in the appropriate category sections
4. Read modules/ to see all new autobuilder-created files (they start with government/central bank names)
5. For each new module, check what indicators it provides and add them to the README's data catalog
6. Update the 'Data Sources & API Keys' section with new government sources
7. Create/update docs/API_CATALOG.md with a comprehensive list of ALL data endpoints including new ones
8. Git add README.md and docs/API_CATALOG.md and commit: \"docs: update API catalog + README — batch ${batch} (${COMPLETED} modules)\"

RULES:
- Keep existing README structure intact
- Add new modules to existing category tables/lists
- Be thorough — list every new endpoint, indicator, and data source
- Include usage examples for new government data modules"

  if timeout 300 cursor agent --print --force "$update_prompt" >> "$LOG" 2>&1; then
    echo "[OK] Docs updated — batch $batch" | tee -a "$OUTPUT_LOG" "$LOG"
  else
    echo "[WARN] Docs update failed — batch $batch — continuing" | tee -a "$OUTPUT_LOG" "$LOG"
  fi

  echo "--- Pushing to GitHub ---" | tee -a "$OUTPUT_LOG" "$LOG"
  if git push origin HEAD 2>> "$LOG"; then
    echo "[OK] Pushed to GitHub" | tee -a "$OUTPUT_LOG" "$LOG"
  else
    echo "[WARN] Git push failed" | tee -a "$OUTPUT_LOG" "$LOG"
  fi

  bash .autobuilder/generate-status.sh 2>/dev/null || true

  local completed_list
  completed_list=$(git log --oneline | grep "autobuilder:" | head -"$COMPLETED" | sed 's/.*autobuilder: //' | while read n; do echo "- $n"; done)

  local msg
  msg="*AutoBuilder Progress Update — Batch ${batch}*

✅ *${COMPLETED} modules built* | ❌ ${FAILED} failed | ⏭️ ${SKIPPED} skipped
📦 Total modules: ${total_modules}

*New modules this batch:*
${completed_list}

📊 Dashboard: http://srv1340294:3063/dashboard.html
🗺️ Roadmap: http://srv1340294:3063/roadmap.html
📝 README + API catalog updated and pushed to GitHub

_AutoBuilder continuing..._"

  # Post update to WhatsApp via openclaw message tool file
  echo "$msg" > /tmp/autobuilder-update-batch-${batch}.txt
  echo "[INFO] WhatsApp update saved to /tmp/autobuilder-update-batch-${batch}.txt" | tee -a "$OUTPUT_LOG" "$LOG"
}

generate_new_initiatives() {
  local batch_num="$1"
  echo "" | tee -a "$OUTPUT_LOG" "$LOG"
  echo "=== GENERATING NEW INITIATIVES (batch $batch_num) — $(date -u) ===" | tee -a "$OUTPUT_LOG" "$LOG"

  local next_num
  next_num=$(ls "$INIT_DIR"/*.md 2>/dev/null | wc -l)
  next_num=$((next_num + 1))
  local padded
  padded=$(printf "%04d" "$next_num")

  local prompt
  prompt="You are the QuantClaw AutoBuilder initiative generator.

Read .autobuilder/scope.md and ls modules/ to see what already exists.
Also read .autobuilder/initiatives/ to see all existing initiatives.

Generate 5 NEW initiative PRDs for data sources NOT yet covered. Focus on:
- Government data portals we missed (any country)
- Niche but valuable financial data APIs (free tier)
- Alternative data sources (shipping, satellite, social, patents)
- Enhanced coverage for existing sources (new endpoints/datasets)

For each, create a file .autobuilder/initiatives/${padded}-<name>.md (increment number for each).

Follow the same PRD format as existing initiatives. Each must have:
- Clear title and description
- API endpoint URLs (verified real)
- Key indicators to fetch
- Module filename
- Test commands

Git add and commit: \"autobuilder: generate batch-${batch_num} new initiatives\""

  if timeout 300 cursor agent --print --force "$prompt" >> "$LOG" 2>&1; then
    echo "[OK] Generated new initiatives batch $batch_num" | tee -a "$OUTPUT_LOG" "$LOG"
  else
    echo "[WARN] Initiative generation batch $batch_num failed — continuing" | tee -a "$OUTPUT_LOG" "$LOG"
  fi
}

DOCS_COUNTER=0

for file in "$INIT_DIR"/*.md; do
  run_initiative "$file"

  local_total=$((COMPLETED + FAILED))

  # Every 4 completed: update docs, push, notify
  if [ $((COMPLETED % UPDATE_EVERY)) -eq 0 ] && [ "$COMPLETED" -gt 0 ] && [ "$DOCS_COUNTER" -lt "$((COMPLETED / UPDATE_EVERY))" ]; then
    DOCS_COUNTER=$((COMPLETED / UPDATE_EVERY))
    update_docs_and_push "$DOCS_COUNTER"
  fi

  # Every 11 total: generate new initiatives
  if [ $((local_total % EXPAND_EVERY)) -eq 0 ] && [ "$local_total" -gt 0 ]; then
    generate_new_initiatives $((local_total / EXPAND_EVERY))

    for new_file in "$INIT_DIR"/*.md; do
      name=$(basename "$new_file" .md)
      if ! git log --oneline | grep -q "autobuilder: $name"; then
        if [ ! -f ".autobuilder/.queued_$name" ]; then
          touch ".autobuilder/.queued_$name"
          run_initiative "$new_file"

          local_total=$((COMPLETED + FAILED))
          if [ $((COMPLETED % UPDATE_EVERY)) -eq 0 ] && [ "$COMPLETED" -gt 0 ] && [ "$DOCS_COUNTER" -lt "$((COMPLETED / UPDATE_EVERY))" ]; then
            DOCS_COUNTER=$((COMPLETED / UPDATE_EVERY))
            update_docs_and_push "$DOCS_COUNTER"
          fi
        fi
      fi
    done
  fi
done

# Final docs update + push
echo "" | tee -a "$OUTPUT_LOG" "$LOG"
echo "=== FINAL DOCS UPDATE + PUSH — $(date -u) ===" | tee -a "$OUTPUT_LOG" "$LOG"
update_docs_and_push "final"

echo "" | tee -a "$OUTPUT_LOG" "$LOG"
echo "=== AutoBuilder Complete: $(date -u) ===" | tee -a "$OUTPUT_LOG" "$LOG"
echo "Completed: $COMPLETED | Failed: $FAILED | Skipped: $SKIPPED" | tee -a "$OUTPUT_LOG" "$LOG"

git log --oneline | grep "autobuilder:" | tee -a "$OUTPUT_LOG" "$LOG"
