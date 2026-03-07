#!/usr/bin/env python3
"""
CBOE Open Data Feed — Options Market Statistics Module

Provides free access to CBOE options market statistics, including volume summaries,
put/call ratios, and VIX historical data. No API key required.

Source: https://www.cboe.com/us/options/market_statistics/
Category: Options & Derivatives
Free tier: True - Completely free, no limits
Update frequency: Daily
Author: QuantClaw Data NightBuilder
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# ========== CONFIGURATION ==========

BASE_URL = "https://cdn.cboe.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Known CBOE data endpoints
CBOE_ENDPOINTS = {
    'vix_history': f"{BASE_URL}/api/global/us_indices/daily_prices/VIX_History.csv",
    'total_put_call': f"{BASE_URL}/resources/options/volume_and_call_put_ratios/totalpc.csv",
    'index_put_call': f"{BASE_URL}/resources/options/volume_and_call_put_ratios/indexpc.csv",
    'equity_put_call': f"{BASE_URL}/resources/options/volume_and_call_put_ratios/equitypc.csv",
}

# ========== HELPER FUNCTIONS ==========

def _fetch_csv(url: str) -> List[Dict]:
    """
    Fetch CSV data from CBOE CDN and parse into list of dicts.
    
    Args:
        url: Full URL to CSV file
        
    Returns:
        List of dictionaries with CSV data
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        lines = response.text.strip().split('\n')
        if len(lines) < 2:
            return []
        
        # Find the header row (contains DATE column for put/call data)
        header_idx = 0
        for i, line in enumerate(lines):
            if 'DATE' in line and ('CALL' in line or 'OPEN' in line):
                header_idx = i
                break
                
        if header_idx == 0 and 'DATE' not in lines[0]:
            # No proper header found
            return []
            
        headers = [h.strip() for h in lines[header_idx].split(',')]
        data = []
        
        for line in lines[header_idx + 1:]:
            if not line.strip():
                continue
            values = [v.strip() for v in line.split(',')]
            if len(values) == len(headers):
                data.append(dict(zip(headers, values)))
                
        return data
        
    except requests.RequestException as e:
        return {"error": f"Failed to fetch CSV from {url}: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to parse CSV: {str(e)}"}

# ========== PUBLIC API FUNCTIONS ==========

