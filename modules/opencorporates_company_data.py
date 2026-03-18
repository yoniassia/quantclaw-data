#!/usr/bin/env python3

"""
opencorporates_company_data module

PURPOSE: Provides public company registration data for alternative investment analysis.
CATEGORY: alt_data
Data Source: https://api.opencorporates.com/
Update Frequency: Real-time, as per API updates (data is sourced from public registries and updated dynamically).
Auth Info: Uses free tier; no API key required for basic endpoints. Be mindful of rate limits.

This module fetches data from OpenCorporates API, caches responses, and handles errors gracefully.
"""

import requests
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/opencorporates_company_data')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url: str, cache_key: str, params: Dict[str, Any] = None, headers: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Helper function to perform a cached GET request.
    
    Args:
        url (str): The API endpoint URL.
        cache_key (str): A unique key for caching the response.
        params (dict): Query parameters for the request.
        headers (dict): Headers for the request.
    
    Returns:
        dict: The JSON response data, or cached data if available and not expired.
    """
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return json.loads(cache_file.read_text())
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        cache_file.write_text(json.dumps(data, indent=2))
        return data
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def search_companies(query: str) -> Dict[str, Any]:
    """
    Search for companies using a query string.
    
    Args:
        query (str): The search query (e.g., company name).
    
    Returns:
        dict: A dictionary containing search results, or an error dictionary.
    """
    url = "https://api.opencorporates.com/v0.4/companies"
    cache_key = f"search_{query.replace(' ', '_')}"
    params = {'q': query}
    try:
        data = _cached_get(url, cache_key, params=params)
        return data  # Expected structure: {'results': {...}}
    except Exception as e:
        return {'error': f"Search failed: {str(e)}"}

def get_company(jurisdiction_code: str, company_number: str) -> Dict[str, Any]:
    """
    Get details of a specific company.
    
    Args:
        jurisdiction_code (str): The company's jurisdiction code (e.g., 'us_de').
        company_number (str): The company's registration number.
    
    Returns:
        dict: A dictionary with company details, or an error dictionary.
    """
    url = f"https://api.opencorporates.com/v0.4/companies/{jurisdiction_code}/{company_number}"
    cache_key = f"company_{jurisdiction_code}_{company_number}"
    try:
        data = _cached_get(url, cache_key)
        return data  # Expected structure: {'results': {'company': {...}}}
    except Exception as e:
        return {'error': f"Company fetch failed: {str(e)}"}

def get_officers(jurisdiction_code: str, company_number: str) -> List[Dict[str, Any]]:
    """
    Get officers associated with a company.
    
    Args:
        jurisdiction_code (str): The company's jurisdiction code.
        company_number (str): The company's registration number.
    
    Returns:
        list: A list of officer dictionaries, or an error dictionary if failed.
    """
    url = f"https://api.opencorporates.com/v0.4/companies/{jurisdiction_code}/{company_number}/officers"
    cache_key = f"officers_{jurisdiction_code}_{company_number}"
    try:
        data = _cached_get(url, cache_key)
        return data.get('results', {}).get('officers', [])  # Extract officers list
    except Exception as e:
        return [{'error': f"Officers fetch failed: {str(e)}"}]

def get_filings(jurisdiction_code: str, company_number: str) -> List[Dict[str, Any]]:
    """
    Get filings associated with a company.
    
    Args:
        jurisdiction_code (str): The company's jurisdiction code.
        company_number (str): The company's registration number.
    
    Returns:
        list: A list of filing dictionaries, or an error dictionary if failed.
    """
    url = f"https://api.opencorporates.com/v0.4/companies/{jurisdiction_code}/{company_number}/filings"
    cache_key = f"filings_{jurisdiction_code}_{company_number}"
    try:
        data = _cached_get(url, cache_key)
        return data.get('results', {}).get('filings', [])  # Extract filings list
    except Exception as e:
        return [{'error': f"Filings fetch failed: {str(e)}"}]

def get_related_companies(jurisdiction_code: str, company_number: str) -> List[Dict[str, Any]]:
    """
    Get companies related to a specific company.
    
    Args:
        jurisdiction_code (str): The company's jurisdiction code.
        company_number (str): The company's registration number.
    
    Returns:
        list: A list of related company dictionaries, or an error dictionary if failed.
    """
    url = f"https://api.opencorporates.com/v0.4/companies/{jurisdiction_code}/{company_number}/related"
    cache_key = f"related_{jurisdiction_code}_{company_number}"
    try:
        data = _cached_get(url, cache_key)
        return data.get('results', {}).get('companies', [])  # Extract related companies list
    except Exception as e:
        return [{'error': f"Related companies fetch failed: {str(e)}"}]

def main():
    """
    Demonstrate key functions of the module.
    """
    print("Demonstrating opencorporates_company_data module:")
    
    # Demo 1: Search for companies
    search_results = search_companies("Apple Inc")
    print("Search results:", search_results)
    
    # Demo 2: Get company details (using the first result if available)
    if 'results' in search_results and search_results['results'].get('companies'):
        first_company = search_results['results']['companies'][0]
        company_data = get_company(first_company['company']['jurisdiction_code'], first_company['company']['company_number'])
        print("Company details:", company_data)
    else:
        print("No company found for search demo.")
    
    # Demo 3: Get officers for the same company
    if 'results' in search_results and search_results['results'].get('companies'):
        first_company = search_results['results']['companies'][0]
        officers_data = get_officers(first_company['company']['jurisdiction_code'], first_company['company']['company_number'])
        print("Officers data:", officers_data)

if __name__ == '__main__':
    main()
