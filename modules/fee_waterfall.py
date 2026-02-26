"""Fee Waterfall Calculator — Models hedge fund fee structures including 2/20,
hurdle rates, high-water marks, clawback provisions, and crystallization frequencies.
Computes net-of-fee returns for LPs across complex waterfall structures."""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


def calculate_management_fee(nav: float, mgmt_fee_rate: float = 0.02,
                              period_days: int = 365) -> Dict:
    """Calculate management fee for a given NAV and period.
    
    Args:
        nav: Net asset value
        mgmt_fee_rate: Annual management fee rate (default 2%)
        period_days: Number of days in the period
    
    Returns:
        Dict with fee amount, daily rate, and post-fee NAV
    """
    daily_rate = mgmt_fee_rate / 365
    fee = nav * daily_rate * period_days
    return {
        "nav": nav,
        "mgmt_fee_rate": mgmt_fee_rate,
        "period_days": period_days,
        "daily_rate": round(daily_rate, 8),
        "fee_amount": round(fee, 2),
        "post_fee_nav": round(nav - fee, 2)
    }


def calculate_performance_fee(starting_nav: float, ending_nav: float,
                                perf_fee_rate: float = 0.20,
                                hurdle_rate: float = 0.0,
                                high_water_mark: Optional[float] = None,
                                crystallization: str = "annual") -> Dict:
    """Calculate performance/incentive fee with hurdle and HWM.
    
    Args:
        starting_nav: NAV at start of period
        ending_nav: NAV at end of period (before perf fee)
        perf_fee_rate: Performance fee rate (default 20%)
        hurdle_rate: Minimum return before perf fee applies
        high_water_mark: Previous high-water mark (None = no HWM)
        crystallization: 'annual', 'quarterly', 'monthly'
    
    Returns:
        Dict with gain, hurdle amount, fee-eligible gain, fee, new HWM
    """
    gross_gain = ending_nav - starting_nav
    gross_return = gross_gain / starting_nav if starting_nav > 0 else 0
    
    hurdle_amount = starting_nav * hurdle_rate
    hwm_threshold = max(starting_nav, high_water_mark or 0)
    
    # Gain above both hurdle and HWM
    effective_base = max(starting_nav + hurdle_amount, hwm_threshold)
    fee_eligible_gain = max(0, ending_nav - effective_base)
    
    perf_fee = fee_eligible_gain * perf_fee_rate
    new_hwm = max(ending_nav - perf_fee, high_water_mark or 0)
    
    return {
        "starting_nav": starting_nav,
        "ending_nav": ending_nav,
        "gross_gain": round(gross_gain, 2),
        "gross_return_pct": round(gross_return * 100, 4),
        "hurdle_rate": hurdle_rate,
        "hurdle_amount": round(hurdle_amount, 2),
        "high_water_mark": high_water_mark,
        "effective_base": round(effective_base, 2),
        "fee_eligible_gain": round(fee_eligible_gain, 2),
        "performance_fee": round(perf_fee, 2),
        "net_nav": round(ending_nav - perf_fee, 2),
        "new_high_water_mark": round(new_hwm, 2),
        "crystallization": crystallization
    }


