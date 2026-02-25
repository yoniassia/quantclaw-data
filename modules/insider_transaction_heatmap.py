#!/usr/bin/env python3
"""
Insider Transaction Heatmap Module — Phase 137

SEC Form 4 cluster analysis with sector-wide insider buying/selling patterns:
- Real-time Form 4 RSS feed monitoring
- Insider buying vs selling ratio by sector
- Cluster detection (coordinated insider activity)
- Magnitude analysis (transaction size relative to holdings)
- C-suite vs director vs 10% owner patterns
- Sentiment scoring (bullish/bearish signals)

Data Sources:
- SEC EDGAR: Form 4 RSS feed (real-time insider transactions)
- SEC EDGAR: Form 4 XML parsing (detailed transaction data)
- Yahoo Finance: Company sector classification and market cap
- SEC Company Tickers: CIK-to-ticker mapping

Refresh: Daily (RSS feed updates in real-time)
Coverage: All US public companies

Author: QUANTCLAW DATA Build Agent
Phase: 137
"""

import sys
import re
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from xml.etree import ElementTree as ET
import time

# SEC EDGAR Configuration
EDGAR_BASE_URL = "https://www.sec.gov"
FORM4_RSS_URL = f"{EDGAR_BASE_URL}/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=include&start=0&count=100&output=atom"
USER_AGENT = "QuantClaw Data quantclaw@example.com"

# Transaction type classifications
PURCHASE_TYPES = ['P', 'A', 'M', 'G', 'J', 'W']  # Purchase, Award, Merger, Gift, Tax, Will
SALE_TYPES = ['S', 'D', 'F', 'I']  # Sale, Disposition, Tax payment, Discretionary
EXERCISE_TYPES = ['M', 'A', 'C']  # Option exercise, Award, Conversion

# Insider role classifications
EXECUTIVE_ROLES = [
    'chief executive officer', 'ceo', 'president', 'chief operating officer', 'coo',
    'chief financial officer', 'cfo', 'chief technology officer', 'cto',
    'chief investment officer', 'cio', 'general counsel', 'treasurer'
]
DIRECTOR_ROLES = ['director', 'board member', 'independent director', 'lead director']
OWNER_ROLES = ['10% owner', 'beneficial owner', 'holder', 'trustee']

# Sector mapping cache
SECTOR_CACHE = {}


def get_company_tickers() -> Dict[str, Dict]:
    """
    Fetch SEC company tickers mapping
    Returns dict mapping CIK -> {ticker, title, exchange}
    """
    try:
        url = "https://www.sec.gov/files/company_tickers.json"
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            companies = response.json()
            # Convert to CIK-indexed dict
            cik_map = {}
            for company in companies.values():
                cik = str(company['cik_str']).zfill(10)
                cik_map[cik] = {
                    'ticker': company.get('ticker', '').upper(),
                    'title': company.get('title', ''),
                    'exchange': company.get('exchange', '')
                }
            return cik_map
        
        return {}
    except Exception as e:
        print(f"Error fetching company tickers: {e}", file=sys.stderr)
        return {}


