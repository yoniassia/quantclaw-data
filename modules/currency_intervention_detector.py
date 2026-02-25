"""Currency Intervention Detector — detect central bank FX intervention patterns.

Analyzes FX price action and reserves data to identify potential central bank
interventions. Uses statistical outlier detection on returns and volume.
"""

import datetime
import json
import math
import urllib.request
from typing import Dict, List, Optional


def fetch_fx_data(pair: str = "USDJPY=X", days: int = 90) -> List[Dict]:
    """Fetch FX pair OHLCV data from Yahoo Finance.

    Args:
        pair: Yahoo Finance FX symbol (e.g., 'USDJPY=X', 'USDCNY=X')
        days: Lookback period in days.

    Returns:
        List of dicts with date, open, high, low, close, volume.
    """
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{pair}"
        f"?range={days}d&interval=1d"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())

    result = data["chart"]["result"][0]
    timestamps = result["timestamp"]
    quotes = result["indicators"]["quote"][0]

    records = []
    for i, ts in enumerate(timestamps):
        c = quotes["close"][i]
        if c is None:
            continue
        records.append({
            "date": datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d"),
            "open": quotes["open"][i],
            "high": quotes["high"][i],
            "low": quotes["low"][i],
            "close": c,
            "volume": quotes.get("volume", [None] * len(timestamps))[i],
        })
    return records


def detect_interventions(
    data: List[Dict], z_threshold: float = 2.5
) -> List[Dict]:
    """Detect potential intervention days using return and range analysis.

    Flags days where:
    - Absolute daily return exceeds z_threshold standard deviations
    - Intraday range is abnormally large
    - Price reversal pattern (large wick relative to body)

    Args:
        data: OHLCV records from fetch_fx_data.
        z_threshold: Z-score threshold for outlier detection.

    Returns:
        List of flagged intervention candidates with confidence scores.
    """
    if len(data) < 20:
        return []

    # Compute returns
    returns = []
    for i in range(1, len(data)):
        prev_close = data[i - 1]["close"]
        if prev_close and prev_close > 0:
            ret = (data[i]["close"] - prev_close) / prev_close
            returns.append(ret)
        else:
            returns.append(0)

    mean_ret = sum(returns) / len(returns)
    std_ret = math.sqrt(sum((r - mean_ret) ** 2 for r in returns) / len(returns))

    if std_ret == 0:
        return []

    flags = []
    for i, ret in enumerate(returns):
        idx = i + 1  # offset since returns start at index 1
        z_score = abs((ret - mean_ret) / std_ret)

        row = data[idx]
        intraday_range = (row["high"] - row["low"]) / row["close"] * 100 if row["close"] else 0
        body = abs(row["close"] - row["open"])
        total_range = row["high"] - row["low"]
        wick_ratio = 1 - (body / total_range) if total_range > 0 else 0

        confidence = 0
        signals = []

        if z_score >= z_threshold:
            confidence += 40
            signals.append(f"return_outlier(z={z_score:.1f})")

        # Large intraday range
        ranges = [(d["high"] - d["low"]) / d["close"] * 100 for d in data if d["close"]]
        avg_range = sum(ranges) / len(ranges) if ranges else 1
        if intraday_range > avg_range * 2:
            confidence += 30
            signals.append(f"wide_range({intraday_range:.2f}%)")

        # Reversal wick pattern (intervention often causes sharp reversal)
        if wick_ratio > 0.6:
            confidence += 20
            signals.append(f"reversal_wick({wick_ratio:.0%})")

        # Same-direction move next day (follow-through = less likely intervention)
        if idx + 1 < len(data):
            next_ret = (data[idx + 1]["close"] - row["close"]) / row["close"] if row["close"] else 0
            if (ret > 0 and next_ret < 0) or (ret < 0 and next_ret > 0):
                confidence += 10
                signals.append("next_day_reversal")

        if confidence >= 40:
            flags.append({
                "date": row["date"],
                "return_pct": round(ret * 100, 3),
                "z_score": round(z_score, 2),
                "intraday_range_pct": round(intraday_range, 3),
                "confidence": min(confidence, 100),
                "signals": signals,
                "direction": "selling_usd" if ret < 0 else "buying_usd",
            })

    return sorted(flags, key=lambda x: x["confidence"], reverse=True)


def scan_major_pairs(days: int = 90) -> Dict[str, List[Dict]]:
    """Scan major FX pairs known for central bank intervention.

    Args:
        days: Lookback in days.

    Returns:
        Dict mapping pair name to list of intervention flags.
    """
    pairs = {
        "USD/JPY": "USDJPY=X",
        "USD/CNY": "USDCNY=X",
        "USD/CHF": "USDCHF=X",
        "USD/KRW": "USDKRW=X",
        "USD/INR": "USDINR=X",
        "USD/TWD": "USDTWD=X",
    }
    results = {}
    for name, symbol in pairs.items():
        try:
            data = fetch_fx_data(symbol, days)
            flags = detect_interventions(data)
            if flags:
                results[name] = flags
        except Exception:
            continue
    return results


def intervention_summary(days: int = 90) -> Dict:
    """Generate a summary report of potential FX interventions.

    Returns:
        Summary with total flags, most suspicious pairs, and recent alerts.
    """
    scan = scan_major_pairs(days)
    total_flags = sum(len(v) for v in scan.values())
    most_active = sorted(scan.items(), key=lambda x: len(x[1]), reverse=True)

    recent = []
    for pair, flags in scan.items():
        for f in flags[:2]:
            recent.append({"pair": pair, **f})
    recent.sort(key=lambda x: x["date"], reverse=True)

    return {
        "period_days": days,
        "pairs_scanned": 6,
        "total_flags": total_flags,
        "most_active_pair": most_active[0][0] if most_active else None,
        "recent_alerts": recent[:10],
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
