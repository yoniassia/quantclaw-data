"""
Commodity Volatility Term Structure (Roadmap #377)
Analyzes the term structure of implied/historical volatility across commodity futures.
Uses free data from Yahoo Finance commodity ETFs and FRED.
"""

import datetime
import math
from typing import Dict, List, Optional, Tuple


# Major commodity tickers (ETFs as proxies for vol calculation)
COMMODITY_ETFS = {
    "crude_oil": "USO",
    "natural_gas": "UNG",
    "gold": "GLD",
    "silver": "SLV",
    "copper": "CPER",
    "corn": "CORN",
    "soybeans": "SOYB",
    "wheat": "WEAT",
    "sugar": "CANE",
    "coffee": "JO",
    "platinum": "PPLT",
    "palladium": "PALL",
}

TIMEFRAMES = [5, 10, 21, 63, 126, 252]  # trading days


def calculate_historical_volatility(prices: List[float], window: int = 21) -> List[float]:
    """
    Calculate rolling historical volatility (annualized) from a price series.
    
    Args:
        prices: List of daily closing prices (oldest first)
        window: Rolling window in trading days
        
    Returns:
        List of annualized volatility values
    """
    if len(prices) < window + 1:
        return []
    
    # Calculate log returns
    log_returns = []
    for i in range(1, len(prices)):
        if prices[i] > 0 and prices[i - 1] > 0:
            log_returns.append(math.log(prices[i] / prices[i - 1]))
        else:
            log_returns.append(0.0)
    
    # Rolling standard deviation, annualized
    vols = []
    for i in range(window - 1, len(log_returns)):
        subset = log_returns[i - window + 1: i + 1]
        mean_r = sum(subset) / len(subset)
        variance = sum((r - mean_r) ** 2 for r in subset) / (len(subset) - 1)
        annual_vol = math.sqrt(variance) * math.sqrt(252)
        vols.append(round(annual_vol * 100, 2))  # percentage
    
    return vols


def build_vol_term_structure(prices: List[float]) -> Dict[str, float]:
    """
    Build volatility term structure across multiple timeframes.
    
    Args:
        prices: Daily closing prices (oldest first), minimum 253 data points
        
    Returns:
        Dict mapping timeframe label to current annualized vol (%)
    """
    result = {}
    for window in TIMEFRAMES:
        vols = calculate_historical_volatility(prices, window)
        if vols:
            result[f"{window}d"] = vols[-1]
    return result


def vol_term_structure_slope(term_structure: Dict[str, float]) -> Optional[float]:
    """
    Calculate the slope of the vol term structure (long-term minus short-term).
    Positive = contango (normal), Negative = backwardation (stress).
    
    Args:
        term_structure: Output from build_vol_term_structure
        
    Returns:
        Slope value (252d vol - 5d vol), or None if insufficient data
    """
    short = term_structure.get("5d")
    long_ = term_structure.get("252d")
    if short is not None and long_ is not None:
        return round(long_ - short, 2)
    return None


def classify_vol_regime(term_structure: Dict[str, float]) -> str:
    """
    Classify current volatility regime based on term structure shape.
    
    Args:
        term_structure: Output from build_vol_term_structure
        
    Returns:
        Regime classification string
    """
    slope = vol_term_structure_slope(term_structure)
    if slope is None:
        return "insufficient_data"
    
    short_vol = term_structure.get("5d", 0)
    
    if slope > 5:
        return "low_vol_complacency"
    elif slope > 0:
        return "normal_contango"
    elif slope > -5:
        return "mild_stress"
    elif slope > -15:
        return "elevated_stress"
    else:
        if short_vol > 50:
            return "crisis_regime"
        return "severe_backwardation"


def compare_commodities_vol(commodity_prices: Dict[str, List[float]], window: int = 21) -> Dict[str, float]:
    """
    Compare current volatility across multiple commodities at a given timeframe.
    
    Args:
        commodity_prices: Dict of commodity name -> price list
        window: Volatility window in days
        
    Returns:
        Dict of commodity name -> current annualized vol (%)
    """
    result = {}
    for name, prices in commodity_prices.items():
        vols = calculate_historical_volatility(prices, window)
        if vols:
            result[name] = vols[-1]
    return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))


def vol_cone(prices: List[float], window: int = 21, lookback_years: int = 3) -> Dict[str, float]:
    """
    Calculate volatility cone (percentile ranks) for a given window.
    Shows where current vol sits relative to historical range.
    
    Args:
        prices: Daily closing prices
        window: Vol calculation window
        lookback_years: Years of history for percentile calculation
        
    Returns:
        Dict with min, p25, median, p75, max, current, percentile
    """
    vols = calculate_historical_volatility(prices, window)
    lookback_days = lookback_years * 252
    
    if len(vols) < lookback_days:
        hist = vols
    else:
        hist = vols[-lookback_days:]
    
    if not hist:
        return {}
    
    sorted_vols = sorted(hist)
    n = len(sorted_vols)
    current = hist[-1]
    
    percentile = sum(1 for v in sorted_vols if v <= current) / n * 100
    
    return {
        "min": sorted_vols[0],
        "p25": sorted_vols[int(n * 0.25)],
        "median": sorted_vols[int(n * 0.5)],
        "p75": sorted_vols[int(n * 0.75)],
        "max": sorted_vols[-1],
        "current": current,
        "percentile": round(percentile, 1),
    }
