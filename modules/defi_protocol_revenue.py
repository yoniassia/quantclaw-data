"""
DeFi Protocol Revenue Tracker — Monitor revenue and fees across major DeFi protocols.

Tracks protocol revenue, fee generation, TVL-to-revenue ratios, and revenue trends
for lending, DEX, derivatives, and yield protocols. Essential for DeFi fundamental analysis.

Data sources: DefiLlama API (free, no key required).
"""

import json
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


DEFILLAMA_BASE = "https://api.llama.fi"
DEFILLAMA_FEES = "https://fees.llama.fi"

# Major revenue-generating protocols
TOP_PROTOCOLS = [
    "lido", "uniswap", "aave", "maker", "pancakeswap",
    "gmx", "curve-dex", "convex-finance", "compound",
    "sushiswap", "balancer", "synthetix", "dydx",
    "raydium", "jupiter", "jito"
]


def _fetch_json(url: str, timeout: int = 15) -> Any:
    """Fetch JSON from URL."""
    req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def get_protocol_fees(protocol: str = "uniswap") -> Dict:
    """
    Get fee and revenue data for a specific DeFi protocol from DefiLlama.

    Args:
        protocol: Protocol slug (e.g., 'uniswap', 'aave', 'lido')

    Returns dict with daily/total fees, revenue, and protocol details.
    """
    url = f"{DEFILLAMA_FEES}/summary/fees/{protocol}"

    try:
        data = _fetch_json(url)
    except Exception:
        return {"protocol": protocol, "error": "Data not available", "timestamp": datetime.utcnow().isoformat()}

    return {
        "protocol": protocol,
        "name": data.get("name", protocol),
        "category": data.get("category", "Unknown"),
        "chains": data.get("chains", []),
        "total_24h_fees": data.get("total24h", 0),
        "total_48h_to_24h_fees": data.get("total48hto24h", 0),
        "total_7d_fees": data.get("total7d", 0),
        "total_30d_fees": data.get("total30d", 0),
        "total_1y_fees": data.get("total1y", 0),
        "total_all_time_fees": data.get("totalAllTime", 0),
        "daily_revenue": data.get("dailyRevenue", 0),
        "methodology": data.get("methodology", {}),
        "fee_change_1d_pct": _calc_change(
            data.get("total24h", 0),
            data.get("total48hto24h", 0)
        ),
        "timestamp": datetime.utcnow().isoformat()
    }


def _calc_change(current: float, previous: float) -> Optional[float]:
    """Calculate percentage change."""
    if previous and previous > 0:
        return round((current - previous) / previous * 100, 2)
    return None


def get_protocol_tvl(protocol: str = "uniswap") -> Dict:
    """
    Get TVL data for a protocol to calculate revenue/TVL ratio.

    Args:
        protocol: Protocol slug

    Returns dict with current TVL and chain breakdown.
    """
    url = f"{DEFILLAMA_BASE}/protocol/{protocol}"
    data = _fetch_json(url)

    current_tvl = data.get("currentChainTvls", {})
    total_tvl = sum(v for k, v in current_tvl.items()
                    if not k.endswith("-staking") and not k.endswith("-borrowed"))

    return {
        "protocol": protocol,
        "name": data.get("name", protocol),
        "total_tvl_usd": total_tvl,
        "chain_tvls": current_tvl,
        "category": data.get("category", ""),
        "timestamp": datetime.utcnow().isoformat()
    }


def get_top_revenue_protocols(limit: int = 20) -> Dict:
    """
    Get top DeFi protocols ranked by fee revenue.

    Args:
        limit: Number of protocols to return

    Returns ranked list of protocols by 24h fees with revenue metrics.
    """
    url = f"{DEFILLAMA_FEES}/overview/fees"
    data = _fetch_json(url)

    protocols = data.get("protocols", [])

    # Sort by 24h fees
    ranked = sorted(protocols, key=lambda x: x.get("total24h", 0) or 0, reverse=True)[:limit]

    results = []
    total_fees = sum(p.get("total24h", 0) or 0 for p in ranked)

    for p in ranked:
        fees_24h = p.get("total24h", 0) or 0
        share = (fees_24h / total_fees * 100) if total_fees > 0 else 0

        results.append({
            "protocol": p.get("slug", p.get("name", "unknown")),
            "name": p.get("name", "Unknown"),
            "category": p.get("category", ""),
            "chains": p.get("chains", []),
            "fees_24h": fees_24h,
            "fees_7d": p.get("total7d", 0) or 0,
            "fees_30d": p.get("total30d", 0) or 0,
            "market_share_pct": round(share, 2),
            "change_1d_pct": _calc_change(
                p.get("total24h", 0) or 0,
                p.get("total48hto24h", 0) or 0
            )
        })

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total_defi_fees_24h": total_fees,
        "protocols_count": len(results),
        "top_protocols": results,
        "by_category": _group_by_category(results),
        "summary": f"Top {len(results)} DeFi protocols generated ${total_fees:,.0f} in 24h fees. "
                   f"#1: {results[0]['name']} (${results[0]['fees_24h']:,.0f})" if results else "No data."
    }


def _group_by_category(protocols: List[Dict]) -> Dict:
    """Group protocol fees by category."""
    categories = {}
    for p in protocols:
        cat = p.get("category", "Other")
        if cat not in categories:
            categories[cat] = {"total_fees_24h": 0, "count": 0, "protocols": []}
        categories[cat]["total_fees_24h"] += p["fees_24h"]
        categories[cat]["count"] += 1
        categories[cat]["protocols"].append(p["name"])
    return categories


def get_revenue_dashboard(protocols: Optional[List[str]] = None) -> Dict:
    """
    Comprehensive DeFi revenue dashboard with TVL-to-revenue analysis.

    Args:
        protocols: List of protocol slugs. Defaults to top protocols.

    Returns dashboard with fees, TVL, and efficiency ratios.
    """
    protocols = protocols or TOP_PROTOCOLS[:8]

    results = []
    for slug in protocols:
        try:
            fees = get_protocol_fees(slug)
            if fees.get("error"):
                continue

            tvl_data = get_protocol_tvl(slug)
            tvl = tvl_data.get("total_tvl_usd", 0)

            # Revenue efficiency: annualized fees / TVL
            fees_24h = fees.get("total_24h_fees", 0) or 0
            annual_fees = fees_24h * 365
            efficiency = (annual_fees / tvl * 100) if tvl > 0 else 0

            results.append({
                "protocol": slug,
                "name": fees.get("name", slug),
                "category": fees.get("category", ""),
                "fees_24h": fees_24h,
                "fees_30d": fees.get("total_30d_fees", 0) or 0,
                "tvl_usd": tvl,
                "annualized_fee_yield_pct": round(efficiency, 2),
                "revenue_24h": fees.get("daily_revenue", 0) or 0,
                "chains": fees.get("chains", [])
            })
        except Exception:
            continue

    results.sort(key=lambda x: x["fees_24h"], reverse=True)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "protocols_analyzed": len(results),
        "total_fees_24h": sum(r["fees_24h"] for r in results),
        "total_tvl": sum(r["tvl_usd"] for r in results),
        "protocols": results,
        "most_efficient": max(results, key=lambda x: x["annualized_fee_yield_pct"])["name"] if results else None,
        "summary": f"Analyzed {len(results)} protocols. "
                   f"Total 24h fees: ${sum(r['fees_24h'] for r in results):,.0f}. "
                   f"Total TVL: ${sum(r['tvl_usd'] for r in results) / 1e9:.1f}B."
    }
