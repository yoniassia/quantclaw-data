"""
Longevity & Biotech Breakthrough Tracker — Monitor anti-aging research, clinical trials,
biotech IPOs, and key longevity companies/funds.

Tracks companies like Altos Labs, Calico, Unity Biotech, clinical trial progress,
and FDA approvals in the aging/longevity space. Uses free public data sources.
"""

import json
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional


LONGEVITY_COMPANIES = {
    "Altos Labs": {"focus": "Cellular Reprogramming", "stage": "Preclinical", "funding_m": 3000, "founded": 2022, "ticker": None},
    "Calico (Alphabet)": {"focus": "Aging Biology", "stage": "Research", "funding_m": 2500, "founded": 2013, "ticker": "GOOGL"},
    "Unity Biotechnology": {"focus": "Senolytics", "stage": "Phase 2", "funding_m": 400, "founded": 2011, "ticker": "UBX"},
    "Insilico Medicine": {"focus": "AI Drug Discovery (aging)", "stage": "Phase 2", "funding_m": 400, "founded": 2014, "ticker": None},
    "BioAge Labs": {"focus": "Aging Biomarkers", "stage": "Phase 2", "funding_m": 200, "founded": 2015, "ticker": "BIOA"},
    "Rejuvenate Bio": {"focus": "Gene Therapy (aging)", "stage": "Preclinical", "funding_m": 50, "founded": 2017, "ticker": None},
    "Turn Biotechnologies": {"focus": "mRNA Epigenetic Reprogramming", "stage": "Preclinical", "funding_m": 60, "founded": 2018, "ticker": None},
    "NewLimit": {"focus": "Epigenetic Reprogramming", "stage": "Preclinical", "funding_m": 40, "founded": 2021, "ticker": None},
    "Retro Biosciences": {"focus": "Autophagy/Plasma/Reprogramming", "stage": "Preclinical", "funding_m": 180, "founded": 2021, "ticker": None},
    "Life Biosciences": {"focus": "Multi-pathway Aging", "stage": "Phase 1", "funding_m": 100, "founded": 2017, "ticker": None},
    "Loyal (for Dogs)": {"focus": "Canine Longevity", "stage": "FDA Review", "funding_m": 125, "founded": 2019, "ticker": None},
    "Hevolution Foundation": {"focus": "Aging Research Grants", "stage": "Funding", "funding_m": 1000, "founded": 2021, "ticker": None},
}

LONGEVITY_APPROACHES = {
    "Senolytics": "Clearing senescent (zombie) cells to reduce inflammation",
    "Cellular Reprogramming": "Using Yamanaka factors to reverse cell aging",
    "Epigenetic Clocks": "Measuring biological age via DNA methylation",
    "NAD+ Boosters": "Restoring cellular energy metabolism (NMN, NR)",
    "Telomere Extension": "Lengthening chromosome caps to delay cell death",
    "Caloric Restriction Mimetics": "Drugs mimicking fasting benefits (rapamycin, metformin)",
    "Parabiosis / Plasma": "Young blood factors for tissue rejuvenation",
    "Gene Therapy": "Direct genetic interventions targeting aging pathways",
    "AI Drug Discovery": "ML-driven identification of anti-aging compounds",
}


def get_longevity_companies(stage_filter: Optional[str] = None) -> List[Dict]:
    """
    Get tracked longevity/biotech companies with funding and stage info.

    Args:
        stage_filter: Optional filter (e.g., 'Phase 2', 'Preclinical')

    Returns:
        List of company dictionaries sorted by funding
    """
    results = []
    for name, info in LONGEVITY_COMPANIES.items():
        if stage_filter and stage_filter.lower() not in info["stage"].lower():
            continue
        results.append({"name": name, **info})
    results.sort(key=lambda x: x["funding_m"], reverse=True)
    return results


def get_longevity_investment_summary() -> Dict:
    """
    Summarize total longevity sector investment and breakdown by approach.

    Returns:
        Dict with total funding, company count, by-stage breakdown
    """
    total = sum(c["funding_m"] for c in LONGEVITY_COMPANIES.values())
    by_stage = {}
    by_focus = {}
    public_tickers = []

    for name, info in LONGEVITY_COMPANIES.items():
        by_stage[info["stage"]] = by_stage.get(info["stage"], 0) + info["funding_m"]
        by_focus[info["focus"]] = by_focus.get(info["focus"], 0) + info["funding_m"]
        if info["ticker"]:
            public_tickers.append({"name": name, "ticker": info["ticker"]})

    return {
        "total_funding_m_usd": total,
        "company_count": len(LONGEVITY_COMPANIES),
        "by_stage": dict(sorted(by_stage.items(), key=lambda x: -x[1])),
        "by_focus_area": dict(sorted(by_focus.items(), key=lambda x: -x[1])),
        "public_tickers": public_tickers,
        "approaches_tracked": len(LONGEVITY_APPROACHES),
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_longevity_approaches() -> Dict[str, str]:
    """
    Get dictionary of major longevity research approaches and descriptions.

    Returns:
        Dict mapping approach name to description
    """
    return LONGEVITY_APPROACHES.copy()


def search_clinical_trials(condition: str = "aging", max_results: int = 10) -> List[Dict]:
    """
    Search ClinicalTrials.gov for longevity/aging-related trials.

    Args:
        condition: Condition to search (default: 'aging')
        max_results: Maximum results to return

    Returns:
        List of clinical trial summaries
    """
    try:
        url = (
            f"https://clinicaltrials.gov/api/v2/studies?"
            f"query.cond={condition}&filter.overallStatus=RECRUITING&pageSize={max_results}&format=json"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            trials = []
            for study in data.get("studies", []):
                proto = study.get("protocolSection", {})
                ident = proto.get("identificationModule", {})
                status_mod = proto.get("statusModule", {})
                trials.append({
                    "nct_id": ident.get("nctId", ""),
                    "title": ident.get("briefTitle", ""),
                    "status": status_mod.get("overallStatus", ""),
                    "start_date": status_mod.get("startDateStruct", {}).get("date", ""),
                    "phase": proto.get("designModule", {}).get("phases", []),
                })
            return trials
    except Exception as e:
        return [{"error": str(e), "note": "ClinicalTrials.gov API may be rate-limited"}]


if __name__ == "__main__":
    summary = get_longevity_investment_summary()
    print(f"Longevity sector: ${summary['total_funding_m_usd']}M across {summary['company_count']} companies")
