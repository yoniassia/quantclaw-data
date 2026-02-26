"""Capital Call & Distribution Tracker — Tracks private fund capital calls,
distributions, recallable capital, DPI/TVPI/RVPI multiples, and IRR calculations
for PE/VC/hedge fund LP investors."""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


def calculate_irr(cashflows: List[Tuple[int, float]], guess: float = 0.1,
                   max_iter: int = 1000, tol: float = 1e-8) -> Optional[float]:
    """Calculate Internal Rate of Return using Newton's method.
    
    Args:
        cashflows: List of (day_offset, amount) tuples. Negative = outflow (capital call)
        guess: Initial IRR guess
        max_iter: Maximum iterations
        tol: Convergence tolerance
    
    Returns:
        Annualized IRR as decimal, or None if no convergence
    """
    if not cashflows:
        return None
    
    rate = guess
    for _ in range(max_iter):
        npv = sum(cf / (1 + rate) ** (d / 365) for d, cf in cashflows)
        dnpv = sum(-d / 365 * cf / (1 + rate) ** (d / 365 + 1) for d, cf in cashflows)
        if abs(dnpv) < 1e-12:
            break
        new_rate = rate - npv / dnpv
        if abs(new_rate - rate) < tol:
            return round(new_rate, 6)
        rate = new_rate
    
    return round(rate, 6) if abs(npv) < 1.0 else None


def track_fund_cashflows(commitment: float, events: List[Dict]) -> Dict:
    """Track capital calls and distributions for a fund investment.
    
    Args:
        commitment: Total LP commitment amount
        events: List of dicts with 'date' (YYYY-MM-DD), 'type' ('call' or 'distribution'),
                'amount', and optional 'recallable' boolean
    
    Returns:
        Full cashflow tracking with multiples and J-curve data
    """
    called = 0
    distributed = 0
    recallable = 0
    net_cashflows = []
    timeline = []
    base_date = None
    
    for event in sorted(events, key=lambda x: x["date"]):
        dt = datetime.strptime(event["date"], "%Y-%m-%d")
        if base_date is None:
            base_date = dt
        
        day_offset = (dt - base_date).days
        amt = event["amount"]
        etype = event["type"]
        
        if etype == "call":
            called += amt
            net_cashflows.append((day_offset, -amt))
        elif etype == "distribution":
            distributed += amt
            net_cashflows.append((day_offset, amt))
            if event.get("recallable", False):
                recallable += amt
        
        unfunded = commitment - called + recallable
        
        timeline.append({
            "date": event["date"],
            "type": etype,
            "amount": amt,
            "cumulative_called": round(called, 2),
            "cumulative_distributed": round(distributed, 2),
            "unfunded_commitment": round(unfunded, 2),
            "net_cashflow": round(distributed - called, 2)
        })
    
    # Multiples
    dpi = distributed / called if called > 0 else 0
    
    irr = calculate_irr(net_cashflows) if len(net_cashflows) >= 2 else None
    
    return {
        "commitment": commitment,
        "total_called": round(called, 2),
        "total_distributed": round(distributed, 2),
        "recallable_capital": round(recallable, 2),
        "unfunded_commitment": round(commitment - called + recallable, 2),
        "call_pct": round(called / commitment * 100, 2) if commitment > 0 else 0,
        "dpi": round(dpi, 4),
        "net_cashflow": round(distributed - called, 2),
        "irr": irr,
        "irr_pct": round(irr * 100, 4) if irr is not None else None,
        "timeline": timeline,
        "event_count": len(events)
    }


def portfolio_summary(funds: List[Dict]) -> Dict:
    """Aggregate capital call tracking across multiple fund commitments.
    
    Args:
        funds: List of dicts with 'name', 'vintage', 'commitment', 'nav', 'events'
    
    Returns:
        Portfolio-level aggregation with per-fund and total metrics
    """
    total_commitment = 0
    total_called = 0
    total_distributed = 0
    total_nav = 0
    fund_results = []
    
    for fund in funds:
        tracking = track_fund_cashflows(fund["commitment"], fund.get("events", []))
        nav = fund.get("nav", 0)
        called = tracking["total_called"]
        distributed = tracking["total_distributed"]
        
        tvpi = (distributed + nav) / called if called > 0 else 0
        dpi = distributed / called if called > 0 else 0
        rvpi = nav / called if called > 0 else 0
        
        total_commitment += fund["commitment"]
        total_called += called
        total_distributed += distributed
        total_nav += nav
        
        fund_results.append({
            "name": fund["name"],
            "vintage": fund.get("vintage"),
            "commitment": fund["commitment"],
            "called": called,
            "distributed": distributed,
            "nav": nav,
            "tvpi": round(tvpi, 4),
            "dpi": round(dpi, 4),
            "rvpi": round(rvpi, 4),
            "irr_pct": tracking["irr_pct"]
        })
    
    total_tvpi = (total_distributed + total_nav) / total_called if total_called > 0 else 0
    total_dpi = total_distributed / total_called if total_called > 0 else 0
    
    return {
        "portfolio_totals": {
            "total_commitment": round(total_commitment, 2),
            "total_called": round(total_called, 2),
            "total_distributed": round(total_distributed, 2),
            "total_nav": round(total_nav, 2),
            "tvpi": round(total_tvpi, 4),
            "dpi": round(total_dpi, 4),
            "fund_count": len(funds)
        },
        "funds": fund_results
    }


def j_curve_projection(commitment: float, fund_life_years: int = 10,
                         deploy_years: int = 4, target_tvpi: float = 2.0) -> Dict:
    """Project J-curve pattern for a PE/VC fund investment.
    
    Args:
        commitment: Total commitment
        fund_life_years: Expected fund life in years
        deploy_years: Capital deployment period
        target_tvpi: Target total value to paid-in multiple
    
    Returns:
        Year-by-year projected cashflows and net position
    """
    projections = []
    called = 0
    distributed = 0
    
    for year in range(1, fund_life_years + 1):
        # Capital calls front-loaded
        if year <= deploy_years:
            call_pct = 0.30 if year == 1 else 0.25 if year == 2 else 0.25 / (deploy_years - 2)
            call = commitment * min(call_pct, (commitment - called) / commitment)
        else:
            call = 0
        
        # Distributions back-loaded (exponential ramp)
        if year >= 3:
            total_target = commitment * target_tvpi
            dist_weight = (year - 2) ** 2
            total_weight = sum((y - 2) ** 2 for y in range(3, fund_life_years + 1))
            dist = total_target * dist_weight / total_weight
        else:
            dist = 0
        
        called += call
        distributed += dist
        net = distributed - called
        
        projections.append({
            "year": year,
            "capital_call": round(call, 2),
            "distribution": round(dist, 2),
            "cumulative_called": round(called, 2),
            "cumulative_distributed": round(distributed, 2),
            "net_position": round(net, 2),
            "dpi": round(distributed / called, 4) if called > 0 else 0
        })
    
    return {
        "commitment": commitment,
        "target_tvpi": target_tvpi,
        "fund_life_years": fund_life_years,
        "j_curve_trough_year": next(
            (p["year"] for p in projections if p["year"] > 1 and 
             p["net_position"] > projections[p["year"] - 2]["net_position"]),
            deploy_years
        ),
        "projections": projections
    }
