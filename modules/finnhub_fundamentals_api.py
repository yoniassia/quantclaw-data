#!/usr/bin/env python3
"""
Finnhub Fundamentals API — Stock Fundamentals & Earnings Data

Comprehensive stock market fundamentals data from Finnhub.io including:
- Basic financials (P/E, P/B, ROE, margins, etc.)
- Earnings estimates and surprises
- Analyst recommendations and trends
- Company profiles and sector data

Source: https://finnhub.io/docs/api/company-basic-financials
Category: Earnings & Fundamentals
Free tier: 60 calls/min, 500 calls/day
API key: Required (FINNHUB_API_KEY env var or .env file)
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Finnhub API Configuration
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")


def _make_request(endpoint: str, params: Dict) -> Dict:
    """
    Helper function to make Finnhub API requests with error handling
    
    Args:
        endpoint: API endpoint path (e.g., '/stock/metric')
        params: Query parameters dict
    
    Returns:
        Dict with success flag and data or error message
    """
    try:
        if not FINNHUB_API_KEY:
            return {
                "success": False,
                "error": "FINNHUB_API_KEY not found in environment variables or .env file"
            }
        
        params["token"] = FINNHUB_API_KEY
        url = f"{FINNHUB_BASE_URL}{endpoint}"
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API error responses
        if isinstance(data, dict) and "error" in data:
            return {
                "success": False,
                "error": data["error"]
            }
        
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timeout - API took too long to respond"
        }
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 429:
            return {
                "success": False,
                "error": "Rate limit exceeded - Free tier: 60 calls/min, 500/day"
            }
        elif status_code == 401:
            return {
                "success": False,
                "error": "Invalid API key - Check FINNHUB_API_KEY"
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {status_code}: {str(e)}"
            }
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Network error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def get_basic_financials(symbol: str, metric: str = "all") -> Dict:
    """
    Get basic financial metrics for a stock symbol
    
    Includes:
    - Valuation ratios: P/E, P/B, P/S, EV/EBITDA
    - Profitability: ROE, ROA, profit margins
    - Growth rates: revenue growth, earnings growth
    - Liquidity: current ratio, quick ratio
    - Leverage: debt/equity, debt/assets
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        metric: Metric type - 'all' or specific metric category
    
    Returns:
        Dict with financial metrics, latest values, and metadata
    """
    result = _make_request("/stock/metric", {"symbol": symbol, "metric": metric})
    
    if not result["success"]:
        return result
    
    data = result["data"]
    
    # Structure the response for easier consumption
    if "metric" in data:
        metrics = data["metric"]
        
        # Organize by category
        organized = {
            "symbol": symbol,
            "valuation": {
                "pe_ratio": metrics.get("peBasicExclExtraTTM"),
                "pb_ratio": metrics.get("pbQuarterly"),
                "ps_ratio": metrics.get("psQuarterly"),
                "peg_ratio": metrics.get("pegBasicTTM"),
                "ev_to_ebitda": metrics.get("enterpriseValueToEBITDATTM"),
            },
            "profitability": {
                "roe": metrics.get("roeRfy"),
                "roa": metrics.get("roaRfy"),
                "gross_margin": metrics.get("grossMarginTTM"),
                "operating_margin": metrics.get("operatingMarginTTM"),
                "net_margin": metrics.get("netProfitMarginTTM"),
            },
            "growth": {
                "revenue_growth_annual": metrics.get("revenueGrowthTTMYoy"),
                "revenue_growth_3y": metrics.get("revenueGrowth3Y"),
                "revenue_growth_5y": metrics.get("revenueGrowth5Y"),
                "eps_growth_annual": metrics.get("epsGrowthTTMYoy"),
                "eps_growth_3y": metrics.get("epsGrowth3Y"),
            },
            "liquidity": {
                "current_ratio": metrics.get("currentRatioQuarterly"),
                "quick_ratio": metrics.get("quickRatioQuarterly"),
            },
            "leverage": {
                "debt_to_equity": metrics.get("totalDebt/totalEquityQuarterly"),
                "debt_to_assets": metrics.get("totalDebt/totalAssetQuarterly"),
                "long_term_debt_to_equity": metrics.get("longTermDebt/equityQuarterly"),
            },
            "raw_metrics": metrics  # Include all raw metrics for advanced users
        }
        
        return {
            "success": True,
            "financials": organized,
            "timestamp": result["timestamp"]
        }
    
    return {
        "success": True,
        "data": data,
        "timestamp": result["timestamp"]
    }


def get_earnings_estimates(symbol: str) -> Dict:
    """
    Get earnings estimates and EPS forecasts
    
    Returns analyst consensus estimates for upcoming quarters/years
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        Dict with EPS estimates by period
    """
    # Finnhub uses the earnings calendar endpoint for estimates
    result = _make_request("/calendar/earnings", {"symbol": symbol})
    
    if not result["success"]:
        return result
    
    data = result["data"]
    
    if "earningsCalendar" in data and data["earningsCalendar"]:
        estimates = []
        for item in data["earningsCalendar"]:
            estimates.append({
                "date": item.get("date"),
                "eps_estimate": item.get("epsEstimate"),
                "eps_actual": item.get("epsActual"),
                "revenue_estimate": item.get("revenueEstimate"),
                "revenue_actual": item.get("revenueActual"),
                "quarter": item.get("quarter"),
                "year": item.get("year"),
            })
        
        return {
            "success": True,
            "symbol": symbol,
            "earnings_estimates": estimates,
            "timestamp": result["timestamp"]
        }
    
    return {
        "success": True,
        "symbol": symbol,
        "earnings_estimates": [],
        "message": "No earnings estimates available",
        "timestamp": result["timestamp"]
    }


def get_recommendation_trends(symbol: str) -> Dict:
    """
    Get analyst recommendation trends (buy/hold/sell ratings)
    
    Shows distribution of analyst recommendations over time:
    - Strong Buy
    - Buy
    - Hold
    - Sell
    - Strong Sell
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        Dict with recommendation distribution and trend changes
    """
    result = _make_request("/stock/recommendation", {"symbol": symbol})
    
    if not result["success"]:
        return result
    
    data = result["data"]
    
    if isinstance(data, list) and len(data) > 0:
        # Most recent recommendations first
        latest = data[0]
        
        trends = []
        for item in data[:12]:  # Last 12 periods
            trends.append({
                "period": item.get("period"),
                "strong_buy": item.get("strongBuy", 0),
                "buy": item.get("buy", 0),
                "hold": item.get("hold", 0),
                "sell": item.get("sell", 0),
                "strong_sell": item.get("strongSell", 0),
            })
        
        # Calculate consensus
        total = (latest.get("strongBuy", 0) + latest.get("buy", 0) + 
                latest.get("hold", 0) + latest.get("sell", 0) + 
                latest.get("strongSell", 0))
        
        buy_total = latest.get("strongBuy", 0) + latest.get("buy", 0)
        
        consensus = "N/A"
        if total > 0:
            buy_pct = (buy_total / total) * 100
            if buy_pct >= 70:
                consensus = "Strong Buy"
            elif buy_pct >= 50:
                consensus = "Buy"
            elif buy_pct >= 30:
                consensus = "Hold"
            else:
                consensus = "Sell"
        
        return {
            "success": True,
            "symbol": symbol,
            "latest_period": latest.get("period"),
            "consensus": consensus,
            "latest_ratings": {
                "strong_buy": latest.get("strongBuy", 0),
                "buy": latest.get("buy", 0),
                "hold": latest.get("hold", 0),
                "sell": latest.get("sell", 0),
                "strong_sell": latest.get("strongSell", 0),
                "total_analysts": total
            },
            "historical_trends": trends,
            "timestamp": result["timestamp"]
        }
    
    return {
        "success": True,
        "symbol": symbol,
        "message": "No recommendation data available",
        "timestamp": result["timestamp"]
    }


def get_earnings_surprises(symbol: str, limit: int = 10) -> Dict:
    """
    Get historical earnings surprises (actual vs estimated EPS)
    
    Shows how actual earnings compared to analyst estimates
    Positive surprise = beat estimates
    Negative surprise = missed estimates
    
    Args:
        symbol: Stock ticker symbol
        limit: Number of historical quarters to return (default 10)
    
    Returns:
        Dict with earnings surprise history and beat rate
    """
    result = _make_request("/stock/earnings", {"symbol": symbol, "limit": limit})
    
    if not result["success"]:
        return result
    
    data = result["data"]
    
    if isinstance(data, list) and len(data) > 0:
        surprises = []
        beats = 0
        misses = 0
        
        for item in data:
            actual = item.get("actual")
            estimate = item.get("estimate")
            
            surprise = None
            surprise_pct = None
            beat = None
            
            if actual is not None and estimate is not None and estimate != 0:
                surprise = actual - estimate
                surprise_pct = (surprise / abs(estimate)) * 100
                beat = surprise > 0
                
                if beat:
                    beats += 1
                else:
                    misses += 1
            
            surprises.append({
                "period": item.get("period"),
                "quarter": item.get("quarter"),
                "year": item.get("year"),
                "actual_eps": actual,
                "estimated_eps": estimate,
                "surprise": surprise,
                "surprise_pct": surprise_pct,
                "beat_estimate": beat
            })
        
        total = beats + misses
        beat_rate = (beats / total * 100) if total > 0 else 0
        
        return {
            "success": True,
            "symbol": symbol,
            "earnings_surprises": surprises,
            "summary": {
                "periods_analyzed": len(surprises),
                "beats": beats,
                "misses": misses,
                "beat_rate_pct": round(beat_rate, 1)
            },
            "timestamp": result["timestamp"]
        }
    
    return {
        "success": True,
        "symbol": symbol,
        "message": "No earnings surprise data available",
        "timestamp": result["timestamp"]
    }


def get_company_profile(symbol: str) -> Dict:
    """
    Get company profile and basic information
    
    Includes:
    - Company name and description
    - Industry and sector
    - Market capitalization
    - Outstanding shares
    - IPO date
    - Country and exchange
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        Dict with company profile data
    """
    result = _make_request("/stock/profile2", {"symbol": symbol})
    
    if not result["success"]:
        return result
    
    data = result["data"]
    
    # Structure the profile data
    profile = {
        "symbol": symbol,
        "name": data.get("name"),
        "country": data.get("country"),
        "currency": data.get("currency"),
        "exchange": data.get("exchange"),
        "ipo_date": data.get("ipo"),
        "market_cap": data.get("marketCapitalization"),
        "shares_outstanding": data.get("shareOutstanding"),
        "industry": data.get("finnhubIndustry"),
        "sector": data.get("ggroup"),  # Global group
        "website": data.get("weburl"),
        "logo": data.get("logo"),
        "phone": data.get("phone"),
        "description": data.get("description"),
    }
    
    return {
        "success": True,
        "profile": profile,
        "timestamp": result["timestamp"]
    }


def get_company_snapshot(symbol: str) -> Dict:
    """
    Get comprehensive company snapshot combining all fundamental data
    
    One-stop function for complete company overview
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        Dict with profile, financials, earnings, and recommendations
    """
    snapshot = {
        "symbol": symbol,
        "timestamp": datetime.now().isoformat()
    }
    
    # Gather all data
    profile = get_company_profile(symbol)
    financials = get_basic_financials(symbol)
    recommendations = get_recommendation_trends(symbol)
    surprises = get_earnings_surprises(symbol, limit=4)
    
    if profile["success"]:
        snapshot["profile"] = profile.get("profile", {})
    
    if financials["success"]:
        snapshot["financials"] = financials.get("financials", {})
    
    if recommendations["success"]:
        snapshot["recommendations"] = {
            "consensus": recommendations.get("consensus"),
            "latest_ratings": recommendations.get("latest_ratings")
        }
    
    if surprises["success"]:
        snapshot["earnings_surprises"] = surprises.get("summary", {})
    
    return {
        "success": True,
        "snapshot": snapshot
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("Finnhub Fundamentals API - QuantClaw Data")
    print("=" * 60)
    
    test_symbol = "AAPL"
    
    if not FINNHUB_API_KEY:
        print("\n⚠️  FINNHUB_API_KEY not set!")
        print("Get free API key at: https://finnhub.io/register")
        print("\nSet in .env file:")
        print("FINNHUB_API_KEY=your_key_here")
    else:
        print(f"\n✓ API Key configured")
        print(f"\nTesting with symbol: {test_symbol}\n")
        
        # Test basic financials
        print("1. Basic Financials:")
        result = get_basic_financials(test_symbol)
        print(json.dumps(result, indent=2))
        
        print("\n" + "=" * 60)
        print("2. Company Profile:")
        result = get_company_profile(test_symbol)
        print(json.dumps(result, indent=2))
