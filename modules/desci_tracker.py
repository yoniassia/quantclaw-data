"""Decentralized Science (DeSci) Tracker — monitors DeSci protocols, tokens, funding, and research DAOs."""

import json
import urllib.request
from datetime import datetime


def get_desci_protocols():
    """Return major DeSci protocols and platforms with key metrics."""
    protocols = [
        {"name": "VitaDAO", "token": "VITA", "focus": "Longevity Research", "treasury_usd_m": 15, "projects_funded": 25, "chain": "Ethereum"},
        {"name": "Molecule", "token": None, "focus": "IP-NFTs / Biotech", "treasury_usd_m": 10, "projects_funded": 12, "chain": "Ethereum"},
        {"name": "LabDAO", "token": None, "focus": "Open-Source Lab Tools", "treasury_usd_m": 3, "projects_funded": 8, "chain": "Ethereum"},
        {"name": "ResearchHub", "token": "RSC", "focus": "Open Science Publishing", "treasury_usd_m": 5, "projects_funded": 200, "chain": "Ethereum"},
        {"name": "AthenaDAO", "token": None, "focus": "Women's Health Research", "treasury_usd_m": 2, "projects_funded": 6, "chain": "Ethereum"},
        {"name": "PsyDAO", "token": None, "focus": "Psychedelic Research", "treasury_usd_m": 1.5, "projects_funded": 4, "chain": "Ethereum"},
        {"name": "ValleyDAO", "token": "GROW", "focus": "Synthetic Biology", "treasury_usd_m": 2, "projects_funded": 5, "chain": "Ethereum"},
        {"name": "HairDAO", "token": "HAIR", "focus": "Hair Loss Research", "treasury_usd_m": 1, "projects_funded": 3, "chain": "Ethereum"},
        {"name": "Bio Protocol", "token": "BIO", "focus": "DeSci Launchpad", "treasury_usd_m": 25, "projects_funded": 7, "chain": "Ethereum"},
        {"name": "GenomesDAO", "token": "GENE", "focus": "Genomic Data Ownership", "treasury_usd_m": 2, "projects_funded": 3, "chain": "Ethereum"},
    ]
    total_treasury = sum(p["treasury_usd_m"] for p in protocols)
    return {"protocols": protocols, "total_treasury_usd_m": total_treasury, "count": len(protocols), "as_of": datetime.utcnow().isoformat()}


def get_desci_market_overview():
    """Return DeSci market size, growth metrics, and key trends."""
    return {
        "total_market_cap_usd_m": 450,
        "total_funding_raised_usd_m": 320,
        "active_research_daos": 30,
        "total_projects_funded": 280,
        "key_trends": [
            "IP-NFTs tokenizing biotech IP rights",
            "Quadratic funding for open science",
            "Data DAOs for patient-owned health data",
            "Token-curated registries for peer review",
            "Biotech launchpads (Bio Protocol) gaining traction",
        ],
        "challenges": [
            "Regulatory uncertainty around IP-NFTs",
            "Limited liquidity for DeSci tokens",
            "Academic adoption still nascent",
            "Sustainability of DAO treasury funding",
        ],
        "as_of": datetime.utcnow().isoformat(),
    }


def get_desci_tokens():
    """Return tradeable DeSci tokens with basic market data."""
    tokens = [
        {"token": "VITA", "name": "VitaDAO", "chain": "Ethereum", "category": "Longevity"},
        {"token": "RSC", "name": "ResearchCoin", "chain": "Ethereum", "category": "Publishing"},
        {"token": "BIO", "name": "Bio Protocol", "chain": "Ethereum", "category": "Launchpad"},
        {"token": "GENE", "name": "GenomesDAO", "chain": "Ethereum", "category": "Genomics"},
        {"token": "GROW", "name": "ValleyDAO", "chain": "Ethereum", "category": "Synthetic Bio"},
        {"token": "HAIR", "name": "HairDAO", "chain": "Ethereum", "category": "Hair Loss"},
        {"token": "LAKE", "name": "Data Lake", "chain": "Ethereum", "category": "Health Data"},
    ]
    return {"tokens": tokens, "count": len(tokens), "note": "Use CoinGecko API for live prices", "as_of": datetime.utcnow().isoformat()}


def fetch_desci_news():
    """Fetch recent DeSci news from free sources."""
    try:
        url = "https://newsapi.org/v2/everything?q=decentralized+science+OR+DeSci+OR+IP-NFT+OR+research+DAO&sortBy=publishedAt&pageSize=10&language=en&apiKey=demo"
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            articles = [{"title": a["title"], "source": a["source"]["name"], "url": a["url"]} for a in data.get("articles", [])]
            return {"articles": articles, "count": len(articles)}
    except Exception as e:
        return {"articles": [], "error": str(e), "note": "Use get_desci_protocols() for offline data"}
