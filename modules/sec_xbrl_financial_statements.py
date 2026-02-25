#!/usr/bin/env python3
"""
SEC XBRL Financial Statements Module — Phase 134

Machine-readable quarterly and annual financial statements for all US public companies
Structured data from SEC XBRL filings (eXtensible Business Reporting Language)

Data Sources:
- SEC EDGAR Company Facts API: https://data.sec.gov/api/xbrl/companyfacts/
- SEC EDGAR Submissions API: https://data.sec.gov/submissions/
- No API key required

Coverage:
- Income Statement: Revenue, COGS, Operating Income, Net Income, EPS
- Balance Sheet: Assets, Liabilities, Equity, Cash, Debt
- Cash Flow: Operating CF, Investing CF, Financing CF, FCF
- Key Metrics: Shares Outstanding, Dividends, Tax Rate

Refresh: Updated within 24hrs of each 10-Q/10-K filing
Author: QUANTCLAW DATA Build Agent
Phase: 134
"""

import sys
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
import time

SEC_BASE_URL = "https://data.sec.gov"
USER_AGENT = "QuantClaw/1.0 ([email protected])"  # SEC requires user agent

# Fallback CIK mapping for common stocks (to avoid rate limiting)
COMMON_CIKS = {
    'AAPL': '0000320193',  # Apple Inc.
    'MSFT': '0000789019',  # Microsoft Corporation
    'GOOGL': '0001652044', # Alphabet Inc.
    'GOOG': '0001652044',  # Alphabet Inc.
    'AMZN': '0001018724',  # Amazon.com Inc.
    'TSLA': '0001318605',  # Tesla Inc.
    'META': '0001326801',  # Meta Platforms Inc.
    'NVDA': '0001045810',  # NVIDIA Corporation
    'BRK.B': '0001067983', # Berkshire Hathaway Inc.
    'V': '0001403161',     # Visa Inc.
    'JNJ': '0000200406',   # Johnson & Johnson
    'WMT': '0000104169',   # Walmart Inc.
    'JPM': '0000019617',   # JPMorgan Chase & Co.
    'MA': '0001141391',    # Mastercard Incorporated
    'PG': '0000080424',    # Procter & Gamble
    'UNH': '0000731766',   # UnitedHealth Group
    'DIS': '0001744489',   # Walt Disney Company
    'HD': '0000354950',    # Home Depot
    'BAC': '0000070858',   # Bank of America
    'NFLX': '0001065280',  # Netflix Inc.
}

# Common XBRL taxonomy tags for financial statements
XBRL_TAGS = {
    # Income Statement
    'revenue': [
        'Revenues',
        'RevenueFromContractWithCustomerExcludingAssessedTax',
        'SalesRevenueNet',
        'RevenueFromContractWithCustomer'
    ],
    'cost_of_revenue': [
        'CostOfRevenue',
        'CostOfGoodsAndServicesSold',
        'CostOfGoodsSold'
    ],
    'gross_profit': [
        'GrossProfit'
    ],
    'operating_income': [
        'OperatingIncomeLoss',
        'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest'
    ],
    'net_income': [
        'NetIncomeLoss',
        'ProfitLoss'
    ],
    'eps_basic': [
        'EarningsPerShareBasic'
    ],
    'eps_diluted': [
        'EarningsPerShareDiluted'
    ],
    
    # Balance Sheet
    'total_assets': [
        'Assets'
    ],
    'current_assets': [
        'AssetsCurrent'
    ],
    'cash': [
        'CashAndCashEquivalentsAtCarryingValue',
        'Cash'
    ],
    'total_liabilities': [
        'Liabilities'
    ],
    'current_liabilities': [
        'LiabilitiesCurrent'
    ],
    'long_term_debt': [
        'LongTermDebtNoncurrent',
        'LongTermDebt'
    ],
    'stockholders_equity': [
        'StockholdersEquity',
        'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'
    ],
    
    # Cash Flow Statement
    'operating_cash_flow': [
        'NetCashProvidedByUsedInOperatingActivities'
    ],
    'investing_cash_flow': [
        'NetCashProvidedByUsedInInvestingActivities'
    ],
    'financing_cash_flow': [
        'NetCashProvidedByUsedInFinancingActivities'
    ],
    'capital_expenditure': [
        'PaymentsToAcquirePropertyPlantAndEquipment'
    ],
    
    # Shares and Dividends
    'shares_outstanding': [
        'CommonStockSharesOutstanding',
        'WeightedAverageNumberOfSharesOutstandingBasic'
    ],
    'dividends_paid': [
        'PaymentsOfDividends',
        'DividendsCash'
    ]
}