def get_recent_form4_filings(days: int = 7, limit: int = 100) -> List[Dict]:
    """
    Fetch recent Form 4 filings from SEC EDGAR RSS feed
    
    Args:
        days: Number of days to look back
        limit: Maximum number of filings to fetch
    
    Returns:
        List of filing metadata
    """
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(FORM4_RSS_URL, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return []
        
        # Parse ATOM feed
        root = ET.fromstring(response.content)
        
        filings = []
        from datetime import timezone
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry')[:limit]:
            try:
                title = entry.find('{http://www.w3.org/2005/Atom}title').text
                updated = entry.find('{http://www.w3.org/2005/Atom}updated').text
                filing_date = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                
                if filing_date < cutoff_date:
                    continue
                
                # Extract company name and CIK from title
                # Format: "4 - Company Name (CIK)"
                match = re.search(r'^4\s*-\s*(.+?)\s*\((\d+)\)', title)
                if not match:
                    continue
                
                company_name = match.group(1).strip()
                cik = match.group(2).zfill(10)
                
                # Get filing URL
                filing_url = None
                for link in entry.findall('{http://www.w3.org/2005/Atom}link'):
                    if link.get('type') == 'text/html':
                        filing_url = link.get('href')
                        break
                
                if not filing_url:
                    continue
                
                # Extract accession number
                accession = None
                acc_match = re.search(r'Accession-Number=(\d+-\d+-\d+)', filing_url)
                if acc_match:
                    accession = acc_match.group(1)
                
                filings.append({
                    'cik': cik,
                    'company_name': company_name,
                    'filing_date': filing_date.strftime('%Y-%m-%d'),
                    'filing_url': filing_url,
                    'accession': accession
                })
                
            except Exception as e:
                print(f"Error parsing entry: {e}", file=sys.stderr)
                continue
        
        return filings
        
    except Exception as e:
        print(f"Error fetching Form 4 RSS feed: {e}", file=sys.stderr)
        return []


def parse_form4_xml(filing_url: str) -> Dict:
    """
    Parse Form 4 XML to extract transaction details
    
    Args:
        filing_url: URL to Form 4 filing page
    
    Returns:
        Dict with transaction data
    """
    try:
        headers = {'User-Agent': USER_AGENT}
        
        # Get filing page HTML
        response = requests.get(filing_url, headers=headers, timeout=15)
        if response.status_code != 200:
            return {}
        
        # Find XML document link
        xml_link = None
        for match in re.finditer(r'<a href="([^"]+\.xml)"', response.text):
            href = match.group(1)
            if 'primary_doc' in href or href.endswith('.xml'):
                xml_link = href
                break
        
        if not xml_link:
            return {}
        
        # Convert relative URL to absolute
        if not xml_link.startswith('http'):
            xml_link = f"{EDGAR_BASE_URL}{xml_link}"
        
        # Fetch XML
        xml_response = requests.get(xml_link, headers=headers, timeout=15)
        if xml_response.status_code != 200:
            return {}
        
        # Parse XML
        root = ET.fromstring(xml_response.content)
        
        # Extract reporting owner info
        owner_data = {}
        reporting_owner = root.find('.//reportingOwner')
        if reporting_owner:
            owner_data['name'] = reporting_owner.findtext('.//rptOwnerName', '').strip()
            owner_data['is_director'] = reporting_owner.findtext('.//isDirector', '0') == '1'
            owner_data['is_officer'] = reporting_owner.findtext('.//isOfficer', '0') == '1'
            owner_data['is_ten_percent_owner'] = reporting_owner.findtext('.//isTenPercentOwner', '0') == '1'
            owner_data['officer_title'] = reporting_owner.findtext('.//officerTitle', '').strip()
        
        # Extract non-derivative transactions
        transactions = []
        for trans in root.findall('.//nonDerivativeTransaction'):
            try:
                security_title = trans.findtext('.//securityTitle', '').strip()
                trans_date = trans.findtext('.//transactionDate/value', '').strip()
                trans_code = trans.findtext('.//transactionCoding/transactionCode', '').strip()
                trans_shares = trans.findtext('.//transactionAmounts/transactionShares/value', '0').strip()
                trans_price = trans.findtext('.//transactionAmounts/transactionPricePerShare/value', '0').strip()
                acquired_disposed = trans.findtext('.//transactionAmounts/transactionAcquiredDisposedCode/value', '').strip()
                
                shares_owned = trans.findtext('.//postTransactionAmounts/sharesOwnedFollowingTransaction/value', '0').strip()
                
                transactions.append({
                    'security': security_title,
                    'date': trans_date,
                    'code': trans_code,
                    'shares': float(trans_shares) if trans_shares else 0,
                    'price': float(trans_price) if trans_price else 0,
                    'acquired_disposed': acquired_disposed,
                    'shares_owned_after': float(shares_owned) if shares_owned else 0
                })
            except Exception as e:
                continue
        
        return {
            'owner': owner_data,
            'transactions': transactions
        }
        
    except Exception as e:
        print(f"Error parsing Form 4 XML: {e}", file=sys.stderr)
        return {}


def classify_insider_role(owner_data: Dict) -> str:
    """
    Classify insider role based on Form 4 data
    
    Returns: 'executive', 'director', 'owner', or 'other'
    """
    title = owner_data.get('officer_title', '').lower()
    
    if owner_data.get('is_ten_percent_owner'):
        return 'owner'
    
    if owner_data.get('is_officer'):
        for role in EXECUTIVE_ROLES:
            if role in title:
                return 'executive'
    
    if owner_data.get('is_director'):
        return 'director'
    
    return 'other'


def get_ticker_sector(ticker: str) -> Optional[str]:
    """
    Get sector for ticker using Yahoo Finance
    """
    if ticker in SECTOR_CACHE:
        return SECTOR_CACHE[ticker]
    
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info
        sector = info.get('sector', 'Unknown')
        SECTOR_CACHE[ticker] = sector
        return sector
    except:
        return 'Unknown'


def get_insider_transaction_summary(days: int = 7, limit: int = 100) -> Dict:
    """
    Get comprehensive insider transaction summary
    
    Args:
        days: Number of days to analyze
        limit: Maximum number of filings to process
    
    Returns:
        Summary with sector patterns, insider roles, buy/sell ratios
    """
    print(f"Fetching Form 4 filings from past {days} days...", file=sys.stderr)
    
    filings = get_recent_form4_filings(days=days, limit=limit)
    
    if not filings:
        return {'error': 'No recent Form 4 filings found'}
    
    print(f"Found {len(filings)} Form 4 filings. Parsing transactions...", file=sys.stderr)
    
    # Get CIK-ticker mapping
    cik_map = get_company_tickers()
    
    # Aggregate data structures
    sector_data = defaultdict(lambda: {
        'buys': 0, 'sells': 0, 'buy_value': 0, 'sell_value': 0,
        'buy_count': 0, 'sell_count': 0, 'companies': set()
    })
    
    role_data = defaultdict(lambda: {
        'buys': 0, 'sells': 0, 'buy_value': 0, 'sell_value': 0
    })
    
    company_transactions = []
    
    # Process each filing
    for i, filing in enumerate(filings[:limit]):
        if i % 10 == 0:
            print(f"Processing filing {i+1}/{min(len(filings), limit)}...", file=sys.stderr)
        
        cik = filing['cik']
        ticker = cik_map.get(cik, {}).get('ticker', '')
        
        if not ticker:
            continue
        
        # Parse Form 4 XML
        form4_data = parse_form4_xml(filing['filing_url'])
        
        if not form4_data or not form4_data.get('transactions'):
            continue
        
        # Get sector
        sector = get_ticker_sector(ticker)
        
        # Get insider role
        role = classify_insider_role(form4_data.get('owner', {}))
        
        # Process transactions
        for trans in form4_data['transactions']:
            code = trans['code']
            shares = trans['shares']
            price = trans['price']
            value = shares * price
            
            is_buy = trans['acquired_disposed'] == 'A' or code in PURCHASE_TYPES
            is_sell = trans['acquired_disposed'] == 'D' or code in SALE_TYPES
            
            if is_buy:
                sector_data[sector]['buys'] += shares
                sector_data[sector]['buy_value'] += value
                sector_data[sector]['buy_count'] += 1
                sector_data[sector]['companies'].add(ticker)
                
                role_data[role]['buys'] += shares
                role_data[role]['buy_value'] += value
            
            elif is_sell:
                sector_data[sector]['sells'] += shares
                sector_data[sector]['sell_value'] += value
                sector_data[sector]['sell_count'] += 1
                sector_data[sector]['companies'].add(ticker)
                
                role_data[role]['sells'] += shares
                role_data[role]['sell_value'] += value
            
            # Record company-level transaction
            company_transactions.append({
                'ticker': ticker,
                'company': filing['company_name'],
                'sector': sector,
                'date': trans['date'],
                'insider': form4_data['owner'].get('name', 'Unknown'),
                'role': role,
                'transaction': 'BUY' if is_buy else 'SELL',
                'shares': shares,
                'price': price,
                'value': value
            })
    
    # Calculate sector ratios and rankings
    sector_summary = []
    for sector, data in sector_data.items():
        total_value = data['buy_value'] + data['sell_value']
        buy_ratio = (data['buy_value'] / total_value * 100) if total_value > 0 else 0
        
        # Sentiment score: -100 (bearish) to +100 (bullish)
        sentiment = buy_ratio - 50
        
        sector_summary.append({
            'sector': sector,
            'buy_count': data['buy_count'],
            'sell_count': data['sell_count'],
            'buy_value': round(data['buy_value'], 2),
            'sell_value': round(data['sell_value'], 2),
            'buy_ratio': round(buy_ratio, 1),
            'sentiment_score': round(sentiment, 1),
            'signal': 'BULLISH' if sentiment > 20 else 'BEARISH' if sentiment < -20 else 'NEUTRAL',
            'companies_count': len(data['companies'])
        })
    
    # Sort by absolute sentiment (most extreme signals first)
    sector_summary.sort(key=lambda x: abs(x['sentiment_score']), reverse=True)
    
    # Calculate role-based patterns
    role_summary = []
    for role, data in role_data.items():
        total_value = data['buy_value'] + data['sell_value']
        buy_ratio = (data['buy_value'] / total_value * 100) if total_value > 0 else 0
        
        role_summary.append({
            'role': role,
            'buy_value': round(data['buy_value'], 2),
            'sell_value': round(data['sell_value'], 2),
            'buy_ratio': round(buy_ratio, 1),
            'signal': 'BULLISH' if buy_ratio > 70 else 'BEARISH' if buy_ratio < 30 else 'NEUTRAL'
        })
    
    # Sort recent large transactions
    large_transactions = sorted(
        [t for t in company_transactions if t['value'] > 100000],
        key=lambda x: x['value'],
        reverse=True
    )[:20]
    
    return {
        'period_days': days,
        'filings_analyzed': len(filings),
        'transactions_found': len(company_transactions),
        'sector_heatmap': sector_summary,
        'role_patterns': role_summary,
        'top_large_transactions': large_transactions,
        'generated_at': datetime.now().isoformat()
    }


def get_sector_insider_cluster(sector: str, days: int = 30) -> Dict:
    """
    Deep dive into insider transactions for a specific sector
    Identify coordinated buying/selling clusters
    
    Args:
        sector: Sector name (e.g., 'Technology', 'Healthcare')
        days: Lookback period
    
    Returns:
        Detailed sector insider activity with cluster detection
    """
    summary = get_insider_transaction_summary(days=days, limit=200)
    
    if 'error' in summary:
        return summary
    
    # Filter to target sector
    sector_transactions = [
        t for t in summary.get('top_large_transactions', [])
        if t['sector'].lower() == sector.lower()
    ]
    
    if not sector_transactions:
        return {'error': f'No transactions found for sector: {sector}'}
    
    # Group by company
    company_groups = defaultdict(list)
    for trans in sector_transactions:
        company_groups[trans['ticker']].append(trans)
    
    # Identify clusters (multiple insiders buying/selling same company)
    clusters = []
    for ticker, transactions in company_groups.items():
        if len(transactions) >= 2:
            buy_count = sum(1 for t in transactions if t['transaction'] == 'BUY')
            sell_count = sum(1 for t in transactions if t['transaction'] == 'SELL')
            total_value = sum(t['value'] for t in transactions)
            
            clusters.append({
                'ticker': ticker,
                'company': transactions[0]['company'],
                'insider_count': len(set(t['insider'] for t in transactions)),
                'buy_count': buy_count,
                'sell_count': sell_count,
                'total_value': round(total_value, 2),
                'signal': 'BULLISH' if buy_count > sell_count else 'BEARISH',
                'transactions': transactions
            })
    
    clusters.sort(key=lambda x: x['total_value'], reverse=True)
    
    return {
        'sector': sector,
        'period_days': days,
        'total_transactions': len(sector_transactions),
        'companies_with_activity': len(company_groups),
        'clusters_detected': len(clusters),
        'cluster_analysis': clusters[:10],  # Top 10 clusters
        'generated_at': datetime.now().isoformat()
    }


def get_ticker_insider_activity(ticker: str, days: int = 90) -> Dict:
    """
    Get insider transaction history for a specific ticker
    
    Args:
        ticker: Stock ticker symbol
        days: Lookback period
    
    Returns:
        Insider transaction summary for ticker
    """
    try:
        # Get CIK for ticker
        cik_map = get_company_tickers()
        cik = None
        company_name = None
        
        for c, data in cik_map.items():
            if data['ticker'] == ticker.upper():
                cik = c
                company_name = data['title']
                break
        
        if not cik:
            return {'error': f'Ticker {ticker} not found in SEC database'}
        
        # Fetch Form 4 filings for this company
        url = f"{EDGAR_BASE_URL}/cgi-bin/browse-edgar"
        params = {
            'action': 'getcompany',
            'CIK': cik,
            'type': '4',
            'dateb': '',
            'owner': 'include',
            'count': 40,
            'output': 'atom'
        }
        
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return {'error': 'Failed to fetch SEC filings'}
        
        root = ET.fromstring(response.content)
        
        from datetime import timezone
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        transactions = []
        
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            try:
                updated = entry.find('{http://www.w3.org/2005/Atom}updated').text
                filing_date = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                
                if filing_date < cutoff_date:
                    continue
                
                filing_url = None
                for link in entry.findall('{http://www.w3.org/2005/Atom}link'):
                    if link.get('type') == 'text/html':
                        filing_url = link.get('href')
                        break
                
                if not filing_url:
                    continue
                
                # Parse Form 4
                form4_data = parse_form4_xml(filing_url)
                
                if not form4_data or not form4_data.get('transactions'):
                    continue
                
                owner = form4_data.get('owner', {})
                role = classify_insider_role(owner)
                
                for trans in form4_data['transactions']:
                    is_buy = trans['acquired_disposed'] == 'A'
                    
                    transactions.append({
                        'date': trans['date'],
                        'insider': owner.get('name', 'Unknown'),
                        'role': role,
                        'title': owner.get('officer_title', ''),
                        'transaction': 'BUY' if is_buy else 'SELL',
                        'shares': trans['shares'],
                        'price': trans['price'],
                        'value': round(trans['shares'] * trans['price'], 2)
                    })
                
            except Exception as e:
                continue
        
        # Calculate summary metrics
        buy_count = sum(1 for t in transactions if t['transaction'] == 'BUY')
        sell_count = sum(1 for t in transactions if t['transaction'] == 'SELL')
        buy_value = sum(t['value'] for t in transactions if t['transaction'] == 'BUY')
        sell_value = sum(t['value'] for t in transactions if t['transaction'] == 'SELL')
        
        total_value = buy_value + sell_value
        buy_ratio = (buy_value / total_value * 100) if total_value > 0 else 0
        
        return {
            'ticker': ticker,
            'company': company_name,
            'cik': cik,
            'period_days': days,
            'total_transactions': len(transactions),
            'buy_count': buy_count,
            'sell_count': sell_count,
            'buy_value': round(buy_value, 2),
            'sell_value': round(sell_value, 2),
            'buy_ratio': round(buy_ratio, 1),
            'signal': 'BULLISH' if buy_ratio > 70 else 'BEARISH' if buy_ratio < 30 else 'NEUTRAL',
            'transactions': sorted(transactions, key=lambda x: x['date'], reverse=True)
        }
        
    except Exception as e:
        return {'error': f'Failed to analyze ticker {ticker}: {str(e)}'}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python insider_transaction_heatmap.py insider-summary [--days DAYS]")
        print("  python insider_transaction_heatmap.py insider-sector SECTOR_NAME [--days DAYS]")
        print("  python insider_transaction_heatmap.py insider-ticker TICKER [--days DAYS]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Parse optional --days argument
    days_arg = None
    for i, arg in enumerate(sys.argv):
        if arg == '--days' and i + 1 < len(sys.argv):
            days_arg = int(sys.argv[i + 1])
            break
    
    if command in ['summary', 'insider-summary']:
        days = days_arg if days_arg is not None else 7
        result = get_insider_transaction_summary(days=days)
        print(json.dumps(result, indent=2, default=str))
    
    elif command in ['sector', 'insider-sector']:
        if len(sys.argv) < 3:
            print("Error: Sector name required")
            sys.exit(1)
        sector = sys.argv[2]
        days = days_arg if days_arg is not None else 30
        result = get_sector_insider_cluster(sector, days=days)
        print(json.dumps(result, indent=2, default=str))
    
    elif command in ['ticker', 'insider-ticker']:
        if len(sys.argv) < 3:
            print("Error: Ticker symbol required")
            sys.exit(1)
        ticker = sys.argv[2].upper()
        days = days_arg if days_arg is not None else 90
        result = get_ticker_insider_activity(ticker, days=days)
        print(json.dumps(result, indent=2, default=str))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
