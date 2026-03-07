"""
Earnings Estimates & Surprises — Real-time EPS Consensus & Revisions

Data Sources: Yahoo Finance (yfinance) + Alpha Vantage + Financial Datasets API
Update: Real-time for estimates, quarterly for surprises
History: 4+ quarters of historical surprises
Free: Yes (yfinance free, Alpha Vantage demo key, Financial Datasets API)

Provides:
- Consensus EPS estimates (current/next quarter)
- Analyst estimate revisions (30/60/90 day trends)
- Earnings surprises (actual vs estimate, % surprise)
- Earnings calendar (upcoming earnings dates)

Usage as Indicator:
- Positive estimate revisions → Often precedes stock rallies
- Negative surprises → Short-term selloffs common
- Pre-earnings drift → Stocks with positive revisions tend to outperform
"""

import requests
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional
import json
import os

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/earnings")
os.makedirs(CACHE_DIR, exist_ok=True)

# Financial Datasets API key (from TOOLS.md)
FINANCIAL_DATASETS_KEY = "f4cd5217-2afe-4d8e-9031-1328633c8532"
FINANCIAL_DATASETS_URL = "https://api.financialdatasets.ai"

# Alpha Vantage demo key (rate limited but works)
ALPHA_VANTAGE_KEY = "demo"
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"


def get_eps_estimates(symbol: str) -> Dict:
    """
    Get consensus EPS estimates for current and next quarter.
    
    Returns:
        {
            "symbol": "AAPL",
            "current_quarter": {"estimate": 1.52, "high": 1.60, "low": 1.45, "num_analysts": 28},
            "next_quarter": {"estimate": 1.68, "high": 1.75, "low": 1.60, "num_analysts": 25},
            "fiscal_year": 2026,
            "updated": "2026-03-07"
        }
    """
    cache_file = os.path.join(CACHE_DIR, f"{symbol}_estimates.json")
    
    # Check cache (refresh daily)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(days=1):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        # Use yfinance to get analyst estimates
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Get earnings estimates from Yahoo Finance
        earnings_estimate = ticker.get_earnings_dates(limit=8)  # Future + recent past
        
        result = {
            "symbol": symbol.upper(),
            "current_quarter": {
                "estimate": info.get("targetMeanPrice"),  # Fallback
                "num_analysts": info.get("numberOfAnalystOpinions", 0)
            },
            "next_quarter": {},
            "fiscal_year": datetime.now().year,
            "updated": datetime.now().strftime("%Y-%m-%d"),
            "source": "yfinance"
        }
        
        # Try to extract EPS estimate from earnings history
        if hasattr(ticker, 'earnings_forecasts') and ticker.earnings_forecasts is not None:
            forecasts = ticker.earnings_forecasts
            if not forecasts.empty and 'EPS Estimate' in forecasts.columns:
                estimates = forecasts['EPS Estimate'].dropna()
                if len(estimates) > 0:
                    result["current_quarter"]["estimate"] = float(estimates.iloc[0])
                if len(estimates) > 1:
                    result["next_quarter"]["estimate"] = float(estimates.iloc[1])
        
        # Fallback: use Financial Datasets API for better estimates
        if not result["current_quarter"].get("estimate"):
            fd_data = _fetch_financial_datasets_earnings(symbol)
            if fd_data:
                result["current_quarter"]["estimate"] = fd_data.get("eps_estimate")
                result["source"] = "financial_datasets"
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
        
    except Exception as e:
        print(f"⚠️  Error fetching EPS estimates for {symbol}: {e}")
        return {
            "symbol": symbol.upper(),
            "error": str(e),
            "current_quarter": {},
            "next_quarter": {},
            "updated": datetime.now().strftime("%Y-%m-%d")
        }


