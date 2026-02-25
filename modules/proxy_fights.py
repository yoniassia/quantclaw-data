#!/usr/bin/env python3
"""
Proxy Fight Tracker Module (Phase 69)
ISS/Glass Lewis recommendations, shareholder voting, proxy contest outcomes

Data Sources:
- SEC EDGAR: DEF 14A proxy statements, DEFA14A additional materials, 8-K voting results
- Company press releases via SEC RSS
- Voting outcome data from 8-K Form 5.07 (Results of Operations and Financial Condition)
"""

import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import requests
from typing import List, Dict, Optional
import re
from collections import defaultdict
import math

# SEC EDGAR Base URLs
SEC_EDGAR_BASE = "https://www.sec.gov"
SEC_EDGAR_API = f"{SEC_EDGAR_BASE}/cgi-bin/browse-edgar"
SEC_RSS_FEED = f"{SEC_EDGAR_BASE}/cgi-bin/browse-edgar?action=getcurrent"

# Form types for proxy materials
PROXY_FORMS = {
    'DEF 14A': 'Definitive proxy statement',
    'DEFA14A': 'Additional proxy soliciting materials',
    'DFAN14A': 'Definitive additional materials by non-management',
    'PRE 14A': 'Preliminary proxy statement',
    'PREC14A': 'Preliminary proxy statement in contested solicitation',
    'DEFC14A': 'Definitive proxy statement in contested solicitation',
    'DEFM14A': 'Definitive proxy statement (merger)',
    '8-K': 'Voting results (Item 5.07)'
}

def clean_nan(obj):
    """Recursively replace NaN with None for JSON serialization"""
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj

def get_cik_from_ticker(ticker: str) -> Optional[str]:
    """
    Convert ticker to CIK using SEC company tickers JSON
    SEC provides a free JSON mapping of all tickers to CIKs
    """
    try:
        # SEC company tickers API (updated quarterly)
        url = "https://www.sec.gov/files/company_tickers.json"
        headers = {'User-Agent': 'QuantClaw Research Tool contact@quantclaw.com'}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        ticker_upper = ticker.upper()
        
        # Data format: {0: {cik_str: 320193, ticker: "AAPL", title: "Apple Inc."}}
        for entry in data.values():
            if entry.get('ticker', '').upper() == ticker_upper:
                cik = str(entry['cik_str']).zfill(10)  # Pad to 10 digits
                return cik
        
        return None
    except Exception as e:
        print(f"Error fetching CIK for {ticker}: {e}", file=sys.stderr)
        return None

def fetch_proxy_filings(ticker: str, years: int = 3) -> dict:
    """
    Fetch proxy-related filings (DEF 14A, DEFA14A, 8-K) for a company
    Returns recent proxy statements and additional materials
    """
    try:
        cik = get_cik_from_ticker(ticker)
        if not cik:
            return {'error': f'Could not find CIK for ticker {ticker}'}
        
        headers = {'User-Agent': 'QuantClaw Research Tool contact@quantclaw.com'}
        
        # Fetch company filings from SEC EDGAR
        # Note: SEC rate limit is 10 requests/second
        url = f"{SEC_EDGAR_API}?action=getcompany&CIK={cik}&type=&dateb=&owner=exclude&count=100&output=json"
        
        response = requests.get(url, headers=headers, timeout=15)
        
        # SEC returns HTML, we need to parse differently
        # Use RSS feed instead for structured data
        rss_url = f"{SEC_EDGAR_BASE}/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=DEF+14A&dateb=&owner=exclude&count=10"
        
        filings_list = []
        form_types = ['DEF 14A', 'DEFA14A', 'PREC14A', 'DEFC14A', '8-K']
        
        for form_type in form_types:
            try:
                # Build URL for each form type
                search_url = f"{SEC_EDGAR_BASE}/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={form_type.replace(' ', '+')}&dateb=&owner=exclude&count=20"
                
                resp = requests.get(search_url, headers=headers, timeout=10)
                resp.raise_for_status()
                
                # Parse HTML to extract filing links (simplified)
                html = resp.text
                
                # Extract filing dates and accession numbers via regex
                # Pattern: <td nowrap="nowrap">2024-04-26</td>
                date_pattern = r'<td nowrap="nowrap">(\d{4}-\d{2}-\d{2})</td>'
                dates = re.findall(date_pattern, html)
                
                # Pattern for accession numbers: href="/cgi-bin/viewer?action=view&cik=320193&accession_number=0000320193-24-000052
                accession_pattern = r'accession_number=(\d+-\d+-\d+)'
                accessions = re.findall(accession_pattern, html)
                
                # Build filing objects
                for i, (date_str, accession) in enumerate(zip(dates[:10], accessions[:10])):
                    filing_date = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    # Only include filings from last N years
                    if filing_date < datetime.now() - timedelta(days=years*365):
                        continue
                    
                    # Build document URL
                    doc_url = f"{SEC_EDGAR_BASE}/cgi-bin/viewer?action=view&cik={cik}&accession_number={accession}&xbrl_type=v"
                    
                    filings_list.append({
                        'form_type': form_type,
                        'filing_date': date_str,
                        'accession_number': accession,
                        'document_url': doc_url,
                        'description': PROXY_FORMS.get(form_type, 'Proxy material')
                    })
                    
            except Exception as e:
                print(f"Error fetching {form_type} for {ticker}: {e}", file=sys.stderr)
                continue
        
        # Sort by filing date (newest first)
        filings_list.sort(key=lambda x: x['filing_date'], reverse=True)
        
        return clean_nan({
            'ticker': ticker.upper(),
            'cik': cik,
            'total_filings': len(filings_list),
            'filings': filings_list[:20],  # Return top 20
            'search_url': f"{SEC_EDGAR_BASE}/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=DEF+14A&owner=exclude&count=100"
        })
        
    except Exception as e:
        return {'error': f'Failed to fetch proxy filings: {str(e)}'}

