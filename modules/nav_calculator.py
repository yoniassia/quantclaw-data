"""
NAV Calculator — Fund-level daily Net Asset Value computation.

Computes NAV per share, tracks subscriptions/redemptions, handles
management and performance fees (2/20 with high-water mark),
and provides NAV time-series analytics.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import math


def calculate_nav(
    total_assets: float,
    total_liabilities: float,
    shares_outstanding: float
) -> Dict[str, float]:
    """
    Calculate Net Asset Value per share.
    
    Args:
        total_assets: Total fund assets (cash + investments at market value)
        total_liabilities: Total fund liabilities (payables, accrued fees)
        shares_outstanding: Total shares/units outstanding
    
    Returns:
        NAV metrics
    """
    net_assets = total_assets - total_liabilities
    nav_per_share = net_assets / shares_outstanding if shares_outstanding > 0 else 0
    
    return {
        'total_assets': round(total_assets, 2),
        'total_liabilities': round(total_liabilities, 2),
        'net_assets': round(net_assets, 2),
        'shares_outstanding': round(shares_outstanding, 6),
        'nav_per_share': round(nav_per_share, 6)
    }


def accrue_management_fee(
    net_assets: float,
    annual_rate: float = 0.02,
    days_in_period: int = 1,
    days_in_year: int = 365
) -> float:
    """
    Accrue management fee for a period.
    
    Args:
        net_assets: Current net assets
        annual_rate: Annual management fee rate (default 2%)
        days_in_period: Days to accrue
        days_in_year: Days in year convention
    
    Returns:
        Accrued management fee amount
    """
    daily_rate = annual_rate / days_in_year
    return round(net_assets * daily_rate * days_in_period, 2)


def calculate_performance_fee(
    current_nav: float,
    high_water_mark: float,
    shares_outstanding: float,
    incentive_rate: float = 0.20,
    hurdle_rate: float = 0.0
) -> Dict[str, float]:
    """
    Calculate performance fee with high-water mark and optional hurdle.
    
    Args:
        current_nav: Current NAV per share
        high_water_mark: Previous high-water mark NAV per share
        shares_outstanding: Shares outstanding
        incentive_rate: Performance fee rate (default 20%)
        hurdle_rate: Annual hurdle rate (default 0%)
    
    Returns:
        Performance fee details
    """
    # Adjusted HWM with hurdle
    adjusted_hwm = high_water_mark * (1 + hurdle_rate)
    
    # Performance fee only on gains above HWM
    gain_per_share = max(0, current_nav - adjusted_hwm)
    fee_per_share = gain_per_share * incentive_rate
    total_fee = fee_per_share * shares_outstanding
    
    new_hwm = max(high_water_mark, current_nav)
    
    return {
        'gain_per_share': round(gain_per_share, 6),
        'fee_per_share': round(fee_per_share, 6),
        'total_fee': round(total_fee, 2),
        'new_high_water_mark': round(new_hwm, 6),
        'above_hwm': current_nav > adjusted_hwm
    }


def process_subscription(
    current_nav_per_share: float,
    subscription_amount: float,
    current_shares: float,
    entry_fee_pct: float = 0.0
) -> Dict[str, float]:
    """
    Process a new subscription (capital inflow).
    
    Args:
        current_nav_per_share: Current NAV per share
        subscription_amount: Cash amount being subscribed
        current_shares: Current shares outstanding
        entry_fee_pct: Entry/load fee percentage
    
    Returns:
        Subscription details
    """
    entry_fee = subscription_amount * entry_fee_pct / 100
    net_amount = subscription_amount - entry_fee
    
    new_shares = net_amount / current_nav_per_share if current_nav_per_share > 0 else 0
    
    return {
        'subscription_amount': round(subscription_amount, 2),
        'entry_fee': round(entry_fee, 2),
        'net_investment': round(net_amount, 2),
        'shares_issued': round(new_shares, 6),
        'nav_per_share': round(current_nav_per_share, 6),
        'new_total_shares': round(current_shares + new_shares, 6)
    }


def process_redemption(
    current_nav_per_share: float,
    shares_to_redeem: float,
    current_shares: float,
    exit_fee_pct: float = 0.0
) -> Dict[str, float]:
    """
    Process a redemption (capital outflow).
    
    Args:
        current_nav_per_share: Current NAV per share
        shares_to_redeem: Shares being redeemed
        current_shares: Current shares outstanding
        exit_fee_pct: Exit/redemption fee percentage
    
    Returns:
        Redemption details
    """
    gross_proceeds = shares_to_redeem * current_nav_per_share
    exit_fee = gross_proceeds * exit_fee_pct / 100
    net_proceeds = gross_proceeds - exit_fee
    
    return {
        'shares_redeemed': round(shares_to_redeem, 6),
        'gross_proceeds': round(gross_proceeds, 2),
        'exit_fee': round(exit_fee, 2),
        'net_proceeds': round(net_proceeds, 2),
        'nav_per_share': round(current_nav_per_share, 6),
        'new_total_shares': round(current_shares - shares_to_redeem, 6)
    }


def nav_time_series_analytics(
    nav_series: List[Dict[str, float]]
) -> Dict[str, float]:
    """
    Compute analytics on NAV time series.
    
    Args:
        nav_series: List of dicts with 'date' (str) and 'nav' (float)
    
    Returns:
        Performance and risk metrics
    """
    if len(nav_series) < 2:
        return {}
    
    navs = [entry['nav'] for entry in nav_series]
    returns = [(navs[i] - navs[i-1]) / navs[i-1] for i in range(1, len(navs))]
    
    total_return = (navs[-1] / navs[0] - 1) * 100
    
    # Annualize (assume daily)
    n_days = len(returns)
    ann_factor = 252 / n_days if n_days > 0 else 1
    ann_return = ((1 + total_return / 100) ** ann_factor - 1) * 100
    
    avg_ret = sum(returns) / len(returns)
    std_ret = math.sqrt(sum((r - avg_ret) ** 2 for r in returns) / max(1, len(returns) - 1))
    ann_vol = std_ret * math.sqrt(252) * 100
    
    sharpe = (ann_return - 2.0) / ann_vol if ann_vol > 0 else 0  # Assume 2% risk-free
    
    # Max drawdown
    peak = navs[0]
    max_dd = 0
    for nav in navs:
        peak = max(peak, nav)
        dd = (peak - nav) / peak
        max_dd = max(max_dd, dd)
    
    return {
        'total_return_pct': round(total_return, 2),
        'annualized_return_pct': round(ann_return, 2),
        'annualized_volatility_pct': round(ann_vol, 2),
        'sharpe_ratio': round(sharpe, 2),
        'max_drawdown_pct': round(max_dd * 100, 2),
        'start_nav': round(navs[0], 4),
        'end_nav': round(navs[-1], 4),
        'high_nav': round(max(navs), 4),
        'low_nav': round(min(navs), 4),
        'trading_days': n_days
    }
