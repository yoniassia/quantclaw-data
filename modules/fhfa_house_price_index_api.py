#!/usr/bin/env python3
"""
FHFA House Price Index API

Federal Housing Finance Agency House Price Index data module.
Provides national, state, and metro-level house price indices.

The FHFA HPI tracks changes in single-family home prices based on repeat sales
and refinancings on the same properties. Data is updated quarterly.

Source: https://www.fhfa.gov/DataTools/Downloads/Pages/House-Price-Index.aspx
Category: Real Estate & Housing
Free tier: True (public downloads, no API key required)
Update frequency: Quarterly
Author: QuantClaw Data NightBuilder
"""

import os
import requests
import pandas as pd
from io import StringIO, BytesIO
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# FHFA Public Data URLs (direct links to Excel files)
# These are the actual download URLs from FHFA website
FHFA_BASE_URL = "https://www.fhfa.gov"
FHFA_DOWNLOADS = {
    'national': '/DataTools/Downloads/Documents/HPI/HPI_master.xlsx',
    'state': '/DataTools/Downloads/Documents/HPI/HPI_AT_state.xlsx', 
    'metro': '/DataTools/Downloads/Documents/HPI/HPI_AT_metro.xlsx',
}

# Alternative: Use FRED for FHFA HPI data (more reliable)
FRED_FHFA_SERIES = {
    'national_sa': 'CSUSHPISA',  # S&P/Case-Shiller U.S. National Home Price Index (SA)
    'national_nsa': 'CSUSHPINSA',  # S&P/Case-Shiller U.S. National Home Price Index (NSA)
}

# Cache directory
CACHE_DIR = Path(__file__).parent.parent / ".cache" / "fhfa"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_national_hpi(start_year: int = 2020) -> Dict:
    """
    Get national house price index data
    
    Uses synthetic data for demonstration since FHFA direct downloads
    require dynamic URLs. In production, integrate with FRED API
    (CSUSHPISA series) or FHFA's emerging API.
    
    Args:
        start_year: Starting year for data (default 2020)
    
    Returns:
        Dict with national HPI values
    """
    try:
        # Generate synthetic quarterly data for demo
        current_year = datetime.now().year
        current_quarter = (datetime.now().month - 1) // 3 + 1
        
        data = []
        base_index = 100.0
        
        for year in range(start_year, current_year + 1):
            max_quarter = 4 if year < current_year else current_quarter
            for quarter in range(1, max_quarter + 1):
                # Synthetic growth pattern (real data would come from FHFA/FRED)
                years_elapsed = year - start_year + (quarter - 1) / 4
                annual_growth = 0.06  # 6% average annual growth
                index_value = base_index * ((1 + annual_growth) ** years_elapsed)
                
                # Add quarterly variation
                import math
                seasonal_factor = 1 + 0.02 * math.sin(quarter * math.pi / 2)
                index_value *= seasonal_factor
                
                # Calculate annual change
                if years_elapsed >= 1:
                    prev_index = base_index * ((1 + annual_growth) ** (years_elapsed - 1))
                    annual_change = ((index_value - prev_index) / prev_index) * 100
                else:
                    annual_change = 0.0
                
                data.append({
                    'year': year,
                    'quarter': quarter,
                    'date': f'{year}Q{quarter}',
                    'index_sa': round(index_value, 2),
                    'annual_change': round(annual_change, 2)
                })
        
        return {
            'success': True,
            'data': data,
            'latest': data[-1] if data else {},
            'count': len(data),
            'source': 'FHFA National HPI (Synthetic Demo Data)',
            'note': 'Using synthetic data. Integrate with FRED API (CSUSHPISA) or FHFA API for real data.'
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': []
        }


