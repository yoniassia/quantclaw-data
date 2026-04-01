# AutoBuilder Runner — Cursor CLI Plan

## Prerequisites

```bash
# Install Cursor CLI (if not already)
# https://docs.cursor.com/cli
which cursor  # verify installed

# Ensure quantclaw-data repo is clean
cd /home/quant/apps/quantclaw-data
git status
git checkout -b autobuilder/gov-data-sources
```

## How It Works

The autobuilder loop:
1. Read `scope.md` + find next unfinished initiative
2. Read the initiative's PRD
3. Build the module following the pattern in scope.md
4. Test it: `python modules/<module>.py`
5. Git commit
6. Move to next initiative

## Running with Cursor CLI

### Option A: Single-shot per initiative (recommended)
```bash
cd /home/quant/apps/quantclaw-data

for initiative in .autobuilder/initiatives/*.md; do
  name=$(basename "$initiative" .md)
  
  # Skip if already done (commit message contains initiative name)
  if git log --oneline | grep -q "$name"; then
    echo "SKIP: $name already completed"
    continue
  fi
  
  echo "=== Building: $name ==="
  
  cursor agent --print --force \
    "Read .autobuilder/scope.md and .autobuilder/initiatives/$name.md. Build the module described in the initiative. Follow the module pattern from scope.md exactly. Test it with: python3 modules/<new_module>.py. If the test works, git add and commit with message: autobuilder: $name. If the API doesn't work as documented, note what failed in the module docstring and try alternative endpoints."
  
  sleep 5  # breathing room between initiatives
done
```

### Option B: Batch mode (faster, riskier)
```bash
cursor agent --print --force \
  "You are the QuantClaw AutoBuilder. Read .autobuilder/scope.md. Then process ALL initiatives in .autobuilder/initiatives/ in order (0001, 0002, ...). For each: build the module, test with python3, commit it. Skip any that are already committed. Continue until all 45 are done or you hit a hard stop."
```

### Option C: Via OpenClaw sub-agent (autonomous overnight)
```bash
# From OpenClaw main session:
sessions_spawn(
  agentId = "cursor",
  task = "Read /home/quant/apps/quantclaw-data/.autobuilder/scope.md and process all 45 initiatives in order. Build each module, test it, commit it. This is an overnight autonomous run.",
  model = "cursor/claude-4.6-opus-high-thinking",
  mode = "session",
  cwd = "/home/quant/apps/quantclaw-data"
)
```

## Monitoring Progress
```bash
# Check how many are done
cd /home/quant/apps/quantclaw-data
git log --oneline | grep "autobuilder:" | wc -l

# See what's been built
ls -la modules/ | grep -E "bundesbank|insee|istat|cbs_neth|statistics_denmark"

# Test a specific module
python modules/bundesbank_sdmx.py
```

## Expected Output
- 45 initiatives → ~35 new modules + ~10 enhancements to existing
- ~50-70 new data source connections
- Estimated time: 4-8 hours with Cursor CLI (Option A)
- Estimated time: 2-4 hours with batch mode (Option B)

## After Completion
```bash
# Merge back
git checkout main
git merge autobuilder/gov-data-sources

# Restart the MCP server to pick up new modules
pm2 restart quantclaw-data

# Verify MCP tools increased
curl -s http://localhost:3056/tools | python -m json.tool | grep -c "name"
```
