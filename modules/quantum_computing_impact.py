"""
Quantum Computing Impact Monitor (Roadmap #388)

Tracks quantum computing progress, investment, and market impact on
cryptography, pharma, materials science, and finance sectors.
Uses free data from arXiv, patent databases, and public company filings.
"""

import json
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# Key quantum computing companies and their focus areas
QUANTUM_COMPANIES = {
    "IONQ": {"name": "IonQ", "type": "trapped_ion", "ticker": "IONQ", "sector": "pure_play"},
    "RGTI": {"name": "Rigetti Computing", "type": "superconducting", "ticker": "RGTI", "sector": "pure_play"},
    "QBTS": {"name": "D-Wave Quantum", "type": "annealing", "ticker": "QBTS", "sector": "pure_play"},
    "IBM": {"name": "IBM Quantum", "type": "superconducting", "ticker": "IBM", "sector": "diversified"},
    "GOOG": {"name": "Google Quantum AI", "type": "superconducting", "ticker": "GOOG", "sector": "diversified"},
    "MSFT": {"name": "Microsoft Azure Quantum", "type": "topological", "ticker": "MSFT", "sector": "diversified"},
}

# Sectors impacted by quantum computing
IMPACT_SECTORS = {
    "cryptography": {
        "risk_level": "HIGH",
        "timeline": "5-15 years",
        "description": "RSA/ECC broken by Shor's algorithm on fault-tolerant QC",
        "affected_tickers": ["CRWD", "PANW", "ZS", "FTNT"],
    },
    "drug_discovery": {
        "risk_level": "MEDIUM",
        "timeline": "3-10 years",
        "description": "Molecular simulation for drug candidates",
        "affected_tickers": ["PFE", "MRNA", "LLY", "ABBV"],
    },
    "materials_science": {
        "risk_level": "MEDIUM",
        "timeline": "5-15 years",
        "description": "Battery, catalyst, and superconductor design",
        "affected_tickers": ["ALB", "LAC", "MP"],
    },
    "finance": {
        "risk_level": "MEDIUM",
        "timeline": "2-8 years",
        "description": "Portfolio optimization, risk modeling, Monte Carlo",
        "affected_tickers": ["GS", "JPM", "MS", "BLK"],
    },
    "logistics": {
        "risk_level": "LOW",
        "timeline": "5-15 years",
        "description": "Combinatorial optimization (routing, scheduling)",
        "affected_tickers": ["UPS", "FDX", "UBER"],
    },
}

# Quantum milestones tracker
MILESTONES = [
    {"date": "2019-10-23", "event": "Google quantum supremacy (Sycamore, 53 qubits)", "impact": "HIGH"},
    {"date": "2021-11-16", "event": "IBM Eagle 127-qubit processor", "impact": "MEDIUM"},
    {"date": "2022-11-09", "event": "IBM Osprey 433-qubit processor", "impact": "MEDIUM"},
    {"date": "2023-12-04", "event": "IBM Condor 1,121-qubit processor", "impact": "HIGH"},
    {"date": "2023-12-06", "event": "Google Willow chip - below error correction threshold", "impact": "HIGH"},
    {"date": "2024-08-01", "event": "Microsoft topological qubit breakthrough claim", "impact": "MEDIUM"},
    {"date": "2025-01-01", "event": "Multiple companies >1000 logical qubits target", "impact": "HIGH"},
]


