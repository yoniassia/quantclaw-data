#!/bin/bash
# Test script for Phase 88: Deep Learning Sentiment

set -e
echo "🧪 Testing Phase 88: Deep Learning Sentiment (FinBERT)"
echo "=========================================="
echo ""

cd /home/quant/apps/quantclaw-data

# Test 1: News sentiment analysis
echo "📰 Test 1: News sentiment analysis (AAPL)"
python3 cli.py finbert-news AAPL 7 | head -50
echo ""

# Test 2: SEC filing analysis
echo "📑 Test 2: SEC filing sentiment (TSLA 10-Q)"
python3 cli.py finbert-sec TSLA 10-Q | head -50
echo ""

# Test 3: Earnings transcript analysis
echo "🎤 Test 3: Earnings transcript sentiment (MSFT)"
python3 cli.py finbert-earnings MSFT | head -50
echo ""

# Test 4: Sentiment trend
echo "📊 Test 4: Sentiment time series (NVDA, 4 quarters)"
python3 cli.py finbert-trend NVDA 4 | head -50
echo ""

# Test 5: Peer comparison
echo "⚖️ Test 5: Peer comparison (AAPL vs MSFT vs GOOGL)"
python3 cli.py finbert-compare AAPL,MSFT,GOOGL news | head -50
echo ""

echo "✅ Phase 88 testing complete!"
echo ""
echo "API endpoints available at:"
echo "  GET /api/v1/deep-learning-sentiment?action=news&ticker=AAPL&days=7"
echo "  GET /api/v1/deep-learning-sentiment?action=sec&ticker=TSLA&form_type=10-K"
echo "  GET /api/v1/deep-learning-sentiment?action=earnings&ticker=MSFT"
echo "  GET /api/v1/deep-learning-sentiment?action=trend&ticker=NVDA&quarters=4"
echo "  GET /api/v1/deep-learning-sentiment?action=compare&tickers=AAPL,MSFT,GOOGL&source=news"