def get_state_hpi(state: str = 'CA', start_year: int = 2020) -> Dict:
    """
    Get state-level house price index data
    
    Args:
        state: Two-letter state code (e.g., 'CA', 'TX', 'NY')
        start_year: Starting year for data (default 2020)
    
    Returns:
        Dict with state HPI values
    """
    try:
        state = state.upper().strip()
        
        # State-specific growth rates (synthetic data)
        state_growth_rates = {
            'CA': 0.08, 'TX': 0.10, 'FL': 0.12, 'NY': 0.05,
            'WA': 0.07, 'CO': 0.09, 'AZ': 0.11, 'NC': 0.08,
            'GA': 0.09, 'TN': 0.10, 'NV': 0.11, 'OR': 0.06,
        }
        
        growth_rate = state_growth_rates.get(state, 0.06)  # Default 6%
        
        current_year = datetime.now().year
        current_quarter = (datetime.now().month - 1) // 3 + 1
        
        data = []
        base_index = 100.0
        
        for year in range(start_year, current_year + 1):
            max_quarter = 4 if year < current_year else current_quarter
            for quarter in range(1, max_quarter + 1):
                years_elapsed = year - start_year + (quarter - 1) / 4
                index_value = base_index * ((1 + growth_rate) ** years_elapsed)
                
                # Calculate annual change
                if years_elapsed >= 1:
                    prev_index = base_index * ((1 + growth_rate) ** (years_elapsed - 1))
                    annual_change = ((index_value - prev_index) / prev_index) * 100
                else:
                    annual_change = 0.0
                
                data.append({
                    'year': year,
                    'quarter': quarter,
                    'date': f'{year}Q{quarter}',
                    'index_sa': round(index_value, 2),
                    'annual_change': round(annual_change, 2)
                })
        
        return {
            'success': True,
            'state': state,
            'data': data,
            'latest': data[-1] if data else {},
            'count': len(data),
            'source': 'FHFA State HPI (Synthetic Demo Data)',
            'note': 'Using synthetic data. Integrate with FHFA API for real data.'
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': []
        }


def get_metro_hpi(metro: str = 'New York', start_year: int = 2020) -> Dict:
    """
    Get metro-area house price index data
    
    Args:
        metro: Metro area name (e.g., 'New York', 'Los Angeles', 'Chicago')
        start_year: Starting year for data (default 2020)
    
    Returns:
        Dict with metro HPI values
    """
    try:
        # Metro-specific growth rates (synthetic data)
        metro_growth_rates = {
            'New York': 0.06, 'Los Angeles': 0.08, 'Chicago': 0.05,
            'Dallas': 0.10, 'Houston': 0.09, 'Phoenix': 0.12,
            'Miami': 0.13, 'Atlanta': 0.09, 'Boston': 0.07,
            'San Francisco': 0.05, 'Seattle': 0.07, 'Denver': 0.09,
        }
        
        # Find matching metro
        matched_metro = None
        growth_rate = 0.06  # Default
        
        for m, rate in metro_growth_rates.items():
            if metro.lower() in m.lower() or m.lower() in metro.lower():
                matched_metro = m
                growth_rate = rate
                break
        
        if not matched_metro:
            matched_metro = metro
        
        current_year = datetime.now().year
        current_quarter = (datetime.now().month - 1) // 3 + 1
        
        data = []
        base_index = 100.0
        
        for year in range(start_year, current_year + 1):
            max_quarter = 4 if year < current_year else current_quarter
            for quarter in range(1, max_quarter + 1):
                years_elapsed = year - start_year + (quarter - 1) / 4
                index_value = base_index * ((1 + growth_rate) ** years_elapsed)
                
                # Calculate annual change
                if years_elapsed >= 1:
                    prev_index = base_index * ((1 + growth_rate) ** (years_elapsed - 1))
                    annual_change = ((index_value - prev_index) / prev_index) * 100
                else:
                    annual_change = 0.0
                
                data.append({
                    'year': year,
                    'quarter': quarter,
                    'date': f'{year}Q{quarter}',
                    'index_sa': round(index_value, 2),
                    'annual_change': round(annual_change, 2)
                })
        
        return {
            'success': True,
            'metro': matched_metro,
            'data': data,
            'latest': data[-1] if data else {},
            'count': len(data),
            'source': 'FHFA Metro HPI (Synthetic Demo Data)',
            'note': 'Using synthetic data. Integrate with FHFA API for real data.'
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': []
        }


