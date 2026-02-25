"""
Options Flow Scanner - Phase 6
Detects unusual options activity, dark pool prints, sweep detection, smart money tracking.
Data: Yahoo Finance options chains + volume analysis
"""

import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import json
import os
from dataclasses import dataclass, asdict


@dataclass
class OptionsFlow:
    """Represents unusual options activity"""
    symbol: str
    timestamp: str
    expiration: str
    strike: float
    call_or_put: str
    volume: int
    open_interest: int
    volume_oi_ratio: float
    iv: Optional[float]
    premium: Optional[float]
    trade_type: str  # sweep, block, unusual
    sentiment: str  # bullish, bearish, neutral
    

class OptionsFlowScanner:
    """Scan for unusual options activity and smart money flows"""
    
    CACHE_DIR = "cache/options_flow"
    CACHE_TTL = 300  # 5 minutes
    
    # Thresholds for unusual activity detection
    VOLUME_OI_THRESHOLD = 2.0  # Volume must be 2x+ open interest
    MIN_VOLUME = 500  # Minimum contract volume
    MIN_PREMIUM = 100000  # $100k minimum premium
    
    def __init__(self):
        os.makedirs(self.CACHE_DIR, exist_ok=True)
    
    def scan_ticker(self, symbol: str, min_premium: int = 50000) -> List[OptionsFlow]:
        """
        Scan a ticker for unusual options activity
        
        Args:
            symbol: Stock ticker
            min_premium: Minimum premium in USD
            
        Returns:
            List of unusual options flows
        """
        cache_key = f"{symbol}_flow"
        cached = self._get_cache(cache_key)
        if cached:
            return [OptionsFlow(**flow) for flow in cached]
        
        try:
            ticker = yf.Ticker(symbol)
            expiration_dates = ticker.options
            
            if not expiration_dates:
                return []
            
            flows = []
            current_price = self._get_current_price(ticker)
            
            # Scan next 3 expiration dates (near-term activity most relevant)
            for exp_date in expiration_dates[:3]:
                opt_chain = ticker.option_chain(exp_date)
                
                # Scan calls
                for _, row in opt_chain.calls.iterrows():
                    flow = self._analyze_option(
                        symbol, exp_date, row, 'call', current_price, min_premium
                    )
                    if flow:
                        flows.append(flow)
                
                # Scan puts
                for _, row in opt_chain.puts.iterrows():
                    flow = self._analyze_option(
                        symbol, exp_date, row, 'put', current_price, min_premium
                    )
                    if flow:
                        flows.append(flow)
            
            # Sort by premium (smart money indicator)
            flows.sort(key=lambda x: x.premium or 0, reverse=True)
            
            self._set_cache(cache_key, [asdict(f) for f in flows])
            return flows
            
        except Exception as e:
            print(f"Error scanning {symbol}: {e}")
            return []
    
    def _analyze_option(
        self, 
        symbol: str, 
        expiration: str, 
        row: pd.Series, 
        opt_type: str,
        current_price: float,
        min_premium: int
    ) -> Optional[OptionsFlow]:
        """Analyze single option for unusual activity"""
        
        # Handle NaN values from Yahoo Finance
        volume = row.get('volume', 0)
        if pd.isna(volume) or volume is None:
            volume = 0
        volume = int(volume) if volume else 0
        
        oi = row.get('openInterest', 0)
        if pd.isna(oi) or oi is None:
            oi = 0
        oi = int(oi) if oi else 0
        
        strike = row.get('strike', 0)
        last_price = row.get('lastPrice', 0)
        if pd.isna(last_price) or last_price is None:
            last_price = 0
        
        iv = row.get('impliedVolatility', None)
        if pd.isna(iv):
            iv = None
        
        if volume < self.MIN_VOLUME:
            return None
        
        # Calculate metrics
        volume_oi_ratio = volume / oi if oi > 0 else float('inf')
        premium = volume * last_price * 100  # Options contracts are 100 shares
        
        if premium < min_premium:
            return None
        
        # Detect trade type
        trade_type = self._classify_trade(volume, oi, volume_oi_ratio, premium)
        
        if trade_type == 'normal':
            return None  # Not unusual
        
        # Determine sentiment
        sentiment = self._determine_sentiment(opt_type, strike, current_price, iv)
        
        return OptionsFlow(
            symbol=symbol,
            timestamp=datetime.now().isoformat(),
            expiration=expiration,
            strike=strike,
            call_or_put=opt_type,
            volume=int(volume),
            open_interest=int(oi),
            volume_oi_ratio=round(volume_oi_ratio, 2),
            iv=round(iv, 4) if iv else None,
            premium=round(premium, 2),
            trade_type=trade_type,
            sentiment=sentiment
        )
    
    def _classify_trade(
        self, 
        volume: int, 
        oi: int, 
        vol_oi_ratio: float, 
        premium: float
    ) -> str:
        """Classify trade as sweep, block, unusual, or normal"""
        
        # Sweep: High volume, very high V/OI ratio (aggressive buying)
        if vol_oi_ratio > 5.0 and volume > 1000:
            return 'sweep'
        
        # Block: Large premium, moderate V/OI (institutional)
        if premium > 500000 and vol_oi_ratio > 1.5:
            return 'block'
        
        # Unusual: Above threshold but not sweep/block
        if vol_oi_ratio > self.VOLUME_OI_THRESHOLD:
            return 'unusual'
        
        return 'normal'
    
    def _determine_sentiment(
        self, 
        opt_type: str, 
        strike: float, 
        current_price: float,
        iv: Optional[float]
    ) -> str:
        """Determine bullish/bearish sentiment from option characteristics"""
        
        moneyness = (strike - current_price) / current_price
        
        if opt_type == 'call':
            # ATM or OTM calls = bullish
            if abs(moneyness) < 0.02:  # ATM
                return 'bullish'
            elif moneyness > 0:  # OTM
                return 'bullish'
            else:  # ITM calls
                return 'neutral'  # Could be hedging
        else:  # put
            # ATM or OTM puts = bearish
            if abs(moneyness) < 0.02:  # ATM
                return 'bearish'
            elif moneyness < 0:  # OTM puts
                return 'bearish'
            else:  # ITM puts
                return 'neutral'  # Could be hedging
    
    def scan_market(self, symbols: List[str], min_premium: int = 100000) -> List[OptionsFlow]:
        """
        Scan multiple tickers for unusual activity
        
        Args:
            symbols: List of tickers
            min_premium: Minimum premium filter
            
        Returns:
            Aggregated flows across all symbols
        """
        all_flows = []
        for symbol in symbols:
            flows = self.scan_ticker(symbol, min_premium)
            all_flows.extend(flows)
        
        # Sort by premium
        all_flows.sort(key=lambda x: x.premium or 0, reverse=True)
        return all_flows
    
    def get_dark_pool_proxy(self, symbol: str) -> Dict:
        """
        Approximate dark pool activity using volume discrepancies
        Note: True dark pool data requires paid services, this is a proxy
        
        Returns:
            Dict with estimated dark pool metrics
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='5d', interval='1d')
            
            if hist.empty:
                return {'error': 'No data'}
            
            # Dark pool proxy: Compare reported volume to price action
            avg_volume = hist['Volume'].mean()
            latest_volume = hist['Volume'].iloc[-1]
            price_change = (hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100
            
            # High volume + low price movement = potential dark pool activity
            volume_ratio = latest_volume / avg_volume
            dark_pool_score = 0
            
            if volume_ratio > 1.5 and abs(price_change) < 1.0:
                dark_pool_score = min(10, volume_ratio * 2)
            
            return {
                'symbol': symbol,
                'latest_volume': int(latest_volume),
                'avg_volume_5d': int(avg_volume),
                'volume_ratio': round(volume_ratio, 2),
                'price_change_pct': round(price_change, 2),
                'dark_pool_score': round(dark_pool_score, 1),
                'signal': 'High dark pool activity' if dark_pool_score > 5 else 'Normal'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_current_price(self, ticker: yf.Ticker) -> float:
        """Get current stock price"""
        try:
            info = ticker.info
            return info.get('currentPrice') or info.get('regularMarketPrice', 0)
        except:
            hist = ticker.history(period='1d')
            if not hist.empty:
                return hist['Close'].iloc[-1]
            return 0
    
    def _get_cache(self, key: str):
        """Get cached data if fresh"""
        cache_file = os.path.join(self.CACHE_DIR, f"{key}.json")
        if os.path.exists(cache_file):
            mtime = os.path.getmtime(cache_file)
            if datetime.now().timestamp() - mtime < self.CACHE_TTL:
                with open(cache_file, 'r') as f:
                    return json.load(f)
        return None
    
    def _set_cache(self, key: str, data):
        """Cache data"""
        cache_file = os.path.join(self.CACHE_DIR, f"{key}.json")
        with open(cache_file, 'w') as f:
            json.dump(data, f)


def main():
    """CLI interface"""
    import sys
    
    scanner = OptionsFlowScanner()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  options_flow_scanner.py scan SYMBOL [--min-premium 50000]")
        print("  options_flow_scanner.py market SYMBOL1,SYMBOL2,...")
        print("  options_flow_scanner.py darkpool SYMBOL")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'scan':
        symbol = sys.argv[2].upper()
        min_premium = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[3] == '--min-premium' else 50000
        
        flows = scanner.scan_ticker(symbol, min_premium)
        
        if not flows:
            print(f"No unusual options activity detected for {symbol}")
            return
        
        print(f"\n🔍 Unusual Options Activity: {symbol}")
        print(f"Found {len(flows)} signals\n")
        
        for flow in flows[:10]:  # Show top 10
            print(f"{'🟢' if flow.sentiment == 'bullish' else '🔴' if flow.sentiment == 'bearish' else '⚪'} "
                  f"{flow.call_or_put.upper()} ${flow.strike} exp {flow.expiration}")
            print(f"   Type: {flow.trade_type.upper()} | Vol: {flow.volume:,} | OI: {flow.open_interest:,} | "
                  f"V/OI: {flow.volume_oi_ratio}x")
            print(f"   Premium: ${flow.premium:,.0f} | IV: {flow.iv or 'N/A'}")
            print(f"   Sentiment: {flow.sentiment.upper()}\n")
    
    elif command == 'market':
        symbols = [s.strip().upper() for s in sys.argv[2].split(',')]
        flows = scanner.scan_market(symbols)
        
        print(f"\n🔍 Market-Wide Options Flow")
        print(f"Scanned {len(symbols)} tickers, found {len(flows)} signals\n")
        
        for flow in flows[:15]:  # Top 15
            print(f"{flow.symbol} {flow.call_or_put.upper()} ${flow.strike} | "
                  f"{flow.trade_type.upper()} | ${flow.premium:,.0f} | {flow.sentiment}")
    
    elif command == 'darkpool':
        symbol = sys.argv[2].upper()
        result = scanner.get_dark_pool_proxy(symbol)
        
        print(f"\n🏴 Dark Pool Activity Proxy: {symbol}")
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