def detect_contested_proxies(ticker: str) -> dict:
    """
    Detect proxy contests by looking for PREC14A and DEFC14A filings
    These indicate a contested proxy solicitation
    """
    try:
        cik = get_cik_from_ticker(ticker)
        if not cik:
            return {'error': f'Could not find CIK for ticker {ticker}'}
        
        headers = {'User-Agent': 'QuantClaw Research Tool contact@quantclaw.com'}
        
        # Look for contested proxy forms
        contested_forms = ['PREC14A', 'DEFC14A', 'DFAN14A']
        contested_filings = []
        
        for form_type in contested_forms:
            try:
                search_url = f"{SEC_EDGAR_BASE}/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={form_type}&dateb=&owner=exclude&count=20"
                
                resp = requests.get(search_url, headers=headers, timeout=10)
                resp.raise_for_status()
                
                html = resp.text
                
                # Extract dates and accession numbers
                date_pattern = r'<td nowrap="nowrap">(\d{4}-\d{2}-\d{2})</td>'
                dates = re.findall(date_pattern, html)
                
                accession_pattern = r'accession_number=(\d+-\d+-\d+)'
                accessions = re.findall(accession_pattern, html)
                
                for date_str, accession in zip(dates[:10], accessions[:10]):
                    filing_date = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    doc_url = f"{SEC_EDGAR_BASE}/cgi-bin/viewer?action=view&cik={cik}&accession_number={accession}&xbrl_type=v"
                    
                    contested_filings.append({
                        'form_type': form_type,
                        'filing_date': date_str,
                        'accession_number': accession,
                        'document_url': doc_url,
                        'contest_type': 'Management' if form_type == 'DEFC14A' else 'Dissident',
                        'description': PROXY_FORMS.get(form_type, 'Contested proxy')
                    })
                    
            except Exception as e:
                print(f"Error checking {form_type} for {ticker}: {e}", file=sys.stderr)
                continue
        
        # Sort by date
        contested_filings.sort(key=lambda x: x['filing_date'], reverse=True)
        
        # Determine contest status
        has_contest = len(contested_filings) > 0
        most_recent = contested_filings[0] if has_contest else None
        
        status = "No active contest"
        if has_contest and most_recent:
            filing_date = datetime.strptime(most_recent['filing_date'], '%Y-%m-%d')
            days_ago = (datetime.now() - filing_date).days
            
            if days_ago < 180:  # Within last 6 months
                status = "Active or recent contest"
            else:
                status = "Historical contest"
        
        return clean_nan({
            'ticker': ticker.upper(),
            'cik': cik,
            'has_contest': has_contest,
            'status': status,
            'total_contested_filings': len(contested_filings),
            'filings': contested_filings[:10],
            'most_recent_date': most_recent['filing_date'] if most_recent else None
        })
        
    except Exception as e:
        return {'error': f'Failed to detect proxy contests: {str(e)}'}

