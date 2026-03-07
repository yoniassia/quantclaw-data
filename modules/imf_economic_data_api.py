#!/usr/bin/env python3
"""
IMF Economic Data API — International Macroeconomic Statistics

Comprehensive module for global macroeconomic data from the International Monetary Fund.
Access cross-country comparisons of GDP, inflation, fiscal indicators, and balance of payments
from central banks worldwide.

Databases:
- IFS (International Financial Statistics): GDP, CPI, exchange rates, reserves
- WEO (World Economic Outlook): Projections and historical macroeconomic indicators
- BOP (Balance of Payments): Current account, capital flows, trade balances

Source: https://data.imf.org/api
Category: Macro / Central Banks
Free tier: True (no API key required, 1000 queries/month)
Update frequency: Quarterly
Author: QuantClaw Data NightBuilder
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Union

# IMF SDMX JSON API Configuration
IMF_BASE_URL = "https://dataservices.imf.org/REST/SDMX_JSON.svc"

# ========== INDICATOR REGISTRY ==========

IFS_INDICATORS = {
    # GDP Indicators
    'NGDP_XDC': 'GDP, Current Prices, National Currency',
    'NGDP_USD': 'GDP, Current Prices, US Dollars',
    'NGDP_R_XDC': 'GDP, Real, National Currency',
    'NGDPD': 'GDP, Deflator',
    
    # Inflation Indicators
    'PCPI_IX': 'Consumer Price Index, All Items',
    'PCPI_PC_CP_A_PT': 'CPI, % Change',
    'PCPIPCH': 'CPI, % Change, Year-over-Year',
    'PCPIEPCH': 'CPI, End of Period, % Change',
    
    # Exchange Rates
    'ENDA_XDC_USD_RATE': 'Exchange Rate, End of Period, National Currency per US Dollar',
    'ENDA_USD_XDC_RATE': 'Exchange Rate, End of Period, US Dollar per National Currency',
    'EREA_XDC_USD_RATE': 'Exchange Rate, Period Average, National Currency per US Dollar',
    
    # Balance of Payments
    'BCA_BP6_USD': 'Current Account Balance, US Dollars',
    'BKA_BP6_USD': 'Capital Account Balance, US Dollars',
    'BFOA_BP6_USD': 'Financial Account Balance, US Dollars',
    
    # Fiscal Indicators
    'GGR_G01_GDP_PT': 'General Government Revenue, % of GDP',
    'GGX_G01_GDP_PT': 'General Government Expenditure, % of GDP',
    'GGXCNL_G01_GDP_PT': 'General Government Net Lending/Borrowing, % of GDP',
    'GGXWDG_G01_GDP_PT': 'General Government Gross Debt, % of GDP',
}

WEO_INDICATORS = {
    'NGDP': 'Gross Domestic Product, Current Prices',
    'NGDPD': 'GDP Deflator',
    'NGDP_RPCH': 'GDP, Real Growth Rate',
    'PCPIPCH': 'Inflation, CPI',
    'LUR': 'Unemployment Rate',
    'GGR': 'Government Revenue',
    'GGX': 'Government Expenditure',
    'GGXCNL': 'Government Net Lending/Borrowing',
    'GGXWDG': 'Government Gross Debt',
    'BCA': 'Current Account Balance',
}

# ISO 3166-1 Alpha-2 Country Codes (Common)
COMMON_COUNTRIES = {
    'US': 'United States', 'GB': 'United Kingdom', 'CN': 'China',
    'JP': 'Japan', 'DE': 'Germany', 'FR': 'France', 'IT': 'Italy',
    'CA': 'Canada', 'AU': 'Australia', 'IN': 'India', 'BR': 'Brazil',
    'MX': 'Mexico', 'KR': 'South Korea', 'ES': 'Spain', 'NL': 'Netherlands',
}


def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Make request to IMF API with error handling.
    
    Args:
        endpoint: API endpoint path
        params: Optional query parameters
        
    Returns:
        dict: JSON response data
    """
    url = f"{IMF_BASE_URL}/{endpoint}"
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            'error': str(e),
            'endpoint': endpoint,
            'status': 'failed'
        }
    except json.JSONDecodeError as e:
        return {
            'error': f'JSON decode error: {str(e)}',
            'endpoint': endpoint,
            'status': 'failed'
        }


def _parse_compact_data(data: Dict, indicator_code: str) -> List[Dict]:
    """
    Parse IMF CompactData response format.
    
    Args:
        data: Raw API response
        indicator_code: Indicator code for reference
        
    Returns:
        list: Parsed time series data
    """
    try:
        if 'error' in data:
            return []
        
        series_list = []
        compact_data = data.get('CompactData', {})
        dataset = compact_data.get('DataSet', {})
        series = dataset.get('Series', [])
        
        # Handle single series vs multiple series
        if isinstance(series, dict):
            series = [series]
        
        for s in series:
            obs_list = s.get('Obs', [])
            if isinstance(obs_list, dict):
                obs_list = [obs_list]
            
            for obs in obs_list:
                series_list.append({
                    'indicator': indicator_code,
                    'period': obs.get('@TIME_PERIOD', ''),
                    'value': obs.get('@OBS_VALUE', ''),
                    'status': obs.get('@OBS_STATUS', ''),
                })
        
        return series_list
    except Exception as e:
        return []


