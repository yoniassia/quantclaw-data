"""
Longevity & Biotech Breakthrough Tracker — Monitor aging research, longevity
biotech companies, clinical trials, and key therapeutic areas using public data.
Roadmap #393.
"""

import datetime
from typing import Dict, List, Optional

LONGEVITY_COMPANIES = [
    {"name": "Altos Labs", "focus": "cellular_reprogramming", "founded": 2021, "funding_mn": 3000, "stage": "preclinical", "public": False},
    {"name": "Unity Biotechnology", "ticker": "UBX", "focus": "senolytics", "founded": 2011, "funding_mn": 300, "stage": "phase_2", "public": True},
    {"name": "Calico (Alphabet)", "focus": "aging_biology", "founded": 2013, "funding_mn": 2500, "stage": "preclinical", "public": False},
    {"name": "Insilico Medicine", "focus": "ai_drug_discovery", "founded": 2014, "funding_mn": 400, "stage": "phase_2", "public": False},
    {"name": "BioAge Labs", "ticker": "BIOA", "focus": "aging_biomarkers", "founded": 2015, "funding_mn": 200, "stage": "phase_2", "public": True},
    {"name": "Rejuvenate Bio", "focus": "gene_therapy", "founded": 2017, "funding_mn": 50, "stage": "preclinical", "public": False},
    {"name": "Turn Biotechnologies", "focus": "epigenetic_reprogramming", "founded": 2018, "funding_mn": 60, "stage": "preclinical", "public": False},
    {"name": "Loyal for Dogs", "focus": "canine_longevity", "founded": 2019, "funding_mn": 60, "stage": "fda_review", "public": False},
    {"name": "Retro Biosciences", "focus": "autophagy_plasma", "founded": 2021, "funding_mn": 180, "stage": "preclinical", "public": False},
    {"name": "NewLimit", "focus": "epigenetic_reprogramming", "founded": 2021, "funding_mn": 40, "stage": "preclinical", "public": False},
]

THERAPEUTIC_AREAS = [
    {"area": "Senolytics", "description": "Clearing senescent (zombie) cells", "readiness": "phase_2"},
    {"area": "Cellular Reprogramming", "description": "Yamanaka factors to reverse cell aging", "readiness": "preclinical"},
    {"area": "NAD+ Boosters", "description": "NMN/NR supplementation for mitochondria", "readiness": "consumer"},
    {"area": "Rapamycin/mTOR", "description": "mTOR inhibition for longevity", "readiness": "off_label"},
    {"area": "Metformin", "description": "TAME trial for anti-aging", "readiness": "phase_3"},
    {"area": "Gene Therapy", "description": "Telomerase / Follistatin delivery", "readiness": "preclinical"},
    {"area": "Blood Plasma", "description": "Young plasma / plasma dilution", "readiness": "phase_1"},
    {"area": "AI Drug Discovery", "description": "ML-driven target identification", "readiness": "phase_2"},
]


def get_longevity_landscape() -> Dict:
    """Get overview of the longevity biotech sector."""
    total_funding = sum(c["funding_mn"] for c in LONGEVITY_COMPANIES)
    public = [c for c in LONGEVITY_COMPANIES if c.get("public")]
    by_stage = {}
    for c in LONGEVITY_COMPANIES:
        by_stage.setdefault(c["stage"], []).append(c["name"])

    return {
        "total_companies_tracked": len(LONGEVITY_COMPANIES),
        "total_funding_mn_usd": total_funding,
        "public_tickers": [{"name": c["name"], "ticker": c.get("ticker")} for c in public],
        "by_stage": by_stage,
        "therapeutic_areas": THERAPEUTIC_AREAS,
    }


def get_company_detail(company_name: str) -> Optional[Dict]:
    """Get detail on a specific longevity biotech company."""
    for c in LONGEVITY_COMPANIES:
        if c["name"].lower() == company_name.lower():
            return c
    return None


def get_therapeutic_pipeline() -> List[Dict]:
    """Return all therapeutic areas ranked by clinical readiness."""
    order = {"consumer": 0, "off_label": 1, "phase_3": 2, "phase_2": 3, "phase_1": 4, "preclinical": 5}
    return sorted(THERAPEUTIC_AREAS, key=lambda t: order.get(t["readiness"], 99))
