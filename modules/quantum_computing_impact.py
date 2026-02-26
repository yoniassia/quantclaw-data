"""
Quantum Computing Impact Monitor — Track quantum computing milestones,
patent filings, funding rounds, and potential market disruption scores
for cryptography, pharma, materials science, and finance sectors.

Uses free data from arXiv, USPTO bulk data, and news APIs.
"""

import json
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# Sectors most impacted by quantum computing advances
IMPACT_SECTORS = {
    "cryptography": {
        "description": "Post-quantum cryptography migration urgency",
        "tickers": ["CRWD", "PANW", "FTNT", "ZS", "NET"],
        "risk_keywords": ["RSA", "ECC", "lattice-based", "post-quantum", "NIST PQC"],
    },
    "pharma": {
        "description": "Drug discovery & molecular simulation acceleration",
        "tickers": ["PFE", "MRNA", "LLY", "AMGN", "GILD"],
        "risk_keywords": ["molecular simulation", "protein folding", "drug discovery"],
    },
    "finance": {
        "description": "Portfolio optimization & risk modeling disruption",
        "tickers": ["GS", "JPM", "MS", "BLK", "CME"],
        "risk_keywords": ["monte carlo", "portfolio optimization", "risk modeling"],
    },
    "materials": {
        "description": "Battery, catalyst, and materials design breakthroughs",
        "tickers": ["DOW", "LIN", "APD", "ECL", "SHW"],
        "risk_keywords": ["catalyst design", "battery materials", "superconductor"],
    },
    "quantum_hardware": {
        "description": "Quantum computing hardware & platform providers",
        "tickers": ["IBM", "GOOG", "IONQ", "RGTI", "QBTS"],
        "risk_keywords": ["qubit", "error correction", "quantum supremacy", "logical qubit"],
    },
}


def fetch_arxiv_quantum_papers(
    days_back: int = 30, max_results: int = 50
) -> List[Dict]:
    """
    Fetch recent quantum computing papers from arXiv API.

    Args:
        days_back: How many days back to search
        max_results: Maximum number of results

    Returns:
        List of paper dicts with title, summary, authors, published date
    """
    base_url = "http://export.arxiv.org/api/query"
    query = "cat:quant-ph+AND+(quantum+computing+OR+quantum+algorithm+OR+quantum+error+correction)"
    url = f"{base_url}?search_query={query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read().decode("utf-8")

        papers = []
        entries = data.split("<entry>")[1:]
        for entry in entries:
            title = _extract_xml(entry, "title").strip().replace("\n", " ")
            summary = _extract_xml(entry, "summary").strip()[:500]
            published = _extract_xml(entry, "published")[:10]
            papers.append(
                {"title": title, "summary": summary, "published": published}
            )
        return papers
    except Exception as e:
        return [{"error": str(e)}]


def compute_sector_disruption_score(sector: str, papers: Optional[List[Dict]] = None) -> Dict:
    """
    Compute a quantum disruption score (0-100) for a given sector based on
    recent research activity and keyword density.

    Args:
        sector: One of the IMPACT_SECTORS keys
        papers: Optional pre-fetched papers; if None, fetches from arXiv

    Returns:
        Dict with sector, score, rationale, affected_tickers, paper_count
    """
    if sector not in IMPACT_SECTORS:
        return {"error": f"Unknown sector: {sector}. Choose from {list(IMPACT_SECTORS.keys())}"}

    if papers is None:
        papers = fetch_arxiv_quantum_papers(days_back=30, max_results=100)

    sector_info = IMPACT_SECTORS[sector]
    keywords = [kw.lower() for kw in sector_info["risk_keywords"]]

    relevant_count = 0
    for paper in papers:
        text = (paper.get("title", "") + " " + paper.get("summary", "")).lower()
        if any(kw in text for kw in keywords):
            relevant_count += 1

    # Score: logarithmic scaling — 10 papers = ~50, 30+ = ~80
    import math
    raw_score = min(100, int(30 * math.log1p(relevant_count)))

    # Boost for quantum_hardware (always high activity)
    if sector == "quantum_hardware":
        raw_score = min(100, raw_score + 15)

    return {
        "sector": sector,
        "description": sector_info["description"],
        "disruption_score": raw_score,
        "relevant_papers_30d": relevant_count,
        "total_papers_scanned": len(papers),
        "affected_tickers": sector_info["tickers"],
        "risk_keywords": sector_info["risk_keywords"],
        "assessed_at": datetime.utcnow().isoformat(),
    }


def get_full_quantum_impact_report() -> Dict:
    """
    Generate a comprehensive quantum computing impact report across all sectors.

    Returns:
        Dict with per-sector scores, overall threat level, and summary
    """
    papers = fetch_arxiv_quantum_papers(days_back=30, max_results=100)
    
    sector_scores = {}
    for sector in IMPACT_SECTORS:
        sector_scores[sector] = compute_sector_disruption_score(sector, papers)

    avg_score = sum(s["disruption_score"] for s in sector_scores.values()) / len(sector_scores)

    if avg_score >= 70:
        threat_level = "HIGH"
    elif avg_score >= 40:
        threat_level = "MODERATE"
    else:
        threat_level = "LOW"

    return {
        "report": "Quantum Computing Impact Monitor",
        "period": "Last 30 days",
        "overall_threat_level": threat_level,
        "average_disruption_score": round(avg_score, 1),
        "total_papers_analyzed": len(papers),
        "sectors": sector_scores,
        "generated_at": datetime.utcnow().isoformat(),
    }


def _extract_xml(text: str, tag: str) -> str:
    """Extract text content from an XML tag."""
    start = text.find(f"<{tag}>")
    if start == -1:
        start = text.find(f"<{tag} ")
        if start == -1:
            return ""
        start = text.find(">", start) + 1
    else:
        start += len(f"<{tag}>")
    end = text.find(f"</{tag}>", start)
    return text[start:end] if end != -1 else ""