def get_hpi_summary() -> Dict:
    """
    Get latest quarter summary across national, state, and metro regions
    
    Returns:
        Dict with latest HPI values and rankings
    """
    try:
        results = {}
        
        # National
        national = get_national_hpi(start_year=2023)
        if national['success'] and national.get('latest'):
            results['national'] = national['latest']
        
        # Top states by growth
        hot_states = [
            {'state': 'FL', 'index_sa': 145.2, 'annual_change': 12.3},
            {'state': 'TX', 'index_sa': 138.1, 'annual_change': 10.2},
            {'state': 'AZ', 'index_sa': 142.7, 'annual_change': 11.5},
            {'state': 'TN', 'index_sa': 135.9, 'annual_change': 10.0},
            {'state': 'NC', 'index_sa': 132.4, 'annual_change': 8.7},
        ]
        
        # Bottom states
        slow_states = [
            {'state': 'CA', 'index_sa': 118.2, 'annual_change': 3.5},
            {'state': 'NY', 'index_sa': 114.6, 'annual_change': 2.8},
            {'state': 'IL', 'index_sa': 112.3, 'annual_change': 2.1},
        ]
        
        # Top metros
        hot_metros = [
            {'metro': 'Miami, FL', 'index_sa': 152.8, 'annual_change': 13.9},
            {'metro': 'Phoenix, AZ', 'index_sa': 148.3, 'annual_change': 12.5},
            {'metro': 'Dallas, TX', 'index_sa': 143.7, 'annual_change': 11.2},
            {'metro': 'Atlanta, GA', 'index_sa': 139.4, 'annual_change': 9.8},
            {'metro': 'Tampa, FL', 'index_sa': 146.1, 'annual_change': 11.8},
        ]
        
        results['top_states'] = hot_states
        results['bottom_states'] = slow_states
        results['top_metros'] = hot_metros
        
        return {
            'success': True,
            **results,
            'timestamp': datetime.now().isoformat(),
            'source': 'FHFA House Price Index (Synthetic Demo Data)',
            'note': 'Using synthetic data. Integrate with FHFA API for real data.'
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    import json
    
    print("=" * 70)
    print("FHFA House Price Index API - QuantClaw Data")
    print("=" * 70)
    print("\n⚠️  Module uses synthetic demo data")
    print("    For production: integrate with FRED API or FHFA API")
    
    # Test national HPI
    print("\n1. National HPI (2023-present):")
    national = get_national_hpi(start_year=2023)
    if national['success']:
        latest = national['latest']
        print(f"   Latest: {latest['date']} - Index: {latest['index_sa']:.2f}, YoY: {latest.get('annual_change', 0):.2f}%")
        print(f"   Data points: {national['count']}")
    else:
        print(f"   Error: {national.get('error')}")
    
    # Test state HPI
    print("\n2. California State HPI:")
    ca = get_state_hpi('CA', start_year=2023)
    if ca['success']:
        latest = ca['latest']
        print(f"   Latest: {latest['date']} - Index: {latest['index_sa']:.2f}, YoY: {latest.get('annual_change', 0):.2f}%")
    else:
        print(f"   Error: {ca.get('error')}")
    
    # Test metro HPI
    print("\n3. New York Metro HPI:")
    ny = get_metro_hpi('New York', start_year=2023)
    if ny['success']:
        latest = ny['latest']
        print(f"   Metro: {ny['metro']}")
        print(f"   Latest: {latest['date']} - Index: {latest['index_sa']:.2f}, YoY: {latest.get('annual_change', 0):.2f}%")
    else:
        print(f"   Error: {ny.get('error')}")
    
    # Test summary
    print("\n4. HPI Summary (Latest Quarter):")
    summary = get_hpi_summary()
    if summary['success']:
        if 'national' in summary:
            nat = summary['national']
            print(f"   National: {nat['date']} - Index: {nat['index_sa']:.2f}, YoY: {nat['annual_change']:.2f}%")
        if 'top_states' in summary:
            print(f"   Top States: {[s['state'] for s in summary['top_states'][:3]]}")
        if 'top_metros' in summary:
            print(f"   Top Metros: {[m['metro'] for m in summary['top_metros'][:3]]}")
    else:
        print(f"   Error: {summary.get('error')}")
    
    print("\n" + "=" * 70)
    print("✅ Module loaded successfully")
    print("   Functions: get_national_hpi, get_state_hpi, get_metro_hpi, get_hpi_summary")
    print("=" * 70)
