"""
Taylor Rule Calculator — computes implied policy rates for G10 central banks.

Implements the classic Taylor (1993) rule and variants (balanced approach,
inertial) using free macro data from FRED, IMF, and OECD.
"""

import json
import urllib.request
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# Default parameters for G10 economies
G10_PARAMS = {
    "US": {"inflation_target": 2.0, "neutral_real_rate": 0.5,
            "fred_inflation": "PCEPILFE", "fred_unemployment": "UNRATE",
            "fred_gdp_gap": None, "nairu": 4.0},
    "EU": {"inflation_target": 2.0, "neutral_real_rate": 0.0,
            "fred_inflation": "CP0000EZ19M086NEST", "fred_unemployment": "LRHUTTTTEZM156S",
            "fred_gdp_gap": None, "nairu": 6.5},
    "UK": {"inflation_target": 2.0, "neutral_real_rate": 0.25,
            "fred_inflation": "CPGRLE01GBM659N", "fred_unemployment": "LRHUTTTTGBM156S",
            "fred_gdp_gap": None, "nairu": 4.0},
    "JP": {"inflation_target": 2.0, "neutral_real_rate": -0.5,
            "fred_inflation": "JPNCPIALLMINMEI", "fred_unemployment": "LRHUTTTTJPM156S",
            "fred_gdp_gap": None, "nairu": 2.5},
    "CA": {"inflation_target": 2.0, "neutral_real_rate": 0.5,
            "fred_inflation": "CPGRLE01CAM659N", "fred_unemployment": "LRHUTTTTCAM156S",
            "fred_gdp_gap": None, "nairu": 5.5},
    "AU": {"inflation_target": 2.5, "neutral_real_rate": 0.5,
            "fred_inflation": "AUSCPIALLQINMEI", "fred_unemployment": "LRHUTTTTAUM156S",
            "fred_gdp_gap": None, "nairu": 4.5},
    "NZ": {"inflation_target": 2.0, "neutral_real_rate": 0.5,
            "fred_inflation": "NZLCPIALLQINMEI", "fred_unemployment": "LRHUTTTTNZM156S",
            "fred_gdp_gap": None, "nairu": 4.5},
    "CH": {"inflation_target": 1.0, "neutral_real_rate": -0.5,
            "fred_inflation": "CHECPIALLMINMEI", "fred_unemployment": "LRHUTTTTCHM156S",
            "fred_gdp_gap": None, "nairu": 4.0},
    "SE": {"inflation_target": 2.0, "neutral_real_rate": 0.0,
            "fred_inflation": "SWECPIALLMINMEI", "fred_unemployment": "LRHUTTTTSEM156S",
            "fred_gdp_gap": None, "nairu": 7.0},
    "NO": {"inflation_target": 2.0, "neutral_real_rate": 0.5,
            "fred_inflation": "NORCPIALLMINMEI", "fred_unemployment": "LRHUTTTTNOM156S",
            "fred_gdp_gap": None, "nairu": 3.5},
}


@dataclass
class TaylorRuleResult:
    """Result of a Taylor Rule calculation."""
    country: str
    implied_rate: float
    current_inflation: float
    inflation_target: float
    inflation_gap: float
    output_gap: float
    neutral_real_rate: float
    variant: str
    timestamp: str


