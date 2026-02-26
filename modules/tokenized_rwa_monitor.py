"""
Tokenized Real World Assets (RWA) Monitor — Track tokenized treasuries, private credit,
real estate, and commodities on-chain across protocols like Ondo, Maple, Centrifuge,
MakerDAO, and Franklin Templeton.

Monitors TVL, yields, asset types, and growth trends in the RWA tokenization space.
"""

import json
import urllib.request
from datetime import datetime, timedelta
from typing import Any


def get_rwa_protocol_tvl() -> dict[str, Any]:
    """Fetch TVL data for major RWA protocols from DeFiLlama."""
    protocols = [
        "ondo-finance", "maple", "centrifuge", "goldfinch",
        "backed-finance", "matrixdock", "mountain-protocol",
        "hashnote", "superstate", "openeden"
    ]
    results = []
    for slug in protocols:
        try:
            url = f"https://api.llama.fi/protocol/{slug}"
            req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                tvl = data.get("tvl", [])
                current_tvl = tvl[-1]["totalLiquidityUSD"] if tvl else 0
                results.append({
                    "protocol": data.get("name", slug),
                    "slug": slug,
                    "category": data.get("category", "RWA"),
                    "tvl_usd": round(current_tvl, 2),
                    "chains": data.get("chains", []),
                    "symbol": data.get("symbol", ""),
                })
        except Exception as e:
            results.append({"protocol": slug, "error": str(e)})
    total_tvl = sum(r.get("tvl_usd", 0) for r in results if "error" not in r)
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total_rwa_tvl_usd": round(total_tvl, 2),
        "protocols": sorted(results, key=lambda x: x.get("tvl_usd", 0), reverse=True),
        "protocol_count": len([r for r in results if "error" not in r]),
    }


def get_rwa_market_overview() -> dict[str, Any]:
    """Get overview of the tokenized RWA market including categories and trends."""
    categories = {
        "tokenized_treasuries": {
            "description": "On-chain US Treasury products",
            "key_protocols": ["Ondo (USDY/OUSG)", "Franklin Templeton (BENJI)", "Hashnote (USYC)", "OpenEden (TBILL)", "Superstate"],
            "typical_yield_range": "4.5-5.2%",
        },
        "private_credit": {
            "description": "Tokenized private lending pools",
            "key_protocols": ["Maple Finance", "Goldfinch", "Centrifuge", "Credix"],
            "typical_yield_range": "8-15%",
        },
        "tokenized_real_estate": {
            "description": "Fractional real estate on-chain",
            "key_protocols": ["RealT", "Lofty", "Tangible (USDR)"],
            "typical_yield_range": "5-10%",
        },
        "tokenized_commodities": {
            "description": "Gold, silver, and other commodities on-chain",
            "key_protocols": ["Paxos (PAXG)", "Tether Gold (XAUT)", "Backed Finance"],
            "typical_yield_range": "0% (appreciation only)",
        },
    }
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "categories": categories,
        "total_categories": len(categories),
        "growth_drivers": [
            "Institutional demand for on-chain yield",
            "Regulatory clarity improving globally",
            "BlackRock BUIDL fund catalyzing adoption",
            "Stablecoin-to-yield pipeline maturing",
        ],
    }


def get_treasury_token_yields() -> dict[str, Any]:
    """Fetch and compare yields across tokenized treasury products."""
    # Known tokenized treasury products with approximate data
    products = [
        {"name": "USDY (Ondo)", "chain": "Ethereum/Solana", "type": "Rebasing yield token", "backing": "US Treasuries + bank deposits"},
        {"name": "OUSG (Ondo)", "chain": "Ethereum", "type": "Tokenized SHV ETF", "backing": "BlackRock SHV"},
        {"name": "BENJI (Franklin Templeton)", "chain": "Stellar/Polygon", "type": "Tokenized money market fund", "backing": "FOBXX fund"},
        {"name": "USYC (Hashnote)", "chain": "Ethereum", "type": "Yield-bearing stablecoin", "backing": "Short-term Treasuries"},
        {"name": "TBILL (OpenEden)", "chain": "Ethereum", "type": "T-Bill vault token", "backing": "US T-Bills"},
        {"name": "BUIDL (BlackRock)", "chain": "Ethereum", "type": "Tokenized fund", "backing": "US Treasuries/repos"},
    ]
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "products": products,
        "benchmark": "Fed Funds Rate",
        "note": "Actual yields vary; check protocol dashboards for real-time APY",
    }


def analyze_rwa_growth_trends() -> dict[str, Any]:
    """Analyze growth trends in the RWA tokenization sector."""
    milestones = [
        {"date": "2023-03", "event": "RWA TVL crosses $1B", "significance": "Milestone for institutional adoption"},
        {"date": "2023-07", "event": "MakerDAO allocates $1B+ to RWA vaults", "significance": "Largest DeFi protocol embraces RWA"},
        {"date": "2024-03", "event": "BlackRock launches BUIDL fund on Ethereum", "significance": "World's largest asset manager enters tokenization"},
        {"date": "2024-06", "event": "RWA TVL crosses $5B", "significance": "5x growth in 15 months"},
        {"date": "2024-11", "event": "Multiple TradFi firms launch tokenized products", "significance": "JPMorgan, Franklin Templeton, WisdomTree active"},
        {"date": "2025-06", "event": "Tokenized treasuries exceed $10B", "significance": "Becoming meaningful share of money market"},
    ]
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "milestones": milestones,
        "growth_metrics": {
            "estimated_cagr": "200%+ (2023-2025)",
            "institutional_participants": "50+ TradFi firms",
            "chains_with_rwa": ["Ethereum", "Polygon", "Solana", "Stellar", "Avalanche", "Base", "Arbitrum"],
        },
        "risks": [
            "Regulatory uncertainty in some jurisdictions",
            "Smart contract risk on underlying protocols",
            "Liquidity fragmentation across chains",
            "Oracle dependency for off-chain asset pricing",
        ],
    }
