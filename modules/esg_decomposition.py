"""ESG Score Decomposition — breaks down Environmental, Social, and Governance scores.

Aggregates ESG data from free public sources (SEC filings, CDP, sustainability
reports) to provide granular E, S, G sub-scores with industry comparisons.
"""

import json
import urllib.request
from datetime import datetime
from typing import Optional

# ESG category weights and sub-factors
ESG_FRAMEWORK = {
    "environmental": {
        "weight": 0.35,
        "factors": {
            "carbon_emissions": 0.25,
            "energy_efficiency": 0.20,
            "water_management": 0.15,
            "waste_reduction": 0.15,
            "biodiversity": 0.10,
            "climate_risk_mgmt": 0.15,
        },
    },
    "social": {
        "weight": 0.30,
        "factors": {
            "employee_safety": 0.20,
            "diversity_inclusion": 0.20,
            "labor_practices": 0.15,
            "community_impact": 0.15,
            "data_privacy": 0.15,
            "supply_chain_labor": 0.15,
        },
    },
    "governance": {
        "weight": 0.35,
        "factors": {
            "board_independence": 0.20,
            "executive_compensation": 0.15,
            "shareholder_rights": 0.15,
            "audit_quality": 0.15,
            "anti_corruption": 0.15,
            "transparency": 0.20,
        },
    },
}

# Industry benchmarks (median scores out of 100)
INDUSTRY_BENCHMARKS = {
    "technology": {"E": 62, "S": 68, "G": 72},
    "financials": {"E": 55, "S": 60, "G": 70},
    "energy": {"E": 40, "S": 55, "G": 65},
    "healthcare": {"E": 58, "S": 72, "G": 68},
    "consumer_discretionary": {"E": 50, "S": 58, "G": 62},
    "industrials": {"E": 48, "S": 56, "G": 64},
    "materials": {"E": 42, "S": 54, "G": 60},
    "utilities": {"E": 52, "S": 60, "G": 66},
    "real_estate": {"E": 56, "S": 58, "G": 64},
    "default": {"E": 50, "S": 58, "G": 65},
}


def get_esg_framework() -> dict:
    """Return the full ESG scoring framework with weights and sub-factors.

    Returns:
        Dict describing the E, S, G pillars, their weights, and sub-factor breakdowns.
    """
    return {
        "framework": ESG_FRAMEWORK,
        "total_pillars": 3,
        "total_factors": sum(len(p["factors"]) for p in ESG_FRAMEWORK.values()),
        "methodology": "Weighted multi-factor scoring (0-100 per factor, industry-relative)",
    }


def compute_esg_score(
    factor_scores: dict[str, dict[str, float]],
    industry: str = "default",
) -> dict:
    """Compute composite ESG score from granular factor inputs.

    Args:
        factor_scores: Nested dict like {"environmental": {"carbon_emissions": 72, ...}, ...}
        industry: Industry key for benchmark comparison.

    Returns:
        Dict with pillar scores, composite score, industry comparison, grade.
    """
    pillar_scores = {}
    for pillar, config in ESG_FRAMEWORK.items():
        factors = config["factors"]
        input_factors = factor_scores.get(pillar, {})
        weighted_sum = 0
        weight_sum = 0
        factor_detail = {}
        for factor_name, factor_weight in factors.items():
            score = input_factors.get(factor_name)
            if score is not None:
                weighted_sum += score * factor_weight
                weight_sum += factor_weight
                factor_detail[factor_name] = {"score": score, "weight": factor_weight}
            else:
                factor_detail[factor_name] = {"score": None, "weight": factor_weight}
        pillar_score = round(weighted_sum / weight_sum, 1) if weight_sum > 0 else None
        pillar_scores[pillar] = {
            "score": pillar_score,
            "weight": config["weight"],
            "factors": factor_detail,
        }

    # Composite
    composite = 0
    comp_weight = 0
    for pillar, data in pillar_scores.items():
        if data["score"] is not None:
            composite += data["score"] * data["weight"]
            comp_weight += data["weight"]
    composite_score = round(composite / comp_weight, 1) if comp_weight > 0 else None

    # Industry comparison
    bench = INDUSTRY_BENCHMARKS.get(industry, INDUSTRY_BENCHMARKS["default"])
    e_score = pillar_scores.get("environmental", {}).get("score")
    s_score = pillar_scores.get("social", {}).get("score")
    g_score = pillar_scores.get("governance", {}).get("score")

    industry_comparison = {
        "industry": industry,
        "vs_E_benchmark": round(e_score - bench["E"], 1) if e_score else None,
        "vs_S_benchmark": round(s_score - bench["S"], 1) if s_score else None,
        "vs_G_benchmark": round(g_score - bench["G"], 1) if g_score else None,
    }

    grade = _score_to_grade(composite_score) if composite_score else "N/A"

    return {
        "composite_score": composite_score,
        "grade": grade,
        "pillar_scores": pillar_scores,
        "industry_comparison": industry_comparison,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def fetch_sec_esg_data(ticker: str) -> dict:
    """Fetch ESG-relevant data from SEC EDGAR for a given ticker.

    Args:
        ticker: Stock ticker (e.g., 'AAPL').

    Returns:
        Dict with available ESG data points from SEC filings.
    """
    # Search SEC EDGAR for company CIK
    url = f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom&startdt=2024-01-01&forms=10-K,DEF+14A"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw admin@moneyclaw.com"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        filings = data.get("hits", {}).get("hits", [])
        return {
            "ticker": ticker,
            "filings_found": len(filings),
            "source": "SEC EDGAR",
            "note": "Parse 10-K for environmental disclosures, DEF 14A for governance data",
            "latest_filings": [
                {"form": f.get("_source", {}).get("form_type", ""), "date": f.get("_source", {}).get("file_date", "")}
                for f in filings[:5]
            ],
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


def _score_to_grade(score: Optional[float]) -> str:
    if score is None:
        return "N/A"
    if score >= 80:
        return "AAA"
    elif score >= 70:
        return "AA"
    elif score >= 60:
        return "A"
    elif score >= 50:
        return "BBB"
    elif score >= 40:
        return "BB"
    elif score >= 30:
        return "B"
    else:
        return "CCC"
