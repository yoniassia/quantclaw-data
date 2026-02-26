"""
Yield Curve Butterfly/Barbell Analyzer — analyzes yield curve shape trades.

Computes butterfly spreads, barbell vs bullet analysis, and curve curvature
metrics using free Treasury yield data from FRED.
"""

import json
import urllib.request
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# Standard Treasury tenors and their FRED series IDs
TREASURY_SERIES = {
    "1M": "DGS1MO", "3M": "DGS3MO", "6M": "DGS6MO",
    "1Y": "DGS1", "2Y": "DGS2", "3Y": "DGS3",
    "5Y": "DGS5", "7Y": "DGS7", "10Y": "DGS10",
    "20Y": "DGS20", "30Y": "DGS30"
}

TENOR_YEARS = {
    "1M": 1/12, "3M": 0.25, "6M": 0.5, "1Y": 1, "2Y": 2, "3Y": 3,
    "5Y": 5, "7Y": 7, "10Y": 10, "20Y": 20, "30Y": 30
}


@dataclass
class ButterflyTrade:
    """A butterfly spread trade on the yield curve."""
    short_tenor: str
    belly_tenor: str
    long_tenor: str
    short_yield: float
    belly_yield: float
    long_yield: float
    butterfly_spread: float  # belly - (short + long) / 2
    direction: str  # "buy butterfly" or "sell butterfly"
    curvature: float
    z_score: Optional[float] = None


@dataclass
class BarbellBullet:
    """Barbell vs Bullet analysis."""
    barbell_short: str
    barbell_long: str
    bullet_tenor: str
    barbell_yield: float  # weighted average
    bullet_yield: float
    pickup: float  # barbell - bullet
    duration_neutral: bool
    convexity_advantage: float


