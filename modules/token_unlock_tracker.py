"""Token Unlock Schedule Tracker — monitors upcoming token vesting unlocks.

Tracks vesting schedules, cliff unlocks, and linear vesting events for major
crypto tokens. Uses free APIs and public vesting data to alert on upcoming
supply increases that may impact price.
"""

import json
import math
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


# Major token unlock schedules (curated from public data)
VESTING_SCHEDULES = {
    "ARB": {
        "name": "Arbitrum",
        "total_supply": 10_000_000_000,
        "tge_date": "2023-03-23",
        "team_pct": 26.94,
        "investor_pct": 17.53,
        "cliff_months": 12,
        "vesting_months": 36,
        "category": "L2",
    },
    "OP": {
        "name": "Optimism",
        "total_supply": 4_294_967_296,
        "tge_date": "2022-05-31",
        "team_pct": 19.0,
        "investor_pct": 17.0,
        "cliff_months": 12,
        "vesting_months": 48,
        "category": "L2",
    },
    "APT": {
        "name": "Aptos",
        "total_supply": 1_000_000_000,
        "tge_date": "2022-10-12",
        "team_pct": 19.0,
        "investor_pct": 13.48,
        "cliff_months": 12,
        "vesting_months": 48,
        "category": "L1",
    },
    "SUI": {
        "name": "Sui",
        "total_supply": 10_000_000_000,
        "tge_date": "2023-05-03",
        "team_pct": 20.0,
        "investor_pct": 14.0,
        "cliff_months": 12,
        "vesting_months": 36,
        "category": "L1",
    },
    "SEI": {
        "name": "Sei",
        "total_supply": 10_000_000_000,
        "tge_date": "2023-08-15",
        "team_pct": 20.0,
        "investor_pct": 20.0,
        "cliff_months": 12,
        "vesting_months": 36,
        "category": "L1",
    },
    "TIA": {
        "name": "Celestia",
        "total_supply": 1_000_000_000,
        "tge_date": "2023-10-31",
        "team_pct": 25.0,
        "investor_pct": 15.0,
        "cliff_months": 12,
        "vesting_months": 48,
        "category": "Modular",
    },
    "JUP": {
        "name": "Jupiter",
        "total_supply": 10_000_000_000,
        "tge_date": "2024-01-31",
        "team_pct": 50.0,
        "investor_pct": 0,
        "cliff_months": 12,
        "vesting_months": 24,
        "category": "DeFi",
    },
    "STRK": {
        "name": "StarkNet",
        "total_supply": 10_000_000_000,
        "tge_date": "2024-02-20",
        "team_pct": 32.9,
        "investor_pct": 17.0,
        "cliff_months": 12,
        "vesting_months": 48,
        "category": "L2",
    },
    "W": {
        "name": "Wormhole",
        "total_supply": 10_000_000_000,
        "tge_date": "2024-04-03",
        "team_pct": 23.3,
        "investor_pct": 16.7,
        "cliff_months": 12,
        "vesting_months": 36,
        "category": "Bridge",
    },
    "ZK": {
        "name": "zkSync",
        "total_supply": 21_000_000_000,
        "tge_date": "2024-06-17",
        "team_pct": 16.1,
        "investor_pct": 17.2,
        "cliff_months": 12,
        "vesting_months": 36,
        "category": "L2",
    },
}


