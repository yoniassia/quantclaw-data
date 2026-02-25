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

from sec_xbrl_financial_statements import (
    get_financial_statements,
    compare_financial_statements,
    search_xbrl_companies,
    get_cik_from_ticker
)

from dcf_valuation import (
    perform_dcf_valuation,
    compare_valuations
)

from comparable_companies import (
    get_company_metrics,
    generate_comps_table,
    compare_to_peers,
    sector_analysis,
    PEER_GROUPS
)

from dividend_history import (
    get_dividend_history,
    calculate_growth_rates,
    get_ex_dividend_calendar,
    project_dividends,
    check_aristocrat_status,
    compare_dividend_growth
)

from earnings_surprise_history import (
    get_earnings_history,
    analyze_surprise_patterns,
    estimate_whisper_numbers,
    analyze_post_earnings_drift,
    calculate_earnings_quality,
    compare_surprise_history
)

from stock_split_corporate_events import (
    get_stock_splits,
    analyze_split_impact,
    get_corporate_actions,
    compare_split_performance
)

from equity_screener import (
    EquityScreener,
    FACTOR_CATEGORIES,
    SCREENING_PRESETS
)

from relative_valuation import (
    get_valuation_metrics,
    get_sector_valuation,
    get_cross_sector_comparison,
    get_peer_comparison,
    screen_by_valuation,
    SECTOR_TICKERS
)

from adr_gdr_arbitrage import (
    calculate_arbitrage_spread,
    scan_all_adrs,
    compare_adrs,
    get_adr_list,
    ADR_PAIRS
)

from stock_loan_borrow_costs import (
    get_borrow_cost_analysis,
    get_threshold_securities,
    scan_hard_to_borrow_stocks,
    compare_borrow_costs
)

from spac_lifecycle import SPACLifecycleTracker
from secondary_offering_monitor import SecondaryOfferingMonitor

from analyst_target_price import (
    get_consensus_targets,
    get_recommendation_distribution,
    get_revision_velocity,
    get_target_summary,
    compare_targets
)

from mutual_fund_flow_analysis import (
    get_fund_flows_yahoo,
    compare_fund_flows,
    analyze_sector_rotation,
    get_smart_money_flows,
    get_fund_performance_comparison,
    get_recent_nport_filings,
    search_fund_cik
)

from etf_flow_tracker import (
    calculate_flows_from_aum,
    generate_flow_signals,
    get_top_etf_flows,
    get_sector_flows
)

