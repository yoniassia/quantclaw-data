"""
CBOE Options Data — Put/Call Ratios, VIX, Most Active Options

Data Source: Chicago Board Options Exchange (CBOE)
Update: Daily (post-market)
Free: Yes (direct CSV download, no registration required)
Priority: HIGH

Provides:
- Total Put/Call Ratio (equity, index, total)
- Most Active Options by Volume
- VIX Historical Data
- Market-wide Options Sentiment Indicator

Usage as Indicator:
- High P/C Ratio (>1.2) → Bearish positioning, potential contrarian buy
- Low P/C Ratio (<0.7) → Bullish positioning, potential contrarian sell
- Extreme readings often precede reversals
- Complements VIX term structure analysis
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os
from bs4 import BeautifulSoup

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/cboe")
os.makedirs(CACHE_DIR, exist_ok=True)

CBOE_PC_RATIO_URL = "https://www.cboe.com/us/options/market_statistics/daily/"
CBOE_VIX_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
CBOE_MOST_ACTIVE_URL = "https://www.cboe.com/us/options/market_statistics/most-active-options/"

def get_put_call_ratios() -> Dict:
    """
    Fetch daily put/call ratios from CBOE.
    Returns equity, index, and total P/C ratios.
    """
    cache_file = os.path.join(CACHE_DIR, "putcall_ratios.json")
    
    # Check cache (refresh daily)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(hours=24):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(CBOE_PC_RATIO_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # CBOE publishes P/C ratios in tables on their daily statistics page
        # Structure: Date, Equity P/C, Index P/C, Total P/C
        result = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "equity_pc": None,
            "index_pc": None,
            "total_pc": None,
            "equity_put_volume": None,
            "equity_call_volume": None,
            "index_put_volume": None,
            "index_call_volume": None,
            "interpretation": None
        }
        
        # Look for P/C ratio data in tables
        tables = soup.find_all('table')
        for table in tables:
            text = table.get_text()
            if 'Put/Call' in text or 'P/C Ratio' in text:
                # Extract ratios from table cells
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text().strip()
                        value_text = cells[-1].get_text().strip()
                        
                        try:
                            value = float(value_text.replace(',', ''))
                        except ValueError:
                            continue
                        
                        if 'Equity' in label and 'Call' not in label:
                            if 'Put' in label:
                                result['equity_put_volume'] = value
                            elif 'Ratio' in label or 'P/C' in label:
                                result['equity_pc'] = value
                        elif 'Index' in label:
                            if 'Put' in label:
                                result['index_put_volume'] = value
                            elif 'Ratio' in label or 'P/C' in label:
                                result['index_pc'] = value
                        elif 'Total' in label:
                            if 'Ratio' in label or 'P/C' in label:
                                result['total_pc'] = value
        
        # If we got a total P/C ratio, add interpretation
        if result['total_pc']:
            pc = result['total_pc']
            if pc > 1.2:
                result['interpretation'] = "High bearish positioning - potential contrarian buy signal"
            elif pc < 0.7:
                result['interpretation'] = "High bullish positioning - potential contrarian sell signal"
            else:
                result['interpretation'] = "Neutral positioning"
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
        
    except Exception as e:
        print(f"Error fetching CBOE P/C ratios: {e}")
        return {
            "error": str(e),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "equity_pc": None,
            "index_pc": None,
            "total_pc": None
        }

def get_vix_data(days: int = 30) -> List[Dict]:
    """
    Fetch VIX historical data from CBOE.
    Returns list of {date, open, high, low, close} dicts.
    """
    cache_file = os.path.join(CACHE_DIR, f"vix_data_{days}d.json")
    
    # Check cache (refresh daily)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(hours=24):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        # Download VIX CSV
        response = requests.get(CBOE_VIX_URL, timeout=15)
        response.raise_for_status()
        
        # Parse CSV with pandas
        from io import StringIO
        df = pd.read_csv(StringIO(response.text))
        
        # CBOE CSV format: DATE, OPEN, HIGH, LOW, CLOSE
        df.columns = [c.strip().upper() for c in df.columns]
        df['DATE'] = pd.to_datetime(df['DATE'])
        
        # Filter to requested days
        cutoff = datetime.now() - timedelta(days=days)
        df = df[df['DATE'] >= cutoff]
        
        # Convert to list of dicts
        result = []
        for _, row in df.iterrows():
            result.append({
                "date": row['DATE'].strftime("%Y-%m-%d"),
                "open": float(row['OPEN']),
                "high": float(row['HIGH']),
                "low": float(row['LOW']),
                "close": float(row['CLOSE'])
            })
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
        
    except Exception as e:
        print(f"Error fetching VIX data: {e}")
        return []

def get_most_active_options(limit: int = 20) -> List[Dict]:
    """
    Scrape most active options by volume from CBOE.
    Returns list of {symbol, strike, expiry, type, volume} dicts.
    """
    cache_file = os.path.join(CACHE_DIR, "most_active.json")
    
    # Check cache (refresh hourly)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(hours=1):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(CBOE_MOST_ACTIVE_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        result = []
        
        # Look for most active options table
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue
            
            # Check if this is the most active table
            headers_row = rows[0]
            if 'Symbol' in headers_row.get_text() or 'Volume' in headers_row.get_text():
                for row in rows[1:limit+1]:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        # Extract option data
                        option_info = {
                            "symbol": cells[0].get_text().strip() if len(cells) > 0 else None,
                            "volume": None,
                            "type": None,
                            "data": cells[1].get_text().strip() if len(cells) > 1 else None
                        }
                        
                        # Try to parse volume
                        for cell in cells:
                            text = cell.get_text().strip().replace(',', '')
                            try:
                                vol = int(text)
                                if vol > 100:  # Likely a volume number
                                    option_info['volume'] = vol
                                    break
                            except ValueError:
                                continue
                        
                        if option_info['symbol'] and option_info['volume']:
                            result.append(option_info)
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result[:limit]
        
    except Exception as e:
        print(f"Error fetching most active options: {e}")
        return []

def get_options_summary() -> Dict:
    """
    Get comprehensive options market summary.
    Combines P/C ratios, VIX, and most active options.
    """
    return {
        "putcall_ratios": get_put_call_ratios(),
        "vix_latest": get_vix_data(days=1),
        "most_active": get_most_active_options(limit=10),
        "timestamp": datetime.now().isoformat()
    }

# CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "pc":
            print(json.dumps(get_put_call_ratios(), indent=2))
        elif command == "vix":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            print(json.dumps(get_vix_data(days), indent=2))
        elif command == "active":
            print(json.dumps(get_most_active_options(), indent=2))
        else:
            print(json.dumps(get_options_summary(), indent=2))
    else:
        print(json.dumps(get_options_summary(), indent=2))
