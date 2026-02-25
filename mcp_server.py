#!/usr/bin/env python3
"""
QuantClaw Data MCP Server
Model Context Protocol server exposing quantitative data tools

Provides access to all QuantClaw data modules via MCP protocol
"""

import sys
import json
from typing import Dict, List, Any, Optional

# Import all modules
sys.path.insert(0, '/home/quant/apps/quantclaw-data/modules')

from worldbank import (
    get_country_profile,
    get_countries,
    get_indicator_data,
    compare_countries,
    search_countries,
    get_regional_aggregate,
    WB_INDICATORS
)

import bls

from census import (
    get_retail_sales,
    get_housing_starts,
    get_building_permits,
    get_trade_deficit,
    get_economic_snapshot
)

from eurostat import (
    get_country_profile as eurostat_get_country_profile,
    list_countries as eurostat_list_countries,
    get_indicator_data as eurostat_get_indicator_data,
    compare_countries as eurostat_compare_countries,
    get_eu27_aggregate,
    search_countries as eurostat_search_countries,
    list_indicators as eurostat_list_indicators,
    EUROSTAT_INDICATORS,
    EU27_COUNTRIES,
    ALL_COUNTRIES as EUROSTAT_ALL_COUNTRIES
)

from cia_factbook import (
    scrape_country_data,
    compare_countries as cia_compare_countries,
    COUNTRY_CODES
)

from comtrade import (
    get_reporters,
    get_partners,
    get_commodities,
    search_country,
    search_commodity,
    get_bilateral_trade,
    get_top_trade_partners,
    get_trade_balance,
    get_commodity_trade,
    analyze_trade_concentration,
    get_trade_dependencies
)

from oecd import (
    get_cli,
    get_housing_prices,
    get_productivity,
    compare_countries as oecd_compare_countries,
    get_oecd_snapshot,
    OECD_COUNTRIES
)

from boj import (
    get_tankan_survey,
    get_monetary_base,
    get_fx_reserves,
    get_interest_rates,
    get_boj_comprehensive,
    compare_with_us,
    get_boj_meeting_schedule
)

import china_nbs


