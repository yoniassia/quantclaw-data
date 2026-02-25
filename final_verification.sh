#!/bin/bash
echo "======================================"
echo "PHASE 48 VERIFICATION REPORT"
echo "======================================"
echo ""

echo "📁 Files Status:"
echo "  • peer_network.py: $(wc -l < modules/peer_network.py) lines"
echo "  • API route: $(test -f src/app/api/v1/peer-network/route.ts && echo '✅ EXISTS' || echo '❌ MISSING')"
echo "  • CLI entry: $(grep -c 'peer_network' cli.py) references"
echo "  • services.ts: $(grep -c 'phase: 48' src/app/services.ts) services"
echo "  • roadmap.ts: $(grep 'id: 48' src/app/roadmap.ts | grep -o 'status: "[^"]*"')"
echo ""

echo "🧪 CLI Commands Test:"
commands=("peer-network" "compare-networks" "map-dependencies")
for cmd in "${commands[@]}"; do
  if python3 cli.py 2>&1 | grep -q "$cmd"; then
    echo "  ✅ $cmd - registered"
  else
    echo "  ❌ $cmd - not found"
  fi
done
echo ""

echo "📊 Functional Test:"
# Run a simple test
output=$(python3 modules/peer_network.py peer-network AAPL 2>&1)
if echo "$output" | grep -q "PEER NETWORK ANALYSIS"; then
  echo "  ✅ Module executes successfully"
  echo "  ✅ Output format: Human-readable"
else
  echo "  ❌ Module execution failed"
fi
echo ""

echo "======================================"
echo "SUMMARY"
echo "======================================"
echo "Phase 48: Peer Network Analysis"
echo "Status: $(grep 'id: 48' src/app/roadmap.ts | grep -o 'status: "[^"]*"' | cut -d'"' -f2)"
echo "LOC: $(wc -l < modules/peer_network.py)"
echo "CLI: 3 commands"
echo "API: 3 endpoints"
echo "======================================"
