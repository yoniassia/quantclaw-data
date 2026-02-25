"""Risk Parity Portfolio Constructor — equal risk contribution portfolio optimization.

Builds portfolios where each asset contributes equally to total portfolio risk,
following the Bridgewater All Weather / Risk Parity methodology.
"""

import datetime
import json
import math
import urllib.request
from typing import Dict, List, Optional, Tuple


def fetch_returns(symbol: str, days: int = 252) -> List[float]:
    """Fetch daily returns for a symbol.

    Args:
        symbol: Ticker symbol.
        days: Lookback period.

    Returns:
        List of daily returns.
    """
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        f"?range={days}d&interval=1d"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
    prices = [c for c in closes if c is not None]
    return [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]


def compute_covariance_matrix(returns_dict: Dict[str, List[float]]) -> Tuple[List[str], List[List[float]]]:
    """Compute covariance matrix from multiple asset returns.

    Args:
        returns_dict: Mapping of symbol -> list of returns.

    Returns:
        Tuple of (asset names, covariance matrix).
    """
    assets = list(returns_dict.keys())
    n = len(assets)
    # Align lengths
    min_len = min(len(r) for r in returns_dict.values())
    aligned = {a: returns_dict[a][-min_len:] for a in assets}

    means = {a: sum(aligned[a]) / min_len for a in assets}
    cov = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for j in range(i, n):
            ai, aj = assets[i], assets[j]
            c = sum(
                (aligned[ai][k] - means[ai]) * (aligned[aj][k] - means[aj])
                for k in range(min_len)
            ) / (min_len - 1)
            cov[i][j] = c
            cov[j][i] = c

    return assets, cov


def risk_parity_weights(
    assets: List[str], cov: List[List[float]], max_iter: int = 500, tol: float = 1e-8
) -> Dict[str, float]:
    """Compute risk parity weights using iterative algorithm.

    Each asset contributes equally to total portfolio variance.

    Args:
        assets: Asset names.
        cov: Covariance matrix.
        max_iter: Maximum iterations.
        tol: Convergence tolerance.

    Returns:
        Dict mapping asset to weight.
    """
    n = len(assets)
    w = [1.0 / n] * n  # start equal weight

    for _ in range(max_iter):
        # Portfolio variance
        port_var = sum(w[i] * sum(cov[i][j] * w[j] for j in range(n)) for i in range(n))
        port_vol = math.sqrt(port_var) if port_var > 0 else 1e-10

        # Marginal risk contribution
        mrc = []
        for i in range(n):
            mc = sum(cov[i][j] * w[j] for j in range(n)) / port_vol
            mrc.append(mc)

        # Risk contribution
        rc = [w[i] * mrc[i] for i in range(n)]
        total_rc = sum(rc)
        target_rc = total_rc / n

        # Update weights
        new_w = []
        for i in range(n):
            if mrc[i] > 0:
                new_w.append(w[i] * target_rc / rc[i] if rc[i] > 0 else w[i])
            else:
                new_w.append(w[i])

        # Normalize
        w_sum = sum(new_w)
        new_w = [x / w_sum for x in new_w]

        # Check convergence
        diff = sum((new_w[i] - w[i]) ** 2 for i in range(n))
        w = new_w
        if diff < tol:
            break

    return {assets[i]: round(w[i], 6) for i in range(n)}


def build_risk_parity_portfolio(
    symbols: Optional[List[str]] = None, days: int = 252
) -> Dict:
    """Build a risk parity portfolio from given assets.

    Args:
        symbols: List of ticker symbols. Defaults to classic risk parity universe.
        days: Lookback for covariance estimation.

    Returns:
        Portfolio with weights, risk contributions, and expected metrics.
    """
    if symbols is None:
        symbols = ["SPY", "TLT", "GLD", "DBC", "VNQ"]  # classic all-weather

    returns_dict = {}
    for sym in symbols:
        try:
            returns_dict[sym] = fetch_returns(sym, days)
        except Exception:
            continue

    if len(returns_dict) < 2:
        return {"error": "Need at least 2 assets with data"}

    assets, cov = compute_covariance_matrix(returns_dict)
    weights = risk_parity_weights(assets, cov)

    # Compute portfolio stats
    n = len(assets)
    w = [weights[a] for a in assets]
    port_var = sum(w[i] * sum(cov[i][j] * w[j] for j in range(n)) for i in range(n))
    port_vol = math.sqrt(port_var) * math.sqrt(252)  # annualized

    # Individual vols
    vols = {assets[i]: round(math.sqrt(cov[i][i]) * math.sqrt(252) * 100, 2) for i in range(n)}

    # Risk contributions
    port_vol_daily = math.sqrt(port_var)
    risk_contribs = {}
    for i in range(n):
        mc = sum(cov[i][j] * w[j] for j in range(n))
        rc = w[i] * mc / port_var if port_var > 0 else 1 / n
        risk_contribs[assets[i]] = round(rc * 100, 2)

    return {
        "weights": weights,
        "annualized_vol_pct": round(port_vol * 100, 2),
        "asset_vols_pct": vols,
        "risk_contributions_pct": risk_contribs,
        "assets": assets,
        "lookback_days": days,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }


def compare_equal_weight_vs_risk_parity(symbols: Optional[List[str]] = None) -> Dict:
    """Compare equal-weight vs risk parity allocation.

    Returns:
        Dict with both allocations and risk metrics for comparison.
    """
    rp = build_risk_parity_portfolio(symbols)
    if "error" in rp:
        return rp

    assets = rp["assets"]
    n = len(assets)
    eq_weight = {a: round(1.0 / n, 6) for a in assets}

    return {
        "equal_weight": {"weights": eq_weight},
        "risk_parity": {
            "weights": rp["weights"],
            "vol_pct": rp["annualized_vol_pct"],
            "risk_contributions": rp["risk_contributions_pct"],
        },
        "insight": "Risk parity tilts toward lower-vol assets to equalize risk contribution",
    }
