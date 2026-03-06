#!/usr/bin/env python3
"""
Industrial Metals (Phase 172)
==============================
LME copper, aluminum, zinc, nickel prices and inventories. Daily.

Data Sources:
- Yahoo Finance: Metal ETFs (CPER copper, JJC copper, JJN nickel, JJUB aluminum)
- FRED: Metal prices and economic indicators
- Public data: LME inventory estimates

CLI Commands:
- python cli.py copper-price           # LME copper price and trend
- python cli.py aluminum-price         # LME aluminum price and trend  
- python cli.py zinc-price             # LME zinc price and trend
- python cli.py nickel-price           # LME nickel price and trend
- python cli.py metal-inventories      # Metal inventory levels
- python cli.py metals-snapshot        # All metals overview
- python cli.py metals-correlation     # Correlation with industrial indicators
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import statistics

# API Configuration
YAHOO_FINANCE_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"
FRED_BASE = "https://api.stlouisfed.org/fred"
FRED_API_KEY = "your_api_key_here"  # Free from https://fred.stlouisfed.org/docs/api/api_key.html

# Metal ETF mappings
METAL_ETFS = {
    'copper': 'CPER',      # United States Copper Index Fund
    'aluminum': 'JJU',     # iPath Bloomberg Aluminum SubTR ETN  
    'nickel': 'JJN',       # iPath Bloomberg Nickel SubTR ETN
    'zinc': 'JJZ'          # iPath Bloomberg Zinc SubTR ETN (proxy)
}

# FRED series for metal prices
FRED_SERIES = {
    'copper': 'PCOPPUSDM',      # Global price of Copper ($/MT)
    'aluminum': 'PALUMUSDM',    # Global price of Aluminum ($/MT)
    'zinc': 'PZINCUSDM',        # Global price of Zinc ($/MT)
    'nickel': 'PNICKUSDM',      # Global price of Nickel ($/MT)
    'lme_copper': 'PCOPPUSDM',
    'lme_aluminum': 'PALUMUSDM',
}

def get_yahoo_metal_price(etf_symbol: str, days: int = 90) -> Optional[Dict[str, Any]]:
    """
    Fetch metal ETF price data from Yahoo Finance
    
    Args:
        etf_symbol: ETF ticker (e.g., CPER, JJU)
        days: Historical period in days
    
    Returns:
        Dict with price history, current price, change%, volume
    """
    try:
        end_date = int(datetime.now().timestamp())
        start_date = int((datetime.now() - timedelta(days=days)).timestamp())
        
        url = f"{YAHOO_FINANCE_BASE}/{etf_symbol}"
        params = {
            'period1': start_date,
            'period2': end_date,
            'interval': '1d'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        result = data['chart']['result'][0]
        quotes = result['indicators']['quote'][0]
        timestamps = result['timestamp']
        
        closes = [p for p in quotes['close'] if p is not None]
        volumes = [v for v in quotes['volume'] if v is not None]
        
        if not closes:
            return None
        
        current_price = closes[-1]
        prev_price = closes[0]
        change_pct = ((current_price - prev_price) / prev_price) * 100
        
        # Calculate volatility
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        volatility = statistics.stdev(returns) * (252 ** 0.5) * 100 if len(returns) > 1 else 0
        
        # Trend analysis
        ma_20 = statistics.mean(closes[-20:]) if len(closes) >= 20 else current_price
        ma_50 = statistics.mean(closes[-50:]) if len(closes) >= 50 else current_price
        
        if current_price > ma_20 > ma_50:
            trend = "strong_uptrend"
        elif current_price > ma_20:
            trend = "uptrend"
        elif current_price < ma_20 < ma_50:
            trend = "strong_downtrend"
        elif current_price < ma_20:
            trend = "downtrend"
        else:
            trend = "sideways"
        
        return {
            'symbol': etf_symbol,
            'current_price': round(current_price, 2),
            'change_percent': round(change_pct, 2),
            'volume': int(volumes[-1]) if volumes else 0,
            'avg_volume_30d': int(statistics.mean(volumes[-30:])) if len(volumes) >= 30 else 0,
            'volatility_annual': round(volatility, 2),
            'ma_20': round(ma_20, 2),
            'ma_50': round(ma_50, 2),
            'trend': trend,
            'high_52w': round(max(closes), 2),
            'low_52w': round(min(closes), 2),
            'price_history': closes[-30:],  # Last 30 days
            'timestamps': timestamps[-30:]
        }
        
    except Exception as e:
        print(f"Error fetching {etf_symbol}: {e}", file=sys.stderr)
        return None

def get_fred_metal_price(series_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch metal price from FRED
    
    Args:
        series_id: FRED series ID (e.g., PCOPPUSDM for copper)
    
    Returns:
        Dict with current price, historical data, trend
    """
    try:
        # Note: In production, use actual FRED API key
        # For now, provide fallback data structure
        
        url = f"{FRED_BASE}/series/observations"
        params = {
            'series_id': series_id,
            'api_key': FRED_API_KEY,
            'file_type': 'json',
            'sort_order': 'desc',
            'limit': 90
        }
        
        # If API key not configured, return mock structure
        if FRED_API_KEY == "your_api_key_here":
            return {
                'series_id': series_id,
                'note': 'FRED API key not configured. Get free key at https://fred.stlouisfed.org/docs/api/api_key.html',
                'current_price': None,
                'unit': 'USD per Metric Ton'
            }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        observations = data['observations']
        values = [float(obs['value']) for obs in observations if obs['value'] != '.']
        dates = [obs['date'] for obs in observations if obs['value'] != '.']
        
        if not values:
            return None
        
        values.reverse()  # Chronological order
        dates.reverse()
        
        current_price = values[-1]
        prev_price = values[0]
        change_pct = ((current_price - prev_price) / prev_price) * 100
        
        # Calculate trend
        ma_30 = statistics.mean(values[-30:]) if len(values) >= 30 else current_price
        trend = "increasing" if current_price > ma_30 else "decreasing"
        
        return {
            'series_id': series_id,
            'current_price': round(current_price, 2),
            'unit': 'USD per Metric Ton',
            'change_percent_90d': round(change_pct, 2),
            'ma_30': round(ma_30, 2),
            'trend': trend,
            'latest_date': dates[-1],
            'price_history': values[-30:],
            'dates': dates[-30:]
        }
        
    except Exception as e:
        print(f"Error fetching FRED {series_id}: {e}", file=sys.stderr)
        return None

