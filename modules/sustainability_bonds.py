#!/usr/bin/env python3
"""
Sustainability-Linked Bonds Tracker — Phase 71

Monitor SLB (Sustainability-Linked Bonds) issuance, KPI achievement, coupon step-up triggers,
and ESG bond market trends using free data sources:
- SEC EDGAR 8-K/S-3 filings for SLB issuance announcements
- EMMA (Municipal Securities Rulemaking Board) for municipal green bonds
- Corporate sustainability reports and ESG disclosures
- Bond pricing data via Yahoo Finance

Key Features:
1. Track SLB issuances from SEC filings
2. Monitor KPI targets and achievement
3. Detect coupon step-up trigger events
4. Compare SLB pricing vs conventional bonds
5. ESG bond market trend analysis
"""

import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import re
from bs4 import BeautifulSoup
import time


# SLB Keywords for SEC filing detection
SLB_KEYWORDS = [
    'sustainability-linked bond',
    'sustainability linked bond',
    'SLB',
    'green bond',
    'ESG bond',
    'social bond',
    'sustainability bond',
    'KPI target',
    'sustainability performance target',
    'coupon step-up',
    'step-up provision',
    'ESG-linked'
]

# Common SLB KPI categories
KPI_CATEGORIES = {
    'carbon': ['greenhouse gas', 'GHG emissions', 'carbon intensity', 'CO2 emissions', 'scope 1', 'scope 2', 'scope 3'],
    'renewable': ['renewable energy', 'clean energy', 'solar', 'wind power', 'carbon-free'],
    'water': ['water consumption', 'water intensity', 'water recycling', 'water usage'],
    'waste': ['waste reduction', 'recycling rate', 'circular economy', 'zero waste'],
    'diversity': ['gender diversity', 'board diversity', 'workforce diversity', 'inclusion'],
    'safety': ['injury rate', 'lost time incidents', 'safety performance', 'TRIR'],
    'supply_chain': ['sustainable sourcing', 'supplier standards', 'responsible sourcing']
}


def search_sec_slb_filings(company: str, limit: int = 50) -> List[Dict]:
    """
    Search SEC EDGAR for SLB-related filings (8-K, S-3, 424B, prospectus supplements).
    
    Args:
        company: Company name or ticker
        limit: Maximum number of filings to search
    
    Returns:
        List of relevant filings with metadata
    """
    base_url = "https://www.sec.gov/cgi-bin/browse-edgar"
    
    # Search parameters
    params = {
        'action': 'getcompany',
        'company': company,
        'type': '8-K',  # Current reports often announce bond issuances
        'count': limit,
        'output': 'atom'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; MoneyClawBot/1.0; +https://moneyclaw.com)'
    }
    
    filings = []
    
    try:
        # Search 8-K filings
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            # Parse XML/Atom feed
            soup = BeautifulSoup(response.content, 'xml')
            entries = soup.find_all('entry')
            
            for entry in entries[:limit]:
                title = entry.find('title').text if entry.find('title') else ''
                summary = entry.find('summary').text if entry.find('summary') else ''
                filing_date = entry.find('updated').text if entry.find('updated') else ''
                link = entry.find('link', attrs={'rel': 'alternate'})
                filing_url = link.get('href') if link else ''
                
                # Check if filing mentions SLB keywords
                text_content = f"{title} {summary}".lower()
                if any(keyword.lower() in text_content for keyword in SLB_KEYWORDS):
                    filings.append({
                        'title': title,
                        'date': filing_date.split('T')[0] if 'T' in filing_date else filing_date,
                        'url': filing_url,
                        'type': '8-K',
                        'summary': summary[:200] + '...' if len(summary) > 200 else summary
                    })
        
        time.sleep(0.2)  # Rate limiting
        
        # Also search prospectus supplements (424B)
        params['type'] = '424B'
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            entries = soup.find_all('entry')
            
            for entry in entries[:limit]:
                title = entry.find('title').text if entry.find('title') else ''
                summary = entry.find('summary').text if entry.find('summary') else ''
                filing_date = entry.find('updated').text if entry.find('updated') else ''
                link = entry.find('link', attrs={'rel': 'alternate'})
                filing_url = link.get('href') if link else ''
                
                text_content = f"{title} {summary}".lower()
                if any(keyword.lower() in text_content for keyword in SLB_KEYWORDS):
                    filings.append({
                        'title': title,
                        'date': filing_date.split('T')[0] if 'T' in filing_date else filing_date,
                        'url': filing_url,
                        'type': '424B',
                        'summary': summary[:200] + '...' if len(summary) > 200 else summary
                    })
    
    except Exception as e:
        print(f"Error searching SEC filings: {e}")
    
    # Sort by date descending
    filings.sort(key=lambda x: x['date'], reverse=True)
    
    return filings