def get_cik_from_ticker(ticker: str) -> Optional[str]:
    """
    Convert ticker symbol to CIK (Central Index Key) using SEC ticker mapping
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
    
    Returns:
        CIK as 10-digit zero-padded string, or None if not found
    """
    ticker_upper = ticker.upper()
    
    # Check fallback mapping first (avoids rate limiting)
    if ticker_upper in COMMON_CIKS:
        return COMMON_CIKS[ticker_upper]
    
    try:
        # SEC maintains a ticker-to-CIK mapping JSON file
        headers = {'User-Agent': USER_AGENT}
        # Note: This file is on www.sec.gov, not data.sec.gov
        url = "https://www.sec.gov/files/company_tickers.json"
        
        # Add delay to avoid rate limiting
        time.sleep(0.2)
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        companies = response.json()
        
        # Search for ticker in the mapping
        for company_data in companies.values():
            if company_data.get('ticker', '').upper() == ticker_upper:
                cik = str(company_data['cik_str']).zfill(10)
                return cik
        
        return None
    except Exception as e:
        print(f"Error converting ticker to CIK: {e}", file=sys.stderr)
        print(f"Note: Add {ticker_upper} to COMMON_CIKS mapping if needed", file=sys.stderr)
        return None


def get_company_facts(cik: str) -> Optional[Dict]:
    """
    Fetch all XBRL facts for a company from SEC EDGAR
    
    Args:
        cik: 10-digit CIK code (zero-padded)
    
    Returns:
        Dictionary of company facts or None on error
    """
    try:
        headers = {'User-Agent': USER_AGENT}
        url = f"{SEC_BASE_URL}/api/xbrl/companyfacts/CIK{cik}.json"
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"No XBRL data found for CIK {cik}", file=sys.stderr)
        else:
            print(f"HTTP error fetching company facts: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error fetching company facts: {e}", file=sys.stderr)
        return None


def extract_metric_value(facts: Dict, metric_tags: List[str], form_type: str = '10-K', 
                         fiscal_year: Optional[int] = None) -> Optional[float]:
    """
    Extract a specific metric value from SEC company facts
    
    Args:
        facts: Company facts dictionary from SEC API
        metric_tags: List of possible XBRL tag names for this metric
        form_type: Filing type ('10-K' for annual, '10-Q' for quarterly)
        fiscal_year: Specific fiscal year to retrieve (None for most recent)
    
    Returns:
        Metric value or None if not found
    """
    try:
        if 'facts' not in facts:
            return None
        
        # Try US-GAAP taxonomy first, then IFRS
        for taxonomy in ['us-gaap', 'ifrs-full']:
            if taxonomy not in facts['facts']:
                continue
            
            # Try each possible tag name
            for tag in metric_tags:
                if tag not in facts['facts'][taxonomy]:
                    continue
                
                tag_data = facts['facts'][taxonomy][tag]
                
                # Get USD units (most common)
                if 'units' not in tag_data:
                    continue
                
                for unit_key in ['USD', 'USD/shares', 'shares', 'pure']:
                    if unit_key not in tag_data['units']:
                        continue
                    
                    unit_data = tag_data['units'][unit_key]
                    
                    # Filter by form type
                    filtered = [item for item in unit_data if item.get('form') == form_type]
                    
                    if not filtered:
                        continue
                    
                    # Filter by fiscal year if specified
                    if fiscal_year:
                        filtered = [item for item in filtered if item.get('fy') == fiscal_year]
                    
                    if not filtered:
                        continue
                    
                    # Get most recent filing
                    sorted_data = sorted(filtered, key=lambda x: x.get('filed', ''), reverse=True)
                    
                    return sorted_data[0].get('val')
        
        return None
    except Exception as e:
        print(f"Error extracting metric: {e}", file=sys.stderr)
        return None


