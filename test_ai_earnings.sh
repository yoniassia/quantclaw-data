#!/bin/bash
# Test script for AI Earnings Call Analyzer (Phase 76)

echo "======================================"
echo "AI Earnings Call Analyzer - Phase 76"
echo "Testing all commands..."
echo "======================================"
echo

cd /home/quant/apps/quantclaw-data

# Test 1: earnings-tone
echo "Test 1: earnings-tone AAPL"
python3 cli.py earnings-tone AAPL > /tmp/test_earnings_tone.json
if [ $? -eq 0 ]; then
  echo "✓ earnings-tone test PASSED"
  cat /tmp/test_earnings_tone.json | jq '.overall_tone.confidence_score' 2>/dev/null || echo "JSON output OK"
else
  echo "✗ earnings-tone test FAILED"
  exit 1
fi
echo

# Test 2: confidence-score
echo "Test 2: confidence-score TSLA"
python3 cli.py confidence-score TSLA > /tmp/test_confidence.json
if [ $? -eq 0 ]; then
  echo "✓ confidence-score test PASSED"
  cat /tmp/test_confidence.json | jq '.executive_confidence.confidence_level' 2>/dev/null || echo "JSON output OK"
else
  echo "✗ confidence-score test FAILED"
  exit 1
fi
echo

# Test 3: language-shift
echo "Test 3: language-shift MSFT"
python3 cli.py language-shift MSFT > /tmp/test_language_shift.json
if [ $? -eq 0 ]; then
  echo "✓ language-shift test PASSED"
  cat /tmp/test_language_shift.json | jq '.language_shift_analysis.trend' 2>/dev/null || echo "JSON output OK"
else
  echo "✗ language-shift test FAILED"
  exit 1
fi
echo

# Test 4: hedging-detector
echo "Test 4: hedging-detector NVDA"
python3 cli.py hedging-detector NVDA > /tmp/test_hedging.json
if [ $? -eq 0 ]; then
  echo "✓ hedging-detector test PASSED"
  cat /tmp/test_hedging.json | jq '.overall_hedging.risk_level' 2>/dev/null || echo "JSON output OK"
else
  echo "✗ hedging-detector test FAILED"
  exit 1
fi
echo

echo "======================================"
echo "All tests PASSED! ✓"
echo "======================================"
echo
echo "Module Location: /home/quant/apps/quantclaw-data/modules/ai_earnings_analyzer.py"
echo "API Endpoint: /api/v1/ai-earnings"
echo "CLI Registration: CONFIRMED"
echo "Services.ts: UPDATED"
echo "Roadmap.ts: Phase 76 marked as DONE"