from global_equity_index_returns import (
    get_index_daily_returns,
    get_index_performance,
    get_regional_performance,
    calculate_correlation_matrix,
    compare_indices,
    list_available_indices
)


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
            },
            
            # Index Reconstitution Tracker Tools (Phase 136)
            'index_sp500_changes': {
                'description': 'Get recent S&P 500 index additions and deletions with price impact analysis',
                'parameters': {
                    'days': {
                        'type': 'integer',
                        'description': 'Look back period in days (default 365)',
                        'required': False,
                        'default': 365
                    }
                },
                'handler': self._index_sp500_changes
            },
            'index_russell_calendar': {
                'description': 'Get Russell reconstitution schedule (rank day and effective date)',
                'parameters': {
                    'year': {
                        'type': 'integer',
                        'description': 'Year to get schedule for (default: current year)',
                        'required': False
                    }
                },
                'handler': self._index_russell_calendar
            },
            'index_russell_candidates': {
                'description': 'Predict Russell 2000/3000 addition and deletion candidates',
                'parameters': {
                    'index': {
                        'type': 'string',
                        'description': 'Index to analyze: 2000 or 3000 (default: 2000)',
                        'required': False,
                        'default': '2000'
                    },
                    'limit': {
                        'type': 'integer',
                        'description': 'Number of candidates to return (default 20)',
                        'required': False,
                        'default': 20
                    }
                },
                'handler': self._index_russell_candidates
            },
            'index_msci_schedule': {
                'description': 'Get MSCI semi-annual rebalancing schedule',
                'parameters': {
                    'year': {
                        'type': 'integer',
                        'description': 'Year to get schedule for (default: current year)',
                        'required': False
                    }
                },
                'handler': self._index_msci_schedule
            },
            'index_addition_opportunity': {
                'description': 'Analyze trading opportunity for potential index addition',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    },
                    'index_name': {
                        'type': 'string',
                        'description': 'Index name (default: S&P 500)',
                        'required': False,
                        'default': 'S&P 500'
                    }
                },
                'handler': self._index_addition_opportunity
            },
            'index_reconstitution_stats': {
                'description': 'Get historical statistics on index reconstitution price impacts',
                'parameters': {},
                'handler': self._index_reconstitution_stats
            },
            
            # SEC XBRL Financial Statements (Phase 134)
            'sec_xbrl_financials': {
                'description': 'Get comprehensive financial statements (income statement, balance sheet, cash flow) from SEC XBRL filings',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol (e.g., AAPL, MSFT, TSLA)',
                        'required': True
                    },
                    'form_type': {
                        'type': 'string',
                        'description': 'Form type: 10-K (annual) or 10-Q (quarterly). Default: 10-K',
                        'required': False,
                        'default': '10-K'
                    },
                    'fiscal_year': {
                        'type': 'integer',
                        'description': 'Specific fiscal year to retrieve (optional, default: most recent)',
                        'required': False
                    }
                },
                'handler': self._sec_xbrl_financials
            },
            'sec_xbrl_compare': {
                'description': 'Compare financial statements across multiple fiscal years with growth trends and CAGR',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    },
                    'years': {
                        'type': 'array',
                        'description': 'List of fiscal years to compare',
                        'required': True
                    },
                    'form_type': {
                        'type': 'string',
                        'description': 'Form type: 10-K or 10-Q. Default: 10-K',
                        'required': False,
                        'default': '10-K'
                    }
                },
                'handler': self._sec_xbrl_compare
            },
            'sec_xbrl_search': {
                'description': 'Search for companies in SEC database by ticker or company name',
                'parameters': {
                    'search_term': {
                        'type': 'string',
                        'description': 'Company name or ticker fragment to search',
                        'required': True
                    },
                    'limit': {
                        'type': 'integer',
                        'description': 'Maximum results to return (default: 10)',
                        'required': False,
                        'default': 10
                    }
                },
                'handler': self._sec_xbrl_search
            },
            'sec_xbrl_cik': {
                'description': 'Convert ticker symbol to SEC CIK (Central Index Key) code',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    }
                },
                'handler': self._sec_xbrl_cik
            },
            
            # Dividend History & Projections (Phase 139)
            'dividend_history': {
                'description': 'Get complete dividend payment history with dates, amounts, and yield analysis',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol (e.g., AAPL, JNJ, KO)',
                        'required': True
                    },
                    'years': {
                        'type': 'integer',
                        'description': 'Number of years of history (default: 10)',
                        'required': False,
                        'default': 10
                    }
                },
                'handler': self._dividend_history
            },
            'dividend_growth_rates': {
                'description': 'Calculate dividend growth rates (1Y, 3Y, 5Y, 10Y CAGR) and consistency metrics',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    }
                },
                'handler': self._dividend_growth_rates
            },
            'dividend_calendar': {
                'description': 'Get ex-dividend date calendar with upcoming projected dates and historical schedule',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    },
                    'months_ahead': {
                        'type': 'integer',
                        'description': 'Months to project ahead (default: 12)',
                        'required': False,
                        'default': 12
                    }
                },
                'handler': self._dividend_calendar
            },
            'dividend_projections': {
                'description': 'Project future dividend payments based on historical growth rates',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    },
                    'years': {
                        'type': 'integer',
                        'description': 'Number of years to project (default: 5)',
                        'required': False,
                        'default': 5
                    },
                    'growth_rate': {
                        'type': 'number',
                        'description': 'Optional custom growth rate (%, uses historical if not provided)',
                        'required': False
                    }
                },
                'handler': self._dividend_projections
            },
            'dividend_aristocrat_check': {
                'description': 'Check if company qualifies as Dividend Aristocrat/King/Champion (25+ years of increases)',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    }
                },
                'handler': self._dividend_aristocrat
            },
            'dividend_compare': {
                'description': 'Compare dividend growth rates across multiple stocks',
                'parameters': {
                    'tickers': {
                        'type': 'array',
                        'description': 'List of stock ticker symbols to compare',
                        'required': True
                    }
                },
                'handler': self._dividend_compare
            },
            
            # Stock Split & Corporate Events (Phase 146)
            'stock_split_history': {
                'description': 'Get complete stock split history including forward/reverse splits, cumulative factors, and patterns',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol (e.g., AAPL, TSLA, NVDA)',
                        'required': True
                    },
                    'years': {
                        'type': 'integer',
                        'description': 'Number of years of history (default: 20)',
                        'required': False,
                        'default': 20
                    }
                },
                'handler': self._stock_split_history
            },
            'stock_split_impact': {
                'description': 'Analyze pre/post split price impact, volume changes, and volatility effects for a specific split',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    },
                    'split_date': {
                        'type': 'string',
                        'description': 'Specific split date to analyze (YYYY-MM-DD), or None for most recent split',
                        'required': False
                    }
                },
                'handler': self._stock_split_impact
            },
            'stock_corporate_actions': {
                'description': 'Get all corporate actions (splits, dividends) with price impact analysis for multiple periods',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    },
                    'years': {
                        'type': 'integer',
                        'description': 'Number of years of history (default: 5)',
                        'required': False,
                        'default': 5
                    }
                },
                'handler': self._stock_corporate_actions
            },
            'stock_compare_splits': {
                'description': 'Compare split performance across multiple tickers to identify best/worst performers post-split',
                'parameters': {
                    'tickers': {
                        'type': 'array',
                        'description': 'List of stock ticker symbols to compare',
                        'required': True
                    },
                    'lookback_days': {
                        'type': 'integer',
                        'description': 'Days to look back for splits (default: 365)',
                        'required': False,
                        'default': 365
                    }
                },
                'handler': self._stock_compare_splits
            },
            
            # DCF Valuation Engine (Phase 142)
            'dcf_valuation': {
                'description': 'Perform comprehensive discounted cash flow (DCF) valuation using SEC XBRL financials and FRED rates',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol (e.g., AAPL, MSFT, TSLA)',
                        'required': True
                    },
                    'projection_years': {
                        'type': 'integer',
                        'description': 'Number of years to project cash flows (default: 5)',
                        'required': False,
                        'default': 5
                    },
                    'terminal_growth_rate': {
                        'type': 'number',
                        'description': 'Terminal growth rate (decimal, default: 0.025 = 2.5%)',
                        'required': False,
                        'default': 0.025
                    },
                    'tax_rate': {
                        'type': 'number',
                        'description': 'Corporate tax rate (decimal, default: 0.21 = 21%)',
                        'required': False,
                        'default': 0.21
                    }
                },
                'handler': self._dcf_valuation
            },
            'dcf_compare': {
                'description': 'Compare DCF valuations across multiple companies',
                'parameters': {
                    'tickers': {
                        'type': 'array',
                        'description': 'List of stock ticker symbols to compare',
                        'required': True
                    }
                },
                'handler': self._dcf_compare
            },
            'dcf_sensitivity': {
                'description': 'Get sensitivity analysis showing how valuation changes with different WACC and terminal growth assumptions',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    }
                },
                'handler': self._dcf_sensitivity
            },
            
            # Comparable Company Analysis (Phase 141)
            'comps_company_metrics': {
                'description': 'Get comprehensive valuation multiples and financial metrics for a single company (P/E, EV/EBITDA, margins, growth, leverage)',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol (e.g., AAPL, MSFT, TSLA)',
                        'required': True
                    }
                },
                'handler': self._comps_company_metrics
            },
            'comps_generate_table': {
                'description': 'Generate comparable company analysis table with summary statistics for multiple companies',
                'parameters': {
                    'tickers': {
                        'type': 'array',
                        'description': 'List of ticker symbols to compare',
                        'required': True
                    }
                },
                'handler': self._comps_generate_table
            },
            'comps_compare_to_peers': {
                'description': 'Compare a company to its peer group with relative positioning analysis',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Target company ticker symbol',
                        'required': True
                    },
                    'peer_group': {
                        'type': 'array',
                        'description': 'Optional list of peer tickers (auto-detect if omitted)',
                        'required': False
                    }
                },
                'handler': self._comps_compare_to_peers
            },
            'comps_sector_analysis': {
                'description': 'Analyze all companies in a sector with aggregate statistics',
                'parameters': {
                    'sector_name': {
                        'type': 'string',
                        'description': 'Sector name (technology, semiconductors, banks, pharma, etc.)',
                        'required': True
                    },
                    'min_market_cap': {
                        'type': 'number',
                        'description': 'Minimum market cap filter in USD (optional)',
                        'required': False
                    }
                },
                'handler': self._comps_sector_analysis
            },
            'comps_peer_groups': {
                'description': 'List all available predefined peer groups',
                'parameters': {},
                'handler': self._comps_peer_groups
            },
            
            # Earnings Surprise History (Phase 144)
            'earnings_surprise_history': {
                'description': 'Get historical earnings surprises with beat/miss analysis and post-earnings drift',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol (e.g., AAPL, TSLA, NVDA)',
                        'required': True
                    },
                    'quarters': {
                        'type': 'integer',
                        'description': 'Number of quarters of history (default: 12)',
                        'required': False,
                        'default': 12
                    }
                },
                'handler': self._earnings_surprise_history
            },
            'earnings_surprise_patterns': {
                'description': 'Analyze beat/miss patterns, streaks, and consistency',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    }
                },
                'handler': self._earnings_surprise_patterns
            },
            'earnings_whisper_numbers': {
                'description': 'Estimate whisper numbers from pre-earnings price action',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    },
                    'quarters': {
                        'type': 'integer',
                        'description': 'Number of quarters to analyze (default: 8)',
                        'required': False,
                        'default': 8
                    }
                },
                'handler': self._earnings_whisper_numbers
            },
            'earnings_post_drift': {
                'description': 'Analyze post-earnings announcement drift (PEAD) - price movement after earnings',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    },
                    'quarters': {
                        'type': 'integer',
                        'description': 'Number of quarters to analyze (default: 12)',
                        'required': False,
                        'default': 12
                    }
                },
                'handler': self._earnings_post_drift
            },
            'earnings_quality_score': {
                'description': 'Calculate earnings quality score based on surprise consistency',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    }
                },
                'handler': self._earnings_quality_score
            },
            'earnings_compare_surprises': {
                'description': 'Compare earnings surprise history across multiple tickers',
                'parameters': {
                    'tickers': {
                        'type': 'array',
                        'description': 'List of stock ticker symbols to compare',
                        'required': True
                    }
                },
                'handler': self._earnings_compare_surprises
            },
            
            # Equity Screener (Phase 140)
            'screen_stocks': {
                'description': 'Screen stocks using custom factor filters (P/E, ROE, momentum, etc.) - supports 8000+ stocks with 50+ factors',
                'parameters': {
                    'filters': {
                        'type': 'object',
                        'description': 'Dictionary of {factor_name: [min_value, max_value]} filters',
                        'required': True
                    },
                    'min_market_cap': {
                        'type': 'number',
                        'description': 'Minimum market cap filter (optional)',
                        'required': False
                    },
                    'sectors': {
                        'type': 'array',
                        'description': 'List of sectors to include (optional)',
                        'required': False
                    },
                    'limit': {
                        'type': 'integer',
                        'description': 'Maximum number of results (default 50)',
                        'required': False,
                        'default': 50
                    }
                },
                'handler': self._screen_stocks
            },
            'screen_preset': {
                'description': 'Screen stocks using a predefined preset (value, growth, momentum, dividend, quality)',
                'parameters': {
                    'preset_name': {
                        'type': 'string',
                        'description': 'Name of preset: value, growth, momentum, dividend, quality',
                        'required': True
                    },
                    'limit': {
                        'type': 'integer',
                        'description': 'Maximum number of results (default 50)',
                        'required': False,
                        'default': 50
                    }
                },
                'handler': self._screen_preset
            },
            'rank_stocks': {
                'description': 'Rank stocks by composite factor score',
                'parameters': {
                    'tickers': {
                        'type': 'array',
                        'description': 'Optional list of tickers to rank',
                        'required': False
                    },
                    'factors': {
                        'type': 'array',
                        'description': 'List of factors to use in ranking',
                        'required': False
                    },
                    'weights': {
                        'type': 'object',
                        'description': 'Optional factor weights dictionary',
                        'required': False
                    },
                    'limit': {
                        'type': 'integer',
                        'description': 'Maximum number of results (default 50)',
                        'required': False,
                        'default': 50
                    }
                },
                'handler': self._rank_stocks
            },
            'screen_factors': {
                'description': 'Get list of all available screening factors by category',
                'parameters': {},
                'handler': self._screen_factors
            },
            'screen_presets_list': {
                'description': 'Get list of all available screening presets',
                'parameters': {},
                'handler': self._screen_presets_list
            },
            
            # Relative Valuation Matrix (Phase 143)
            'valuation_heatmap': {
                'description': 'Generate cross-sector valuation comparison heatmap showing P/E, PEG, P/B, EV/EBITDA, dividend yields across all sectors',
                'parameters': {
                    'format': {
                        'type': 'string',
                        'description': 'Output format: json or text',
                        'required': False,
                        'default': 'json'
                    }
                },
                'handler': self._valuation_heatmap
            },
            'valuation_sector': {
                'description': 'Get valuation metrics for all stocks in a specific sector with sector averages',
                'parameters': {
                    'sector': {
                        'type': 'string',
                        'description': 'Sector name (e.g., Technology, Healthcare, Financials)',
                        'required': True
                    }
                },
                'handler': self._valuation_sector
            },
            'valuation_stock': {
                'description': 'Get comprehensive valuation metrics for a single stock (P/E, PEG, P/B, EV/EBITDA, yields, growth)',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    }
                },
                'handler': self._valuation_stock
            },
            'valuation_peers': {
                'description': 'Compare valuation metrics across a custom peer group with relative valuations',
                'parameters': {
                    'tickers': {
                        'type': 'array',
                        'description': 'List of ticker symbols to compare',
                        'required': True
                    }
                },
                'handler': self._valuation_peers
            },
            'valuation_screen': {
                'description': 'Screen stocks by valuation metric threshold (find cheap/expensive stocks)',
                'parameters': {
                    'metric': {
                        'type': 'string',
                        'description': 'Valuation metric: pe_trailing, peg_ratio, price_to_book, ev_to_ebitda',
                        'required': True
                    },
                    'threshold': {
                        'type': 'number',
                        'description': 'Numeric threshold value',
                        'required': True
                    },
                    'comparison': {
                        'type': 'string',
                        'description': 'Comparison type: below or above',
                        'required': False,
                        'default': 'below'
                    },
                    'limit': {
                        'type': 'integer',
                        'description': 'Maximum number of results',
                        'required': False,
                        'default': 20
                    }
                },
                'handler': self._valuation_screen
            },
            'valuation_sectors_list': {
                'description': 'Get list of all available sectors for valuation analysis',
                'parameters': {},
                'handler': self._valuation_sectors_list
            },
            
            # ADR/GDR Arbitrage Monitor (Phase 147)
            'adr_spread': {
                'description': 'Calculate arbitrage spread between ADR and ordinary shares with FX adjustment',
                'parameters': {
                    'adr_ticker': {
                        'type': 'string',
                        'description': 'US-listed ADR ticker symbol (e.g., BP, BABA, SONY)',
                        'required': True
                    }
                },
                'handler': self._adr_spread
            },
            'adr_scan': {
                'description': 'Scan all known ADR/ordinary pairs for arbitrage opportunities above threshold',
                'parameters': {
                    'min_spread_bps': {
                        'type': 'number',
                        'description': 'Minimum spread threshold in basis points (default 50)',
                        'required': False,
                        'default': 50.0
                    },
                    'sort_by': {
                        'type': 'string',
                        'description': 'Sort results by: spread, volume, or alpha (spread*volume score)',
                        'required': False,
                        'default': 'spread'
                    }
                },
                'handler': self._adr_scan
            },
            'adr_compare': {
                'description': 'Compare arbitrage spreads across multiple ADRs side-by-side',
                'parameters': {
                    'tickers': {
                        'type': 'array',
                        'description': 'List of ADR ticker symbols to compare',
                        'required': True
                    }
                },
                'handler': self._adr_compare
            },
            'adr_list': {
                'description': 'Get list of all known ADR/GDR pairs with conversion ratios and currencies',
                'parameters': {
                    'currency': {
                        'type': 'string',
                        'description': 'Optional filter by currency (GBP, EUR, JPY, etc.)',
                        'required': False
                    }
                },
                'handler': self._adr_list
            },
            
            # Stock Loan & Borrow Costs (Phase 150)
            'stock_borrow_analysis': {
                'description': 'Comprehensive stock borrow cost analysis with estimated borrow rates, short interest, and squeeze risk',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol (e.g., GME, AMC, TSLA)',
                        'required': True
                    }
                },
                'handler': self._stock_borrow_analysis
            },
            'threshold_securities_list': {
                'description': 'Get FINRA Reg SHO threshold securities list (stocks with significant delivery fails)',
                'parameters': {
                    'exchange': {
                        'type': 'string',
                        'description': 'Exchange filter: nyse, nasdaq, or all (default: all)',
                        'required': False,
                        'default': 'all'
                    }
                },
                'handler': self._threshold_securities_list
            },
            'htb_scan': {
                'description': 'Scan multiple stocks for hard-to-borrow status and high borrow costs',
                'parameters': {
                    'tickers': {
                        'type': 'array',
                        'description': 'List of ticker symbols to scan',
                        'required': True
                    }
                },
                'handler': self._htb_scan
            },
            'borrow_cost_compare': {
                'description': 'Compare borrow costs and short squeeze risk across multiple stocks',
                'parameters': {
                    'tickers': {
                        'type': 'array',
                        'description': 'List of ticker symbols to compare',
                        'required': True
                    }
                },
                'handler': self._borrow_cost_compare
            },
            
            # Analyst Target Price Tracker (Phase 145)
            'analyst_consensus_targets': {
                'description': 'Get analyst consensus price targets with bull/bear cases and upside potential',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    }
                },
                'handler': self._analyst_consensus_targets
            },
            'analyst_recommendations': {
                'description': 'Get analyst recommendation distribution (strong buy, buy, hold, sell, strong sell)',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    }
                },
                'handler': self._analyst_recommendations
            },
            'analyst_revision_velocity': {
                'description': 'Track analyst target price revision velocity with upgrade/downgrade momentum',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    },
                    'days': {
                        'type': 'integer',
                        'description': 'Number of days to analyze (default 90)',
                        'required': False,
                        'default': 90
                    }
                },
                'handler': self._analyst_revision_velocity
            },
            'analyst_target_summary': {
                'description': 'Comprehensive analyst target price summary combining targets, recommendations, and revisions',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    }
                },
                'handler': self._analyst_target_summary
            },
            'analyst_compare_targets': {
                'description': 'Compare analyst price targets across multiple stocks',
                'parameters': {
                    'tickers': {
                        'type': 'array',
                        'description': 'List of stock ticker symbols to compare',
                        'required': True
                    }
                },
                'handler': self._analyst_compare_targets
            },
            
            # Mutual Fund Flow Analysis (Phase 152)
            'fund_flows': {
                'description': 'Get mutual fund flow data and metrics from Yahoo Finance',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Fund ticker symbol (e.g., SPY, QQQ, VTI)',
                        'required': True
                    },
                    'period': {
                        'type': 'string',
                        'description': 'Time period: 1mo, 3mo, 6mo, 1y, 2y, 5y (default: 1y)',
                        'required': False,
                        'default': '1y'
                    }
                },
                'handler': self._fund_flows
            },
            'compare_fund_flows': {
                'description': 'Compare flows and performance across multiple mutual funds or ETFs',
                'parameters': {
                    'tickers': {
                        'type': 'array',
                        'description': 'List of fund ticker symbols to compare',
                        'required': True
                    },
                    'period': {
                        'type': 'string',
                        'description': 'Time period for comparison (default: 1y)',
                        'required': False,
                        'default': '1y'
                    }
                },
                'handler': self._compare_fund_flows
            },
            'fund_sector_rotation': {
                'description': 'Analyze sector allocation and holdings for a fund',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Fund ticker symbol',
                        'required': True
                    }
                },
                'handler': self._fund_sector_rotation
            },
            'smart_money_flows': {
                'description': 'Track institutional smart money flows across major funds to gauge market sentiment',
                'parameters': {
                    'family': {
                        'type': 'string',
                        'description': 'Fund family name or "all" (default: all)',
                        'required': False,
                        'default': 'all'
                    },
                    'period': {
                        'type': 'string',
                        'description': 'Analysis period (default: 3mo)',
                        'required': False,
                        'default': '3mo'
                    }
                },
                'handler': self._smart_money_flows
            },
            'fund_performance_comparison': {
                'description': 'Compare fund performance metrics including returns, volatility, Sharpe ratio, and drawdown',
                'parameters': {
                    'tickers': {
                        'type': 'array',
                        'description': 'List of fund ticker symbols',
                        'required': True
                    },
                    'period': {
                        'type': 'string',
                        'description': 'Time period (default: 1y)',
                        'required': False,
                        'default': '1y'
                    }
                },
                'handler': self._fund_performance_comparison
            },
            'nport_filings': {
                'description': 'Get SEC N-PORT filing history for a mutual fund',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Fund ticker symbol or CIK',
                        'required': True
                    },
                    'count': {
                        'type': 'integer',
                        'description': 'Number of filings to retrieve (default: 12)',
                        'required': False,
                        'default': 12
                    }
                },
                'handler': self._nport_filings
            },
            
            # SPAC Lifecycle Tracker (Phase 148)
            'spac_list': {
                'description': 'Get list of tracked SPACs with current status (searching, announced, completed)',
                'parameters': {
                    'status': {
                        'type': 'string',
                        'description': 'Optional filter by status: searching, announced, or completed',
                        'required': False
                    }
                },
                'handler': self._spac_list
            },
            'spac_trust_value': {
                'description': 'Calculate SPAC trust value per share and discount/premium to trust',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'SPAC ticker symbol',
                        'required': True
                    }
                },
                'handler': self._spac_trust_value
            },
            'spac_deal_timeline': {
                'description': 'Get SPAC deal timeline from IPO through merger completion',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'SPAC ticker symbol',
                        'required': True
                    }
                },
                'handler': self._spac_deal_timeline
            },
            'spac_redemption_risk': {
                'description': 'Estimate redemption rate risk based on price/trust ratio',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'SPAC ticker symbol',
                        'required': True
                    }
                },
                'handler': self._spac_redemption_risk
            },
            'spac_arbitrage_opportunities': {
                'description': 'Find SPACs trading below trust value (arbitrage opportunities)',
                'parameters': {},
                'handler': self._spac_arbitrage_opportunities
            },
            'spac_search': {
                'description': 'Search for SPACs by keyword (name, target, sector)',
                'parameters': {
                    'keyword': {
                        'type': 'string',
                        'description': 'Optional search keyword',
                        'required': False
                    }
                },
                'handler': self._spac_search
            },
            'secondary_recent': {
                'description': 'Get recent secondary offering filings (S-3, 424B)',
                'parameters': {
                    'days': {
                        'type': 'number',
                        'description': 'Number of days to look back (default: 7)',
                        'required': False
                    }
                },
                'handler': self._secondary_recent
            },
            'secondary_by_ticker': {
                'description': 'Get all secondary offering filings for a specific ticker',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    },
                    'days': {
                        'type': 'number',
                        'description': 'Days to look back (default: 30)',
                        'required': False
                    }
                },
                'handler': self._secondary_by_ticker
            },
            'secondary_shelf_status': {
                'description': 'Check if company has active shelf registration (S-3)',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    }
                },
                'handler': self._secondary_shelf_status
            },
            'secondary_price_impact': {
                'description': 'Analyze stock price impact of secondary offering',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol',
                        'required': True
                    }
                },
                'handler': self._secondary_price_impact
            },
            'secondary_upcoming': {
                'description': 'Find offerings that are filed but not yet priced',
                'parameters': {},
                'handler': self._secondary_upcoming
            },
            'secondary_search': {
                'description': 'Search secondary offerings by keyword',
                'parameters': {
                    'keyword': {
                        'type': 'string',
                        'description': 'Search keyword (optional)',
                        'required': False
                    },
                    'days': {
                        'type': 'number',
                        'description': 'Days to look back (default: 30)',
                        'required': False
                    }
                },
                'handler': self._secondary_search
            },
            'etf_flows': {
                'description': 'Calculate ETF flows from AUM and price changes',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'ETF ticker symbol',
                        'required': True
                    },
                    'days': {
                        'type': 'integer',
                        'description': 'Number of days to analyze (default: 30)',
                        'required': False,
                        'default': 30
                    }
                },
                'handler': self._etf_flows
            },
            'etf_flow_signals': {
                'description': 'Generate flow-based trading signals for ETFs',
                'parameters': {
                    'tickers': {
                        'type': 'array',
                        'description': 'List of ETF ticker symbols',
                        'required': True
                    }
                },
                'handler': self._etf_flow_signals
            },
            'etf_top_flows': {
                'description': 'Get top ETFs by flow magnitude',
                'parameters': {
                    'category': {
                        'type': 'string',
                        'description': 'ETF category: all, equity, bond, commodity, sector (default: all)',
                        'required': False,
                        'default': 'all'
                    },
                    'limit': {
                        'type': 'integer',
                        'description': 'Number of results to return (default: 20)',
                        'required': False,
                        'default': 20
                    }
                },
                'handler': self._etf_top_flows
            },
            'etf_sector_flows': {
                'description': 'Aggregate ETF flows by sector',
                'parameters': {},
                'handler': self._etf_sector_flows
            },
            
            # Global Equity Index Returns (Phase 153)
            'index_daily_returns': {
                'description': 'Get daily returns for global equity indices (S&P 500, FTSE, DAX, Nikkei, etc)',
                'parameters': {
                    'indices': {
                        'type': 'array',
                        'description': 'List of index names (optional, default: all)',
                        'required': False
                    },
                    'days': {
                        'type': 'integer',
                        'description': 'Number of days of history (default: 1)',
                        'required': False,
                        'default': 1
                    }
                },
                'handler': self._index_daily_returns
            },
            'index_performance': {
                'description': 'Get comprehensive performance metrics for global indices',
                'parameters': {
                    'indices': {
                        'type': 'array',
                        'description': 'List of index names (optional, default: all)',
                        'required': False
                    },
                    'period_days': {
                        'type': 'integer',
                        'description': 'Number of days for analysis (default: 365)',
                        'required': False,
                        'default': 365
                    }
                },
                'handler': self._index_performance
            },
            'index_regional_performance': {
                'description': 'Get aggregated performance by region (Americas, Europe, Asia-Pacific, Emerging)',
                'parameters': {
                    'region': {
                        'type': 'string',
                        'description': 'Specific region name (optional, default: all regions)',
                        'required': False
                    }
                },
                'handler': self._index_regional_performance
            },
            'index_correlation_matrix': {
                'description': 'Calculate correlation matrix between global indices',
                'parameters': {
                    'indices': {
                        'type': 'array',
                        'description': 'List of index names (optional, default: major indices)',
                        'required': False
                    },
                    'period': {
                        'type': 'string',
                        'description': 'Time period: 30d, 90d, or 1y (default: 90d)',
                        'required': False,
                        'default': '90d'
                    }
                },
                'handler': self._index_correlation_matrix
            },
            'index_compare': {
                'description': 'Compare multiple indices on a specific metric',
                'parameters': {
                    'indices': {
                        'type': 'array',
                        'description': 'List of index names to compare',
                        'required': True
                    },
                    'metric': {
                        'type': 'string',
                        'description': 'Metric to compare: ytd_return, volatility_30d, sharpe_ratio, max_drawdown (default: ytd_return)',
                        'required': False,
                        'default': 'ytd_return'
                    }
                },
                'handler': self._index_compare
            },
            'index_list_available': {
                'description': 'List all available global indices, optionally filtered by region',
                'parameters': {
                    'region': {
                        'type': 'string',
                        'description': 'Optional region filter (Americas, Europe, Asia-Pacific, Emerging Markets)',
                        'required': False
                    }
                },
                'handler': self._index_list_available
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
    
    # SPAC Lifecycle Tracker handlers (Phase 148)
    def _spac_list(self, status: Optional[str] = None) -> Dict:
        """Handler for spac_list tool"""
        tracker = SPACLifecycleTracker()
        spacs = tracker.get_spac_list(status=status)
        return {
            'success': True,
            'spacs': spacs,
            'count': len(spacs)
        }
    
    def _spac_trust_value(self, ticker: str) -> Dict:
        """Handler for spac_trust_value tool"""
        tracker = SPACLifecycleTracker()
        result = tracker.calculate_trust_value(ticker)
        if 'error' in result:
            return {
                'success': False,
                'error': result['error']
            }
        return {
            'success': True,
            'data': result
        }
    
    def _spac_deal_timeline(self, ticker: str) -> Dict:
        """Handler for spac_deal_timeline tool"""
        tracker = SPACLifecycleTracker()
        timeline = tracker.get_deal_timeline(ticker)
        if 'error' in timeline:
            return {
                'success': False,
                'error': timeline['error']
            }
        return {
            'success': True,
            'data': timeline
        }
    
    def _spac_redemption_risk(self, ticker: str) -> Dict:
        """Handler for spac_redemption_risk tool"""
        tracker = SPACLifecycleTracker()
        result = tracker.estimate_redemption_risk(ticker)
        if 'error' in result:
            return {
                'success': False,
                'error': result['error']
            }
        return {
            'success': True,
            'data': result
        }
    
    def _spac_arbitrage_opportunities(self) -> Dict:
        """Handler for spac_arbitrage_opportunities tool"""
        tracker = SPACLifecycleTracker()
        opportunities = tracker.find_arbitrage_opportunities()
        return {
            'success': True,
            'opportunities': opportunities,
            'count': len(opportunities)
        }
    
    def _spac_search(self, keyword: Optional[str] = None) -> Dict:
        """Handler for spac_search tool"""
        tracker = SPACLifecycleTracker()
        results = tracker.search_spacs(keyword=keyword)
        return {
            'success': True,
            'results': results,
            'count': len(results)
        }
    
    # Secondary Offering Handler Methods (Phase 149)
    def _secondary_recent(self, days: Optional[int] = 7) -> Dict:
        """Handler for secondary_recent tool"""
        monitor = SecondaryOfferingMonitor()
        filings = monitor.get_recent_filings(days=days if days else 7)
        return {
            'success': True,
            'filings': filings,
            'count': len(filings),
            'days': days if days else 7
        }
    
    def _secondary_by_ticker(self, ticker: str, days: Optional[int] = 30) -> Dict:
        """Handler for secondary_by_ticker tool"""
        monitor = SecondaryOfferingMonitor()
        filings = monitor.get_ticker_filings(ticker, days=days if days else 30)
        return {
            'success': True,
            'ticker': ticker,
            'filings': filings,
            'count': len(filings)
        }
    
    def _secondary_shelf_status(self, ticker: str) -> Dict:
        """Handler for secondary_shelf_status tool"""
        monitor = SecondaryOfferingMonitor()
        result = monitor.check_shelf_status(ticker)
        return {
            'success': True,
            **result
        }
    
    def _secondary_price_impact(self, ticker: str) -> Dict:
        """Handler for secondary_price_impact tool"""
        monitor = SecondaryOfferingMonitor()
        result = monitor.analyze_price_impact(ticker)
        if 'error' in result:
            return {
                'success': False,
                'error': result['error']
            }
        return {
            'success': True,
            **result
        }
    
    def _secondary_upcoming(self) -> Dict:
        """Handler for secondary_upcoming tool"""
        monitor = SecondaryOfferingMonitor()
        upcoming = monitor.get_upcoming_offerings()
        return {
            'success': True,
            'upcoming_offerings': upcoming,
            'count': len(upcoming)
        }
    
    def _secondary_search(self, keyword: Optional[str] = None, days: Optional[int] = 30) -> Dict:
        """Handler for secondary_search tool"""
        monitor = SecondaryOfferingMonitor()
        results = monitor.search_offerings(keyword=keyword, days=days if days else 30)
        return {
            'success': True,
            'results': results,
            'count': len(results),
            'keyword': keyword if keyword else 'all'
        }
    
    # ETF Flow Tracker Handler Methods (Phase 151)
    def _etf_flows(self, ticker: str, days: int = 30) -> Dict:
        """Handler for etf_flows tool"""
        try:
            flows = calculate_flows_from_aum(ticker.upper(), days=days)
            if not flows:
                return {
                    'success': False,
                    'error': f'No flow data available for {ticker}'
                }
            
            # Calculate summary metrics
            flow_1d = float(flows[-1].net_flow) if flows else 0
            flow_5d = float(sum(f.net_flow for f in flows[-5:]) / 5) if len(flows) >= 5 else 0
            flow_20d = float(sum(f.net_flow for f in flows[-20:]) / 20) if len(flows) >= 20 else 0
            
            return {
                'success': True,
                'ticker': ticker.upper(),
                'name': flows[-1].name if flows else ticker,
                'aum_millions': float(flows[-1].aum) if flows else 0,
                'flow_1d': flow_1d,
                'flow_5d': flow_5d,
                'flow_20d': flow_20d,
                'flows': [
                    {
                        'date': f.date,
                        'net_flow': float(f.net_flow),
                        'flow_as_pct_aum': float(f.flow_as_pct_aum),
                        'price': float(f.price),
                        'price_change_1d': float(f.price_change_1d),
                        'volume': int(f.volume),
                        'volume_avg_ratio': float(f.volume_avg_ratio)
                    }
                    for f in flows
                ]
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _etf_flow_signals(self, tickers: List[str]) -> Dict:
        """Handler for etf_flow_signals tool"""
        try:
            signals = generate_flow_signals(tickers)
            return {
                'success': True,
                'signals': [
                    {
                        'ticker': s.ticker,
                        'name': s.name,
                        'signal': s.signal,
                        'signal_strength': float(s.signal_strength),
                        'flow_score': float(s.flow_score),
                        'price_score': float(s.price_score),
                        'volume_score': float(s.volume_score),
                        'reason': s.reason,
                        'aum_millions': float(s.aum_millions),
                        'flow_1d': float(s.flow_1d),
                        'flow_5d': float(s.flow_5d),
                        'flow_20d': float(s.flow_20d)
                    }
                    for s in signals
                ],
                'count': len(signals)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _etf_top_flows(self, category: str = 'all', limit: int = 20) -> Dict:
        """Handler for etf_top_flows tool"""
        try:
            results = get_top_etf_flows(category=category, limit=limit)
            # Convert numpy types to Python native types
            for r in results:
                for k, v in r.items():
                    if hasattr(v, 'item'):  # numpy type
                        r[k] = float(v) if isinstance(v, (np.floating, float)) else int(v)
            return {
                'success': True,
                'category': category,
                'flows': results,
                'count': len(results)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _etf_sector_flows(self) -> Dict:
        """Handler for etf_sector_flows tool"""
        try:
            sector_etfs = {
                'Financials': ['XLF', 'VFH', 'KRE', 'KBE'],
                'Technology': ['XLK', 'VGT', 'QQQ', 'SMH'],
                'Healthcare': ['XLV', 'VHT', 'IBB', 'XBI'],
                'Energy': ['XLE', 'VDE', 'XOP', 'OIH'],
                'Industrials': ['XLI', 'VIS', 'IYT'],
                'Consumer Discretionary': ['XLY', 'VCR', 'RTH'],
                'Consumer Staples': ['XLP', 'VDC', 'KXI'],
                'Utilities': ['XLU', 'VPU', 'IDU'],
                'Real Estate': ['XLRE', 'VNQ', 'IYR'],
                'Communications': ['XLC', 'VOX', 'IYZ']
            }
            
            flows = get_sector_flows(sector_etfs, days=5)
            return {
                'success': True,
                'sector_flows': [
                    {
                        'sector': f.sector,
                        'date': f.date,
                        'net_flow_millions': float(f.net_flow_millions),
                        'num_etfs': int(f.num_etfs),
                        'avg_flow_pct_aum': float(f.avg_flow_pct_aum)
                    }
                    for f in flows
                ],
                'count': len(flows)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _index_daily_returns(self, indices: Optional[List[str]] = None, days: int = 1) -> Dict:
        """Handler for index_daily_returns tool"""
        result = get_index_daily_returns(indices=indices, days=days)
        if 'error' in result:
            return {'success': False, 'error': result['error']}
        return {'success': True, 'data': result}
    
    def _index_performance(self, indices: Optional[List[str]] = None, period_days: int = 365) -> Dict:
        """Handler for index_performance tool"""
        result = get_index_performance(indices=indices, period_days=period_days)
        if 'error' in result:
            return {'success': False, 'error': result['error']}
        return {'success': True, 'data': result}
    
    def _index_regional_performance(self, region: Optional[str] = None) -> Dict:
        """Handler for index_regional_performance tool"""
        result = get_regional_performance(region=region)
        if 'error' in result:
            return {'success': False, 'error': result['error']}
        return {'success': True, 'data': result}
    
    def _index_correlation_matrix(self, indices: Optional[List[str]] = None, period: str = '90d') -> Dict:
        """Handler for index_correlation_matrix tool"""
        result = calculate_correlation_matrix(indices=indices, period=period)
        if 'error' in result:
            return {'success': False, 'error': result['error']}
        return {'success': True, 'data': result}
    
    def _index_compare(self, indices: List[str], metric: str = 'ytd_return') -> Dict:
        """Handler for index_compare tool"""
        result = compare_indices(indices=indices, metric=metric)
        if 'error' in result:
            return {'success': False, 'error': result['error']}
        return {'success': True, 'data': result}
    
    def _index_list_available(self, region: Optional[str] = None) -> Dict:
        """Handler for index_list_available tool"""
        result = list_available_indices(region=region)
        if 'error' in result:
            return {'success': False, 'error': result['error']}
        return {'success': True, 'data': result}
    
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
    
    # Index Reconstitution Tracker Handler Methods (Phase 136)
    def _index_sp500_changes(self, days: int = 365) -> Dict:
        """Handler for index_sp500_changes tool"""
        from index_reconstitution_tracker import get_sp500_recent_changes
        return get_sp500_recent_changes(days)
    
    def _index_russell_calendar(self, year: Optional[int] = None) -> Dict:
        """Handler for index_russell_calendar tool"""
        from index_reconstitution_tracker import get_russell_reconstitution_calendar
        return get_russell_reconstitution_calendar(year)
    
    def _index_russell_candidates(self, index: str = '2000', limit: int = 20) -> Dict:
        """Handler for index_russell_candidates tool"""
        from index_reconstitution_tracker import predict_russell_candidates
        return predict_russell_candidates(index, limit)
    
    def _index_msci_schedule(self, year: Optional[int] = None) -> Dict:
        """Handler for index_msci_schedule tool"""
        from index_reconstitution_tracker import get_msci_schedule
        return get_msci_schedule(year)
    
    def _index_addition_opportunity(self, ticker: str, index_name: str = 'S&P 500') -> Dict:
        """Handler for index_addition_opportunity tool"""
        from index_reconstitution_tracker import analyze_index_addition_opportunity
        return analyze_index_addition_opportunity(ticker, index_name)
    
    def _index_reconstitution_stats(self) -> Dict:
        """Handler for index_reconstitution_stats tool"""
        from index_reconstitution_tracker import get_historical_reconstitution_stats
        return get_historical_reconstitution_stats()
    
    # SEC XBRL Financial Statements Handlers (Phase 134)
    def _sec_xbrl_financials(self, ticker: str, form_type: str = '10-K', 
                            fiscal_year: Optional[int] = None) -> Dict:
        """Handler for sec_xbrl_financials tool"""
        return get_financial_statements(ticker, form_type, fiscal_year)
    
    def _sec_xbrl_compare(self, ticker: str, years: List[int], form_type: str = '10-K') -> Dict:
        """Handler for sec_xbrl_compare tool"""
        return compare_financial_statements(ticker, years, form_type)
    
    def _sec_xbrl_search(self, search_term: str, limit: int = 10) -> Dict:
        """Handler for sec_xbrl_search tool"""
        results = search_xbrl_companies(search_term, limit)
        return {
            'success': True,
            'search_term': search_term,
            'results': results,
            'count': len(results)
        }
    
    def _sec_xbrl_cik(self, ticker: str) -> Dict:
        """Handler for sec_xbrl_cik tool"""
        cik = get_cik_from_ticker(ticker)
        if cik:
            return {
                'success': True,
                'ticker': ticker.upper(),
                'cik': cik
            }
        else:
            return {
                'success': False,
                'error': f'Ticker {ticker} not found in SEC database'
            }
    
    # DCF Valuation Engine handlers (Phase 142)
    def _dcf_valuation(self, ticker: str, projection_years: int = 5,
                      terminal_growth_rate: float = 0.025, tax_rate: float = 0.21) -> Dict:
        """Handler for dcf_valuation tool"""
        result = perform_dcf_valuation(
            ticker=ticker,
            projection_years=projection_years,
            terminal_growth_rate=terminal_growth_rate,
            tax_rate=tax_rate
        )
        if 'error' in result:
            return {
                'success': False,
                'error': result['error']
            }
        return {
            'success': True,
            'data': result
        }
    
    def _dcf_compare(self, tickers: List[str]) -> Dict:
        """Handler for dcf_compare tool"""
        result = compare_valuations(tickers)
        if 'error' in result:
            return {
                'success': False,
                'error': result['error']
            }
        return {
            'success': True,
            'data': result
        }
    
    def _dcf_sensitivity(self, ticker: str) -> Dict:
        """Handler for dcf_sensitivity tool"""
        result = perform_dcf_valuation(ticker)
        if 'error' in result:
            return {
                'success': False,
                'error': result['error']
            }
        return {
            'success': True,
            'data': result.get('sensitivity_analysis', {})
        }
    
    # Comparable Company Analysis handlers (Phase 141)
    def _comps_company_metrics(self, ticker: str) -> Dict:
        """Handler for comps_company_metrics tool"""
        result = get_company_metrics(ticker)
        if result:
            return {
                'success': True,
                'data': result
            }
        else:
            return {
                'success': False,
                'error': f'No metrics available for {ticker}'
            }
    
    def _comps_generate_table(self, tickers: List[str]) -> Dict:
        """Handler for comps_generate_table tool"""
        result = generate_comps_table(tickers)
        if 'error' in result:
            return {
                'success': False,
                'error': result['error']
            }
        return {
            'success': True,
            'data': result
        }
    
    def _comps_compare_to_peers(self, ticker: str, peer_group: Optional[List[str]] = None) -> Dict:
        """Handler for comps_compare_to_peers tool"""
        result = compare_to_peers(ticker, peer_group)
        if 'error' in result:
            return {
                'success': False,
                'error': result['error']
            }
        return {
            'success': True,
            'data': result
        }
    
    def _comps_sector_analysis(self, sector_name: str, min_market_cap: Optional[float] = None) -> Dict:
        """Handler for comps_sector_analysis tool"""
        result = sector_analysis(sector_name, min_market_cap)
        if 'error' in result:
            return {
                'success': False,
                'error': result['error']
            }
        return {
            'success': True,
            'data': result
        }
    
    def _comps_peer_groups(self) -> Dict:
        """Handler for comps_peer_groups tool"""
        return {
            'success': True,
            'peer_groups': PEER_GROUPS
        }
    
    # Dividend History & Projections Handlers (Phase 139)
    def _dividend_history(self, ticker: str, years: int = 10) -> Dict:
        """Handler for dividend_history tool"""
        return get_dividend_history(ticker, years)
    
    def _dividend_growth_rates(self, ticker: str) -> Dict:
        """Handler for dividend_growth_rates tool"""
        return calculate_growth_rates(ticker)
    
    def _dividend_calendar(self, ticker: str, months_ahead: int = 12) -> Dict:
        """Handler for dividend_calendar tool"""
        return get_ex_dividend_calendar(ticker, months_ahead)
    
    def _dividend_projections(self, ticker: str, years: int = 5, 
                             growth_rate: Optional[float] = None) -> Dict:
        """Handler for dividend_projections tool"""
        return project_dividends(ticker, years, growth_rate)
    
    def _dividend_aristocrat(self, ticker: str) -> Dict:
        """Handler for dividend_aristocrat_check tool"""
        return check_aristocrat_status(ticker)
    
    def _dividend_compare(self, tickers: List[str]) -> Dict:
        """Handler for dividend_compare tool"""
        return compare_dividend_growth(tickers)
    
    # Earnings Surprise History handlers (Phase 144)
    def _earnings_surprise_history(self, ticker: str, quarters: int = 12) -> Dict:
        """Handler for earnings_surprise_history tool"""
        return get_earnings_history(ticker, quarters)
    
    def _earnings_surprise_patterns(self, ticker: str) -> Dict:
        """Handler for earnings_surprise_patterns tool"""
        return analyze_surprise_patterns(ticker)
    
    def _earnings_whisper_numbers(self, ticker: str, quarters: int = 8) -> Dict:
        """Handler for earnings_whisper_numbers tool"""
        return estimate_whisper_numbers(ticker, quarters)
    
    def _earnings_post_drift(self, ticker: str, quarters: int = 12) -> Dict:
        """Handler for earnings_post_drift tool"""
        return analyze_post_earnings_drift(ticker, quarters)
    
    def _earnings_quality_score(self, ticker: str) -> Dict:
        """Handler for earnings_quality_score tool"""
        return calculate_earnings_quality(ticker)
    
    def _earnings_compare_surprises(self, tickers: List[str]) -> Dict:
        """Handler for earnings_compare_surprises tool"""
        return compare_surprise_history(tickers)
    
    # Stock Split & Corporate Events handlers (Phase 146)
    def _stock_split_history(self, ticker: str, years: int = 20) -> Dict:
        """Handler for stock_split_history tool"""
        return get_stock_splits(ticker, years)
    
    def _stock_split_impact(self, ticker: str, split_date: Optional[str] = None) -> Dict:
        """Handler for stock_split_impact tool"""
        return analyze_split_impact(ticker, split_date)
    
    def _stock_corporate_actions(self, ticker: str, years: int = 5) -> Dict:
        """Handler for stock_corporate_actions tool"""
        return get_corporate_actions(ticker, years)
    
    def _stock_compare_splits(self, tickers: List[str], lookback_days: int = 365) -> Dict:
        """Handler for stock_compare_splits tool"""
        return compare_split_performance(tickers, lookback_days)
    
    # Equity Screener handlers (Phase 140)
    def _screen_stocks(self, filters: Dict, min_market_cap: Optional[float] = None, 
                      sectors: Optional[List[str]] = None, limit: int = 50) -> Dict:
        """Handler for screen_stocks tool"""
        try:
            # Convert filter format from dict to tuples
            filter_tuples = {k: tuple(v) if isinstance(v, list) else v for k, v in filters.items()}
            
            screener = EquityScreener()
            results = screener.screen(filter_tuples, min_market_cap=min_market_cap, 
                                     sectors=sectors, limit=limit)
            
            return {
                'success': True,
                'filters': filters,
                'count': len(results),
                'results': results
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _screen_preset(self, preset_name: str, limit: int = 50) -> Dict:
        """Handler for screen_preset tool"""
        try:
            screener = EquityScreener()
            results = screener.screen_preset(preset_name, limit=limit)
            
            preset_info = SCREENING_PRESETS.get(preset_name, {})
            
            return {
                'success': True,
                'preset': preset_name,
                'description': preset_info.get('name', ''),
                'filters': preset_info.get('filters', {}),
                'count': len(results),
                'results': results
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _rank_stocks(self, tickers: Optional[List[str]] = None, 
                    factors: Optional[List[str]] = None,
                    weights: Optional[Dict[str, float]] = None,
                    limit: int = 50) -> Dict:
        """Handler for rank_stocks tool"""
        try:
            screener = EquityScreener()
            ranked = screener.rank_stocks(tickers=tickers, factors=factors, weights=weights)
            
            # Convert to list of dicts
            results = ranked.head(limit).to_dict(orient='records')
            
            return {
                'success': True,
                'count': len(results),
                'factors_used': factors or ['pe', 'pb', 'roe', 'return_3m', 'return_6m'],
                'results': results
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _screen_factors(self) -> Dict:
        """Handler for screen_factors tool"""
        return {
            'success': True,
            'categories': FACTOR_CATEGORIES,
            'total_factors': sum(len(v) for v in FACTOR_CATEGORIES.values())
        }
    
    def _screen_presets_list(self) -> Dict:
        """Handler for screen_presets_list tool"""
        return {
            'success': True,
            'presets': {k: {'name': v['name'], 'filters': v['filters']} 
                       for k, v in SCREENING_PRESETS.items()}
        }
    
    # Relative Valuation Matrix handlers (Phase 143)
    def _valuation_heatmap(self, format: str = 'json') -> Dict:
        """Handler for valuation_heatmap tool"""
        try:
            data = get_cross_sector_comparison()
            return {
                'success': True,
                'data': data
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _valuation_sector(self, sector: str) -> Dict:
        """Handler for valuation_sector tool"""
        try:
            data = get_sector_valuation(sector)
            if 'error' in data:
                return {
                    'success': False,
                    'error': data['error']
                }
            return {
                'success': True,
                'data': data
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _valuation_stock(self, ticker: str) -> Dict:
        """Handler for valuation_stock tool"""
        try:
            data = get_valuation_metrics(ticker)
            if 'error' in data:
                return {
                    'success': False,
                    'error': data['error']
                }
            return {
                'success': True,
                'data': data
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _valuation_peers(self, tickers: List[str]) -> Dict:
        """Handler for valuation_peers tool"""
        try:
            data = get_peer_comparison(tickers)
            if 'error' in data:
                return {
                    'success': False,
                    'error': data['error']
                }
            return {
                'success': True,
                'data': data
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _valuation_screen(self, metric: str, threshold: float, 
                         comparison: str = 'below', limit: int = 20) -> Dict:
        """Handler for valuation_screen tool"""
        try:
            results = screen_by_valuation(metric, threshold, comparison)
            return {
                'success': True,
                'results': results[:limit],
                'count': len(results[:limit])
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _valuation_sectors_list(self) -> Dict:
        """Handler for valuation_sectors_list tool"""
        return {
            'success': True,
            'sectors': list(SECTOR_TICKERS.keys()),
            'count': len(SECTOR_TICKERS)
        }
    
    # ADR/GDR Arbitrage Monitor Handler Methods (Phase 147)
    def _adr_spread(self, adr_ticker: str) -> Dict:
        """Handler for adr_spread tool"""
        try:
            data = calculate_arbitrage_spread(adr_ticker.upper(), verbose=False)
            if data is None:
                return {
                    'success': False,
                    'error': f'Failed to calculate spread for {adr_ticker}'
                }
            return {
                'success': True,
                'data': data
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _adr_scan(self, min_spread_bps: float = 50.0, sort_by: str = 'spread') -> Dict:
        """Handler for adr_scan tool"""
        try:
            results = scan_all_adrs(min_spread_bps, sort_by)
            return {
                'success': True,
                'opportunities': results,
                'count': len(results),
                'min_spread_bps': min_spread_bps,
                'sorted_by': sort_by
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _adr_compare(self, tickers: List[str]) -> Dict:
        """Handler for adr_compare tool"""
        try:
            data = compare_adrs([t.upper() for t in tickers])
            if 'error' in data:
                return {
                    'success': False,
                    'error': data['error']
                }
            return {
                'success': True,
                'data': data
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _adr_list(self, currency: Optional[str] = None) -> Dict:
        """Handler for adr_list tool"""
        try:
            pairs = get_adr_list()
            if currency:
                pairs = [p for p in pairs if p['currency'] == currency.upper()]
            return {
                'success': True,
                'pairs': pairs,
                'count': len(pairs),
                'total_pairs': len(ADR_PAIRS)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # Stock Loan & Borrow Costs Handler Methods (Phase 150)
    def _stock_borrow_analysis(self, ticker: str) -> Dict:
        """Handler for stock_borrow_analysis tool"""
        try:
            data = get_borrow_cost_analysis(ticker.upper())
            if 'error' in data:
                return {
                    'success': False,
                    'error': data['error']
                }
            return {
                'success': True,
                'data': data
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _threshold_securities_list(self, exchange: str = 'all') -> Dict:
        """Handler for threshold_securities_list tool"""
        try:
            securities = get_threshold_securities(exchange)
            return {
                'success': True,
                'securities': securities,
                'count': len(securities),
                'exchange': exchange
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _htb_scan(self, tickers: List[str]) -> Dict:
        """Handler for htb_scan tool"""
        try:
            tickers_upper = [t.upper() for t in tickers]
            results = scan_hard_to_borrow_stocks(tickers_upper)
            return {
                'success': True,
                'results': results,
                'count': len(results),
                'tickers_scanned': len(tickers_upper)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _borrow_cost_compare(self, tickers: List[str]) -> Dict:
        """Handler for borrow_cost_compare tool"""
        try:
            tickers_upper = [t.upper() for t in tickers]
            data = compare_borrow_costs(tickers_upper)
            return {
                'success': True,
                'data': data
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # Analyst Target Price Tracker Handler Methods (Phase 145)
    def _analyst_consensus_targets(self, ticker: str) -> Dict:
        """Handler for analyst_consensus_targets tool"""
        return get_consensus_targets(ticker.upper())
    
    def _analyst_recommendations(self, ticker: str) -> Dict:
        """Handler for analyst_recommendations tool"""
        return get_recommendation_distribution(ticker.upper())
    
    def _analyst_revision_velocity(self, ticker: str, days: int = 90) -> Dict:
        """Handler for analyst_revision_velocity tool"""
        return get_revision_velocity(ticker.upper(), days=days)
    
    def _analyst_target_summary(self, ticker: str) -> Dict:
        """Handler for analyst_target_summary tool"""
        return get_target_summary(ticker.upper())
    
    def _analyst_compare_targets(self, tickers: List[str]) -> Dict:
        """Handler for analyst_compare_targets tool"""
        tickers_upper = [t.upper() for t in tickers]
        return compare_targets(tickers_upper)
    
    # Mutual Fund Flow Analysis handlers (Phase 152)
    def _fund_flows(self, ticker: str, period: str = '1y') -> Dict:
        """Handler for fund_flows tool"""
        try:
            result = get_fund_flows_yahoo(ticker.upper(), period)
            if 'error' in result:
                return {
                    'success': False,
                    'error': result['error']
                }
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _compare_fund_flows(self, tickers: List[str], period: str = '1y') -> Dict:
        """Handler for compare_fund_flows tool"""
        try:
            tickers_upper = [t.upper() for t in tickers]
            result = compare_fund_flows(tickers_upper, period)
            if 'error' in result:
                return {
                    'success': False,
                    'error': result['error']
                }
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _fund_sector_rotation(self, ticker: str) -> Dict:
        """Handler for fund_sector_rotation tool"""
        try:
            result = analyze_sector_rotation(ticker.upper())
            if 'error' in result:
                return {
                    'success': False,
                    'error': result['error']
                }
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _smart_money_flows(self, family: str = 'all', period: str = '3mo') -> Dict:
        """Handler for smart_money_flows tool"""
        try:
            result = get_smart_money_flows(family, period)
            if 'error' in result:
                return {
                    'success': False,
                    'error': result['error']
                }
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _fund_performance_comparison(self, tickers: List[str], period: str = '1y') -> Dict:
        """Handler for fund_performance_comparison tool"""
        try:
            tickers_upper = [t.upper() for t in tickers]
            result = get_fund_performance_comparison(tickers_upper, period)
            if 'error' in result:
                return {
                    'success': False,
                    'error': result['error']
                }
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _nport_filings(self, ticker: str, count: int = 12) -> Dict:
        """Handler for nport_filings tool"""
        try:
            cik = search_fund_cik(ticker)
            if not cik:
                return {
                    'success': False,
                    'error': f'Could not find CIK for {ticker}'
                }
            result = get_recent_nport_filings(cik, count)
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
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