def get_copper_price() -> Dict[str, Any]:
    """
    Get LME copper price and analysis
    
    Returns:
        Current price, trend, correlation with industrial activity
    """
    etf_data = get_yahoo_metal_price(METAL_ETFS['copper'])
    fred_data = get_fred_metal_price(FRED_SERIES['copper'])
    
    result = {
        'metal': 'Copper',
        'symbol': 'Cu',
        'etf_data': etf_data,
        'fred_data': fred_data,
        'market_signal': None,
        'interpretation': {
            'copper': 'Leading indicator for global economy - Dr. Copper predicts economic cycles',
            'uses': 'Construction, electronics, electric vehicles, power grids',
            'key_consumers': 'China (54%), Europe (18%), US (8%)'
        }
    }
    
    # Generate market signal
    if etf_data and etf_data['trend'] in ['strong_uptrend', 'uptrend']:
        result['market_signal'] = 'bullish_economy'
    elif etf_data and etf_data['trend'] in ['strong_downtrend', 'downtrend']:
        result['market_signal'] = 'bearish_economy'
    else:
        result['market_signal'] = 'neutral'
    
    return result

def get_aluminum_price() -> Dict[str, Any]:
    """
    Get LME aluminum price and analysis
    
    Returns:
        Current price, trend, industrial demand signals
    """
    etf_data = get_yahoo_metal_price(METAL_ETFS['aluminum'])
    fred_data = get_fred_metal_price(FRED_SERIES['aluminum'])
    
    result = {
        'metal': 'Aluminum',
        'symbol': 'Al',
        'etf_data': etf_data,
        'fred_data': fred_data,
        'market_signal': None,
        'interpretation': {
            'aluminum': 'Key for transportation, packaging, construction - energy-intensive production',
            'uses': 'Aerospace, automotive, beverage cans, building materials',
            'key_consumers': 'China (56%), Europe (12%), US (11%)'
        }
    }
    
    # Generate market signal
    if etf_data and etf_data['trend'] in ['strong_uptrend', 'uptrend']:
        result['market_signal'] = 'strong_industrial_demand'
    elif etf_data and etf_data['trend'] in ['strong_downtrend', 'downtrend']:
        result['market_signal'] = 'weak_industrial_demand'
    else:
        result['market_signal'] = 'neutral'
    
    return result