def fetch_voting_results(ticker: str) -> dict:
    """
    Fetch voting results from 8-K filings (Item 5.07)
    8-K Item 5.07 reports results of annual meetings including vote counts
    """
    try:
        cik = get_cik_from_ticker(ticker)
        if not cik:
            return {'error': f'Could not find CIK for ticker {ticker}'}
        
        headers = {'User-Agent': 'QuantClaw Research Tool contact@quantclaw.com'}
        
        # Fetch recent 8-K filings
        search_url = f"{SEC_EDGAR_BASE}/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=8-K&dateb=&owner=exclude&count=50"
        
        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        html = response.text
        
        # Extract dates and accession numbers
        date_pattern = r'<td nowrap="nowrap">(\d{4}-\d{2}-\d{2})</td>'
        dates = re.findall(date_pattern, html)
        
        accession_pattern = r'accession_number=(\d+-\d+-\d+)'
        accessions = re.findall(accession_pattern, html)
        
        voting_results = []
        
        for date_str, accession in zip(dates[:20], accessions[:20]):
            filing_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Only look at filings from last 2 years
            if filing_date < datetime.now() - timedelta(days=730):
                continue
            
            doc_url = f"{SEC_EDGAR_BASE}/cgi-bin/viewer?action=view&cik={cik}&accession_number={accession}&xbrl_type=v"
            
            # Try to fetch document text to check for Item 5.07
            try:
                doc_resp = requests.get(doc_url, headers=headers, timeout=10)
                doc_text = doc_resp.text
                
                # Check if this 8-K contains Item 5.07 (voting results)
                if 'Item 5.07' in doc_text or 'Item 5.7' in doc_text or 'Submission of Matters to a Vote' in doc_text:
                    # Parse voting data (simplified - real implementation would need detailed parsing)
                    # Look for common patterns like "FOR: 1,234,567 AGAINST: 123,456"
                    
                    voting_results.append({
                        'filing_date': date_str,
                        'accession_number': accession,
                        'document_url': doc_url,
                        'meeting_type': 'Annual Meeting' if 'annual' in doc_text.lower()[:5000] else 'Special Meeting',
                        'has_voting_data': True,
                        'note': 'Document contains voting results - manual review recommended for detailed analysis'
                    })
                    
            except Exception as e:
                # If we can't fetch the document, still include the filing
                print(f"Could not fetch 8-K content for {accession}: {e}", file=sys.stderr)
                continue
        
        return clean_nan({
            'ticker': ticker.upper(),
            'cik': cik,
            'total_voting_filings': len(voting_results),
            'filings': voting_results,
            'note': 'Voting results require manual review of 8-K Item 5.07 sections for detailed vote counts'
        })
        
    except Exception as e:
        return {'error': f'Failed to fetch voting results: {str(e)}'}

def analyze_proxy_advisory(ticker: str) -> dict:
    """
    Placeholder for ISS/Glass Lewis recommendations
    Note: ISS and Glass Lewis data requires paid subscriptions
    This function provides guidance on where to find this data
    """
    try:
        cik = get_cik_from_ticker(ticker)
        if not cik:
            return {'error': f'Could not find CIK for ticker {ticker}'}
        
        return clean_nan({
            'ticker': ticker.upper(),
            'cik': cik,
            'note': 'ISS and Glass Lewis data requires paid subscriptions',
            'iss_info': {
                'provider': 'Institutional Shareholder Services (ISS)',
                'website': 'https://www.issgovernance.com',
                'data_type': 'Voting recommendations, governance ratings, proxy research',
                'access': 'Paid subscription required'
            },
            'glass_lewis_info': {
                'provider': 'Glass Lewis & Co.',
                'website': 'https://www.glasslewis.com',
                'data_type': 'Independent proxy research and voting recommendations',
                'access': 'Paid subscription required'
            },
            'free_alternatives': {
                'sec_edgar': 'Monitor contested proxy filings (PREC14A, DEFC14A)',
                'sec_8k': 'Track actual voting results in 8-K Item 5.07 filings',
                'company_ir': 'Review company investor relations pages for proxy materials'
            },
            'sec_filings_url': f"{SEC_EDGAR_BASE}/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=DEF+14A&owner=exclude&count=100"
        })
        
    except Exception as e:
        return {'error': f'Failed to analyze proxy advisory: {str(e)}'}

