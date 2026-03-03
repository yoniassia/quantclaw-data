#!/bin/bash
# Test script for SPACInsider module

echo "============================================"
echo "SPACInsider Module Test Suite"
echo "============================================"
echo ""

cd /home/quant/apps/quantclaw-data

echo "1. Testing Active SPACs..."
echo "-------------------------------------------"
python3 modules/spacinsider.py active
echo ""

echo "2. Testing Merger SPACs..."
echo "-------------------------------------------"
python3 modules/spacinsider.py merger
echo ""

echo "3. Testing SPAC IPOs..."
echo "-------------------------------------------"
python3 modules/spacinsider.py ipo
echo ""

echo "4. Testing Liquidations..."
echo "-------------------------------------------"
python3 modules/spacinsider.py liquidation
echo ""

echo "5. Testing Performance Data..."
echo "-------------------------------------------"
python3 modules/spacinsider.py performance
echo ""

echo "============================================"
echo "Testing import in Python..."
echo "============================================"
python3 << 'EOF'
import sys
sys.path.insert(0, '/home/quant/apps/quantclaw-data')

from modules import spacinsider

print("\nTesting get_data() function:")
print("------------------------------")

# Test active SPACs
print("\n1. Active SPACs:")
df = spacinsider.get_data(period='active')
print(f"   Rows: {len(df)}")
print(f"   Columns: {list(df.columns)}")
if not df.empty:
    print(df.head(3).to_string())

# Test mergers
print("\n2. Merger SPACs:")
df = spacinsider.get_data(period='merger')
print(f"   Rows: {len(df)}")
if not df.empty:
    print(df.head(2).to_string())

# Test IPOs
print("\n3. SPAC IPOs:")
df = spacinsider.get_data(period='ipo')
print(f"   Rows: {len(df)}")
if not df.empty:
    print(df.head(2).to_string())

print("\n✓ Module loaded and tested successfully")
EOF

echo ""
echo "============================================"
echo "Test suite complete!"
echo "============================================"
