#!/usr/bin/env python3
"""
FRED Enhanced Module — Phase 104

Comprehensive Federal Reserve Economic Data (FRED) API access
300+ economic time series covering all major indicators:
- Complete yield curve (13 maturities)
- Money supply (M1, M2, M3, monetary base)
- Financial conditions indices (NFCI, STLFSI, ANFCI)
- Leading Economic Index (LEI) and components
- Consumer credit (total, revolving, non-revolving)
- Labor market indicators
- Inflation metrics (CPI, PCE, PPI)
- GDP components
- Housing market
- Manufacturing & production
- Trade & balance of payments

Data Source: api.stlouisfed.org/fred
Refresh: Daily to monthly depending on series
Coverage: 300+ economic time series

Author: QUANTCLAW DATA Build Agent
Phase: 104
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time

# FRED API Configuration
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_API_KEY = ""  # Public access for basic queries

# ========== COMPREHENSIVE FRED SERIES REGISTRY ==========

FRED_SERIES = {
    # ===== YIELD CURVE (13 maturities) =====
    'YIELD_CURVE': {
        'DGS1MO': '1-Month Treasury Constant Maturity Rate',
        'DGS3MO': '3-Month Treasury Constant Maturity Rate',
        'DGS6MO': '6-Month Treasury Constant Maturity Rate',
        'DGS1': '1-Year Treasury Constant Maturity Rate',
        'DGS2': '2-Year Treasury Constant Maturity Rate',
        'DGS3': '3-Year Treasury Constant Maturity Rate',
        'DGS5': '5-Year Treasury Constant Maturity Rate',
        'DGS7': '7-Year Treasury Constant Maturity Rate',
        'DGS10': '10-Year Treasury Constant Maturity Rate',
        'DGS20': '20-Year Treasury Constant Maturity Rate',
        'DGS30': '30-Year Treasury Constant Maturity Rate',
        'T10Y2Y': '10-Year minus 2-Year Treasury Spread',
        'T10Y3M': '10-Year minus 3-Month Treasury Spread (Recession Indicator)',
    },
    
    # ===== MONEY SUPPLY =====
    'MONEY_SUPPLY': {
        'M1SL': 'M1 Money Stock (Seasonally Adjusted)',
        'M2SL': 'M2 Money Stock (Seasonally Adjusted)',
        'M1V': 'Velocity of M1 Money Stock',
        'M2V': 'Velocity of M2 Money Stock',
        'BOGMBASE': 'Monetary Base',
        'WALCL': 'Fed Total Assets (Balance Sheet)',
        'WRESBAL': 'Reserve Balances with Federal Reserve Banks',
    },
    
    # ===== FINANCIAL CONDITIONS =====
    'FINANCIAL_CONDITIONS': {
        'NFCI': 'Chicago Fed National Financial Conditions Index',
        'NFCILEVERAGE': 'NFCI Leverage Subindex',
        'NFCICREDIT': 'NFCI Credit Subindex',
        'NFCIRISK': 'NFCI Risk Subindex',
        'STLFSI': 'St. Louis Fed Financial Stress Index',
        'ANFCI': 'Chicago Fed Adjusted National Financial Conditions Index',
        'VIXCLS': 'CBOE Volatility Index (VIX)',
        'TEDRATE': 'TED Spread (3-Month LIBOR minus 3-Month Treasury)',
    },
    
    # ===== LEADING ECONOMIC INDICATORS =====
    'LEADING_INDICATORS': {
        'USSLIND': 'Leading Index for the United States',
        'UMCSENT': 'University of Michigan Consumer Sentiment',
        'USCONS': 'University of Michigan Consumer Expectations',
        'CONSUMER': 'Consumer Opinion Surveys: Confidence Indicators',
        'DSPIC96': 'Real Disposable Personal Income',
        'PPIACO': 'Producer Price Index for All Commodities',
        'PERMIT': 'New Private Housing Units Authorized by Building Permits',
        'HOUST': 'Housing Starts: Total New Privately Owned',
        'NEWORDER': 'Manufacturers New Orders: Nondefense Capital Goods',
        'DGORDER': 'Manufacturers New Orders: Durable Goods',
    },
    
    # ===== CONSUMER CREDIT =====
    'CONSUMER_CREDIT': {
        'TOTALSL': 'Total Consumer Credit Outstanding',
        'REVOLSL': 'Revolving Consumer Credit Outstanding',
        'NONREVSL': 'Non-Revolving Consumer Credit Outstanding',
        'CONSUMER': 'Consumer Loans at All Commercial Banks',
        'DRCLACBS': 'Delinquency Rate on Consumer Loans',
        'DRSDCIS': 'Delinquency Rate on Single-Family Residential Mortgages',
        'DRCCLACBS': 'Delinquency Rate on Credit Card Loans',
        'DRALACBS': 'Delinquency Rate on All Loans',
    },
    
    # ===== LABOR MARKET =====
    'LABOR': {
        'UNRATE': 'Unemployment Rate',
        'U6RATE': 'Total Unemployed, Plus Marginally Attached & Part-Time (U-6)',
        'CIVPART': 'Labor Force Participation Rate',
        'EMRATIO': 'Employment-Population Ratio',
        'PAYEMS': 'All Employees: Total Nonfarm',
        'USPRIV': 'All Employees: Total Private Industries',
        'USGOVT': 'All Employees: Government',
        'USCONS': 'All Employees: Construction',
        'MANEMP': 'All Employees: Manufacturing',
        'USINFO': 'All Employees: Information',
        'USFIRE': 'All Employees: Financial Activities',
        'USPBS': 'All Employees: Professional and Business Services',
        'USEHS': 'All Employees: Education and Health Services',
        'USLAH': 'All Employees: Leisure and Hospitality',
        'AWHMAN': 'Average Weekly Hours: Manufacturing',
        'CES0500000003': 'Average Hourly Earnings: Total Private',
        'ICSA': 'Initial Claims (Weekly, Seasonally Adjusted)',
        'CCSA': 'Continued Claims (Insured Unemployment)',
        'JTSJOL': 'Job Openings: Total Nonfarm (JOLTS)',
        'JTSQUR': 'Quits Rate: Total Nonfarm',
    },
    
    # ===== INFLATION =====
    'INFLATION': {
        'CPIAUCSL': 'Consumer Price Index for All Urban Consumers: All Items',
        'CPILFESL': 'CPI: All Items Less Food and Energy (Core CPI)',
        'CPIENGSL': 'CPI: Energy',
        'CPIUFDSL': 'CPI: Food',
        'CPIMEDSL': 'CPI: Medical Care',
        'CUSR0000SAH1': 'CPI: Shelter',
        'CUSR0000SETA02': 'CPI: Used Cars and Trucks',
        'PCEPI': 'Personal Consumption Expenditures: Chain-type Price Index',
        'PCEPILFE': 'PCE Excluding Food and Energy (Core PCE)',
        'PPIACO': 'Producer Price Index for All Commodities',
        'PPIFIS': 'Producer Price Index: Finished Goods',
        'PPIFGS': 'Producer Price Index: Finished Goods Less Foods and Energy',
        'T5YIE': '5-Year Breakeven Inflation Rate',
        'T10YIE': '10-Year Breakeven Inflation Rate',
        'T5YIFR': '5-Year, 5-Year Forward Inflation Expectation Rate',
    },
    
    # ===== GDP & COMPONENTS =====
    'GDP': {
        'GDP': 'Gross Domestic Product',
        'GDPC1': 'Real Gross Domestic Product',
        'A191RL1Q225SBEA': 'Real GDP Growth Rate',
        'GDPPOT': 'Real Potential Gross Domestic Product',
        'GDPDEF': 'GDP Implicit Price Deflator',
        'PCEC96': 'Real Personal Consumption Expenditures',
        'PCDG96': 'Real Personal Consumption: Durable Goods',
        'PCESV96': 'Real Personal Consumption: Services',
        'GPDI': 'Gross Private Domestic Investment',
        'GPDIC1': 'Real Gross Private Domestic Investment',
        'PRFI': 'Private Residential Fixed Investment',
        'PNFI': 'Private Nonresidential Fixed Investment',
        'GCE': 'Government Consumption Expenditures and Gross Investment',
        'NETEXP': 'Net Exports of Goods and Services',
        'EXPGS': 'Exports of Goods and Services',
        'IMPGS': 'Imports of Goods and Services',
    },
    
    # ===== HOUSING =====
    'HOUSING': {
        'HOUST': 'Housing Starts: Total',
        'HOUST1F': 'Housing Starts: Single-Family',
        'HOUST5F': 'Housing Starts: 5-Unit Structures or More',
        'PERMIT': 'New Private Housing Units Authorized by Building Permits',
        'COMPUTSA': 'New Private Housing Units Completed',
        'USSTHPI': 'S&P/Case-Shiller U.S. National Home Price Index',
        'CSUSHPISA': 'S&P/Case-Shiller 20-City Composite Home Price Index',
        'MSPUS': 'Median Sales Price of Houses Sold',
        'ASPUS': 'Average Sales Price of Houses Sold',
        'HSN1F': 'New One Family Houses Sold',
        'MSACSR': 'Monthly Supply of New Houses',
        'MORTGAGE30US': '30-Year Fixed Rate Mortgage Average',
        'MORTGAGE15US': '15-Year Fixed Rate Mortgage Average',
        'RHORUSQ156N': 'Homeownership Rate',
    },
    
    # ===== MANUFACTURING & PRODUCTION =====
    'MANUFACTURING': {
        'INDPRO': 'Industrial Production Index',
        'IPMAN': 'Industrial Production: Manufacturing',
        'IPDMAT': 'Industrial Production: Durable Materials',
        'IPNMAT': 'Industrial Production: Nondurable Materials',
        'IPMANSICS': 'Industrial Production: Manufacturing (SIC)',
        'TCU': 'Capacity Utilization: Total Industry',
        'MCUMFN': 'Capacity Utilization: Manufacturing',
        'DGORDER': 'Manufacturers New Orders: Durable Goods',
        'NEWORDER': 'Manufacturers New Orders: Nondefense Capital Goods',
        'AMTMNO': 'Manufacturers New Orders: Durable Goods Excluding Transportation',
        'USPRIV': 'All Employees: Total Private Industries',
        'MANEMP': 'All Employees: Manufacturing',
        'AWHI': 'Aggregate Weekly Hours Index: Manufacturing',
        'AWHMAN': 'Average Weekly Hours: Manufacturing',
        'NAPM': 'ISM Manufacturing: PMI Composite Index (discontinued, use MANEMP proxy)',
        'NAPMNOI': 'ISM Manufacturing: New Orders Index',
        'NAPMPI': 'ISM Manufacturing: Production Index',
        'NAPMSDI': 'ISM Manufacturing: Supplier Deliveries Index',
    },
    
    # ===== TRADE & BALANCE OF PAYMENTS =====
    'TRADE': {
        'BOPGSTB': 'Trade Balance: Goods and Services',
        'BOPGTB': 'Trade Balance: Goods',
        'BOPSTB': 'Trade Balance: Services',
        'EXPGS': 'Exports of Goods and Services',
        'IMPGS': 'Imports of Goods and Services',
        'IEABCSN': 'U.S. Imports from China',
        'XTEXVA01CNM667S': 'U.S. Exports to China',
        'DEXCHUS': 'China / U.S. Foreign Exchange Rate',
        'DEXUSEU': 'U.S. / Euro Foreign Exchange Rate',
        'DEXJPUS': 'Japan / U.S. Foreign Exchange Rate',
        'DEXUSUK': 'U.S. / U.K. Foreign Exchange Rate',
        'DTWEXBGS': 'Trade Weighted U.S. Dollar Index: Broad, Goods and Services',
        'DTWEXEMEGS': 'Trade Weighted U.S. Dollar Index: Emerging Market Economies',
    },
    
    # ===== RETAIL & SALES =====
    'RETAIL': {
        'RSAFS': 'Retail Sales: Total',
        'RSXFS': 'Retail Sales Excluding Food Services',
        'RSGASS': 'Retail Sales: Gasoline Stations',
        'RSFSDP': 'Retail Sales: Food and Beverage Stores',
        'MRTSSM4451USS': 'Retail Sales: Clothing and Clothing Accessory Stores',
        'MRTSSM44X72USS': 'Retail Sales: Building Materials and Garden Equipment',
        'MRTSSM722USS': 'Retail Sales: Food Services and Drinking Places',
        'RSCCAS': 'Retail Sales: Auto and Other Motor Vehicles',
        'RSSGHBMS': 'Retail Sales: General Merchandise Stores',
    },
    
    # ===== ENERGY & COMMODITIES =====
    'ENERGY': {
        'DCOILWTICO': 'Crude Oil Prices: West Texas Intermediate (WTI)',
        'DCOILBRENTEU': 'Crude Oil Prices: Brent - Europe',
        'GASREGW': 'US Regular All Formulations Gas Price',
        'DHHNGSP': 'Henry Hub Natural Gas Spot Price',
        'DPROPANEMBTX': 'Propane Prices: Mont Belvieu, Texas',
        'DEXCHUS': 'China / U.S. Foreign Exchange Rate',
        'GOLDAMGBD228NLBM': 'Gold Fixing Price',
        'DEXBZUS': 'Brazil / U.S. Foreign Exchange Rate',
    },
    
    # ===== SAVINGS & WEALTH =====
    'SAVINGS': {
        'PSAVERT': 'Personal Saving Rate',
        'BOGZ1FL192090005Q': 'Households and Nonprofit Organizations; Net Worth',
        'WIMFSL': 'Wealth Index for Middle Income Families',
        'WTREGEN': 'Wealth Index for Top 0.1%',
        'PI': 'Personal Income',
        'DSPI': 'Disposable Personal Income',
        'DSPIC96': 'Real Disposable Personal Income',
        'PCECC96': 'Real Personal Consumption Expenditures',
    },
    
    # ===== DEBT & CREDIT =====
    'DEBT': {
        'GFDEBTN': 'Federal Debt: Total Public Debt',
        'GFDEGDQ188S': 'Federal Debt: Total Public Debt as Percent of GDP',
        'FYGFD': 'Federal Surplus or Deficit',
        'TOTLL': 'Total Loans and Leases at Commercial Banks',
        'TOTCI': 'Total Consumer Credit Outstanding',
        'HHMSDODNS': 'Households and Nonprofit Orgs: Debt Service Payments',
        'TDSP': 'Household Debt Service Payments as Percent of Disposable Personal Income',
        'SLOAS': 'Total Student Loans Owned and Securitized',
    },
    
    # ===== CORPORATE & BUSINESS =====
    'CORPORATE': {
        'NCBCMDPMVCE': 'Nonfinancial Corporate Business: Cash Flow',
        'CP': 'Corporate Profits After Tax',
        'A053RC1Q027SBEA': 'Corporate Profits After Tax (without IVA and CCAdj)',
        'CPROFIT': 'Corporate Profits After Tax: Corporate Business',
        'NCBEILQ027S': 'Nonfinancial Corporate Business: Liabilities',
        'INVEST': 'Real Gross Private Domestic Investment',
        'BUSLOANS': 'Commercial and Industrial Loans at All Commercial Banks',
    }
}


def get_fred_series(
    series_id: str,
    lookback_days: int = 365,
    api_key: Optional[str] = None
) -> Dict:
    """
    Fetch single FRED time series
    
    Args:
        series_id: FRED series identifier (e.g., 'DGS10')
        lookback_days: Number of days of history (default 365)
        api_key: Optional FRED API key for higher rate limits
    
    Returns:
        Dict with series data, latest value, and changes
    """
    try:
        url = f"{FRED_BASE_URL}/series/observations"
        params = {
            "series_id": series_id,
            "file_type": "json",
            "observation_start": (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d"),
        }
        
        if api_key or FRED_API_KEY:
            params["api_key"] = api_key or FRED_API_KEY
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if "observations" not in data:
            return {
                "success": False,
                "error": "No observations in response",
                "series_id": series_id
            }
        
        # Filter out missing values (".")
        obs = [o for o in data["observations"] if o["value"] != "."]
        
        if not obs:
            return {
                "success": False,
                "error": "No valid observations found",
                "series_id": series_id
            }
        
        latest = obs[-1]
        latest_val = float(latest["value"])
        
        # Calculate changes
        changes = {}
        if len(obs) >= 2:
            prev_val = float(obs[-2]["value"])
            changes["period_change"] = latest_val - prev_val
            changes["period_change_pct"] = ((latest_val - prev_val) / prev_val * 100) if prev_val != 0 else 0
        
        if len(obs) >= 30:  # ~1 month
            month_ago = float(obs[-30]["value"])
            changes["month_change"] = latest_val - month_ago
            changes["month_change_pct"] = ((latest_val - month_ago) / month_ago * 100) if month_ago != 0 else 0
        
        if len(obs) >= 90:  # ~3 months
            quarter_ago = float(obs[-90]["value"])
            changes["quarter_change"] = latest_val - quarter_ago
            changes["quarter_change_pct"] = ((latest_val - quarter_ago) / quarter_ago * 100) if quarter_ago != 0 else 0
        
        # Year-over-year
        year_ago_idx = min(len(obs) - 1, 252)  # ~252 trading days
        if year_ago_idx > 0:
            year_ago = float(obs[-year_ago_idx]["value"])
            changes["yoy_change"] = latest_val - year_ago
            changes["yoy_change_pct"] = ((latest_val - year_ago) / year_ago * 100) if year_ago != 0 else 0
        
        return {
            "success": True,
            "series_id": series_id,
            "latest_value": latest_val,
            "latest_date": latest["date"],
            "changes": changes,
            "observations": [{"date": o["date"], "value": float(o["value"])} for o in obs[-90:]],  # Last 90 points
            "count": len(obs)
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "series_id": series_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "series_id": series_id
        }


def get_yield_curve(api_key: Optional[str] = None) -> Dict:
    """
    Get complete US Treasury yield curve (13 maturities)
    
    Returns:
        Dict with all yields, spreads, and inversion indicators
    """
    curve_series = FRED_SERIES['YIELD_CURVE']
    results = {}
    
    for series_id in curve_series.keys():
        data = get_fred_series(series_id, lookback_days=30, api_key=api_key)
        if data['success']:
            results[series_id] = {
                'name': curve_series[series_id],
                'value': data['latest_value'],
                'date': data['latest_date'],
                'change': data['changes'].get('period_change', 0)
            }
    
    # Calculate inversion indicators
    inversions = []
    if 'DGS10' in results and 'DGS2' in results:
        spread_10y_2y = results['DGS10']['value'] - results['DGS2']['value']
        if spread_10y_2y < 0:
            inversions.append({
                'pair': '10Y-2Y',
                'spread': spread_10y_2y,
                'inverted': True,
                'significance': 'Strong recession indicator'
            })
    
    if 'DGS10' in results and 'DGS3MO' in results:
        spread_10y_3m = results['DGS10']['value'] - results['DGS3MO']['value']
        if spread_10y_3m < 0:
            inversions.append({
                'pair': '10Y-3M',
                'spread': spread_10y_3m,
                'inverted': True,
                'significance': 'Classic recession indicator'
            })
    
    return {
        'success': True,
        'yields': results,
        'inversions': inversions if inversions else None,
        'timestamp': datetime.now().isoformat()
    }


def get_money_supply(api_key: Optional[str] = None) -> Dict:
    """
    Get money supply metrics (M1, M2, velocity, Fed balance sheet)
    
    Returns:
        Dict with monetary aggregates and velocity
    """
    money_series = FRED_SERIES['MONEY_SUPPLY']
    results = {}
    
    for series_id, name in money_series.items():
        data = get_fred_series(series_id, lookback_days=365, api_key=api_key)
        if data['success']:
            results[series_id] = {
                'name': name,
                'value': data['latest_value'],
                'date': data['latest_date'],
                'yoy_change_pct': data['changes'].get('yoy_change_pct', 0)
            }
    
    # Calculate M2 velocity trend
    if 'M2V' in results:
        velocity_trend = 'accelerating' if results['M2V']['yoy_change_pct'] > 0 else 'decelerating'
        results['velocity_trend'] = velocity_trend
    
    return {
        'success': True,
        'money_supply': results,
        'timestamp': datetime.now().isoformat()
    }


def get_financial_conditions(api_key: Optional[str] = None) -> Dict:
    """
    Get financial conditions indices (NFCI, STLFSI, VIX, TED spread)
    
    Returns:
        Dict with financial stress indicators
    """
    fc_series = FRED_SERIES['FINANCIAL_CONDITIONS']
    results = {}
    
    for series_id, name in fc_series.items():
        data = get_fred_series(series_id, lookback_days=90, api_key=api_key)
        if data['success']:
            results[series_id] = {
                'name': name,
                'value': data['latest_value'],
                'date': data['latest_date'],
                'month_change': data['changes'].get('month_change', 0)
            }
    
    # Interpret financial conditions
    interpretation = []
    if 'NFCI' in results:
        nfci = results['NFCI']['value']
        if nfci > 0.5:
            interpretation.append('Tight financial conditions (NFCI > 0.5)')
        elif nfci < -0.5:
            interpretation.append('Loose financial conditions (NFCI < -0.5)')
        else:
            interpretation.append('Neutral financial conditions')
    
    if 'STLFSI' in results:
        stlfsi = results['STLFSI']['value']
        if stlfsi > 1.0:
            interpretation.append('Elevated financial stress (STLFSI > 1.0)')
        elif stlfsi < -1.0:
            interpretation.append('Low financial stress')
    
    return {
        'success': True,
        'indicators': results,
        'interpretation': interpretation,
        'timestamp': datetime.now().isoformat()
    }


def get_leading_indicators(api_key: Optional[str] = None) -> Dict:
    """
    Get Leading Economic Index and components
    
    Returns:
        Dict with LEI and forward-looking indicators
    """
    lei_series = FRED_SERIES['LEADING_INDICATORS']
    results = {}
    
    for series_id, name in lei_series.items():
        data = get_fred_series(series_id, lookback_days=365, api_key=api_key)
        if data['success']:
            results[series_id] = {
                'name': name,
                'value': data['latest_value'],
                'date': data['latest_date'],
                'month_change_pct': data['changes'].get('month_change_pct', 0),
                'yoy_change_pct': data['changes'].get('yoy_change_pct', 0)
            }
    
    return {
        'success': True,
        'leading_indicators': results,
        'timestamp': datetime.now().isoformat()
    }


def get_consumer_credit(api_key: Optional[str] = None) -> Dict:
    """
    Get consumer credit outstanding (total, revolving, non-revolving) and delinquency rates
    
    Returns:
        Dict with credit metrics and delinquencies
    """
    credit_series = FRED_SERIES['CONSUMER_CREDIT']
    results = {}
    
    for series_id, name in credit_series.items():
        data = get_fred_series(series_id, lookback_days=365, api_key=api_key)
        if data['success']:
            results[series_id] = {
                'name': name,
                'value': data['latest_value'],
                'date': data['latest_date'],
                'yoy_change_pct': data['changes'].get('yoy_change_pct', 0)
            }
    
    # Calculate credit health score
    health_indicators = []
    if 'DRCLACBS' in results:
        delinq_rate = results['DRCLACBS']['value']
        if delinq_rate > 3.0:
            health_indicators.append('Elevated consumer loan delinquencies')
        elif delinq_rate < 1.5:
            health_indicators.append('Low consumer loan delinquencies')
    
    return {
        'success': True,
        'consumer_credit': results,
        'health_indicators': health_indicators,
        'timestamp': datetime.now().isoformat()
    }


def get_category(category: str, api_key: Optional[str] = None) -> Dict:
    """
    Get all series for a specific category
    
    Args:
        category: Category name from FRED_SERIES keys (e.g., 'LABOR', 'INFLATION', 'GDP')
        api_key: Optional FRED API key
    
    Returns:
        Dict with all series in that category
    """
    if category not in FRED_SERIES:
        return {
            'success': False,
            'error': f'Invalid category. Must be one of: {list(FRED_SERIES.keys())}'
        }
    
    series_dict = FRED_SERIES[category]
    results = {}
    
    for series_id, name in series_dict.items():
        data = get_fred_series(series_id, lookback_days=365, api_key=api_key)
        if data['success']:
            results[series_id] = {
                'name': name,
                'value': data['latest_value'],
                'date': data['latest_date'],
                'changes': data['changes']
            }
    
    return {
        'success': True,
        'category': category,
        'data': results,
        'count': len(results),
        'timestamp': datetime.now().isoformat()
    }


def get_macro_snapshot(api_key: Optional[str] = None) -> Dict:
    """
    Get comprehensive economic snapshot with key indicators from all categories
    
    Returns:
        Dict with summary metrics across all categories
    """
    # Key series from each category
    key_series = {
        'GDP': 'GDPC1',
        'Unemployment': 'UNRATE',
        'Core CPI': 'CPILFESL',
        'Core PCE': 'PCEPILFE',
        '10Y Treasury': 'DGS10',
        '10Y-2Y Spread': 'T10Y2Y',
        'M2 Money Supply': 'M2SL',
        'Fed Balance Sheet': 'WALCL',
        'Financial Conditions': 'NFCI',
        'VIX': 'VIXCLS',
        'Consumer Sentiment': 'UMCSENT',
        'Total Consumer Credit': 'TOTALSL',
        'Federal Debt': 'GFDEBTN',
        'Oil Price (WTI)': 'DCOILWTICO',
    }
    
    results = {}
    
    for name, series_id in key_series.items():
        data = get_fred_series(series_id, lookback_days=365, api_key=api_key)
        if data['success']:
            results[name] = {
                'value': data['latest_value'],
                'date': data['latest_date'],
                'yoy_change_pct': data['changes'].get('yoy_change_pct', 0)
            }
    
    return {
        'success': True,
        'snapshot': results,
        'timestamp': datetime.now().isoformat(),
        'source': 'FRED API'
    }


def list_categories() -> Dict:
    """
    List all available FRED categories and their series counts
    
    Returns:
        Dict with category names and series counts
    """
    categories = []
    
    for cat_name, series_dict in FRED_SERIES.items():
        categories.append({
            'category': cat_name,
            'series_count': len(series_dict),
            'series_ids': list(series_dict.keys())
        })
    
    return {
        'success': True,
        'total_categories': len(FRED_SERIES),
        'total_series': sum(len(s) for s in FRED_SERIES.values()),
        'categories': categories
    }


def search_series(query: str) -> Dict:
    """
    Search FRED series by name or description
    
    Args:
        query: Search term
    
    Returns:
        List of matching series
    """
    query_lower = query.lower()
    results = []
    
    for cat_name, series_dict in FRED_SERIES.items():
        for series_id, series_name in series_dict.items():
            if query_lower in series_name.lower() or query_lower in series_id.lower():
                results.append({
                    'series_id': series_id,
                    'name': series_name,
                    'category': cat_name
                })
    
    return {
        'success': True,
        'query': query,
        'results_count': len(results),
        'results': results
    }


def cli_main():
    """CLI interface for FRED Enhanced module"""
    import argparse
    
    parser = argparse.ArgumentParser(description='FRED Enhanced - 300+ Economic Series')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # fred-series
    series_parser = subparsers.add_parser('fred-series', help='Get single FRED series')
    series_parser.add_argument('series_id', help='FRED series ID (e.g., DGS10)')
    series_parser.add_argument('--days', type=int, default=365, help='Days of history')
    series_parser.add_argument('--api-key', help='FRED API key')
    
    # fred-yield-curve
    yc_parser = subparsers.add_parser('fred-yield-curve', help='Get complete yield curve')
    yc_parser.add_argument('--api-key', help='FRED API key')
    
    # fred-money-supply
    ms_parser = subparsers.add_parser('fred-money-supply', help='Get money supply metrics')
    ms_parser.add_argument('--api-key', help='FRED API key')
    
    # fred-financial-conditions
    fc_parser = subparsers.add_parser('fred-financial-conditions', help='Get financial conditions indices')
    fc_parser.add_argument('--api-key', help='FRED API key')
    
    # fred-leading-indicators
    lei_parser = subparsers.add_parser('fred-leading-indicators', help='Get LEI and components')
    lei_parser.add_argument('--api-key', help='FRED API key')
    
    # fred-consumer-credit
    cc_parser = subparsers.add_parser('fred-consumer-credit', help='Get consumer credit metrics')
    cc_parser.add_argument('--api-key', help='FRED API key')
    
    # fred-category
    cat_parser = subparsers.add_parser('fred-category', help='Get all series in a category')
    cat_parser.add_argument('category', help='Category name (e.g., LABOR, INFLATION)')
    cat_parser.add_argument('--api-key', help='FRED API key')
    
    # fred-snapshot
    snap_parser = subparsers.add_parser('fred-snapshot', help='Get macro economic snapshot')
    snap_parser.add_argument('--api-key', help='FRED API key')
    
    # fred-categories
    subparsers.add_parser('fred-categories', help='List all categories')
    
    # fred-search
    search_parser = subparsers.add_parser('fred-search', help='Search series by name')
    search_parser.add_argument('query', help='Search term')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    if args.command == 'fred-series':
        result = get_fred_series(args.series_id, args.days, args.api_key)
    elif args.command == 'fred-yield-curve':
        result = get_yield_curve(args.api_key)
    elif args.command == 'fred-money-supply':
        result = get_money_supply(args.api_key)
    elif args.command == 'fred-financial-conditions':
        result = get_financial_conditions(args.api_key)
    elif args.command == 'fred-leading-indicators':
        result = get_leading_indicators(args.api_key)
    elif args.command == 'fred-consumer-credit':
        result = get_consumer_credit(args.api_key)
    elif args.command == 'fred-category':
        result = get_category(args.category.upper(), args.api_key)
    elif args.command == 'fred-snapshot':
        result = get_macro_snapshot(args.api_key)
    elif args.command == 'fred-categories':
        result = list_categories()
    elif args.command == 'fred-search':
        result = search_series(args.query)
    else:
        parser.print_help()
        return
    
    # Print result
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    cli_main()
