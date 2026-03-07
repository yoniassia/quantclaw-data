#!/usr/bin/env python3
"""
OpenBB SDK — Open-Source Financial Data Aggregator

OpenBB SDK is an open-source Python library for accessing financial data from 
multiple providers (Yahoo Finance, Alpha Vantage, FRED, etc.). Enables quant 
analysis, backtesting, and ML model training with unified interface for stocks, 
crypto, economics, and more.

Source: https://docs.openbb.co/sdk
Category: Quant Tools & ML
Free tier: True - Fully free and open-source; no rate limits
Author: QuantClaw Data NightBuilder
Phase: 105
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# ========== OPENBB SDK IMPORT WITH GRACEFUL FALLBACK ==========

try:
    from openbb import obb
    OPENBB_AVAILABLE = True
except ImportError:
    OPENBB_AVAILABLE = False
    obb = None

# ========== INSTALLATION HELPER ==========

def get_installation_message() -> Dict[str, Any]:
    """Return installation instructions if OpenBB SDK is not available."""
    return {
        "error": "OpenBB SDK not installed",
        "install_command": "pip install openbb",
        "documentation": "https://docs.openbb.co/sdk",
        "note": "After installation, restart your Python environment"
    }

# ========== STOCK DATA FUNCTIONS ==========

def get_stock_quote(symbol: str) -> Dict[str, Any]:
    """
    Get real-time stock quote for a given symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        
    Returns:
        Dict with quote data: symbol, price, volume, change, etc.
    """
    if not OPENBB_AVAILABLE:
        return get_installation_message()
    
    try:
        result = obb.equity.price.quote(symbol=symbol, provider="yfinance")
        
        if not result or not result.results:
            return {"error": f"No data found for symbol: {symbol}"}
        
        data = result.results[0]
        
        return {
            "symbol": symbol.upper(),
            "price": getattr(data, 'last_price', getattr(data, 'price', None)),
            "open": getattr(data, 'open', None),
            "high": getattr(data, 'high', None),
            "low": getattr(data, 'low', None),
            "volume": getattr(data, 'volume', None),
            "previous_close": getattr(data, 'previous_close', None),
            "change": getattr(data, 'change', None),
            "change_percent": getattr(data, 'change_percent', None),
            "timestamp": datetime.now().isoformat(),
            "provider": "yfinance"
        }
        
    except Exception as e:
        return {
            "error": f"Failed to fetch quote for {symbol}",
            "details": str(e),
            "symbol": symbol
        }

def get_historical_prices(symbol: str, start: str, end: str, interval: str = "1d") -> Dict[str, Any]:
    """
    Get historical price data for a stock.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        start: Start date in YYYY-MM-DD format
        end: End date in YYYY-MM-DD format
        interval: Data interval ('1d', '1h', '1m', etc.)
        
    Returns:
        Dict with historical prices list and metadata
    """
    if not OPENBB_AVAILABLE:
        return get_installation_message()
    
    try:
        result = obb.equity.price.historical(
            symbol=symbol,
            start_date=start,
            end_date=end,
            interval=interval,
            provider="yfinance"
        )
        
        if not result or not result.results:
            return {
                "error": f"No historical data found for {symbol}",
                "symbol": symbol,
                "start": start,
                "end": end
            }
        
        prices = []
        for record in result.results:
            prices.append({
                "date": str(getattr(record, 'date', '')),
                "open": getattr(record, 'open', None),
                "high": getattr(record, 'high', None),
                "low": getattr(record, 'low', None),
                "close": getattr(record, 'close', None),
                "volume": getattr(record, 'volume', None),
                "adjusted_close": getattr(record, 'adj_close', None)
            })
        
        return {
            "symbol": symbol.upper(),
            "interval": interval,
            "start_date": start,
            "end_date": end,
            "count": len(prices),
            "data": prices,
            "provider": "yfinance"
        }
        
    except Exception as e:
        return {
            "error": f"Failed to fetch historical data for {symbol}",
            "details": str(e),
            "symbol": symbol,
            "start": start,
            "end": end
        }

def get_company_fundamentals(symbol: str) -> Dict[str, Any]:
    """
    Get company fundamental data (financials, metrics, profile).
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Dict with company fundamentals
    """
    if not OPENBB_AVAILABLE:
        return get_installation_message()
    
    try:
        # Get company profile
        profile_result = obb.equity.profile(symbol=symbol, provider="yfinance")
        
        if not profile_result or not profile_result.results:
            return {"error": f"No fundamental data found for {symbol}"}
        
        profile = profile_result.results[0]
        
        fundamentals = {
            "symbol": symbol.upper(),
            "name": getattr(profile, 'name', None),
            "sector": getattr(profile, 'sector', None),
            "industry": getattr(profile, 'industry', None),
            "market_cap": getattr(profile, 'market_cap', None),
            "employees": getattr(profile, 'employees', None),
            "description": getattr(profile, 'description', None),
            "website": getattr(profile, 'website', None),
            "ceo": getattr(profile, 'ceo', None),
            "provider": "yfinance"
        }
        
        # Try to get key metrics
        try:
            metrics_result = obb.equity.fundamental.metrics(symbol=symbol, provider="yfinance")
            if metrics_result and metrics_result.results:
                metrics = metrics_result.results[0]
                fundamentals.update({
                    "pe_ratio": getattr(metrics, 'pe_ratio', None),
                    "forward_pe": getattr(metrics, 'forward_pe', None),
                    "peg_ratio": getattr(metrics, 'peg_ratio', None),
                    "price_to_book": getattr(metrics, 'price_to_book', None),
                    "dividend_yield": getattr(metrics, 'dividend_yield', None),
                    "beta": getattr(metrics, 'beta', None),
                })
        except:
            pass  # Metrics are optional
        
        return fundamentals
        
    except Exception as e:
        return {
            "error": f"Failed to fetch fundamentals for {symbol}",
            "details": str(e),
            "symbol": symbol
        }

# ========== CRYPTO DATA FUNCTIONS ==========

def get_crypto_price(symbol: str) -> Dict[str, Any]:
    """
    Get real-time cryptocurrency price.
    
    Args:
        symbol: Crypto symbol (e.g., 'BTC', 'ETH', 'BTCUSD')
        
    Returns:
        Dict with crypto price data
    """
    if not OPENBB_AVAILABLE:
        return get_installation_message()
    
    try:
        # Normalize symbol (add USD if not present)
        if not symbol.upper().endswith('USD') and len(symbol) <= 4:
            symbol = f"{symbol}USD"
        
        result = obb.crypto.price.historical(
            symbol=symbol,
            interval="1d",
            provider="yfinance"
        )
        
        if not result or not result.results:
            return {"error": f"No crypto data found for {symbol}"}
        
        # Get the latest price (most recent record)
        latest = result.results[-1]
        
        return {
            "symbol": symbol.upper(),
            "price": getattr(latest, 'close', None),
            "open": getattr(latest, 'open', None),
            "high": getattr(latest, 'high', None),
            "low": getattr(latest, 'low', None),
            "volume": getattr(latest, 'volume', None),
            "timestamp": str(getattr(latest, 'date', datetime.now().isoformat())),
            "provider": "yfinance"
        }
        
    except Exception as e:
        return {
            "error": f"Failed to fetch crypto price for {symbol}",
            "details": str(e),
            "symbol": symbol
        }

# ========== ECONOMIC DATA FUNCTIONS ==========

def get_economic_indicator(series_id: str, start: Optional[str] = None, end: Optional[str] = None) -> Dict[str, Any]:
    """
    Get economic indicator data from FRED.
    
    Args:
        series_id: FRED series ID (e.g., 'GDP', 'UNRATE', 'DFF')
        start: Start date in YYYY-MM-DD format (optional)
        end: End date in YYYY-MM-DD format (optional)
        
    Returns:
        Dict with economic indicator data
    """
    if not OPENBB_AVAILABLE:
        return get_installation_message()
    
    try:
        # Default to last 5 years if no dates provided
        if not end:
            end = datetime.now().strftime("%Y-%m-%d")
        if not start:
            start = (datetime.now() - timedelta(days=365*5)).strftime("%Y-%m-%d")
        
        result = obb.economy.fred_series(
            symbol=series_id,
            start_date=start,
            end_date=end,
            provider="fred"
        )
        
        if not result or not result.results:
            return {
                "error": f"No data found for series: {series_id}",
                "series_id": series_id
            }
        
        data_points = []
        for record in result.results:
            data_points.append({
                "date": str(getattr(record, 'date', '')),
                "value": getattr(record, 'value', None)
            })
        
        return {
            "series_id": series_id.upper(),
            "start_date": start,
            "end_date": end,
            "count": len(data_points),
            "data": data_points,
            "provider": "fred"
        }
        
    except Exception as e:
        return {
            "error": f"Failed to fetch economic data for {series_id}",
            "details": str(e),
            "series_id": series_id
        }

# ========== UTILITY FUNCTIONS ==========

def list_available_providers() -> List[str]:
    """
    List available data providers in OpenBB SDK.
    
    Returns:
        List of provider names
    """
    if not OPENBB_AVAILABLE:
        return []
    
    try:
        # Common providers available in OpenBB
        providers = [
            "yfinance",
            "fred",
            "alpha_vantage",
            "polygon",
            "fmp",
            "intrinio",
            "benzinga",
            "nasdaq",
            "sec"
        ]
        return providers
    except:
        return []

def get_module_status() -> Dict[str, Any]:
    """
    Get module status and availability information.
    
    Returns:
        Dict with module status
    """
    return {
        "module": "openbb_sdk",
        "available": OPENBB_AVAILABLE,
        "version": "105",
        "providers": list_available_providers() if OPENBB_AVAILABLE else [],
        "functions": [
            "get_stock_quote",
            "get_historical_prices",
            "get_company_fundamentals",
            "get_crypto_price",
            "get_economic_indicator",
            "list_available_providers"
        ],
        "install_command": "pip install openbb" if not OPENBB_AVAILABLE else None
    }

# ========== MAIN ENTRYPOINT ==========

if __name__ == "__main__":
    status = get_module_status()
    print(json.dumps(status, indent=2))
    
    if OPENBB_AVAILABLE:
        print("\n✅ OpenBB SDK is available")
        print("\nTesting stock quote for AAPL...")
        quote = get_stock_quote("AAPL")
        print(json.dumps(quote, indent=2))
    else:
        print("\n❌ OpenBB SDK is not installed")
        print(json.dumps(get_installation_message(), indent=2))