def extract_slb_details(filing_url: str) -> Optional[Dict]:
    """
    Extract SLB details from SEC filing HTML.
    
    Args:
        filing_url: URL to SEC filing
    
    Returns:
        Dict with SLB issuance details, KPIs, targets, coupon terms
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; MoneyClawBot/1.0; +https://moneyclaw.com)'
    }
    
    try:
        response = requests.get(filing_url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
        
        # Extract bond details
        details = {
            'principal_amount': extract_dollar_amounts(text),
            'maturity_date': extract_dates(text),
            'base_coupon': extract_coupon_rate(text),
            'kpi_targets': extract_kpi_targets(text),
            'step_up_provisions': extract_step_up_terms(text),
            'verification': extract_verification_info(text)
        }
        
        return details
    
    except Exception as e:
        print(f"Error extracting SLB details: {e}")
        return None


def extract_dollar_amounts(text: str) -> List[str]:
    """Extract dollar amounts from filing text."""
    pattern = r'\$\s*[\d,]+(?:\.\d+)?\s*(?:million|billion)?'
    matches = re.findall(pattern, text, re.IGNORECASE)
    return matches[:5]  # Top 5 amounts


def extract_dates(text: str) -> List[str]:
    """Extract dates (maturity, KPI target dates) from text."""
    # Match dates in formats: January 15, 2030 or 2030-01-15
    pattern = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2}'
    matches = re.findall(pattern, text, re.IGNORECASE)
    return matches[:10]


def extract_coupon_rate(text: str) -> Optional[str]:
    """Extract coupon rate from filing."""
    pattern = r'(\d+\.?\d*)\s*%\s*(?:per annum|annual rate|interest rate|coupon)'
    matches = re.findall(pattern, text, re.IGNORECASE)
    return matches[0] if matches else None


def extract_kpi_targets(text: str) -> List[Dict]:
    """Extract KPI targets from SLB filing."""
    kpis = []
    
    for category, keywords in KPI_CATEGORIES.items():
        for keyword in keywords:
            # Look for keyword near numbers/percentages
            pattern = rf'{re.escape(keyword)}.{{0,200}}?(\d+\.?\d*)\s*%'
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            if matches:
                for match in matches[:2]:  # Limit to 2 per keyword
                    kpis.append({
                        'category': category,
                        'metric': keyword,
                        'target_value': match,
                        'unit': 'percentage'
                    })
    
    return kpis


def extract_step_up_terms(text: str) -> List[str]:
    """Extract coupon step-up provisions."""
    patterns = [
        r'step-up\s+of\s+(\d+\.?\d*)\s*(?:basis points|bps)',
        r'increase\s+(?:by|of)\s+(\d+\.?\d*)\s*(?:basis points|bps)',
        r'coupon\s+adjustment\s+of\s+(\d+\.?\d*)\s*(?:basis points|bps)'
    ]
    
    step_ups = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        step_ups.extend(matches)
    
    return step_ups


def extract_verification_info(text: str) -> Optional[str]:
    """Extract third-party verifier information."""
    verifier_keywords = ['verified by', 'assurance by', 'audited by', 'verified third party']
    
    for keyword in verifier_keywords:
        idx = text.lower().find(keyword)
        if idx != -1:
            # Extract next 100 characters after keyword
            snippet = text[idx:idx+150]
            return snippet.strip()
    
    return None


def get_slb_issuances(ticker: str, months_back: int = 12) -> Dict:
    """
    Get all SLB issuances for a company.
    
    Args:
        ticker: Company ticker
        months_back: How many months to look back
    
    Returns:
        Dict with issuance history and details
    """
    # Get company info
    try:
        stock = yf.Ticker(ticker)
        company_name = stock.info.get('longName', ticker)
    except:
        company_name = ticker
    
    # Search SEC filings
    filings = search_sec_slb_filings(company_name, limit=50)
    
    # Filter by date range
    cutoff_date = (datetime.now() - timedelta(days=months_back*30)).strftime('%Y-%m-%d')
    recent_filings = [f for f in filings if f['date'] >= cutoff_date]
    
    result = {
        'ticker': ticker,
        'company': company_name,
        'search_period_months': months_back,
        'total_filings_found': len(recent_filings),
        'issuances': recent_filings,
        'summary': generate_issuance_summary(recent_filings)
    }
    
    return result


def generate_issuance_summary(filings: List[Dict]) -> List[str]:
    """Generate human-readable summary of SLB issuances."""
    if not filings:
        return ["No sustainability-linked bond issuances found in search period."]
    
    insights = [
        f"Found {len(filings)} SLB-related filing(s)",
        f"Most recent: {filings[0]['date']}" if filings else "None"
    ]
    
    # Count filing types
    types = {}
    for f in filings:
        t = f.get('type', 'Unknown')
        types[t] = types.get(t, 0) + 1
    
    if types:
        insights.append(f"Filing types: {', '.join([f'{k}({v})' for k, v in types.items()])}")
    
    return insights


def analyze_slb_market_trends(sector: str = None) -> Dict:
    """
    Analyze SLB market trends across sectors.
    
    Args:
        sector: Optional sector filter (Technology, Energy, etc.)
    
    Returns:
        Market trend analysis
    """
    # Major SLB issuers by sector
    issuers_by_sector = {
        'Technology': ['AAPL', 'MSFT', 'GOOGL'],
        'Energy': ['XOM', 'CVX', 'COP'],
        'Consumer': ['PG', 'KO', 'PEP'],
        'Finance': ['JPM', 'BAC', 'WFC'],
        'Healthcare': ['JNJ', 'UNH', 'PFE']
    }
    
    sectors_to_analyze = [sector] if sector else list(issuers_by_sector.keys())
    
    results = {
        'analysis_date': datetime.now().strftime('%Y-%m-%d'),
        'sectors_analyzed': len(sectors_to_analyze),
        'sector_data': []
    }
    
    for sec in sectors_to_analyze:
        tickers = issuers_by_sector.get(sec, [])
        
        sector_issuances = 0
        for ticker in tickers[:3]:  # Limit to 3 per sector to avoid rate limits
            data = get_slb_issuances(ticker, months_back=24)
            sector_issuances += data['total_filings_found']
            time.sleep(0.3)  # Rate limiting
        
        results['sector_data'].append({
            'sector': sec,
            'sample_companies': len(tickers),
            'slb_filings_24mo': sector_issuances
        })
    
    # Add market insights
    results['insights'] = generate_market_insights(results['sector_data'])
    
    return results


def generate_market_insights(sector_data: List[Dict]) -> List[str]:
    """Generate insights from sector SLB data."""
    insights = []
    
    if not sector_data:
        return ["Insufficient data for market insights."]
    
    # Total filings
    total = sum([s['slb_filings_24mo'] for s in sector_data])
    insights.append(f"Total SLB filings (24mo): {total}")
    
    # Most active sector
    if sector_data:
        most_active = max(sector_data, key=lambda x: x['slb_filings_24mo'])
        insights.append(f"Most active sector: {most_active['sector']} ({most_active['slb_filings_24mo']} filings)")
    
    # Emerging sectors
    emerging = [s for s in sector_data if s['slb_filings_24mo'] > 0]
    insights.append(f"Sectors with SLB activity: {len(emerging)}/{len(sector_data)}")
    
    return insights


def get_slb_coupon_comparison(ticker: str) -> Dict:
    """
    Compare SLB coupon rates vs conventional bonds for a company.
    
    Args:
        ticker: Company ticker
    
    Returns:
        Coupon comparison analysis
    """
    try:
        stock = yf.Ticker(ticker)
        company_name = stock.info.get('longName', ticker)
    except:
        company_name = ticker
    
    # Search for both SLB and conventional bond filings
    slb_filings = search_sec_slb_filings(company_name, limit=30)
    
    # Extract coupon rates
    slb_coupons = []
    conventional_coupons = []
    
    for filing in slb_filings:
        # This is a simplified analysis - real implementation would parse actual filing text
        # For demo, we'll use placeholder logic
        pass
    
    result = {
        'ticker': ticker,
        'company': company_name,
        'slb_issuances_found': len([f for f in slb_filings if 'sustainability' in f['title'].lower()]),
        'analysis': 'SLB coupon comparison requires detailed filing parsing',
        'methodology': 'Compare SLB base coupon + step-up vs conventional bond yields',
        'data_sources': ['SEC EDGAR 8-K', 'SEC EDGAR 424B', 'Yahoo Finance bond data']
    }
    
    return result


def monitor_kpi_achievement(ticker: str) -> Dict:
    """
    Monitor KPI achievement and potential coupon step-up triggers.
    
    Args:
        ticker: Company ticker
    
    Returns:
        KPI monitoring report
    """
    try:
        stock = yf.Ticker(ticker)
        company_name = stock.info.get('longName', ticker)
    except:
        company_name = ticker
    
    # Get recent SLB issuances
    issuances = get_slb_issuances(ticker, months_back=36)
    
    result = {
        'ticker': ticker,
        'company': company_name,
        'monitoring_date': datetime.now().strftime('%Y-%m-%d'),
        'active_slbs': issuances['total_filings_found'],
        'kpi_status': 'Requires ESG report analysis',
        'data_sources': [
            'Corporate sustainability reports',
            'CDP (Carbon Disclosure Project)',
            'SEC 10-K ESG sections',
            'Company ESG portals'
        ],
        'methodology': [
            '1. Extract KPI targets from SLB prospectus',
            '2. Track actual performance from ESG reports',
            '3. Calculate gap to target',
            '4. Identify potential step-up triggers'
        ],
        'filings': issuances['issuances'][:5]  # Top 5 recent
    }
    
    return result


if __name__ == "__main__":
    # Test module
    print("=== Sustainability-Linked Bonds Tracker Test ===\n")
    
    # Test 1: Search for SLB issuances
    print("Test 1: Apple SLB Issuances")
    result = get_slb_issuances('AAPL', months_back=24)
    print(json.dumps(result, indent=2))
    print()
    
    # Test 2: Market trends
    print("\nTest 2: SLB Market Trends")
    trends = analyze_slb_market_trends(sector='Technology')
    print(json.dumps(trends, indent=2))
    print()
    
    # Test 3: KPI monitoring
    print("\nTest 3: KPI Achievement Monitor")
    kpi_result = monitor_kpi_achievement('MSFT')
    print(json.dumps(kpi_result, indent=2))
