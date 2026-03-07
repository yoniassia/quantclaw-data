"""
Nasdaq Data Link Corporate Credit — Corporate Bond Spreads & Credit Indicators

Data Source: Nasdaq Data Link (formerly Quandl)
Update: Daily (business days)
History: 20+ years for major indices
Free: Core datasets available without API key (Note: ML datasets require subscription as of 2025)

Provides:
- High-Yield (HY) bond spreads (ML/EMHYS - requires subscription)
- Investment-Grade (IG) bond spreads (ML/EMIG - requires subscription)
- Corporate bond indices
- Credit default swap (CDS) spreads
- Historical spread data for trend analysis
- Fallback to FRED data when Nasdaq datasets unavailable

Usage as Indicator:
- Widening spreads → Credit stress, risk-off sentiment
- Narrowing spreads → Credit health, risk-on sentiment
- HY spreads >500bps → Potential recession signal
- IG spreads >150bps → Corporate credit stress
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/nasdaq_credit")
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_URL = "https://data.nasdaq.com/api/v3/datasets"
FRED_BASE_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
API_KEY = os.environ.get("NASDAQ_DATA_LINK_API_KEY", "")

# Dataset codes (ML series require subscription)
DATASETS = {
    "hy_spread": "ML/EMHYS",      # High-Yield OAS spread (premium)
    "ig_spread": "ML/EMIG",       # Investment-Grade OAS spread (premium)
    "hy_index": "ML/EMHY",        # High-Yield Total Return Index (premium)
    "ig_index": "ML/EMIG",        # Investment-Grade Index (premium)
}

# Alternative free data sources (FRED)
FRED_SERIES = {
    "hy_spread": "BAMLH0A0HYM2",   # ICE BofA US High Yield Index OAS
    "ig_spread": "BAMLC0A0CM",     # ICE BofA US Corporate Index OAS
    "aaa_spread": "BAMLC0A1CAAA",  # ICE BofA AAA US Corporate Index OAS
    "bbb_spread": "BAMLC0A4CBBB",  # ICE BofA BBB US Corporate Index OAS
}


def _fetch_from_fred(series_id: str, observations: int = 1) -> Dict:
    """
    Fetch data from FRED as fallback (free, no API key needed for basic CSV access).
    
    Args:
        series_id: FRED series ID
        observations: Number of observations to fetch
    
    Returns:
        Dict with series data
    """
    cache_file = os.path.join(CACHE_DIR, f"fred_{series_id}_obs{observations}.json")
    
    # Check cache (refresh daily)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(hours=24):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        # FRED provides free CSV downloads
        params = {
            "id": series_id,
            "cosd": (datetime.now() - timedelta(days=observations * 7)).strftime("%Y-%m-%d"),
        }
        
        response = requests.get(FRED_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        
        # Parse CSV (simple: DATE,VALUE format)
        lines = response.text.strip().split('\n')
        if len(lines) < 2:
            raise Exception("No data in FRED response")
        
        # Skip header, get last non-empty line
        data_lines = [l for l in lines[1:] if l.strip() and '.' not in l.split(',')[0]]
        if not data_lines:
            raise Exception("No valid data rows")
        
        latest = data_lines[-1].split(',')
        date_val = latest[0]
        value_val = float(latest[1]) if len(latest) > 1 and latest[1] else None
        
        result = {
            "date": date_val,
            "value": value_val,
            "series_id": series_id,
            "source": "FRED"
        }
        
        # Parse all data for historical
        all_data = []
        for line in data_lines:
            parts = line.split(',')
            if len(parts) >= 2 and parts[1]:
                try:
                    all_data.append({
                        "date": parts[0],
                        "value": float(parts[1])
                    })
                except ValueError:
                    continue
        
        result["historical"] = all_data
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
        
    except Exception as e:
        # If cache exists (even if stale), return it as fallback
        if os.path.exists(cache_file):
            with open(cache_file) as f:
                cached = json.load(f)
                cached["warning"] = "Using stale cache due to fetch error"
                return cached
        raise Exception(f"Failed to fetch FRED {series_id}: {str(e)}")


def _fetch_dataset(dataset_code: str, rows: int = 1) -> Dict:
    """
    Fetch data from Nasdaq Data Link API.
    Falls back to FRED if Nasdaq dataset is unavailable.
    
    Args:
        dataset_code: Dataset code (e.g., "ML/EMHYS")
        rows: Number of rows to fetch (most recent first)
    
    Returns:
        Dict with dataset metadata and data
    """
    cache_file = os.path.join(CACHE_DIR, f"{dataset_code.replace('/', '_')}_rows{rows}.json")
    
    # Check cache (refresh daily)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(hours=24):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        params = {"rows": rows}
        if API_KEY:
            params["api_key"] = API_KEY
        
        url = f"{BASE_URL}/{dataset_code}.json"
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403 or e.response.status_code == 404:
            # Premium dataset or not found - try FRED alternative
            fred_series = None
            if "EMHYS" in dataset_code:
                fred_series = FRED_SERIES["hy_spread"]
            elif "EMIG" in dataset_code:
                fred_series = FRED_SERIES["ig_spread"]
            
            if fred_series:
                try:
                    fred_data = _fetch_from_fred(fred_series, observations=rows)
                    # Convert to Nasdaq-like format
                    return {
                        "dataset": {
                            "data": [[fred_data["date"], fred_data["value"]]],
                            "column_names": ["Date", "Value"],
                            "database_code": "FRED",
                            "dataset_code": fred_series,
                            "source": "FRED"
                        }
                    }
                except Exception as fred_error:
                    pass
        
        # If cache exists (even if stale), return it as fallback
        if os.path.exists(cache_file):
            with open(cache_file) as f:
                cached = json.load(f)
                cached["warning"] = "Using stale cache"
                return cached
        
        raise Exception(f"Failed to fetch {dataset_code}: {str(e)}")
    
    except Exception as e:
        # If cache exists (even if stale), return it as fallback
        if os.path.exists(cache_file):
            with open(cache_file) as f:
                cached = json.load(f)
                cached["warning"] = "Using stale cache"
                return cached
        raise Exception(f"Failed to fetch {dataset_code}: {str(e)}")


def get_hy_spread() -> Dict:
    """
    Get current High-Yield (HY) bond OAS spread.
    
    OAS = Option-Adjusted Spread (basis points over Treasuries)
    Higher spread = higher credit risk premium
    
    Uses FRED BAMLH0A0HYM2 series as fallback when Nasdaq Data Link unavailable.
    
    Returns:
        Dict with latest HY spread data and interpretation
    """
    try:
        # Try FRED directly (free, reliable)
        fred_data = _fetch_from_fred(FRED_SERIES["hy_spread"], observations=1)
        
        date_val = fred_data["date"]
        spread_val = fred_data["value"]
        
        if spread_val is None:
            return {"error": "No data available", "source": "FRED"}
        
        # Interpret spread level
        signal = "NORMAL"
        if spread_val > 800:
            signal = "SEVERE_STRESS"
        elif spread_val > 500:
            signal = "STRESS"
        elif spread_val > 400:
            signal = "ELEVATED"
        elif spread_val < 300:
            signal = "TIGHT"
        
        return {
            "date": date_val,
            "spread_bps": spread_val,
            "spread_pct": round(spread_val / 100, 2),
            "source": "FRED",
            "series_id": FRED_SERIES["hy_spread"],
            "signal": signal,
            "interpretation": _interpret_hy_spread(spread_val),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e), "source": "FRED", "series_id": FRED_SERIES.get("hy_spread")}


def get_ig_spread() -> Dict:
    """
    Get current Investment-Grade (IG) bond spread.
    
    IG spreads are typically lower and less volatile than HY.
    Used as barometer for corporate credit health overall.
    
    Uses FRED BAMLC0A0CM series as fallback.
    
    Returns:
        Dict with latest IG spread data and interpretation
    """
    try:
        # Try FRED directly
        fred_data = _fetch_from_fred(FRED_SERIES["ig_spread"], observations=1)
        
        date_val = fred_data["date"]
        spread_val = fred_data["value"]
        
        if spread_val is None:
            return {"error": "No data available", "source": "FRED"}
        
        # Interpret spread level
        signal = "NORMAL"
        if spread_val > 200:
            signal = "STRESS"
        elif spread_val > 150:
            signal = "ELEVATED"
        elif spread_val < 100:
            signal = "TIGHT"
        
        return {
            "date": date_val,
            "spread_bps": spread_val,
            "spread_pct": round(spread_val / 100, 2),
            "source": "FRED",
            "series_id": FRED_SERIES["ig_spread"],
            "signal": signal,
            "interpretation": _interpret_ig_spread(spread_val),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e), "source": "FRED", "series_id": FRED_SERIES.get("ig_spread")}


def get_credit_default_swap(ticker: str = "AAPL") -> Dict:
    """
    Get Credit Default Swap (CDS) spread for a specific company.
    
    Note: CDS data requires premium Nasdaq Data Link subscription.
    This function provides a framework for when access is available.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Dict with CDS spread data (if available)
    """
    # CDS data typically under FINRA or ICE datasets (premium)
    # Example: FINRA/TRACE_{ticker} or ICE/CDS_{ticker}
    
    return {
        "ticker": ticker,
        "error": "CDS data requires premium subscription",
        "note": "Use get_hy_spread() and get_ig_spread() for aggregate credit risk",
        "alternative": "Consider using high-yield spread as proxy for credit stress",
        "timestamp": datetime.now().isoformat()
    }


def get_corporate_bond_index() -> Dict:
    """
    Get corporate bond index values (HY and IG).
    
    Returns:
        Dict with both HY and IG index levels
    """
    try:
        hy = get_hy_spread()
        ig = get_ig_spread()
        
        result = {
            "high_yield": {
                "date": hy.get("date"),
                "spread_bps": hy.get("spread_bps"),
                "signal": hy.get("signal"),
                "source": hy.get("source")
            },
            "investment_grade": {
                "date": ig.get("date"),
                "spread_bps": ig.get("spread_bps"),
                "signal": ig.get("signal"),
                "source": ig.get("source")
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return result
        
    except Exception as e:
        return {"error": str(e)}


def get_historical_spreads(dataset: str = "ML/EMHYS", months: int = 12) -> List[Dict]:
    """
    Get historical spread data for trend analysis.
    
    Args:
        dataset: Dataset code (default: ML/EMHYS for HY spreads, will use FRED fallback)
        months: Number of months of history
    
    Returns:
        List of dicts with date and spread values
    """
    try:
        # Map dataset to FRED series
        fred_series = FRED_SERIES["hy_spread"]
        if "EMIG" in dataset:
            fred_series = FRED_SERIES["ig_spread"]
        
        # Fetch from FRED
        fred_data = _fetch_from_fred(fred_series, observations=months * 5)  # ~5 data points per month
        
        historical = fred_data.get("historical", [])
        
        # Filter to requested months
        cutoff_date = datetime.now() - timedelta(days=months * 30)
        filtered = [
            {
                "date": item["date"],
                "spread_bps": item["value"],
                "spread_pct": round(item["value"] / 100, 2) if item["value"] else None
            }
            for item in historical
            if datetime.strptime(item["date"], "%Y-%m-%d") >= cutoff_date
        ]
        
        return filtered
        
    except Exception as e:
        return [{"error": str(e), "dataset": dataset}]


def get_latest() -> Dict:
    """
    Get summary of key credit metrics.
    
    Returns:
        Dict with HY spread, IG spread, spread differential, and signals
    """
    hy = get_hy_spread()
    ig = get_ig_spread()
    
    # Calculate spread differential (HY - IG)
    spread_diff = None
    if "spread_bps" in hy and "spread_bps" in ig:
        if hy["spread_bps"] is not None and ig["spread_bps"] is not None:
            spread_diff = round(hy["spread_bps"] - ig["spread_bps"], 1)
    
    # Overall credit signal
    credit_signal = "NORMAL"
    if hy.get("signal") in ["SEVERE_STRESS", "STRESS"]:
        credit_signal = "RISK_OFF"
    elif hy.get("signal") == "ELEVATED" or ig.get("signal") == "ELEVATED":
        credit_signal = "CAUTIOUS"
    elif hy.get("signal") == "TIGHT" and ig.get("signal") == "TIGHT":
        credit_signal = "RISK_ON"
    
    return {
        "high_yield": {
            "spread_bps": hy.get("spread_bps"),
            "signal": hy.get("signal"),
            "date": hy.get("date"),
            "source": hy.get("source")
        },
        "investment_grade": {
            "spread_bps": ig.get("spread_bps"),
            "signal": ig.get("signal"),
            "date": ig.get("date"),
            "source": ig.get("source")
        },
        "spread_differential_bps": spread_diff,
        "overall_credit_signal": credit_signal,
        "interpretation": _interpret_credit_environment(credit_signal, hy, ig),
        "timestamp": datetime.now().isoformat()
    }


def _interpret_hy_spread(spread_bps: float) -> str:
    """Interpret high-yield spread level."""
    if spread_bps > 800:
        return "Severe credit stress. Historical distress levels. Potential recession."
    elif spread_bps > 500:
        return "Elevated credit risk. Market pricing significant default risk."
    elif spread_bps > 400:
        return "Above-average spreads. Investors demanding higher risk premium."
    elif spread_bps < 300:
        return "Tight spreads. Low credit risk perception. Risk-on environment."
    else:
        return "Normal credit conditions."


def _interpret_ig_spread(spread_bps: float) -> str:
    """Interpret investment-grade spread level."""
    if spread_bps > 200:
        return "Corporate credit stress. Flight to quality in progress."
    elif spread_bps > 150:
        return "Elevated IG spreads. Concerns about corporate health."
    elif spread_bps < 100:
        return "Very tight spreads. Strong corporate credit environment."
    else:
        return "Normal IG credit conditions."


def _interpret_credit_environment(signal: str, hy: Dict, ig: Dict) -> str:
    """Interpret overall credit market environment."""
    if signal == "RISK_OFF":
        return "Credit markets under stress. High-yield spreads elevated. Risk-off positioning."
    elif signal == "CAUTIOUS":
        return "Mixed credit signals. Some caution warranted in credit markets."
    elif signal == "RISK_ON":
        return "Healthy credit environment. Tight spreads suggest low default risk."
    else:
        return "Normal credit market conditions."


# Module info for discovery
__all__ = [
    'get_hy_spread',
    'get_ig_spread', 
    'get_credit_default_swap',
    'get_corporate_bond_index',
    'get_historical_spreads',
    'get_latest'
]

if __name__ == "__main__":
    print(json.dumps(get_latest(), indent=2))
