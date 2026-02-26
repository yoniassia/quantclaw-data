"""
Decentralized Science (DeSci) Tracker (Roadmap #398)

Monitors decentralized science projects, funding DAOs, IP-NFTs,
and open research initiatives using public blockchain and web data.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional


DESCI_PROJECTS = {
    "VitaDAO": {
        "focus": "longevity_research",
        "token": "VITA",
        "blockchain": "Ethereum",
        "treasury_usd": 4_000_000,
        "projects_funded": 24,
        "governance": "token_weighted",
        "url": "https://vitadao.com",
    },
    "Molecule": {
        "focus": "ip_nft_infrastructure",
        "description": "IP-NFT framework for on-chain IP",
        "blockchain": "Ethereum",
        "ip_nfts_minted": 30,
        "url": "https://molecule.to",
    },
    "LabDAO": {
        "focus": "open_compute_biotech",
        "description": "Decentralized wet lab and compute services",
        "blockchain": "Ethereum",
        "url": "https://labdao.xyz",
    },
    "ResearchHub": {
        "focus": "open_access_publishing",
        "token": "RSC",
        "description": "Incentivized open science publishing",
        "papers_hosted": 2_000_000,
        "url": "https://researchhub.com",
    },
    "DeSci Labs": {
        "focus": "research_publishing",
        "product": "DeSci Nodes",
        "description": "Verifiable research object publishing",
        "url": "https://desci.com",
    },
    "AthenaDAO": {
        "focus": "womens_health_research",
        "token": "ATH",
        "blockchain": "Ethereum",
        "governance": "token_weighted",
    },
    "PsyDAO": {
        "focus": "psychedelics_research",
        "blockchain": "Ethereum",
        "governance": "token_weighted",
    },
    "HairDAO": {
        "focus": "hair_loss_research",
        "token": "HAIR",
        "blockchain": "Ethereum",
    },
    "GenomesDAO": {
        "focus": "genomic_data_ownership",
        "token": "GENE",
        "blockchain": "Ethereum",
        "description": "User-owned genomic data vault",
    },
    "Bio Protocol": {
        "focus": "biotech_dao_launchpad",
        "token": "BIO",
        "blockchain": "Ethereum",
        "description": "Launchpad for biotech DAOs",
        "backed_by": ["Binance Labs", "a16z crypto"],
    },
}

DESCI_CATEGORIES = {
    "funding_daos": "DAOs that fund scientific research via token governance",
    "ip_nfts": "Intellectual property represented as NFTs for licensing/trading",
    "open_publishing": "Decentralized and incentivized research publishing",
    "data_ownership": "Platforms for user-owned scientific/health data",
    "compute_infrastructure": "Decentralized lab/compute services for researchers",
}


def get_desci_landscape() -> Dict:
    """
    Get comprehensive overview of the DeSci ecosystem including
    all tracked projects, categories, and aggregate metrics.
    """
    by_focus = {}
    for name, proj in DESCI_PROJECTS.items():
        focus = proj.get("focus", "other")
        by_focus.setdefault(focus, []).append(name)

    tokens = [
        {"project": k, "token": v["token"]}
        for k, v in DESCI_PROJECTS.items()
        if "token" in v
    ]

    return {
        "total_projects": len(DESCI_PROJECTS),
        "categories": DESCI_CATEGORIES,
        "projects_by_focus": by_focus,
        "tokens": tokens,
        "market_context": {
            "trend": "Growing interest post-2022 as Web3 meets academic frustration",
            "key_narratives": [
                "IP-NFTs enable tradeable intellectual property",
                "Token-gated funding bypasses traditional grants",
                "Open access publishing with economic incentives",
                "Patient/citizen-owned health data",
            ],
        },
        "as_of": datetime.utcnow().isoformat(),
    }


def get_desci_project(project_name: str) -> Optional[Dict]:
    """
    Get detailed info on a specific DeSci project by name (case-insensitive partial match).
    """
    for name, data in DESCI_PROJECTS.items():
        if project_name.lower() in name.lower():
            return {"name": name, **data}
    return None


def desci_funding_analysis() -> Dict:
    """
    Analyze DeSci funding flows, treasury sizes, and research output.
    """
    treasuries = [
        {"project": k, "treasury_usd": v["treasury_usd"]}
        for k, v in DESCI_PROJECTS.items()
        if "treasury_usd" in v
    ]
    funded_projects = sum(
        v.get("projects_funded", 0) for v in DESCI_PROJECTS.values()
    )

    return {
        "tracked_treasuries": treasuries,
        "total_research_projects_funded": funded_projects,
        "funding_mechanisms": [
            "Token sales and treasury management",
            "IP-NFT fractionalization (e.g., VITA-FAST)",
            "Quadratic funding rounds",
            "Retroactive public goods funding",
            "Direct token-gated grants",
        ],
        "comparison_to_traditional": {
            "nih_annual_budget_bn": 47,
            "nsf_annual_budget_bn": 9.9,
            "desci_total_deployed_est_mn": 50,
            "note": "DeSci is <0.1% of traditional funding but growing rapidly in niche areas",
        },
    }


def desci_vs_traditional_science() -> Dict:
    """
    Compare DeSci approach to traditional academic publishing and funding.
    """
    return {
        "traditional_pain_points": [
            "Average 2-3 year grant application cycle",
            "Elsevier/Springer paywalls ($30-50 per paper access)",
            "Peer review takes 6-18 months",
            "Reproducibility crisis (>50% of studies fail replication)",
            "IP owned by institutions, not researchers",
        ],
        "desci_solutions": [
            "DAO governance for faster funding decisions (weeks not years)",
            "Open access by default with token incentives",
            "Transparent on-chain peer review",
            "Verifiable research objects (DeSci Nodes)",
            "IP-NFTs let researchers retain and monetize IP",
        ],
        "challenges": [
            "Regulatory uncertainty around token-funded research",
            "Quality control without traditional peer review",
            "Token price volatility affecting treasury stability",
            "Limited adoption by mainstream researchers",
            "Legal enforceability of IP-NFTs across jurisdictions",
        ],
    }
