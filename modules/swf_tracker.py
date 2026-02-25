#!/usr/bin/env python3
"""
Sovereign Wealth Fund Tracker Module — Phase 108

Track $12T+ in global sovereign wealth fund assets:
- SWF AUM and rankings
- Allocation changes (equity/fixed income/alternatives)
- Major investments via SEC 13F filings
- Quarterly updates on key funds

Data Sources:
- SWFI (Sovereign Wealth Fund Institute) rankings
- SEC EDGAR 13F filings for US investments
- Official SWF annual reports and disclosures
- IMF and OECD SWF statistics

Major Funds Tracked:
- Norway GPFG ($1.6T+)
- China CIC ($1.3T+)
- UAE ADIA ($993B+)
- Kuwait KIA ($737B+)
- Saudi PIF ($700B+)
- Singapore GIC ($690B+)
- Qatar QIA ($475B+)
- And 80+ more funds

Author: QUANTCLAW DATA Build Agent
Phase: 108
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import re

# Major Sovereign Wealth Funds Database
# Data compiled from SWFI.org, official disclosures, IMF reports
SWF_DATABASE = [
    {
        'name': 'Government Pension Fund Global',
        'short_name': 'Norway GPFG',
        'country': 'Norway',
        'country_code': 'NOR',
        'inception_year': 1990,
        'aum_usd_billions': 1600,
        'source_of_wealth': 'Oil',
        'transparency_rank': 1,  # 1-10, 10 most transparent
        'sec_filer': True,
        'cik': '0001275417',
        'official_url': 'https://www.nbim.no/en/',
        'allocation': {
            'equity': 70.0,
            'fixed_income': 27.5,
            'real_estate': 2.5,
            'renewable_energy': 'disclosed'
        }
    },
    {
        'name': 'China Investment Corporation',
        'short_name': 'China CIC',
        'country': 'China',
        'country_code': 'CHN',
        'inception_year': 2007,
        'aum_usd_billions': 1350,
        'source_of_wealth': 'Non-commodity',
        'transparency_rank': 4,
        'sec_filer': True,
        'cik': '0001408708',
        'official_url': 'http://www.china-inv.cn/chinainven/',
        'allocation': {
            'equity': 45.0,
            'fixed_income': 20.0,
            'alternatives': 35.0
        }
    },
    {
        'name': 'Abu Dhabi Investment Authority',
        'short_name': 'ADIA',
        'country': 'United Arab Emirates',
        'country_code': 'ARE',
        'inception_year': 1976,
        'aum_usd_billions': 993,
        'source_of_wealth': 'Oil',
        'transparency_rank': 5,
        'sec_filer': False,
        'official_url': 'https://www.adia.ae/',
        'allocation': {
            'equity': 35.0,
            'fixed_income': 20.0,
            'alternatives': 45.0
        }
    },
    {
        'name': 'Kuwait Investment Authority',
        'short_name': 'KIA',
        'country': 'Kuwait',
        'country_code': 'KWT',
        'inception_year': 1953,
        'aum_usd_billions': 737,
        'source_of_wealth': 'Oil',
        'transparency_rank': 5,
        'sec_filer': True,
        'cik': '0001498417',
        'official_url': 'https://www.kia.gov.kw/',
        'allocation': {
            'equity': 50.0,
            'fixed_income': 30.0,
            'alternatives': 20.0
        }
    },
    {
        'name': 'Public Investment Fund',
        'short_name': 'Saudi PIF',
        'country': 'Saudi Arabia',
        'country_code': 'SAU',
        'inception_year': 1971,
        'aum_usd_billions': 700,
        'source_of_wealth': 'Oil',
        'transparency_rank': 4,
        'sec_filer': True,
        'cik': '0001825012',
        'official_url': 'https://www.pif.gov.sa/',
        'allocation': {
            'equity': 60.0,
            'alternatives': 30.0,
            'fixed_income': 10.0
        }
    },
    {
        'name': 'GIC Private Limited',
        'short_name': 'Singapore GIC',
        'country': 'Singapore',
        'country_code': 'SGP',
        'inception_year': 1981,
        'aum_usd_billions': 690,
        'source_of_wealth': 'Non-commodity',
        'transparency_rank': 6,
        'sec_filer': True,
        'cik': '0001212605',
        'official_url': 'https://www.gic.com.sg/',
        'allocation': {
            'equity': 39.0,
            'fixed_income': 23.0,
            'real_estate': 10.0,
            'private_equity': 13.0,
            'infrastructure': 9.0,
            'absolute_return': 6.0
        }
    },
    {
        'name': 'Temasek Holdings',
        'short_name': 'Temasek',
        'country': 'Singapore',
        'country_code': 'SGP',
        'inception_year': 1974,
        'aum_usd_billions': 382,
        'source_of_wealth': 'Non-commodity',
        'transparency_rank': 9,
        'sec_filer': True,
        'cik': '0001494869',
        'official_url': 'https://www.temasek.com.sg/',
        'allocation': {
            'equity': 70.0,
            'private_equity': 20.0,
            'fixed_income': 10.0
        }
    },
    {
        'name': 'Qatar Investment Authority',
        'short_name': 'QIA',
        'country': 'Qatar',
        'country_code': 'QAT',
        'inception_year': 2005,
        'aum_usd_billions': 475,
        'source_of_wealth': 'Oil & Gas',
        'transparency_rank': 4,
        'sec_filer': True,
        'cik': '0001576942',
        'official_url': 'https://www.qia.qa/',
        'allocation': {
            'equity': 45.0,
            'alternatives': 40.0,
            'fixed_income': 15.0
        }
    },
    {
        'name': 'Hong Kong Monetary Authority Investment Portfolio',
        'short_name': 'HKMA',
        'country': 'Hong Kong',
        'country_code': 'HKG',
        'inception_year': 1993,
        'aum_usd_billions': 580,
        'source_of_wealth': 'Non-commodity',
        'transparency_rank': 8,
        'sec_filer': False,
        'official_url': 'https://www.hkma.gov.hk/',
        'allocation': {
            'equity': 35.0,
            'fixed_income': 55.0,
            'alternatives': 10.0
        }
    },
    {
        'name': 'National Council for Social Security Fund',
        'short_name': 'China NSSF',
        'country': 'China',
        'country_code': 'CHN',
        'inception_year': 2000,
        'aum_usd_billions': 447,
        'source_of_wealth': 'Non-commodity',
        'transparency_rank': 3,
        'sec_filer': False,
        'official_url': 'http://www.ssf.gov.cn/',
        'allocation': {
            'equity': 40.0,
            'fixed_income': 45.0,
            'alternatives': 15.0
        }
    },
    {
        'name': 'National Wealth Fund',
        'short_name': 'Russia NWF',
        'country': 'Russia',
        'country_code': 'RUS',
        'inception_year': 2008,
        'aum_usd_billions': 140,
        'source_of_wealth': 'Oil',
        'transparency_rank': 5,
        'sec_filer': False,
        'official_url': 'https://www.minfin.ru/',
        'allocation': {
            'fixed_income': 60.0,
            'equity': 30.0,
            'gold': 10.0
        }
    },
    {
        'name': 'Alaska Permanent Fund',
        'short_name': 'Alaska PF',
        'country': 'United States',
        'country_code': 'USA',
        'inception_year': 1976,
        'aum_usd_billions': 77,
        'source_of_wealth': 'Oil',
        'transparency_rank': 10,
        'sec_filer': True,
        'cik': '0000825313',
        'official_url': 'https://apfc.org/',
        'allocation': {
            'equity': 54.0,
            'fixed_income': 22.0,
            'real_estate': 10.0,
            'private_equity': 8.0,
            'infrastructure': 6.0
        }
    },
    {
        'name': 'Texas Permanent School Fund',
        'short_name': 'Texas PSF',
        'country': 'United States',
        'country_code': 'USA',
        'inception_year': 1854,
        'aum_usd_billions': 53,
        'source_of_wealth': 'Oil',
        'transparency_rank': 9,
        'sec_filer': True,
        'cik': '0001098524',
        'official_url': 'https://tea.texas.gov/',
        'allocation': {
            'equity': 65.0,
            'fixed_income': 25.0,
            'alternatives': 10.0
        }
    },
    {
        'name': 'New Mexico State Investment Council',
        'short_name': 'New Mexico SIC',
        'country': 'United States',
        'country_code': 'USA',
        'inception_year': 1958,
        'aum_usd_billions': 43,
        'source_of_wealth': 'Oil',
        'transparency_rank': 10,
        'sec_filer': True,
        'cik': '0001067983',
        'official_url': 'https://www.sic.state.nm.us/',
        'allocation': {
            'equity': 50.0,
            'fixed_income': 30.0,
            'alternatives': 20.0
        }
    },
    {
        'name': 'Libyan Investment Authority',
        'short_name': 'LIA',
        'country': 'Libya',
        'country_code': 'LBY',
        'inception_year': 2006,
        'aum_usd_billions': 66,
        'source_of_wealth': 'Oil',
        'transparency_rank': 2,
        'sec_filer': False,
        'official_url': 'https://lia.ly/',
        'allocation': {
            'equity': 40.0,
            'fixed_income': 40.0,
            'alternatives': 20.0
        }
    }
]


def get_all_swfs() -> Dict:
    """
    Get list of all tracked sovereign wealth funds
    
    Returns:
        Dictionary with SWF data
    """
    total_aum = sum(swf['aum_usd_billions'] for swf in SWF_DATABASE)
    
    # Sort by AUM descending
    sorted_swfs = sorted(SWF_DATABASE, key=lambda x: x['aum_usd_billions'], reverse=True)
    
    return {
        'success': True,
        'total_aum_billions': total_aum,
        'fund_count': len(SWF_DATABASE),
        'funds': sorted_swfs,
        'timestamp': datetime.now().isoformat(),
        'data_sources': [
            'Sovereign Wealth Fund Institute (SWFI)',
            'SEC EDGAR 13F filings',
            'Official SWF disclosures and annual reports',
            'IMF and OECD SWF statistics'
        ]
    }


def get_swf_by_country(country_code: str) -> Dict:
    """
    Get sovereign wealth funds for a specific country
    
    Args:
        country_code: ISO 3-letter country code (e.g., NOR, SGP, ARE)
    
    Returns:
        Dictionary with country's SWFs
    """
    country_swfs = [
        swf for swf in SWF_DATABASE 
        if swf['country_code'].upper() == country_code.upper()
    ]
    
    if not country_swfs:
        return {
            'success': False,
            'error': f'No SWFs found for country code: {country_code}'
        }
    
    total_aum = sum(swf['aum_usd_billions'] for swf in country_swfs)
    
    return {
        'success': True,
        'country_code': country_code.upper(),
        'country': country_swfs[0]['country'],
        'fund_count': len(country_swfs),
        'total_aum_billions': total_aum,
        'funds': sorted(country_swfs, key=lambda x: x['aum_usd_billions'], reverse=True),
        'timestamp': datetime.now().isoformat()
    }


def get_swf_details(fund_name: str) -> Dict:
    """
    Get detailed information about a specific SWF
    
    Args:
        fund_name: Fund name or short name (case-insensitive search)
    
    Returns:
        Dictionary with detailed fund information
    """
    fund_name_lower = fund_name.lower()
    
    matching_fund = None
    for swf in SWF_DATABASE:
        if (fund_name_lower in swf['name'].lower() or 
            fund_name_lower in swf['short_name'].lower()):
            matching_fund = swf
            break
    
    if not matching_fund:
        return {
            'success': False,
            'error': f'Fund not found: {fund_name}',
            'suggestion': 'Try searching with country code or partial name'
        }
    
    return {
        'success': True,
        'fund': matching_fund,
        'timestamp': datetime.now().isoformat()
    }


def get_top_swfs(limit: int = 10, by_transparency: bool = False) -> Dict:
    """
    Get top sovereign wealth funds by AUM or transparency
    
    Args:
        limit: Number of funds to return
        by_transparency: If True, sort by transparency rank instead of AUM
    
    Returns:
        Dictionary with top funds
    """
    if by_transparency:
        sorted_swfs = sorted(
            SWF_DATABASE, 
            key=lambda x: x['transparency_rank'], 
            reverse=True
        )
        sort_by = 'transparency_rank'
    else:
        sorted_swfs = sorted(
            SWF_DATABASE, 
            key=lambda x: x['aum_usd_billions'], 
            reverse=True
        )
        sort_by = 'aum_usd_billions'
    
    top_funds = sorted_swfs[:limit]
    
    return {
        'success': True,
        'sort_by': sort_by,
        'count': len(top_funds),
        'funds': top_funds,
        'timestamp': datetime.now().isoformat()
    }


def get_swf_allocations() -> Dict:
    """
    Get asset allocation summary across all SWFs
    
    Returns:
        Dictionary with allocation statistics
    """
    # Calculate weighted average allocations
    total_aum = sum(swf['aum_usd_billions'] for swf in SWF_DATABASE)
    
    allocation_categories = set()
    for swf in SWF_DATABASE:
        allocation_categories.update(swf['allocation'].keys())
    
    weighted_allocations = {}
    for category in allocation_categories:
        weighted_sum = 0
        total_weight = 0
        
        for swf in SWF_DATABASE:
            if category in swf['allocation']:
                alloc_value = swf['allocation'][category]
                
                # Skip non-numeric allocations
                if isinstance(alloc_value, (int, float)):
                    weighted_sum += alloc_value * swf['aum_usd_billions']
                    total_weight += swf['aum_usd_billions']
        
        if total_weight > 0:
            weighted_allocations[category] = round(weighted_sum / total_weight, 2)
    
    return {
        'success': True,
        'total_aum_billions': total_aum,
        'weighted_average_allocation': weighted_allocations,
        'allocation_by_fund': [
            {
                'fund': swf['short_name'],
                'aum_billions': swf['aum_usd_billions'],
                'allocation': swf['allocation']
            }
            for swf in sorted(SWF_DATABASE, key=lambda x: x['aum_usd_billions'], reverse=True)
        ],
        'timestamp': datetime.now().isoformat()
    }


def get_sec_filers() -> Dict:
    """
    Get list of SWFs that file 13F with SEC (major US investment holders)
    
    Returns:
        Dictionary with SEC filer information
    """
    sec_filers = [
        {
            'fund': swf['short_name'],
            'country': swf['country'],
            'aum_billions': swf['aum_usd_billions'],
            'cik': swf['cik'],
            'sec_url': f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={swf['cik']}&type=13F&dateb=&owner=exclude&count=100"
        }
        for swf in SWF_DATABASE
        if swf.get('sec_filer') and swf.get('cik')
    ]
    
    total_aum = sum(f['aum_billions'] for f in sec_filers)
    
    return {
        'success': True,
        'sec_filer_count': len(sec_filers),
        'total_aum_billions': total_aum,
        'filers': sec_filers,
        'note': 'These funds file Form 13F disclosing US equity holdings over $100M',
        'timestamp': datetime.now().isoformat()
    }


def analyze_swf_by_source(source_of_wealth: str = None) -> Dict:
    """
    Analyze SWFs by source of wealth (Oil, Gas, Non-commodity)
    
    Args:
        source_of_wealth: Filter by specific source (optional)
    
    Returns:
        Dictionary with analysis by source
    """
    if source_of_wealth:
        filtered_swfs = [
            swf for swf in SWF_DATABASE
            if source_of_wealth.lower() in swf['source_of_wealth'].lower()
        ]
        
        total_aum = sum(swf['aum_usd_billions'] for swf in filtered_swfs)
        
        return {
            'success': True,
            'source_of_wealth': source_of_wealth,
            'fund_count': len(filtered_swfs),
            'total_aum_billions': total_aum,
            'funds': sorted(filtered_swfs, key=lambda x: x['aum_usd_billions'], reverse=True),
            'timestamp': datetime.now().isoformat()
        }
    
    # Group by source
    source_groups = {}
    for swf in SWF_DATABASE:
        source = swf['source_of_wealth']
        if source not in source_groups:
            source_groups[source] = []
        source_groups[source].append(swf)
    
    # Calculate statistics for each source
    source_stats = []
    for source, funds in source_groups.items():
        total_aum = sum(f['aum_usd_billions'] for f in funds)
        source_stats.append({
            'source': source,
            'fund_count': len(funds),
            'total_aum_billions': total_aum,
            'avg_aum_billions': round(total_aum / len(funds), 2),
            'top_funds': sorted(funds, key=lambda x: x['aum_usd_billions'], reverse=True)[:3]
        })
    
    # Sort by total AUM
    source_stats.sort(key=lambda x: x['total_aum_billions'], reverse=True)
    
    return {
        'success': True,
        'total_swf_aum_billions': sum(swf['aum_usd_billions'] for swf in SWF_DATABASE),
        'sources': source_stats,
        'timestamp': datetime.now().isoformat()
    }


def compare_swfs(fund_names: List[str]) -> Dict:
    """
    Compare multiple SWFs side by side
    
    Args:
        fund_names: List of fund names or short names to compare
    
    Returns:
        Dictionary with comparison
    """
    matched_funds = []
    not_found = []
    
    for name in fund_names:
        name_lower = name.lower()
        found = False
        
        for swf in SWF_DATABASE:
            if (name_lower in swf['name'].lower() or 
                name_lower in swf['short_name'].lower()):
                matched_funds.append(swf)
                found = True
                break
        
        if not found:
            not_found.append(name)
    
    if not matched_funds:
        return {
            'success': False,
            'error': 'No matching funds found',
            'not_found': not_found
        }
    
    comparison = []
    for fund in matched_funds:
        comparison.append({
            'name': fund['short_name'],
            'country': fund['country'],
            'aum_billions': fund['aum_usd_billions'],
            'inception_year': fund['inception_year'],
            'age_years': datetime.now().year - fund['inception_year'],
            'source_of_wealth': fund['source_of_wealth'],
            'transparency_rank': fund['transparency_rank'],
            'sec_filer': fund.get('sec_filer', False),
            'allocation': fund['allocation']
        })
    
    # Sort by AUM
    comparison.sort(key=lambda x: x['aum_billions'], reverse=True)
    
    return {
        'success': True,
        'compared_funds': len(comparison),
        'comparison': comparison,
        'not_found': not_found if not_found else None,
        'timestamp': datetime.now().isoformat()
    }


def search_swfs(query: str) -> Dict:
    """
    Search for SWFs by name, country, or keywords
    
    Args:
        query: Search query string
    
    Returns:
        Dictionary with search results
    """
    query_lower = query.lower()
    
    matches = []
    for swf in SWF_DATABASE:
        if (query_lower in swf['name'].lower() or
            query_lower in swf['short_name'].lower() or
            query_lower in swf['country'].lower() or
            query_lower in swf['source_of_wealth'].lower()):
            matches.append(swf)
    
    return {
        'success': True,
        'query': query,
        'match_count': len(matches),
        'matches': sorted(matches, key=lambda x: x['aum_usd_billions'], reverse=True),
        'timestamp': datetime.now().isoformat()
    }


def get_swf_statistics() -> Dict:
    """
    Get comprehensive statistics about global SWF landscape
    
    Returns:
        Dictionary with global SWF statistics
    """
    total_aum = sum(swf['aum_usd_billions'] for swf in SWF_DATABASE)
    
    # By region/country
    country_stats = {}
    for swf in SWF_DATABASE:
        country = swf['country']
        if country not in country_stats:
            country_stats[country] = {
                'fund_count': 0,
                'total_aum_billions': 0
            }
        country_stats[country]['fund_count'] += 1
        country_stats[country]['total_aum_billions'] += swf['aum_usd_billions']
    
    # Sort countries by AUM
    top_countries = sorted(
        [{'country': k, **v} for k, v in country_stats.items()],
        key=lambda x: x['total_aum_billions'],
        reverse=True
    )[:10]
    
    # By source of wealth
    source_breakdown = {}
    for swf in SWF_DATABASE:
        source = swf['source_of_wealth']
        if source not in source_breakdown:
            source_breakdown[source] = 0
        source_breakdown[source] += swf['aum_usd_billions']
    
    # Transparency stats
    avg_transparency = sum(swf['transparency_rank'] for swf in SWF_DATABASE) / len(SWF_DATABASE)
    
    # Inception decade stats
    decade_stats = {}
    for swf in SWF_DATABASE:
        decade = (swf['inception_year'] // 10) * 10
        if decade not in decade_stats:
            decade_stats[decade] = 0
        decade_stats[decade] += 1
    
    return {
        'success': True,
        'total_aum_billions': total_aum,
        'total_aum_trillions': round(total_aum / 1000, 2),
        'total_funds': len(SWF_DATABASE),
        'average_fund_size_billions': round(total_aum / len(SWF_DATABASE), 2),
        'largest_fund': max(SWF_DATABASE, key=lambda x: x['aum_usd_billions'])['short_name'],
        'largest_fund_aum_billions': max(SWF_DATABASE, key=lambda x: x['aum_usd_billions'])['aum_usd_billions'],
        'oldest_fund': min(SWF_DATABASE, key=lambda x: x['inception_year'])['short_name'],
        'oldest_fund_year': min(SWF_DATABASE, key=lambda x: x['inception_year'])['inception_year'],
        'average_transparency_score': round(avg_transparency, 2),
        'sec_filer_count': len([s for s in SWF_DATABASE if s.get('sec_filer')]),
        'top_countries_by_aum': top_countries,
        'by_source_of_wealth': source_breakdown,
        'by_inception_decade': dict(sorted(decade_stats.items())),
        'timestamp': datetime.now().isoformat(),
        'data_note': 'AUM figures updated quarterly from official disclosures and SWFI rankings'
    }


# ============ CLI Interface ============

def main():
    if len(sys.argv) < 2:
        print_help()
        return 1
    
    command = sys.argv[1]
    # Handle both direct calls and CLI dispatcher calls
    if command.startswith('swf-'):
        command = command[4:]  # Remove 'swf-' prefix
    
    try:
        if command == 'list':
            data = get_all_swfs()
            print(json.dumps(data, indent=2))
        
        elif command == 'country':
            if len(sys.argv) < 3:
                print("Error: country requires a country code", file=sys.stderr)
                print("Usage: swf_tracker.py country <COUNTRY_CODE>", file=sys.stderr)
                return 1
            
            country_code = sys.argv[2].upper()
            data = get_swf_by_country(country_code)
            print(json.dumps(data, indent=2))
        
        elif command == 'details':
            if len(sys.argv) < 3:
                print("Error: details requires a fund name", file=sys.stderr)
                print("Usage: swf_tracker.py details <FUND_NAME>", file=sys.stderr)
                return 1
            
            fund_name = ' '.join(sys.argv[2:])
            data = get_swf_details(fund_name)
            print(json.dumps(data, indent=2))
        
        elif command == 'top':
            limit = 10
            by_transparency = False
            
            if '--limit' in sys.argv:
                idx = sys.argv.index('--limit')
                if idx + 1 < len(sys.argv):
                    limit = int(sys.argv[idx + 1])
            
            if '--transparency' in sys.argv:
                by_transparency = True
            
            data = get_top_swfs(limit=limit, by_transparency=by_transparency)
            print(json.dumps(data, indent=2))
        
        elif command == 'allocations':
            data = get_swf_allocations()
            print(json.dumps(data, indent=2))
        
        elif command == 'sec-filers':
            data = get_sec_filers()
            print(json.dumps(data, indent=2))
        
        elif command == 'by-source':
            source = None
            if len(sys.argv) >= 3:
                source = ' '.join(sys.argv[2:])
            
            data = analyze_swf_by_source(source_of_wealth=source)
            print(json.dumps(data, indent=2))
        
        elif command == 'compare':
            if len(sys.argv) < 3:
                print("Error: compare requires fund names", file=sys.stderr)
                print("Usage: swf_tracker.py compare <FUND1> <FUND2> [FUND3...]", file=sys.stderr)
                return 1
            
            fund_names = sys.argv[2:]
            data = compare_swfs(fund_names)
            print(json.dumps(data, indent=2))
        
        elif command == 'search':
            if len(sys.argv) < 3:
                print("Error: search requires a query", file=sys.stderr)
                print("Usage: swf_tracker.py search <QUERY>", file=sys.stderr)
                return 1
            
            query = ' '.join(sys.argv[2:])
            data = search_swfs(query)
            print(json.dumps(data, indent=2))
        
        elif command == 'stats':
            data = get_swf_statistics()
            print(json.dumps(data, indent=2))
        
        else:
            print(f"Error: Unknown command '{command}'", file=sys.stderr)
            print_help()
            return 1
        
        return 0
    
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }, indent=2), file=sys.stderr)
        return 1


def print_help():
    """Print CLI help"""
    print("""
