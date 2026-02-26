"""
Dark Pool Print Monitor — Track off-exchange and ATS trading activity.

Monitors dark pool prints using FINRA ATS data and SEC market structure
reports to identify unusual off-exchange activity patterns.
"""

import csv
import io
import json
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional


FINRA_ATS_URL = "https://api.finra.org/data/group/otcMarket/name/weeklySummary"


def get_ats_volume(symbol: Optional[str] = None, weeks: int = 4) -> Dict:
    """
    Fetch FINRA ATS (dark pool) weekly volume data.

    Uses FINRA's public OTC transparency data to track dark pool activity.

    Args:
        symbol: Optional stock ticker to filter (None = market-wide)
        weeks: Number of weeks of history

    Returns:
        Dict with ATS volume data and dark pool activity metrics
    """
    try:
        # FINRA OTC transparency data
        url = "https://otctransparency.finra.org/otctransparency/api/AtsIssueData"
        headers = {
            "User-Agent": "QuantClaw/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Try to get recent data
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks)

        payload = json.dumps({
            "dateRangeFilters": [{
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
            }],
            "symbol": symbol.upper() if symbol else None,
            "limit": 100,
            "offset": 0,
        }).encode()

        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        records = data if isinstance(data, list) else data.get("records", [])

        if records:
            total_shares = sum(r.get("totalWeeklyShareQuantity", 0) for r in records)
            total_trades = sum(r.get("totalWeeklyTradeCount", 0) for r in records)
            ats_names = list(set(r.get("atsName", "Unknown") for r in records))

            return {
                "symbol": symbol or "MARKET-WIDE",
                "period_weeks": weeks,
                "total_dark_pool_shares": total_shares,
                "total_dark_pool_trades": total_trades,
                "avg_trade_size": round(total_shares / total_trades, 2) if total_trades else 0,
                "active_ats_count": len(ats_names),
                "ats_venues": ats_names[:20],
                "records_found": len(records),
                "source": "FINRA OTC Transparency",
            }

        return {
            "symbol": symbol or "MARKET-WIDE",
            "note": "No ATS data found for period",
            "source": "FINRA OTC Transparency",
        }

    except Exception as e:
        return _get_sec_market_structure_fallback(symbol, str(e))


def _get_sec_market_structure_fallback(symbol: Optional[str], error: str) -> Dict:
    """Fallback to SEC market structure data."""
    try:
        url = "https://www.sec.gov/api/marketstructure/metrics"
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        return {
            "symbol": symbol or "MARKET-WIDE",
            "source": "SEC Market Structure (fallback)",
            "primary_error": error,
            "data": data,
        }
    except Exception:
        return {
            "symbol": symbol or "MARKET-WIDE",
            "error": error,
            "fallback_error": "SEC endpoint also unavailable",
            "guidance": "Use FINRA OTC transparency portal for manual lookup",
        }


def analyze_dark_pool_prints(prints: List[Dict]) -> Dict:
    """
    Analyze a list of dark pool prints for unusual patterns.

    Detects block trades, sweep patterns, and volume anomalies.

    Args:
        prints: List of dicts with 'size', 'price', 'timestamp', 'venue'

    Returns:
        Dict with dark pool analysis including block detection and venue breakdown
    """
    if not prints:
        return {"error": "No prints provided"}

    total_volume = sum(p.get("size", 0) for p in prints)
    total_trades = len(prints)
    avg_size = total_volume / total_trades if total_trades else 0

    # Block trade detection (>= 10,000 shares)
    blocks = [p for p in prints if p.get("size", 0) >= 10000]
    block_volume = sum(p.get("size", 0) for p in blocks)

    # Large prints (>= 50,000 shares) - institutional
    large_prints = [p for p in prints if p.get("size", 0) >= 50000]

    # Venue breakdown
    venue_volumes: Dict[str, int] = {}
    for p in prints:
        venue = p.get("venue", "UNKNOWN")
        venue_volumes[venue] = venue_volumes.get(venue, 0) + p.get("size", 0)

    venue_breakdown = [
        {"venue": v, "volume": vol, "pct": round(vol / total_volume * 100, 2)}
        for v, vol in sorted(venue_volumes.items(), key=lambda x: -x[1])
    ]

    # Price clustering analysis
    prices = [p.get("price", 0) for p in prints if p.get("price")]
    price_at_round = sum(1 for pr in prices if pr == round(pr)) if prices else 0

    return {
        "total_trades": total_trades,
        "total_volume": total_volume,
        "avg_trade_size": round(avg_size, 2),
        "block_trades": {
            "count": len(blocks),
            "volume": block_volume,
            "pct_of_total": round(block_volume / total_volume * 100, 2) if total_volume else 0,
        },
        "large_institutional_prints": {
            "count": len(large_prints),
            "volume": sum(p.get("size", 0) for p in large_prints),
        },
        "venue_breakdown": venue_breakdown,
        "price_clustering": {
            "trades_at_round_prices": price_at_round,
            "pct_round": round(price_at_round / len(prices) * 100, 2) if prices else 0,
        },
        "activity_level": (
            "VERY HIGH" if avg_size > 5000 else
            "HIGH" if avg_size > 2000 else
            "MODERATE" if avg_size > 500 else "LOW"
        ),
    }


def estimate_dark_pool_ratio(
    dark_volume: int, total_volume: int, historical_avg_pct: float = 39.0
) -> Dict:
    """
    Calculate dark pool ratio and compare to historical norms.

    Args:
        dark_volume: Off-exchange volume
        total_volume: Total consolidated volume
        historical_avg_pct: Historical average dark pool % (default ~39%)

    Returns:
        Dict with dark pool ratio analysis
    """
    if total_volume <= 0:
        return {"error": "Total volume must be positive"}

    ratio = dark_volume / total_volume * 100
    deviation = ratio - historical_avg_pct

    return {
        "dark_pool_volume": dark_volume,
        "total_volume": total_volume,
        "lit_volume": total_volume - dark_volume,
        "dark_pool_pct": round(ratio, 2),
        "historical_avg_pct": historical_avg_pct,
        "deviation_pct": round(deviation, 2),
        "signal": (
            "UNUSUALLY HIGH" if deviation > 5 else
            "ABOVE AVERAGE" if deviation > 2 else
            "NORMAL" if abs(deviation) <= 2 else
            "BELOW AVERAGE" if deviation > -5 else "UNUSUALLY LOW"
        ),
        "interpretation": (
            "Elevated dark pool activity may indicate institutional accumulation"
            if deviation > 5 else
            "Dark pool activity within normal range"
            if abs(deviation) <= 2 else
            "Reduced dark pool activity — more price discovery on lit venues"
        ),
    }
