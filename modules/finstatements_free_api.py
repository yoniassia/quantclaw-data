"""
Financial Statements Free API — SEC EDGAR Company Facts

Data Source: SEC EDGAR Company Facts API (https://data.sec.gov/api/xbrl/companyfacts/)
Update: Real-time (as companies file with SEC)
History: 10+ years of filings
Free: Yes (no API key required, just User-Agent header per SEC policy)

Provides:
- Income Statement data (Revenue, NetIncome, EPS, etc.)
- Balance Sheet data (Assets, Liabilities, Equity, etc.)
- Cash Flow Statement data (OperatingCF, InvestingCF, FinancingCF)
- Key financial ratios calculated from fundamentals
- Company search by ticker/CIK

Usage:
- Fetch standardized XBRL financial data for any US public company
- Calculate fundamental ratios (P/E, ROE, Debt/Equity, etc.)
- Track earnings trends and quarterly performance
- Build fundamental factor models for quant strategies

Note: SEC data has ~1 quarter lag (filed 45 days after quarter end)
"""

import requests
import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import time

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/sec_edgar")
os.makedirs(CACHE_DIR, exist_ok=True)

# SEC requires User-Agent header with contact info
SEC_HEADERS = {
    'User-Agent': 'QuantClaw Data Module admin@moneyclaw.com',
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'data.sec.gov'
}

# Common XBRL tags for financial statements
INCOME_STATEMENT_TAGS = {
    'Revenues': 'us-gaap:Revenues',
    'RevenueFromContractWithCustomerExcludingAssessedTax': 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax',
    'NetIncomeLoss': 'us-gaap:NetIncomeLoss',
    'OperatingIncomeLoss': 'us-gaap:OperatingIncomeLoss',
    'GrossProfit': 'us-gaap:GrossProfit',
    'CostOfRevenue': 'us-gaap:CostOfRevenue',
    'OperatingExpenses': 'us-gaap:OperatingExpenses',
    'EarningsPerShareBasic': 'us-gaap:EarningsPerShareBasic',
    'EarningsPerShareDiluted': 'us-gaap:EarningsPerShareDiluted',
}

BALANCE_SHEET_TAGS = {
    'Assets': 'us-gaap:Assets',
    'Liabilities': 'us-gaap:Liabilities',
    'StockholdersEquity': 'us-gaap:StockholdersEquity',
    'AssetsCurrent': 'us-gaap:AssetsCurrent',
    'LiabilitiesCurrent': 'us-gaap:LiabilitiesCurrent',
    'CashAndCashEquivalentsAtCarryingValue': 'us-gaap:CashAndCashEquivalentsAtCarryingValue',
    'LongTermDebt': 'us-gaap:LongTermDebt',
}

CASHFLOW_TAGS = {
    'NetCashProvidedByUsedInOperatingActivities': 'us-gaap:NetCashProvidedByUsedInOperatingActivities',
    'NetCashProvidedByUsedInInvestingActivities': 'us-gaap:NetCashProvidedByUsedInInvestingActivities',
    'NetCashProvidedByUsedInFinancingActivities': 'us-gaap:NetCashProvidedByUsedInFinancingActivities',
}

def _get_cik_from_ticker(ticker: str) -> Optional[str]:
    """
    Convert ticker symbol to CIK (Central Index Key) using SEC company tickers JSON.
    SEC provides a mapping file updated daily.
    """
    cache_file = os.path.join(CACHE_DIR, "ticker_cik_map.json")
    
    # Check cache (refresh daily)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age.days < 1:
            with open(cache_file) as f:
                ticker_map = json.load(f)
        else:
            ticker_map = _fetch_ticker_map()
    else:
        ticker_map = _fetch_ticker_map()
    
    # Search for ticker (case insensitive)
    ticker_upper = ticker.upper()
    for cik, data in ticker_map.get('data', {}).items():
        if data.get('ticker', '').upper() == ticker_upper:
            return str(cik).zfill(10)  # CIK must be 10 digits with leading zeros
    
    return None

