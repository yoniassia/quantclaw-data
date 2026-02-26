"""Governance Proposal Monitor — tracks on-chain and Snapshot governance proposals.

Monitors DAO governance activity across major protocols using Snapshot GraphQL
API and on-chain data. Tracks proposals, voting power, quorum, and outcomes.
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


SNAPSHOT_GRAPHQL = "https://hub.snapshot.org/graphql"

# Major DAOs to track
TRACKED_DAOS = {
    "aave.eth": {"name": "Aave", "category": "DeFi/Lending"},
    "uniswapgovernance.eth": {"name": "Uniswap", "category": "DeFi/DEX"},
    "ens.eth": {"name": "ENS", "category": "Infrastructure"},
    "arbitrumfoundation.eth": {"name": "Arbitrum", "category": "L2"},
    "opcollective.eth": {"name": "Optimism", "category": "L2"},
    "lido-snapshot.eth": {"name": "Lido", "category": "DeFi/Staking"},
    "safe.eth": {"name": "Safe", "category": "Infrastructure"},
    "balancer.eth": {"name": "Balancer", "category": "DeFi/DEX"},
    "gmx.eth": {"name": "GMX", "category": "DeFi/Perps"},
    "frax.eth": {"name": "Frax", "category": "DeFi/Stablecoin"},
    "starknet.eth": {"name": "StarkNet", "category": "L2"},
    "apecoin.eth": {"name": "ApeCoin", "category": "NFT/Gaming"},
    "gitcoindao.eth": {"name": "Gitcoin", "category": "Public Goods"},
    "cakevote.eth": {"name": "PancakeSwap", "category": "DeFi/DEX"},
    "snapshot.dcl.eth": {"name": "Decentraland", "category": "Metaverse"},
}


def _graphql_query(query: str, variables: Optional[Dict] = None) -> Any:
    """Execute a GraphQL query against Snapshot Hub."""
    payload = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        SNAPSHOT_GRAPHQL,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "QuantClaw/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def get_active_proposals(
    space: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """Fetch active governance proposals from Snapshot.
    
    Args:
        space: Specific DAO space (e.g., 'aave.eth'). None for all tracked.
        limit: Max proposals to return.
        
    Returns:
        List of active proposals with voting data.
    """
    now_ts = int(datetime.utcnow().timestamp())
    
    if space:
        spaces = [space]
    else:
        spaces = list(TRACKED_DAOS.keys())
    
    query = """
    query($spaces: [String!], $now: Int!, $limit: Int!) {
        proposals(
            where: { space_in: $spaces, state: "active", end_gte: $now }
            orderBy: "end"
            orderDirection: asc
            first: $limit
        ) {
            id
            title
            body
            choices
            start
            end
            state
            space { id name }
            scores
            scores_total
            votes
            quorum
            type
            link
        }
    }
    """
    
    result = _graphql_query(query, {"spaces": spaces, "now": now_ts, "limit": limit})
    
    if "error" in result:
        return result
    
    proposals = result.get("data", {}).get("proposals", [])
    
    formatted = []
    for p in proposals:
        end_dt = datetime.fromtimestamp(p.get("end", 0))
        hours_left = max(0, (end_dt - datetime.utcnow()).total_seconds() / 3600)
        
        scores = p.get("scores", [])
        choices = p.get("choices", [])
        total = p.get("scores_total", 0)
        
        # Determine leading choice
        if scores and choices:
            max_idx = scores.index(max(scores))
            leading = choices[max_idx] if max_idx < len(choices) else "Unknown"
            leading_pct = (scores[max_idx] / total * 100) if total > 0 else 0
        else:
            leading = "No votes"
            leading_pct = 0
        
        quorum = p.get("quorum", 0)
        quorum_reached = total >= quorum if quorum > 0 else None
        
        formatted.append({
            "id": p.get("id", "")[:16],
            "title": p.get("title", ""),
            "space": p.get("space", {}).get("name", ""),
            "space_id": p.get("space", {}).get("id", ""),
            "type": p.get("type", "single-choice"),
            "votes": p.get("votes", 0),
            "scores_total": round(total, 2),
            "leading_choice": leading,
            "leading_pct": round(leading_pct, 1),
            "quorum": quorum,
            "quorum_reached": quorum_reached,
            "hours_remaining": round(hours_left, 1),
            "end_date": end_dt.strftime("%Y-%m-%d %H:%M UTC"),
            "choices_breakdown": list(zip(choices, [round(s, 2) for s in scores])) if scores else [],
        })
    
    return {
        "active_proposals": formatted,
        "total_found": len(formatted),
        "spaces_queried": len(spaces),
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_recent_proposals(
    space: Optional[str] = None,
    days: int = 7,
    limit: int = 30
) -> Dict[str, Any]:
    """Fetch recently closed proposals.
    
    Args:
        space: Specific DAO space or None for all tracked.
        days: Look back this many days.
        limit: Max proposals.
        
    Returns:
        List of closed proposals with outcomes.
    """
    cutoff = int((datetime.utcnow() - timedelta(days=days)).timestamp())
    spaces = [space] if space else list(TRACKED_DAOS.keys())
    
    query = """
    query($spaces: [String!], $cutoff: Int!, $limit: Int!) {
        proposals(
            where: { space_in: $spaces, state: "closed", end_gte: $cutoff }
            orderBy: "end"
            orderDirection: desc
            first: $limit
        ) {
            id
            title
            choices
            start
            end
            state
            space { id name }
            scores
            scores_total
            votes
            quorum
            type
        }
    }
    """
    
    result = _graphql_query(query, {"spaces": spaces, "cutoff": cutoff, "limit": limit})
    
    if "error" in result:
        return result
    
    proposals = result.get("data", {}).get("proposals", [])
    
    formatted = []
    for p in proposals:
        scores = p.get("scores", [])
        choices = p.get("choices", [])
        total = p.get("scores_total", 0)
        
        if scores and choices:
            max_idx = scores.index(max(scores))
            outcome = choices[max_idx] if max_idx < len(choices) else "Unknown"
            outcome_pct = (scores[max_idx] / total * 100) if total > 0 else 0
        else:
            outcome = "No votes"
            outcome_pct = 0
        
        quorum = p.get("quorum", 0)
        passed = total >= quorum if quorum > 0 else None
        
        formatted.append({
            "title": p.get("title", ""),
            "space": p.get("space", {}).get("name", ""),
            "outcome": outcome,
            "outcome_pct": round(outcome_pct, 1),
            "votes": p.get("votes", 0),
            "quorum_met": passed,
            "end_date": datetime.fromtimestamp(p.get("end", 0)).strftime("%Y-%m-%d"),
        })
    
    return {
        "recent_proposals": formatted,
        "total_found": len(formatted),
        "lookback_days": days,
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_dao_activity_summary() -> Dict[str, Any]:
    """Get governance activity summary across all tracked DAOs.
    
    Returns:
        Summary of active proposals, recent votes, and DAO activity levels.
    """
    active = get_active_proposals(limit=50)
    recent = get_recent_proposals(days=7, limit=50)
    
    if "error" in active:
        return active
    
    # Aggregate by DAO
    dao_stats = {}
    for p in active.get("active_proposals", []):
        space = p.get("space_id", p.get("space", ""))
        if space not in dao_stats:
            dao_stats[space] = {"active": 0, "recent_closed": 0, "total_votes": 0, "name": p.get("space", "")}
        dao_stats[space]["active"] += 1
    
    for p in recent.get("recent_proposals", []):
        space = p.get("space", "")
        for sid, info in TRACKED_DAOS.items():
            if info["name"] == space:
                if sid not in dao_stats:
                    dao_stats[sid] = {"active": 0, "recent_closed": 0, "total_votes": 0, "name": space}
                dao_stats[sid]["recent_closed"] += 1
                dao_stats[sid]["total_votes"] += p.get("votes", 0)
                break
    
    # Sort by activity
    ranked = sorted(dao_stats.items(), key=lambda x: x[1]["active"] + x[1]["recent_closed"], reverse=True)
    
    return {
        "total_active_proposals": active.get("total_found", 0),
        "total_recent_closed": recent.get("total_found", 0),
        "daos_tracked": len(TRACKED_DAOS),
        "most_active_daos": [{"space": k, **v} for k, v in ranked[:10]],
        "high_urgency": [p for p in active.get("active_proposals", []) if p.get("hours_remaining", 999) < 24],
        "timestamp": datetime.utcnow().isoformat(),
    }