def get_financial_statements(ticker: str, form_type: str = '10-K', 
                             fiscal_year: Optional[int] = None) -> Dict:
    """
    Get comprehensive financial statements for a company
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        form_type: '10-K' for annual, '10-Q' for quarterly
        fiscal_year: Specific fiscal year (None for most recent)
    
    Returns:
        Dictionary with income statement, balance sheet, cash flow, and metadata
    """
    result = {
        'ticker': ticker.upper(),
        'form_type': form_type,
        'fiscal_year': fiscal_year,
        'income_statement': {},
        'balance_sheet': {},
        'cash_flow': {},
        'shares_and_dividends': {},
        'key_metrics': {},
        'metadata': {}
    }
    
    # Convert ticker to CIK
    cik = get_cik_from_ticker(ticker)
    if not cik:
        result['error'] = f"Ticker {ticker} not found in SEC database"
        return result
    
    result['metadata']['cik'] = cik
    
    # Fetch company facts
    facts = get_company_facts(cik)
    if not facts:
        result['error'] = f"No XBRL data available for {ticker}"
        return result
    
    result['metadata']['company_name'] = facts.get('entityName', '')
    
    # Extract Income Statement
    result['income_statement']['revenue'] = extract_metric_value(
        facts, XBRL_TAGS['revenue'], form_type, fiscal_year
    )
    result['income_statement']['cost_of_revenue'] = extract_metric_value(
        facts, XBRL_TAGS['cost_of_revenue'], form_type, fiscal_year
    )
    result['income_statement']['gross_profit'] = extract_metric_value(
        facts, XBRL_TAGS['gross_profit'], form_type, fiscal_year
    )
    result['income_statement']['operating_income'] = extract_metric_value(
        facts, XBRL_TAGS['operating_income'], form_type, fiscal_year
    )
    result['income_statement']['net_income'] = extract_metric_value(
        facts, XBRL_TAGS['net_income'], form_type, fiscal_year
    )
    result['income_statement']['eps_basic'] = extract_metric_value(
        facts, XBRL_TAGS['eps_basic'], form_type, fiscal_year
    )
    result['income_statement']['eps_diluted'] = extract_metric_value(
        facts, XBRL_TAGS['eps_diluted'], form_type, fiscal_year
    )
    
    # Extract Balance Sheet
    result['balance_sheet']['total_assets'] = extract_metric_value(
        facts, XBRL_TAGS['total_assets'], form_type, fiscal_year
    )
    result['balance_sheet']['current_assets'] = extract_metric_value(
        facts, XBRL_TAGS['current_assets'], form_type, fiscal_year
    )
    result['balance_sheet']['cash'] = extract_metric_value(
        facts, XBRL_TAGS['cash'], form_type, fiscal_year
    )
    result['balance_sheet']['total_liabilities'] = extract_metric_value(
        facts, XBRL_TAGS['total_liabilities'], form_type, fiscal_year
    )
    result['balance_sheet']['current_liabilities'] = extract_metric_value(
        facts, XBRL_TAGS['current_liabilities'], form_type, fiscal_year
    )
    result['balance_sheet']['long_term_debt'] = extract_metric_value(
        facts, XBRL_TAGS['long_term_debt'], form_type, fiscal_year
    )
    result['balance_sheet']['stockholders_equity'] = extract_metric_value(
        facts, XBRL_TAGS['stockholders_equity'], form_type, fiscal_year
    )
    
    # Extract Cash Flow Statement
    result['cash_flow']['operating_cash_flow'] = extract_metric_value(
        facts, XBRL_TAGS['operating_cash_flow'], form_type, fiscal_year
    )
    result['cash_flow']['investing_cash_flow'] = extract_metric_value(
        facts, XBRL_TAGS['investing_cash_flow'], form_type, fiscal_year
    )
    result['cash_flow']['financing_cash_flow'] = extract_metric_value(
        facts, XBRL_TAGS['financing_cash_flow'], form_type, fiscal_year
    )
    result['cash_flow']['capital_expenditure'] = extract_metric_value(
        facts, XBRL_TAGS['capital_expenditure'], form_type, fiscal_year
    )
    
    # Calculate Free Cash Flow if possible
    ocf = result['cash_flow']['operating_cash_flow']
    capex = result['cash_flow']['capital_expenditure']
    if ocf is not None and capex is not None:
        result['cash_flow']['free_cash_flow'] = ocf - abs(capex)
    
    # Extract Shares and Dividends
    result['shares_and_dividends']['shares_outstanding'] = extract_metric_value(
        facts, XBRL_TAGS['shares_outstanding'], form_type, fiscal_year
    )
    result['shares_and_dividends']['dividends_paid'] = extract_metric_value(
        facts, XBRL_TAGS['dividends_paid'], form_type, fiscal_year
    )
    
    # Calculate Key Metrics
    revenue = result['income_statement'].get('revenue')
    net_income = result['income_statement'].get('net_income')
    total_assets = result['balance_sheet'].get('total_assets')
    stockholders_equity = result['balance_sheet'].get('stockholders_equity')
    
    if revenue and revenue > 0:
        if net_income:
            result['key_metrics']['profit_margin'] = (net_income / revenue) * 100
        
        if total_assets:
            result['key_metrics']['asset_turnover'] = revenue / total_assets
    
    if total_assets and total_assets > 0 and net_income:
        result['key_metrics']['roa'] = (net_income / total_assets) * 100
    
    if stockholders_equity and stockholders_equity > 0 and net_income:
        result['key_metrics']['roe'] = (net_income / stockholders_equity) * 100
    
    total_liabilities = result['balance_sheet'].get('total_liabilities')
    if stockholders_equity and stockholders_equity > 0 and total_liabilities:
        result['key_metrics']['debt_to_equity'] = total_liabilities / stockholders_equity
    
    return result