def _fetch_ticker_map() -> Dict:
    """Fetch and cache the SEC ticker->CIK mapping"""
    cache_file = os.path.join(CACHE_DIR, "ticker_cik_map.json")
    
    try:
        # Try new SEC endpoint first
        url = "https://www.sec.gov/files/company_tickers.json"
        time.sleep(0.15)
        response = requests.get(url, headers=SEC_HEADERS, timeout=10)
        
        # If 404, fall back to known tickers
        if response.status_code == 404:
            return _get_fallback_ticker_map()
        
        response.raise_for_status()
        ticker_data = response.json()
        
        # Restructure for easier lookup
        ticker_map = {'data': {}}
        for item in ticker_data.values():
            cik = str(item['cik_str']).zfill(10)
            ticker_map['data'][cik] = {
                'ticker': item['ticker'],
                'title': item['title'],
                'cik': cik
            }
        
        # Cache it
        with open(cache_file, 'w') as f:
            json.dump(ticker_map, f, indent=2)
        
        return ticker_map
        
    except Exception as e:
        print(f"⚠️  SEC ticker map unavailable, using fallback: {e}")
        return _get_fallback_ticker_map()

def _get_fallback_ticker_map() -> Dict:
    """Fallback ticker->CIK map for common stocks"""
    # Top 100 US stocks by market cap
    common_tickers = {
        'AAPL': ('0000320193', 'Apple Inc.'),
        'MSFT': ('0000789019', 'Microsoft Corp'),
        'GOOGL': ('0001652044', 'Alphabet Inc.'),
        'GOOG': ('0001652044', 'Alphabet Inc.'),
        'AMZN': ('0001018724', 'Amazon.com Inc'),
        'NVDA': ('0001045810', 'NVIDIA Corp'),
        'META': ('0001326801', 'Meta Platforms Inc'),
        'TSLA': ('0001318605', 'Tesla Inc'),
        'BRK.B': ('0001067983', 'Berkshire Hathaway Inc'),
        'V': ('0001403161', 'Visa Inc.'),
        'JPM': ('0000019617', 'JPMorgan Chase & Co'),
        'WMT': ('0000104169', 'Walmart Inc'),
        'MA': ('0001141391', 'Mastercard Inc'),
        'JNJ': ('0000200406', 'Johnson & Johnson'),
        'UNH': ('0000731766', 'UnitedHealth Group Inc'),
        'HD': ('0000354950', 'Home Depot Inc'),
        'PG': ('0000080424', 'Procter & Gamble Co'),
        'XOM': ('0000034088', 'Exxon Mobil Corp'),
        'CVX': ('0000093410', 'Chevron Corp'),
        'BAC': ('0000070858', 'Bank of America Corp'),
        'KO': ('0000021344', 'Coca-Cola Co'),
        'PEP': ('0000077476', 'PepsiCo Inc'),
        'COST': ('0000909832', 'Costco Wholesale Corp'),
        'ABBV': ('0001551152', 'AbbVie Inc'),
        'MRK': ('0000310158', 'Merck & Co Inc'),
        'AVGO': ('0001730168', 'Broadcom Inc'),
        'TMO': ('0000097745', 'Thermo Fisher Scientific Inc'),
        'NFLX': ('0001065280', 'Netflix Inc'),
        'DIS': ('0001744489', 'Walt Disney Co'),
        'ORCL': ('0001341439', 'Oracle Corp'),
        'CSCO': ('0000858877', 'Cisco Systems Inc'),
        'ADBE': ('0000796343', 'Adobe Inc'),
        'ACN': ('0001467373', 'Accenture PLC'),
        'CRM': ('0001108524', 'Salesforce Inc'),
        'INTC': ('0000050863', 'Intel Corp'),
        'AMD': ('0000002488', 'Advanced Micro Devices Inc'),
        'NKE': ('0000320187', 'Nike Inc'),
        'IBM': ('0000051143', 'International Business Machines Corp'),
        'GE': ('0000040545', 'General Electric Co'),
        'F': ('0000037996', 'Ford Motor Co'),
        'GM': ('0001467858', 'General Motors Co'),
        'T': ('0000732717', 'AT&T Inc'),
        'VZ': ('0000732712', 'Verizon Communications Inc'),
    }
    
    ticker_map = {'data': {}}
    for ticker, (cik, name) in common_tickers.items():
        ticker_map['data'][cik] = {
            'ticker': ticker,
            'title': name,
            'cik': cik
        }
    
    return ticker_map

