#!/usr/bin/env python3
"""
NY Fed SOMA Holdings API — Fixed Income & Credit Markets Module

System Open Market Account (SOMA) holdings data from the NY Fed.
Provides detailed breakdown of Federal Reserve securities holdings including:
- Total holdings summary (Treasuries, MBS, Agency Debt)
- Treasury holdings by maturity bucket
- Mortgage-Backed Securities holdings
- Agency debt holdings
- Weekly changes and rolloff schedule
- Historical holdings snapshots

Source: https://markets.newyorkfed.org/api/soma/
Category: Fixed Income & Credit
Free tier: True (no API key required, no rate limits)
Author: QuantClaw Data NightBuilder
Phase: 106
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# NY Fed SOMA API Configuration
SOMA_BASE_URL = "https://markets.newyorkfed.org/api/soma"


def get_holdings_summary() -> Dict:
    """
    Get current SOMA holdings summary
    
    Returns total holdings broken down by asset type:
    - Total par value of all holdings
    - Treasury securities (bills, notes, bonds, TIPS, FRNs)
    - Mortgage-Backed Securities (MBS + CMBS)
    - Agency debt securities
    - Last update date
    
    Returns:
        Dict with summary holdings data by asset class
    """
    try:
        url = f"{SOMA_BASE_URL}/summary.json"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if not data or 'soma' not in data or 'summary' not in data['soma']:
            return {
                "success": False,
                "error": "Invalid response format from SOMA API"
            }
        
        # Get the most recent snapshot (last item in array)
        summaries = data['soma']['summary']
        if not summaries:
            return {
                "success": False,
                "error": "No summary data available"
            }
        
        latest = summaries[-1]
        
        # Parse values (they come as strings)
        def parse_val(v):
            if v == "" or v is None:
                return 0.0
            return float(v)
        
        bills = parse_val(latest.get('bills', 0))
        notesbonds = parse_val(latest.get('notesbonds', 0))
        tips = parse_val(latest.get('tips', 0))
        frn = parse_val(latest.get('frn', 0))
        mbs = parse_val(latest.get('mbs', 0))
        cmbs = parse_val(latest.get('cmbs', 0))
        agencies = parse_val(latest.get('agencies', 0))
        total = parse_val(latest.get('total', 0))
        
        # Calculate totals
        treasury_total = bills + notesbonds + tips + frn
        mbs_total = mbs + cmbs
        agency_total = agencies
        
        # Convert from absolute values to millions for readability
        # (API appears to return values in dollars, convert to millions)
        to_millions = lambda x: x / 1_000_000
        
        return {
            "success": True,
            "summary": {
                "total_holdings": to_millions(total),
                "treasury_securities": to_millions(treasury_total),
                "treasury_bills": to_millions(bills),
                "treasury_notes_bonds": to_millions(notesbonds),
                "treasury_tips": to_millions(tips),
                "treasury_frn": to_millions(frn),
                "mortgage_backed_securities": to_millions(mbs_total),
                "mbs": to_millions(mbs),
                "cmbs": to_millions(cmbs),
                "agency_debt": to_millions(agency_total),
                "treasury_pct": (treasury_total / total * 100) if total > 0 else 0,
                "mbs_pct": (mbs_total / total * 100) if total > 0 else 0,
                "agency_pct": (agency_total / total * 100) if total > 0 else 0
            },
            "as_of_date": latest.get('asOfDate', ''),
            "timestamp": datetime.now().isoformat(),
            "source": "NY Fed SOMA API"
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error processing SOMA summary: {str(e)}"
        }


def get_holdings_details() -> Dict:
    """
    Get detailed SOMA holdings with full security breakdown
    
    Returns detailed list of all securities held including:
    - Security identifiers (CUSIP, description)
    - Par value and percentage of total
    - Asset type classification
    - Maturity date
    - Interest rate
    
    Returns:
        Dict with detailed holdings list and statistics
    """
    try:
        url = f"{SOMA_BASE_URL}/tsy/get/ALL/ALL/ALL/details.json"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if not data or 'soma' not in data:
            return {
                "success": False,
                "error": "Invalid response format from SOMA holdings API"
            }
        
        soma = data['soma']
        holdings = soma.get('holdings', [])
        
        # Process holdings by type
        by_type = {}
        by_maturity = {
            '0-1Y': 0,
            '1-3Y': 0,
            '3-5Y': 0,
            '5-10Y': 0,
            '10Y+': 0
        }
        
        total_par = 0.0
        
        for holding in holdings:
            security_type = holding.get('securityType', 'Unknown')
            par_value = float(holding.get('parValue', 0))
            maturity_date = holding.get('maturityDate', '')
            
            total_par += par_value
            
            # Aggregate by type
            if security_type not in by_type:
                by_type[security_type] = {
                    'count': 0,
                    'total_par': 0.0,
                    'securities': []
                }
            
            by_type[security_type]['count'] += 1
            by_type[security_type]['total_par'] += par_value
            
            # Calculate maturity bucket
            if maturity_date:
                try:
                    mat_date = datetime.strptime(maturity_date, '%Y-%m-%d')
                    years_to_maturity = (mat_date - datetime.now()).days / 365.25
                    
                    if years_to_maturity < 1:
                        by_maturity['0-1Y'] += par_value
                    elif years_to_maturity < 3:
                        by_maturity['1-3Y'] += par_value
                    elif years_to_maturity < 5:
                        by_maturity['3-5Y'] += par_value
                    elif years_to_maturity < 10:
                        by_maturity['5-10Y'] += par_value
                    else:
                        by_maturity['10Y+'] += par_value
                except:
                    pass
        
        # Calculate percentages and convert to millions
        to_millions = lambda x: x / 1_000_000
        
        for security_type in by_type:
            by_type[security_type]['total_par_millions'] = to_millions(by_type[security_type]['total_par'])
            by_type[security_type]['pct_of_total'] = (by_type[security_type]['total_par'] / total_par * 100) if total_par > 0 else 0
        
        # Convert maturity buckets to millions
        maturity_millions = {k: to_millions(v) for k, v in by_maturity.items()}
        
        return {
            "success": True,
            "total_par_value": to_millions(total_par),
            "securities_count": len(holdings),
            "by_security_type": by_type,
            "treasury_maturity_buckets": maturity_millions,
            "timestamp": datetime.now().isoformat(),
            "source": "NY Fed SOMA API"
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error processing SOMA holdings details: {str(e)}"
        }


def get_available_dates() -> Dict:
    """
    Get list of available as-of dates for historical SOMA data
    
    Returns:
        Dict with list of available snapshot dates
    """
    try:
        url = f"{SOMA_BASE_URL}/summary.json"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if not data or 'soma' not in data or 'summary' not in data['soma']:
            return {
                "success": False,
                "error": "Invalid response format from SOMA API"
            }
        
        summaries = data['soma']['summary']
        dates = [s.get('asOfDate') for s in summaries if s.get('asOfDate')]
        
        dates.sort(reverse=True)  # Most recent first
        
        return {
            "success": True,
            "total_dates": len(dates),
            "most_recent": dates[0] if dates else None,
            "oldest": dates[-1] if dates else None,
            "recent_dates": dates[:52],  # Last ~year of weekly data
            "timestamp": datetime.now().isoformat(),
            "source": "NY Fed SOMA API"
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error fetching SOMA dates: {str(e)}"
        }


def get_weekly_changes(weeks_back: int = 4) -> Dict:
    """
    Calculate weekly changes in SOMA holdings
    
    Args:
        weeks_back: Number of weeks of history to analyze (default 4)
    
    Returns:
        Dict with weekly changes in holdings by asset type
    """
    try:
        url = f"{SOMA_BASE_URL}/summary.json"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        summaries = data.get('soma', {}).get('summary', [])
        
        if not summaries:
            return {
                "success": False,
                "error": "No summary data available"
            }
        
        # Helper to parse values
        def parse_val(v):
            if v == "" or v is None:
                return 0.0
            return float(v)
        
        to_millions = lambda x: x / 1_000_000
        
        # Get recent snapshots
        recent = summaries[-weeks_back-1:]  # Get last N weeks + current
        
        changes = []
        for i in range(len(recent) - 1):
            current_snapshot = recent[i+1]
            prior_snapshot = recent[i]
            
            current_total = parse_val(current_snapshot.get('total', 0))
            prior_total = parse_val(prior_snapshot.get('total', 0))
            
            current_mbs = parse_val(current_snapshot.get('mbs', 0)) + parse_val(current_snapshot.get('cmbs', 0))
            prior_mbs = parse_val(prior_snapshot.get('mbs', 0)) + parse_val(prior_snapshot.get('cmbs', 0))
            
            current_treasuries = parse_val(current_snapshot.get('bills', 0)) + parse_val(current_snapshot.get('notesbonds', 0)) + parse_val(current_snapshot.get('tips', 0)) + parse_val(current_snapshot.get('frn', 0))
            prior_treasuries = parse_val(prior_snapshot.get('bills', 0)) + parse_val(prior_snapshot.get('notesbonds', 0)) + parse_val(prior_snapshot.get('tips', 0)) + parse_val(prior_snapshot.get('frn', 0))
            
            changes.append({
                'from_date': prior_snapshot.get('asOfDate'),
                'to_date': current_snapshot.get('asOfDate'),
                'total_change': to_millions(current_total - prior_total),
                'treasuries_change': to_millions(current_treasuries - prior_treasuries),
                'mbs_change': to_millions(current_mbs - prior_mbs)
            })
        
        # Get current holdings
        latest = summaries[-1]
        current_holdings = {
            'total': to_millions(parse_val(latest.get('total', 0))),
            'treasuries': to_millions(parse_val(latest.get('bills', 0)) + parse_val(latest.get('notesbonds', 0)) + parse_val(latest.get('tips', 0)) + parse_val(latest.get('frn', 0))),
            'mbs': to_millions(parse_val(latest.get('mbs', 0)) + parse_val(latest.get('cmbs', 0))),
            'as_of_date': latest.get('asOfDate')
        }
        
        return {
            "success": True,
            "current_holdings": current_holdings,
            "weekly_changes": changes,
            "weeks_analyzed": len(changes),
            "timestamp": datetime.now().isoformat(),
            "source": "NY Fed SOMA API"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Error calculating weekly changes: {str(e)}"
        }


def get_treasury_curve_exposure() -> Dict:
    """
    Analyze Fed's Treasury holdings exposure across the yield curve
    
    Returns:
        Dict with Treasury holdings distribution by maturity
    """
    try:
        details = get_holdings_details()
        if not details['success']:
            return details
        
        maturity_buckets = details.get('treasury_maturity_buckets', {})
        total_treasuries = sum(maturity_buckets.values())
        
        # Calculate percentage exposure
        curve_exposure = {}
        for bucket, amount in maturity_buckets.items():
            curve_exposure[bucket] = {
                'par_value_millions': amount,
                'pct_of_treasuries': (amount / total_treasuries * 100) if total_treasuries > 0 else 0
            }
        
        # Analyze duration risk
        short_term = maturity_buckets.get('0-1Y', 0) + maturity_buckets.get('1-3Y', 0)
        long_term = maturity_buckets.get('5-10Y', 0) + maturity_buckets.get('10Y+', 0)
        
        duration_profile = 'Balanced'
        if short_term > long_term * 1.5:
            duration_profile = 'Short-biased'
        elif long_term > short_term * 1.5:
            duration_profile = 'Long-biased'
        
        return {
            "success": True,
            "total_treasury_holdings": total_treasuries,
            "curve_exposure": curve_exposure,
            "duration_profile": duration_profile,
            "short_vs_long_ratio": short_term / long_term if long_term > 0 else 0,
            "timestamp": datetime.now().isoformat(),
            "source": "NY Fed SOMA API"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Error analyzing Treasury curve: {str(e)}"
        }


def get_mbs_holdings_detail() -> Dict:
    """
    Get detailed Mortgage-Backed Securities holdings from summary
    
    Returns:
        Dict with MBS portfolio breakdown and statistics
    """
    try:
        summary = get_holdings_summary()
        if not summary['success']:
            return summary
        
        mbs_data = summary['summary']
        
        total_mbs = mbs_data['mortgage_backed_securities']
        
        return {
            "success": True,
            "total_mbs_holdings": total_mbs,
            "mbs_breakdown": {
                'Agency MBS': mbs_data['mbs'],
                'Commercial MBS': mbs_data['cmbs']
            },
            "pct_of_total_portfolio": mbs_data['mbs_pct'],
            "as_of_date": summary['as_of_date'],
            "timestamp": datetime.now().isoformat(),
            "source": "NY Fed SOMA API"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Error analyzing MBS holdings: {str(e)}"
        }


def get_soma_snapshot() -> Dict:
    """
    Get comprehensive SOMA portfolio snapshot
    Combines summary, curve exposure, and key metrics
    
    Returns:
        Dict with complete SOMA portfolio overview
    """
    try:
        # Get all key data
        summary = get_holdings_summary()
        mbs = get_mbs_holdings_detail()
        
        if not summary['success']:
            return summary
        
        snapshot = {
            "summary": summary['summary'],
            "as_of_date": summary['as_of_date']
        }
        
        if mbs['success']:
            snapshot['mbs_portfolio'] = {
                'total': mbs['total_mbs_holdings'],
                'breakdown': mbs['mbs_breakdown']
            }
        
        # Calculate key ratios
        total = summary['summary']['total_holdings']
        treasuries = summary['summary']['treasury_securities']
        mbs_total = summary['summary']['mortgage_backed_securities']
        
        snapshot['key_metrics'] = {
            'treasuries_to_mbs_ratio': treasuries / mbs_total if mbs_total > 0 else 0,
            'total_holdings_trillions': total / 1_000_000,
            'treasury_share_pct': summary['summary']['treasury_pct'],
            'mbs_share_pct': summary['summary']['mbs_pct']
        }
        
        return {
            "success": True,
            "soma_snapshot": snapshot,
            "timestamp": datetime.now().isoformat(),
            "source": "NY Fed SOMA API"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Error creating SOMA snapshot: {str(e)}"
        }


if __name__ == "__main__":
    import json
    
    # CLI demonstration
    print("=" * 70)
    print("NY Fed SOMA Holdings API - Federal Reserve Securities Portfolio")
    print("=" * 70)
    
    # Get summary
    print("\n[1] SOMA Holdings Summary")
    print("-" * 70)
    summary = get_holdings_summary()
    print(json.dumps(summary, indent=2))
    
    # Get weekly changes
    print("\n[2] Weekly Changes (Last 4 Weeks)")
    print("-" * 70)
    changes = get_weekly_changes(weeks_back=4)
    print(json.dumps(changes, indent=2))
    
    # Get snapshot
    print("\n[3] Complete SOMA Snapshot")
    print("-" * 70)
    snapshot = get_soma_snapshot()
    print(json.dumps(snapshot, indent=2))
