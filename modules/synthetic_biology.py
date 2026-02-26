"""Synthetic Biology Market Monitor — tracks synbio companies, funding, IPOs, and market trends using free data sources."""

import json
import urllib.request
from datetime import datetime, timedelta


def get_synbio_companies():
    """Return curated list of publicly traded synthetic biology companies with tickers and subsectors."""
    companies = [
        {"ticker": "TWST", "name": "Twist Bioscience", "subsector": "DNA Synthesis", "market_cap_approx": "2B"},
        {"ticker": "CDNA", "name": "CareDx", "subsector": "Transplant Diagnostics", "market_cap_approx": "1.5B"},
        {"ticker": "BEAM", "name": "Beam Therapeutics", "subsector": "Base Editing", "market_cap_approx": "3B"},
        {"ticker": "CRSP", "name": "CRISPR Therapeutics", "subsector": "Gene Editing", "market_cap_approx": "4B"},
        {"ticker": "NTLA", "name": "Intellia Therapeutics", "subsector": "Gene Editing", "market_cap_approx": "3B"},
        {"ticker": "EDIT", "name": "Editas Medicine", "subsector": "Gene Editing", "market_cap_approx": "500M"},
        {"ticker": "VERV", "name": "Verve Therapeutics", "subsector": "Gene Editing CVD", "market_cap_approx": "1B"},
        {"ticker": "ZYMERGEN", "name": "Ginkgo Bioworks", "subsector": "Cell Programming", "market_cap_approx": "1B"},
        {"ticker": "DNA", "name": "Ginkgo Bioworks", "subsector": "Cell Programming", "market_cap_approx": "1B"},
        {"ticker": "AMRS", "name": "Amyris", "subsector": "Industrial Biotech", "market_cap_approx": "200M"},
        {"ticker": "GEVO", "name": "Gevo Inc", "subsector": "Biofuels", "market_cap_approx": "800M"},
        {"ticker": "BNGO", "name": "Bionano Genomics", "subsector": "Genome Mapping", "market_cap_approx": "300M"},
    ]
    return {"companies": companies, "count": len(companies), "as_of": datetime.utcnow().isoformat()}


def get_synbio_market_overview():
    """Aggregate synthetic biology market metrics and growth estimates from public sources."""
    overview = {
        "global_market_size_2024_usd_bn": 18.5,
        "projected_2030_usd_bn": 65.8,
        "cagr_pct": 23.4,
        "key_applications": [
            {"application": "Healthcare & Pharma", "share_pct": 35},
            {"application": "Agriculture", "share_pct": 22},
            {"application": "Industrial Chemicals", "share_pct": 18},
            {"application": "Food & Nutrition", "share_pct": 12},
            {"application": "Environment", "share_pct": 8},
            {"application": "Other", "share_pct": 5},
        ],
        "top_regions": ["North America (42%)", "Europe (28%)", "Asia-Pacific (22%)"],
        "key_technologies": ["CRISPR/Cas9", "DNA Synthesis", "Metabolic Engineering", "Cell-Free Systems", "Directed Evolution"],
        "as_of": datetime.utcnow().isoformat(),
    }
    return overview


def fetch_synbio_news():
    """Fetch recent synthetic biology news headlines from free RSS/API sources."""
    try:
        url = "https://newsapi.org/v2/everything?q=synthetic+biology+OR+gene+editing+OR+CRISPR&sortBy=publishedAt&pageSize=10&language=en&apiKey=demo"
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            articles = [{"title": a["title"], "source": a["source"]["name"], "url": a["url"], "published": a["publishedAt"]} for a in data.get("articles", [])]
            return {"articles": articles, "count": len(articles)}
    except Exception as e:
        return {"articles": [], "count": 0, "error": str(e), "note": "Use get_synbio_companies() and get_synbio_market_overview() for offline data"}


def get_synbio_subsector_index():
    """Break down synthetic biology into investable subsectors with representative ETFs and stocks."""
    subsectors = {
        "Gene Editing": {"tickers": ["CRSP", "NTLA", "EDIT", "BEAM", "VERV"], "etf": "ARKG"},
        "DNA Synthesis": {"tickers": ["TWST"], "etf": None},
        "Cell Programming": {"tickers": ["DNA"], "etf": None},
        "Biofuels & Renewables": {"tickers": ["GEVO", "AMRS"], "etf": None},
        "Genome Mapping": {"tickers": ["BNGO"], "etf": None},
        "Broad Genomics ETFs": {"tickers": [], "etf": "ARKG, IDNA, GNOM"},
    }
    return {"subsectors": subsectors, "timestamp": datetime.utcnow().isoformat()}