def get_financial_statements(symbol: str, period: str = 'annual') -> Dict:
    """
    Fetch complete financial statements (Income/Balance/Cash Flow) from SEC EDGAR.
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'MSFT')
        period: 'annual' or 'quarterly' (default: 'annual')
    
    Returns:
        Dict with income_statement, balance_sheet, cash_flow sections
        Each contains latest and historical data points
    """
    cik = _get_cik_from_ticker(symbol)
    if not cik:
        return {
            'error': f'Ticker {symbol} not found in SEC database',
            'symbol': symbol
        }
    
    cache_file = os.path.join(CACHE_DIR, f"{symbol}_{cik}_facts.json")
    
    # Check cache (refresh weekly for company facts)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age.days < 7:
            with open(cache_file) as f:
                company_facts = json.load(f)
        else:
            company_facts = _fetch_company_facts(cik, symbol)
    else:
        company_facts = _fetch_company_facts(cik, symbol)
    
    if 'error' in company_facts:
        return company_facts
    
    # Extract financial statements
    facts = company_facts.get('facts', {}).get('us-gaap', {})
    
    result = {
        'symbol': symbol,
        'cik': cik,
        'company_name': company_facts.get('entityName', symbol),
        'period': period,
        'income_statement': _extract_statement_data(facts, INCOME_STATEMENT_TAGS, period),
        'balance_sheet': _extract_statement_data(facts, BALANCE_SHEET_TAGS, period),
        'cash_flow': _extract_statement_data(facts, CASHFLOW_TAGS, period),
        'data_date': datetime.now().strftime('%Y-%m-%d')
    }
    
    return result

def _fetch_company_facts(cik: str, symbol: str) -> Dict:
    """Fetch company facts from SEC EDGAR API"""
    cache_file = os.path.join(CACHE_DIR, f"{symbol}_{cik}_facts.json")
    
    try:
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        
        # SEC rate limit: 10 requests per second, be polite
        time.sleep(0.15)
        
        response = requests.get(url, headers=SEC_HEADERS, timeout=15)
        response.raise_for_status()
        
        company_facts = response.json()
        
        # Cache it
        with open(cache_file, 'w') as f:
            json.dump(company_facts, f, indent=2)
        
        return company_facts
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {'error': f'CIK {cik} not found (company may not file with SEC)', 'symbol': symbol}
        return {'error': f'HTTP error: {e}', 'symbol': symbol}
    except Exception as e:
        return {'error': f'Error fetching data: {e}', 'symbol': symbol}

def _extract_statement_data(facts: Dict, tag_map: Dict, period: str) -> Dict:
    """Extract specific financial statement line items from XBRL facts"""
    statement_data = {}
    
    for label, tag in tag_map.items():
        # Remove 'us-gaap:' prefix for lookup
        tag_key = tag.replace('us-gaap:', '')
        
        if tag_key not in facts:
            continue
        
        tag_data = facts[tag_key]
        units = tag_data.get('units', {})
        
        # Try USD first, then USD/shares for per-share metrics
        values = units.get('USD', units.get('USD/shares', []))
        
        if not values:
            continue
        
        # Filter by form type (10-K for annual, 10-Q for quarterly)
        if period == 'annual':
            filtered = [v for v in values if v.get('form') == '10-K']
        else:
            filtered = [v for v in values if v.get('form') == '10-Q']
        
        if not filtered:
            filtered = values  # Fallback to all if no form match
        
        # Get most recent value
        sorted_values = sorted(filtered, key=lambda x: x.get('end', ''), reverse=True)
        
        if sorted_values:
            latest = sorted_values[0]
            statement_data[label] = {
                'value': latest.get('val'),
                'end_date': latest.get('end'),
                'filed': latest.get('filed'),
                'form': latest.get('form'),
                'fy': latest.get('fy'),  # Fiscal year
                'fp': latest.get('fp'),  # Fiscal period
            }
    
    return statement_data