def get_zinc_price() -> Dict[str, Any]:
    """
    Get LME zinc price and analysis
    
    Returns:
        Current price, trend, steel production correlation
    """
    etf_data = get_yahoo_metal_price(METAL_ETFS['zinc'])
    fred_data = get_fred_metal_price(FRED_SERIES['zinc'])
    
    result = {
        'metal': 'Zinc',
        'symbol': 'Zn',
        'etf_data': etf_data,
        'fred_data': fred_data,
        'market_signal': None,
        'interpretation': {
            'zinc': 'Primarily for galvanizing steel - corrosion protection',
            'uses': '50% galvanizing, 17% brass/bronze, 17% zinc alloys, 16% other',
            'key_consumers': 'China (48%), India (7%), EU (15%)'
        }
    }
    
    # Generate market signal
    if etf_data and etf_data['trend'] in ['strong_uptrend', 'uptrend']:
        result['market_signal'] = 'strong_steel_demand'
    elif etf_data and etf_data['trend'] in ['strong_downtrend', 'downtrend']:
        result['market_signal'] = 'weak_steel_demand'
    else:
        result['market_signal'] = 'neutral'
    
    return result

def get_nickel_price() -> Dict[str, Any]:
    """
    Get LME nickel price and analysis
    
    Returns:
        Current price, trend, EV battery demand signals
    """
    etf_data = get_yahoo_metal_price(METAL_ETFS['nickel'])
    fred_data = get_fred_metal_price(FRED_SERIES['nickel'])
    
    result = {
        'metal': 'Nickel',
        'symbol': 'Ni',
        'etf_data': etf_data,
        'fred_data': fred_data,
        'market_signal': None,
        'interpretation': {
            'nickel': 'Critical for stainless steel and EV batteries - high volatility',
            'uses': '70% stainless steel, 12% alloys, 9% plating, 9% batteries',
            'key_consumers': 'China (54%), Europe (13%), Japan (9%)',
            'battery_demand': 'Rapidly growing - NMC/NCA lithium-ion batteries for EVs'
        }
    }
    
    # Generate market signal
    if etf_data and etf_data['trend'] in ['strong_uptrend', 'uptrend']:
        result['market_signal'] = 'strong_ev_demand'
    elif etf_data and etf_data['trend'] in ['strong_downtrend', 'downtrend']:
        result['market_signal'] = 'weak_ev_demand'
    else:
        result['market_signal'] = 'neutral'
    
    return result

def get_metal_inventories() -> Dict[str, Any]:
    """
    Estimate metal inventory levels
    
    Note: Real LME inventory data requires paid subscription.
    This provides proxy indicators via ETF volumes and price action.
    
    Returns:
        Inventory signals, supply/demand balance indicators
    """
    metals_data = {}
    
    for metal, etf in METAL_ETFS.items():
        etf_data = get_yahoo_metal_price(etf, days=30)
        if etf_data:
            # Proxy inventory signal from volume and price action
            vol_ratio = etf_data['volume'] / etf_data['avg_volume_30d'] if etf_data['avg_volume_30d'] > 0 else 1
            
            # High volume + falling price = potential oversupply
            # Low volume + rising price = potential shortage
            if vol_ratio > 1.5 and etf_data['change_percent'] < -2:
                inventory_signal = 'oversupply_risk'
            elif vol_ratio < 0.7 and etf_data['change_percent'] > 2:
                inventory_signal = 'shortage_risk'
            elif etf_data['change_percent'] < -5:
                inventory_signal = 'weak_demand'
            elif etf_data['change_percent'] > 5:
                inventory_signal = 'strong_demand'
            else:
                inventory_signal = 'balanced'
            
            metals_data[metal] = {
                'current_price': etf_data['current_price'],
                'change_percent': etf_data['change_percent'],
                'volume_ratio': round(vol_ratio, 2),
                'inventory_signal': inventory_signal,
                'trend': etf_data['trend']
            }
    
    return {
        'metals': metals_data,
        'timestamp': datetime.now().isoformat(),
        'note': 'Inventory signals derived from price-volume analysis. Real LME warehouse data requires paid subscription.',
        'interpretation': {
            'oversupply_risk': 'High volume selling pressure - possible inventory buildup',
            'shortage_risk': 'Low liquidity + rising prices - potential supply constraints',
            'weak_demand': 'Price declining - demand softening or oversupply',
            'strong_demand': 'Price rising - demand exceeding supply',
            'balanced': 'Normal supply/demand dynamics'
        }
    }

