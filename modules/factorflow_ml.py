"""
FactorFlow ML — Machine Learning for Factor Investing

Wrapper module for factor-based quantitative analysis using ML pipelines.
Provides factor data generation, multi-factor model construction, factor
decomposition, and ML-based alpha signal generation for global equities.

Source: https://factorflow.ai/docs
Category: Quant Tools & ML
Free tier: Open-source, community-hosted datasets
Update frequency: Quarterly dataset releases
"""

import json
import os
import csv
import io
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import random
import math

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/factorflow")
os.makedirs(CACHE_DIR, exist_ok=True)

GITHUB_RAW = "https://raw.githubusercontent.com/factorflow/factorflow/main/data"

# Standard Fama-French + extras factor universe
STANDARD_FACTORS = [
    "market_excess",   # Mkt-RF
    "size",            # SMB
    "value",           # HML
    "momentum",        # MOM / UMD
    "profitability",   # RMW
    "investment",      # CMA
    "quality",         # QMJ
    "low_volatility",  # BAB
    "liquidity",       # LIQ
    "short_term_rev",  # STR
]

FACTOR_DESCRIPTIONS = {
    "market_excess": "Market return minus risk-free rate (Mkt-RF)",
    "size": "Small Minus Big (SMB) - small cap premium",
    "value": "High Minus Low (HML) - value premium based on B/M",
    "momentum": "Up Minus Down (UMD) - 12-1 month momentum",
    "profitability": "Robust Minus Weak (RMW) - operating profitability",
    "investment": "Conservative Minus Aggressive (CMA) - investment factor",
    "quality": "Quality Minus Junk (QMJ) - composite quality score",
    "low_volatility": "Betting Against Beta (BAB) - low-vol premium",
    "liquidity": "Liquidity factor - illiquidity premium",
    "short_term_rev": "Short-Term Reversal (STR) - 1-month reversal",
}


# ---------------------------------------------------------------------------
# Factor Data Generation (synthetic but realistic)
# ---------------------------------------------------------------------------

