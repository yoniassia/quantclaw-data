#!/usr/bin/env python3
"""
SEC EDGAR Company Facts API — Phase 701
Direct access to XBRL-formatted company financials from SEC filings (10-K, 10-Q, 8-K).

Data includes:
- Income statement: Revenue, net income, EPS, operating income, COGS
- Balance sheet: Assets, liabilities, equity, cash, debt
- Cash flow: Operating cash flow, investing cash flow, financing cash flow
- Key metrics: Shares outstanding, dividends, R&D expenses

Usage:
  python modules/sec_edgar_company_facts.py --cik 0000320193  # Apple
  python modules/sec_edgar_company_facts.py --ticker AAPL --json
  from modules.sec_edgar_company_facts import get_company_facts
  data = get_company_facts('AAPL')

Data source: https://data.sec.gov/api/xbrl/companyfacts/
Free tier: Completely free, no API key needed, just requires user-agent header
Update frequency: Real-time as filings are submitted
"""

import requests
import json
import sys
import argparse
from datetime import datetime
from typing import Dict, Any, Optional, List

class SECEdgarCompanyFacts:
    """Fetch XBRL company facts from SEC EDGAR API"""
    
    BASE_URL = "https://data.sec.gov/api/xbrl/companyfacts"
    CIK_LOOKUP_URL = "https://www.sec.gov/cgi-bin/browse-edgar"
    
    def __init__(self):
        self.session = requests.Session()
        # SEC requires user-agent header
        self.session.headers.update({
            'User-Agent': 'QuantClawData/1.0 (contact@moneyclaw.com)',
            'Accept': 'application/json'
        })
    
    def _format_cik(self, cik: str) -> str:
        """Format CIK to 10-digit zero-padded string"""
        return str(cik).zfill(10)
    
    def get_company_facts(self, cik: str) -> Dict[str, Any]:
        """
        Get all company facts for a given CIK.
        
        Args:
            cik: Company CIK number (e.g., '0000320193' for Apple)
        
        Returns:
            Dict with:
            - cik: Company CIK
            - entity_name: Company name
            - facts: Nested dict of all XBRL facts by taxonomy
            - timestamp: ISO timestamp
        """
        cik = self._format_cik(cik)
        
        try:
            url = f"{self.BASE_URL}/CIK{cik}.json"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 404:
                return {'error': f'CIK {cik} not found', 'cik': cik}
            
            response.raise_for_status()
            data = response.json()
            
            return {
                'cik': data.get('cik'),
                'entity_name': data.get('entityName'),
                'facts': data.get('facts', {}),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except requests.RequestException as e:
            return {'error': f'HTTP error: {str(e)}', 'cik': cik}
        except json.JSONDecodeError as e:
            return {'error': f'JSON parse error: {str(e)}', 'cik': cik}
    
    def get_latest_financials(self, cik: str, taxonomy: str = 'us-gaap') -> Dict[str, Any]:
        """
        Extract latest financial metrics from company facts.
        
        Args:
            cik: Company CIK
            taxonomy: XBRL taxonomy ('us-gaap', 'dei', or 'ifrs-full')
        
        Returns:
            Dict with latest values for key financial metrics:
            - revenue (Revenues)
            - net_income (NetIncomeLoss)
            - assets (Assets)
            - liabilities (Liabilities)
            - equity (StockholdersEquity)
            - cash (CashAndCashEquivalentsAtCarryingValue)
            - eps (EarningsPerShareBasic)
            - shares_outstanding (CommonStockSharesOutstanding)
        """
        facts = self.get_company_facts(cik)
        
        if 'error' in facts:
            return facts
        
        taxonomy_facts = facts.get('facts', {}).get(taxonomy, {})
        
        latest = {
            'cik': facts['cik'],
            'entity_name': facts['entity_name'],
            'taxonomy': taxonomy,
            'metrics': {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Map of XBRL tags to friendly names
        key_metrics = {
            'Revenues': 'revenue',
            'NetIncomeLoss': 'net_income',
            'Assets': 'assets',
            'Liabilities': 'liabilities',
            'StockholdersEquity': 'equity',
            'CashAndCashEquivalentsAtCarryingValue': 'cash',
            'EarningsPerShareBasic': 'eps',
            'CommonStockSharesOutstanding': 'shares_outstanding',
            'OperatingIncomeLoss': 'operating_income',
            'GrossProfit': 'gross_profit',
            'CostOfRevenue': 'cogs',
            'ResearchAndDevelopmentExpense': 'rd_expense',
            'LongTermDebt': 'long_term_debt',
            'ShortTermDebt': 'short_term_debt'
        }
        
        for xbrl_tag, metric_name in key_metrics.items():
            if xbrl_tag in taxonomy_facts:
                metric_data = taxonomy_facts[xbrl_tag]
                # Get the latest value from USD units
                usd_data = metric_data.get('units', {}).get('USD', [])
                if usd_data:
                    # Sort by filing date and get the most recent
                    sorted_data = sorted(usd_data, key=lambda x: x.get('filed', ''), reverse=True)
                    latest_entry = sorted_data[0]
                    latest['metrics'][metric_name] = {
                        'value': latest_entry.get('val'),
                        'end_date': latest_entry.get('end'),
                        'filed': latest_entry.get('filed'),
                        'form': latest_entry.get('form'),
                        'fy': latest_entry.get('fy'),
                        'fp': latest_entry.get('fp')
                    }
        
        return latest
    
    def get_metric_history(self, cik: str, metric: str, taxonomy: str = 'us-gaap') -> Dict[str, Any]:
        """
        Get historical time series for a specific metric.
        
        Args:
            cik: Company CIK
            metric: XBRL tag (e.g., 'Revenues', 'NetIncomeLoss')
            taxonomy: XBRL taxonomy ('us-gaap', 'dei', or 'ifrs-full')
        
        Returns:
            Dict with:
            - cik, entity_name, metric, taxonomy
            - history: List of all reported values with dates
        """
        facts = self.get_company_facts(cik)
        
        if 'error' in facts:
            return facts
        
        taxonomy_facts = facts.get('facts', {}).get(taxonomy, {})
        
        if metric not in taxonomy_facts:
            return {
                'error': f'Metric {metric} not found in {taxonomy} taxonomy',
                'available_metrics': list(taxonomy_facts.keys())[:20]
            }
        
        metric_data = taxonomy_facts[metric]
        usd_data = metric_data.get('units', {}).get('USD', [])
        
        # Sort by end date
        history = sorted(usd_data, key=lambda x: x.get('end', ''), reverse=True)
        
        return {
            'cik': facts['cik'],
            'entity_name': facts['entity_name'],
            'taxonomy': taxonomy,
            'metric': metric,
            'label': metric_data.get('label', metric),
            'description': metric_data.get('description', ''),
            'history': history[:50],  # Limit to most recent 50 filings
            'total_count': len(history),
            'timestamp': datetime.utcnow().isoformat()
        }


# Convenience functions for direct import
def get_company_facts(cik: str) -> Dict[str, Any]:
    """Get all company facts for a CIK"""
    api = SECEdgarCompanyFacts()
    return api.get_company_facts(cik)


def get_latest_financials(cik: str) -> Dict[str, Any]:
    """Get latest financial metrics for a CIK"""
    api = SECEdgarCompanyFacts()
    return api.get_latest_financials(cik)


def get_metric_history(cik: str, metric: str) -> Dict[str, Any]:
    """Get historical time series for a specific metric"""
    api = SECEdgarCompanyFacts()
    return api.get_metric_history(cik, metric)


def main():
    parser = argparse.ArgumentParser(description='SEC EDGAR Company Facts API')
    parser.add_argument('--cik', help='Company CIK number')
    parser.add_argument('--ticker', help='Stock ticker (will try to look up CIK)')
    parser.add_argument('--metric', help='Specific XBRL metric to fetch (e.g., Revenues)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    # Simple CIK lookup for common tickers (expand as needed)
    ticker_to_cik = {
        'AAPL': '0000320193',
        'MSFT': '0000789019',
        'GOOGL': '0001652044',
        'AMZN': '0001018724',
        'TSLA': '0001318605',
        'META': '0001326801',
        'NVDA': '0001045810',
        'JPM': '0000019617',
        'V': '0001403161',
        'WMT': '0000104169'
    }
    
    cik = args.cik
    if args.ticker:
        cik = ticker_to_cik.get(args.ticker.upper())
        if not cik:
            print(json.dumps({'error': f'CIK lookup for {args.ticker} not available. Use --cik instead.'}))
            sys.exit(1)
    
    if not cik:
        parser.print_help()
        sys.exit(1)
    
    api = SECEdgarCompanyFacts()
    
    if args.metric:
        result = api.get_metric_history(cik, args.metric)
    else:
        result = api.get_latest_financials(cik)
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