def get_metals_snapshot() -> Dict[str, Any]:
    """
    Comprehensive snapshot of all industrial metals
    
    Returns:
        Current prices, trends, market signals for copper, aluminum, zinc, nickel
    """
    snapshot = {
        'timestamp': datetime.now().isoformat(),
        'metals': {
            'copper': get_copper_price(),
            'aluminum': get_aluminum_price(),
            'zinc': get_zinc_price(),
            'nickel': get_nickel_price()
        },
        'market_overview': None
    }
    
    # Generate overall market signal
    signals = [m['market_signal'] for m in snapshot['metals'].values() if m['market_signal']]
    bullish_count = sum(1 for s in signals if 'bullish' in s or 'strong' in s)
    bearish_count = sum(1 for s in signals if 'bearish' in s or 'weak' in s)
    
    if bullish_count >= 3:
        snapshot['market_overview'] = 'strong_industrial_expansion'
    elif bearish_count >= 3:
        snapshot['market_overview'] = 'industrial_contraction'
    else:
        snapshot['market_overview'] = 'mixed_signals'
    
    return snapshot

def get_metals_correlation() -> Dict[str, Any]:
    """
    Calculate correlation between industrial metals and economic indicators
    
    Returns:
        Correlation matrix, leading indicators, economic regime signals
    """
    metals = ['copper', 'aluminum', 'zinc', 'nickel']
    correlations = []
    
    # Fetch metal prices
    metal_data = {}
    for metal in metals:
        etf_data = get_yahoo_metal_price(METAL_ETFS[metal], days=90)
        if etf_data:
            metal_data[metal] = etf_data['price_history']
    
    # Calculate correlations between metals
    def correlation(x, y):
        if len(x) != len(y) or len(x) == 0:
            return 0
        min_len = min(len(x), len(y))
        x = x[:min_len]
        y = y[:min_len]
        
        # Calculate returns
        x_ret = [(x[i] - x[i-1]) / x[i-1] for i in range(1, len(x))]
        y_ret = [(y[i] - y[i-1]) / y[i-1] for i in range(1, len(y))]
        
        if len(x_ret) == 0:
            return 0
        
        mean_x = statistics.mean(x_ret)
        mean_y = statistics.mean(y_ret)
        cov = sum((x_ret[i] - mean_x) * (y_ret[i] - mean_y) for i in range(len(x_ret))) / len(x_ret)
        std_x = statistics.stdev(x_ret) if len(x_ret) > 1 else 1
        std_y = statistics.stdev(y_ret) if len(y_ret) > 1 else 1
        
        return cov / (std_x * std_y) if std_x * std_y != 0 else 0
    
    # Build correlation matrix
    for i, metal1 in enumerate(metals):
        for metal2 in metals[i+1:]:
            if metal1 in metal_data and metal2 in metal_data:
                corr = correlation(metal_data[metal1], metal_data[metal2])
                correlations.append({
                    'metal1': metal1,
                    'metal2': metal2,
                    'correlation': round(corr, 3)
                })
    
    # Calculate average correlation
    avg_corr = statistics.mean([abs(c['correlation']) for c in correlations]) if correlations else 0
    
    # Interpret correlation regime
    if avg_corr > 0.7:
        regime = 'synchronized_cycle'
        interpretation = 'All metals moving together - broad industrial demand/supply shock'
    elif avg_corr > 0.4:
        regime = 'normal_correlation'
        interpretation = 'Typical metal co-movement - general industrial cycle'
    else:
        regime = 'divergent'
        interpretation = 'Metals diverging - sector-specific factors dominating'
    
    return {
        'average_correlation': round(avg_corr, 3),
        'regime': regime,
        'interpretation': interpretation,
        'correlations': correlations,
        'leading_indicator': 'Copper (Dr. Copper) is the most reliable leading indicator for global economic activity',
        'market_insight': 'High correlation suggests macro-driven environment. Divergence indicates sector-specific narratives.'
    }

def main():
    """CLI dispatcher"""
    if len(sys.argv) < 2:
        print("Usage: python industrial_metals.py <command>")
        print("Commands: copper-price, aluminum-price, zinc-price, nickel-price, metal-inventories, metals-snapshot, metals-correlation")
        return 1
    
    command = sys.argv[1]
    
    if command == "copper-price":
        result = get_copper_price()
    elif command == "aluminum-price":
        result = get_aluminum_price()
    elif command == "zinc-price":
        result = get_zinc_price()
    elif command == "nickel-price":
        result = get_nickel_price()
    elif command == "metal-inventories":
        result = get_metal_inventories()
    elif command == "metals-snapshot":
        result = get_metals_snapshot()
    elif command == "metals-correlation":
        result = get_metals_correlation()
    else:
        print(f"Unknown command: {command}")
        return 1
    
    print(json.dumps(result, indent=2))
    return 0

if __name__ == '__main__':
    sys.exit(main())