def get_earnings_data(symbol: str) -> Dict:
    """
    Get earnings data including EPS actual vs estimate, surprise %.
    
    Note: SEC data doesn't include analyst estimates, so this returns
    actual EPS and revenue from filings. For estimates, you'd need
    a paid service like FactSet or Bloomberg.
    
    Args:
        symbol: Stock ticker
    
    Returns:
        Dict with EPS history and revenue trends
    """
    statements = get_financial_statements(symbol, period='quarterly')
    
    if 'error' in statements:
        return statements
    
    income = statements.get('income_statement', {})
    
    # Extract EPS data
    eps_basic = income.get('EarningsPerShareBasic', {})
    eps_diluted = income.get('EarningsPerShareDiluted', {})
    revenue = income.get('Revenues') or income.get('RevenueFromContractWithCustomerExcludingAssessedTax', {})
    net_income = income.get('NetIncomeLoss', {})
    
    result = {
        'symbol': symbol,
        'company_name': statements.get('company_name'),
        'latest_quarter': {
            'eps_basic': eps_basic.get('value') if eps_basic else None,
            'eps_diluted': eps_diluted.get('value') if eps_diluted else None,
            'revenue': revenue.get('value') if revenue else None,
            'net_income': net_income.get('value') if net_income else None,
            'end_date': eps_basic.get('end_date') if eps_basic else None,
            'fiscal_year': eps_basic.get('fy') if eps_basic else None,
            'fiscal_period': eps_basic.get('fp') if eps_basic else None,
        },
        'note': 'SEC data only includes actual results. Analyst estimates require paid API.'
    }
    
    return result

def get_key_ratios(symbol: str) -> Dict:
    """
    Calculate key financial ratios from SEC EDGAR data.
    
    Ratios calculated:
    - P/E Ratio (requires current price from market data)
    - ROE (Return on Equity)
    - ROA (Return on Assets)
    - Debt-to-Equity
    - Current Ratio
    - Gross Margin
    - Operating Margin
    - Net Margin
    
    Args:
        symbol: Stock ticker
    
    Returns:
        Dict with calculated financial ratios
    """
    statements = get_financial_statements(symbol, period='annual')
    
    if 'error' in statements:
        return statements
    
    income = statements.get('income_statement', {})
    balance = statements.get('balance_sheet', {})
    
    # Extract values
    net_income = income.get('NetIncomeLoss', {}).get('value')
    revenue = (income.get('Revenues') or income.get('RevenueFromContractWithCustomerExcludingAssessedTax', {})).get('value')
    gross_profit = income.get('GrossProfit', {}).get('value')
    operating_income = income.get('OperatingIncomeLoss', {}).get('value')
    
    assets = balance.get('Assets', {}).get('value')
    equity = balance.get('StockholdersEquity', {}).get('value')
    liabilities = balance.get('Liabilities', {}).get('value')
    current_assets = balance.get('AssetsCurrent', {}).get('value')
    current_liabilities = balance.get('LiabilitiesCurrent', {}).get('value')
    long_term_debt = balance.get('LongTermDebt', {}).get('value')
    
    # Calculate ratios
    ratios = {
        'symbol': symbol,
        'company_name': statements.get('company_name'),
        'ratios': {}
    }
    
    # ROE = Net Income / Equity
    if net_income and equity and equity != 0:
        ratios['ratios']['roe'] = round((net_income / equity) * 100, 2)
    
    # ROA = Net Income / Assets
    if net_income and assets and assets != 0:
        ratios['ratios']['roa'] = round((net_income / assets) * 100, 2)
    
    # Debt-to-Equity
    if long_term_debt and equity and equity != 0:
        ratios['ratios']['debt_to_equity'] = round(long_term_debt / equity, 2)
    
    # Current Ratio
    if current_assets and current_liabilities and current_liabilities != 0:
        ratios['ratios']['current_ratio'] = round(current_assets / current_liabilities, 2)
    
    # Margins
    if revenue and revenue != 0:
        if gross_profit:
            ratios['ratios']['gross_margin'] = round((gross_profit / revenue) * 100, 2)
        if operating_income:
            ratios['ratios']['operating_margin'] = round((operating_income / revenue) * 100, 2)
        if net_income:
            ratios['ratios']['net_margin'] = round((net_income / revenue) * 100, 2)
    
    ratios['note'] = 'P/E ratio requires current market price (not in SEC data)'
    ratios['data_date'] = statements.get('data_date')
    
    return ratios