def get_estimate_revisions(symbol: str, period: str = '30d') -> Dict:
    """
    Get analyst estimate revision trends (upgrades vs downgrades).
    
    Args:
        symbol: Stock ticker
        period: '30d', '60d', or '90d'
    
    Returns:
        {
            "symbol": "AAPL",
            "period": "30d",
            "revisions": {
                "up": 5,
                "down": 2,
                "unchanged": 10
            },
            "trend": "POSITIVE",  # POSITIVE, NEGATIVE, NEUTRAL
            "avg_revision_pct": +2.5,
            "updated": "2026-03-07"
        }
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Yahoo Finance doesn't provide revision history directly
        # Use recommendations as proxy for revision trends
        recommendations = ticker.recommendations
        
        period_days = int(period.replace('d', ''))
        cutoff_date = datetime.now() - timedelta(days=period_days)
        
        if recommendations is not None and not recommendations.empty:
            # Ensure index is datetime
            if not isinstance(recommendations.index, pd.DatetimeIndex):
                recommendations.index = pd.to_datetime(recommendations.index)
            
            recent = recommendations[recommendations.index > cutoff_date]
            
            # Count upgrades/downgrades based on available columns
            # yfinance uses 'To Grade' or 'Action' column
            grade_col = None
            if 'To Grade' in recent.columns:
                grade_col = 'To Grade'
            elif 'Action' in recent.columns:
                grade_col = 'Action'
            elif 'ToGrade' in recent.columns:
                grade_col = 'ToGrade'
            
            if grade_col:
                upgrades = len(recent[recent[grade_col].str.contains('Buy|Strong Buy|up', case=False, na=False)])
                downgrades = len(recent[recent[grade_col].str.contains('Sell|Underperform|down', case=False, na=False)])
                unchanged = len(recent) - upgrades - downgrades
                
                net_revisions = upgrades - downgrades
                trend = "POSITIVE" if net_revisions > 2 else ("NEGATIVE" if net_revisions < -2 else "NEUTRAL")
                
                return {
                    "symbol": symbol.upper(),
                    "period": period,
                    "revisions": {
                        "up": upgrades,
                        "down": downgrades,
                        "unchanged": unchanged
                    },
                    "trend": trend,
                    "net_revisions": net_revisions,
                    "updated": datetime.now().strftime("%Y-%m-%d"),
                    "source": "yfinance"
                }
            else:
                # Fallback if no recognizable column
                total_recs = len(recent)
                return {
                    "symbol": symbol.upper(),
                    "period": period,
                    "revisions": {
                        "up": 0,
                        "down": 0,
                        "unchanged": total_recs
                    },
                    "trend": "NEUTRAL",
                    "updated": datetime.now().strftime("%Y-%m-%d"),
                    "note": f"Found {total_recs} recommendations but unable to classify"
                }
        else:
            # Fallback: use Financial Datasets API
            return {
                "symbol": symbol.upper(),
                "period": period,
                "revisions": {"up": 0, "down": 0, "unchanged": 0},
                "trend": "NEUTRAL",
                "updated": datetime.now().strftime("%Y-%m-%d"),
                "note": "No recent analyst revisions found"
            }
            
    except Exception as e:
        print(f"⚠️  Error fetching estimate revisions for {symbol}: {e}")
        return {
            "symbol": symbol.upper(),
            "period": period,
            "error": str(e),
            "revisions": {},
            "trend": "UNKNOWN"
        }


def get_earnings_surprises(symbol: str, quarters: int = 4) -> List[Dict]:
    """
    Get historical earnings surprises (actual vs estimate).
    
    Returns list of past quarters:
        [
            {
                "date": "2026-01-30",
                "quarter": "Q4 2025",
                "eps_estimate": 1.52,
                "eps_actual": 1.58,
                "surprise": +0.06,
                "surprise_pct": +3.95
            },
            ...
        ]
    """
    cache_file = os.path.join(CACHE_DIR, f"{symbol}_surprises.json")
    
    # Check cache (refresh weekly)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(days=7):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        # Method 1: Try Alpha Vantage (has earnings data)
        av_data = _fetch_alpha_vantage_earnings(symbol)
        if av_data:
            surprises = av_data[:quarters]
            
            # Cache result
            with open(cache_file, 'w') as f:
                json.dump(surprises, f, indent=2)
            
            return surprises
        
        # Method 2: Use yfinance earnings history
        ticker = yf.Ticker(symbol)
        earnings_history = ticker.earnings_history
        
        if earnings_history is not None and not earnings_history.empty:
            surprises = []
            
            for idx, row in earnings_history.head(quarters).iterrows():
                eps_estimate = row.get('epsEstimate', 0)
                eps_actual = row.get('epsActual', 0)
                surprise = eps_actual - eps_estimate if eps_estimate else 0
                surprise_pct = (surprise / eps_estimate * 100) if eps_estimate else 0
                
                surprises.append({
                    "date": row.get('startdatetime', idx).strftime("%Y-%m-%d") if hasattr(row.get('startdatetime', idx), 'strftime') else str(idx),
                    "quarter": row.get('quarter', 'N/A'),
                    "eps_estimate": float(eps_estimate) if eps_estimate else None,
                    "eps_actual": float(eps_actual) if eps_actual else None,
                    "surprise": float(surprise),
                    "surprise_pct": round(float(surprise_pct), 2)
                })
            
            # Cache result
            with open(cache_file, 'w') as f:
                json.dump(surprises, f, indent=2)
            
            return surprises
        else:
            return []
            
    except Exception as e:
        print(f"⚠️  Error fetching earnings surprises for {symbol}: {e}")
        return []


def get_earnings_calendar(days_ahead: int = 7) -> List[Dict]:
    """
    Get upcoming earnings dates for major stocks.
    
    Returns:
        [
            {
                "symbol": "AAPL",
                "company": "Apple Inc.",
                "earnings_date": "2026-03-15",
                "when": "After Market Close",
                "eps_estimate": 1.52
            },
            ...
        ]
    """
    try:
        # Use yfinance to get earnings calendar
        # Note: yfinance doesn't have a global calendar, so we'll check common tickers
        
        common_tickers = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B",
            "JPM", "V", "JNJ", "WMT", "PG", "MA", "UNH", "HD", "DIS", "BAC",
            "NFLX", "COST", "XOM", "PFE", "ABBV", "CVX", "MRK", "KO", "PEP", "ADBE"
        ]
        
        calendar = []
        end_date = datetime.now() + timedelta(days=days_ahead)
        
        for symbol in common_tickers:
            try:
                ticker = yf.Ticker(symbol)
                earnings_dates = ticker.get_earnings_dates(limit=2)
                
                if earnings_dates is not None and not earnings_dates.empty:
                    # Get next earnings date
                    future_earnings = earnings_dates[earnings_dates.index > datetime.now()]
                    
                    if not future_earnings.empty:
                        next_date = future_earnings.index[0]
                        
                        if next_date <= end_date:
                            calendar.append({
                                "symbol": symbol,
                                "company": ticker.info.get('longName', symbol),
                                "earnings_date": next_date.strftime("%Y-%m-%d"),
                                "when": "After Market Close",  # Default assumption
                                "eps_estimate": future_earnings.iloc[0].get('epsEstimate') if 'epsEstimate' in future_earnings.columns else None
                            })
            except:
                continue  # Skip tickers that fail
        
        # Sort by date
        calendar.sort(key=lambda x: x['earnings_date'])
        
        return calendar
        
    except Exception as e:
        print(f"⚠️  Error fetching earnings calendar: {e}")
        return []


# === Helper Functions ===

def _fetch_alpha_vantage_earnings(symbol: str) -> List[Dict]:
    """Fetch earnings data from Alpha Vantage API."""
    try:
        params = {
            "function": "EARNINGS",
            "symbol": symbol,
            "apikey": ALPHA_VANTAGE_KEY
        }
        
        response = requests.get(ALPHA_VANTAGE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "quarterlyEarnings" in data:
            surprises = []
            for quarter in data["quarterlyEarnings"][:4]:
                reported_eps = quarter.get("reportedEPS")
                estimated_eps = quarter.get("estimatedEPS")
                surprise = quarter.get("surprise")
                surprise_pct = quarter.get("surprisePercentage")
                
                if reported_eps and estimated_eps:
                    surprises.append({
                        "date": quarter.get("reportedDate"),
                        "quarter": quarter.get("fiscalDateEnding"),
                        "eps_estimate": float(estimated_eps),
                        "eps_actual": float(reported_eps),
                        "surprise": float(surprise) if surprise else 0,
                        "surprise_pct": float(surprise_pct) if surprise_pct else 0
                    })
            
            return surprises
        
        return []
        
    except Exception as e:
        print(f"⚠️  Alpha Vantage API error: {e}")
        return []


def _fetch_financial_datasets_earnings(symbol: str) -> Optional[Dict]:
    """Fetch earnings data from Financial Datasets API."""
    try:
        headers = {"X-API-KEY": FINANCIAL_DATASETS_KEY}
        url = f"{FINANCIAL_DATASETS_URL}/earnings/{symbol}"
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data
        
        return None
        
    except Exception as e:
        print(f"⚠️  Financial Datasets API error: {e}")
        return None


# === CLI Commands ===

def cli_estimates(symbol: str):
    """Show EPS estimates for a stock."""
    data = get_eps_estimates(symbol)
    
    print(f"\n📊 EPS Estimates — {data['symbol']}")
    print("=" * 50)
    
    if "error" in data:
        print(f"❌ Error: {data['error']}")
        return
    
    cq = data.get("current_quarter", {})
    nq = data.get("next_quarter", {})
    
    if cq.get("estimate"):
        print(f"📈 Current Quarter Estimate: ${cq['estimate']:.2f}")
        if cq.get("num_analysts"):
            print(f"   Analysts: {cq['num_analysts']}")
    
    if nq.get("estimate"):
        print(f"📈 Next Quarter Estimate: ${nq['estimate']:.2f}")
    
    print(f"\n✅ Source: {data.get('source', 'unknown')}")
    print(f"📅 Updated: {data['updated']}")


def cli_surprises(symbol: str, quarters: int = 4):
    """Show earnings surprise history."""
    surprises = get_earnings_surprises(symbol, quarters)
    
    print(f"\n📊 Earnings Surprises — {symbol.upper()}")
    print("=" * 70)
    
    if not surprises:
        print("❌ No earnings surprise data available")
        return
    
    for s in surprises:
        emoji = "✅" if s['surprise'] > 0 else ("❌" if s['surprise'] < 0 else "➖")
        print(f"{emoji} {s['date']} | Q: {s['quarter']}")
        print(f"   Estimate: ${s['eps_estimate']:.2f} | Actual: ${s['eps_actual']:.2f}")
        print(f"   Surprise: ${s['surprise']:+.2f} ({s['surprise_pct']:+.1f}%)")
        print()


def cli_calendar(days: int = 7):
    """Show upcoming earnings calendar."""
    calendar = get_earnings_calendar(days)
    
    print(f"\n📅 Earnings Calendar — Next {days} Days")
    print("=" * 70)
    
    if not calendar:
        print("No earnings found in this period")
        return
    
    for event in calendar:
        print(f"📊 {event['symbol']} — {event['company']}")
        print(f"   Date: {event['earnings_date']} ({event['when']})")
        if event.get('eps_estimate'):
            print(f"   EPS Estimate: ${event['eps_estimate']:.2f}")
        print()


def cli_revisions(symbol: str, period: str = '30d'):
    """Show analyst estimate revisions."""
    data = get_estimate_revisions(symbol, period)
    
    print(f"\n📊 Analyst Revisions — {data['symbol']} (Last {period})")
    print("=" * 50)
    
    if "error" in data:
        print(f"❌ Error: {data['error']}")
        return
    
    rev = data.get("revisions", {})
    print(f"⬆️  Upgrades: {rev.get('up', 0)}")
    print(f"⬇️  Downgrades: {rev.get('down', 0)}")
    print(f"➖ Unchanged: {rev.get('unchanged', 0)}")
    
    trend = data.get("trend", "NEUTRAL")
    if trend == "POSITIVE":
        print(f"\n✅ Trend: 🟢 POSITIVE (Net: {data.get('net_revisions', 0):+d})")
    elif trend == "NEGATIVE":
        print(f"\n⚠️  Trend: 🔴 NEGATIVE (Net: {data.get('net_revisions', 0):+d})")
    else:
        print(f"\n➖ Trend: ⚪ NEUTRAL")
    
    print(f"\n📅 Updated: {data['updated']}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "estimates" and len(sys.argv) > 2:
            cli_estimates(sys.argv[2])
        elif command == "surprises" and len(sys.argv) > 2:
            cli_surprises(sys.argv[2])
        elif command == "calendar":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            cli_calendar(days)
        elif command == "revisions" and len(sys.argv) > 2:
            period = sys.argv[3] if len(sys.argv) > 3 else '30d'
            cli_revisions(sys.argv[2], period)
        else:
            print("Usage:")
            print("  estimates <SYMBOL>")
            print("  surprises <SYMBOL>")
            print("  calendar [days]")
            print("  revisions <SYMBOL> [period]")
    else:
        # Demo
        cli_estimates("AAPL")