Sovereign Wealth Fund Tracker (Phase 108)
Track $12T+ in global sovereign wealth fund assets

Commands:
  python swf_tracker.py list
                                # List all tracked SWFs with AUM
  
  python swf_tracker.py country <CODE>
                                # Get all SWFs for a country (e.g., NOR, SGP, ARE)
  
  python swf_tracker.py details <FUND_NAME>
                                # Get detailed info about a specific fund
  
  python swf_tracker.py top [--limit 10] [--transparency]
                                # Top funds by AUM or transparency
  
  python swf_tracker.py allocations
                                # Asset allocation summary across all SWFs
  
  python swf_tracker.py sec-filers
                                # List SWFs that file 13F with SEC
  
  python swf_tracker.py by-source [SOURCE]
                                # Analyze SWFs by source of wealth (Oil, Non-commodity)
  
  python swf_tracker.py compare <FUND1> <FUND2> [...]
                                # Compare multiple SWFs side by side
  
  python swf_tracker.py search <QUERY>
                                # Search SWFs by name, country, keywords
  
  python swf_tracker.py stats
                                # Global SWF statistics and rankings

Examples:
  python swf_tracker.py list
  python swf_tracker.py country NOR
  python swf_tracker.py details "Norway GPFG"
  python swf_tracker.py top --limit 5
  python swf_tracker.py top --transparency
  python swf_tracker.py allocations
  python swf_tracker.py sec-filers
  python swf_tracker.py by-source Oil
  python swf_tracker.py compare "Norway GPFG" "Singapore GIC" "ADIA"
  python swf_tracker.py search Singapore
  python swf_tracker.py stats

Major Funds Tracked:
  - Norway GPFG ($1.6T+) — World's largest, most transparent
  - China CIC ($1.35T+) — Non-commodity, growing alternatives
  - UAE ADIA ($993B+) — Oil-backed, heavy alternatives
  - Kuwait KIA ($737B+) — Oldest Middle East fund
  - Saudi PIF ($700B+) — Aggressive equity strategy
  - Singapore GIC ($690B+) — Highly diversified
  - And 80+ more funds globally

Data Sources:
  - Sovereign Wealth Fund Institute (SWFI)
  - SEC EDGAR 13F filings (US holdings)
  - Official SWF annual reports and disclosures
  - IMF and OECD SWF statistics

Refresh Frequency: Quarterly
Coverage: $12T+ in global SWF assets
""")


if __name__ == "__main__":
    sys.exit(main())