def full_fee_waterfall(periods: List[Dict], mgmt_fee_rate: float = 0.02,
                        perf_fee_rate: float = 0.20, hurdle_rate: float = 0.0,
                        use_hwm: bool = True, clawback: bool = False) -> Dict:
    """Run a multi-period fee waterfall simulation.
    
    Args:
        periods: List of dicts with 'ending_nav' and optional 'days' per period
        mgmt_fee_rate: Annual management fee rate
        perf_fee_rate: Performance fee rate
        hurdle_rate: Hurdle rate per period
        use_hwm: Whether to apply high-water mark
        clawback: Whether GP clawback applies
    
    Returns:
        Complete waterfall breakdown per period and totals
    """
    results = []
    hwm = None
    total_mgmt_fees = 0
    total_perf_fees = 0
    current_nav = periods[0].get("starting_nav", 100_000_000)
    cumulative_perf_fees = 0
    cumulative_gains = 0
    
    for i, period in enumerate(periods):
        days = period.get("days", 365)
        ending_nav_gross = period["ending_nav"]
        
        # Management fee first
        mgmt = calculate_management_fee(current_nav, mgmt_fee_rate, days)
        nav_after_mgmt = ending_nav_gross - mgmt["fee_amount"]
        
        # Performance fee
        perf = calculate_performance_fee(
            current_nav, nav_after_mgmt, perf_fee_rate,
            hurdle_rate, hwm if use_hwm else None
        )
        
        # Clawback check
        clawback_amount = 0
        if clawback:
            cumulative_gains += (nav_after_mgmt - current_nav)
            cumulative_perf_fees += perf["performance_fee"]
            max_cumulative_fee = max(0, cumulative_gains * perf_fee_rate)
            if cumulative_perf_fees > max_cumulative_fee:
                clawback_amount = cumulative_perf_fees - max_cumulative_fee
                cumulative_perf_fees = max_cumulative_fee
        
        total_mgmt_fees += mgmt["fee_amount"]
        total_perf_fees += perf["performance_fee"] - clawback_amount
        
        if use_hwm:
            hwm = perf["new_high_water_mark"]
        
        current_nav = perf["net_nav"] + clawback_amount
        
        results.append({
            "period": i + 1,
            "gross_ending_nav": ending_nav_gross,
            "management_fee": mgmt["fee_amount"],
            "performance_fee": perf["performance_fee"],
            "clawback": round(clawback_amount, 2),
            "net_fee": round(mgmt["fee_amount"] + perf["performance_fee"] - clawback_amount, 2),
            "net_nav": round(current_nav, 2),
            "high_water_mark": round(hwm, 2) if hwm else None
        })
    
    initial_nav = periods[0].get("starting_nav", 100_000_000)
    gross_return = (periods[-1]["ending_nav"] / initial_nav - 1) * 100
    net_return = (current_nav / initial_nav - 1) * 100
    fee_drag = gross_return - net_return
    
    return {
        "periods": results,
        "summary": {
            "total_management_fees": round(total_mgmt_fees, 2),
            "total_performance_fees": round(total_perf_fees, 2),
            "total_fees": round(total_mgmt_fees + total_perf_fees, 2),
            "gross_return_pct": round(gross_return, 4),
            "net_return_pct": round(net_return, 4),
            "fee_drag_pct": round(fee_drag, 4),
            "final_nav": round(current_nav, 2)
        },
        "structure": {
            "mgmt_fee_rate": mgmt_fee_rate,
            "perf_fee_rate": perf_fee_rate,
            "hurdle_rate": hurdle_rate,
            "high_water_mark": use_hwm,
            "clawback": clawback
        }
    }


def compare_fee_structures(gross_returns: List[float],
                            structures: List[Dict]) -> Dict:
    """Compare net returns across different fee structures.
    
    Args:
        gross_returns: List of period gross returns as multipliers (e.g., 1.10 = +10%)
        structures: List of fee structure dicts with mgmt_fee, perf_fee, hurdle, hwm keys
    
    Returns:
        Comparison table of net returns per structure
    """
    initial = 100_000_000
    comparisons = []
    
    for struct in structures:
        periods = []
        nav = initial
        for ret in gross_returns:
            nav *= ret
            periods.append({"ending_nav": nav})
        periods[0]["starting_nav"] = initial
        
        result = full_fee_waterfall(
            periods,
            mgmt_fee_rate=struct.get("mgmt_fee", 0.02),
            perf_fee_rate=struct.get("perf_fee", 0.20),
            hurdle_rate=struct.get("hurdle", 0.0),
            use_hwm=struct.get("hwm", True)
        )
        
        comparisons.append({
            "label": struct.get("label", "Unknown"),
            "total_fees": result["summary"]["total_fees"],
            "net_return_pct": result["summary"]["net_return_pct"],
            "fee_drag_pct": result["summary"]["fee_drag_pct"]
        })
    
    return {
        "initial_investment": initial,
        "gross_returns": gross_returns,
        "comparisons": comparisons
    }