def search_arxiv_quantum(query: str = "quantum computing", max_results: int = 10) -> Dict:
    """
    Search arXiv for recent quantum computing papers to track research velocity.

    Args:
        query: Search query for arXiv
        max_results: Number of results to return

    Returns:
        Dict with paper count, titles, and research trend indicators
    """
    encoded_query = urllib.request.quote(f"all:{query}")
    url = (
        f"http://export.arxiv.org/api/query"
        f"?search_query={encoded_query}"
        f"&sortBy=submittedDate&sortOrder=descending"
        f"&max_results={max_results}"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode()

        # Simple XML parsing for titles and dates
        papers = []
        entries = content.split("<entry>")[1:]  # skip header
        for entry in entries[:max_results]:
            title_start = entry.find("<title>") + 7
            title_end = entry.find("</title>")
            title = entry[title_start:title_end].strip().replace("\n", " ")

            pub_start = entry.find("<published>") + 11
            pub_end = entry.find("</published>")
            published = entry[pub_start:pub_end].strip()

            papers.append({"title": title, "published": published})

        return {
            "query": query,
            "paper_count": len(papers),
            "papers": papers,
            "source": "arXiv",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"query": query, "error": str(e), "papers": []}


def get_quantum_readiness_score() -> Dict:
    """
    Calculate a quantum readiness/threat score across sectors.
    Combines qubit progress, error rates, and sector vulnerability.

    Returns:
        Dict with sector-by-sector quantum impact assessment
    """
    # Current estimated state of quantum computing
    current_state = {
        "max_physical_qubits": 1121,  # IBM Condor
        "best_error_rate": 0.001,  # approximate best 2-qubit gate error
        "logical_qubits_achieved": 12,  # approximate
        "qubits_needed_for_rsa2048": 4000,  # logical qubits estimate
        "years_to_cryptographic_threat": "7-15",
    }

    sector_assessments = {}
    for sector, info in IMPACT_SECTORS.items():
        # Simple threat proximity calculation
        timeline_years = int(info["timeline"].split("-")[0])
        proximity_score = max(0, 100 - (timeline_years * 10))

        sector_assessments[sector] = {
            "sector": sector,
            "risk_level": info["risk_level"],
            "timeline": info["timeline"],
            "proximity_score": proximity_score,
            "description": info["description"],
            "affected_tickers": info["affected_tickers"],
            "recommendation": (
                "MONITOR CLOSELY" if proximity_score >= 50
                else "TRACK DEVELOPMENTS" if proximity_score >= 20
                else "LONG-TERM WATCH"
            ),
        }

    return {
        "current_state": current_state,
        "sector_assessments": sector_assessments,
        "milestones": MILESTONES[-5:],
        "quantum_pure_plays": list(QUANTUM_COMPANIES.keys()),
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_quantum_investment_landscape() -> Dict:
    """
    Map the quantum computing investment landscape including
    public companies, key metrics, and competitive positioning.

    Returns:
        Dict with company profiles and market overview
    """
    landscape = {
        "pure_play_public": [],
        "diversified_players": [],
        "total_companies_tracked": len(QUANTUM_COMPANIES),
    }

    for ticker, info in QUANTUM_COMPANIES.items():
        entry = {
            "ticker": ticker,
            "name": info["name"],
            "qubit_type": info["type"],
        }
        if info["sector"] == "pure_play":
            landscape["pure_play_public"].append(entry)
        else:
            landscape["diversified_players"].append(entry)

    landscape["investment_themes"] = [
        "Error correction breakthroughs → pure play rally",
        "Post-quantum cryptography mandate → cybersecurity beneficiaries",
        "Quantum-as-a-Service (QaaS) → cloud providers",
        "Quantum-resistant blockchain → crypto infrastructure",
        "Drug discovery acceleration → biotech partnerships",
    ]

    landscape["timestamp"] = datetime.utcnow().isoformat()
    return landscape


def track_research_velocity(topics: Optional[List[str]] = None) -> Dict:
    """
    Track research paper velocity across quantum computing sub-fields.

    Args:
        topics: List of sub-topics to track. Defaults to key areas.

    Returns:
        Dict with paper counts per topic indicating research momentum
    """
    if topics is None:
        topics = [
            "quantum error correction",
            "quantum machine learning",
            "quantum cryptography",
            "quantum simulation chemistry",
            "quantum optimization",
        ]

    results = {}
    for topic in topics:
        data = search_arxiv_quantum(topic, max_results=5)
        results[topic] = {
            "recent_papers": data.get("paper_count", 0),
            "latest_title": data["papers"][0]["title"] if data.get("papers") else None,
        }

    return {
        "research_velocity": results,
        "hottest_area": max(results, key=lambda k: results[k]["recent_papers"]) if results else None,
        "timestamp": datetime.utcnow().isoformat(),
    }
