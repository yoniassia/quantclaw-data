#!/bin/bash
# Phase 71: Sustainability-Linked Bonds - Comprehensive Test Suite

echo "======================================"
echo "PHASE 71: SUSTAINABILITY-LINKED BONDS"
echo "======================================"
echo ""

echo "1. SLB Market Dashboard"
echo "------------------------"
python3 cli.py slb-market
echo ""

echo "2. SLB Issuer Analysis (ENEL)"
echo "------------------------------"
python3 cli.py slb-issuer ENEL
echo ""

echo "3. SLB Issuer Analysis (CHTR)"
echo "------------------------------"
python3 cli.py slb-issuer CHTR
echo ""

echo "4. SLB KPI Tracker"
echo "------------------"
python3 cli.py slb-kpi-tracker
echo ""

echo "5. SLB Coupon Forecast"
echo "----------------------"
python3 cli.py slb-coupon-forecast
echo ""

echo "======================================"
echo "✅ PHASE 71 TEST COMPLETE"
echo "======================================"
