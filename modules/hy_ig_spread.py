"""
High Yield vs Investment Grade Spread Decomposition — Analyze credit spread dynamics.

Decomposes the HY-IG spread into components: default risk premium, liquidity premium,
and risk appetite indicator. Uses FRED and Yahoo Finance free data.
"""

import json
import urllib.request
from datetime import datetime


FRED_SERIES = {
    "BAMLH0A0HYM2": "ICE BofA US High Yield OAS",
    "BAMLC0A0CM": "ICE BofA US Corporate OAS (IG)",
    "BAMLH0A0HYM2EY": "ICE BofA US HY Effective Yield",
    "DFF": "Federal Funds Rate",
}

FRED_API_KEY = "DEMO_KEY"  # Replace with real key for production


def get_credit_spreads(api_key: str = None) -> dict:
    """
    Fetch latest High Yield and Investment Grade OAS spreads from FRED.
    Returns spread levels and the HY-IG differential.
    """
    api_key = api_key or FRED_API_KEY
    results = {}
    for series_id, label in FRED_SERIES.items():
        try:
            url = (
                f"https://api.stlouisfed.org/fred/series/observations"
                f"?series_id={series_id}&api_key={api_key}&file_type=json"
                f"&sort_order=desc&limit=30"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            obs = data.get("observations", [])
            valid = [(o["date"], float(o["value"])) for o in obs if o.get("value") != "."]
            if valid:
                results[series_id] = {
                    "label": label,
                    "latest_value": valid[0][1],
                    "latest_date": valid[0][0],
                    "month_ago": valid[min(20, len(valid) - 1)][1] if len(valid) > 20 else None,
                }
        except Exception as e:
            results[series_id] = {"label": label, "error": str(e)}

    hy = results.get("BAMLH0A0HYM2", {}).get("latest_value")
    ig = results.get("BAMLC0A0CM", {}).get("latest_value")
    differential = round(hy - ig, 2) if hy is not None and ig is not None else None

    return {
        "spreads": results,
        "hy_ig_differential_bps": differential,
        "as_of": datetime.utcnow().isoformat(),
    }


def decompose_spread(api_key: str = None) -> dict:
    """
    Decompose the HY-IG spread into estimated components:
    - Default risk premium (historical default rate proxy)
    - Liquidity premium (residual)
    - Risk appetite signal
    """
    spreads = get_credit_spreads(api_key)
    diff = spreads.get("hy_ig_differential_bps")
    if diff is None:
        return {"decomposition": None, "error": "insufficient_data"}

    # Rough decomposition based on historical averages
    # Long-run HY default rate ~3.5%/yr, recovery ~40%, so expected loss ~210bp
    # IG default rate ~0.1%/yr, recovery ~50%, expected loss ~5bp
    default_premium_estimate = 205  # bp, long-run average
    liquidity_premium = max(0, diff - default_premium_estimate - 50)
    risk_appetite_residual = diff - default_premium_estimate - liquidity_premium

    if diff < 250:
        regime = "risk_on_tight"
    elif diff < 400:
        regime = "normal"
    elif diff < 600:
        regime = "stress"
    else:
        regime = "crisis"

    return {
        "decomposition": {
            "total_hy_ig_spread_bps": diff,
            "estimated_default_premium_bps": default_premium_estimate,
            "estimated_liquidity_premium_bps": round(liquidity_premium, 1),
            "risk_appetite_residual_bps": round(risk_appetite_residual, 1),
        },
        "regime": regime,
        "interpretation": f"HY-IG spread at {diff}bp indicates {regime.replace('_', ' ')} conditions",
        "as_of": datetime.utcnow().isoformat(),
    }


def get_spread_history(api_key: str = None, periods: int = 52) -> dict:
    """Fetch weekly HY OAS history for trend analysis."""
    api_key = api_key or FRED_API_KEY
    try:
        url = (
            f"https://api.stlouisfed.org/fred/series/observations"
            f"?series_id=BAMLH0A0HYM2&api_key={api_key}&file_type=json"
            f"&sort_order=desc&limit={periods}&frequency=w"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        obs = data.get("observations", [])
        history = [(o["date"], float(o["value"])) for o in obs if o.get("value") != "."]
        values = [v for _, v in history]
        return {
            "hy_oas_history": history[:10],  # last 10 for brevity
            "current": values[0] if values else None,
            "52w_high": max(values) if values else None,
            "52w_low": min(values) if values else None,
            "trend": "tightening" if len(values) >= 2 and values[0] < values[1] else "widening",
            "as_of": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}
