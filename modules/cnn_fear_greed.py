"""
CNN Fear & Greed Index — Equity Market Sentiment Composite

7-component composite sentiment indicator for stock market:
1. Stock Price Momentum (S&P 500 vs 125-day MA)
2. Stock Price Strength (NYSE 52-week highs vs lows)
3. Stock Price Breadth (McClellan Volume Summation Index)
4. Put/Call Options Ratio
5. Junk Bond Demand (spread vs investment grade)
6. Market Volatility (VIX)
7. Safe Haven Demand (stocks vs bonds)

Data source: CNN Business Fear & Greed Index (no API key needed)
URL: https://production.dataviz.cnn.io/index/fearandgreed/graphdata
Update frequency: Real-time (updated throughout trading day)
Coverage: 1 year historical data

Classic contrarian indicator:
- Extreme Fear (0-25): Potential buying opportunity
- Fear (25-45): Below average sentiment
- Neutral (45-55): Balanced market
- Greed (55-75): Above average sentiment
- Extreme Greed (75-100): Potential selling opportunity

Free alternative to Bloomberg GTMI (Global Trading Market Intelligence)
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from pathlib import Path
import json


class CNNFearGreed:
    """CNN Fear & Greed Index data fetcher"""
    
    BASE_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    CACHE_DIR = Path.home() / ".quantclaw" / "cache" / "cnn_fear_greed"
    CACHE_HOURS = 1  # Refresh every hour during market hours
    
    # Sentiment thresholds
    THRESHOLDS = {
        "extreme_fear": (0, 25),
        "fear": (25, 45),
        "neutral": (45, 55),
        "greed": (55, 75),
        "extreme_greed": (75, 100)
    }
    
    def __init__(self):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_current(self) -> Dict:
        """Get current Fear & Greed Index value and components"""
        cache_file = self.CACHE_DIR / "current.json"
        
        # Check cache
        if cache_file.exists():
            age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if age < timedelta(hours=self.CACHE_HOURS):
                with open(cache_file) as f:
                    return json.load(f)
        
        # Fetch fresh data
        try:
            response = self.session.get(self.BASE_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract current value
            current = {
                "timestamp": datetime.now().isoformat(),
                "score": data["fear_and_greed"]["score"],
                "rating": data["fear_and_greed"]["rating"],
                "previous_close": data["fear_and_greed"]["previous_close"],
                "previous_1_week": data["fear_and_greed"].get("previous_1_week"),
                "previous_1_month": data["fear_and_greed"].get("previous_1_month"),
                "previous_1_year": data["fear_and_greed"].get("previous_1_year"),
            }
            
            # Add component breakdown if available
            if "fear_and_greed_historical" in data:
                hist = data["fear_and_greed_historical"]
                if "data" in hist and len(hist["data"]) > 0:
                    latest = hist["data"][-1]
                    current["components"] = {
                        "momentum": latest.get("x"),  # Stock Price Momentum
                        "strength": latest.get("y"),  # Stock Price Strength
                        # Other components may vary by CNN's API structure
                    }
            
            # Cache result
            with open(cache_file, 'w') as f:
                json.dump(current, f, indent=2)
            
            return current
            
        except Exception as e:
            print(f"Error fetching Fear & Greed: {e}")
            # Return cached data if available
            if cache_file.exists():
                with open(cache_file) as f:
                    return json.load(f)
            raise
    
    def get_historical(self, days: int = 365) -> pd.DataFrame:
        """Get historical Fear & Greed Index values"""
        cache_file = self.CACHE_DIR / f"history_{days}d.parquet"
        
        # Check cache (daily refresh for historical)
        if cache_file.exists():
            age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if age < timedelta(hours=24):
                return pd.read_parquet(cache_file)
        
        try:
            response = self.session.get(self.BASE_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract historical data
            hist = data.get("fear_and_greed_historical", {})
            if "data" not in hist:
                return pd.DataFrame()
            
            records = []
            for point in hist["data"]:
                records.append({
                    "timestamp": datetime.fromtimestamp(point["x"] / 1000),  # Convert ms to datetime
                    "score": point["y"],
                    "rating": point.get("rating", self._classify_score(point["y"]))
                })
            
            df = pd.DataFrame(records)
            df = df.set_index("timestamp").sort_index()
            
            # Trim to requested days
            if len(df) > 0:
                cutoff = datetime.now() - timedelta(days=days)
                df = df[df.index >= cutoff]
            
            # Cache result
            df.to_parquet(cache_file)
            return df
            
        except Exception as e:
            print(f"Error fetching historical Fear & Greed: {e}")
            if cache_file.exists():
                return pd.read_parquet(cache_file)
            return pd.DataFrame()
    
    def get_stats(self, days: int = 365) -> Dict:
        """Get statistical summary of Fear & Greed over period"""
        df = self.get_historical(days)
        if df.empty:
            return {}
        
        current = self.get_current()
        
        return {
            "current": current["score"],
            "rating": current["rating"],
            "mean": df["score"].mean(),
            "median": df["score"].median(),
            "std": df["score"].std(),
            "min": df["score"].min(),
            "max": df["score"].max(),
            "percentile": (df["score"] < current["score"]).mean() * 100,  # Current value percentile
            "days_analyzed": len(df),
            "sentiment_distribution": {
                "extreme_fear": (df["score"] < 25).sum(),
                "fear": ((df["score"] >= 25) & (df["score"] < 45)).sum(),
                "neutral": ((df["score"] >= 45) & (df["score"] < 55)).sum(),
                "greed": ((df["score"] >= 55) & (df["score"] < 75)).sum(),
                "extreme_greed": (df["score"] >= 75).sum()
            }
        }
    
    def get_signal(self) -> str:
        """Get trading signal based on current sentiment"""
        current = self.get_current()
        score = current["score"]
        
        if score < 25:
            return "STRONG_BUY"  # Extreme fear
        elif score < 35:
            return "BUY"  # Deep fear
        elif score < 45:
            return "WEAK_BUY"  # Mild fear
        elif score < 55:
            return "HOLD"  # Neutral
        elif score < 65:
            return "WEAK_SELL"  # Mild greed
        elif score < 75:
            return "SELL"  # Greed
        else:
            return "STRONG_SELL"  # Extreme greed
    
    def get_divergence(self, ticker: str = "SPY") -> Optional[Dict]:
        """
        Detect divergence between Fear & Greed and market price
        (Fear & Greed rising while market falling = bullish divergence)
        """
        try:
            import yfinance as yf
            
            # Get Fear & Greed history
            fg_df = self.get_historical(90)
            if fg_df.empty:
                return None
            
            # Get SPY price history
            spy = yf.Ticker(ticker)
            price_df = spy.history(period="3mo")["Close"]
            
            # Align timestamps
            fg_df = fg_df.reindex(price_df.index, method='ffill')
            
            # Calculate correlation
            corr = fg_df["score"].corr(price_df)
            
            # Recent trends (last 30 days)
            recent_fg = fg_df["score"].tail(30)
            recent_price = price_df.tail(30)
            
            fg_trend = (recent_fg.iloc[-1] - recent_fg.iloc[0]) / recent_fg.iloc[0]
            price_trend = (recent_price.iloc[-1] - recent_price.iloc[0]) / recent_price.iloc[0]
            
            # Divergence detection
            divergence_type = None
            if fg_trend > 0.05 and price_trend < -0.02:
                divergence_type = "bullish"  # Sentiment improving, price falling
            elif fg_trend < -0.05 and price_trend > 0.02:
                divergence_type = "bearish"  # Sentiment worsening, price rising
            
            return {
                "correlation": corr,
                "fg_30d_change": fg_trend,
                "price_30d_change": price_trend,
                "divergence": divergence_type,
                "signal_strength": abs(fg_trend - price_trend) if divergence_type else 0
            }
            
        except Exception as e:
            print(f"Error calculating divergence: {e}")
            return None
    
    @staticmethod
    def _classify_score(score: float) -> str:
        """Classify Fear & Greed score into rating"""
        if score < 25:
            return "Extreme Fear"
        elif score < 45:
            return "Fear"
        elif score < 55:
            return "Neutral"
        elif score < 75:
            return "Greed"
        else:
            return "Extreme Greed"


# CLI Interface
def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python cnn_fear_greed.py COMMAND [OPTIONS]")
        print("\nCommands:")
        print("  fear-greed                Current Fear & Greed Index score")
        print("  fear-greed-history [DAYS] Historical Fear & Greed values (default: 90)")
        print("  fear-greed-stats [DAYS]   Statistical summary (default: 365)")
        print("  fear-greed-signal         Trading signal based on sentiment")
        print("  fear-greed-divergence     Detect divergence vs SPY price")
        sys.exit(1)
    
    command = sys.argv[1]
    fg = CNNFearGreed()
    
    if command == 'fear-greed':
        data = fg.get_current()
        print(f"\n📊 CNN Fear & Greed Index")
        print(f"Score: {data['score']:.1f} ({data['rating']})")
        print(f"Previous Close: {data.get('previous_close', 'N/A')}")
        if 'previous_1_week' in data and data['previous_1_week']:
            print(f"1 Week Ago: {data['previous_1_week']}")
        if 'previous_1_month' in data and data['previous_1_month']:
            print(f"1 Month Ago: {data['previous_1_month']}")
        print()
    
    elif command == 'fear-greed-history':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
        df = fg.get_historical(days)
        if not df.empty:
            print(df.tail(20).to_string())
        else:
            print("No historical data available")
    
    elif command == 'fear-greed-stats':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 365
        stats = fg.get_stats(days)
        if stats:
            print(f"\n📈 Statistics (Last {days} days)")
            print(f"Current: {stats['current']:.1f} ({stats['rating']})")
            print(f"Mean: {stats['mean']:.1f}")
            print(f"Median: {stats['median']:.1f}")
            print(f"Range: {stats['min']:.1f} - {stats['max']:.1f}")
            print(f"Percentile: {stats['percentile']:.1f}%")
            print(f"\nSentiment Distribution:")
            for k, v in stats['sentiment_distribution'].items():
                pct = (v / stats['days_analyzed']) * 100
                print(f"  {k.replace('_', ' ').title()}: {v} days ({pct:.1f}%)")
            print()
        else:
            print("No data available")
    
    elif command == 'fear-greed-signal':
        signal = fg.get_signal()
        current = fg.get_current()
        print(f"\n🎯 Signal: {signal} (Score: {current['score']:.1f})")
    
    elif command == 'fear-greed-divergence':
        div = fg.get_divergence()
        if div:
            print(f"\n🔀 SPY Divergence Analysis")
            print(f"Correlation (90d): {div['correlation']:.3f}")
            print(f"Fear & Greed 30d Change: {div['fg_30d_change']*100:+.2f}%")
            print(f"SPY 30d Change: {div['price_30d_change']*100:+.2f}%")
            if div['divergence']:
                print(f"Divergence: {div['divergence'].upper()} (strength: {div['signal_strength']:.3f})")
            else:
                print("Divergence: None detected")
            print()
        else:
            print("Error calculating divergence")
    
    else:
        print(f"Error: Unknown command '{command}'")
        sys.exit(1)


if __name__ == "__main__":
    main()