def compare_financial_statements(ticker: str, years: List[int], form_type: str = '10-K') -> Dict:
    """
    Compare financial statements across multiple fiscal years
    
    Args:
        ticker: Stock ticker symbol
        years: List of fiscal years to compare
        form_type: '10-K' for annual, '10-Q' for quarterly
    
    Returns:
        Dictionary with year-over-year comparison and trends
    """
    result = {
        'ticker': ticker.upper(),
        'form_type': form_type,
        'years': years,
        'data': [],
        'trends': {}
    }
    
    # Fetch data for each year
    for year in sorted(years):
        stmt = get_financial_statements(ticker, form_type, year)
        if 'error' not in stmt:
            result['data'].append({
                'year': year,
                'statements': stmt
            })
    
    if len(result['data']) < 2:
        result['error'] = "Insufficient data for comparison"
        return result
    
    # Calculate trends
    def calculate_trend(metric_path):
        values = []
        for year_data in result['data']:
            # Navigate nested dict
            val = year_data['statements']
            for key in metric_path.split('.'):
                if isinstance(val, dict):
                    val = val.get(key)
                else:
                    val = None
                    break
            if val is not None:
                values.append((year_data['year'], val))
        
        if len(values) >= 2:
            growth_rates = []
            for i in range(1, len(values)):
                prev_val = values[i-1][1]
                curr_val = values[i][1]
                if prev_val != 0:
                    growth = ((curr_val - prev_val) / abs(prev_val)) * 100
                    growth_rates.append(growth)
            
            if growth_rates:
                return {
                    'values': values,
                    'cagr': sum(growth_rates) / len(growth_rates),
                    'latest_growth': growth_rates[-1] if growth_rates else None
                }
        return None
    
    # Calculate trends for key metrics
    trend_metrics = [
        'income_statement.revenue',
        'income_statement.net_income',
        'cash_flow.operating_cash_flow',
        'cash_flow.free_cash_flow',
        'balance_sheet.total_assets',
        'balance_sheet.stockholders_equity'
    ]
    
    for metric in trend_metrics:
        trend = calculate_trend(metric)
        if trend:
            result['trends'][metric] = trend
    
    return result


