"""
Real Rate Monitor — tracks global inflation-adjusted interest rates.

Monitors real (inflation-adjusted) policy rates, bond yields, and real rate
differentials across major economies using free data from FRED and central banks.
"""

import json
import urllib.request
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# Country config: policy rate series, inflation series, 10Y yield series
COUNTRY_CONFIG = {
    "US": {
        "name": "United States",
        "policy_rate": "FEDFUNDS",
        "inflation": "PCEPILFE",  # Core PCE
        "headline_cpi": "CPIAUCSL",
        "yield_10y": "DGS10",
        "tips_10y": "DFII10",  # Real yield directly from TIPS
    },
    "EU": {
        "name": "Eurozone",
        "policy_rate": "ECBDFR",
        "inflation": "CP0000EZ19M086NEST",
        "headline_cpi": None,
        "yield_10y": "IRLTLT01DEM156N",  # Germany 10Y as proxy
        "tips_10y": None,
    },
    "UK": {
        "name": "United Kingdom",
        "policy_rate": "BOERUKM",
        "inflation": "CPGRLE01GBM659N",
        "headline_cpi": None,
        "yield_10y": "IRLTLT01GBM156N",
        "tips_10y": None,
    },
    "JP": {
        "name": "Japan",
        "policy_rate": "IRSTCB01JPM156N",
        "inflation": "JPNCPIALLMINMEI",
        "headline_cpi": None,
        "yield_10y": "IRLTLT01JPM156N",
        "tips_10y": None,
    },
    "CA": {
        "name": "Canada",
        "policy_rate": "IRSTCB01CAM156N",
        "inflation": "CPGRLE01CAM659N",
        "headline_cpi": None,
        "yield_10y": "IRLTLT01CAM156N",
        "tips_10y": None,
    },
    "AU": {
        "name": "Australia",
        "policy_rate": "IRSTCB01AUM156N",
        "inflation": "AUSCPIALLQINMEI",
        "headline_cpi": None,
        "yield_10y": "IRLTLT01AUM156N",
        "tips_10y": None,
    },
}


@dataclass
class RealRateData:
    """Real rate data for a single country."""
    country: str
    country_name: str
    nominal_policy_rate: float
    inflation: float
    real_policy_rate: float
    nominal_10y: Optional[float]
    real_10y: Optional[float]
    tips_real_yield: Optional[float]  # Market-implied from TIPS
    inflation_expectations: Optional[float]  # breakeven
    timestamp: str


def _fetch_fred(series_id: str, api_key: str = "DEMO_KEY") -> Optional[float]:
    """Fetch latest FRED value."""
    url = (f"{FRED_BASE}?series_id={series_id}&api_key={api_key}"
           f"&file_type=json&sort_order=desc&limit=12")
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


def get_real_rates(countries: Optional[List[str]] = None,
                   api_key: str = "DEMO_KEY") -> List[RealRateData]:
    """Fetch real rates for specified countries.

    Args:
        countries: List of country codes (default: all configured).
        api_key: FRED API key.

    Returns:
        List of RealRateData sorted by real policy rate.
    """
    if countries is None:
        countries = list(COUNTRY_CONFIG.keys())

    results = []
    for cc in countries:
        cfg = COUNTRY_CONFIG.get(cc)
        if not cfg:
            continue

        policy = _fetch_fred(cfg["policy_rate"], api_key)
        inflation = _fetch_fred(cfg["inflation"], api_key)
        nominal_10y = _fetch_fred(cfg["yield_10y"], api_key) if cfg["yield_10y"] else None
        tips = _fetch_fred(cfg["tips_10y"], api_key) if cfg.get("tips_10y") else None

        if policy is None or inflation is None:
            continue

        real_policy = policy - inflation
        real_10y = (nominal_10y - inflation) if nominal_10y is not None else None
        breakeven = (nominal_10y - tips) if (nominal_10y and tips) else None

        results.append(RealRateData(
            country=cc,
            country_name=cfg["name"],
            nominal_policy_rate=round(policy, 2),
            inflation=round(inflation, 2),
            real_policy_rate=round(real_policy, 2),
            nominal_10y=round(nominal_10y, 2) if nominal_10y else None,
            real_10y=round(real_10y, 2) if real_10y else None,
            tips_real_yield=round(tips, 2) if tips else None,
            inflation_expectations=round(breakeven, 2) if breakeven else None,
            timestamp=datetime.utcnow().isoformat()
        ))

    return sorted(results, key=lambda x: x.real_policy_rate, reverse=True)


def real_rate_differential(base: str, quote: str,
                           api_key: str = "DEMO_KEY") -> Optional[Dict]:
    """Calculate real rate differential between two countries.

    Positive = base has higher real rates (should attract capital / strengthen currency).

    Args:
        base: Base country code.
        quote: Quote country code.
        api_key: FRED API key.

    Returns:
        Dict with differential analysis or None.
    """
    rates = get_real_rates([base, quote], api_key)
    rate_map = {r.country: r for r in rates}

    if base not in rate_map or quote not in rate_map:
        return None

    b, q = rate_map[base], rate_map[quote]
    policy_diff = b.real_policy_rate - q.real_policy_rate

    bond_diff = None
    if b.real_10y is not None and q.real_10y is not None:
        bond_diff = round(b.real_10y - q.real_10y, 2)

    return {
        "pair": f"{base}/{quote}",
        "real_policy_differential": round(policy_diff, 2),
        "real_bond_differential": bond_diff,
        "base_real_rate": b.real_policy_rate,
        "quote_real_rate": q.real_policy_rate,
        "base_inflation": b.inflation,
        "quote_inflation": q.inflation,
        "capital_flow_bias": f"toward {base}" if policy_diff > 0 else f"toward {quote}",
        "timestamp": datetime.utcnow().isoformat()
    }


def global_real_rate_dashboard(api_key: str = "DEMO_KEY") -> Dict:
    """Generate a global real rate dashboard.

    Args:
        api_key: FRED API key.

    Returns:
        Comprehensive dashboard with rates, rankings, and differentials.
    """
    rates = get_real_rates(api_key=api_key)

    avg_real = sum(r.real_policy_rate for r in rates) / len(rates) if rates else 0
    most_restrictive = rates[0] if rates else None
    most_accommodative = rates[-1] if rates else None

    # Key differentials
    diffs = []
    pairs = [("US", "EU"), ("US", "JP"), ("US", "UK"), ("EU", "JP")]
    for b, q in pairs:
        d = real_rate_differential(b, q, api_key)
        if d:
            diffs.append(d)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "global_average_real_rate": round(avg_real, 2),
        "most_restrictive": {
            "country": most_restrictive.country,
            "real_rate": most_restrictive.real_policy_rate
        } if most_restrictive else None,
        "most_accommodative": {
            "country": most_accommodative.country,
            "real_rate": most_accommodative.real_policy_rate
        } if most_accommodative else None,
        "country_rates": [
            {"country": r.country, "nominal": r.nominal_policy_rate,
             "inflation": r.inflation, "real": r.real_policy_rate,
             "real_10y": r.real_10y}
            for r in rates
        ],
        "key_differentials": diffs
    }
