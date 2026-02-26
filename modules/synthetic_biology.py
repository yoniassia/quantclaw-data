"""
Synthetic Biology Market Monitor (Roadmap #400)

Tracks synthetic biology companies, applications, market growth,
and key developments using public data sources.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional


SYNBIO_COMPANIES = {
    "Ginkgo Bioworks": {
        "ticker": "DNA",
        "market_cap_bn": 1.5,
        "focus": "cell_programming_platform",
        "founded": 2008,
        "platform": "Foundry (automated organism design)",
        "applications": ["pharma", "agriculture", "industrials", "government"],
    },
    "Twist Bioscience": {
        "ticker": "TWST",
        "market_cap_bn": 2.5,
        "focus": "synthetic_dna_manufacturing",
        "founded": 2013,
        "platform": "Silicon-based DNA synthesis",
    },
    "Amyris": {
        "status": "bankrupt_2023",
        "focus": "bio_based_ingredients",
        "lesson": "Scale-up costs exceeded revenue; cautionary tale",
    },
    "Zymergen": {
        "status": "acquired_by_ginkgo_2022",
        "focus": "materials_biology",
    },
    "Moderna": {
        "ticker": "MRNA",
        "market_cap_bn": 35,
        "focus": "mrna_therapeutics",
        "founded": 2010,
        "applications": ["vaccines", "cancer", "rare_diseases"],
    },
    "BioNTech": {
        "ticker": "BNTX",
        "market_cap_bn": 25,
        "focus": "mrna_therapeutics",
        "founded": 2008,
    },
    "Intellia Therapeutics": {
        "ticker": "NTLA",
        "market_cap_bn": 3,
        "focus": "crispr_gene_editing",
        "founded": 2014,
    },
    "CRISPR Therapeutics": {
        "ticker": "CRSP",
        "market_cap_bn": 4,
        "focus": "crispr_gene_editing",
        "founded": 2013,
        "milestone": "First CRISPR therapy approved (Casgevy) Dec 2023",
    },
    "Beam Therapeutics": {
        "ticker": "BEAM",
        "market_cap_bn": 1.5,
        "focus": "base_editing",
        "founded": 2017,
    },
    "Recursion Pharmaceuticals": {
        "ticker": "RXRX",
        "market_cap_bn": 3,
        "focus": "ai_driven_drug_discovery",
        "founded": 2013,
        "platform": "AI + biology platform for drug discovery",
    },
}

SYNBIO_APPLICATIONS = {
    "therapeutics": {
        "market_size_bn_2024": 80,
        "growth_rate_pct": 15,
        "examples": ["mRNA vaccines", "gene therapy", "CRISPR treatments", "cell therapy"],
    },
    "agriculture": {
        "market_size_bn_2024": 12,
        "growth_rate_pct": 12,
        "examples": ["engineered crops", "biopesticides", "nitrogen-fixing microbes"],
    },
    "industrial_biotech": {
        "market_size_bn_2024": 15,
        "growth_rate_pct": 8,
        "examples": ["bio-based materials", "enzymes", "biofuels"],
    },
    "food_tech": {
        "market_size_bn_2024": 5,
        "growth_rate_pct": 20,
        "examples": ["precision fermentation", "cultivated meat", "synthetic flavors"],
    },
    "data_storage": {
        "market_size_bn_2024": 0.1,
        "growth_rate_pct": 50,
        "examples": ["DNA data storage", "biocomputing"],
    },
}


def get_synbio_overview() -> Dict:
    """
    Get comprehensive overview of the synthetic biology market including
    companies, applications, and market sizing.
    """
    public_companies = [
        {"name": k, "ticker": v["ticker"], "market_cap_bn": v.get("market_cap_bn")}
        for k, v in SYNBIO_COMPANIES.items()
        if "ticker" in v
    ]
    total_market = sum(a["market_size_bn_2024"] for a in SYNBIO_APPLICATIONS.values())

    return {
        "total_market_size_bn_2024": round(total_market, 1),
        "projected_market_size_bn_2030": round(total_market * 2.5, 1),
        "public_companies": public_companies,
        "applications": {k: v for k, v in SYNBIO_APPLICATIONS.items()},
        "key_milestones": [
            "2012: CRISPR-Cas9 gene editing discovered",
            "2020: mRNA vaccines for COVID-19",
            "2023: First CRISPR therapy (Casgevy) approved by FDA/MHRA",
            "2024: AI-designed proteins advancing to clinical trials",
        ],
        "as_of": datetime.utcnow().isoformat(),
    }


def get_synbio_company(company_name: str) -> Optional[Dict]:
    """
    Get detailed info on a specific synthetic biology company.
    """
    for name, data in SYNBIO_COMPANIES.items():
        if company_name.lower() in name.lower():
            return {"name": name, **data}
    return None


def synbio_investment_trends() -> Dict:
    """
    Track venture capital and public market investment in synthetic biology.
    """
    return {
        "vc_funding_by_year": [
            {"year": 2019, "funding_bn": 7.5},
            {"year": 2020, "funding_bn": 12.0},
            {"year": 2021, "funding_bn": 22.0},
            {"year": 2022, "funding_bn": 15.0},
            {"year": 2023, "funding_bn": 10.0},
            {"year": 2024, "funding_bn": 11.5},
        ],
        "ipo_tracker": [
            {"company": "Ginkgo Bioworks", "year": 2021, "method": "SPAC", "valuation_bn": 15},
            {"company": "Recursion", "year": 2021, "method": "IPO", "valuation_bn": 3.5},
        ],
        "ma_activity": [
            {"target": "Zymergen", "acquirer": "Ginkgo Bioworks", "year": 2022},
            {"target": "Seagen", "acquirer": "Pfizer", "year": 2023, "value_bn": 43},
        ],
        "trend": "Post-2021 funding correction, but AI+bio convergence driving renewed interest in 2024-25",
    }


def crispr_therapy_pipeline() -> Dict:
    """
    Track CRISPR and gene editing therapy pipeline and approvals.
    """
    return {
        "approved_therapies": [
            {
                "name": "Casgevy (exagamglogene autotemcel)",
                "companies": ["CRISPR Therapeutics", "Vertex"],
                "indication": "Sickle cell disease, beta-thalassemia",
                "approved": "Dec 2023",
                "price_usd": 2_200_000,
            },
        ],
        "phase_3_trials": [
            {"name": "CTX001 expansion", "company": "CRISPR Therapeutics", "indication": "additional blood disorders"},
            {"name": "NTLA-2001", "company": "Intellia", "indication": "transthyretin amyloidosis"},
        ],
        "key_challenges": [
            "Delivery mechanisms (getting CRISPR to target cells in vivo)",
            "Off-target editing effects",
            "Manufacturing scale and cost ($2M+ per treatment)",
            "Regulatory frameworks for germline editing",
            "Ethical considerations for enhancement applications",
        ],
    }
