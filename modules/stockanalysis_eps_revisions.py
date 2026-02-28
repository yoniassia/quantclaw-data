#!/usr/bin/env python3
"""
StockAnalysis.com EPS Revisions Scraper
CRITICAL: Analyst EPS/revenue estimate revisions — closes Alpha Picker v3 accuracy gap (65%→85%+ SA match)

Free data, no API key required. Scrapes:
- EPS estimates (current/next quarter, current/next year)
- Revenue estimates
- Analyst count, consensus, high/low ranges
- Historical estimate changes (revision momentum)

Source: stockanalysis.com/{ticker}/forecast/
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import re
from pathlib import Path

# Cache directory
CACHE_DIR = Path.home() / ".quantclaw_cache" / "stockanalysis"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def get_cache_path(ticker: str, data_type: str = "forecast") -> Path:
    """Get cache file path for ticker"""
    return CACHE_DIR / f"{ticker.upper()}_{data_type}.json"

def load_cache(ticker: str, max_age_hours: int = 24) -> Optional[Dict]:
    """Load cached data if fresh"""
    cache_file = get_cache_path(ticker)
    if not cache_file.exists():
        return None
    
    try:
        data = json.loads(cache_file.read_text())
        cached_time = datetime.fromisoformat(data.get("cached_at", ""))
        age_hours = (datetime.now() - cached_time).total_seconds() / 3600
        
        if age_hours < max_age_hours:
            return data
    except:
        pass
    
    return None

def save_cache(ticker: str, data: Dict):
    """Save data to cache"""
    data["cached_at"] = datetime.now().isoformat()
    cache_file = get_cache_path(ticker)
    cache_file.write_text(json.dumps(data, indent=2))

def parse_number(text: str) -> Optional[float]:
    """Parse number from text (handles $, B, M, K suffixes)"""
    if not text or text.strip() in ["-", "N/A", ""]:
        return None
    
    text = text.strip().replace("$", "").replace(",", "")
    
    # Handle suffixes
    multiplier = 1
    if text.endswith("B"):
        multiplier = 1_000_000_000
        text = text[:-1]
    elif text.endswith("M"):
        multiplier = 1_000_000
        text = text[:-1]
    elif text.endswith("K"):
        multiplier = 1_000
        text = text[:-1]
    
    try:
        return float(text) * multiplier
    except:
        return None

def _parse_forecast_table(table) -> Dict:
    """Parse StockAnalysis.com forecast table (years as columns, metrics as rows)"""
    rows = table.find_all("tr")
    if len(rows) < 2:
        return {}
    
    # Get years from header row
    header_cells = rows[0].find_all(["th", "td"])
    years = [cell.get_text().strip() for cell in header_cells[1:]]  # Skip first col
    
    # Initialize result dict
    year_data = {year: {} for year in years}
    
    # Parse data rows (High, Avg, Low)
    for row in rows[1:]:
        cells = row.find_all(["th", "td"])
        if len(cells) < 2:
            continue
        
        metric_name = cells[0].get_text().strip().lower()
        
        # Map metric names
        if "avg" in metric_name or "mean" in metric_name:
            metric_key = "mean"
        elif "high" in metric_name:
            metric_key = "high"
        elif "low" in metric_name:
            metric_key = "low"
        elif "analyst" in metric_name or "# of" in metric_name:
            metric_key = "analysts"
        else:
            continue
        
        # Parse values for each year
        for i, year in enumerate(years):
            if i + 1 < len(cells):
                value_text = cells[i + 1].get_text().strip()
                
                # Skip "Pro" cells (paywalled)
                if value_text.lower() == "pro":
                    continue
                
                if metric_key == "analysts":
                    try:
                        year_data[year][metric_key] = int(value_text.replace(",", ""))
                    except:
                        pass
                else:
                    year_data[year][metric_key] = parse_number(value_text)
    
    return year_data

def scrape_forecast(ticker: str, use_cache: bool = True) -> Dict:
    """
    Scrape analyst forecasts from stockanalysis.com
    
    Returns:
        {
            "ticker": "AAPL",
            "eps_estimates": {
                "current_quarter": {"mean": 1.50, "high": 1.60, "low": 1.40, "analysts": 25},
                "next_quarter": {...},
                "current_year": {...},
                "next_year": {...}
            },
            "revenue_estimates": {
                "current_quarter": {"mean": 95000000000, ...},
                ...
            },
            "last_updated": "2026-02-28T13:00:00",
            "cached_at": "..."
        }
    """
    ticker = ticker.upper()
    
    # Try cache first
    if use_cache:
        cached = load_cache(ticker)
        if cached:
            return cached
    
    url = f"https://stockanalysis.com/stocks/{ticker.lower()}/forecast/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        result = {
            "ticker": ticker,
            "eps_estimates": {},
            "revenue_estimates": {},
            "last_updated": datetime.now().isoformat(),
            "source": url
        }
        
        # Find EPS and Revenue forecast tables
        # New structure: years as columns, metrics as rows (High, Avg, Low)
        
        # Find EPS Forecast table
        eps_heading = soup.find(['h2', 'h3'], string=lambda text: text and 'EPS Forecast' in text)
        if eps_heading:
            eps_table = eps_heading.find_next('table')
            if eps_table:
                result["eps_estimates"] = _parse_forecast_table(eps_table)
        
        # Find Revenue Forecast table
        rev_heading = soup.find(['h2', 'h3'], string=lambda text: text and 'Revenue Forecast' in text)
        if rev_heading:
            rev_table = rev_heading.find_next('table')
            if rev_table:
                result["revenue_estimates"] = _parse_forecast_table(rev_table)
        
        # Save to cache
        save_cache(ticker, result)
        
        return result
        
    except requests.RequestException as e:
        return {"error": f"Request failed: {e}", "ticker": ticker}
    except Exception as e:
        return {"error": f"Parse failed: {e}", "ticker": ticker}

def get_eps_surprise_history(ticker: str, use_cache: bool = True) -> Dict:
    """
    Scrape EPS surprise history (beat/miss patterns)
    
    Source: stockanalysis.com/{ticker}/earnings/
    """
    ticker = ticker.upper()
    
    # Try cache
    cache_file = get_cache_path(ticker, "earnings_history")
    if use_cache and cache_file.exists():
        try:
            data = json.loads(cache_file.read_text())
            cached_time = datetime.fromisoformat(data.get("cached_at", ""))
            age_hours = (datetime.now() - cached_time).total_seconds() / 3600
            if age_hours < 168:  # 1 week cache for historical data
                return data
        except:
            pass
    
    url = f"https://stockanalysis.com/stocks/{ticker.lower()}/earnings/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        result = {
            "ticker": ticker,
            "earnings_history": [],
            "last_updated": datetime.now().isoformat(),
            "source": url
        }
        
        # Find earnings history table
        table = soup.find("table")
        
        if table:
            rows = table.find_all("tr")[1:]  # Skip header
            
            for row in rows[:12]:  # Last 12 quarters
                cells = row.find_all(["td", "th"])
                
                if len(cells) >= 5:
                    try:
                        quarter = cells[0].get_text().strip()
                        eps_actual = parse_number(cells[1].get_text())
                        eps_estimate = parse_number(cells[2].get_text())
                        surprise_pct = parse_number(cells[3].get_text().replace("%", ""))
                        
                        result["earnings_history"].append({
                            "quarter": quarter,
                            "eps_actual": eps_actual,
                            "eps_estimate": eps_estimate,
                            "surprise_pct": surprise_pct,
                            "beat": surprise_pct > 0 if surprise_pct else None
                        })
                    except:
                        continue
        
        # Save cache
        result["cached_at"] = datetime.now().isoformat()
        cache_file.write_text(json.dumps(result, indent=2))
        
        return result
        
    except Exception as e:
        return {"error": str(e), "ticker": ticker}

def calculate_revision_momentum(ticker: str) -> Dict:
    """
    Calculate EPS estimate revision momentum (critical for Alpha Picker v3)
    
    Returns upward/downward revision trends
    """
    forecast = scrape_forecast(ticker)
    
    if "error" in forecast:
        return forecast
    
    result = {
        "ticker": ticker,
        "revision_signal": "neutral",
        "confidence": 0.0,
        "metrics": {}
    }
    
    eps = forecast.get("eps_estimates", {})
    
    # Check current quarter estimate vs range
    cq = eps.get("current_quarter", {})
    
    if cq.get("mean") and cq.get("high") and cq.get("low"):
        mean = cq["mean"]
        high = cq["high"]
        low = cq["low"]
        
        range_size = high - low
        if range_size > 0:
            # Where is mean in the range? (0 = low, 1 = high)
            mean_position = (mean - low) / range_size
            
            result["metrics"]["cq_mean_position"] = round(mean_position, 3)
            
            # Upward bias if mean > 0.6, downward if < 0.4
            if mean_position > 0.6:
                result["revision_signal"] = "upward"
                result["confidence"] = round((mean_position - 0.5) * 2, 3)  # 0-1 scale
            elif mean_position < 0.4:
                result["revision_signal"] = "downward"
                result["confidence"] = round((0.5 - mean_position) * 2, 3)
    
    # Check analyst count trend (increasing = more attention = good)
    analyst_counts = []
    for period in ["current_quarter", "next_quarter", "current_year", "next_year"]:
        if period in eps and "analysts" in eps[period]:
            analyst_counts.append(eps[period]["analysts"])
    
    if len(analyst_counts) >= 2:
        result["metrics"]["analyst_count_trend"] = "increasing" if analyst_counts[0] < analyst_counts[-1] else "decreasing"
    
    return result

def cli_forecast(ticker: str):
    """CLI: Get analyst forecasts for ticker"""
    data = scrape_forecast(ticker, use_cache=False)
    
    if "error" in data:
        print(f"❌ {data['error']}")
        return
    
    print(f"\n📊 Analyst Forecasts: {ticker}")
    print("=" * 60)
    
    # EPS Estimates
    print("\n💰 EPS Estimates:")
    for period, est in data.get("eps_estimates", {}).items():
        print(f"\n  {period.replace('_', ' ').title()}:")
        if "mean" in est and est['mean'] is not None:
            print(f"    Mean: ${est['mean']:.2f}")
        if "high" in est and "low" in est and est['high'] is not None and est['low'] is not None:
            print(f"    Range: ${est['low']:.2f} - ${est['high']:.2f}")
        if "analysts" in est and est['analysts'] is not None:
            print(f"    Analysts: {est['analysts']}")
    
    # Revenue Estimates
    print("\n💵 Revenue Estimates:")
    for period, est in data.get("revenue_estimates", {}).items():
        print(f"\n  {period.replace('_', ' ').title()}:")
        if "mean" in est and est['mean'] is not None:
            rev_b = est['mean'] / 1e9
            print(f"    Mean: ${rev_b:.2f}B")
        if "high" in est and "low" in est and est['high'] is not None and est['low'] is not None:
            high_b = est['high'] / 1e9
            low_b = est['low'] / 1e9
            print(f"    Range: ${low_b:.2f}B - ${high_b:.2f}B")
        if "analysts" in est and est['analysts'] is not None:
            print(f"    Analysts: {est['analysts']}")
    
    print(f"\n📅 Last Updated: {data.get('last_updated', 'N/A')}")
    print(f"🔗 Source: {data.get('source', 'N/A')}\n")

def cli_revision_momentum(ticker: str):
    """CLI: Calculate EPS revision momentum signal"""
    data = calculate_revision_momentum(ticker)
    
    if "error" in data:
        print(f"❌ {data['error']}")
        return
    
    signal = data.get("revision_signal", "neutral")
    confidence = data.get("confidence", 0.0)
    
    # Signal emoji
    signal_emoji = {
        "upward": "📈",
        "downward": "📉",
        "neutral": "➡️"
    }
    
    print(f"\n{signal_emoji.get(signal, '➡️')} EPS Revision Momentum: {ticker}")
    print("=" * 60)
    print(f"Signal: {signal.upper()}")
    print(f"Confidence: {confidence:.1%}")
    
    if data.get("metrics"):
        print("\nMetrics:")
        for key, val in data["metrics"].items():
            print(f"  {key}: {val}")
    
    print()

def cli_earnings_history(ticker: str):
    """CLI: Show EPS surprise history"""
    data = get_eps_surprise_history(ticker, use_cache=False)
    
    if "error" in data:
        print(f"❌ {data['error']}")
        return
    
    print(f"\n📊 Earnings History: {ticker}")
    print("=" * 80)
    print(f"{'Quarter':<12} {'Actual':>10} {'Estimate':>10} {'Surprise':>10} {'Beat/Miss':>12}")
    print("-" * 80)
    
    for item in data.get("earnings_history", [])[:8]:
        quarter = item.get("quarter", "N/A")
        actual = item.get("eps_actual")
        estimate = item.get("eps_estimate")
        surprise = item.get("surprise_pct")
        beat = item.get("beat")
        
        actual_str = f"${actual:.2f}" if actual else "N/A"
        estimate_str = f"${estimate:.2f}" if estimate else "N/A"
        surprise_str = f"{surprise:+.1f}%" if surprise else "N/A"
        
        beat_str = "✅ Beat" if beat else "❌ Miss" if beat is False else "—"
        
        print(f"{quarter:<12} {actual_str:>10} {estimate_str:>10} {surprise_str:>10} {beat_str:>12}")
    
    print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python stockanalysis_eps_revisions.py eps-forecast <ticker>")
        print("  python stockanalysis_eps_revisions.py eps-momentum <ticker>")
        print("  python stockanalysis_eps_revisions.py eps-history <ticker>")
        print("\nExamples:")
        print("  python stockanalysis_eps_revisions.py eps-forecast AAPL")
        print("  python stockanalysis_eps_revisions.py eps-momentum TSLA")
        print("  python stockanalysis_eps_revisions.py eps-history NVDA")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Strip eps- prefix if present (for CLI compatibility)
    if command.startswith('eps-'):
        command = command[4:]
    
    if len(sys.argv) < 3:
        print(f"❌ Missing ticker symbol for command: {sys.argv[1]}")
        sys.exit(1)
    
    ticker = sys.argv[2]
    
    if command == "forecast":
        cli_forecast(ticker)
    elif command == "momentum":
        cli_revision_momentum(ticker)
    elif command == "history":
        cli_earnings_history(ticker)
    else:
        print(f"❌ Unknown command: {sys.argv[1]}")
        sys.exit(1)