def get_market_statistics() -> Dict:
    """
    Get daily options market statistics including total volume and put/call ratios.
    
    Returns:
        Dictionary containing:
        - date: Latest trading date
        - total_volume: Total options volume across all exchanges
        - total_call_volume: Total call volume
        - total_put_volume: Total put volume
        - total_put_call_ratio: Overall put/call ratio
        - equity_put_call_ratio: Equity-only put/call ratio
        - index_put_call_ratio: Index-only put/call ratio
    """
    try:
        # Fetch total put/call data
        total_pc = _fetch_csv(CBOE_ENDPOINTS['total_put_call'])
        
        if isinstance(total_pc, dict) and 'error' in total_pc:
            return total_pc
            
        if not total_pc:
            return {"error": "No data available"}
            
        # Get most recent record
        latest = total_pc[-1]
        
        return {
            "date": latest.get('DATE', ''),
            "total_volume": int(latest.get('TOTAL', 0)),
            "total_call_volume": int(latest.get('CALL', 0)),
            "total_put_volume": int(latest.get('PUT', 0)),
            "total_put_call_ratio": float(latest.get('P/C Ratio', 0)),
            "data_source": "CBOE Total Exchange",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Error fetching market statistics: {str(e)}"}

def get_volume_summary(days: int = 5) -> Dict:
    """
    Get options volume summary for recent trading days.
    
    Args:
        days: Number of recent trading days to return (default 5)
        
    Returns:
        Dictionary with daily volume breakdown for total, equity, and index options
    """
    try:
        total_pc = _fetch_csv(CBOE_ENDPOINTS['total_put_call'])
        equity_pc = _fetch_csv(CBOE_ENDPOINTS['equity_put_call'])
        index_pc = _fetch_csv(CBOE_ENDPOINTS['index_put_call'])
        
        # Get last N days
        total_recent = total_pc[-days:] if len(total_pc) >= days else total_pc
        equity_recent = equity_pc[-days:] if len(equity_pc) >= days else equity_pc
        index_recent = index_pc[-days:] if len(index_pc) >= days else index_pc
        
        return {
            "total_volume": total_recent,
            "equity_volume": equity_recent,
            "index_volume": index_recent,
            "days_returned": len(total_recent),
            "data_source": "CBOE Exchange Volume Data",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Error fetching volume summary: {str(e)}"}

def get_put_call_ratio(product_type: str = "total") -> Dict:
    """
    Get put/call ratios for equity, index, or total options.
    
    Args:
        product_type: Type of options - "total", "equity", or "index" (default "total")
        
    Returns:
        Dictionary with recent put/call ratio data and trend
    """
    try:
        # Select appropriate endpoint
        if product_type.lower() == "equity":
            endpoint = CBOE_ENDPOINTS['equity_put_call']
            source = "Equity Options"
        elif product_type.lower() == "index":
            endpoint = CBOE_ENDPOINTS['index_put_call']
            source = "Index Options"
        else:
            endpoint = CBOE_ENDPOINTS['total_put_call']
            source = "Total Exchange"
            
        data = _fetch_csv(endpoint)
        
        if isinstance(data, dict) and 'error' in data:
            return data
            
        if not data:
            return {"error": "No data available"}
            
        # Get recent data
        recent = data[-20:] if len(data) >= 20 else data
        latest = data[-1]
        
        return {
            "product_type": product_type,
            "latest_date": latest.get('DATE', ''),
            "latest_ratio": float(latest.get('P/C Ratio', 0)),
            "latest_call_volume": int(latest.get('CALL', 0)),
            "latest_put_volume": int(latest.get('PUT', 0)),
            "historical_20d": [
                {
                    "date": r.get('DATE', ''),
                    "ratio": float(r.get('P/C Ratio', 0)),
                    "call_volume": int(r.get('CALL', 0)),
                    "put_volume": int(r.get('PUT', 0))
                }
                for r in recent
            ],
            "data_source": f"CBOE {source}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Error fetching put/call ratio: {str(e)}"}

def get_most_active_options(type: str = "volume") -> Dict:
    """
    Get most active options contracts.
    
    Note: CBOE does not provide a free API for real-time most active contracts.
    This function returns a note directing users to CBOE's website.
    
    Args:
        type: "volume" or "open_interest" (currently returns informational message)
        
    Returns:
        Dictionary with information about accessing most active options data
    """
    return {
        "message": "Most active options data is not available via free CBOE data feeds",
        "alternative": "Visit https://www.cboe.com/us/options/market_statistics/daily/ for current most active contracts",
        "note": "For programmatic access, consider CBOE DataShop (https://datashop.cboe.com/) or market data vendors",
        "timestamp": datetime.now().isoformat()
    }

def get_vix_history(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
    """
    Get VIX historical data.
    
    Args:
        start_date: Start date in format 'YYYY-MM-DD' (optional)
        end_date: End date in format 'YYYY-MM-DD' (optional)
        
    Returns:
        Dictionary with VIX historical OHLC data
    """
    try:
        vix_data = _fetch_csv(CBOE_ENDPOINTS['vix_history'])
        
        if isinstance(vix_data, dict) and 'error' in vix_data:
            return vix_data
            
        if not vix_data:
            return {"error": "No VIX data available"}
            
        # Filter by date range if specified
        filtered_data = vix_data
        if start_date or end_date:
            filtered_data = []
            for record in vix_data:
                record_date = record.get('DATE', '')
                if start_date and record_date < start_date:
                    continue
                if end_date and record_date > end_date:
                    continue
                filtered_data.append(record)
                
        return {
            "symbol": "VIX",
            "name": "CBOE Volatility Index",
            "records": len(filtered_data),
            "data": filtered_data[-100:] if len(filtered_data) > 100 else filtered_data,  # Last 100 records max
            "latest": filtered_data[-1] if filtered_data else None,
            "data_source": "CBOE VIX Historical Data",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Error fetching VIX history: {str(e)}"}

# ========== MODULE INFO ==========

def get_info() -> Dict:
    """
    Get module information and available functions.
    
    Returns:
        Dictionary with module metadata
    """
    return {
        "module": "cboe_open_data_feed",
        "description": "CBOE Options Market Statistics - Free data feeds",
        "source": "https://www.cboe.com/us/options/market_statistics/",
        "free_tier": True,
        "api_key_required": False,
        "functions": [
            "get_market_statistics() - Daily options market stats",
            "get_volume_summary(days=5) - Recent volume breakdown",
            "get_put_call_ratio(product_type='total') - Put/call ratios (total/equity/index)",
            "get_most_active_options(type='volume') - Info about most active contracts",
            "get_vix_history(start_date=None, end_date=None) - VIX historical OHLC data"
        ],
        "data_update_frequency": "Daily (end of day)",
        "author": "QuantClaw Data NightBuilder"
    }

# ========== MAIN (for testing) ==========

if __name__ == "__main__":
    print(json.dumps(get_info(), indent=2))