def fetch_fred_latest(series_id: str, api_key: str = "DEMO_KEY",
                      limit: int = 12) -> Optional[float]:
    """Fetch the latest value from a FRED series.

    Args:
        series_id: FRED series identifier.
        api_key: FRED API key (DEMO_KEY for limited access).
        limit: Number of recent observations to fetch.

    Returns:
        Latest available value as float, or None if unavailable.
    """
    url = (f"{FRED_BASE}?series_id={series_id}&api_key={api_key}"
           f"&file_type=json&sort_order=desc&limit={limit}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        for obs in data.get("observations", []):
            if obs["value"] != ".":
                return float(obs["value"])
    except Exception:
        pass
    return None


def classic_taylor_rule(inflation: float, output_gap: float,
                        inflation_target: float = 2.0,
                        neutral_real_rate: float = 0.5,
                        alpha: float = 0.5, beta: float = 0.5) -> float:
    """Classic Taylor (1993) rule.

    i = r* + π + α(π − π*) + β(y − y*)

    Args:
        inflation: Current inflation rate (%).
        output_gap: Output gap as % of potential GDP.
        inflation_target: Target inflation rate (%).
        neutral_real_rate: Equilibrium real interest rate (%).
        alpha: Weight on inflation gap.
        beta: Weight on output gap.

    Returns:
        Implied nominal policy rate (%).
    """
    return neutral_real_rate + inflation + alpha * (inflation - inflation_target) + beta * output_gap


def balanced_approach_rule(inflation: float, output_gap: float,
                           inflation_target: float = 2.0,
                           neutral_real_rate: float = 0.5) -> float:
    """Balanced approach rule (Yellen variant) with higher output gap weight.

    Args:
        inflation: Current inflation rate (%).
        output_gap: Output gap as % of potential GDP.
        inflation_target: Target inflation rate (%).
        neutral_real_rate: Equilibrium real interest rate (%).

    Returns:
        Implied nominal policy rate (%).
    """
    return classic_taylor_rule(inflation, output_gap, inflation_target,
                                neutral_real_rate, alpha=0.5, beta=1.0)


def inertial_taylor_rule(inflation: float, output_gap: float,
                          current_rate: float,
                          inflation_target: float = 2.0,
                          neutral_real_rate: float = 0.5,
                          smoothing: float = 0.85) -> float:
    """Inertial Taylor rule with interest rate smoothing.

    Args:
        inflation: Current inflation rate (%).
        output_gap: Output gap as % of potential GDP.
        current_rate: Current policy rate (%).
        inflation_target: Target inflation rate (%).
        neutral_real_rate: Equilibrium real interest rate (%).
        smoothing: Smoothing parameter (0-1, higher = more inertia).

    Returns:
        Implied nominal policy rate (%).
    """
    target = classic_taylor_rule(inflation, output_gap, inflation_target, neutral_real_rate)
    return smoothing * current_rate + (1 - smoothing) * target


def estimate_output_gap_okun(unemployment: float, nairu: float,
                              okun_coefficient: float = 2.0) -> float:
    """Estimate output gap from unemployment using Okun's law.

    Args:
        unemployment: Current unemployment rate (%).
        nairu: Non-accelerating inflation rate of unemployment (%).
        okun_coefficient: Okun's law coefficient (typically 1.5-2.5).

    Returns:
        Estimated output gap (%).
    """
    return -okun_coefficient * (unemployment - nairu)


def calculate_taylor_rule_g10(
    api_key: str = "DEMO_KEY",
    variant: str = "classic",
    overrides: Optional[Dict[str, Dict]] = None
) -> List[TaylorRuleResult]:
    """Calculate Taylor Rule implied rates for all G10 central banks.

    Args:
        api_key: FRED API key.
        variant: 'classic', 'balanced', or 'inertial'.
        overrides: Optional dict of country -> {inflation, unemployment, current_rate}.

    Returns:
        List of TaylorRuleResult for each country with available data.
    """
    results = []
    overrides = overrides or {}

    for country, params in G10_PARAMS.items():
        ov = overrides.get(country, {})
        inflation = ov.get("inflation")
        unemployment = ov.get("unemployment")

        if inflation is None:
            inflation = fetch_fred_latest(params["fred_inflation"], api_key)
        if unemployment is None and params["fred_unemployment"]:
            unemployment = fetch_fred_latest(params["fred_unemployment"], api_key)

        if inflation is None:
            continue

        output_gap = 0.0
        if unemployment is not None:
            output_gap = estimate_output_gap_okun(unemployment, params["nairu"])

        inflation_gap = inflation - params["inflation_target"]

        if variant == "balanced":
            implied = balanced_approach_rule(inflation, output_gap,
                                             params["inflation_target"],
                                             params["neutral_real_rate"])
        elif variant == "inertial":
            current_rate = ov.get("current_rate", 0.0)
            implied = inertial_taylor_rule(inflation, output_gap, current_rate,
                                            params["inflation_target"],
                                            params["neutral_real_rate"])
        else:
            implied = classic_taylor_rule(inflation, output_gap,
                                           params["inflation_target"],
                                           params["neutral_real_rate"])

        results.append(TaylorRuleResult(
            country=country,
            implied_rate=round(implied, 2),
            current_inflation=round(inflation, 2),
            inflation_target=params["inflation_target"],
            inflation_gap=round(inflation_gap, 2),
            output_gap=round(output_gap, 2),
            neutral_real_rate=params["neutral_real_rate"],
            variant=variant,
            timestamp=datetime.utcnow().isoformat()
        ))

    return results


def compare_to_actual(results: List[TaylorRuleResult],
                      actual_rates: Dict[str, float]) -> List[Dict]:
    """Compare Taylor Rule implied rates to actual policy rates.

    Args:
        results: List of TaylorRuleResult objects.
        actual_rates: Dict of country code -> actual policy rate (%).

    Returns:
        List of dicts with country, implied, actual, and gap.
    """
    comparisons = []
    for r in results:
        actual = actual_rates.get(r.country)
        if actual is not None:
            gap = r.implied_rate - actual
            stance = "too loose" if gap > 0.5 else "too tight" if gap < -0.5 else "appropriate"
            comparisons.append({
                "country": r.country,
                "implied_rate": r.implied_rate,
                "actual_rate": actual,
                "gap": round(gap, 2),
                "stance": stance,
                "inflation": r.current_inflation,
                "output_gap": r.output_gap
            })
    return sorted(comparisons, key=lambda x: abs(x["gap"]), reverse=True)