def get_gdp_data(country: str = "US", start_year: int = 2020) -> Dict:
    """
    Get GDP data from IFS database.
    
    Args:
        country: ISO 3166-1 Alpha-2 country code (default: "US")
        start_year: Start year for data (default: 2020)
        
    Returns:
        dict: GDP data with nominal, real, and deflator series
    """
    try:
        # Fetch nominal GDP (current prices, USD)
        endpoint = f"CompactData/IFS/A.{country}.NGDP_XDC"
        response = _make_request(endpoint)
        nominal_data = _parse_compact_data(response, 'NGDP_XDC')
        
        # Fetch real GDP
        endpoint = f"CompactData/IFS/A.{country}.NGDP_R_XDC"
        response = _make_request(endpoint)
        real_data = _parse_compact_data(response, 'NGDP_R_XDC')
        
        # Filter by start_year
        nominal_filtered = [d for d in nominal_data if int(d['period']) >= start_year]
        real_filtered = [d for d in real_data if int(d['period']) >= start_year]
        
        return {
            'country': country,
            'indicator': 'GDP',
            'start_year': start_year,
            'nominal_gdp': nominal_filtered,
            'real_gdp': real_filtered,
            'data_points': len(nominal_filtered),
            'status': 'success'
        }
    except Exception as e:
        return {
            'country': country,
            'error': str(e),
            'status': 'failed'
        }


def get_inflation_data(country: str = "US", start_year: int = 2020) -> Dict:
    """
    Get CPI inflation data from IFS database.
    
    Args:
        country: ISO 3166-1 Alpha-2 country code (default: "US")
        start_year: Start year for data (default: 2020)
        
    Returns:
        dict: CPI index and year-over-year inflation rates
    """
    try:
        # Fetch CPI Index
        endpoint = f"CompactData/IFS/A.{country}.PCPI_IX"
        response = _make_request(endpoint)
        cpi_data = _parse_compact_data(response, 'PCPI_IX')
        
        # Fetch CPI % change YoY
        endpoint = f"CompactData/IFS/A.{country}.PCPIPCH"
        response = _make_request(endpoint)
        inflation_data = _parse_compact_data(response, 'PCPIPCH')
        
        # Filter by start_year
        cpi_filtered = [d for d in cpi_data if int(d['period']) >= start_year]
        inflation_filtered = [d for d in inflation_data if int(d['period']) >= start_year]
        
        return {
            'country': country,
            'indicator': 'Inflation (CPI)',
            'start_year': start_year,
            'cpi_index': cpi_filtered,
            'inflation_rate': inflation_filtered,
            'data_points': len(inflation_filtered),
            'status': 'success'
        }
    except Exception as e:
        return {
            'country': country,
            'error': str(e),
            'status': 'failed'
        }


def get_balance_of_payments(country: str = "US", start_year: int = 2020) -> Dict:
    """
    Get Balance of Payments data from BOP database.
    
    Args:
        country: ISO 3166-1 Alpha-2 country code (default: "US")
        start_year: Start year for data (default: 2020)
        
    Returns:
        dict: Current account, capital account, and financial account balances
    """
    try:
        # Fetch Current Account Balance
        endpoint = f"CompactData/BOP/A.{country}.BCA_BP6_USD"
        response = _make_request(endpoint)
        current_account = _parse_compact_data(response, 'BCA_BP6_USD')
        
        # Fetch Capital Account Balance
        endpoint = f"CompactData/BOP/A.{country}.BKA_BP6_USD"
        response = _make_request(endpoint)
        capital_account = _parse_compact_data(response, 'BKA_BP6_USD')
        
        # Filter by start_year
        current_filtered = [d for d in current_account if int(d['period']) >= start_year]
        capital_filtered = [d for d in capital_account if int(d['period']) >= start_year]
        
        return {
            'country': country,
            'indicator': 'Balance of Payments',
            'start_year': start_year,
            'current_account': current_filtered,
            'capital_account': capital_filtered,
            'data_points': len(current_filtered),
            'status': 'success'
        }
    except Exception as e:
        return {
            'country': country,
            'error': str(e),
            'status': 'failed'
        }


