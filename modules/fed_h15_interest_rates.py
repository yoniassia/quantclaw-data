"""
Fed H.15 Interest Rates Module

Fetches daily selected interest rates from FRED (Federal Reserve Economic Data).
Data includes fed funds, commercial paper, Treasury yields, SOFR, and swap rates.

Free public data, no API key required.
Source: https://fred.stlouisfed.org/

This module provides the building blocks for:
- Yield curve analysis
- Short-term rate monitoring
- SOFR tracking (replacing LIBOR)
- Money market conditions
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict
from io import StringIO


class FedH15RatesError(Exception):
    """Custom exception for Fed H.15 rate fetching errors."""
    pass


def fetch_fred_series(series_id: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch a single FRED series.
    
    Args:
        series_id: FRED series ID (e.g., "DGS10" for 10-year Treasury)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        DataFrame with columns: date, rate
    """
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        df = pd.read_csv(StringIO(response.text))
        df.columns = ['date', 'rate']
        df['date'] = pd.to_datetime(df['date'])
        df['rate'] = pd.to_numeric(df['rate'], errors='coerce')
        
        # Filter by date range
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        df = df.dropna(subset=['rate'])
        
        return df
        
    except Exception as e:
        raise FedH15RatesError(f"Failed to fetch {series_id}: {e}")


def fetch_h15_rates(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    rate_type: str = "all"
) -> pd.DataFrame:
    """
    Fetch H.15 selected interest rates from FRED.
    
    Args:
        start_date: Start date (YYYY-MM-DD). Defaults to 90 days ago.
        end_date: End date (YYYY-MM-DD). Defaults to today.
        rate_type: Type of rates to fetch:
            - "all": All available rates
            - "treasury": Treasury yields only
            - "fed_funds": Fed funds rate only
            - "sofr": SOFR only
            - "commercial_paper": Commercial paper rates
            - "swaps": Interest rate swaps
    
    Returns:
        DataFrame with columns: date, series_name, rate
    
    Examples:
        >>> # Get all rates for last 90 days
        >>> df = fetch_h15_rates()
        
        >>> # Get Treasury yields for 2024
        >>> df = fetch_h15_rates("2024-01-01", "2024-12-31", "treasury")
        
        >>> # Get current SOFR
        >>> df = fetch_h15_rates(rate_type="sofr")
    """
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    
    # FRED series IDs for key H.15 rates
    series_map = {
        "fed_funds": "DFF",  # Effective federal funds rate
        "sofr": "SOFR",  # Secured Overnight Financing Rate
        "treasury_1m": "DGS1MO",  # 1-month Treasury
        "treasury_3m": "DGS3MO",  # 3-month Treasury
        "treasury_6m": "DGS6MO",  # 6-month Treasury
        "treasury_1y": "DGS1",    # 1-year Treasury
        "treasury_2y": "DGS2",    # 2-year Treasury
        "treasury_3y": "DGS3",    # 3-year Treasury
        "treasury_5y": "DGS5",    # 5-year Treasury
        "treasury_7y": "DGS7",    # 7-year Treasury
        "treasury_10y": "DGS10",  # 10-year Treasury
        "treasury_20y": "DGS20",  # 20-year Treasury
        "treasury_30y": "DGS30",  # 30-year Treasury
        "commercial_paper_1m": "DCPN1M",  # 1-month AA commercial paper
        "commercial_paper_3m": "DCPN3M",  # 3-month AA commercial paper
        "swap_1y": "DSWP1",       # 1-year interest rate swap
        "swap_2y": "DSWP2",       # 2-year interest rate swap
        "swap_5y": "DSWP5",       # 5-year interest rate swap
        "swap_10y": "DSWP10",     # 10-year interest rate swap
        "swap_30y": "DSWP30",     # 30-year interest rate swap
    }
    
    # Filter series based on rate_type
    if rate_type == "treasury":
        series_to_fetch = {k: v for k, v in series_map.items() if k.startswith("treasury")}
    elif rate_type == "fed_funds":
        series_to_fetch = {"fed_funds": series_map["fed_funds"]}
    elif rate_type == "sofr":
        series_to_fetch = {"sofr": series_map["sofr"]}
    elif rate_type == "commercial_paper":
        series_to_fetch = {k: v for k, v in series_map.items() if k.startswith("commercial_paper")}
    elif rate_type == "swaps":
        series_to_fetch = {k: v for k, v in series_map.items() if k.startswith("swap")}
    elif rate_type == "all":
        series_to_fetch = series_map
    else:
        raise FedH15RatesError(f"Invalid rate_type: {rate_type}")
    
    all_data = []
    
    for series_name, series_id in series_to_fetch.items():
        try:
            df = fetch_fred_series(series_id, start_date, end_date)
            df['series_name'] = series_name
            all_data.append(df[['date', 'series_name', 'rate']])
        except Exception as e:
            print(f"Warning: Could not fetch {series_name}: {e}")
            continue
    
    if not all_data:
        raise FedH15RatesError("No data could be fetched from FRED")
    
    result = pd.concat(all_data, ignore_index=True)
    result = result.sort_values('date')
    
    return result