def search_companies(query: str) -> List[Dict]:
    """
    Search for companies by name or ticker symbol.
    
    Args:
        query: Company name or ticker to search for
    
    Returns:
        List of matching companies with ticker, name, CIK
    """
    # Fetch ticker map
    ticker_map = _fetch_ticker_map()
    
    query_upper = query.upper()
    results = []
    
    for cik, data in ticker_map.get('data', {}).items():
        ticker = data.get('ticker', '')
        title = data.get('title', '')
        
        # Match on ticker or company name
        if query_upper in ticker.upper() or query_upper in title.upper():
            results.append({
                'ticker': ticker,
                'company_name': title,
                'cik': cik
            })
    
    # Limit to top 20 results
    return results[:20]

# === CLI Commands ===

def cli_statements(symbol: str, period: str = 'annual'):
    """Display financial statements for a company"""
    data = get_financial_statements(symbol, period)
    
    if 'error' in data:
        print(f"❌ Error: {data['error']}")
        return
    
    print(f"\n📊 Financial Statements: {data['company_name']} ({symbol})")
    print("=" * 70)
    print(f"Period: {period.upper()} | CIK: {data['cik']}")
    
    print("\n💰 INCOME STATEMENT")
    print("-" * 70)
    for item, values in data.get('income_statement', {}).items():
        if values.get('value'):
            val_formatted = f"${values['value']:,.0f}" if values['value'] > 0 else f"-${abs(values['value']):,.0f}"
            print(f"  {item:40s} {val_formatted:>20s}  ({values.get('end_date', 'N/A')})")
    
    print("\n📈 BALANCE SHEET")
    print("-" * 70)
    for item, values in data.get('balance_sheet', {}).items():
        if values.get('value'):
            val_formatted = f"${values['value']:,.0f}" if values['value'] > 0 else f"-${abs(values['value']):,.0f}"
            print(f"  {item:40s} {val_formatted:>20s}  ({values.get('end_date', 'N/A')})")
    
    print("\n💵 CASH FLOW")
    print("-" * 70)
    for item, values in data.get('cash_flow', {}).items():
        if values.get('value'):
            val_formatted = f"${values['value']:,.0f}" if values['value'] > 0 else f"-${abs(values['value']):,.0f}"
            print(f"  {item:40s} {val_formatted:>20s}  ({values.get('end_date', 'N/A')})")

def cli_ratios(symbol: str):
    """Display key financial ratios"""
    data = get_key_ratios(symbol)
    
    if 'error' in data:
        print(f"❌ Error: {data['error']}")
        return
    
    print(f"\n📊 Key Financial Ratios: {data['company_name']} ({symbol})")
    print("=" * 70)
    
    ratios = data.get('ratios', {})
    
    print("\n🔢 PROFITABILITY RATIOS")
    if 'roe' in ratios:
        print(f"  Return on Equity (ROE):        {ratios['roe']:>8.2f}%")
    if 'roa' in ratios:
        print(f"  Return on Assets (ROA):        {ratios['roa']:>8.2f}%")
    
    print("\n💹 MARGIN RATIOS")
    if 'gross_margin' in ratios:
        print(f"  Gross Margin:                  {ratios['gross_margin']:>8.2f}%")
    if 'operating_margin' in ratios:
        print(f"  Operating Margin:              {ratios['operating_margin']:>8.2f}%")
    if 'net_margin' in ratios:
        print(f"  Net Margin:                    {ratios['net_margin']:>8.2f}%")
    
    print("\n📊 FINANCIAL HEALTH")
    if 'debt_to_equity' in ratios:
        print(f"  Debt-to-Equity:                {ratios['debt_to_equity']:>8.2f}")
    if 'current_ratio' in ratios:
        print(f"  Current Ratio:                 {ratios['current_ratio']:>8.2f}")
    
    if data.get('note'):
        print(f"\nℹ️  Note: {data['note']}")

def cli_search(query: str):
    """Search for companies"""
    results = search_companies(query)
    
    print(f"\n🔍 Search Results for: '{query}'")
    print("=" * 70)
    
    if not results:
        print("  No companies found")
        return
    
    print(f"  Found {len(results)} companies:\n")
    for r in results:
        print(f"  {r['ticker']:6s} | {r['company_name']:50s} | CIK: {r['cik']}")

if __name__ == "__main__":
    # Demo
    import sys
    
    if len(sys.argv) > 1:
        symbol = sys.argv[1].upper()
        cli_statements(symbol)
        print("\n")
        cli_ratios(symbol)
    else:
        print("Usage: python3 finstatements_free_api.py <TICKER>")
        print("Example: python3 finstatements_free_api.py AAPL")