def get_exchange_rates(country: str = "US", start_year: int = 2020) -> Dict:
    """
    Get exchange rate data from IFS database.
    
    Args:
        country: ISO 3166-1 Alpha-2 country code (default: "US")
        start_year: Start year for data (default: 2020)
        
    Returns:
        dict: Exchange rates (national currency per USD)
    """
    try:
        # Fetch End of Period Exchange Rate
        endpoint = f"CompactData/IFS/A.{country}.ENDA_XDC_USD_RATE"
        response = _make_request(endpoint)
        eop_rate = _parse_compact_data(response, 'ENDA_XDC_USD_RATE')
        
        # Fetch Period Average Exchange Rate
        endpoint = f"CompactData/IFS/A.{country}.EREA_XDC_USD_RATE"
        response = _make_request(endpoint)
        avg_rate = _parse_compact_data(response, 'EREA_XDC_USD_RATE')
        
        # Filter by start_year
        eop_filtered = [d for d in eop_rate if int(d['period']) >= start_year]
        avg_filtered = [d for d in avg_rate if int(d['period']) >= start_year]
        
        return {
            'country': country,
            'indicator': 'Exchange Rates',
            'start_year': start_year,
            'end_of_period': eop_filtered,
            'period_average': avg_filtered,
            'data_points': len(eop_filtered),
            'status': 'success'
        }
    except Exception as e:
        return {
            'country': country,
            'error': str(e),
            'status': 'failed'
        }


def get_fiscal_indicators(country: str = "US", start_year: int = 2020) -> Dict:
    """
    Get fiscal indicators (government debt, deficit) from IFS database.
    
    Args:
        country: ISO 3166-1 Alpha-2 country code (default: "US")
        start_year: Start year for data (default: 2020)
        
    Returns:
        dict: Government revenue, expenditure, debt, and deficit as % of GDP
    """
    try:
        # Fetch Government Gross Debt (% of GDP)
        endpoint = f"CompactData/IFS/A.{country}.GGXWDG_G01_GDP_PT"
        response = _make_request(endpoint)
        debt_data = _parse_compact_data(response, 'GGXWDG_G01_GDP_PT')
        
        # Fetch Government Net Lending/Borrowing (% of GDP)
        endpoint = f"CompactData/IFS/A.{country}.GGXCNL_G01_GDP_PT"
        response = _make_request(endpoint)
        deficit_data = _parse_compact_data(response, 'GGXCNL_G01_GDP_PT')
        
        # Filter by start_year
        debt_filtered = [d for d in debt_data if int(d['period']) >= start_year]
        deficit_filtered = [d for d in deficit_data if int(d['period']) >= start_year]
        
        return {
            'country': country,
            'indicator': 'Fiscal Indicators',
            'start_year': start_year,
            'gross_debt_pct_gdp': debt_filtered,
            'net_lending_borrowing_pct_gdp': deficit_filtered,
            'data_points': len(debt_filtered),
            'status': 'success'
        }
    except Exception as e:
        return {
            'country': country,
            'error': str(e),
            'status': 'failed'
        }


def get_world_economic_outlook(country: str = "US", indicator: str = "NGDP") -> Dict:
    """
    Get World Economic Outlook projections and historical data.
    
    Args:
        country: ISO 3166-1 Alpha-2 country code (default: "US")
        indicator: WEO indicator code (default: "NGDP" for nominal GDP)
        
    Returns:
        dict: WEO projections with historical and forecast data
    """
    try:
        # Note: WEO API structure may vary; using generic CompactData approach
        # WEO typically uses format: CompactData/WEO/{period}/{country}.{indicator}
        endpoint = f"CompactData/WEO/2024/01/{country}.{indicator}"
        response = _make_request(endpoint)
        
        # If specific WEO endpoint fails, try IFS fallback
        if 'error' in response or not response:
            endpoint = f"CompactData/IFS/A.{country}.{indicator}"
            response = _make_request(endpoint)
        
        data = _parse_compact_data(response, indicator)
        
        return {
            'country': country,
            'indicator': indicator,
            'indicator_name': WEO_INDICATORS.get(indicator, 'Unknown'),
            'data': data,
            'data_points': len(data),
            'status': 'success'
        }
    except Exception as e:
        return {
            'country': country,
            'indicator': indicator,
            'error': str(e),
            'status': 'failed'
        }


def search_indicators(query: str = "gdp") -> Dict:
    """
    Search available IMF indicators by keyword.
    
    Args:
        query: Search keyword (default: "gdp")
        
    Returns:
        dict: Matching indicators from IFS and WEO registries
    """
    try:
        query_lower = query.lower()
        
        # Search IFS indicators
        ifs_matches = {
            code: desc for code, desc in IFS_INDICATORS.items()
            if query_lower in desc.lower() or query_lower in code.lower()
        }
        
        # Search WEO indicators
        weo_matches = {
            code: desc for code, desc in WEO_INDICATORS.items()
            if query_lower in desc.lower() or query_lower in code.lower()
        }
        
        return {
            'query': query,
            'ifs_indicators': ifs_matches,
            'weo_indicators': weo_matches,
            'total_matches': len(ifs_matches) + len(weo_matches),
            'status': 'success'
        }
    except Exception as e:
        return {
            'query': query,
            'error': str(e),
            'status': 'failed'
        }


if __name__ == "__main__":
    # Test module
    print("IMF Economic Data API Module")
    print("=" * 50)
    
    # Test search
    print("\n1. Testing search_indicators('gdp')...")
    result = search_indicators("gdp")
    print(json.dumps(result, indent=2))
    
    # Test GDP data
    print("\n2. Testing get_gdp_data('US')...")
    result = get_gdp_data("US", start_year=2020)
    print(json.dumps(result, indent=2))