def get_current_rates(rate_type: str = "all") -> Dict[str, float]:
    """
    Get the most recent values for each rate series.
    
    Args:
        rate_type: Same as fetch_h15_rates (all, treasury, fed_funds, etc.)
    
    Returns:
        Dictionary mapping series_name to latest rate value
    
    Examples:
        >>> rates = get_current_rates("treasury")
        >>> print(f"10Y Treasury: {rates['treasury_10y']:.2f}%")
    """
    df = fetch_h15_rates(rate_type=rate_type)
    latest = df.sort_values('date').groupby('series_name').tail(1)
    return dict(zip(latest['series_name'], latest['rate']))


def get_yield_curve(date: Optional[str] = None) -> pd.DataFrame:
    """
    Get Treasury yield curve for a specific date.
    
    Args:
        date: Date (YYYY-MM-DD). Defaults to most recent.
    
    Returns:
        DataFrame with columns: maturity_months, rate
        Sorted by maturity
    
    Examples:
        >>> curve = get_yield_curve()
        >>> print(curve)
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    df = fetch_h15_rates(start_date=date, end_date=date, rate_type="treasury")
    
    if df.empty:
        # Fetch last 7 days and get most recent
        df = fetch_h15_rates(
            start_date=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            rate_type="treasury"
        )
        if df.empty:
            raise FedH15RatesError("No recent Treasury yield data available")
        
        latest_date = df['date'].max()
        df = df[df['date'] == latest_date]
    
    # Map series names to maturity in months
    maturity_map = {
        "treasury_1m": 1,
        "treasury_3m": 3,
        "treasury_6m": 6,
        "treasury_1y": 12,
        "treasury_2y": 24,
        "treasury_3y": 36,
        "treasury_5y": 60,
        "treasury_7y": 84,
        "treasury_10y": 120,
        "treasury_20y": 240,
        "treasury_30y": 360,
    }
    
    df['maturity_months'] = df['series_name'].map(maturity_map)
    curve = df[['maturity_months', 'rate']].dropna().sort_values('maturity_months')
    
    return curve


def calculate_yield_curve_slope(date: Optional[str] = None) -> Dict[str, float]:
    """
    Calculate key yield curve slope metrics.
    
    Args:
        date: Date (YYYY-MM-DD). Defaults to most recent.
    
    Returns:
        Dictionary with spreads and steepness metrics
    """
    curve = get_yield_curve(date)
    
    rates = dict(zip(curve['maturity_months'], curve['rate']))
    
    # Common spreads (in basis points)
    spread_2y_10y = rates.get(120, 0) - rates.get(24, 0)
    spread_3m_10y = rates.get(120, 0) - rates.get(3, 0)
    spread_2y_30y = rates.get(360, 0) - rates.get(24, 0)
    steepness = rates.get(360, 0) - rates.get(3, 0)
    
    return {
        "2y_10y_spread": spread_2y_10y,
        "3m_10y_spread": spread_3m_10y,
        "2y_30y_spread": spread_2y_30y,
        "curve_steepness": steepness,
    }


def analyze_rate_changes(days: int = 30) -> pd.DataFrame:
    """
    Analyze rate changes over a period.
    
    Args:
        days: Number of days to look back
    
    Returns:
        DataFrame with rate changes
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    df = fetch_h15_rates(start_date=start_date, end_date=end_date)
    
    results = []
    for series in df['series_name'].unique():
        series_data = df[df['series_name'] == series].sort_values('date')
        
        if len(series_data) < 2:
            continue
        
        initial_rate = series_data.iloc[0]['rate']
        current_rate = series_data.iloc[-1]['rate']
        rate_change = current_rate - initial_rate
        pct_change = (rate_change / initial_rate * 100) if initial_rate != 0 else 0
        
        results.append({
            'series_name': series,
            'current_rate': current_rate,
            'rate_change': rate_change,
            'pct_change': pct_change,
        })
    
    return pd.DataFrame(results)


def main():
    """CLI entry point."""
    import sys
    
    rate_type = sys.argv[1] if len(sys.argv) > 1 else "treasury"
    
    print(f"Fetching Fed H.15 rates via FRED (type: {rate_type})...")
    
    try:
        current = get_current_rates(rate_type)
        print("\n📊 Current Rates:")
        for name, rate in sorted(current.items()):
            print(f"  {name:25s}: {rate:6.2f}%")
        
        if rate_type in ["all", "treasury"]:
            print("\n📈 Yield Curve Slopes:")
            slopes = calculate_yield_curve_slope()
            for name, value in slopes.items():
                indicator = "⚠️ INVERTED" if value < 0 else "✅"
                print(f"  {name:20s}: {value:+6.2f} bps {indicator if 'spread' in name else ''}")
        
        print("\n📉 30-Day Changes:")
        changes = analyze_rate_changes(days=30)
        if not changes.empty:
            top_movers = changes.nlargest(min(5, len(changes)), 'pct_change')
            for _, row in top_movers.iterrows():
                print(f"  {row['series_name']:25s}: {row['current_rate']:6.2f}% ({row['pct_change']:+6.2f}%)")
        
    except FedH15RatesError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
