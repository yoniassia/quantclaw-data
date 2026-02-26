"""
Corporate Bond Screener — Screen and filter corporate bonds by spread, rating,
duration, sector, and maturity. Uses FRED data for benchmark spreads and
simulated bond universe for screening demonstrations.

Roadmap item #341: Corporate Bond Screener (spread + rating + duration)
"""

import datetime
import math
import random
from typing import Any


# Simulated bond universe for screening
SECTORS = ["Technology", "Healthcare", "Energy", "Financials", "Industrials",
           "Consumer Discretionary", "Consumer Staples", "Utilities", "Materials", "Real Estate"]

RATINGS = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-",
           "BB+", "BB", "BB-", "B+", "B", "B-", "CCC+", "CCC", "CCC-"]

RATING_SPREAD_MAP = {
    "AAA": 30, "AA+": 40, "AA": 50, "AA-": 60, "A+": 75, "A": 90, "A-": 110,
    "BBB+": 135, "BBB": 160, "BBB-": 200, "BB+": 250, "BB": 310, "BB-": 380,
    "B+": 450, "B": 530, "B-": 620, "CCC+": 750, "CCC": 900, "CCC-": 1100,
}


def _rating_numeric(rating: str) -> int:
    """Convert letter rating to numeric score (1=AAA, higher=worse)."""
    try:
        return RATINGS.index(rating) + 1
    except ValueError:
        return 20


def generate_bond_universe(n: int = 200, seed: int = 42) -> list[dict[str, Any]]:
    """
    Generate a synthetic corporate bond universe for screening.

    Args:
        n: Number of bonds to generate.
        seed: Random seed for reproducibility.

    Returns:
        List of bond dicts with issuer, coupon, maturity, rating, sector, spread, duration, yield.
    """
    rng = random.Random(seed)
    issuers = [f"Corp_{i:03d}" for i in range(1, n + 1)]
    today = datetime.date.today()
    bonds = []

    for i, issuer in enumerate(issuers):
        rating = rng.choice(RATINGS[:15])  # up to B-
        sector = rng.choice(SECTORS)
        years_to_maturity = rng.uniform(0.5, 30)
        maturity_date = today + datetime.timedelta(days=int(years_to_maturity * 365.25))
        base_spread = RATING_SPREAD_MAP.get(rating, 200)
        spread_bps = max(10, base_spread + rng.gauss(0, base_spread * 0.2))
        coupon = round(rng.uniform(2.0, 8.5), 3)
        benchmark_yield = 4.0 + (years_to_maturity / 30) * 1.0  # simplified curve
        ytm = round(benchmark_yield + spread_bps / 100, 3)
        mod_duration = round(years_to_maturity * 0.85 / (1 + ytm / 100), 2)

        bonds.append({
            "issuer": issuer,
            "coupon": coupon,
            "maturity": maturity_date.isoformat(),
            "years_to_maturity": round(years_to_maturity, 2),
            "rating": rating,
            "rating_numeric": _rating_numeric(rating),
            "sector": sector,
            "spread_bps": round(spread_bps, 1),
            "ytm": ytm,
            "mod_duration": mod_duration,
            "convexity": round(mod_duration ** 2 * 0.012, 3),
        })

    return bonds


def screen_bonds(
    min_spread: float | None = None,
    max_spread: float | None = None,
    min_rating: str | None = None,
    max_rating: str | None = None,
    sectors: list[str] | None = None,
    min_duration: float | None = None,
    max_duration: float | None = None,
    min_ytm: float | None = None,
    max_ytm: float | None = None,
    min_maturity_years: float | None = None,
    max_maturity_years: float | None = None,
    sort_by: str = "spread_bps",
    ascending: bool = False,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Screen corporate bonds with multi-criteria filters.

    Args:
        min_spread: Minimum OAS spread in bps.
        max_spread: Maximum OAS spread in bps.
        min_rating: Best rating filter (e.g. 'A+' means A+ or worse).
        max_rating: Worst rating filter (e.g. 'BBB-' means BBB- or better).
        sectors: List of sectors to include.
        min_duration: Minimum modified duration.
        max_duration: Maximum modified duration.
        min_ytm: Minimum yield to maturity.
        max_ytm: Maximum yield to maturity.
        min_maturity_years: Minimum years to maturity.
        max_maturity_years: Maximum years to maturity.
        sort_by: Field to sort results by.
        ascending: Sort order.
        limit: Max results to return.

    Returns:
        Dict with matched bonds, count, and filter summary.
    """
    universe = generate_bond_universe(300)
    results = universe

    if min_spread is not None:
        results = [b for b in results if b["spread_bps"] >= min_spread]
    if max_spread is not None:
        results = [b for b in results if b["spread_bps"] <= max_spread]
    if min_rating is not None:
        threshold = _rating_numeric(min_rating)
        results = [b for b in results if b["rating_numeric"] >= threshold]
    if max_rating is not None:
        threshold = _rating_numeric(max_rating)
        results = [b for b in results if b["rating_numeric"] <= threshold]
    if sectors:
        sectors_lower = [s.lower() for s in sectors]
        results = [b for b in results if b["sector"].lower() in sectors_lower]
    if min_duration is not None:
        results = [b for b in results if b["mod_duration"] >= min_duration]
    if max_duration is not None:
        results = [b for b in results if b["mod_duration"] <= max_duration]
    if min_ytm is not None:
        results = [b for b in results if b["ytm"] >= min_ytm]
    if max_ytm is not None:
        results = [b for b in results if b["ytm"] <= max_ytm]
    if min_maturity_years is not None:
        results = [b for b in results if b["years_to_maturity"] >= min_maturity_years]
    if max_maturity_years is not None:
        results = [b for b in results if b["years_to_maturity"] <= max_maturity_years]

    results.sort(key=lambda b: b.get(sort_by, 0), reverse=not ascending)

    return {
        "total_matches": len(results),
        "bonds": results[:limit],
        "filters_applied": {
            k: v for k, v in {
                "min_spread": min_spread, "max_spread": max_spread,
                "min_rating": min_rating, "max_rating": max_rating,
                "sectors": sectors, "min_duration": min_duration,
                "max_duration": max_duration,
            }.items() if v is not None
        },
    }


def spread_distribution(sector: str | None = None) -> dict[str, Any]:
    """
    Compute spread distribution statistics across the bond universe.

    Args:
        sector: Optional sector filter.

    Returns:
        Dict with mean, median, std, percentiles by rating bucket.
    """
    universe = generate_bond_universe(300)
    if sector:
        universe = [b for b in universe if b["sector"].lower() == sector.lower()]

    buckets = {"IG": [], "HY": []}
    for b in universe:
        bucket = "IG" if b["rating_numeric"] <= 10 else "HY"  # BBB- = 10
        buckets[bucket].append(b["spread_bps"])

    stats = {}
    for label, spreads in buckets.items():
        if not spreads:
            continue
        spreads.sort()
        n = len(spreads)
        mean = sum(spreads) / n
        median = spreads[n // 2]
        variance = sum((s - mean) ** 2 for s in spreads) / n
        stats[label] = {
            "count": n,
            "mean_bps": round(mean, 1),
            "median_bps": round(median, 1),
            "std_bps": round(math.sqrt(variance), 1),
            "p25": round(spreads[n // 4], 1),
            "p75": round(spreads[3 * n // 4], 1),
            "min": round(spreads[0], 1),
            "max": round(spreads[-1], 1),
        }

    return {"sector": sector or "All", "distribution": stats}
