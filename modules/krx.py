"""
Korea Exchange (KRX) Data Module
KOSPI, KOSDAQ indices, foreign ownership, derivatives
Data from Yahoo Finance + KRX open data
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

# Major KRX indices and ETFs available via Yahoo Finance
KRX_TICKERS = {
    "KOSPI": "^KS11",         # KOSPI Index
    "KOSDAQ": "^KQ11",        # KOSDAQ Index
    "KRW200": "^KS200",       # KOSPI 200
    "TIGER200": "102110.KS",  # KOSPI 200 ETF
    "KODEX200": "069500.KS",  # KOSPI 200 ETF
}

# Top Korean stocks (ADRs available)
TOP_KOREAN_STOCKS = {
    "Samsung Electronics": "005930.KS",
    "SK Hynix": "000660.KS",
    "LG Energy Solution": "373220.KS",
    "Samsung Biologics": "207940.KS",
    "Hyundai Motor": "005380.KS",
    "Kia Corporation": "000270.KS",
    "POSCO Holdings": "005490.KS",
    "KB Financial": "105560.KS",
    "Naver": "035420.KS",
    "Kakao": "035720.KS",
    "LG Chem": "051910.KS",
    "Samsung SDI": "006400.KS",
    "Shinhan Financial": "055550.KS",
    "Celltrion": "068270.KS",
    "SK Innovation": "096770.KS",
}


def get_krx_indices(period: str = "1mo") -> pd.DataFrame:
    """
    Fetch KRX index data (KOSPI, KOSDAQ, KOSPI 200)
    
    Args:
        period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
    
    Returns:
        DataFrame with index data
    """
    logger.info(f"Fetching KRX indices for period: {period}")
    
    results = []
    for name, ticker in KRX_TICKERS.items():
        try:
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period=period)
            
            if not hist.empty:
                latest = hist.iloc[-1]
                first = hist.iloc[0]
                
                change_pct = ((latest['Close'] - first['Close']) / first['Close']) * 100
                
                results.append({
                    'index': name,
                    'ticker': ticker,
                    'last_close': round(latest['Close'], 2),
                    'high': round(hist['High'].max(), 2),
                    'low': round(hist['Low'].min(), 2),
                    'volume_avg': int(hist['Volume'].mean()),
                    'change_pct': round(change_pct, 2),
                    'last_update': hist.index[-1].strftime('%Y-%m-%d')
                })
        except Exception as e:
            logger.warning(f"Failed to fetch {name}: {e}")
    
    return pd.DataFrame(results)


def get_kospi_composition(limit: int = 50) -> pd.DataFrame:
    """
    Get top KOSPI stocks by market cap
    
    Args:
        limit: Number of top stocks to return
    
    Returns:
        DataFrame with stock data
    """
    logger.info(f"Fetching top {limit} KOSPI stocks")
    
    stocks_data = []
    for name, ticker in list(TOP_KOREAN_STOCKS.items())[:limit]:
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            
            # Get 1-month history for trend
            hist = ticker_obj.history(period="1mo")
            
            if hist.empty:
                continue
            
            latest = hist.iloc[-1]
            first = hist.iloc[0]
            change_1m = ((latest['Close'] - first['Close']) / first['Close']) * 100
            
            stocks_data.append({
                'name': name,
                'ticker': ticker,
                'price': round(latest['Close'], 0),
                'market_cap_krw': info.get('marketCap', 0) / 1e9,  # Billions
                'volume': int(latest['Volume']),
                'change_1m_pct': round(change_1m, 2),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
            })
        except Exception as e:
            logger.warning(f"Failed to fetch {name}: {e}")
    
    df = pd.DataFrame(stocks_data)
    if not df.empty:
        df = df.sort_values('market_cap_krw', ascending=False)
    
    return df


def get_foreign_ownership_proxy(ticker: str = "^KS11") -> Dict:
    """
    Estimate foreign ownership trends via ETF flows
    (Real foreign ownership data requires KRX direct access)
    
    Args:
        ticker: KRX ticker (default KOSPI)
    
    Returns:
        Dictionary with proxy metrics
    """
    logger.info(f"Analyzing foreign ownership proxy for {ticker}")
    
    try:
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period="3mo")
        
        if hist.empty:
            return {}
        
        # Use volume trends as proxy for foreign participation
        recent_vol = hist['Volume'].tail(20).mean()
        older_vol = hist['Volume'].head(20).mean()
        volume_trend = ((recent_vol - older_vol) / older_vol) * 100
        
        # Price momentum (foreign investors often lead trends)
        latest = hist.iloc[-1]['Close']
        ma_20 = hist['Close'].tail(20).mean()
        ma_60 = hist['Close'].tail(60).mean()
        
        return {
            'ticker': ticker,
            'recent_volume_avg': int(recent_vol),
            'volume_trend_pct': round(volume_trend, 2),
            'price_vs_ma20_pct': round(((latest - ma_20) / ma_20) * 100, 2),
            'price_vs_ma60_pct': round(((latest - ma_60) / ma_60) * 100, 2),
            'trend': 'Bullish' if latest > ma_20 > ma_60 else 'Bearish' if latest < ma_20 < ma_60 else 'Mixed',
            'note': 'Proxy metrics - real foreign ownership requires KRX data subscription'
        }
    except Exception as e:
        logger.error(f"Foreign ownership analysis failed: {e}")
        return {}


def get_sector_performance() -> pd.DataFrame:
    """
    Analyze sector performance via sector ETFs and major stocks
    
    Returns:
        DataFrame with sector performance
    """
    logger.info("Analyzing Korean sector performance")
    
    # Map top stocks to sectors for sector analysis
    sector_stocks = {}
    for name, ticker in TOP_KOREAN_STOCKS.items():
        try:
            info = yf.Ticker(ticker).info
            sector = info.get('sector', 'Unknown')
            if sector not in sector_stocks:
                sector_stocks[sector] = []
            sector_stocks[sector].append(ticker)
        except:
            pass
    
    sector_data = []
    for sector, tickers in sector_stocks.items():
        try:
            # Calculate sector average performance
            performances = []
            for ticker in tickers:
                hist = yf.Ticker(ticker).history(period="1mo")
                if not hist.empty:
                    change = ((hist.iloc[-1]['Close'] - hist.iloc[0]['Close']) / hist.iloc[0]['Close']) * 100
                    performances.append(change)
            
            if performances:
                sector_data.append({
                    'sector': sector,
                    'num_stocks': len(tickers),
                    'avg_change_1m': round(sum(performances) / len(performances), 2),
                    'best': round(max(performances), 2),
                    'worst': round(min(performances), 2),
                })
        except Exception as e:
            logger.warning(f"Sector {sector} analysis failed: {e}")
    
    df = pd.DataFrame(sector_data)
    if not df.empty:
        df = df.sort_values('avg_change_1m', ascending=False)
    
    return df


def get_market_summary() -> Dict:
    """
    Get comprehensive KRX market summary
    
    Returns:
        Dictionary with market overview
    """
    logger.info("Generating KRX market summary")
    
    try:
        # Get index data
        indices = get_krx_indices(period="1mo")
        
        # Get KOSPI latest
        kospi = yf.Ticker("^KS11")
        kospi_hist = kospi.history(period="5d")
        
        if kospi_hist.empty:
            return {'error': 'Unable to fetch market data'}
        
        latest = kospi_hist.iloc[-1]
        prev = kospi_hist.iloc[-2] if len(kospi_hist) > 1 else kospi_hist.iloc[-1]
        
        daily_change = latest['Close'] - prev['Close']
        daily_change_pct = (daily_change / prev['Close']) * 100
        
        # Calculate volatility (20-day)
        kospi_1m = kospi.history(period="1mo")
        volatility = kospi_1m['Close'].pct_change().std() * (252 ** 0.5) * 100  # Annualized
        
        summary = {
            'market': 'Korea Exchange (KRX)',
            'kospi_level': round(latest['Close'], 2),
            'kospi_change': round(daily_change, 2),
            'kospi_change_pct': round(daily_change_pct, 2),
            'volume': int(latest['Volume']),
            'volatility_annual_pct': round(volatility, 2),
            'indices_tracked': len(indices),
            'timestamp': datetime.now().isoformat(),
            'note': 'Data from Yahoo Finance - for professional use, consider KRX Data subscription'
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Market summary failed: {e}")
        return {'error': str(e)}


def cli_krx_indices(period: str = "1mo"):
    """CLI command to display KRX indices"""
    df = get_krx_indices(period=period)
    if df.empty:
        print("❌ No data available")
        return
    
    print(f"\n📊 KRX Indices ({period})\n")
    print(df.to_string(index=False))


def cli_krx_top_stocks(limit: int = 20):
    """CLI command to display top KOSPI stocks"""
    df = get_kospi_composition(limit=limit)
    if df.empty:
        print("❌ No data available")
        return
    
    print(f"\n🇰🇷 Top {limit} KOSPI Stocks by Market Cap\n")
    print(df.to_string(index=False))


def cli_krx_summary():
    """CLI command to display market summary"""
    summary = get_market_summary()
    
    print("\n🇰🇷 KRX Market Summary\n")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    # Test module
    print("Testing KRX module...")
    
    print("\n1. Indices:")
    cli_krx_indices()
    
    print("\n2. Top Stocks:")
    cli_krx_top_stocks(10)
    
    print("\n3. Market Summary:")
    cli_krx_summary()
