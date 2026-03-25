#!/bin/bash
# Phase 129: Argentina INDEC Statistics - Test Suite

echo "============================================"
echo "Phase 129: Argentina INDEC Statistics Test"
echo "============================================"
echo ""

echo "1. Economic Snapshot"
echo "--------------------"
python3 cli.py ar-snapshot 2>/dev/null | head -30
echo ""

echo "2. Inflation Data"
echo "-----------------"
python3 cli.py ar-inflation 2>/dev/null | head -20
echo ""

echo "3. List Available Indicators"
echo "-----------------------------"
python3 cli.py ar-indicators 2>/dev/null | head -30
echo ""

echo "4. GDP Data"
echo "-----------"
python3 cli.py ar-gdp 2>/dev/null | head -25
echo ""

echo "5. Trade Balance Data"
echo "---------------------"
python3 cli.py ar-trade 2>/dev/null | head -25
echo ""

echo "6. Employment Data"
echo "------------------"
python3 cli.py ar-employment 2>/dev/null | head -25
echo ""

echo "7. Poverty Data"
echo "---------------"
python3 cli.py ar-poverty 2>/dev/null | head -20
echo ""

echo "============================================"
echo "All Argentina INDEC tests completed!"
echo "============================================"
