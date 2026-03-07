#!/usr/bin/env python3
"""
SEC EDGAR 13F API — Institutional Holdings & Manager Filings
Access 13F filings, which detail institutional investment managers' quarterly holdings of U.S. equities.

Data includes:
- 13F filings list by CIK (Central Index Key)
- Holdings details from specific or latest filing
- Manager search by name (basic implementation)
- CIK lookup by exact company name

Usage:
  python modules/sec_edgar_13f_api.py --cik 0001067983 --filings
  python modules/sec_edgar_13f_api.py --cik 0001067983 --holdings
  python modules/sec_edgar_13f_api.py --lookup "BERKSHIRE HATHAWAY INC"

Data source: https://www.sec.gov/edgar/api & https://data.sec.gov/
Free tier: 10 requests/second (requires User-Agent header)
"""

import requests
import json
import re
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import argparse
import sys
from xml.etree import ElementTree as ET

class SecEdgar13FAPI:
    """SEC EDGAR 13F API wrapper for institutional holdings data"""
    
    BASE_URL = "https://data.sec.gov"
    EFTS_URL = "https://efts.sec.gov/LATEST"
    USER_AGENT = "QuantClaw quantclaw@example.com"
    
    # Common institutional investor CIKs for testing
    KNOWN_CIKS = {
        'BERKSHIRE HATHAWAY': '0001067983',
        'VANGUARD': '0000102909',
        'BLACKROCK': '0001086364',
        'STATE STREET': '0000093751',
        'BRIDGEWATER': '0001350694',
        'RENAISSANCE': '0001037389',
        'CITADEL': '0001423053',
        'TIGER GLOBAL': '0001167483',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.USER_AGENT,
            'Accept': 'application/json'
        })
        self.rate_limit_delay = 0.11  # ~9 req/sec to stay under 10/sec limit
    
    def lookup_cik(self, query: str) -> Dict[str, Any]:
        """
        Resolve company/manager name to CIK (basic implementation using known CIKs).
        
        For full CIK lookup, use SEC's EDGAR search or company_tickers endpoint when available.
        This is a simplified version for common institutional investors.
        
        Args:
            query: Company/manager name
            
        Returns:
            {
                'cik': '0001067983',
                'name': 'BERKSHIRE HATHAWAY INC',
                'source': 'known_ciks',
                'error': None
            }
        """
        query_upper = query.upper().strip()
        
        # Check known CIKs first
        for name, cik in self.KNOWN_CIKS.items():
            if name in query_upper or query_upper in name:
                return {
                    'cik': cik,
                    'name': name,
                    'source': 'known_ciks',
                    'error': None
                }
        
        # If not found, try to fetch submissions to validate CIK if provided as number
        if query.strip().isdigit():
            cik_test = query.strip().zfill(10)
            try:
                url = f"{self.BASE_URL}/submissions/CIK{cik_test}.json"
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'cik': cik_test,
                        'name': data.get('name', 'Unknown'),
                        'source': 'submissions_api',
                        'error': None
                    }
                time.sleep(self.rate_limit_delay)
            except:
                pass
        
        return {
            'error': f'CIK not found for: {query}. Try using numeric CIK directly.',
            'hint': f'Known managers: {", ".join(self.KNOWN_CIKS.keys())}'
        }
    
    def search_managers(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for institutional managers by name (basic implementation).
        
        Args:
            query: Manager name search term
            limit: Maximum results to return
            
        Returns:
            [
                {
                    'cik': '0001067983',
                    'name': 'BERKSHIRE HATHAWAY',
                    'matches': True
                },
                ...
            ]
        """
        query_upper = query.upper().strip()
        results = []
        
        for name, cik in self.KNOWN_CIKS.items():
            if query_upper in name:
                results.append({
                    'cik': cik,
                    'name': name,
                    'matches': True
                })
                
                if len(results) >= limit:
                    break
        
        if not results:
            results.append({
                'error': f'No matches for: {query}',
                'hint': f'Known managers: {", ".join(self.KNOWN_CIKS.keys())}'
            })
        
        return results
    
    def get_13f_filings(self, cik: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List 13F filings for a manager by CIK.
        
        Args:
            cik: Central Index Key (with or without leading zeros)
            limit: Maximum number of filings to return
            
        Returns:
            [
                {
                    'accession_number': '0001193125-21-123456',
                    'filing_date': '2021-05-17',
                    'report_date': '2021-03-31',
                    'form': '13F-HR',
                    'file_number': '028-12345',
                    'cik': '0001067983'
                },
                ...
            ]
        """
        try:
            # Normalize CIK (pad with zeros to 10 digits)
            cik_str = str(cik).strip().lstrip('0')
            if not cik_str:
                return [{'error': 'Invalid CIK'}]
            
            cik_padded = cik_str.zfill(10)
            
            url = f"{self.BASE_URL}/submissions/CIK{cik_padded}.json"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            time.sleep(self.rate_limit_delay)
            
            data = response.json()
            filings = data.get('filings', {}).get('recent', {})
            
            # Extract 13F filings
            forms = filings.get('form', [])
            accession_numbers = filings.get('accessionNumber', [])
            filing_dates = filings.get('filingDate', [])
            report_dates = filings.get('reportDate', [])
            file_numbers = filings.get('fileNumber', [])
            primary_documents = filings.get('primaryDocument', [])
            
            results = []
            for i, form in enumerate(forms):
                if '13F' in form:
                    results.append({
                        'accession_number': accession_numbers[i],
                        'filing_date': filing_dates[i],
                        'report_date': report_dates[i],
                        'form': form,
                        'file_number': file_numbers[i] if i < len(file_numbers) else None,
                        'primary_document': primary_documents[i] if i < len(primary_documents) else None,
                        'cik': cik_padded
                    })
                    
                    if len(results) >= limit:
                        break
            
            if not results:
                return [{'error': 'No 13F filings found', 'cik': cik_padded}]
            
            return results
            
        except requests.RequestException as e:
            return [{'error': f'HTTP error: {str(e)}', 'cik': cik}]
        except Exception as e:
            return [{'error': f'Filings error: {str(e)}', 'cik': cik}]
    
    def get_13f_holdings(self, cik: str, accession_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse holdings from latest or specific 13F filing.
        
        Args:
            cik: Central Index Key
            accession_number: Specific filing accession number (optional, uses latest if None)
            
        Returns:
            {
                'cik': '0001067983',
                'name': 'BERKSHIRE HATHAWAY INC',
                'report_date': '2021-03-31',
                'filing_date': '2021-05-17',
                'accession_number': '0001193125-21-123456',
                'total_value': 280500000000,
                'holdings_count': 45,
                'holdings': [
                    {
                        'name': 'APPLE INC',
                        'cusip': '037833100',
                        'value': 120000000000,
                        'shares': 887136600,
                        'weight_pct': 42.85
                    },
                    ...
                ]
            }
        """
        try:
            # Get filings if no accession number provided
            if not accession_number:
                filings = self.get_13f_filings(cik, limit=1)
                if not filings or 'error' in filings[0]:
                    return {'error': 'No 13F filings found', 'cik': cik}
                accession_number = filings[0]['accession_number']
                report_date = filings[0]['report_date']
                filing_date = filings[0]['filing_date']
            else:
                # Need to get dates from filing
                filings = self.get_13f_filings(cik, limit=50)
                filing_info = next((f for f in filings if f.get('accession_number') == accession_number), None)
                if filing_info:
                    report_date = filing_info['report_date']
                    filing_date = filing_info['filing_date']
                else:
                    report_date = 'N/A'
                    filing_date = 'N/A'
            
            # Normalize CIK and accession number
            cik_str = str(cik).strip().lstrip('0').zfill(10)
            accession_clean = accession_number.replace('-', '')
            
            # Get company name
            name_url = f"{self.BASE_URL}/submissions/CIK{cik_str}.json"
            name_response = self.session.get(name_url, timeout=10)
            company_name = name_response.json().get('name', 'N/A') if name_response.status_code == 200 else 'N/A'
            time.sleep(self.rate_limit_delay)
            
            # Build path to filing documents
            base_path = f"{self.BASE_URL}/Archives/edgar/data/{int(cik_str)}/{accession_clean}"
            
            # Try to find and parse information table XML
            # Common filenames: primary_doc.xml, informationTable.xml, form13fInfoTable.xml
            info_table_file = None
            for pattern in ['primary_doc.xml', 'informationTable.xml', 'form13fInfoTable.xml', 'infotable.xml']:
                test_url = f"{base_path}/{pattern}"
                try:
                    test_response = self.session.get(test_url, timeout=5)
                    if test_response.status_code == 200 and '<informationTable' in test_response.text:
                        info_table_file = pattern
                        xml_content = test_response.content
                        break
                    time.sleep(self.rate_limit_delay)
                except:
                    continue
            
            if not info_table_file:
                return {
                    'error': 'Could not find information table XML',
                    'cik': cik_str,
                    'name': company_name,
                    'accession_number': accession_number,
                    'hint': 'Try accessing filing directly via SEC EDGAR website'
                }
            
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Extract holdings
            holdings = []
            total_value = 0
            
            # Find all infoTable entries (handle namespaces)
            for info_table in root.iter():
                if 'infoTable' in info_table.tag:
                    name = None
                    cusip = None
                    value = None
                    shares = None
                    
                    for child in info_table:
                        tag_name = child.tag.split('}')[-1]  # Remove namespace
                        
                        if tag_name == 'nameOfIssuer':
                            name = child.text
                        elif tag_name == 'cusip':
                            cusip = child.text
                        elif tag_name == 'value':
                            value = float(child.text) * 1000 if child.text else 0  # SEC reports in thousands
                        elif tag_name == 'shrsOrPrnAmt':
                            for subchild in child:
                                sub_tag = subchild.tag.split('}')[-1]
                                if sub_tag in ['sshPrnamt', 'sshPrnamtType']:
                                    if sub_tag == 'sshPrnamt':
                                        shares = float(subchild.text) if subchild.text else 0
                    
                    if name and cusip:
                        holdings.append({
                            'name': name,
                            'cusip': cusip,
                            'value': value,
                            'shares': shares
                        })
                        total_value += value if value else 0
            
            # Calculate weights
            for holding in holdings:
                if total_value > 0 and holding['value']:
                    holding['weight_pct'] = (holding['value'] / total_value) * 100
                else:
                    holding['weight_pct'] = 0
            
            # Sort by value descending
            holdings.sort(key=lambda x: x.get('value', 0) or 0, reverse=True)
            
            return {
                'cik': cik_str,
                'name': company_name,
                'accession_number': accession_number,
                'report_date': report_date,
                'filing_date': filing_date,
                'total_value': total_value,
                'holdings_count': len(holdings),
                'holdings': holdings,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except requests.RequestException as e:
            return {'error': f'HTTP error: {str(e)}', 'cik': cik}
        except Exception as e:
            return {'error': f'Holdings parsing error: {str(e)}', 'cik': cik}
    
    def get_top_holders(self, ticker: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find top institutional holders of a stock.
        
        Note: This requires cross-referencing multiple 13F filings across all institutional
        investors. Full implementation would need a database of pre-processed filings.
        This is a placeholder that explains the limitation.
        
        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of holders to return
            
        Returns:
            [{'error': '...', 'note': '...'}]
        """
        return [{
            'error': 'get_top_holders requires database of all 13F filings',
            'note': 'This would require scanning thousands of recent 13F filings to find all holders of a given CUSIP. Best implemented with pre-processed data or commercial data provider.',
            'alternative': 'Use get_13f_holdings() with known institutional investor CIKs to see if they hold the stock.'
        }]


def main():
    parser = argparse.ArgumentParser(
        description='SEC EDGAR 13F API — Institutional Holdings Data'
    )
    
    # Command group
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--lookup', type=str, help='Lookup CIK by name (limited to known managers)')
    group.add_argument('--search', type=str, help='Search for managers by name (limited to known managers)')
    group.add_argument('--cik', type=str, help='CIK for filings or holdings query')
    
    # Options
    parser.add_argument('--filings', action='store_true', help='List 13F filings (use with --cik)')
    parser.add_argument('--holdings', action='store_true', help='Get holdings detail (use with --cik)')
    parser.add_argument('--accession', type=str, help='Specific accession number for holdings')
    parser.add_argument('--limit', type=int, default=10, help='Result limit')
    parser.add_argument('--json', action='store_true', help='Output raw JSON')
    
    args = parser.parse_args()
    
    api = SecEdgar13FAPI()
    
    # Route command
    if args.lookup:
        result = api.lookup_cik(args.lookup)
    elif args.search:
        result = api.search_managers(args.search, limit=args.limit)
    elif args.cik:
        if args.holdings:
            result = api.get_13f_holdings(args.cik, accession_number=args.accession)
        else:  # Default to filings list
            result = api.get_13f_filings(args.cik, limit=args.limit)
    else:
        parser.print_help()
        sys.exit(1)
    
    # Output
    if args.json:
        print(json.dumps(result, indent=2))
        return
    
    # Pretty print
    if isinstance(result, dict) and 'error' in result:
        print(f"❌ Error: {result['error']}")
        if 'hint' in result:
            print(f"💡 Hint: {result['hint']}")
        sys.exit(1)
    
    if args.lookup:
        print(f"\n{'='*60}")
        print(f"🔍 CIK Lookup: {args.lookup}")
        print(f"{'='*60}\n")
        print(f"  CIK:    {result.get('cik')}")
        print(f"  Name:   {result.get('name')}")
        print(f"  Source: {result.get('source')}")
        print()
    
    elif args.search:
        print(f"\n{'='*60}")
        print(f"🔍 Manager Search: {args.search}")
        print(f"{'='*60}\n")
        for i, manager in enumerate(result, 1):
            if 'error' not in manager:
                print(f"{i}. {manager['name']}")
                print(f"   CIK: {manager['cik']}")
                print()
    
    elif args.cik and args.holdings:
        print(f"\n{'='*60}")
        print(f"📊 13F Holdings: {result.get('name', 'Unknown')}")
        print(f"{'='*60}\n")
        print(f"  CIK:            {result.get('cik')}")
        print(f"  Filing Date:    {result.get('filing_date')}")
        print(f"  Report Date:    {result.get('report_date')}")
        print(f"  Total Value:    ${result.get('total_value', 0):,.0f}")
        print(f"  Holdings Count: {result.get('holdings_count', 0)}")
        print(f"\n  Top 10 Holdings:")
        for i, holding in enumerate(result.get('holdings', [])[:10], 1):
            print(f"\n  {i}. {holding['name']}")
            print(f"     CUSIP:  {holding.get('cusip')}")
            print(f"     Value:  ${holding.get('value', 0):,.0f}")
            print(f"     Shares: {holding.get('shares', 0):,.0f}")
            print(f"     Weight: {holding.get('weight_pct', 0):.2f}%")
        print()
    
    elif args.cik:
        print(f"\n{'='*60}")
        print(f"📋 13F Filings (CIK: {args.cik})")
        print(f"{'='*60}\n")
        for i, filing in enumerate(result, 1):
            if 'error' not in filing:
                print(f"{i}. {filing['form']} — {filing['filing_date']}")
                print(f"   Accession: {filing['accession_number']}")
                print(f"   Report Date: {filing['report_date']}")
                print()

if __name__ == '__main__':
    main()
