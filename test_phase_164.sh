#!/bin/bash
# Phase 164 Verification Test - Sovereign Rating Tracker

echo "================================================"
echo "Phase 164: Sovereign Rating Tracker - Test Suite"
echo "================================================"
echo ""

cd /home/quant/apps/quantclaw-data

echo "Test 1: All Rating Changes (30 days)"
echo "-------------------------------------"
python3 cli.py sovereign-ratings 30 | jq '.total_actions, .agencies.sp[0].country, .agencies.sp[0].action_type'
echo ""

echo "Test 2: Recent Downgrades"
echo "-------------------------"
python3 cli.py sovereign-downgrades | jq '.total_downgrades, .downgrades[0].country // "none"'
echo ""

echo "Test 3: Recent Upgrades"
echo "-----------------------"
python3 cli.py sovereign-upgrades | jq '.total_upgrades, .upgrades[0].country // "none"'
echo ""

echo "Test 4: Watch List (Negative Outlook)"
echo "--------------------------------------"
python3 cli.py sovereign-watch | jq '.countries_on_watch, .watch_list[0].country // "none"'
echo ""

echo "Test 5: Investment Grade Transitions"
echo "------------------------------------"
python3 cli.py sovereign-ig-changes | jq '.total_ig_transitions, .fallen_angels[0].country // "none", .rising_stars[0].country // "none"'
echo ""

echo "Test 6: Country-Specific Ratings"
echo "--------------------------------"
python3 cli.py sovereign-country "Brazil" | jq '.country, .ratings | keys'
echo ""

echo "Test 7: Full Dashboard"
echo "----------------------"
python3 cli.py sovereign-dashboard | jq 'keys'
echo ""

echo "Test 8: Direct Module Test"
echo "---------------------------"
python3 modules/sovereign_rating_tracker.py all 90 | jq '.total_actions'
echo ""

echo "================================================"
echo "All Tests Complete! ✅"
echo "================================================"
