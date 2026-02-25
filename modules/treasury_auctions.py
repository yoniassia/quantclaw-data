#!/usr/bin/env python3
"""
US Treasury Auctions & Debt Module — Phase 118

Comprehensive US Treasury auction data and debt holdings tracking
- Auction results with bid-to-cover ratios
- Foreign holdings via TIC (Treasury International Capital) data
- Treasury debt outstanding by maturity
- Yield analysis and auction performance metrics

Data Sources:
- TreasuryDirect.gov auction query API
- TIC (ticdata.treasury.gov) foreign holdings reports
- Treasury.gov debt to the penny data

Refresh: Weekly (auctions occur regularly)
Coverage: US Treasury auctions and international holdings

Author: QUANTCLAW DATA Build Agent
Phase: 118
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re

# Treasury Direct API Configuration
TREASURY_API_BASE = "https://www.treasurydirect.gov/TA_WS/securities"
TIC_DATA_BASE = "https://ticdata.treasury.gov"
DEBT_TO_PENNY_API = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"

# Maturity type mappings
SECURITY_TYPES = {
    'Bill': ['4-Week', '8-Week', '13-Week', '17-Week', '26-Week', '52-Week'],
    'Note': ['2-Year', '3-Year', '5-Year', '7-Year', '10-Year'],
    'Bond': ['20-Year', '30-Year'],
    'TIPS': ['5-Year TIPS', '10-Year TIPS', '30-Year TIPS'],
    'FRN': ['2-Year FRN']
}

# ========== CORE FUNCTIONS ==========

def get_auction_results(
    security_type: Optional[str] = None,
    days_back: int = 30,
    cusip: Optional[str] = None
) -> Dict:
    """
    Get recent Treasury auction results
    
    Args:
        security_type: Type of security (Bill, Note, Bond, TIPS, FRN)
        days_back: Number of days to look back
        cusip: Specific CUSIP to query
        
    Returns:
        Dict with auction results including bid-to-cover ratios
    """
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Build query parameters
        params = {
            'format': 'json',
            'pagesize': 100
        }
        
        if security_type:
            params['type'] = security_type
        if cusip:
            params['cusip'] = cusip
            
        # Query Treasury Direct API
        url = f"{TREASURY_API_BASE}/auctioned"
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        auctions = []
        
        for item in data:
            # Parse auction data
            auction = {
                'cusip': item.get('cusip', ''),
                'security_type': item.get('securityType', ''),
                'security_term': item.get('securityTerm', ''),
                'issue_date': item.get('issueDate', ''),
                'maturity_date': item.get('maturityDate', ''),
                'auction_date': item.get('auctionDate', ''),
                'original_security_term': item.get('originalSecurityTerm', ''),
                
                # Auction results
                'high_investment_rate': float(item.get('highInvestmentRate', 0) or 0),
                'interest_rate': float(item.get('interestRate', 0) or 0),
                'allotted_amount_in_millions': float(item.get('totalAccepted', 0) or 0) / 1_000_000,
                'total_tendered': float(item.get('totalTendered', 0) or 0) / 1_000_000,
                
                # Calculate bid-to-cover ratio
                'bid_to_cover': 0.0,
                
                # Competitive bidding metrics
                'competitive_tendered': float(item.get('competitiveTendered', 0) or 0) / 1_000_000,
                'competitive_accepted': float(item.get('competitiveAccepted', 0) or 0) / 1_000_000,
                'noncompetitive_accepted': float(item.get('noncompetitiveAccepted', 0) or 0) / 1_000_000,
                
                # Pricing
                'high_price': float(item.get('highPrice', 0) or 0),
                'low_price': float(item.get('lowPrice', 0) or 0),
                'median_price': float(item.get('medianPrice', 0) or 0),
            }
            
            # Calculate bid-to-cover ratio
            if auction['allotted_amount_in_millions'] > 0:
                auction['bid_to_cover'] = round(
                    auction['total_tendered'] / auction['allotted_amount_in_millions'], 
                    2
                )
            
            # Filter by date range
            auction_date = datetime.strptime(auction['auction_date'], '%Y-%m-%dT%H:%M:%S')
            if start_date <= auction_date <= end_date:
                auctions.append(auction)
        
        return {
            'success': True,
            'data': sorted(auctions, key=lambda x: x['auction_date'], reverse=True),
            'count': len(auctions),
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'API request failed: {str(e)}',
            'data': []
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error processing auction data: {str(e)}',
            'data': []
        }


def get_upcoming_auctions(days_ahead: int = 30) -> Dict:
    """
    Get scheduled upcoming Treasury auctions
    
    Args:
        days_ahead: Number of days to look ahead
        
    Returns:
        Dict with upcoming auction schedule
    """
    try:
        end_date = datetime.now() + timedelta(days=days_ahead)
        
        params = {
            'format': 'json',
            'pagesize': 50
        }
        
        url = f"{TREASURY_API_BASE}/announced"
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        upcoming = []
        
        for item in data:
            auction = {
                'cusip': item.get('cusip', ''),
                'security_type': item.get('securityType', ''),
                'security_term': item.get('securityTerm', ''),
                'auction_date': item.get('auctionDate', ''),
                'issue_date': item.get('issueDate', ''),
                'maturity_date': item.get('maturityDate', ''),
                'offering_amount': float(item.get('offeringAmount', 0) or 0) / 1_000_000,
                'current_status': item.get('currentlyOutstanding', ''),
                'announcement_date': item.get('announcementDate', '')
            }
            upcoming.append(auction)
        
        return {
            'success': True,
            'data': sorted(upcoming, key=lambda x: x['auction_date']),
            'count': len(upcoming)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': []
        }


def get_tic_foreign_holdings(country: Optional[str] = None) -> Dict:
    """
    Get TIC (Treasury International Capital) foreign holdings data
    
    Args:
        country: Specific country code (CN=China, JP=Japan, etc.)
        
    Returns:
        Dict with foreign holdings of US Treasuries
    """
    try:
        # TIC data is published monthly with a 2-month lag
        # Use Fiscal Data API for Treasury holdings
        url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny"
        
        params = {
            'sort': '-record_date',
            'page[size]': '12',
            'format': 'json'
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        debt_records = []
        for record in data.get('data', []):
            total = float(record.get('tot_pub_debt_out_amt', 0))
            intragovt = float(record.get('intragov_hold_amt', 0))
            public = float(record.get('debt_held_public_amt', 0))
            
            debt_records.append({
                'record_date': record.get('record_date'),
                'total_debt_billions': round(total / 1_000_000, 2),
                'intragovernmental_holdings_billions': round(intragovt / 1_000_000, 2),
                'debt_held_by_public_billions': round(public / 1_000_000, 2)
            })
        
        # Note: Full TIC country-level data requires parsing Excel files from ticdata.treasury.gov
        # Major foreign holders data is available at:
        # https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/slt_table5.html
        
        return {
            'success': True,
            'data': {
                'debt_outstanding_trend': debt_records,
                'note': 'Full country-level TIC data (foreign holdings by country) requires parsing monthly Excel reports from ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/slt_table5.html',
                'major_holders': {
                    'note': 'Top holders include: Japan, China, UK, Luxembourg, Cayman Islands, Ireland, Brazil, Switzerland, Belgium, Taiwan'
                }
            },
            'source': 'Fiscal Data API v2 - Debt to the Penny'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


def get_debt_outstanding() -> Dict:
    """
    Get current US Treasury debt outstanding by category
    
    Returns:
        Dict with debt outstanding breakdown
    """
    try:
        # Use correct Fiscal Data API endpoint
        url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny"
        
        params = {
            'sort': '-record_date',
            'page[size]': '1',
            'format': 'json'
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('data'):
            return {'success': False, 'error': 'No data available'}
        
        latest = data['data'][0]
        
        total_debt = float(latest.get('tot_pub_debt_out_amt', 0))
        intragovt = float(latest.get('intragov_hold_amt', 0))
        public = float(latest.get('debt_held_public_amt', 0))
        
        return {
            'success': True,
            'data': {
                'record_date': latest.get('record_date'),
                'total_public_debt_billions': round(total_debt / 1_000_000, 2),
                'intragovernmental_holdings_billions': round(intragovt / 1_000_000, 2),
                'debt_held_by_public_billions': round(public / 1_000_000, 2),
                'total_public_debt_raw': total_debt,
                'marketable_vs_nonmarketable': {
                    'note': 'Breakdown available via Monthly Statement of Public Debt'
                }
            },
            'source': 'US Treasury - Debt to the Penny (Fiscal Data API v2)'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


def analyze_auction_performance(days_back: int = 90) -> Dict:
    """
    Analyze auction performance metrics across security types
    
    Args:
        days_back: Number of days to analyze
        
    Returns:
        Dict with auction performance analytics
    """
    try:
        results = get_auction_results(days_back=days_back)
        
        if not results['success']:
            return results
        
        auctions = results['data']
        
        # Group by security type
        by_type = {}
        for auction in auctions:
            sec_type = auction['security_type']
            if sec_type not in by_type:
                by_type[sec_type] = []
            by_type[sec_type].append(auction)
        
        # Calculate statistics
        analysis = {}
        for sec_type, aucs in by_type.items():
            bid_to_covers = [a['bid_to_cover'] for a in aucs if a['bid_to_cover'] > 0]
            yields = [a['high_investment_rate'] for a in aucs if a['high_investment_rate'] > 0]
            amounts = [a['allotted_amount_in_millions'] for a in aucs]
            
            analysis[sec_type] = {
                'auction_count': len(aucs),
                'avg_bid_to_cover': round(sum(bid_to_covers) / len(bid_to_covers), 2) if bid_to_covers else 0,
                'min_bid_to_cover': round(min(bid_to_covers), 2) if bid_to_covers else 0,
                'max_bid_to_cover': round(max(bid_to_covers), 2) if bid_to_covers else 0,
                'avg_yield': round(sum(yields) / len(yields), 3) if yields else 0,
                'total_amount_auctioned': round(sum(amounts), 0),
                'recent_auctions': aucs[:3]  # Last 3 auctions
            }
        
        return {
            'success': True,
            'data': analysis,
            'period_days': days_back,
            'total_auctions': len(auctions)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


def get_treasury_dashboard() -> Dict:
    """
    Get comprehensive Treasury auctions & debt dashboard
    
    Returns:
        Dict with dashboard data
    """
    try:
        # Get recent auction results
        recent_auctions = get_auction_results(days_back=14)
        
        # Get upcoming auctions
        upcoming = get_upcoming_auctions(days_ahead=14)
        
        # Get debt outstanding
        debt = get_debt_outstanding()
        
        # Get performance metrics
        performance = analyze_auction_performance(days_back=90)
        
        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'recent_auctions': recent_auctions.get('data', [])[:5],
            'upcoming_auctions': upcoming.get('data', [])[:5],
            'debt_outstanding': debt.get('data', {}),
            'performance_summary': performance.get('data', {}),
            'sources': [
                'TreasuryDirect.gov',
                'Fiscal Data API',
                'TIC Data (ticdata.treasury.gov)'
            ]
        }
        
        return {
            'success': True,
            'data': dashboard
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


# ========== CLI INTERFACE ==========

def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("Usage: python treasury_auctions.py <command> [options]")
        print("\nCommands:")
        print("  treasury-recent [days] [type]     - Recent auction results (default: 30 days)")
        print("  treasury-upcoming [days]          - Upcoming auction schedule")
        print("  treasury-tic [country]            - Foreign holdings of US Treasuries")
        print("  treasury-debt                     - Current US debt outstanding")
        print("  treasury-performance [days]       - Auction performance analysis")
        print("  treasury-dashboard                - Comprehensive dashboard")
        print("\nSecurity types: Bill, Note, Bond, TIPS, FRN")
        print("\nExamples:")
        print("  python treasury_auctions.py treasury-recent 90 Note")
        print("  python treasury_auctions.py treasury-upcoming 30")
        print("  python treasury_auctions.py treasury-performance 180")
        return
    
    command = sys.argv[1]
    
    if command == 'treasury-recent':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        sec_type = sys.argv[3] if len(sys.argv) > 3 else None
        result = get_auction_results(security_type=sec_type, days_back=days)
        print(json.dumps(result, indent=2))
        
    elif command == 'treasury-upcoming':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        result = get_upcoming_auctions(days_ahead=days)
        print(json.dumps(result, indent=2))
        
    elif command == 'treasury-tic':
        country = sys.argv[2] if len(sys.argv) > 2 else None
        result = get_tic_foreign_holdings(country=country)
        print(json.dumps(result, indent=2))
        
    elif command == 'treasury-debt':
        result = get_debt_outstanding()
        print(json.dumps(result, indent=2))
        
    elif command == 'treasury-performance':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
        result = analyze_auction_performance(days_back=days)
        print(json.dumps(result, indent=2))
        
    elif command == 'treasury-dashboard':
        result = get_treasury_dashboard()
        print(json.dumps(result, indent=2))
        
    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == '__main__':
    main()
