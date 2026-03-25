#!/bin/bash
# Phase 87 - Correlation Anomaly Detector Test Suite

echo "=========================================="
echo "PHASE 87: CORRELATION ANOMALY DETECTOR"
echo "=========================================="
echo ""

cd /home/quant/apps/quantclaw-data

echo "Test 1: Correlation Breakdown Detection (AAPL vs MSFT)"
echo "---------------------------------------------------"
python3 cli.py corr-breakdown --ticker1 AAPL --ticker2 MSFT --lookback 180
echo ""

echo "Test 2: Correlation Matrix Scanner (Multi-Asset)"
echo "---------------------------------------------------"
python3 cli.py corr-scan --tickers SPY,TLT,GLD,QQQ,IWM
echo ""

echo "Test 3: Regime Detection (Cross-Asset)"
echo "---------------------------------------------------"
python3 cli.py corr-regime --tickers SPY,TLT,GLD,DBC,UUP
echo ""

echo "Test 4: Statistical Arbitrage Scanner (Sector ETFs)"
echo "---------------------------------------------------"
python3 cli.py corr-arbitrage --tickers XLF,XLK,XLE,XLV,XLY
echo ""

echo "Test 5: Tech Stock Correlation Breakdown (AAPL vs TSLA)"
echo "---------------------------------------------------"
python3 cli.py corr-breakdown --ticker1 AAPL --ticker2 TSLA --lookback 252
echo ""

echo "=========================================="
echo "PHASE 87 TESTS COMPLETE"
echo "=========================================="
