#!/usr/bin/env python3
"""
Shared API Configuration Module

Centralized API key management for all QuantClaw Data modules.
Loads API keys from environment variables (.env file) and exports them as constants.

Usage:
    from api_config import FRED_API_KEY, EIA_API_KEY
    
    # Use in your API calls
    params = {"api_key": FRED_API_KEY}

Benefits:
    - Single source of truth for API keys
    - Consistent environment variable loading
    - Easy to add new API keys
    - Type hints and documentation

Author: QuantClaw Data Migration Script
Date: 2026-03-04
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
ENV_PATH = Path(__file__).parent.parent / '.env'
load_dotenv(ENV_PATH)

# ============================================================================
# FEDERAL RESERVE & ECONOMIC DATA
# ============================================================================

FRED_API_KEY = os.environ.get('FRED_API_KEY', '')
"""
Federal Reserve Economic Data (FRED) API Key
Register: https://fred.stlouisfed.org/docs/api/api_key.html
Free tier: 1000 requests/day
"""

# ============================================================================
# ENERGY INFORMATION ADMINISTRATION
# ============================================================================

EIA_API_KEY = os.environ.get('EIA_API_KEY', 'DEMO_KEY')
"""
Energy Information Administration (EIA) API Key
Register: https://www.eia.gov/opendata/register.php
Free tier: DEMO_KEY works, but register for higher limits
"""

# ============================================================================
# LABOR & CENSUS DATA
# ============================================================================

BLS_API_KEY = os.environ.get('BLS_API_KEY', '')
"""
Bureau of Labor Statistics (BLS) API Key
Register: https://data.bls.gov/registrationEngine/
Optional: V2 API works without key but with rate limits
"""

CENSUS_API_KEY = os.environ.get('CENSUS_API_KEY', '')
"""
US Census Bureau API Key
Register: https://api.census.gov/data/key_signup.html
Free tier: 500 requests/day
"""

# ============================================================================
# FINANCIAL MARKETS & STOCK DATA
# ============================================================================

FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY', '')
"""
Finnhub Stock API Key
Register: https://finnhub.io/register
Free tier: 60 API calls/minute
"""

POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY', '')
"""
Polygon.io Market Data API Key
Register: https://polygon.io/
Free tier: 5 API calls/minute
"""

IEX_API_KEY = os.environ.get('IEX_API_KEY', '')
"""
IEX Cloud Financial Data API Key
Register: https://iexcloud.io/
Free tier: 50,000 messages/month
"""

FINANCIAL_DATASETS_API_KEY = os.environ.get('FINANCIAL_DATASETS_API_KEY', '')
"""
Financial Datasets API Key
Custom API for financial data aggregation
"""

# ============================================================================
# BLOCKCHAIN & CRYPTO
# ============================================================================

ETHERSCAN_API_KEY = os.environ.get('ETHERSCAN_API_KEY', '')
"""
Etherscan Ethereum Blockchain Explorer API Key
Register: https://etherscan.io/apis
Free tier: 5 calls/second
"""

# ============================================================================
# AGRICULTURE & COMMODITIES
# ============================================================================

USDA_NASS_API_KEY = os.environ.get('USDA_NASS_API_KEY', '')
"""
USDA National Agricultural Statistics Service (NASS) API Key
Register: https://quickstats.nass.usda.gov/api
Free
"""

NASS_API_KEY = os.environ.get('NASS_API_KEY', '')
"""
Alias for USDA_NASS_API_KEY (for backward compatibility)
"""

# ============================================================================
# INTERNATIONAL DATA
# ============================================================================

BOK_API_KEY = os.environ.get('BOK_API_KEY', '')
"""
Bank of Korea Economic Statistics API Key
Register: https://ecos.bok.or.kr/
Free
"""

COMTRADE_API_KEY = os.environ.get('COMTRADE_API_KEY', '')
"""
UN Comtrade International Trade Statistics API Key
Register: https://comtrade.un.org/
Free tier: 100 requests/hour
"""

# ============================================================================
# VENTURE CAPITAL & STARTUPS
# ============================================================================

CRUNCHBASE_API_KEY = os.environ.get('CRUNCHBASE_API_KEY', '')
"""
Crunchbase Startup & VC Data API Key
Register: https://data.crunchbase.com/
Paid service
"""

# ============================================================================
# AEROSPACE & DEFENSE
# ============================================================================

SPACINSIDER_API_KEY = os.environ.get('SPACINSIDER_API_KEY', '')
"""
SpacInsider Space Industry Data API Key
Custom API for aerospace and defense data
"""

# ============================================================================
# GENERIC / FALLBACK
# ============================================================================

DEFAULT_API_KEY = os.environ.get('DEFAULT_API_KEY', '')
"""
Generic default API key for services that don't specify
"""

API_KEY = os.environ.get('API_KEY', '')
"""
Generic API_KEY environment variable
"""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_api_key(service: str) -> str:
    """
    Get API key for a specific service.
    
    Args:
        service: Service name (e.g., 'FRED', 'EIA', 'FINNHUB')
        
    Returns:
        API key string (may be empty if not configured)
        
    Example:
        >>> key = get_api_key('FRED')
        >>> if key:
        ...     make_api_call(api_key=key)
    """
    service_upper = service.upper()
    key_name = f"{service_upper}_API_KEY"
    return globals().get(key_name, '')


def is_configured(service: str) -> bool:
    """
    Check if an API key is configured for a service.
    
    Args:
        service: Service name (e.g., 'FRED', 'EIA', 'FINNHUB')
        
    Returns:
        True if API key is set and non-empty, False otherwise
        
    Example:
        >>> if is_configured('FRED'):
        ...     data = fetch_fred_data()
        ... else:
        ...     print("FRED API key not configured")
    """
    key = get_api_key(service)
    return bool(key and key not in ['', 'DEMO_KEY', 'demo', 'your_api_key_here'])


def list_configured_services() -> list[str]:
    """
    List all services that have API keys configured.
    
    Returns:
        List of service names that have valid API keys
        
    Example:
        >>> configured = list_configured_services()
        >>> print(f"Configured services: {', '.join(configured)}")
    """
    services = [
        'FRED', 'EIA', 'BLS', 'CENSUS', 'FINNHUB', 'POLYGON', 'IEX',
        'ETHERSCAN', 'USDA_NASS', 'NASS', 'BOK', 'COMTRADE',
        'CRUNCHBASE', 'SPACINSIDER', 'FINANCIAL_DATASETS'
    ]
    return [svc for svc in services if is_configured(svc)]


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

if __name__ == '__main__':
    # Print configuration status when run directly
    print("=" * 80)
    print("QuantClaw Data - API Configuration Status")
    print("=" * 80)
    print()
    
    configured = list_configured_services()
    print(f"✓ Configured services ({len(configured)}):")
    for service in configured:
        key = get_api_key(service)
        masked = key[:4] + "..." + key[-4:] if len(key) > 8 else "***"
        print(f"  • {service}: {masked}")
    
    print()
    print(f"✗ Not configured:")
    all_services = [
        'FRED', 'EIA', 'BLS', 'CENSUS', 'FINNHUB', 'POLYGON', 'IEX',
        'ETHERSCAN', 'USDA_NASS', 'BOK', 'COMTRADE',
        'CRUNCHBASE', 'SPACINSIDER', 'FINANCIAL_DATASETS'
    ]
    not_configured = [svc for svc in all_services if not is_configured(svc)]
    for service in not_configured:
        print(f"  • {service}")
    
    print()
    print("=" * 80)
