import requests
from typing import Dict, List
import time  # For mock delays

__doc__ = """Module for AlphaGen ML data fetching. Uses mock data to simulate API responses without real keys."""

def get_alphagen_data(symbol: str, interval: str = 'daily') -> Dict:
    """
    Fetches mock financial data for a given stock symbol and interval.

    Args:
        symbol (str): Stock symbol (e.g., 'AAPL').
        interval (str): Data interval (e.g., 'daily', 'weekly').

    Returns:
        Dict: Mock data structure with OHLC prices.

    Raises:
        ValueError: If symbol is invalid.
        Exception: For simulation of API errors.
    """
    if not symbol:
        raise ValueError("Symbol cannot be empty.")
    
    try:
        # Mock API call - in reality, this would hit an endpoint, but we're using static data
        time.sleep(1)  # Simulate network delay
        mock_data = {
            'symbol': symbol.upper(),
            'interval': interval,
            'data': [
                {'date': '2026-03-08', 'open': 150.0, 'high': 152.0, 'low': 148.0, 'close': 151.0},
                {'date': '2026-03-07', 'open': 149.0, 'high': 151.0, 'low': 147.0, 'close': 150.0}
            ]
        }
        return mock_data
    except Exception as e:
        raise Exception(f"Mock API error: {str(e)}")

def get_multiple_symbols(symbols: List[str]) -> List[Dict]:
    """
    Fetches mock data for a list of symbols.

    Args:
        symbols (List[str]): List of stock symbols.

    Returns:
        List[Dict]: List of mock data dictionaries.

    Raises:
        ValueError: If symbols list is empty.
    """
    if not symbols:
        raise ValueError("Symbols list cannot be empty.")
    
    return [get_alphagen_data(symbol) for symbol in symbols]