class MCPServer:
    """MCP Server for QuantClaw Data"""
    
    def __init__(self):
        self.tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, Dict]:
        """Register all available MCP tools"""
        return {
            'worldbank_country_profile': {
                'description': 'Get comprehensive economic profile for a country from World Bank data',
                'parameters': {
                    'country_code': {
                        'type': 'string',
                        'description': 'ISO 3-letter country code (e.g., USA, CHN, GBR)',
                        'required': True
                    },
                    'indicators': {
                        'type': 'array',
                        'description': 'Optional list of indicator keys to fetch',
                        'required': False
                    },
                    'years': {
                        'type': 'integer',
                        'description': 'Number of historical years to fetch (default 10)',
                        'required': False,
                        'default': 10
                    }
                },
                'handler': self._worldbank_country_profile
            },
            'worldbank_countries': {
                'description': 'Get list of all countries from World Bank',
                'parameters': {
                    'region': {
                        'type': 'string',
                        'description': 'Optional region code to filter (EAS, ECS, LCN, NAC, SAS, SSA)',
                        'required': False
                    }
                },
                'handler': self._worldbank_countries
            },
            'worldbank_indicator': {
                'description': 'Get specific economic indicator data for a country',
                'parameters': {
                    'country_code': {
                        'type': 'string',
                        'description': 'ISO 3-letter country code',
                        'required': True
                    },
                    'indicator_key': {
                        'type': 'string',
                        'description': 'Indicator key (GDP, INFLATION, FDI, etc.)',
                        'required': True
                    },
                    'start_year': {
                        'type': 'integer',
                        'description': 'Start year for data (optional)',
                        'required': False
                    },
                    'end_year': {
                        'type': 'integer',
                        'description': 'End year for data (optional)',
                        'required': False
                    }
                },
                'handler': self._worldbank_indicator
            },
            'worldbank_compare': {
                'description': 'Compare economic indicator across multiple countries',
                'parameters': {
                    'country_codes': {
                        'type': 'array',
                        'description': 'List of ISO 3-letter country codes',
                        'required': True
                    },
                    'indicator_key': {
                        'type': 'string',
                        'description': 'Indicator key to compare (default GDP)',
                        'required': False,
                        'default': 'GDP'
                    },
                    'year': {
                        'type': 'integer',
                        'description': 'Specific year to compare (optional, defaults to latest)',
                        'required': False
                    }
                },
                'handler': self._worldbank_compare
            },
            'worldbank_search': {
                'description': 'Search for countries by name',
                'parameters': {
                    'query': {
                        'type': 'string',
                        'description': 'Search query string',
                        'required': True
                    }
                },
                'handler': self._worldbank_search
            },
            'worldbank_regional': {
                'description': 'Get aggregated indicator data for a region',
                'parameters': {
                    'region_code': {
                        'type': 'string',
                        'description': 'World Bank region code (EAS, ECS, LCN, MEA, NAC, SAS, SSA)',
                        'required': True
                    },
                    'indicator_key': {
                        'type': 'string',
                        'description': 'Indicator key (default GDP)',
                        'required': False,
                        'default': 'GDP'
                    }
                },
                'handler': self._worldbank_regional
            },
            'worldbank_indicators': {
                'description': 'List all available World Bank indicators',
                'parameters': {},
                'handler': self._worldbank_indicators
            },
            'cia_factbook_country': {
                'description': 'Get comprehensive country data from CIA World Factbook (demographics, military, resources, trade)',
                'parameters': {
                    'country': {
                        'type': 'string',
                        'description': 'Country name (e.g., "United States", "China", "Israel")',
                        'required': True
                    }
                },
                'handler': self._cia_factbook_country
            },
            'cia_factbook_demographics': {
                'description': 'Get demographic data for a country (population, life expectancy, birth/death rates)',
                'parameters': {
                    'country': {
                        'type': 'string',
                        'description': 'Country name',
                        'required': True
                    }
                },
                'handler': self._cia_factbook_demographics
            },
            'cia_factbook_military': {
                'description': 'Get military expenditure data for a country (% of GDP, USD amounts)',
                'parameters': {
                    'country': {
                        'type': 'string',
                        'description': 'Country name',
                        'required': True
                    }
                },
                'handler': self._cia_factbook_military
            },
            'cia_factbook_trade': {
                'description': 'Get trade partners data for a country (top export/import partners)',
                'parameters': {
                    'country': {
                        'type': 'string',
                        'description': 'Country name',
                        'required': True
                    }
                },
                'handler': self._cia_factbook_trade
            },
            'cia_factbook_resources': {
                'description': 'Get natural resources data for a country',
                'parameters': {
                    'country': {
                        'type': 'string',
                        'description': 'Country name',
                        'required': True
                    }
                },
                'handler': self._cia_factbook_resources
            },
            'cia_factbook_compare': {
                'description': 'Compare multiple countries side-by-side (demographics, economy, military, trade)',
                'parameters': {
                    'countries': {
                        'type': 'array',
                        'description': 'List of country names to compare',
                        'required': True
                    }
                },
                'handler': self._cia_factbook_compare
            },
            
            # UN Comtrade Tools (Phase 103)
            'comtrade_reporters': {
                'description': 'Get list of reporting countries available in UN Comtrade',
                'parameters': {
                    'region': {
                        'type': 'string',
                        'description': 'Optional region filter',
                        'required': False
                    }
                },
                'handler': self._comtrade_reporters
            },
            'comtrade_search_country': {
                'description': 'Search for a country by name or ISO code in UN Comtrade database',
                'parameters': {
                    'query': {
                        'type': 'string',
                        'description': 'Country name or ISO code to search',
                        'required': True
                    }
                },
                'handler': self._comtrade_search_country
            },
            'comtrade_search_commodity': {
                'description': 'Search for commodity by description or HS code',
                'parameters': {
                    'query': {
                        'type': 'string',
                        'description': 'Commodity description or HS code',
                        'required': True
                    }
                },
                'handler': self._comtrade_search_commodity
            },
            'comtrade_bilateral_trade': {
                'description': 'Get bilateral trade flows between two countries',
                'parameters': {
                    'reporter': {
                        'type': 'string',
                        'description': 'Reporter country code (ISO3 or numeric)',
                        'required': True
                    },
                    'partner': {
                        'type': 'string',
                        'description': 'Partner country code (ISO3 or numeric)',
                        'required': True
                    },
                    'year': {
                        'type': 'integer',
                        'description': 'Year (default: previous year)',
                        'required': False
                    },
                    'flow': {
                        'type': 'string',
                        'description': 'Trade flow type: M (imports), X (exports), RM (re-imports), RX (re-exports)',
                        'required': False,
                        'default': 'M'
                    },
                    'api_key': {
                        'type': 'string',
                        'description': 'UN Comtrade API subscription key',
                        'required': False
                    }
                },
                'handler': self._comtrade_bilateral_trade
            },
            'comtrade_top_partners': {
                'description': 'Get top trade partners for a country',
                'parameters': {
                    'reporter': {
                        'type': 'string',
                        'description': 'Reporter country code',
                        'required': True
                    },
                    'flow': {
                        'type': 'string',
                        'description': 'Trade flow type (M or X)',
                        'required': False,
                        'default': 'M'
                    },
                    'year': {
                        'type': 'integer',
                        'description': 'Year (default: previous year)',
                        'required': False
                    },
                    'limit': {
                        'type': 'integer',
                        'description': 'Number of top partners to return',
                        'required': False,
                        'default': 20
                    },
                    'api_key': {
                        'type': 'string',
                        'description': 'UN Comtrade API subscription key',
                        'required': False
                    }
                },
                'handler': self._comtrade_top_partners
            },
            'comtrade_trade_balance': {
                'description': 'Calculate trade balance (exports - imports) for a country',
                'parameters': {
                    'reporter': {
                        'type': 'string',
                        'description': 'Reporter country code',
                        'required': True
                    },
                    'partner': {
                        'type': 'string',
                        'description': 'Optional partner country code (default: all partners)',
                        'required': False
                    },
                    'year': {
                        'type': 'integer',
                        'description': 'Year (default: previous year)',
                        'required': False
                    },
                    'api_key': {
                        'type': 'string',
                        'description': 'UN Comtrade API subscription key',
                        'required': False
                    }
                },
                'handler': self._comtrade_trade_balance
            },
            'comtrade_concentration': {
                'description': 'Analyze trade concentration using Herfindahl-Hirschman Index',
                'parameters': {
                    'reporter': {
                        'type': 'string',
                        'description': 'Reporter country code',
                        'required': True
                    },
                    'year': {
                        'type': 'integer',
                        'description': 'Year (default: previous year)',
                        'required': False
                    },
                    'flow': {
                        'type': 'string',
                        'description': 'Trade flow type (M or X)',
                        'required': False,
                        'default': 'X'
                    },
                    'api_key': {
                        'type': 'string',
                        'description': 'UN Comtrade API subscription key',
                        'required': False
                    }
                },
                'handler': self._comtrade_concentration
            },
            'comtrade_dependencies': {
                'description': 'Identify critical trade dependencies (partners above threshold)',
                'parameters': {
                    'reporter': {
                        'type': 'string',
                        'description': 'Reporter country code',
                        'required': True
                    },
                    'threshold': {
                        'type': 'number',
                        'description': 'Minimum share percentage to flag as dependency (default: 10%)',
                        'required': False,
                        'default': 10.0
                    },
                    'year': {
                        'type': 'integer',
                        'description': 'Year (default: previous year)',
                        'required': False
                    },
                    'api_key': {
                        'type': 'string',
                        'description': 'UN Comtrade API subscription key',
                        'required': False
                    }
                },
                'handler': self._comtrade_dependencies
            },
            
            # BLS Tools (Phase 97)
            'bls_cpi': {
                'description': 'Get Consumer Price Index (CPI) data - headline and core inflation with optional component breakdown',
                'parameters': {
                    'months': {
                        'type': 'integer',
                        'description': 'Number of months of data (default 12)',
                        'required': False,
                        'default': 12
                    },
                    'components': {
                        'type': 'boolean',
                        'description': 'Include CPI component breakdown (food, housing, gasoline, medical, etc)',
                        'required': False,
                        'default': False
                    }
                },
                'handler': self._bls_cpi
            },
            'bls_ppi': {
                'description': 'Get Producer Price Index (PPI) data - wholesale inflation indicators',
                'parameters': {
                    'months': {
                        'type': 'integer',
                        'description': 'Number of months of data (default 12)',
                        'required': False,
                        'default': 12
                    }
                },
                'handler': self._bls_ppi
            },
            'bls_employment': {
                'description': 'Get Non-Farm Payrolls (NFP) and employment statistics with optional sector breakdown',
                'parameters': {
                    'months': {
                        'type': 'integer',
                        'description': 'Number of months of data (default 12)',
                        'required': False,
                        'default': 12
                    },
                    'detailed': {
                        'type': 'boolean',
                        'description': 'Include employment by sector breakdown',
                        'required': False,
                        'default': False
                    }
                },
                'handler': self._bls_employment
            },
            'bls_wages': {
                'description': 'Get Average Hourly Earnings (wage) data by sector',
                'parameters': {
                    'months': {
                        'type': 'integer',
                        'description': 'Number of months of data (default 12)',
                        'required': False,
                        'default': 12
                    }
                },
                'handler': self._bls_wages
            },
            'bls_productivity': {
                'description': 'Get Labor Productivity and Unit Labor Costs (quarterly data)',
                'parameters': {
                    'years': {
                        'type': 'integer',
                        'description': 'Number of years of quarterly data (default 5)',
                        'required': False,
                        'default': 5
                    }
                },
                'handler': self._bls_productivity
            },
            'bls_inflation_summary': {
                'description': 'Get comprehensive inflation dashboard (CPI, PPI, wages, real wage growth)',
                'parameters': {},
                'handler': self._bls_inflation_summary
            },
            'bls_employment_summary': {
                'description': 'Get comprehensive employment dashboard (NFP, unemployment, labor force participation, sectors)',
                'parameters': {},
                'handler': self._bls_employment_summary
            },
            'bls_dashboard': {
                'description': 'Get complete BLS dashboard with all inflation, employment, and productivity data',
                'parameters': {},
                'handler': self._bls_dashboard
            },
            
            # Eurostat EU Statistics Tools (Phase 99)
            'eurostat_country_profile': {
                'description': 'Get comprehensive economic profile for an EU country from Eurostat SDMX API',
                'parameters': {
                    'country_code': {
                        'type': 'string',
                        'description': 'EU country code (e.g., DE, FR, IT, ES, EU27_2020 for aggregate)',
                        'required': True
                    },
                    'indicators': {
                        'type': 'array',
                        'description': 'Optional list of indicator keys (GDP, INFLATION, UNEMPLOYMENT, etc.)',
                        'required': False
                    },
                    'periods': {
                        'type': 'integer',
                        'description': 'Number of historical periods to fetch (default 20)',
                        'required': False,
                        'default': 20
                    }
                },
                'handler': self._eurostat_country_profile
            },
            'eurostat_countries': {
                'description': 'Get list of all EU countries available in Eurostat',
                'parameters': {
                    'eu27_only': {
                        'type': 'boolean',
                        'description': 'If true, return only EU-27 countries (default False)',
                        'required': False,
                        'default': False
                    }
                },
                'handler': self._eurostat_countries
            },
            'eurostat_indicator': {
                'description': 'Get specific economic indicator data for an EU country',
                'parameters': {
                    'country_code': {
                        'type': 'string',
                        'description': 'EU country code (e.g., DE, FR, IT)',
                        'required': True
                    },
                    'indicator_key': {
                        'type': 'string',
                        'description': 'Indicator key (GDP, INFLATION, UNEMPLOYMENT, etc.)',
                        'required': True
                    },
                    'last_n_periods': {
                        'type': 'integer',
                        'description': 'Number of recent periods to fetch (default 20)',
                        'required': False,
                        'default': 20
                    }
                },
                'handler': self._eurostat_indicator
            },
            'eurostat_compare': {
                'description': 'Compare economic indicator across multiple EU countries',
                'parameters': {
                    'country_codes': {
                        'type': 'array',
                        'description': 'List of EU country codes to compare',
                        'required': True
                    },
                    'indicator_key': {
                        'type': 'string',
                        'description': 'Indicator key to compare (default GDP)',
                        'required': False,
                        'default': 'GDP'
                    }
                },
                'handler': self._eurostat_compare
            },
            'eurostat_eu27_aggregate': {
                'description': 'Get EU-27 aggregate data for an indicator',
                'parameters': {
                    'indicator_key': {
                        'type': 'string',
                        'description': 'Indicator key (default GDP)',
                        'required': False,
                        'default': 'GDP'
                    },
                    'periods': {
                        'type': 'integer',
                        'description': 'Number of historical periods (default 20)',
                        'required': False,
                        'default': 20
                    }
                },
                'handler': self._eurostat_eu27_aggregate
            },
            'eurostat_search': {
                'description': 'Search for EU countries by name',
                'parameters': {
                    'query': {
                        'type': 'string',
                        'description': 'Search query string',
                        'required': True
                    }
                },
                'handler': self._eurostat_search
            },
            'eurostat_indicators': {
                'description': 'List all available Eurostat indicators',
                'parameters': {},
                'handler': self._eurostat_indicators
            },
            
            # IMF World Economic Outlook Tools (Phase 95)
            'imf_country_outlook': {
                'description': 'Get IMF World Economic Outlook data for a specific country including GDP growth, CPI inflation, unemployment, and projections',
                'parameters': {
                    'country_code': {
                        'type': 'string',
                        'description': 'ISO 3-letter country code (e.g., USA, CHN, DEU)',
                        'required': True
                    },
                    'indicators': {
                        'type': 'array',
                        'description': 'Optional list of indicator codes (default: NGDP_RPCH, PCPIPCH, NGDPD, PPPPC, LUR)',
                        'required': False
                    }
                },
                'handler': self._imf_country_outlook
            },
            'imf_compare_countries': {
                'description': 'Compare multiple countries on a specific IMF indicator (GDP growth, inflation, etc.)',
                'parameters': {
                    'country_codes': {
                        'type': 'array',
                        'description': 'List of ISO country codes to compare',
                        'required': True
                    },
                    'indicator': {
                        'type': 'string',
                        'description': 'IMF indicator code (default: NGDP_RPCH for GDP growth)',
                        'required': False,
                        'default': 'NGDP_RPCH'
                    },
                    'year': {
                        'type': 'integer',
                        'description': 'Year to compare (default: current year)',
                        'required': False
                    }
                },
                'handler': self._imf_compare_countries
            },
            'imf_global_outlook': {
                'description': 'Get global economic outlook - top and bottom performing countries for an indicator',
                'parameters': {
                    'indicator': {
                        'type': 'string',
                        'description': 'IMF indicator code (default: NGDP_RPCH)',
                        'required': False,
                        'default': 'NGDP_RPCH'
                    },
                    'year': {
                        'type': 'integer',
                        'description': 'Year to analyze (default: current year)',
                        'required': False
                    },
                    'top_n': {
                        'type': 'integer',
                        'description': 'Number of top/bottom countries to show (default: 20)',
                        'required': False,
                        'default': 20
                    }
                },
                'handler': self._imf_global_outlook
            },
            'imf_group_outlook': {
                'description': 'Get economic outlook for country groups (G7, G20, BRICS, emerging markets, etc.)',
                'parameters': {
                    'group': {
                        'type': 'string',
                        'description': 'Country group: g7, g20, brics, emerging, developed, asia, europe, middle_east, latin_america',
                        'required': True
                    },
                    'indicator': {
                        'type': 'string',
                        'description': 'IMF indicator code (default: NGDP_RPCH)',
                        'required': False,
                        'default': 'NGDP_RPCH'
                    },
                    'years': {
                        'type': 'array',
                        'description': 'List of years to analyze (default: last 3 + next 2)',
                        'required': False
                    }
                },
                'handler': self._imf_group_outlook
            },
            'imf_projections': {
                'description': 'Get IMF projections for a country with historical data and future forecasts',
                'parameters': {
                    'country_code': {
                        'type': 'string',
                        'description': 'ISO 3-letter country code',
                        'required': True
                    },
                    'indicator': {
                        'type': 'string',
                        'description': 'IMF indicator code (default: NGDP_RPCH)',
                        'required': False,
                        'default': 'NGDP_RPCH'
                    },
                    'years_ahead': {
                        'type': 'integer',
                        'description': 'Number of years ahead to project (default: 5)',
                        'required': False,
                        'default': 5
                    }
                },
                'handler': self._imf_projections
            },
            'imf_search_countries': {
                'description': 'Search for countries by name or ISO code',
                'parameters': {
                    'query': {
                        'type': 'string',
                        'description': 'Search query (country name or code)',
                        'required': True
                    }
                },
                'handler': self._imf_search_countries
            },
            
            # OECD Tools (Phase 102)
            'oecd_cli': {
                'description': 'Get Composite Leading Indicator for an OECD country - early signals of economic turning points',
                'parameters': {
                    'country': {
                        'type': 'string',
                        'description': 'ISO 3-letter country code (e.g., USA, DEU, JPN)',
                        'required': True
                    },
                    'measure': {
                        'type': 'string',
                        'description': 'CLI measure type: AMPLITUDE (default), AMPLNORM, or TREND',
                        'required': False,
                        'default': 'AMPLITUDE'
                    },
                    'months': {
                        'type': 'integer',
                        'description': 'Number of months of historical data (default 24)',
                        'required': False,
                        'default': 24
                    }
                },
                'handler': self._oecd_cli
            },
            'oecd_housing': {
                'description': 'Get Housing Price Index for an OECD country - real and nominal residential property prices',
                'parameters': {
                    'country': {
                        'type': 'string',
                        'description': 'ISO 3-letter country code (e.g., USA, DEU, JPN)',
                        'required': True
                    },
                    'measure': {
                        'type': 'string',
                        'description': 'Price measure: REAL (inflation-adjusted, default) or NOMINAL',
                        'required': False,
                        'default': 'REAL'
                    },
                    'quarters': {
                        'type': 'integer',
                        'description': 'Number of quarters of historical data (default 20)',
                        'required': False,
                        'default': 20
                    }
                },
                'handler': self._oecd_housing
            },
            'oecd_productivity': {
                'description': 'Get Labour Productivity (GDP per hour worked) for an OECD country',
                'parameters': {
                    'country': {
                        'type': 'string',
                        'description': 'ISO 3-letter country code (e.g., USA, DEU, JPN)',
                        'required': True
                    },
                    'years': {
                        'type': 'integer',
                        'description': 'Number of years of historical data (default 10)',
                        'required': False,
                        'default': 10
                    }
                },
                'handler': self._oecd_productivity
            },
            'oecd_compare': {
                'description': 'Compare an OECD indicator across multiple countries',
                'parameters': {
                    'indicator': {
                        'type': 'string',
                        'description': 'Indicator type: CLI, HOUSING, or PRODUCTIVITY',
                        'required': True
                    },
                    'countries': {
                        'type': 'array',
                        'description': 'List of country codes to compare (default: G7)',
                        'required': False
                    },
                    'measure': {
                        'type': 'string',
                        'description': 'Optional specific measure to compare',
                        'required': False
                    }
                },
                'handler': self._oecd_compare
            },
            'oecd_snapshot': {
                'description': 'Get comprehensive economic snapshot for a country (CLI, housing, productivity)',
                'parameters': {
                    'country': {
                        'type': 'string',
                        'description': 'ISO 3-letter country code (e.g., USA, DEU, JPN)',
                        'required': True
                    }
                },
                'handler': self._oecd_snapshot
            },
            'oecd_countries': {
                'description': 'List all OECD countries (38 members + key non-members)',
                'parameters': {},
                'handler': self._oecd_countries
            },
            'china_pmi': {
                'description': 'Get China Manufacturing PMI (Purchasing Managers Index). PMI > 50 = expansion, < 50 = contraction',
                'parameters': {
                    'months': {
                        'type': 'integer',
                        'description': 'Number of months of historical data (default 24)',
                        'required': False,
                        'default': 24
                    },
                    'api_key': {
                        'type': 'string',
                        'description': 'Optional FRED API key',
                        'required': False
                    }
                },
                'handler': self._china_pmi
            },
            'china_gdp': {
                'description': 'Get China GDP growth rate (Year-over-Year %)',
                'parameters': {
                    'quarters': {
                        'type': 'integer',
                        'description': 'Number of quarters of historical data (default 20)',
                        'required': False,
                        'default': 20
                    },
                    'api_key': {
                        'type': 'string',
                        'description': 'Optional FRED API key',
                        'required': False
                    }
                },
                'handler': self._china_gdp
            },
            'china_trade_balance': {
                'description': 'Get China trade balance, exports, and imports data',
                'parameters': {
                    'months': {
                        'type': 'integer',
                        'description': 'Number of months of historical data (default 24)',
                        'required': False,
                        'default': 24
                    },
                    'api_key': {
                        'type': 'string',
                        'description': 'Optional FRED API key',
                        'required': False
                    }
                },
                'handler': self._china_trade_balance
            },
            'china_fx_reserves': {
                'description': 'Get China foreign exchange reserves (excluding gold). China holds world largest FX reserves (~$3.2T)',
                'parameters': {
                    'months': {
                        'type': 'integer',
                        'description': 'Number of months of historical data (default 36)',
                        'required': False,
                        'default': 36
                    },
                    'api_key': {
                        'type': 'string',
                        'description': 'Optional FRED API key',
                        'required': False
                    }
                },
                'handler': self._china_fx_reserves
            },
            'china_yuan_rate': {
                'description': 'Get Yuan/USD exchange rate. Higher = weaker yuan (more yuan per dollar)',
                'parameters': {
                    'days': {
                        'type': 'integer',
                        'description': 'Number of days of historical data (default 365)',
                        'required': False,
                        'default': 365
                    },
                    'api_key': {
                        'type': 'string',
                        'description': 'Optional FRED API key',
                        'required': False
                    }
                },
                'handler': self._china_yuan_rate
            },
            'china_industrial_production': {
                'description': 'Get China Industrial Production Index (YoY % change). Key indicator of manufacturing activity',
                'parameters': {
                    'months': {
                        'type': 'integer',
                        'description': 'Number of months of historical data (default 24)',
                        'required': False,
                        'default': 24
                    },
                    'api_key': {
                        'type': 'string',
                        'description': 'Optional FRED API key',
                        'required': False
                    }
                },
                'handler': self._china_industrial_production
            },
            'china_inflation': {
                'description': 'Get China inflation data (CPI and PPI)',
                'parameters': {
                    'months': {
                        'type': 'integer',
                        'description': 'Number of months of historical data (default 24)',
                        'required': False,
                        'default': 24
                    },
                    'api_key': {
                        'type': 'string',
                        'description': 'Optional FRED API key',
                        'required': False
                    }
                },
                'handler': self._china_inflation
            },
            'china_dashboard': {
                'description': 'Get comprehensive China economic dashboard with all major indicators',
                'parameters': {
                    'api_key': {
                        'type': 'string',
                        'description': 'Optional FRED API key',
                        'required': False
                    }
                },
                'handler': self._china_dashboard
            },
            
            # Bank of Japan Tools (Phase 100)
            'boj_tankan': {
                'description': 'Get Bank of Japan Tankan Survey results - quarterly business sentiment (DI = % favorable - % unfavorable)',
                'parameters': {},
                'handler': self._boj_tankan
            },
            'boj_monetary_base': {
                'description': 'Get BOJ monetary base and money stock (M2, M3) - monthly money supply data',
                'parameters': {},
                'handler': self._boj_monetary_base
            },
            'boj_fx_reserves': {
                'description': 'Get Japan\'s foreign exchange reserves - world\'s 2nd largest at ~$1.3 trillion',
                'parameters': {},
                'handler': self._boj_fx_reserves
            },
            'boj_interest_rates': {
                'description': 'Get BOJ policy rate, JGB yields, and overnight rates - ultra-loose policy monitoring',
                'parameters': {},
                'handler': self._boj_interest_rates
            },
            'boj_comprehensive': {
                'description': 'Comprehensive BOJ dashboard combining all key indicators - Tankan, monetary base, FX reserves, rates',
                'parameters': {},
                'handler': self._boj_comprehensive
            },
            'boj_vs_fed': {
                'description': 'Compare BOJ vs Fed monetary policy - rate differentials and divergence analysis',
                'parameters': {},
                'handler': self._boj_vs_fed
            },
            'boj_meeting_schedule': {
                'description': 'Get BOJ Monetary Policy Meeting (MPM) schedule - 8 meetings per year',
                'parameters': {},
                'handler': self._boj_meeting_schedule
            }
        }
    
    # Handler methods
    def _worldbank_country_profile(self, country_code: str, indicators: Optional[List[str]] = None, years: int = 10) -> Dict:
        """Handler for worldbank_country_profile tool"""
        return get_country_profile(country_code.upper(), indicators=indicators, years=years)
    
    def _worldbank_countries(self, region: Optional[str] = None) -> Dict:
        """Handler for worldbank_countries tool"""
        return get_countries(region=region)
    
    def _worldbank_indicator(self, country_code: str, indicator_key: str, 
                            start_year: Optional[int] = None, end_year: Optional[int] = None) -> Dict:
        """Handler for worldbank_indicator tool"""
        if indicator_key.upper() not in WB_INDICATORS:
            return {
                'success': False,
                'error': f'Unknown indicator: {indicator_key}'
            }
        
        indicator_config = WB_INDICATORS[indicator_key.upper()]
        return get_indicator_data(country_code.upper(), indicator_config['id'], 
                                 start_year=start_year, end_year=end_year)
    
    def _worldbank_compare(self, country_codes: List[str], indicator_key: str = 'GDP', 
                          year: Optional[int] = None) -> Dict:
        """Handler for worldbank_compare tool"""
        # Ensure country codes are uppercase
        country_codes = [code.upper() for code in country_codes]
        return compare_countries(country_codes, indicator_key=indicator_key.upper(), year=year)
    
    def _worldbank_search(self, query: str) -> Dict:
        """Handler for worldbank_search tool"""
        return search_countries(query)
    
    def _worldbank_regional(self, region_code: str, indicator_key: str = 'GDP') -> Dict:
        """Handler for worldbank_regional tool"""
        return get_regional_aggregate(region_code.upper(), indicator_key=indicator_key.upper())
    
    def _worldbank_indicators(self) -> Dict:
        """Handler for worldbank_indicators tool"""
        indicators_list = []
        for key, config in WB_INDICATORS.items():
            indicators_list.append({
                'key': key,
                'id': config['id'],
                'name': config['name'],
                'description': config['description']
            })
        
        return {
            'success': True,
            'indicators': indicators_list,
            'count': len(indicators_list)
        }
    
    # IMF WEO Handler Methods
    def _imf_country_outlook(self, country_code: str, indicators: Optional[List[str]] = None) -> Dict:
        """Handler for imf_country_outlook tool"""
        return imf_weo.get_country_data(country_code.upper(), indicators=indicators)
    
    def _imf_compare_countries(self, country_codes: List[str], indicator: str = 'NGDP_RPCH', 
                               year: Optional[int] = None) -> Dict:
        """Handler for imf_compare_countries tool"""
        country_codes = [code.upper() for code in country_codes]
        return imf_weo.compare_countries(country_codes, indicator=indicator, year=year)
    
    def _imf_global_outlook(self, indicator: str = 'NGDP_RPCH', year: Optional[int] = None, 
                           top_n: int = 20) -> Dict:
        """Handler for imf_global_outlook tool"""
        return imf_weo.get_global_outlook(indicator=indicator, year=year, top_n=top_n)
    
    def _imf_group_outlook(self, group: str, indicator: str = 'NGDP_RPCH', 
                          years: Optional[List[int]] = None) -> Dict:
        """Handler for imf_group_outlook tool"""
        return imf_weo.get_group_outlook(group=group, indicator=indicator, years=years)
    
    def _imf_projections(self, country_code: str, indicator: str = 'NGDP_RPCH', 
                        years_ahead: int = 5) -> Dict:
        """Handler for imf_projections tool"""
        return imf_weo.get_projections(country_code.upper(), indicator=indicator, years_ahead=years_ahead)
    
    def _imf_search_countries(self, query: str) -> Dict:
        """Handler for imf_search_countries tool"""
        results = imf_weo.search_countries(query)
        return {
            'success': True,
            'results': results,
            'count': len(results)
        }
    
    # BLS Handler Methods (Phase 97)
    def _bls_cpi(self, months: int = 12, components: bool = False) -> Dict:
        """Handler for bls_cpi tool"""
        return bls.get_cpi_data(months=months, components=components)
    
    def _bls_ppi(self, months: int = 12) -> Dict:
        """Handler for bls_ppi tool"""
        return bls.get_ppi_data(months=months)
    
    def _bls_employment(self, months: int = 12, detailed: bool = False) -> Dict:
        """Handler for bls_employment tool"""
        return bls.get_employment_data(months=months, detailed=detailed)
    
    def _bls_wages(self, months: int = 12) -> Dict:
        """Handler for bls_wages tool"""
        return bls.get_wages_data(months=months)
    
    def _bls_productivity(self, years: int = 5) -> Dict:
        """Handler for bls_productivity tool"""
        return bls.get_productivity_data(years=years)
    
    def _bls_inflation_summary(self) -> Dict:
        """Handler for bls_inflation_summary tool"""
        return bls.get_inflation_summary()
    
    def _bls_employment_summary(self) -> Dict:
        """Handler for bls_employment_summary tool"""
        return bls.get_employment_summary()
    
    def _bls_dashboard(self) -> Dict:
        """Handler for bls_dashboard tool"""
        from datetime import datetime
        return {
            "timestamp": datetime.now().isoformat(),
            "inflation": bls.get_inflation_summary(),
            "employment": bls.get_employment_summary(),
            "productivity": bls.get_productivity_data(years=3),
        }
    
    # Eurostat EU Statistics Handlers (Phase 99)
    def _eurostat_country_profile(self, country_code: str, indicators: Optional[List[str]] = None, periods: int = 20) -> Dict:
        """Handler for eurostat_country_profile tool"""
        return eurostat_get_country_profile(country_code.upper(), indicators=indicators, periods=periods)
    
    def _eurostat_countries(self, eu27_only: bool = False) -> Dict:
        """Handler for eurostat_countries tool"""
        return eurostat_list_countries(eu27_only=eu27_only)
    
    def _eurostat_indicator(self, country_code: str, indicator_key: str, last_n_periods: int = 20) -> Dict:
        """Handler for eurostat_indicator tool"""
        return eurostat_get_indicator_data(country_code.upper(), indicator_key.upper(), last_n_periods=last_n_periods)
    
    def _eurostat_compare(self, country_codes: List[str], indicator_key: str = 'GDP') -> Dict:
        """Handler for eurostat_compare tool"""
        country_codes_upper = [code.upper() for code in country_codes]
        return eurostat_compare_countries(country_codes_upper, indicator_key=indicator_key.upper())
    
    def _eurostat_eu27_aggregate(self, indicator_key: str = 'GDP', periods: int = 20) -> Dict:
        """Handler for eurostat_eu27_aggregate tool"""
        return get_eu27_aggregate(indicator_key=indicator_key.upper(), periods=periods)
    
    def _eurostat_search(self, query: str) -> Dict:
        """Handler for eurostat_search tool"""
        return eurostat_search_countries(query)
    
    def _eurostat_indicators(self) -> Dict:
        """Handler for eurostat_indicators tool"""
        return eurostat_list_indicators()
    
    def list_tools(self) -> Dict:
        """List all available tools"""
        tools_list = []
        for tool_name, tool_info in self.tools.items():
            tools_list.append({
                'name': tool_name,
                'description': tool_info['description'],
                'parameters': tool_info['parameters']
            })
        
        return {
            'tools': tools_list,
            'count': len(tools_list)
        }
    
    # CIA Factbook Handler Methods
    def _cia_factbook_country(self, country: str) -> Dict:
        """Handler for cia_factbook_country tool"""
        return scrape_country_data(country)
    
    def _cia_factbook_demographics(self, country: str) -> Dict:
        """Handler for cia_factbook_demographics tool"""
        data = scrape_country_data(country)
        return data.get('demographics', {})
    
    def _cia_factbook_military(self, country: str) -> Dict:
        """Handler for cia_factbook_military tool"""
        data = scrape_country_data(country)
        return data.get('military', {})
    
    def _cia_factbook_trade(self, country: str) -> Dict:
        """Handler for cia_factbook_trade tool"""
        data = scrape_country_data(country)
        return data.get('trade', {})
    
    def _cia_factbook_resources(self, country: str) -> Dict:
        """Handler for cia_factbook_resources tool"""
        data = scrape_country_data(country)
        return data.get('resources', {})
    
    def _cia_factbook_compare(self, countries: List[str]) -> Dict:
        """Handler for cia_factbook_compare tool"""
        return cia_compare_countries(countries)
    
    # UN Comtrade Handlers (Phase 103)
    def _comtrade_reporters(self, region: Optional[str] = None) -> Dict:
        """Handler for comtrade_reporters tool"""
        return get_reporters(region)
    
    def _comtrade_search_country(self, query: str) -> Dict:
        """Handler for comtrade_search_country tool"""
        return search_country(query)
    
    def _comtrade_search_commodity(self, query: str) -> Dict:
        """Handler for comtrade_search_commodity tool"""
        return search_commodity(query)
    
    def _comtrade_bilateral_trade(self, reporter: str, partner: str, year: Optional[int] = None, 
                                  flow: str = 'M', api_key: Optional[str] = None) -> Dict:
        """Handler for comtrade_bilateral_trade tool"""
        return get_bilateral_trade(reporter, partner, year, flow, 'TOTAL', api_key)
    
    def _comtrade_top_partners(self, reporter: str, flow: str = 'M', year: Optional[int] = None,
                              limit: int = 20, api_key: Optional[str] = None) -> Dict:
        """Handler for comtrade_top_partners tool"""
        return get_top_trade_partners(reporter, flow, year, limit, api_key)
    
    def _comtrade_trade_balance(self, reporter: str, partner: Optional[str] = None, 
                               year: Optional[int] = None, api_key: Optional[str] = None) -> Dict:
        """Handler for comtrade_trade_balance tool"""
        return get_trade_balance(reporter, partner, year, api_key)
    
    def _comtrade_concentration(self, reporter: str, year: Optional[int] = None, 
                               flow: str = 'X', api_key: Optional[str] = None) -> Dict:
        """Handler for comtrade_concentration tool"""
        return analyze_trade_concentration(reporter, year, flow, api_key)
    
    def _comtrade_dependencies(self, reporter: str, threshold: float = 10.0, 
                              year: Optional[int] = None, api_key: Optional[str] = None) -> Dict:
        """Handler for comtrade_dependencies tool"""
        return get_trade_dependencies(reporter, threshold, year, api_key)
    
    # OECD Handlers (Phase 102)
    def _oecd_cli(self, country: str, measure: str = 'AMPLITUDE', months: int = 24) -> Dict:
        """Handler for oecd_cli tool"""
        return get_cli(country.upper(), measure, months)
    
    def _oecd_housing(self, country: str, measure: str = 'REAL', quarters: int = 20) -> Dict:
        """Handler for oecd_housing tool"""
        return get_housing_prices(country.upper(), measure, quarters)
    
    def _oecd_productivity(self, country: str, years: int = 10) -> Dict:
        """Handler for oecd_productivity tool"""
        return get_productivity(country.upper(), years)
    
    def _oecd_compare(self, indicator: str, countries: Optional[List[str]] = None, measure: Optional[str] = None) -> Dict:
        """Handler for oecd_compare tool"""
        if countries:
            countries = [c.upper() for c in countries]
        return oecd_compare_countries(indicator, countries, measure)
    
    def _oecd_snapshot(self, country: str) -> Dict:
        """Handler for oecd_snapshot tool"""
        return get_oecd_snapshot(country.upper())
    
    def _oecd_countries(self) -> Dict:
        """Handler for oecd_countries tool"""
        countries_list = [
            {'code': code, 'name': name}
            for code, name in sorted(OECD_COUNTRIES.items())
        ]
        return {
            'success': True,
            'countries': countries_list,
            'total': len(countries_list),
            'source': 'OECD'
        }
    
    # China NBS/PBOC Handlers (Phase 101)
    def _china_pmi(self, months: int = 24, api_key: Optional[str] = None) -> Dict:
        """Handler for china_pmi tool"""
        return china_nbs.get_china_pmi(months=months, api_key=api_key)
    
    def _china_gdp(self, quarters: int = 20, api_key: Optional[str] = None) -> Dict:
        """Handler for china_gdp tool"""
        return china_nbs.get_china_gdp(quarters=quarters, api_key=api_key)
    
    def _china_trade_balance(self, months: int = 24, api_key: Optional[str] = None) -> Dict:
        """Handler for china_trade_balance tool"""
        return china_nbs.get_trade_balance(months=months, api_key=api_key)
    
    def _china_fx_reserves(self, months: int = 36, api_key: Optional[str] = None) -> Dict:
        """Handler for china_fx_reserves tool"""
        return china_nbs.get_fx_reserves(months=months, api_key=api_key)
    
    def _china_yuan_rate(self, days: int = 365, api_key: Optional[str] = None) -> Dict:
        """Handler for china_yuan_rate tool"""
        return china_nbs.get_yuan_exchange_rate(days=days, api_key=api_key)
    
    def _china_industrial_production(self, months: int = 24, api_key: Optional[str] = None) -> Dict:
        """Handler for china_industrial_production tool"""
        return china_nbs.get_industrial_production(months=months, api_key=api_key)
    
    def _china_inflation(self, months: int = 24, api_key: Optional[str] = None) -> Dict:
        """Handler for china_inflation tool"""
        return china_nbs.get_china_inflation(months=months, api_key=api_key)
    
    def _china_dashboard(self, api_key: Optional[str] = None) -> Dict:
        """Handler for china_dashboard tool"""
        return china_nbs.get_china_dashboard(api_key=api_key)
    
    # BOJ (Bank of Japan) Handlers
    def _boj_tankan(self) -> Dict:
        """Handler for boj_tankan tool"""
        return get_tankan_survey()
    
    def _boj_monetary_base(self) -> Dict:
        """Handler for boj_monetary_base tool"""
        return get_monetary_base()
    
    def _boj_fx_reserves(self) -> Dict:
        """Handler for boj_fx_reserves tool"""
        return get_fx_reserves()
    
    def _boj_interest_rates(self) -> Dict:
        """Handler for boj_interest_rates tool"""
        return get_interest_rates()
    
    def _boj_comprehensive(self) -> Dict:
        """Handler for boj_comprehensive tool"""
        return get_boj_comprehensive()
    
    def _boj_vs_fed(self) -> Dict:
        """Handler for boj_vs_fed tool"""
        return compare_with_us()
    
    def _boj_meeting_schedule(self) -> Dict:
        """Handler for boj_meeting_schedule tool"""
        return get_boj_meeting_schedule()
    
    def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict:
        """Call a tool with given parameters"""
        if tool_name not in self.tools:
            return {
                'success': False,
                'error': f'Unknown tool: {tool_name}'
            }
        
        tool = self.tools[tool_name]
        handler = tool['handler']
        
        try:
            result = handler(**parameters)
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tool': tool_name
            }
    
    def handle_request(self, request: Dict) -> Dict:
        """Handle MCP request"""
        method = request.get('method')
        params = request.get('params', {})
        
        if method == 'tools/list':
            return self.list_tools()
        elif method == 'tools/call':
            tool_name = params.get('name')
            tool_params = params.get('arguments', {})
            return self.call_tool(tool_name, tool_params)
        else:
            return {
                'success': False,
                'error': f'Unknown method: {method}'
            }


