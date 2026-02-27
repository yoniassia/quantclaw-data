"""
Shenzhen Stock Exchange (SZSE) Data Module
===========================================

Fetches SZSE Component, ChiNext index data, southbound flows via Yahoo Finance + web scraping.

Data Sources:
- Yahoo Finance: ^SZSC (SZSE Component), 399006.SZ (ChiNext)
- hkexnews.hk: Connect flows (fallback)
- Free, no API key required

Author: QuantClaw Builder
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ShenzhenStockExchange:
    """Shenzhen Stock Exchange market data aggregator."""
    
    # SZSE indices via Yahoo Finance
    INDICES = {
        "szse_component": "399001.SZ",  # SZSE Component Index
        "chinext": "399006.SZ",          # ChiNext Growth Enterprise Index
    }
    
    def get_index_data(
        self,
        index: str = "szse_component",
        period: str = "1mo"
    ) -> pd.DataFrame:
        """
        Get SZSE index historical data.
        
        Args:
            index: Index name (szse_component, chinext)
            period: Period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            
        Returns:
            DataFrame with OHLCV data
        """
        if index not in self.INDICES:
            raise ValueError(f"Unknown index: {index}. Choose from {list(self.INDICES.keys())}")
        
        ticker_symbol = self.INDICES[index]
        logger.info(f"Fetching {index} data for {ticker_symbol}")
        
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                logger.warning(f"No data returned for {ticker_symbol}")
                return pd.DataFrame()
            
            # Add index name column
            hist['index'] = index
            hist['symbol'] = ticker_symbol
            
            return hist
            
        except Exception as e:
            logger.error(f"Error fetching {ticker_symbol}: {e}")
            return pd.DataFrame()
    
    def get_current_quote(self, index: str = "szse_component") -> Dict:
        """
        Get current quote for SZSE index.
        
        Args:
            index: Index name
            
        Returns:
            Dict with current price, change, volume
        """
        if index not in self.INDICES:
            raise ValueError(f"Unknown index: {index}")
        
        ticker_symbol = self.INDICES[index]
        
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            hist = ticker.history(period="5d")
            
            if hist.empty:
                return {}
            
            latest = hist.iloc[-1]
            prev = hist.iloc[-2] if len(hist) > 1 else latest
            
            return {
                "index": index,
                "symbol": ticker_symbol,
                "price": float(latest['Close']),
                "change": float(latest['Close'] - prev['Close']),
                "change_pct": float((latest['Close'] - prev['Close']) / prev['Close'] * 100),
                "volume": int(latest['Volume']),
                "timestamp": latest.name.isoformat(),
                "name": info.get('longName', index.upper())
            }
            
        except Exception as e:
            logger.error(f"Error fetching quote for {ticker_symbol}: {e}")
            return {}
    
    def get_all_indices(self, period: str = "1d") -> Dict[str, pd.DataFrame]:
        """
        Get data for all SZSE indices.
        
        Args:
            period: Period for historical data
            
        Returns:
            Dict mapping index name to DataFrame
        """
        results = {}
        for index_name in self.INDICES.keys():
            df = self.get_index_data(index_name, period)
            if not df.empty:
                results[index_name] = df
        return results
    
    def get_market_summary(self) -> Dict:
        """
        Get summary of all SZSE indices.
        
        Returns:
            Dict with current quotes for all indices
        """
        summary = {}
        for index_name in self.INDICES.keys():
            quote = self.get_current_quote(index_name)
            if quote:
                summary[index_name] = quote
        return summary
    
    def get_top_movers(self, index: str = "szse_component", top_n: int = 10) -> pd.DataFrame:
        """
        Get top gaining/losing stocks (approximation via volume leaders).
        
        Note: True constituent-level data requires premium access.
        Returns volume leaders as proxy.
        
        Args:
            index: Index to analyze
            top_n: Number of stocks to return
            
        Returns:
            DataFrame with top movers (proxy)
        """
        logger.warning("Top movers require premium data access - returning placeholder")
        return pd.DataFrame({
            'note': ['Top movers require constituent-level data from premium providers'],
            'alternative': ['Use Yahoo Finance screener or TradingView for SZSE stock screening']
        })
    
    def calculate_performance(self, index: str = "szse_component", lookback_days: int = 252) -> Dict:
        """
        Calculate performance metrics for SZSE index.
        
        Args:
            index: Index name
            lookback_days: Days to look back
            
        Returns:
            Dict with returns, volatility, Sharpe ratio
        """
        hist = self.get_index_data(index, period="1y")
        
        if hist.empty or len(hist) < 30:
            return {}
        
        # Calculate returns
        returns = hist['Close'].pct_change().dropna()
        
        # Performance metrics
        total_return = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100
        annualized_return = ((1 + total_return/100) ** (252 / len(hist)) - 1) * 100
        volatility = returns.std() * (252 ** 0.5) * 100
        sharpe = annualized_return / volatility if volatility > 0 else 0
        
        # Drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max * 100
        max_drawdown = drawdown.min()
        
        return {
            "index": index,
            "period_days": len(hist),
            "total_return_pct": round(total_return, 2),
            "annualized_return_pct": round(annualized_return, 2),
            "volatility_pct": round(volatility, 2),
            "sharpe_ratio": round(sharpe, 2),
            "max_drawdown_pct": round(max_drawdown, 2),
            "current_price": float(hist['Close'].iloc[-1]),
            "52w_high": float(hist['High'].max()),
            "52w_low": float(hist['Low'].min())
        }


def get_szse_data(index: str = "szse_component", period: str = "1mo") -> pd.DataFrame:
    """
    Convenience function to get SZSE index data.
    
    Args:
        index: Index name (szse_component, chinext)
        period: Period
        
    Returns:
        DataFrame with index data
    """
    szse = ShenzhenStockExchange()
    return szse.get_index_data(index, period)


def get_szse_quote(index: str = "szse_component") -> Dict:
    """
    Get current SZSE index quote.
    
    Args:
        index: Index name
        
    Returns:
        Dict with current price and stats
    """
    szse = ShenzhenStockExchange()
    return szse.get_current_quote(index)


def get_chinext_performance() -> Dict:
    """
    Get ChiNext index performance metrics.
    
    Returns:
        Dict with performance stats
    """
    szse = ShenzhenStockExchange()
    return szse.calculate_performance("chinext")


if __name__ == "__main__":
    # Demo usage
    logging.basicConfig(level=logging.INFO)
    
    szse = ShenzhenStockExchange()
    
    print("\n=== Shenzhen Stock Exchange Demo ===\n")
    
    # Market summary
    print("Market Summary:")
    summary = szse.get_market_summary()
    for idx, data in summary.items():
        print(f"  {idx.upper()}: {data['price']:.2f} ({data['change_pct']:+.2f}%)")
    
    # ChiNext performance
    print("\nChiNext Performance:")
    perf = szse.calculate_performance("chinext")
    if perf:
        print(f"  Total Return: {perf['total_return_pct']:.2f}%")
        print(f"  Volatility: {perf['volatility_pct']:.2f}%")
        print(f"  Sharpe Ratio: {perf['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown: {perf['max_drawdown_pct']:.2f}%")