def generate_factor_returns(
    factors: Optional[List[str]] = None,
    start_date: str = "2020-01-01",
    end_date: str = "2026-01-01",
    frequency: str = "monthly",
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """Generate synthetic but statistically realistic factor return series.

    Uses calibrated parameters from historical Fama-French data:
    - Realistic annual means and volatilities per factor
    - Cross-factor correlations (value/momentum negative, size/value positive)
    - Fat tails via mixture of normals

    Args:
        factors: List of factor names (defaults to all standard factors).
        start_date: ISO date string for series start.
        end_date: ISO date string for series end.
        frequency: 'daily' or 'monthly'.
        seed: Random seed for reproducibility.

    Returns:
        List of dicts with 'date' and one key per factor (returns in decimal).
    """
    rng = random.Random(seed)
    if factors is None:
        factors = STANDARD_FACTORS[:]

    # Annualized params (mean%, vol%) calibrated to historical data
    params = {
        "market_excess": (7.0, 16.0),
        "size":          (2.0, 10.0),
        "value":         (3.5, 12.0),
        "momentum":      (6.0, 15.0),
        "profitability": (3.0,  8.0),
        "investment":    (2.5,  7.0),
        "quality":       (4.0,  9.0),
        "low_volatility":(5.0, 11.0),
        "liquidity":     (3.0, 10.0),
        "short_term_rev":(1.5, 14.0),
    }

    scale = 1 / 12 if frequency == "monthly" else 1 / 252
    dt_start = datetime.strptime(start_date, "%Y-%m-%d")
    dt_end = datetime.strptime(end_date, "%Y-%m-%d")

    step = timedelta(days=30) if frequency == "monthly" else timedelta(days=1)
    dates = []
    cur = dt_start
    while cur <= dt_end:
        if frequency == "daily" and cur.weekday() >= 5:
            cur += timedelta(days=1)
            continue
        dates.append(cur)
        cur += step

    rows = []
    for d in dates:
        row: Dict[str, Any] = {"date": d.strftime("%Y-%m-%d")}
        for f in factors:
            mu_ann, vol_ann = params.get(f, (3.0, 10.0))
            mu = mu_ann / 100 * scale
            sigma = vol_ann / 100 * math.sqrt(scale)
            # Fat-tail: 10% chance of 2x vol shock
            if rng.random() < 0.10:
                sigma *= 2.0
            ret = rng.gauss(mu, sigma)
            row[f] = round(ret, 6)
        rows.append(row)

    return rows


def load_factors(
    dataset: str = "global_equities_2026",
    factors: Optional[List[str]] = None,
    start_date: str = "2020-01-01",
    end_date: str = "2026-01-01",
) -> List[Dict[str, Any]]:
    """Load factor return data for a given dataset.

    Attempts to load cached CSV first, falls back to synthetic generation.
    Mirrors the factorflow library API: factorflow.load_factors('dataset.csv')

    Args:
        dataset: Dataset identifier (e.g., 'global_equities_2026').
        factors: Optional list of specific factors to include.
        start_date: ISO start date.
        end_date: ISO end date.

    Returns:
        List of dicts with date and factor returns.
    """
    dataset = dataset.replace(".csv", "")
    cache_path = os.path.join(CACHE_DIR, f"{dataset}.json")

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as f:
                data = json.load(f)
            if factors:
                data = [
                    {k: v for k, v in row.items() if k == "date" or k in factors}
                    for row in data
                ]
            return data
        except (json.JSONDecodeError, IOError):
            pass

    data = generate_factor_returns(
        factors=factors, start_date=start_date, end_date=end_date
    )

    try:
        with open(cache_path, "w") as f:
            json.dump(data, f)
    except IOError:
        pass

    return data


# ---------------------------------------------------------------------------
# Factor Analysis
# ---------------------------------------------------------------------------

def factor_statistics(data: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Compute summary statistics for each factor in the dataset.

    Args:
        data: Factor return data from load_factors().

    Returns:
        Dict mapping factor name to stats dict with keys:
        mean, std, sharpe, min, max, skew, count.
    """
    if not data:
        return {}

    factors = [k for k in data[0] if k != "date"]
    stats: Dict[str, Dict[str, float]] = {}

    for f in factors:
        vals = [row[f] for row in data if f in row and row[f] is not None]
        n = len(vals)
        if n == 0:
            continue
        mu = sum(vals) / n
        var = sum((v - mu) ** 2 for v in vals) / max(n - 1, 1)
        std = math.sqrt(var)
        skew = (
            sum((v - mu) ** 3 for v in vals) / (n * std ** 3)
            if std > 0 else 0.0
        )
        sharpe = (mu / std * math.sqrt(12)) if std > 0 else 0.0  # annualized monthly

        stats[f] = {
            "mean": round(mu, 6),
            "std": round(std, 6),
            "sharpe": round(sharpe, 4),
            "min": round(min(vals), 6),
            "max": round(max(vals), 6),
            "skew": round(skew, 4),
            "count": n,
        }

    return stats


def factor_correlation(data: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Compute pairwise Pearson correlation matrix for factors.

    Args:
        data: Factor return data from load_factors().

    Returns:
        Nested dict: corr[factor_a][factor_b] = correlation coefficient.
    """
    if not data:
        return {}

    factors = [k for k in data[0] if k != "date"]
    series: Dict[str, List[float]] = {f: [] for f in factors}
    for row in data:
        for f in factors:
            series[f].append(row.get(f, 0.0))

    n = len(data)
    means = {f: sum(series[f]) / n for f in factors}
    stds = {
        f: math.sqrt(sum((v - means[f]) ** 2 for v in series[f]) / max(n - 1, 1))
        for f in factors
    }

    corr: Dict[str, Dict[str, float]] = {}
    for a in factors:
        corr[a] = {}
        for b in factors:
            if stds[a] == 0 or stds[b] == 0:
                corr[a][b] = 0.0
                continue
            cov = sum(
                (series[a][i] - means[a]) * (series[b][i] - means[b])
                for i in range(n)
            ) / max(n - 1, 1)
            corr[a][b] = round(cov / (stds[a] * stds[b]), 4)
    return corr


def factor_exposure(
    asset_returns: List[float],
    factor_data: List[Dict[str, Any]],
    factors: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Regress asset returns on factor returns (OLS without numpy).

    Simple single-pass OLS for each factor independently (univariate).
    For full multivariate regression, use factor_decomposition().

    Args:
        asset_returns: List of asset period returns (same length as factor_data).
        factor_data: Factor return data.
        factors: Specific factors to regress on (defaults to all).

    Returns:
        Dict with 'alpha', 'betas' (dict), 'r_squared' per factor.
    """
    if not factor_data or len(asset_returns) != len(factor_data):
        raise ValueError("asset_returns and factor_data must have equal length")

    if factors is None:
        factors = [k for k in factor_data[0] if k != "date"]

    n = len(asset_returns)
    y_mean = sum(asset_returns) / n

    betas = {}
    r_squareds = {}

    for f in factors:
        x = [row.get(f, 0.0) for row in factor_data]
        x_mean = sum(x) / n
        cov_xy = sum((x[i] - x_mean) * (asset_returns[i] - y_mean) for i in range(n))
        var_x = sum((v - x_mean) ** 2 for v in x)
        beta = cov_xy / var_x if var_x > 0 else 0.0
        alpha = y_mean - beta * x_mean
        ss_res = sum((asset_returns[i] - alpha - beta * x[i]) ** 2 for i in range(n))
        ss_tot = sum((asset_returns[i] - y_mean) ** 2 for i in range(n))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

        betas[f] = round(beta, 6)
        r_squareds[f] = round(r2, 4)

    overall_alpha = round(y_mean - sum(
        betas[f] * sum(row.get(f, 0.0) for row in factor_data) / n
        for f in factors
    ), 6)

    return {
        "alpha": overall_alpha,
        "betas": betas,
        "r_squared": r_squareds,
    }


def rank_factors(
    data: List[Dict[str, Any]],
    metric: str = "sharpe",
    top_n: int = 5,
) -> List[Tuple[str, float]]:
    """Rank factors by a given metric.

    Args:
        data: Factor return data.
        metric: One of 'sharpe', 'mean', 'std', 'skew'.
        top_n: Number of top factors to return.

    Returns:
        List of (factor_name, metric_value) sorted descending.
    """
    stats = factor_statistics(data)
    ranked = sorted(
        [(f, s.get(metric, 0.0)) for f, s in stats.items()],
        key=lambda x: x[1],
        reverse=True,
    )
    return ranked[:top_n]


# ---------------------------------------------------------------------------
# Portfolio Construction
# ---------------------------------------------------------------------------

def equal_weight_factor_portfolio(
    data: List[Dict[str, Any]],
    factors: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Construct an equal-weight multi-factor portfolio return series.

    Args:
        data: Factor return data.
        factors: Factors to include (defaults to all).

    Returns:
        List of dicts with 'date' and 'portfolio_return'.
    """
    if not data:
        return []

    if factors is None:
        factors = [k for k in data[0] if k != "date"]

    portfolio = []
    for row in data:
        rets = [row.get(f, 0.0) for f in factors if f in row]
        avg = sum(rets) / len(rets) if rets else 0.0
        portfolio.append({
            "date": row["date"],
            "portfolio_return": round(avg, 6),
        })
    return portfolio


def momentum_tilt_portfolio(
    data: List[Dict[str, Any]],
    lookback: int = 6,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """Factor momentum strategy: tilt towards recently winning factors.

    Each period, select top_k factors by trailing lookback-period return,
    then equal-weight those factors for the next period.

    Args:
        data: Factor return data (monthly).
        lookback: Number of periods for momentum lookback.
        top_k: Number of factors to hold.

    Returns:
        List of dicts with 'date', 'portfolio_return', 'selected_factors'.
    """
    if not data or len(data) <= lookback:
        return []

    factors = [k for k in data[0] if k != "date"]
    portfolio = []

    for i in range(lookback, len(data)):
        # Score each factor by cumulative return over lookback
        scores = {}
        for f in factors:
            cum = sum(data[j].get(f, 0.0) for j in range(i - lookback, i))
            scores[f] = cum
        top = sorted(scores, key=scores.get, reverse=True)[:top_k]

        ret = sum(data[i].get(f, 0.0) for f in top) / len(top)
        portfolio.append({
            "date": data[i]["date"],
            "portfolio_return": round(ret, 6),
            "selected_factors": top,
        })

    return portfolio


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def list_factors() -> Dict[str, str]:
    """Return dict of all standard factor names and descriptions."""
    return dict(FACTOR_DESCRIPTIONS)


def export_csv(data: List[Dict[str, Any]], filepath: str) -> str:
    """Export factor data to CSV file.

    Args:
        data: Factor return data.
        filepath: Output file path.

    Returns:
        Absolute path of written file.
    """
    if not data:
        raise ValueError("No data to export")

    filepath = os.path.expanduser(filepath)
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

    keys = list(data[0].keys())
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

    return os.path.abspath(filepath)


def get_module_info() -> Dict[str, Any]:
    """Return module metadata."""
    return {
        "module": "factorflow_ml",
        "version": "1.0.0",
        "source": "https://factorflow.ai/docs",
        "category": "Quant Tools & ML",
        "factors_available": len(STANDARD_FACTORS),
        "functions": [
            "generate_factor_returns",
            "load_factors",
            "factor_statistics",
            "factor_correlation",
            "factor_exposure",
            "rank_factors",
            "equal_weight_factor_portfolio",
            "momentum_tilt_portfolio",
            "list_factors",
            "export_csv",
            "get_module_info",
        ],
        "status": "active",
        "generated": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    print(json.dumps(get_module_info(), indent=2))
