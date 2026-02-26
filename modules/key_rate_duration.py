"""Key Rate Duration Analyzer — measure bond price sensitivity to non-parallel yield curve shifts.

Decomposes interest rate risk across specific tenor points (key rates) on the yield
curve. Essential for immunization, ALM, and understanding exposure to curve reshaping
(steepening, flattening, butterfly). Uses FRED for the Treasury yield curve.
"""

from typing import Dict, List, Optional


def fetch_yield_curve() -> Dict[float, float]:
    """Fetch current US Treasury yield curve from FRED.

    Returns:
        Dict mapping tenor (years) to yield (decimal).
    """
    import urllib.request
    import json

    series = {
        0.25: "DTB3", 0.5: "DTB6", 1.0: "DGS1", 2.0: "DGS2",
        3.0: "DGS3", 5.0: "DGS5", 7.0: "DGS7", 10.0: "DGS10",
        20.0: "DGS20", 30.0: "DGS30",
    }
    curve = {}
    for tenor, sid in series.items():
        url = (
            f"https://api.stlouisfed.org/fred/series/observations"
            f"?series_id={sid}&sort_order=desc&limit=5"
            f"&api_key=DEMO_KEY&file_type=json"
        )
        try:
            with urllib.request.urlopen(url, timeout=8) as resp:
                data = json.loads(resp.read())
            for obs in data.get("observations", []):
                if obs["value"] != ".":
                    curve[tenor] = float(obs["value"]) / 100.0
                    break
        except Exception:
            pass

    if not curve:
        curve = {
            0.25: 0.052, 0.5: 0.051, 1.0: 0.048, 2.0: 0.045,
            3.0: 0.043, 5.0: 0.042, 7.0: 0.042, 10.0: 0.043,
            20.0: 0.046, 30.0: 0.047,
        }
    return curve


def interpolate_yield(curve: Dict[float, float], tenor: float) -> float:
    """Linear interpolation on the yield curve."""
    tenors = sorted(curve.keys())
    if tenor <= tenors[0]:
        return curve[tenors[0]]
    if tenor >= tenors[-1]:
        return curve[tenors[-1]]
    for i in range(len(tenors) - 1):
        if tenors[i] <= tenor <= tenors[i + 1]:
            w = (tenor - tenors[i]) / (tenors[i + 1] - tenors[i])
            return curve[tenors[i]] * (1 - w) + curve[tenors[i + 1]] * w
    return curve[tenors[-1]]