def search_xbrl_companies(search_term: str, limit: int = 10) -> List[Dict]:
    """
    Search for companies in SEC database
    
    Args:
        search_term: Company name or ticker fragment
        limit: Maximum results to return
    
    Returns:
        List of matching companies with ticker, CIK, and name
    """
    try:
        headers = {'User-Agent': USER_AGENT}
        url = "https://www.sec.gov/files/company_tickers.json"
        
        time.sleep(0.2)
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        companies = response.json()
        search_upper = search_term.upper()
        
        matches = []
        for company_data in companies.values():
            ticker = company_data.get('ticker', '').upper()
            name = company_data.get('title', '').upper()
            
            if search_upper in ticker or search_upper in name:
                matches.append({
                    'ticker': company_data.get('ticker'),
                    'name': company_data.get('title'),
                    'cik': str(company_data['cik_str']).zfill(10)
                })
            
            if len(matches) >= limit:
                break
        
        return matches
    except Exception as e:
        print(f"Error searching companies: {e}", file=sys.stderr)
        return []


def main():
    """CLI Interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SEC XBRL Financial Statements')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # financials command
    financials_parser = subparsers.add_parser('financials', 
                                               help='Get financial statements')
    financials_parser.add_argument('ticker', help='Stock ticker symbol')
    financials_parser.add_argument('--form', choices=['10-K', '10-Q'], default='10-K',
                                   help='Form type (10-K=annual, 10-Q=quarterly)')
    financials_parser.add_argument('--year', type=int, 
                                   help='Fiscal year (default: most recent)')
    
    # compare command
    compare_parser = subparsers.add_parser('compare',
                                           help='Compare financials across years')
    compare_parser.add_argument('ticker', help='Stock ticker symbol')
    compare_parser.add_argument('--years', type=int, nargs='+', required=True,
                               help='Fiscal years to compare')
    compare_parser.add_argument('--form', choices=['10-K', '10-Q'], default='10-K',
                               help='Form type')
    
    # search command
    search_parser = subparsers.add_parser('search', help='Search for companies')
    search_parser.add_argument('term', help='Company name or ticker fragment')
    search_parser.add_argument('--limit', type=int, default=10,
                              help='Maximum results')
    
    # cik command
    cik_parser = subparsers.add_parser('cik', help='Get CIK from ticker')
    cik_parser.add_argument('ticker', help='Stock ticker symbol')
    
    args = parser.parse_args()
    
    if args.command == 'financials':
        result = get_financial_statements(args.ticker, args.form, args.year)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'compare':
        result = compare_financial_statements(args.ticker, args.years, args.form)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'search':
        results = search_xbrl_companies(args.term, args.limit)
        print(json.dumps(results, indent=2))
    
    elif args.command == 'cik':
        cik = get_cik_from_ticker(args.ticker)
        if cik:
            print(json.dumps({'ticker': args.ticker, 'cik': cik}, indent=2))
        else:
            print(json.dumps({'error': f"Ticker {args.ticker} not found"}, indent=2))
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
