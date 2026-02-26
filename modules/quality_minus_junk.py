"""Quality Minus Junk (QMJ) Factor — Implements the Asness-Frazzini-Pedersen (2019)
quality factor that goes long high-quality stocks and short low-quality (junk) stocks.

Quality is a composite of:
  - Profitability (GPOA, ROE, ROA, CF/Assets, gross margin, low accruals)
  - Growth (5-year growth in profitability measures)
  - Safety (low beta, low leverage, low earnings vol, low bankruptcy risk)
  - Payout (equity issuance, debt issuance, dividend payout)

Data sources: SEC XBRL (free), Yahoo Finance (free), FRED (free).
"""

import math
from typing import Dict, List, Optional, Tuple


def compute_profitability_score(
    gross_profit: float,
    total_assets: float,
    net_income: float,
    equity: float,
    operating_cf: float,
    revenue: float,
    cogs: float,
    accruals: float,
) -> Dict[str, float]:
    """Compute profitability z-scores for QMJ.

    Args:
        gross_profit: Gross profit (TTM).
        total_assets: Total assets.
        net_income: Net income (TTM).
        equity: Total shareholders' equity.
        operating_cf: Operating cash flow (TTM).
        revenue: Total revenue (TTM).
        cogs: Cost of goods sold (TTM).
        accruals: Total accruals (net income - operating CF).

    Returns:
        Dict of individual profitability metrics.
    """
    gpoa = gross_profit / total_assets if total_assets > 0 else 0
    roe = net_income / equity if equity > 0 else 0
    roa = net_income / total_assets if total_assets > 0 else 0
    cfoa = operating_cf / total_assets if total_assets > 0 else 0
    gross_margin = (revenue - cogs) / revenue if revenue > 0 else 0
    acc_ratio = accruals / total_assets if total_assets > 0 else 0  # Lower is better

    return {
        "gpoa": round(gpoa, 6),
        "roe": round(roe, 6),
        "roa": round(roa, 6),
        "cfoa": round(cfoa, 6),
        "gross_margin": round(gross_margin, 6),
        "accruals_ratio": round(acc_ratio, 6),
    }


def compute_safety_score(
    beta: float,
    leverage: float,
    earnings_volatility: float,
    z_score_altman: float,
) -> Dict[str, float]:
    """Compute safety component of QMJ.

    Args:
        beta: Market beta (lower is safer).
        leverage: Total debt / total assets (lower is safer).
        earnings_volatility: Std dev of ROE over 5 years (lower is safer).
        z_score_altman: Altman Z-Score (higher is safer).

    Returns:
        Safety metrics (all oriented so higher = safer/better quality).
    """
    return {
        "low_beta": round(-beta, 6),  # Negative so lower beta = higher score
        "low_leverage": round(-leverage, 6),
        "low_earnings_vol": round(-earnings_volatility, 6),
        "altman_z": round(z_score_altman, 6),
    }


def composite_quality_score(
    profitability: Dict[str, float],
    safety: Dict[str, float],
    growth_5yr: Optional[Dict[str, float]] = None,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """Compute composite quality score from components.

    Args:
        profitability: Output of compute_profitability_score.
        safety: Output of compute_safety_score.
        growth_5yr: Optional 5-year growth in profitability metrics.
        weights: Component weights (default equal).

    Returns:
        Composite quality score (higher = better quality).
    """
    if weights is None:
        weights = {"profitability": 0.4, "safety": 0.3, "growth": 0.3}

    # Average within each component
    prof_score = sum(v for k, v in profitability.items() if k != "accruals_ratio")
    prof_score -= profitability.get("accruals_ratio", 0)  # Lower accruals = better
    prof_score /= len(profitability)

    safety_score = sum(safety.values()) / len(safety) if safety else 0

    growth_score = 0
    if growth_5yr:
        growth_score = sum(growth_5yr.values()) / len(growth_5yr)

    composite = (
        weights.get("profitability", 0.4) * prof_score
        + weights.get("safety", 0.3) * safety_score
        + weights.get("growth", 0.3) * growth_score
    )

    return round(composite, 6)


def construct_qmj_portfolio(
    quality_scores: Dict[str, float],
    n_long: int = 10,
    n_short: int = 10,
) -> Dict[str, object]:
    """Construct Quality Minus Junk long-short portfolio.

    Args:
        quality_scores: Dict of ticker -> composite quality score.
        n_long: Number of high-quality stocks to go long.
        n_short: Number of junk stocks to short.

    Returns:
        QMJ portfolio with positions and summary.
    """
    if len(quality_scores) < n_long + n_short:
        raise ValueError(f"Need {n_long + n_short} stocks, have {len(quality_scores)}")

    ranked = sorted(quality_scores.items(), key=lambda x: x[1], reverse=True)
    quality = ranked[:n_long]
    junk = ranked[-n_short:]

    w_long = 1.0 / n_long
    w_short = 1.0 / n_short

    return {
        "long": {t: {"weight": round(w_long, 6), "quality_score": round(s, 6)} for t, s in quality},
        "short": {t: {"weight": round(w_short, 6), "quality_score": round(s, 6)} for t, s in junk},
        "quality_spread": round(
            sum(s for _, s in quality) / n_long - sum(s for _, s in junk) / n_short, 6
        ),
        "long_avg_quality": round(sum(s for _, s in quality) / n_long, 6),
        "short_avg_quality": round(sum(s for _, s in junk) / n_short, 6),
        "n_long": n_long,
        "n_short": n_short,
    }


def rank_universe_by_quality(
    universe: Dict[str, Dict],
) -> List[Tuple[str, float, str]]:
    """Rank a universe of stocks by quality score and assign quintile labels.

    Args:
        universe: Dict of ticker -> dict with keys matching compute_profitability_score args.

    Returns:
        List of (ticker, quality_score, quintile_label) sorted by quality descending.
    """
    scores = {}
    for ticker, data in universe.items():
        prof = compute_profitability_score(
            gross_profit=data.get("gross_profit", 0),
            total_assets=data.get("total_assets", 1),
            net_income=data.get("net_income", 0),
            equity=data.get("equity", 1),
            operating_cf=data.get("operating_cf", 0),
            revenue=data.get("revenue", 1),
            cogs=data.get("cogs", 0),
            accruals=data.get("accruals", 0),
        )
        safety = compute_safety_score(
            beta=data.get("beta", 1.0),
            leverage=data.get("leverage", 0.5),
            earnings_volatility=data.get("earnings_vol", 0.1),
            z_score_altman=data.get("altman_z", 2.0),
        )
        scores[ticker] = composite_quality_score(prof, safety)

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    n = len(ranked)
    quintile_size = max(1, n // 5)

    result = []
    for i, (ticker, score) in enumerate(ranked):
        if i < quintile_size:
            label = "Q1_HIGH_QUALITY"
        elif i < 2 * quintile_size:
            label = "Q2"
        elif i < 3 * quintile_size:
            label = "Q3"
        elif i < 4 * quintile_size:
            label = "Q4"
        else:
            label = "Q5_JUNK"
        result.append((ticker, score, label))

    return result