def proxy_summary(ticker: str) -> dict:
    """
    Comprehensive proxy fight analysis combining all data sources
    """
    try:
        # Fetch all components
        filings = fetch_proxy_filings(ticker, years=2)
        contests = detect_contested_proxies(ticker)
        voting = fetch_voting_results(ticker)
        
        # Check for errors
        if 'error' in filings:
            return filings
        
        # Determine overall status
        has_recent_def14a = False
        most_recent_proxy = None
        
        if 'filings' in filings and len(filings['filings']) > 0:
            def14a_filings = [f for f in filings['filings'] if f['form_type'] == 'DEF 14A']
            if def14a_filings:
                has_recent_def14a = True
                most_recent_proxy = def14a_filings[0]
        
        # Calculate risk score (0-100)
        risk_score = 0
        risk_factors = []
        
        if contests.get('has_contest', False):
            status = contests.get('status', '')
            if 'Active' in status:
                risk_score += 50
                risk_factors.append('Active proxy contest detected')
            elif 'recent' in status.lower():
                risk_score += 30
                risk_factors.append('Recent proxy contest within 6 months')
            else:
                risk_score += 10
                risk_factors.append('Historical proxy contest')
        
        # Check for multiple contested filings
        contested_count = contests.get('total_contested_filings', 0)
        if contested_count > 3:
            risk_score += 20
            risk_factors.append(f'Multiple contested filings ({contested_count})')
        
        # Check for DEFA14A (additional materials - often indicates complexity)
        defa_count = len([f for f in filings.get('filings', []) if f['form_type'] == 'DEFA14A'])
        if defa_count > 5:
            risk_score += 10
            risk_factors.append(f'Numerous additional proxy materials filed ({defa_count})')
        
        risk_score = min(risk_score, 100)  # Cap at 100
        
        # Determine risk level
        if risk_score >= 60:
            risk_level = 'High'
        elif risk_score >= 30:
            risk_level = 'Moderate'
        else:
            risk_level = 'Low'
        
        return clean_nan({
            'ticker': ticker.upper(),
            'cik': filings.get('cik'),
            'summary': {
                'has_recent_proxy': has_recent_def14a,
                'most_recent_proxy_date': most_recent_proxy['filing_date'] if most_recent_proxy else None,
                'total_proxy_filings_2y': filings.get('total_filings', 0),
                'has_active_contest': contests.get('status', '') == 'Active or recent contest',
                'contested_filings': contests.get('total_contested_filings', 0),
                'voting_result_filings': voting.get('total_voting_filings', 0)
            },
            'risk_assessment': {
                'score': risk_score,
                'level': risk_level,
                'factors': risk_factors if risk_factors else ['No significant risk factors detected']
            },
            'recent_filings': filings.get('filings', [])[:5],
            'contested_filings': contests.get('filings', [])[:3],
            'voting_results': voting.get('filings', [])[:3],
            'data_sources': {
                'sec_edgar': f"{SEC_EDGAR_BASE}/cgi-bin/browse-edgar?CIK={filings.get('cik')}&owner=exclude",
                'note': 'For ISS/Glass Lewis recommendations, see proxy-advisory endpoint'
            }
        })
        
    except Exception as e:
        return {'error': f'Failed to generate proxy summary: {str(e)}'}

def print_help():
    """Print help message"""
    print("Proxy Fight Tracker — ISS/Glass Lewis recommendations, shareholder voting, proxy contest outcomes")
    print("\nUsage:")
    print("  python proxy_fights.py proxy-filings TICKER [--years 3]")
    print("  python proxy_fights.py proxy-contests TICKER")
    print("  python proxy_fights.py proxy-voting TICKER")
    print("  python proxy_fights.py proxy-advisory TICKER")
    print("  python proxy_fights.py proxy-summary TICKER")
    print("\nCommands:")
    print("  proxy-filings     Fetch proxy-related filings (DEF 14A, DEFA14A, 8-K)")
    print("  proxy-contests    Detect proxy contests (PREC14A, DEFC14A)")
    print("  proxy-voting      Fetch voting results from 8-K Item 5.07")
    print("  proxy-advisory    Information on ISS/Glass Lewis data sources")
    print("  proxy-summary     Comprehensive proxy fight analysis with risk score")

def main():
    if len(sys.argv) < 2:
        print_help()
        return 1
    
    command = sys.argv[1]
    
    if command == "proxy-filings":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing ticker argument"}))
            return 1
        ticker = sys.argv[2]
        years = 3
        for i, arg in enumerate(sys.argv):
            if arg == '--years' and i + 1 < len(sys.argv):
                years = int(sys.argv[i + 1])
        result = fetch_proxy_filings(ticker, years)
        
    elif command == "proxy-contests":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing ticker argument"}))
            return 1
        ticker = sys.argv[2]
        result = detect_contested_proxies(ticker)
        
    elif command == "proxy-voting":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing ticker argument"}))
            return 1
        ticker = sys.argv[2]
        result = fetch_voting_results(ticker)
        
    elif command == "proxy-advisory":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing ticker argument"}))
            return 1
        ticker = sys.argv[2]
        result = analyze_proxy_advisory(ticker)
        
    elif command == "proxy-summary":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing ticker argument"}))
            return 1
        ticker = sys.argv[2]
        result = proxy_summary(ticker)
        
    else:
        print(json.dumps({"error": f"Unknown command: {command}"}))
        print_help()
        return 1
    
    print(json.dumps(result, indent=2))
    return 0

if __name__ == '__main__':
    main()
