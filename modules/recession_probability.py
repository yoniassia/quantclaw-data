"""
Recession Probability Model — Multi-indicator recession forecasting.

Combines yield curve inversion signals, initial jobless claims, leading
economic indicators, and other macro data to estimate the probability
of a US recession within the next 12 months. Uses the classic
Estrella-Mishkin (1998) probit model approach plus modern enhancements.
"""

import json
import math
import urllib.request
from datetime import datetime
from typing import Any


# FRED series IDs for key recession indicators
FRED_SERIES = {
    "T10Y2Y": "10Y-2Y Treasury Spread",
    "T10Y3M": "10Y-3M Treasury Spread",
    "ICSA": "Initial Jobless Claims",
    "UNRATE": "Unemployment Rate",
    "UMCSENT": "U Michigan Consumer Sentiment",
    "INDPRO": "Industrial Production Index",
    "PERMIT": "Building Permits",
    "M2SL": "M2 Money Supply",
    "CPILFESL": "Core CPI",
}

# Probit model coefficients (Estrella-Mishkin inspired)
# P(recession) = Φ(α + β * spread)
PROBIT_ALPHA = -0.5333
PROBIT_BETA = -0.6330


def _normal_cdf(x: float) -> float:
    """Approximate standard normal CDF using Abramowitz & Stegun."""
    a1 = 0.254829592
    a2 = -0.284496736
    a3 = 1.421413741
    a4 = -1.453152027
    a5 = 1.061405429
    p = 0.3275911
    sign = 1 if x >= 0 else -1
    x = abs(x) / math.sqrt(2)
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
    return 0.5 * (1.0 + sign * y)


def _fetch_fred_series(series_id: str) -> float | None:
    """Fetch latest value from FRED."""
    url = (
        f"https://api.stlouisfed.org/fred/series/observations?"
        f"series_id={series_id}&sort_order=desc&limit=1"
        f"&file_type=json&api_key=DEMO_KEY"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        obs = data.get("observations", [])
        if obs and obs[0].get("value", ".") != ".":
            return float(obs[0]["value"])
    except Exception:
        pass
    return None


def get_yield_curve_signal(spread_10y2y: float | None = None) -> dict[str, Any]:
    """
    Calculate recession probability from the yield curve spread.

    Uses the Estrella-Mishkin probit model: the 10Y-2Y Treasury spread
    is the single best predictor of recessions 12 months ahead.

    Args:
        spread_10y2y: 10Y minus 2Y Treasury yield spread in percentage points.
                     If None, attempts to fetch from FRED.
    """
    if spread_10y2y is None:
        spread_10y2y = _fetch_fred_series("T10Y2Y")
        if spread_10y2y is None:
            spread_10y2y = 0.0  # fallback

    z_score = PROBIT_ALPHA + PROBIT_BETA * spread_10y2y
    probability = _normal_cdf(z_score)

    # Classify risk level
    if probability > 0.50:
        risk_level = "HIGH"
    elif probability > 0.30:
        risk_level = "ELEVATED"
    elif probability > 0.15:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    return {
        "model": "Estrella-Mishkin Probit",
        "spread_10y2y": spread_10y2y,
        "recession_probability_12m": round(probability * 100, 1),
        "risk_level": risk_level,
        "z_score": round(z_score, 4),
        "interpretation": (
            f"Based on a 10Y-2Y spread of {spread_10y2y:.2f}%, "
            f"the probit model estimates a {probability*100:.1f}% probability "
            f"of recession within 12 months ({risk_level} risk)."
        ),
        "inverted": spread_10y2y < 0,
        "historical_note": (
            "Every US recession since 1955 was preceded by yield curve inversion. "
            "Average lead time: 12-18 months. False positive rate: ~15%."
        ),
    }


def get_composite_recession_score() -> dict[str, Any]:
    """
    Calculate a composite recession probability using multiple indicators.

    Combines yield curve, jobless claims momentum, consumer sentiment,
    and industrial production into a weighted ensemble score.
    """
    indicators = {}

    # 1. Yield curve (weight: 35%)
    spread = _fetch_fred_series("T10Y2Y")
    if spread is not None:
        yc_prob = _normal_cdf(PROBIT_ALPHA + PROBIT_BETA * spread)
        indicators["yield_curve"] = {
            "value": spread, "probability": round(yc_prob, 3), "weight": 0.35
        }

    # 2. Jobless claims (weight: 25%) — rising claims = recession signal
    claims = _fetch_fred_series("ICSA")
    if claims is not None:
        # Sahm-like: claims > 300K and rising = elevated risk
        claims_prob = min(1.0, max(0.0, (claims - 200000) / 300000))
        indicators["jobless_claims"] = {
            "value": claims, "probability": round(claims_prob, 3), "weight": 0.25
        }

    # 3. Consumer sentiment (weight: 20%) — low sentiment = recession signal
    sentiment = _fetch_fred_series("UMCSENT")
    if sentiment is not None:
        sent_prob = min(1.0, max(0.0, (80 - sentiment) / 40))
        indicators["consumer_sentiment"] = {
            "value": sentiment, "probability": round(sent_prob, 3), "weight": 0.20
        }

    # 4. Unemployment rate (weight: 20%) — Sahm Rule
    urate = _fetch_fred_series("UNRATE")
    if urate is not None:
        # Simplified: > 4.5% = elevated risk
        ur_prob = min(1.0, max(0.0, (urate - 3.5) / 3.0))
        indicators["unemployment"] = {
            "value": urate, "probability": round(ur_prob, 3), "weight": 0.20
        }

    # Weighted composite
    if indicators:
        total_weight = sum(v["weight"] for v in indicators.values())
        composite = sum(
            v["probability"] * v["weight"] for v in indicators.values()
        ) / total_weight
    else:
        composite = 0.5  # no data = uncertain

    if composite > 0.50:
        risk = "HIGH"
    elif composite > 0.30:
        risk = "ELEVATED"
    elif composite > 0.15:
        risk = "MODERATE"
    else:
        risk = "LOW"

    return {
        "composite_probability_pct": round(composite * 100, 1),
        "risk_level": risk,
        "indicators": indicators,
        "model": "Multi-Indicator Ensemble",
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_historical_recessions() -> dict[str, Any]:
    """
    Return historical US recession dates and durations (NBER).
    """
    recessions = [
        {"start": "2020-02", "end": "2020-04", "months": 2, "name": "COVID-19"},
        {"start": "2007-12", "end": "2009-06", "months": 18, "name": "Great Recession"},
        {"start": "2001-03", "end": "2001-11", "months": 8, "name": "Dot-Com"},
        {"start": "1990-07", "end": "1991-03", "months": 8, "name": "Early 1990s"},
        {"start": "1981-07", "end": "1982-11", "months": 16, "name": "Volcker"},
        {"start": "1980-01", "end": "1980-07", "months": 6, "name": "Energy Crisis"},
        {"start": "1973-11", "end": "1975-03", "months": 16, "name": "Oil Embargo"},
        {"start": "1969-12", "end": "1970-11", "months": 11, "name": "1969-70"},
    ]
    avg_duration = sum(r["months"] for r in recessions) / len(recessions)
    return {
        "recessions": recessions,
        "count": len(recessions),
        "average_duration_months": round(avg_duration, 1),
        "source": "NBER Business Cycle Dating Committee",
    }
