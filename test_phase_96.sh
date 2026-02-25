#!/bin/bash
# Test Phase 96: CIA World Factbook Module

echo "========================================="
echo "Phase 96: CIA World Factbook Test Suite"
echo "========================================="
echo

# Test 1: Get full country data
echo "Test 1: Full country data for United States"
echo "-------------------------------------------"
python3 cli.py cia-factbook 'United States' | jq -r '.country, .demographics.population, .military.expenditure_pct_gdp'
echo

# Test 2: Demographics only
echo "Test 2: Demographics for Israel"
echo "--------------------------------"
python3 cli.py cia-factbook-demographics Israel | jq '.'
echo

# Test 3: Military data only
echo "Test 3: Military expenditure for China"
echo "---------------------------------------"
python3 cli.py cia-factbook-military China | jq '.'
echo

# Test 4: Trade partners only
echo "Test 4: Trade partners for Russia"
echo "----------------------------------"
python3 cli.py cia-factbook-trade Russia | jq '.export_partners[0:2]'
echo

# Test 5: Natural resources only
echo "Test 5: Natural resources for United States"
echo "--------------------------------------------"
python3 cli.py cia-factbook-resources 'United States' | jq '.natural_resources[0:5]'
echo

# Test 6: Compare multiple countries
echo "Test 6: Compare China, Russia, United States"
echo "---------------------------------------------"
python3 cli.py cia-factbook-compare China Russia 'United States' | jq '.countries[] | {name, population, gdp_usd, military_expenditure_pct}'
echo

echo "========================================="
echo "✓ All Phase 96 tests completed"
echo "========================================="