def calculate_unlock_schedule(
    token: str,
    months_ahead: int = 12
) -> Dict[str, Any]:
    """Calculate upcoming unlock events for a specific token.
    
    Args:
        token: Token ticker (e.g., 'ARB', 'OP').
        months_ahead: How many months ahead to project.
        
    Returns:
        Unlock schedule with dates and amounts.
    """
    token = token.upper()
    if token not in VESTING_SCHEDULES:
        return {"error": f"Token {token} not tracked", "available": list(VESTING_SCHEDULES.keys())}
    
    sched = VESTING_SCHEDULES[token]
    tge = datetime.strptime(sched["tge_date"], "%Y-%m-%d")
    now = datetime.utcnow()
    
    total = sched["total_supply"]
    team_tokens = total * sched["team_pct"] / 100
    investor_tokens = total * sched["investor_pct"] / 100
    locked_tokens = team_tokens + investor_tokens
    
    cliff_date = tge + timedelta(days=sched["cliff_months"] * 30)
    vest_end = tge + timedelta(days=(sched["cliff_months"] + sched["vesting_months"]) * 30)
    
    # Monthly linear unlock after cliff
    monthly_unlock = locked_tokens / sched["vesting_months"] if sched["vesting_months"] > 0 else 0
    
    events = []
    for m in range(sched["vesting_months"]):
        event_date = cliff_date + timedelta(days=m * 30)
        if event_date < now:
            continue
        if event_date > now + timedelta(days=months_ahead * 30):
            break
        events.append({
            "date": event_date.strftime("%Y-%m-%d"),
            "tokens_unlocked": round(monthly_unlock),
            "pct_of_supply": round(monthly_unlock / total * 100, 2),
            "type": "linear_vest",
            "days_from_now": (event_date - now).days,
        })
    
    # Calculate current circulating estimate
    months_since_cliff = max(0, (now - cliff_date).days / 30)
    already_unlocked = min(locked_tokens, monthly_unlock * months_since_cliff)
    circulating_pct = (total - locked_tokens + already_unlocked) / total * 100
    
    return {
        "token": token,
        "name": sched["name"],
        "category": sched["category"],
        "total_supply": total,
        "locked_tokens": round(locked_tokens),
        "monthly_unlock": round(monthly_unlock),
        "monthly_unlock_pct": round(monthly_unlock / total * 100, 2),
        "cliff_date": cliff_date.strftime("%Y-%m-%d"),
        "cliff_passed": now >= cliff_date,
        "vesting_end": vest_end.strftime("%Y-%m-%d"),
        "vesting_complete": now >= vest_end,
        "est_circulating_pct": round(circulating_pct, 1),
        "upcoming_events": events[:12],
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_upcoming_unlocks(
    days_ahead: int = 30,
    min_pct_supply: float = 0.5
) -> List[Dict[str, Any]]:
    """Get all upcoming token unlocks across tracked tokens.
    
    Args:
        days_ahead: Days to look ahead.
        min_pct_supply: Minimum % of supply to include.
        
    Returns:
        List of upcoming unlock events sorted by date.
    """
    all_events = []
    now = datetime.utcnow()
    
    for token in VESTING_SCHEDULES:
        schedule = calculate_unlock_schedule(token, months_ahead=max(1, days_ahead // 30 + 1))
        if "error" in schedule:
            continue
        for event in schedule.get("upcoming_events", []):
            if event["days_from_now"] <= days_ahead and event["pct_of_supply"] >= min_pct_supply:
                event["token"] = token
                event["name"] = schedule["name"]
                all_events.append(event)
    
    all_events.sort(key=lambda x: x["days_from_now"])
    
    return {
        "upcoming_unlocks": all_events,
        "total_events": len(all_events),
        "days_ahead": days_ahead,
        "min_pct_filter": min_pct_supply,
        "tokens_tracked": len(VESTING_SCHEDULES),
        "timestamp": datetime.utcnow().isoformat(),
    }


def unlock_impact_score(token: str) -> Dict[str, Any]:
    """Calculate supply dilution impact score for a token's unlocks.
    
    Args:
        token: Token ticker.
        
    Returns:
        Impact assessment with pressure score.
    """
    schedule = calculate_unlock_schedule(token, months_ahead=6)
    if "error" in schedule:
        return schedule
    
    events = schedule.get("upcoming_events", [])
    
    # 30-day supply pressure
    pressure_30d = sum(e["pct_of_supply"] for e in events if e["days_from_now"] <= 30)
    pressure_90d = sum(e["pct_of_supply"] for e in events if e["days_from_now"] <= 90)
    pressure_180d = sum(e["pct_of_supply"] for e in events if e["days_from_now"] <= 180)
    
    # Impact score (0-100, higher = more dilutive pressure)
    score = min(100, pressure_30d * 10 + pressure_90d * 3 + pressure_180d)
    
    if score > 70:
        risk = "HIGH"
        signal = "Significant selling pressure expected"
    elif score > 30:
        risk = "MEDIUM"
        signal = "Moderate supply increase"
    else:
        risk = "LOW"
        signal = "Minimal dilution pressure"
    
    return {
        "token": token,
        "name": schedule["name"],
        "impact_score": round(score, 1),
        "risk_level": risk,
        "signal": signal,
        "supply_pressure_30d_pct": round(pressure_30d, 2),
        "supply_pressure_90d_pct": round(pressure_90d, 2),
        "supply_pressure_180d_pct": round(pressure_180d, 2),
        "est_circulating_pct": schedule["est_circulating_pct"],
        "vesting_complete": schedule["vesting_complete"],
        "timestamp": datetime.utcnow().isoformat(),
    }
