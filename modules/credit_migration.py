"""
Credit Migration Matrix — Build and analyze credit rating transition
matrices using historical default studies. Model rating drift, estimate
downgrade/upgrade probabilities, and compute expected loss from migration.

Based on Moody's/S&P historical transition rate methodology.
Free data: historical averages from published rating agency studies.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# 1-year average transition probabilities (%) — based on S&P historical averages
# Rows = from rating, Columns = to rating
RATINGS = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "D"]

# Historical average 1-year transition matrix (S&P, ~1981-2023 averages)
TRANSITION_MATRIX_1Y = {
    "AAA": {"AAA": 87.44, "AA": 10.54, "A": 1.56, "BBB": 0.26, "BB": 0.08, "B": 0.04, "CCC": 0.02, "D": 0.06},
    "AA":  {"AAA": 0.52,  "AA": 87.12, "A": 10.29, "BBB": 1.21, "BB": 0.38, "B": 0.21, "CCC": 0.09, "D": 0.18},
    "A":   {"AAA": 0.04,  "AA": 1.84,  "A": 89.24, "BBB": 6.82, "BB": 1.15, "B": 0.48, "CCC": 0.14, "D": 0.29},
    "BBB": {"AAA": 0.01,  "AA": 0.12,  "A": 3.41,  "BBB": 87.61, "BB": 5.72, "B": 1.83, "CCC": 0.52, "D": 0.78},
    "BB":  {"AAA": 0.01,  "AA": 0.04,  "A": 0.18,  "BBB": 5.14, "BB": 78.82, "B": 9.63, "CCC": 3.14, "D": 3.04},
    "B":   {"AAA": 0.00,  "AA": 0.02,  "A": 0.08,  "BBB": 0.24, "BB": 5.41, "B": 76.33, "CCC": 9.46, "D": 8.46},
    "CCC": {"AAA": 0.00,  "AA": 0.00,  "A": 0.10,  "BBB": 0.28, "BB": 0.86, "B": 9.52, "CCC": 54.12, "D": 35.12},
}

# Average recovery rates by seniority
RECOVERY_RATES = {
    "senior_secured": 0.52,
    "senior_unsecured": 0.37,
    "subordinated": 0.24,
    "junior_subordinated": 0.12,
}


def get_transition_probability(from_rating: str, to_rating: str, years: int = 1) -> Dict:
    """
    Get the probability of transitioning from one rating to another.

    Args:
        from_rating: Starting credit rating (e.g., 'BBB')
        to_rating: Ending credit rating (e.g., 'BB')
        years: Time horizon (1-5, multi-year via matrix power)

    Returns:
        Dict with transition probability and context
    """
    from_rating = from_rating.upper()
    to_rating = to_rating.upper()

    if from_rating not in TRANSITION_MATRIX_1Y:
        return {"error": f"Invalid from_rating. Choose from: {list(TRANSITION_MATRIX_1Y.keys())}"}
    if to_rating not in RATINGS:
        return {"error": f"Invalid to_rating. Choose from: {RATINGS}"}

    if years == 1:
        prob = TRANSITION_MATRIX_1Y[from_rating].get(to_rating, 0.0)
    else:
        # Multi-year: matrix exponentiation
        matrix = _matrix_power(years)
        from_idx = RATINGS.index(from_rating)
        to_idx = RATINGS.index(to_rating)
        prob = matrix[from_idx][to_idx]

    # Classify the transition
    from_idx = RATINGS.index(from_rating)
    to_idx = RATINGS.index(to_rating)
    if to_idx > from_idx:
        direction = "DOWNGRADE"
    elif to_idx < from_idx:
        direction = "UPGRADE"
    else:
        direction = "STABLE"

    return {
        "from_rating": from_rating,
        "to_rating": to_rating,
        "horizon_years": years,
        "probability_pct": round(prob, 4),
        "direction": direction,
        "notches": to_idx - from_idx,
    }


def get_full_migration_matrix(years: int = 1) -> Dict:
    """
    Return the complete credit migration matrix for a given horizon.

    Args:
        years: Time horizon (1-5 years)

    Returns:
        Dict with full matrix and summary statistics
    """
    if years == 1:
        matrix_dict = TRANSITION_MATRIX_1Y
    else:
        matrix = _matrix_power(years)
        matrix_dict = {}
        for i, from_r in enumerate(RATINGS[:-1]):  # Exclude D (absorbing state)
            matrix_dict[from_r] = {
                to_r: round(matrix[i][j], 4) for j, to_r in enumerate(RATINGS)
            }

    # Compute default probabilities
    default_probs = {
        rating: round(row.get("D", 0), 4)
        for rating, row in matrix_dict.items()
    }

    return {
        "horizon_years": years,
        "ratings": RATINGS,
        "matrix": matrix_dict,
        "default_probabilities": default_probs,
        "source": "S&P Historical Averages (1981-2023)",
        "generated_at": datetime.utcnow().isoformat(),
    }


def estimate_portfolio_migration_loss(
    holdings: List[Dict],
    years: int = 1,
    seniority: str = "senior_unsecured"
) -> Dict:
    """
    Estimate expected loss from credit migration for a bond portfolio.

    Args:
        holdings: List of dicts with 'rating', 'notional', and optional 'spread_bps'
                  e.g., [{"rating": "BBB", "notional": 1000000, "spread_bps": 150}]
        years: Time horizon
        seniority: Bond seniority for recovery rate

    Returns:
        Dict with per-holding and total expected migration loss
    """
    recovery = RECOVERY_RATES.get(seniority, 0.37)
    lgd = 1 - recovery

    results = []
    total_el = 0

    for h in holdings:
        rating = h.get("rating", "BBB").upper()
        notional = h.get("notional", 0)

        if rating not in TRANSITION_MATRIX_1Y:
            results.append({"rating": rating, "error": "Invalid rating"})
            continue

        # Default probability
        prob = get_transition_probability(rating, "D", years)
        pd = prob["probability_pct"] / 100

        # Expected loss = PD * LGD * Notional
        el = pd * lgd * notional

        # Downgrade probability (any downgrade)
        from_idx = RATINGS.index(rating)
        downgrade_prob = sum(
            get_transition_probability(rating, RATINGS[j], years)["probability_pct"]
            for j in range(from_idx + 1, len(RATINGS))
        )

        results.append({
            "rating": rating,
            "notional": notional,
            "default_prob_pct": round(pd * 100, 4),
            "downgrade_prob_pct": round(downgrade_prob, 2),
            "lgd": round(lgd, 2),
            "expected_loss": round(el, 2),
        })
        total_el += el

    total_notional = sum(h.get("notional", 0) for h in holdings)

    return {
        "holdings": results,
        "total_expected_loss": round(total_el, 2),
        "total_notional": total_notional,
        "portfolio_el_pct": round(total_el / total_notional * 100, 4) if total_notional else 0,
        "recovery_rate": recovery,
        "seniority": seniority,
        "horizon_years": years,
    }


def _matrix_power(years: int) -> List[List[float]]:
    """Compute matrix^years via repeated multiplication."""
    n = len(RATINGS)
    # Convert dict to 2D list
    mat = []
    for from_r in RATINGS:
        if from_r in TRANSITION_MATRIX_1Y:
            row = [TRANSITION_MATRIX_1Y[from_r].get(to_r, 0) / 100 for to_r in RATINGS]
        else:
            # D is absorbing state
            row = [0.0] * n
            row[RATINGS.index("D")] = 1.0
        mat.append(row)

    result = [row[:] for row in mat]
    for _ in range(years - 1):
        new = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    new[i][j] += result[i][k] * mat[k][j]
        result = new

    # Convert back to percentages
    return [[val * 100 for val in row] for row in result]
