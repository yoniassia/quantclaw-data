#!/bin/bash
# Setup script for Finnhub IPO Calendar module

echo "======================================"
echo "Finnhub IPO Calendar Setup"
echo "======================================"
echo ""
echo "This module requires a Finnhub API key."
echo ""
echo "Options:"
echo "1. Get a FREE API key from https://finnhub.io (recommended)"
echo "   - No credit card required"
echo "   - 60 API calls per minute"
echo "   - Sign up in < 2 minutes"
echo ""
echo "2. Use an existing API key if you have one"
echo ""

read -p "Do you want to set up your Finnhub API key now? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled. You can run this script again anytime."
    exit 0
fi

echo ""
echo "Please enter your Finnhub API key:"
echo "(Visit https://finnhub.io to get one if you don't have it)"
read -p "API Key: " api_key

if [ -z "$api_key" ]; then
    echo "❌ No API key provided. Setup cancelled."
    exit 1
fi

# Create credentials directory if it doesn't exist
mkdir -p ~/.credentials

# Save API key
cat > ~/.credentials/finnhub.json << EOF
{
  "api_key": "$api_key",
  "setup_date": "$(date -u +"%Y-%m-%d %H:%M:%S UTC")"
}
EOF

echo ""
echo "✅ API key saved to ~/.credentials/finnhub.json"
echo ""
echo "Testing API key..."

# Test the API key
cd /home/quant/apps/quantclaw-data
python3 modules/finnhub_ipo_calendar.py test

echo ""
echo "======================================"
echo "Setup complete!"
echo "======================================"
echo ""
echo "You can now use the Finnhub IPO Calendar module:"
echo "  python3 modules/finnhub_ipo_calendar.py upcoming"
echo "  python3 modules/finnhub_ipo_calendar.py recent"
echo ""
