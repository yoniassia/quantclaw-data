"""
Multi-Account Allocation Engine — GIPS-compliant trade allocation across accounts.

Implements pre-trade and post-trade allocation methods for managing multiple
accounts/funds with fairness guarantees. Supports pro-rata, step-out,
and waterfall allocation strategies.
"""

from typing import Dict, List, Optional, Tuple
import math


def pro_rata_allocation(
    total_shares: int,
    account_targets: Dict[str, float],
    min_lot_size: int = 1
) -> Dict[str, int]:
    """
    Pro-rata allocation based on account target weights.
    
    Distributes filled shares proportionally to each account's target weight,
    respecting minimum lot sizes. Residual shares go to largest accounts first.
    
    Args:
        total_shares: Total shares to allocate
        account_targets: Dict of {account_id: target_weight} (weights sum to 1)
        min_lot_size: Minimum allocation unit (default 1 share)
    
    Returns:
        Dict of {account_id: allocated_shares}
    """
    if not account_targets or total_shares <= 0:
        return {acc: 0 for acc in account_targets}
    
    # Normalize weights
    total_weight = sum(account_targets.values())
    if total_weight <= 0:
        return {acc: 0 for acc in account_targets}
    
    weights = {acc: w / total_weight for acc, w in account_targets.items()}
    
    # Initial allocation (floor)
    raw = {acc: w * total_shares for acc, w in weights.items()}
    floored = {acc: int(math.floor(r / min_lot_size) * min_lot_size) for acc, r in raw.items()}
    
    # Distribute residual
    allocated = sum(floored.values())
    residual = total_shares - allocated
    
    # Sort by fractional remainder (largest first)
    remainders = {acc: raw[acc] - floored[acc] for acc in account_targets}
    sorted_accs = sorted(remainders.keys(), key=lambda a: remainders[a], reverse=True)
    
    i = 0
    while residual >= min_lot_size and i < len(sorted_accs):
        floored[sorted_accs[i]] += min_lot_size
        residual -= min_lot_size
        i += 1
    
    return floored


def average_price_allocation(
    fills: List[Dict[str, float]],
    account_shares: Dict[str, int]
) -> Dict[str, float]:
    """
    Compute average price per account given fills and allocations.
    
    GIPS requires accounts receive the same average price when filled
    from the same order block.
    
    Args:
        fills: List of dicts with 'price' and 'shares'
        account_shares: Dict of {account_id: shares_allocated}
    
    Returns:
        Dict of {account_id: average_price} (same for all in block trade)
    """
    if not fills:
        return {acc: 0.0 for acc in account_shares}
    
    # Block average price
    total_cost = sum(f['price'] * f['shares'] for f in fills)
    total_shares = sum(f['shares'] for f in fills)
    
    if total_shares <= 0:
        return {acc: 0.0 for acc in account_shares}
    
    avg_price = total_cost / total_shares
    
    # All accounts get same average price (GIPS compliant)
    return {acc: round(avg_price, 6) for acc in account_shares}


def waterfall_allocation(
    total_shares: int,
    accounts: List[Dict[str, any]],
    min_lot_size: int = 100
) -> Dict[str, int]:
    """
    Waterfall allocation: fill accounts by priority until exhausted.
    
    Higher priority accounts get filled first. Useful for model portfolio
    rebalancing where some accounts need larger fills.
    
    Args:
        total_shares: Total shares available
        accounts: List of dicts with 'id', 'priority' (1=highest), 'target_shares'
        min_lot_size: Minimum lot size
    
    Returns:
        Dict of {account_id: shares_allocated}
    """
    result = {}
    remaining = total_shares
    
    # Sort by priority (1 = highest)
    sorted_accs = sorted(accounts, key=lambda a: a.get('priority', 99))
    
    for acc in sorted_accs:
        acc_id = acc['id']
        target = acc.get('target_shares', 0)
        
        allocatable = min(target, remaining)
        allocatable = int(math.floor(allocatable / min_lot_size) * min_lot_size)
        
        result[acc_id] = allocatable
        remaining -= allocatable
        
        if remaining <= 0:
            break
    
    # Zero-fill remaining accounts
    for acc in sorted_accs:
        if acc['id'] not in result:
            result[acc['id']] = 0
    
    return result


def allocation_fairness_check(
    allocation: Dict[str, int],
    target_weights: Dict[str, float],
    total_shares: int,
    tolerance_pct: float = 5.0
) -> Dict[str, any]:
    """
    Check allocation fairness vs target weights.
    
    Args:
        allocation: Actual allocated shares per account
        target_weights: Target weights per account
        total_shares: Total order shares
        tolerance_pct: Acceptable deviation percentage
    
    Returns:
        Fairness report with deviations and pass/fail
    """
    total_weight = sum(target_weights.values())
    
    results = {}
    all_pass = True
    
    for acc_id in target_weights:
        target_pct = (target_weights[acc_id] / total_weight) * 100
        actual_shares = allocation.get(acc_id, 0)
        actual_pct = (actual_shares / total_shares * 100) if total_shares > 0 else 0
        deviation = actual_pct - target_pct
        passed = abs(deviation) <= tolerance_pct
        
        if not passed:
            all_pass = False
        
        results[acc_id] = {
            'target_pct': round(target_pct, 2),
            'actual_pct': round(actual_pct, 2),
            'deviation_pct': round(deviation, 2),
            'shares': actual_shares,
            'pass': passed
        }
    
    return {
        'accounts': results,
        'overall_pass': all_pass,
        'max_deviation': round(max(abs(r['deviation_pct']) for r in results.values()), 2) if results else 0
    }


def rebalance_allocation(
    current_holdings: Dict[str, Dict[str, float]],
    model_weights: Dict[str, float],
    total_nav: float
) -> Dict[str, Dict[str, float]]:
    """
    Calculate rebalance trades needed to match model portfolio.
    
    Args:
        current_holdings: {account_id: {ticker: market_value}}
        model_weights: {ticker: target_weight}
        total_nav: Total NAV across all accounts
    
    Returns:
        {account_id: {ticker: trade_value}} (positive=buy, negative=sell)
    """
    result = {}
    
    for acc_id, holdings in current_holdings.items():
        acc_nav = sum(holdings.values())
        if acc_nav <= 0:
            continue
        
        trades = {}
        for ticker, target_w in model_weights.items():
            current_val = holdings.get(ticker, 0)
            target_val = acc_nav * target_w
            trade_val = target_val - current_val
            
            if abs(trade_val) > 0.01:
                trades[ticker] = round(trade_val, 2)
        
        # Sell positions not in model
        for ticker, val in holdings.items():
            if ticker not in model_weights and val > 0:
                trades[ticker] = -round(val, 2)
        
        result[acc_id] = trades
    
    return result