def main():
    """Main CLI entry point"""
    server = MCPServer()
    
    if len(sys.argv) < 2:
        print_help(server)
        return 1
    
    command = sys.argv[1]
    
    if command == 'list-tools':
        # List all available tools
        result = server.list_tools()
        print(json.dumps(result, indent=2))
        return 0
    
    elif command == 'call':
        # Call a specific tool
        if len(sys.argv) < 3:
            print("Error: call requires tool name", file=sys.stderr)
            print("Usage: python mcp_server.py call <TOOL_NAME> <JSON_PARAMS>", file=sys.stderr)
            return 1
        
        tool_name = sys.argv[2]
        
        # Parse JSON parameters
        if len(sys.argv) >= 4:
            try:
                params = json.loads(sys.argv[3])
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON parameters: {e}", file=sys.stderr)
                return 1
        else:
            params = {}
        
        result = server.call_tool(tool_name, params)
        print(json.dumps(result, indent=2))
        return 0
    
    elif command == 'serve':
        # Start MCP server (stdin/stdout protocol)
        print("Starting QuantClaw Data MCP Server...", file=sys.stderr)
        
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                request = json.loads(line)
                response = server.handle_request(request)
                
                print(json.dumps(response))
                sys.stdout.flush()
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                error_response = {
                    'success': False,
                    'error': str(e)
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
        
        return 0
    
    else:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        print_help(server)
        return 1


def print_help(server: Optional[MCPServer] = None):
    """Print CLI help"""
    print("""
QuantClaw Data MCP Server

Commands:
  python mcp_server.py list-tools
                                    # List all available MCP tools
  
  python mcp_server.py call <TOOL_NAME> '<JSON_PARAMS>'
                                    # Call a specific tool
  
  python mcp_server.py serve        # Start MCP server (stdin/stdout protocol)

Examples:
  # List all tools
  python mcp_server.py list-tools
  
  # Get country profile
  python mcp_server.py call worldbank_country_profile '{"country_code": "USA"}'
  
  # Compare countries
  python mcp_server.py call worldbank_compare '{"country_codes": ["USA", "CHN", "JPN"], "indicator_key": "GDP"}'
  
  # Search countries
  python mcp_server.py call worldbank_search '{"query": "United"}'
  
  # Start server
  python mcp_server.py serve
""")
    
    if server:
        print("\nAvailable Tools:")
        tools = server.list_tools()
        for tool in tools['tools']:
            print(f"\n  {tool['name']}")
            print(f"    {tool['description']}")


if __name__ == "__main__":
    sys.exit(main())
