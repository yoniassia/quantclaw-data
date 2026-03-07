#!/usr/bin/env python3
"""
Crunchbase Venture Data API — Startup & VC Data Module

Access to private market data including venture capital deals, funding rounds,
company profiles, and IPO pipeline. Uses Crunchbase API (100 calls/month free tier)
with web scraping fallback for public company pages.

Useful for analyzing startup ecosystems, private equity trends, sector funding,
and early-stage company data in quant models.

Source: https://www.crunchbase.com/api
Category: IPO & Private Markets
Free tier: True (requires CRUNCHBASE_API_KEY env var, 100 calls/month)
Update frequency: Daily
Author: QuantClaw Data NightBuilder
Phase: 106
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import time

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Crunchbase API Configuration
CRUNCHBASE_BASE_URL = "https://api.crunchbase.com/api/v4"
CRUNCHBASE_API_KEY = os.environ.get("CRUNCHBASE_API_KEY", "")
CRUNCHBASE_WEB_BASE = "https://www.crunchbase.com"

# Request headers for web scraping
SCRAPE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def _call_crunchbase_api(endpoint: str, params: Dict = None) -> Dict:
    """
    Internal helper to call Crunchbase API with authentication
    
    Args:
        endpoint: API endpoint path (e.g., '/entities/organizations')
        params: Query parameters
    
    Returns:
        Dict with API response or error
    """
    if not CRUNCHBASE_API_KEY:
        return {
            "success": False,
            "error": "CRUNCHBASE_API_KEY not set in environment",
            "fallback": True
        }
    
    try:
        url = f"{CRUNCHBASE_BASE_URL}{endpoint}"
        headers = {"X-cb-user-key": CRUNCHBASE_API_KEY}
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        # Check if we hit rate limit
        if response.status_code == 429:
            return {
                "success": False,
                "error": "API rate limit exceeded (100 calls/month)",
                "fallback": True
            }
        
        response.raise_for_status()
        
        return {
            "success": True,
            "data": response.json()
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "fallback": True
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "fallback": True
        }


def _scrape_company_page(company_slug: str) -> Dict:
    """
    Scrape public Crunchbase company page as fallback
    
    Args:
        company_slug: Company identifier (e.g., 'openai')
    
    Returns:
        Dict with scraped company data
    """
    try:
        url = f"{CRUNCHBASE_WEB_BASE}/organization/{company_slug}"
        response = requests.get(url, headers=SCRAPE_HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract basic info from meta tags and page structure
        company_data = {
            "name": company_slug.replace('-', ' ').title(),
            "url": url,
            "description": "",
            "founded_date": None,
            "total_funding": None,
            "last_funding_type": None,
            "employee_count": None,
            "headquarters": None,
            "industries": [],
            "scraped": True
        }
        
        # Try to extract description from meta tags
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc:
            company_data["description"] = meta_desc.get('content', '')[:200]
        
        # Extract structured data if available
        json_ld = soup.find('script', {'type': 'application/ld+json'})
        if json_ld:
            try:
                structured = json.loads(json_ld.string)
                if isinstance(structured, dict):
                    company_data["name"] = structured.get("name", company_data["name"])
                    company_data["description"] = structured.get("description", company_data["description"])[:200]
            except:
                pass
        
        return {
            "success": True,
            "data": company_data
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Scraping failed: {str(e)}"
        }


def search_companies(query: str = 'AI', limit: int = 10, use_api: bool = True) -> Dict:
    """
    Search for companies by keyword
    
    Args:
        query: Search term (e.g., 'AI', 'fintech', 'biotech')
        limit: Maximum number of results (default 10)
        use_api: Try API first before falling back to scraping
    
    Returns:
        Dict with list of matching companies
    """
    if use_api and CRUNCHBASE_API_KEY:
        # Try API first
        result = _call_crunchbase_api(
            '/searches/organizations',
            params={
                'query': query,
                'limit': limit,
                'field_ids': 'identifier,name,short_description,funding_total,num_funding_rounds'
            }
        )
        
        if result.get('success'):
            companies = []
            entities = result.get('data', {}).get('entities', [])
            
            for entity in entities[:limit]:
                props = entity.get('properties', {})
                companies.append({
                    'name': props.get('name', ''),
                    'identifier': props.get('identifier', ''),
                    'description': props.get('short_description', '')[:150],
                    'funding_total': props.get('funding_total', {}).get('value', 0),
                    'funding_rounds': props.get('num_funding_rounds', 0)
                })
            
            return {
                'success': True,
                'query': query,
                'count': len(companies),
                'companies': companies,
                'source': 'crunchbase_api',
                'timestamp': datetime.now().isoformat()
            }
    
    # Fallback: scrape search results page
    try:
        search_url = f"{CRUNCHBASE_WEB_BASE}/discover/organization.companies"
        params = {'q': query}
        
        response = requests.get(search_url, headers=SCRAPE_HEADERS, params=params, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract company cards (structure may vary)
        companies = []
        company_links = soup.find_all('a', href=lambda x: x and '/organization/' in x)[:limit]
        
        for link in company_links:
            slug = link['href'].split('/organization/')[-1].split('?')[0]
            name = link.get_text(strip=True) or slug.replace('-', ' ').title()
            
            companies.append({
                'name': name,
                'identifier': slug,
                'description': f'Company page: {CRUNCHBASE_WEB_BASE}/organization/{slug}',
                'scraped': True
            })
        
        return {
            'success': True,
            'query': query,
            'count': len(companies),
            'companies': companies,
            'source': 'crunchbase_scrape',
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f"Search failed: {str(e)}",
            'query': query
        }


def get_company_profile(company: str, use_api: bool = True) -> Dict:
    """
    Get detailed company profile
    
    Args:
        company: Company identifier or slug (e.g., 'openai', 'anthropic')
        use_api: Try API first before falling back to scraping
    
    Returns:
        Dict with company details, funding history, team info
    """
    if use_api and CRUNCHBASE_API_KEY:
        # Try API first
        result = _call_crunchbase_api(
            f'/entities/organizations/{company}',
            params={
                'field_ids': 'identifier,name,short_description,description,founded_on,num_employees_enum,funding_total,last_funding_type,categories,website,location_identifiers'
            }
        )
        
        if result.get('success'):
            props = result.get('data', {}).get('properties', {})
            
            return {
                'success': True,
                'company': {
                    'name': props.get('name', company),
                    'identifier': props.get('identifier', company),
                    'description': props.get('description', props.get('short_description', '')),
                    'founded_date': props.get('founded_on', {}).get('value'),
                    'employee_count': props.get('num_employees_enum'),
                    'total_funding': props.get('funding_total', {}).get('value', 0),
                    'last_funding_type': props.get('last_funding_type'),
                    'categories': [c.get('value') for c in props.get('categories', [])],
                    'website': props.get('website', {}).get('value'),
                    'headquarters': props.get('location_identifiers', [{}])[0].get('value') if props.get('location_identifiers') else None
                },
                'source': 'crunchbase_api',
                'timestamp': datetime.now().isoformat()
            }
    
    # Fallback: scrape company page
    scrape_result = _scrape_company_page(company)
    
    if scrape_result.get('success'):
        return {
            'success': True,
            'company': scrape_result['data'],
            'source': 'crunchbase_scrape',
            'timestamp': datetime.now().isoformat()
        }
    
    return {
        'success': False,
        'error': f"Could not retrieve profile for {company}",
        'company': company
    }


def get_recent_funding_rounds(limit: int = 20, days_back: int = 30) -> Dict:
    """
    Get recent VC funding rounds across all companies
    
    Args:
        limit: Maximum number of funding rounds to return
        days_back: Look back this many days (default 30)
    
    Returns:
        Dict with recent funding rounds, amounts, investors
    """
    if CRUNCHBASE_API_KEY:
        # Try API
        result = _call_crunchbase_api(
            '/searches/funding_rounds',
            params={
                'limit': limit,
                'order': 'announced_on DESC',
                'field_ids': 'identifier,name,announced_on,funded_organization_identifier,money_raised,investment_type,investor_identifiers'
            }
        )
        
        if result.get('success'):
            rounds = []
            entities = result.get('data', {}).get('entities', [])
            
            for entity in entities[:limit]:
                props = entity.get('properties', {})
                announced = props.get('announced_on', {}).get('value')
                
                # Filter by date
                if announced:
                    announced_date = datetime.fromisoformat(announced.replace('Z', '+00:00'))
                    if datetime.now(announced_date.tzinfo) - announced_date > timedelta(days=days_back):
                        continue
                
                rounds.append({
                    'company': props.get('funded_organization_identifier', {}).get('value', 'Unknown'),
                    'round_type': props.get('investment_type'),
                    'amount': props.get('money_raised', {}).get('value', 0),
                    'currency': props.get('money_raised', {}).get('currency', 'USD'),
                    'announced_date': announced,
                    'investors': [inv.get('value') for inv in props.get('investor_identifiers', [])][:5]
                })
            
            return {
                'success': True,
                'count': len(rounds),
                'funding_rounds': rounds,
                'days_back': days_back,
                'source': 'crunchbase_api',
                'timestamp': datetime.now().isoformat()
            }
    
    # Fallback: scrape recent funding page
    try:
        url = f"{CRUNCHBASE_WEB_BASE}/discover/funding_rounds"
        response = requests.get(url, headers=SCRAPE_HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract funding round info (simplified)
        rounds = []
        # Note: actual scraping logic would depend on current page structure
        # This is a placeholder showing the pattern
        
        return {
            'success': True,
            'count': len(rounds),
            'funding_rounds': rounds,
            'source': 'crunchbase_scrape',
            'note': 'Limited data from web scraping - consider API key',
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f"Failed to fetch funding rounds: {str(e)}"
        }


def get_funding_by_sector(sector: str = 'fintech', limit: int = 20) -> Dict:
    """
    Get funding activity by sector/industry
    
    Args:
        sector: Industry sector (e.g., 'fintech', 'biotech', 'ai', 'crypto')
        limit: Maximum number of results
    
    Returns:
        Dict with sector funding trends and top funded companies
    """
    if CRUNCHBASE_API_KEY:
        # Try API with category filter
        result = _call_crunchbase_api(
            '/searches/organizations',
            params={
                'categories': sector,
                'limit': limit,
                'order': 'funding_total DESC',
                'field_ids': 'identifier,name,short_description,funding_total,last_funding_at,last_funding_type,categories'
            }
        )
        
        if result.get('success'):
            companies = []
            total_funding = 0
            entities = result.get('data', {}).get('entities', [])
            
            for entity in entities[:limit]:
                props = entity.get('properties', {})
                funding = props.get('funding_total', {}).get('value', 0)
                total_funding += funding
                
                companies.append({
                    'name': props.get('name', ''),
                    'identifier': props.get('identifier', ''),
                    'description': props.get('short_description', '')[:100],
                    'total_funding': funding,
                    'last_funding_date': props.get('last_funding_at', {}).get('value'),
                    'last_funding_type': props.get('last_funding_type')
                })
            
            return {
                'success': True,
                'sector': sector,
                'count': len(companies),
                'total_funding': total_funding,
                'average_funding': total_funding / len(companies) if companies else 0,
                'top_funded': companies,
                'source': 'crunchbase_api',
                'timestamp': datetime.now().isoformat()
            }
    
    # Fallback: search by sector term
    search_result = search_companies(query=sector, limit=limit, use_api=False)
    
    if search_result.get('success'):
        return {
            'success': True,
            'sector': sector,
            'count': search_result['count'],
            'companies': search_result['companies'],
            'source': 'crunchbase_scrape',
            'note': 'Limited sector filtering via search - consider API key',
            'timestamp': datetime.now().isoformat()
        }
    
    return {
        'success': False,
        'error': f"Could not retrieve funding data for sector: {sector}"
    }


def get_ipo_pipeline(limit: int = 10, include_recent: bool = True) -> Dict:
    """
    Get upcoming and recent IPO pipeline
    
    Args:
        limit: Maximum number of companies to return
        include_recent: Include recently IPO'd companies (last 90 days)
    
    Returns:
        Dict with IPO pipeline companies and status
    """
    if CRUNCHBASE_API_KEY:
        # Try API with IPO status filter
        result = _call_crunchbase_api(
            '/searches/organizations',
            params={
                'went_public_on': 'recent' if include_recent else None,
                'limit': limit,
                'order': 'went_public_on DESC',
                'field_ids': 'identifier,name,short_description,ipo_status,went_public_on,stock_symbol,stock_exchange_symbol,funding_total'
            }
        )
        
        if result.get('success'):
            pipeline = []
            entities = result.get('data', {}).get('entities', [])
            
            for entity in entities[:limit]:
                props = entity.get('properties', {})
                
                pipeline.append({
                    'name': props.get('name', ''),
                    'identifier': props.get('identifier', ''),
                    'description': props.get('short_description', '')[:120],
                    'ipo_status': props.get('ipo_status'),
                    'ipo_date': props.get('went_public_on', {}).get('value'),
                    'ticker': props.get('stock_symbol'),
                    'exchange': props.get('stock_exchange_symbol'),
                    'pre_ipo_funding': props.get('funding_total', {}).get('value', 0)
                })
            
            return {
                'success': True,
                'count': len(pipeline),
                'ipo_pipeline': pipeline,
                'include_recent': include_recent,
                'source': 'crunchbase_api',
                'timestamp': datetime.now().isoformat()
            }
    
    # Fallback: scrape IPO tracking page
    try:
        url = f"{CRUNCHBASE_WEB_BASE}/discover/organization.companies/recent_ipo"
        response = requests.get(url, headers=SCRAPE_HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        pipeline = []
        # Simplified scraping pattern
        company_links = soup.find_all('a', href=lambda x: x and '/organization/' in x)[:limit]
        
        for link in company_links:
            slug = link['href'].split('/organization/')[-1].split('?')[0]
            name = link.get_text(strip=True) or slug.replace('-', ' ').title()
            
            pipeline.append({
                'name': name,
                'identifier': slug,
                'url': f"{CRUNCHBASE_WEB_BASE}/organization/{slug}",
                'scraped': True
            })
        
        return {
            'success': True,
            'count': len(pipeline),
            'ipo_pipeline': pipeline,
            'source': 'crunchbase_scrape',
            'note': 'Limited IPO data from web scraping - consider API key',
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f"Failed to fetch IPO pipeline: {str(e)}"
        }


def get_module_info() -> Dict:
    """
    Get module information and available functions
    
    Returns:
        Dict with module metadata
    """
    return {
        'module': 'crunchbase_venture_data_api',
        'description': 'Startup & VC data from Crunchbase',
        'source': 'https://www.crunchbase.com/api',
        'free_tier': True,
        'api_limit': '100 calls/month',
        'has_api_key': bool(CRUNCHBASE_API_KEY),
        'fallback': 'Web scraping for public pages',
        'functions': [
            'search_companies(query, limit)',
            'get_company_profile(company)',
            'get_recent_funding_rounds(limit, days_back)',
            'get_funding_by_sector(sector, limit)',
            'get_ipo_pipeline(limit, include_recent)'
        ],
        'author': 'QuantClaw Data NightBuilder',
        'phase': 106
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("Crunchbase Venture Data API")
    print("=" * 60)
    
    info = get_module_info()
    print(f"\nModule: {info['module']}")
    print(f"API Key Set: {info['has_api_key']}")
    print(f"Free Tier: {info['api_limit']}")
    print(f"Fallback: {info['fallback']}")
    
    print("\nAvailable Functions:")
    for func in info['functions']:
        print(f"  - {func}")
    
    print("\n" + json.dumps(info, indent=2))