def fetch_treasury_yields(api_key: str = "DEMO_KEY",
                          limit: int = 1) -> Dict[str, float]:
    """Fetch latest Treasury yields from FRED.

    Args:
        api_key: FRED API key.
        limit: Number of recent observations.

    Returns:
        Dict of tenor -> yield (%).
    """
    yields = {}
    for tenor, series_id in TREASURY_SERIES.items():
        url = (f"{FRED_BASE}?series_id={series_id}&api_key={api_key}"
               f"&file_type=json&sort_order=desc&limit={limit}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read())
            for obs in data.get("observations", []):
                if obs["value"] != ".":
                    yields[tenor] = float(obs["value"])
                    break
        except Exception:
            continue
    return yields


def fetch_treasury_history(api_key: str = "DEMO_KEY",
                           series_id: str = "DGS10",
                           limit: int = 252) -> List[Tuple[str, float]]:
    """Fetch historical Treasury yield series.

    Args:
        api_key: FRED API key.
        series_id: FRED series ID.
        limit: Number of observations.

    Returns:
        List of (date_str, yield_value) tuples.
    """
    url = (f"{FRED_BASE}?series_id={series_id}&api_key={api_key}"
           f"&file_type=json&sort_order=desc&limit={limit}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        return [(obs["date"], float(obs["value"]))
                for obs in data.get("observations", [])
                if obs["value"] != "."]
    except Exception:
        return []


def calculate_butterfly(yields: Dict[str, float],
                        short: str = "2Y", belly: str = "5Y",
                        long: str = "10Y") -> Optional[ButterflyTrade]:
    """Calculate a butterfly spread.

    Butterfly = belly yield - (short yield + long yield) / 2
    Positive = curve is humped (belly cheap), negative = curve is cupped.

    Args:
        yields: Dict of tenor -> yield.
        short: Short wing tenor.
        belly: Belly tenor.
        long: Long wing tenor.

    Returns:
        ButterflyTrade or None if data missing.
    """
    if not all(t in yields for t in [short, belly, long]):
        return None

    s, b, l = yields[short], yields[belly], yields[long]
    spread = b - (s + l) / 2
    direction = "sell butterfly" if spread > 0 else "buy butterfly"

    # Curvature: second derivative approximation
    t_s, t_b, t_l = TENOR_YEARS[short], TENOR_YEARS[belly], TENOR_YEARS[long]
    h1, h2 = t_b - t_s, t_l - t_b
    curvature = 2 * ((l - b) / h2 - (b - s) / h1) / (h1 + h2)

    return ButterflyTrade(
        short_tenor=short, belly_tenor=belly, long_tenor=long,
        short_yield=s, belly_yield=b, long_yield=l,
        butterfly_spread=round(spread, 4),
        direction=direction,
        curvature=round(curvature, 4)
    )


def standard_butterflies(yields: Dict[str, float]) -> List[ButterflyTrade]:
    """Calculate all standard butterfly spreads.

    Args:
        yields: Dict of tenor -> yield.

    Returns:
        List of ButterflyTrade for common structures.
    """
    combos = [
        ("2Y", "3Y", "5Y"),
        ("2Y", "5Y", "10Y"),
        ("2Y", "5Y", "30Y"),
        ("5Y", "7Y", "10Y"),
        ("5Y", "10Y", "30Y"),
        ("2Y", "10Y", "30Y"),
        ("3M", "2Y", "10Y"),
    ]
    results = []
    for short, belly, long in combos:
        bf = calculate_butterfly(yields, short, belly, long)
        if bf:
            results.append(bf)
    return results


def barbell_vs_bullet(yields: Dict[str, float],
                      short: str = "2Y", long: str = "10Y",
                      bullet: str = "5Y",
                      short_weight: float = 0.5) -> Optional[BarbellBullet]:
    """Analyze barbell vs bullet trade.

    Args:
        yields: Dict of tenor -> yield.
        short: Short end of barbell.
        long: Long end of barbell.
        bullet: Bullet maturity.
        short_weight: Weight on short end (rest on long).

    Returns:
        BarbellBullet analysis or None.
    """
    if not all(t in yields for t in [short, long, bullet]):
        return None

    s, l, b = yields[short], yields[long], yields[bullet]
    barbell_yield = short_weight * s + (1 - short_weight) * l

    # Duration-neutral weighting
    d_s, d_l, d_b = TENOR_YEARS[short], TENOR_YEARS[long], TENOR_YEARS[bullet]
    dn_weight = (d_b - d_l) / (d_s - d_l) if (d_s - d_l) != 0 else 0.5
    dn_barbell_yield = dn_weight * s + (1 - dn_weight) * l

    # Convexity advantage approximation (barbell has more convexity)
    convexity_adv = (d_s**2 * dn_weight + d_l**2 * (1 - dn_weight)) - d_b**2

    return BarbellBullet(
        barbell_short=short, barbell_long=long, bullet_tenor=bullet,
        barbell_yield=round(dn_barbell_yield, 4),
        bullet_yield=round(b, 4),
        pickup=round(dn_barbell_yield - b, 4),
        duration_neutral=True,
        convexity_advantage=round(convexity_adv, 2)
    )


def curve_curvature_summary(yields: Dict[str, float]) -> Dict:
    """Generate full yield curve curvature analysis.

    Args:
        yields: Dict of tenor -> yield.

    Returns:
        Summary dict with curve metrics, butterflies, and barbell analysis.
    """
    butterflies = standard_butterflies(yields)
    bb = barbell_vs_bullet(yields)

    # Key spreads
    spread_2s10s = yields.get("10Y", 0) - yields.get("2Y", 0)
    spread_2s30s = yields.get("30Y", 0) - yields.get("2Y", 0)
    spread_5s30s = yields.get("30Y", 0) - yields.get("5Y", 0)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "yields": {k: round(v, 3) for k, v in sorted(yields.items(),
                   key=lambda x: TENOR_YEARS.get(x[0], 0))},
        "key_spreads": {
            "2s10s": round(spread_2s10s, 3),
            "2s30s": round(spread_2s30s, 3),
            "5s30s": round(spread_5s30s, 3),
        },
        "butterflies": [
            {"wings": f"{bf.short_tenor}/{bf.belly_tenor}/{bf.long_tenor}",
             "spread_bps": round(bf.butterfly_spread * 100, 1),
             "direction": bf.direction,
             "curvature": bf.curvature}
            for bf in butterflies
        ],
        "barbell_vs_bullet": {
            "structure": f"{bb.barbell_short}/{bb.bullet_tenor}/{bb.barbell_long}" if bb else None,
            "pickup_bps": round(bb.pickup * 100, 1) if bb else None,
            "convexity_advantage": bb.convexity_advantage if bb else None,
        } if bb else None,
        "curve_shape": "inverted" if spread_2s10s < 0 else "flat" if abs(spread_2s10s) < 0.25 else "steep"
    }