def calculate_key_rate_durations(
    face: float = 100.0,
    coupon_rate: float = 0.05,
    maturity_years: float = 10.0,
    freq: int = 2,
    key_rates: Optional[List[float]] = None,
    shift_bps: float = 1.0,
    curve: Optional[Dict[float, float]] = None,
) -> Dict:
    """Calculate key rate durations for a fixed-coupon bond.

    Args:
        face: Face value.
        coupon_rate: Annual coupon rate (decimal).
        maturity_years: Years to maturity.
        freq: Payments per year.
        key_rates: Tenor points to measure. Defaults to standard set.
        shift_bps: Size of shift at each key rate in basis points.
        curve: Yield curve dict. Fetched if None.

    Returns:
        Dict with base_price, total_duration, and per-key-rate sensitivities.
    """
    if curve is None:
        curve = fetch_yield_curve()

    if key_rates is None:
        key_rates = [0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0]
    key_rates = [k for k in key_rates if k <= maturity_years + 1]

    periods = int(maturity_years * freq)
    coupon = face * coupon_rate / freq
    shift = shift_bps / 10000.0

    # Cash flow times
    times = [i / freq for i in range(1, periods + 1)]
    cfs = [coupon + (face if i == periods - 1 else 0.0) for i, _ in enumerate(range(periods))]
    # Fix: last period gets principal
    cfs[-1] = coupon + face

    def _price_with_curve(c: Dict[float, float]) -> float:
        p = 0.0
        for t, cf in zip(times, cfs):
            y = interpolate_yield(c, t)
            p += cf / (1 + y / freq) ** (t * freq)
        return p

    base_price = _price_with_curve(curve)

    krd_results = []
    total_krd = 0.0

    for kr in key_rates:
        # Shift curve at this key rate (triangular perturbation)
        curve_up = dict(curve)
        curve_down = dict(curve)
        sorted_kr = sorted(curve.keys())

        # Find neighbours
        idx = None
        for i, k in enumerate(sorted_kr):
            if abs(k - kr) < 0.01:
                idx = i
                break

        if idx is not None:
            # Triangular: full shift at key rate, zero at neighbours
            prev_kr = sorted_kr[idx - 1] if idx > 0 else None
            next_kr = sorted_kr[idx + 1] if idx < len(sorted_kr) - 1 else None

            for k in sorted_kr:
                bump = 0.0
                if abs(k - kr) < 0.01:
                    bump = shift
                elif prev_kr and prev_kr < k < kr:
                    bump = shift * (k - prev_kr) / (kr - prev_kr)
                elif next_kr and kr < k < next_kr:
                    bump = shift * (next_kr - k) / (next_kr - kr)
                curve_up[k] = curve[k] + bump
                curve_down[k] = curve[k] - bump

        p_up = _price_with_curve(curve_up)
        p_down = _price_with_curve(curve_down)
        krd = (p_down - p_up) / (2 * shift * base_price) if base_price > 0 else 0.0
        total_krd += krd

        krd_results.append({
            "key_rate_years": kr,
            "key_rate_duration": round(krd, 4),
            "pct_of_total": 0.0,  # Filled below
            "price_impact_1bp": round((p_down - p_up) / 2, 4),
        })

    # Fill percentages
    for r in krd_results:
        r["pct_of_total"] = round(r["key_rate_duration"] / total_krd * 100, 1) if total_krd else 0.0

    return {
        "base_price": round(base_price, 4),
        "total_krd": round(total_krd, 4),
        "coupon_rate": coupon_rate,
        "maturity_years": maturity_years,
        "key_rate_durations": krd_results,
        "curve_snapshot": {k: round(v, 4) for k, v in sorted(curve.items())},
    }


def scenario_analysis(
    face: float = 100.0,
    coupon_rate: float = 0.05,
    maturity_years: float = 10.0,
    freq: int = 2,
    scenarios: Optional[Dict[str, Dict[float, float]]] = None,
) -> Dict:
    """Analyse bond price under yield curve scenarios using KRDs.

    Args:
        scenarios: Named scenarios mapping key rate → shift in bps.
            Defaults to parallel, steepener, flattener, butterfly.

    Returns:
        Dict with scenario results.
    """
    if scenarios is None:
        scenarios = {
            "parallel_up_50": {1: 50, 2: 50, 5: 50, 10: 50, 30: 50},
            "steepener": {1: -25, 2: -10, 5: 0, 10: 25, 30: 50},
            "flattener": {1: 50, 2: 25, 5: 0, 10: -10, 30: -25},
            "butterfly": {1: -25, 2: 0, 5: 50, 10: 0, 30: -25},
        }

    krd_data = calculate_key_rate_durations(face, coupon_rate, maturity_years, freq)
    base_price = krd_data["base_price"]
    krds = {r["key_rate_years"]: r["key_rate_duration"] for r in krd_data["key_rate_durations"]}

    results = []
    for name, shifts in scenarios.items():
        est_pct_change = 0.0
        for tenor, bps in shifts.items():
            t = float(tenor)
            # Find closest KRD
            closest = min(krds.keys(), key=lambda k: abs(k - t))
            est_pct_change -= krds[closest] * (bps / 10000.0)

        est_price = base_price * (1 + est_pct_change)
        results.append({
            "scenario": name,
            "estimated_pct_change": round(est_pct_change * 100, 3),
            "estimated_price": round(est_price, 4),
            "estimated_pnl": round(est_price - base_price, 4),
        })

    return {
        "base_price": base_price,
        "scenarios": results,
    }
