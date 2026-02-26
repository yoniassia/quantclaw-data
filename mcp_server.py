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

from bank_of_israel_dashboard import (
    get_dashboard as boi_get_dashboard,
    get_policy_rate as boi_get_policy_rate,
    get_fx_reserves as boi_get_fx_reserves,
    get_exchange_rates as boi_get_exchange_rates,
    get_inflation_data as boi_get_inflation_data,
    get_monetary_policy_history as boi_get_policy_history
)

from tase import (
    fetch_ta35_index,
    fetch_israeli_stock,
    get_market_summary as tase_get_market_summary,
    fetch_sector_performance as tase_fetch_sector_performance,
    fetch_historical_ta35
)

import china_nbs

from em_sovereign_spreads import (
    get_embi_global,
    get_regional_spreads,
    get_credit_quality_spreads,
    get_spread_history,
    get_comprehensive_em_report
)

from em_currency_crisis import (
    get_fx_reserves,
    get_current_account,
    get_reer,
    calculate_crisis_risk_score,
    get_regional_crisis_overview
)

from central_bank_rates import (
    get_central_bank_rate,
    get_all_central_bank_rates,
    compare_central_banks,
    get_global_rate_heatmap,
    search_central_banks,
    get_rate_differential,
    list_all_banks
)

from fx_carry_trade import (
    get_carry_trade_opportunities,
    get_rate_differential as fx_get_rate_differential,
    get_fx_carry_dashboard,
    get_top_funding_currencies,
    get_top_investment_currencies
)

from industrial_metals import (
    get_copper_price,
    get_aluminum_price,
    get_zinc_price,
    get_nickel_price,
    get_metal_inventories,
    get_metals_snapshot,
    get_metals_correlation
)

from crude_oil_fundamentals import (
    get_eia_crude_stocks,
    get_eia_cushing_stocks,
    get_eia_spr_levels,
    get_eia_production,
    get_eia_trade_flows,
    get_eia_refinery_operations,
    scrape_opec_momr_production,
    get_opec_spare_capacity,
    compare_us_vs_opec,
    get_crude_oil_fundamentals_dashboard,
    get_weekly_oil_report
)

from rare_earths import (
    get_mineral_profile,
    get_all_critical_minerals,
    calculate_supply_risk_score,
    get_supply_risk_rankings,
    get_sector_exposure,
    get_country_production_profile,
    get_rare_earths_detailed,
    get_comprehensive_minerals_report,
    CRITICAL_MINERALS,
    STRATEGIC_CATEGORIES,
    PRODUCTION_DATA
)

from patent_tracking import (
    search_patents_by_company,
    compare_companies as patent_compare_companies,
    patent_trend_analysis,
    get_industry_leaders
)

from semiconductor_chip import (
    get_chip_sales,
    get_chip_forecast,
    get_fab_utilization,
    get_chip_market_summary
)

from natural_gas_supply_demand import (
    get_weekly_storage_report,
    get_production_data,
    get_demand_data,
    get_supply_demand_balance,
    fetch_eia_series
)

from lng_gas import (
    get_lng_prices as lng_get_lng_prices,
    get_lng_price_summary as lng_get_lng_price_summary,
    get_lng_trade_flows as lng_get_lng_trade_flows,
    get_lng_exporters as lng_get_lng_exporters,
    get_lng_importers as lng_get_lng_importers,
    get_lng_terminals as lng_get_lng_terminals,
    get_terminal_by_name as lng_get_terminal_by_name,
    get_lng_market_summary as lng_get_lng_market_summary
)

from carbon_credits import (
    get_eu_ets_price_history,
    get_global_carbon_prices,
    get_carbon_market_statistics,
    get_emissions_by_sector,
    compare_carbon_markets,
    get_carbon_offset_projects
)

from container_port_throughput import (
    get_port_throughput,
    compare_ports as port_compare_ports,
    get_port_list,
    get_global_port_rankings
)

from nft_market import (
    get_collection_stats,
    get_top_collections,
    detect_wash_trading,
    get_nft_market_overview,
    compare_collections,
    get_collection_history
)

from fx_volatility_surface import (
    get_volatility_surface,
    get_risk_reversals,
    get_butterflies,
    get_all_pairs_summary
)

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

from global_fx_rates import (
    get_fx_rate,
    get_all_rates,
    get_cross_rate,
    get_fx_matrix,
    convert_currency,
    get_strongest_weakest,
    list_supported_currencies
)

from stablecoin_supply import (
    get_all_stablecoins,
    get_stablecoin_detail,
    get_chain_stablecoins,
    analyze_mint_burn_events,
    get_stablecoin_dominance
)

from global_electricity_demand import (
    get_entsoe_load,
    get_entsoe_forecast,
    get_europe_aggregate_load,
    get_eia_demand,
    get_us_generation_mix,
    get_caiso_load,
    get_caiso_renewables,
    get_global_demand_dashboard,
    compare_regional_demand
)

from global_tourism_statistics import (
    get_international_arrivals,
    get_tourism_receipts,
    get_country_tourism_profile,
    get_global_tourism_overview,
    compare_tourism_countries,
    get_us_hotel_occupancy,
    get_airline_passenger_data,
    get_tourism_recovery_tracker
)

from bankruptcy_tracker import (
    search_bankruptcy_filings,
    get_company_bankruptcy_status,
    get_bankruptcy_statistics
)

from pe_vc_deals import (
    get_vc_deals,
    get_pe_deals,
    search_form_d_filings,
    get_deal_flow_summary
)

from health_impact import (
    get_health_outbreaks,
    get_pandemic_impact,
    get_health_monitor
)

from academic_papers import (
    get_latest_papers,
    search_papers,
    get_trending_papers,
    search_by_author,
    generate_report
)

from corporate_bond_spreads import (
    get_ig_spreads,
    get_hy_spreads,
    get_sector_spreads,
    compare_ig_vs_hy,
    get_spreads_by_maturity,
    get_credit_risk_dashboard,
    analyze_spread_trends
)

from clo_abs import (
    get_clo_market_overview,
    get_abs_spreads_by_asset_class,
    get_cmbs_market_metrics,
    get_structured_finance_issuance,
    get_delinquency_rates,
    get_abs_liquidity_indicators,
    get_comprehensive_clo_abs_dashboard,
    analyze_abs_credit_quality,
    get_sec_nport_clo_abs_holdings
)

from muni_bonds import (
    search_muni_bonds,
    get_recent_trades,
    get_issuer_profile,
    get_credit_events,
    get_state_summary,
    get_yield_curve,
    compare_spreads
)

from mmf_flows import (
    get_mmf_aggregate_flows,
    get_sec_mmf_filings,
    parse_nmfp_filing,
    get_mmf_yields,
    get_mmf_concentration_risk,
    compare_mmf_categories
)

from repo_rate_monitor import (
    get_sofr_rates,
    get_repo_rates,
    get_reverse_repo_operations,
    get_overnight_rates_dashboard,
    compare_money_market_rates,
    get_funding_stress_indicators
)

from treasury_curve import (
    get_current_curve,
    get_historical_curve,
    analyze_curve_shape,
    compare_curves,
    get_specific_maturity
)

from tips_breakeven import (
    get_current_tips_data,
    analyze_breakeven_curve,
    get_real_yield_history,
    compare_tips_vs_nominal,
    get_inflation_expectations_summary,
    track_breakeven_changes
)

from inflation_linked_bonds import (
    get_global_linker_summary,
    get_us_tips_yields,
    get_euro_linker_yields,
    get_uk_gilt_yields,
    compare_linker_yields,
    get_linker_history,
    analyze_real_yield_trends
)

from commercial_paper import (
    get_current_rates,
    get_rate_history,
    analyze_spreads,
    get_rate_comparison,
    get_cp_dashboard
)

from bond_new_issue import (
    get_upcoming_issues,
    get_issuer_history,
    get_company_filings,
    analyze_filing_content,
    get_bond_dashboard
)

from gold_precious_metals import (
    get_yahoo_quote,
    get_all_metals_prices,
    get_all_etf_holdings,
    calculate_gold_silver_ratio,
    get_metals_performance,
    get_world_gold_council_summary,
    get_comprehensive_metals_report
)

from agricultural_commodities import (
    get_yahoo_futures_price,
    get_usda_crop_data,
    get_grain_futures,
    get_soft_commodities,
    get_commodity_dashboard,
    get_all_futures,
    list_commodities,
    FUTURES_SYMBOLS,
    USDA_COMMODITIES
)

from livestock_meat import (
    get_cattle_prices,
    get_hog_prices,
    get_all_livestock_futures,
    get_slaughter_data,
    get_livestock_dashboard,
    get_ams_report,
    list_ams_reports,
    LIVESTOCK_FUTURES,
    AMS_REPORTS
)

from opec import (
    get_opec_production_latest,
    get_opec_summary,
    get_country_production,
    get_compliance_report,
    get_quota_changes
)
from cftc_cot import (
    get_latest_cot_report,
    get_cot_by_contract,
    get_cot_extremes,
    get_cot_summary,
    get_commercial_vs_spec_divergence,
    get_cot_dashboard
)

from crypto_derivatives import (
    get_funding_rates,
    get_futures_basis,
    get_open_interest,
    scan_funding_arbitrage,
    get_market_snapshot
)

from cross_chain_bridge_monitor import (
    get_all_bridges,
    get_bridge_details,
    get_bridge_volume,
    calculate_bridge_risk_score,
    get_top_bridges,
    get_flow_analysis,
    get_comprehensive_bridge_report
)

from defi_tvl_yield import (
    get_global_tvl,
    get_protocol_tvl,
    get_all_protocols,
    get_chain_tvl,
    get_chains_tvl,
    get_yield_pools,
    get_stablecoin_yields,
    get_protocol_yields,
    get_tvl_rankings,
    get_defi_dashboard
)

from airport_traffic_aviation import (
    get_airport_operations,
    get_airline_capacity_index,
    get_flight_delay_index,
    compare_regional_traffic,
    get_aviation_economic_dashboard,
    list_airports
)

from auto_sales_ev import (
    get_us_auto_sales,
    get_ev_registrations,
    get_auto_market_share,
    get_comprehensive_auto_report
)

from shanghai_stock_exchange import (
    get_sse_index,
    get_margin_trading,
    get_northbound_flow
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
            
            # EM Sovereign Spread Monitor Tools (Phase 158)
            'em_embi_global': {
                'description': 'Get JPMorgan EMBI Global Diversified spread - main benchmark for emerging market sovereign debt',
                'parameters': {},
                'handler': self._em_embi_global
            },
            'em_regional_spreads': {
                'description': 'Get regional EMBI spreads for Latin America, Asia, Europe, and Middle East/Africa',
                'parameters': {},
                'handler': self._em_regional_spreads
            },
            'em_credit_quality': {
                'description': 'Compare high yield vs investment grade emerging market spreads',
                'parameters': {},
                'handler': self._em_credit_quality
            },
            'em_spread_history': {
                'description': 'Get historical spread data for charting and trend analysis',
                'parameters': {
                    'series_id': {
                        'type': 'string',
                        'description': 'FRED series ID (default: BAMLEMRECRPIUSEYGEY for EMBI Global)',
                        'required': False,
                        'default': 'BAMLEMRECRPIUSEYGEY'
                    },
                    'days': {
                        'type': 'integer',
                        'description': 'Number of days of history to fetch (default: 365)',
                        'required': False,
                        'default': 365
                    }
                },
                'handler': self._em_spread_history
            },
            'em_comprehensive_report': {
                'description': 'Get comprehensive emerging market sovereign spread analysis including global, regional, and credit quality metrics',
                'parameters': {},
                'handler': self._em_comprehensive_report
            },
            
            # EM Currency Crisis Monitor Tools (Phase 184)
            'em_fx_reserves': {
                'description': 'Get FX reserves data and risk analysis for an emerging market country',
                'parameters': {
                    'country': {
                        'type': 'string',
                        'description': 'Country name (Brazil, Mexico, Argentina, China, India, Indonesia, Thailand, Philippines, Malaysia, Russia, Turkey, South Africa, Poland)',
                        'required': True
                    }
                },
                'handler': self._em_fx_reserves
            },
            'em_current_account': {
                'description': 'Get current account balance data and risk analysis for an EM country',
                'parameters': {
                    'country': {
                        'type': 'string',
                        'description': 'Country name',
                        'required': True
                    }
                },
                'handler': self._em_current_account
            },
            'em_reer': {
                'description': 'Get real effective exchange rate (REER) and currency valuation analysis',
                'parameters': {
                    'country': {
                        'type': 'string',
                        'description': 'Country name',
                        'required': True
                    }
                },
                'handler': self._em_reer
            },
            'em_crisis_risk': {
                'description': 'Calculate comprehensive currency crisis risk score combining FX reserves, current account, and REER analysis',
                'parameters': {
                    'country': {
                        'type': 'string',
                        'description': 'Country name',
                        'required': True
                    }
                },
                'handler': self._em_crisis_risk
            },
            'em_regional_crisis_overview': {
                'description': 'Get currency crisis risk overview for a region or all EM countries, sorted by risk level',
                'parameters': {
                    'region': {
                        'type': 'string',
                        'description': 'Region code: all, latam, asia, emea (default: all)',
                        'required': False,
                        'default': 'all'
                    }
                },
                'handler': self._em_regional_crisis_overview
            },
            
            # Crypto Exchange Flow Monitor Tools (Phase 185)
            'crypto_exchange_flows': {
                'description': 'Get exchange inflows/outflows for top crypto exchanges with volume analysis and market concentration',
                'parameters': {
                    'limit': {
                        'type': 'integer',
                        'description': 'Number of exchanges to analyze (default: 10)',
                        'required': False,
                        'default': 10
                    }
                },
                'handler': self._crypto_exchange_flows
            },
            'crypto_exchange_netflow': {
                'description': 'Calculate net flow for a specific crypto exchange with trend analysis',
                'parameters': {
                    'exchange_id': {
                        'type': 'string',
                        'description': 'CoinGecko exchange ID (e.g., binance, coinbase_exchange, kraken)',
                        'required': True
                    },
                    'days': {
                        'type': 'integer',
                        'description': 'Number of days to analyze (default: 7)',
                        'required': False,
                        'default': 7
                    }
                },
                'handler': self._crypto_exchange_netflow
            },
            'crypto_whale_movements': {
                'description': 'Track large crypto movements and whale activity via volume analysis',
                'parameters': {
                    'min_value_usd': {
                        'type': 'number',
                        'description': 'Minimum transaction value in USD to track (default: 1000000)',
                        'required': False,
                        'default': 1000000
                    }
                },
                'handler': self._crypto_whale_movements
            },
            'crypto_exchange_tvl': {
                'description': 'Get Total Value Locked (TVL) rankings for crypto exchanges via DeFi Llama',
                'parameters': {},
                'handler': self._crypto_exchange_tvl
            },
            'crypto_exchange_dominance': {
                'description': 'Analyze crypto exchange market share and dominance with concentration metrics (HHI index)',
                'parameters': {},
                'handler': self._crypto_exchange_dominance
            },
            
            # DeFi TVL & Yield Aggregator Tools (Phase 186)
            'defi_global_tvl': {
                'description': 'Get current global DeFi TVL across all protocols and chains',
                'parameters': {},
                'handler': self._defi_global_tvl
            },
            'defi_protocol_tvl': {
                'description': 'Get TVL data for a specific DeFi protocol',
                'parameters': {
                    'protocol': {
                        'type': 'string',
                        'description': 'Protocol slug (e.g., aave, uniswap, compound, curve)',
                        'required': True
                    }
                },
                'handler': self._defi_protocol_tvl
            },
            'defi_all_protocols': {
                'description': 'Get list of all DeFi protocols with their current TVL sorted by TVL',
                'parameters': {},
                'handler': self._defi_all_protocols
            },
            'defi_chain_tvl': {
                'description': 'Get TVL for a specific blockchain',
                'parameters': {
                    'chain': {
                        'type': 'string',
                        'description': 'Chain name (e.g., Ethereum, BSC, Polygon, Arbitrum, Avalanche)',
                        'required': True
                    }
                },
                'handler': self._defi_chain_tvl
            },
            'defi_chains_tvl': {
                'description': 'Get TVL breakdown across all major chains',
                'parameters': {},
                'handler': self._defi_chains_tvl
            },
            'defi_yield_pools': {
                'description': 'Get yield farming opportunities across DeFi protocols',
                'parameters': {
                    'chain': {
                        'type': 'string',
                        'description': 'Optional chain filter (e.g., Ethereum, BSC)',
                        'required': False
                    },
                    'min_tvl': {
                        'type': 'number',
                        'description': 'Minimum pool TVL in USD (default: 1000000)',
                        'required': False,
                        'default': 1000000
                    }
                },
                'handler': self._defi_yield_pools
            },
            'defi_stablecoin_yields': {
                'description': 'Get stablecoin yield opportunities (low risk)',
                'parameters': {
                    'min_apy': {
                        'type': 'number',
                        'description': 'Minimum APY threshold (default: 0)',
                        'required': False,
                        'default': 0
                    }
                },
                'handler': self._defi_stablecoin_yields
            },
            'defi_protocol_yields': {
                'description': 'Get all yield pools for a specific protocol',
                'parameters': {
                    'protocol': {
                        'type': 'string',
                        'description': 'Protocol name (e.g., aave, compound, curve)',
                        'required': True
                    }
                },
                'handler': self._defi_protocol_yields
            },
            'defi_tvl_rankings': {
                'description': 'Get protocol TVL rankings with optional category filter',
                'parameters': {
                    'category': {
                        'type': 'string',
                        'description': 'Optional category filter (e.g., Lending, DEX, Yield)',
                        'required': False
                    },
                    'top_n': {
                        'type': 'integer',
                        'description': 'Number of top protocols to return (default: 25)',
                        'required': False,
                        'default': 25
                    }
                },
                'handler': self._defi_tvl_rankings
            },
            'defi_dashboard': {
                'description': 'Get comprehensive DeFi dashboard with TVL and top yields',
                'parameters': {},
                'handler': self._defi_dashboard
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
            
            # Bank of Israel Dashboard Tools (Phase 629)
            'boi_dashboard': {
                'description': 'Comprehensive Bank of Israel dashboard with policy rate, FX reserves, exchange rates, inflation, and unemployment',
                'parameters': {},
                'handler': self._boi_dashboard
            },
            'boi_policy_rate': {
                'description': 'Get current Bank of Israel policy interest rate',
                'parameters': {},
                'handler': self._boi_policy_rate
            },
            'boi_fx_reserves': {
                'description': 'Get Israel foreign exchange reserves in USD (billions)',
                'parameters': {},
                'handler': self._boi_fx_reserves
            },
            'boi_exchange_rates': {
                'description': 'Get ILS exchange rates vs USD and EUR',
                'parameters': {},
                'handler': self._boi_exchange_rates
            },
            'boi_inflation': {
                'description': 'Get Israel CPI index, year-over-year inflation rate, and inflation target',
                'parameters': {},
                'handler': self._boi_inflation
            },
            'boi_policy_history': {
                'description': 'Get historical Bank of Israel policy rate decisions',
                'parameters': {
                    'months': {
                        'type': 'integer',
                        'description': 'Number of months of history (default 24)',
                        'required': False,
                        'default': 24
                    }
                },
                'handler': self._boi_policy_history
            },
            
            # Tel Aviv Stock Exchange (TASE) Tools (Phase 631)
            'tase_ta35_index': {
                'description': 'Get TA-35 index (Tel Aviv 35 leading stocks) - price, change, volume, 52-week range',
                'parameters': {
                    'period': {
                        'type': 'string',
                        'description': 'Data period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max (default 1d)',
                        'required': False,
                        'default': '1d'
                    }
                },
                'handler': self._tase_ta35_index
            },
            'tase_stock': {
                'description': 'Get Israeli stock data - TEVA, NICE, CHKP, CYBR, WIX, MNDY, etc. Dual-listed (US+TASE) and local stocks',
                'parameters': {
                    'symbol': {
                        'type': 'string',
                        'description': 'Stock symbol (e.g., TEVA, NICE, CHKP) or TASE ticker (e.g., PSTI.TA for Bank Leumi)',
                        'required': True
                    },
                    'period': {
                        'type': 'string',
                        'description': 'Data period (default 1d)',
                        'required': False,
                        'default': '1d'
                    }
                },
                'handler': self._tase_stock
            },
            'tase_market_summary': {
                'description': 'TASE market summary - TA-35, market breadth (advancers/decliners), top gainers/losers, total volume',
                'parameters': {},
                'handler': self._tase_market_summary
            },
            'tase_sector_performance': {
                'description': 'Sector performance analysis for Israeli stocks - Technology, Healthcare, Financials, etc.',
                'parameters': {},
                'handler': self._tase_sector_performance
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
            },
            
            # Global FX Rates (Phase 181)
            'fx_rate': {
                'description': 'Get exchange rate for a currency pair from ECB, FRED, or exchangerate.host',
                'parameters': {
                    'base': {
                        'type': 'string',
                        'description': 'Base currency code (e.g., USD, EUR, GBP)',
                        'required': True
                    },
                    'target': {
                        'type': 'string',
                        'description': 'Target currency code (e.g., EUR, JPY, CNY)',
                        'required': True
                    },
                    'source': {
                        'type': 'string',
                        'description': 'Data source: auto, ecb, fred, or exchangerate (default: auto)',
                        'required': False,
                        'default': 'auto'
                    }
                },
                'handler': self._fx_rate
            },
            'fx_all_rates': {
                'description': 'Get all available FX rates for a base currency',
                'parameters': {
                    'base': {
                        'type': 'string',
                        'description': 'Base currency code (default: USD)',
                        'required': False,
                        'default': 'USD'
                    }
                },
                'handler': self._fx_all_rates
            },
            'fx_cross_rate': {
                'description': 'Calculate cross rate for two non-USD currencies',
                'parameters': {
                    'currency1': {
                        'type': 'string',
                        'description': 'First currency code',
                        'required': True
                    },
                    'currency2': {
                        'type': 'string',
                        'description': 'Second currency code',
                        'required': True
                    },
                    'via': {
                        'type': 'string',
                        'description': 'Bridge currency (default: USD)',
                        'required': False,
                        'default': 'USD'
                    }
                },
                'handler': self._fx_cross_rate
            },
            'fx_matrix': {
                'description': 'Get FX rate matrix for a list of currencies',
                'parameters': {
                    'currencies': {
                        'type': 'array',
                        'description': 'List of currency codes',
                        'required': True
                    }
                },
                'handler': self._fx_matrix
            },
            'fx_convert': {
                'description': 'Convert amount from one currency to another',
                'parameters': {
                    'amount': {
                        'type': 'number',
                        'description': 'Amount to convert',
                        'required': True
                    },
                    'from_currency': {
                        'type': 'string',
                        'description': 'Source currency code',
                        'required': True
                    },
                    'to_currency': {
                        'type': 'string',
                        'description': 'Target currency code',
                        'required': True
                    }
                },
                'handler': self._fx_convert
            },
            'fx_strongest_weakest': {
                'description': 'Get strongest and weakest currencies vs base currency',
                'parameters': {
                    'base': {
                        'type': 'string',
                        'description': 'Base currency code (default: USD)',
                        'required': False,
                        'default': 'USD'
                    },
                    'period': {
                        'type': 'string',
                        'description': 'Time period: 1D, 1W, 1M (default: 1D)',
                        'required': False,
                        'default': '1D'
                    }
                },
                'handler': self._fx_strongest_weakest
            },
            'fx_list_currencies': {
                'description': 'List all supported currencies organized by region (G10, EM, Asia, MENA)',
                'parameters': {},
                'handler': self._fx_list_currencies
            },
            
            # Corporate Bond Spreads (Phase 156)
            'corporate_ig_spreads': {
                'description': 'Get Investment Grade corporate bond spreads by rating (AAA, AA, A, BBB)',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days of historical data (default 365)',
                        'required': False,
                        'default': 365
                    }
                },
                'handler': self._corporate_ig_spreads
            },
            'corporate_hy_spreads': {
                'description': 'Get High Yield corporate bond spreads by rating (BB, B, CCC)',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days of historical data (default 365)',
                        'required': False,
                        'default': 365
                    }
                },
                'handler': self._corporate_hy_spreads
            },
            'corporate_sector_spreads': {
                'description': 'Get sector-specific corporate bond spreads',
                'parameters': {
                    'sector': {
                        'type': 'string',
                        'description': 'Sector name (financials, energy, utilities, etc.)',
                        'required': False
                    },
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days of historical data (default 365)',
                        'required': False,
                        'default': 365
                    }
                },
                'handler': self._corporate_sector_spreads
            },
            'corporate_ig_vs_hy': {
                'description': 'Compare Investment Grade vs High Yield corporate bond spreads',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days of historical data (default 365)',
                        'required': False,
                        'default': 365
                    }
                },
                'handler': self._corporate_ig_vs_hy
            },
            'corporate_spreads_by_maturity': {
                'description': 'Get corporate bond spreads segmented by maturity buckets',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days of historical data (default 365)',
                        'required': False,
                        'default': 365
                    }
                },
                'handler': self._corporate_spreads_by_maturity
            },
            'corporate_credit_dashboard': {
                'description': 'Comprehensive corporate bond credit risk dashboard',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days of historical data (default 365)',
                        'required': False,
                        'default': 365
                    }
                },
                'handler': self._corporate_credit_dashboard
            },
            'corporate_spread_trends': {
                'description': 'Analyze recent corporate bond spread trends and market signals',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days to analyze (default 90)',
                        'required': False,
                        'default': 90
                    }
                },
                'handler': self._corporate_spread_trends
            },
            
            # High Yield Bond Tracker (Phase 157)
            'hy_spreads': {
                'description': 'Get current high yield bond spreads by rating tier (Overall HY, BB, B, CCC)',
                'parameters': {},
                'handler': self._hy_spreads
            },
            'distressed_debt': {
                'description': 'Track distressed debt signals (CCC and below spreads, default risk)',
                'parameters': {},
                'handler': self._distressed_debt
            },
            'default_rates': {
                'description': 'Track high yield default rate indicators and estimates',
                'parameters': {},
                'handler': self._default_rates
            },
            'hy_dashboard': {
                'description': 'Comprehensive high yield bond dashboard with spreads, distressed debt, and defaults',
                'parameters': {},
                'handler': self._hy_dashboard
            },
            
            # CLO/ABS Market Monitor (Phase 163)
            'clo_market_overview': {
                'description': 'Get CLO market overview including spreads, leveraged loan indicators, and collateral health',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days of historical data (default 365)',
                        'required': False,
                        'default': 365
                    }
                },
                'handler': self._clo_market_overview
            },
            'abs_spreads_by_asset_class': {
                'description': 'Get ABS spreads and metrics by asset class (auto, credit_card, student_loan, cmbs)',
                'parameters': {
                    'asset_class': {
                        'type': 'string',
                        'description': 'Asset class: auto, credit_card, student_loan, cmbs (optional - defaults to all)',
                        'required': False
                    },
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days of historical data (default 365)',
                        'required': False,
                        'default': 365
                    }
                },
                'handler': self._abs_spreads_by_asset_class
            },
            'cmbs_market_metrics': {
                'description': 'Get Commercial Mortgage-Backed Securities (CMBS) market metrics',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days of historical data (default 365)',
                        'required': False,
                        'default': 365
                    }
                },
                'handler': self._cmbs_market_metrics
            },
            'structured_finance_issuance': {
                'description': 'Get structured finance new issuance trends (CLO, ABS, CMBS)',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days of historical data (default 730 for 2 years)',
                        'required': False,
                        'default': 730
                    }
                },
                'handler': self._structured_finance_issuance
            },
            'abs_delinquency_rates': {
                'description': 'Get delinquency rates across all ABS asset classes',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days of historical data (default 365)',
                        'required': False,
                        'default': 365
                    }
                },
                'handler': self._abs_delinquency_rates
            },
            'abs_liquidity_indicators': {
                'description': 'Get ABS market liquidity indicators (ABCP, commercial paper)',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days of historical data (default 365)',
                        'required': False,
                        'default': 365
                    }
                },
                'handler': self._abs_liquidity_indicators
            },
            'clo_abs_dashboard': {
                'description': 'Comprehensive CLO/ABS market dashboard with all metrics',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days of historical data (default 365)',
                        'required': False,
                        'default': 365
                    }
                },
                'handler': self._clo_abs_dashboard
            },
            'abs_credit_quality': {
                'description': 'Analyze credit quality trends for specific ABS asset class',
                'parameters': {
                    'asset_class': {
                        'type': 'string',
                        'description': 'Asset class to analyze: auto, credit_card, student_loan, cmbs',
                        'required': True
                    },
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days of historical data (default 365)',
                        'required': False,
                        'default': 365
                    }
                },
                'handler': self._abs_credit_quality
            },
            'nport_clo_abs_holdings': {
                'description': 'Get CLO/ABS holdings from SEC N-PORT institutional filings',
                'parameters': {
                    'cik': {
                        'type': 'string',
                        'description': 'Specific fund CIK to query (optional)',
                        'required': False
                    },
                    'limit': {
                        'type': 'integer',
                        'description': 'Maximum number of filings to fetch (default 10)',
                        'required': False,
                        'default': 10
                    }
                },
                'handler': self._nport_clo_abs_holdings
            },
            
            # Municipal Bond Monitor (Phase 155)
            'muni_search': {
                'description': 'Search for municipal bonds by issuer, state, or CUSIP',
                'parameters': {
                    'issuer_name': {
                        'type': 'string',
                        'description': 'Name of issuing entity (e.g., "New York City")',
                        'required': False
                    },
                    'state': {
                        'type': 'string',
                        'description': 'Two-letter state code (e.g., "NY")',
                        'required': False
                    },
                    'cusip': {
                        'type': 'string',
                        'description': 'Specific CUSIP identifier',
                        'required': False
                    },
                    'min_size': {
                        'type': 'number',
                        'description': 'Minimum issue size in millions',
                        'required': False
                    }
                },
                'handler': self._muni_search
            },
            'muni_trades': {
                'description': 'Get recent municipal bond trades with pricing and yield data',
                'parameters': {
                    'cusip': {
                        'type': 'string',
                        'description': 'Specific CUSIP to query',
                        'required': False
                    },
                    'state': {
                        'type': 'string',
                        'description': 'Filter by state code',
                        'required': False
                    },
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days to look back (default 7)',
                        'required': False,
                        'default': 7
                    },
                    'min_trade_size': {
                        'type': 'number',
                        'description': 'Minimum trade size in thousands',
                        'required': False
                    }
                },
                'handler': self._muni_trades
            },
            'muni_issuer': {
                'description': 'Get comprehensive issuer profile including credit ratings and outstanding debt',
                'parameters': {
                    'issuer_name': {
                        'type': 'string',
                        'description': 'Name of the issuing entity',
                        'required': True
                    }
                },
                'handler': self._muni_issuer
            },
            'muni_credit_events': {
                'description': 'Get recent credit events (rating changes, defaults, material events)',
                'parameters': {
                    'state': {
                        'type': 'string',
                        'description': 'Filter by state code',
                        'required': False
                    },
                    'event_type': {
                        'type': 'string',
                        'description': 'Type of event: rating_change, default, material_event',
                        'required': False
                    },
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days to look back (default 30)',
                        'required': False,
                        'default': 30
                    }
                },
                'handler': self._muni_credit_events
            },
            'muni_state_summary': {
                'description': 'Get comprehensive summary of municipal bonds for a specific state',
                'parameters': {
                    'state_code': {
                        'type': 'string',
                        'description': 'Two-letter state code (e.g., "NY", "CA")',
                        'required': True
                    }
                },
                'handler': self._muni_state_summary
            },
            'muni_yield_curve': {
                'description': 'Get municipal bond yield curve across maturities',
                'parameters': {
                    'state': {
                        'type': 'string',
                        'description': 'Optional state filter',
                        'required': False
                    },
                    'rating': {
                        'type': 'string',
                        'description': 'Credit rating: AAA, AA, A, BBB (default AAA)',
                        'required': False,
                        'default': 'AAA'
                    }
                },
                'handler': self._muni_yield_curve
            },
            'muni_compare_spreads': {
                'description': 'Compare yield spreads between two states',
                'parameters': {
                    'state1': {
                        'type': 'string',
                        'description': 'First state code',
                        'required': True
                    },
                    'state2': {
                        'type': 'string',
                        'description': 'Second state code',
                        'required': True
                    },
                    'maturity_years': {
                        'type': 'integer',
                        'description': 'Maturity to compare in years (default 10)',
                        'required': False,
                        'default': 10
                    }
                },
                'handler': self._muni_compare_spreads
            },
            
            # Swap Rate Curves (Phase 160)
            'usd_swap_curve': {
                'description': 'Get USD interest rate swap curve with spreads over Treasuries',
                'parameters': {},
                'handler': self._usd_swap_curve
            },
            'eur_swap_curve': {
                'description': 'Get EUR interest rate swap curve from ECB',
                'parameters': {},
                'handler': self._eur_swap_curve
            },
            'compare_swap_curves': {
                'description': 'Compare USD and EUR swap curves with policy divergence analysis',
                'parameters': {},
                'handler': self._compare_swap_curves
            },
            'swap_spread': {
                'description': 'Get swap spread for specific tenor and currency',
                'parameters': {
                    'tenor': {
                        'type': 'string',
                        'description': 'Tenor like "2Y", "5Y", "10Y", "30Y" (default "10Y")',
                        'required': False,
                        'default': '10Y'
                    },
                    'currency': {
                        'type': 'string',
                        'description': 'Currency: "USD" or "EUR" (default "USD")',
                        'required': False,
                        'default': 'USD'
                    }
                },
                'handler': self._swap_spread
            },
            'swap_inversion_signal': {
                'description': 'Detect yield curve inversions in USD and EUR swap markets (recession signals)',
                'parameters': {},
                'handler': self._swap_inversion_signal
            },
            
            # Treasury Yield Curve Tools (Phase 154)
            'treasury_yield_curve': {
                'description': 'Get current US Treasury yield curve from 1 Month to 30 Years',
                'parameters': {
                    'format_table': {
                        'type': 'boolean',
                        'description': 'Include ASCII table format in output',
                        'required': False,
                        'default': False
                    }
                },
                'handler': self._treasury_yield_curve
            },
            'treasury_yield_history': {
                'description': 'Get historical yield curve data across time',
                'parameters': {
                    'start_date': {
                        'type': 'string',
                        'description': 'Start date (YYYY-MM-DD format)',
                        'required': False
                    },
                    'end_date': {
                        'type': 'string',
                        'description': 'End date (YYYY-MM-DD format)',
                        'required': False
                    },
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days to look back if dates not specified (default 90)',
                        'required': False,
                        'default': 90
                    }
                },
                'handler': self._treasury_yield_history
            },
            'treasury_yield_analyze': {
                'description': 'Analyze yield curve shape and detect inversions (recession signals)',
                'parameters': {
                    'curve_data': {
                        'type': 'object',
                        'description': 'Optional pre-fetched curve data',
                        'required': False
                    }
                },
                'handler': self._treasury_yield_analyze
            },
            'treasury_yield_compare': {
                'description': 'Compare yield curves between two dates to detect shifts',
                'parameters': {
                    'date1': {
                        'type': 'string',
                        'description': 'First date (YYYY-MM-DD format, default today)',
                        'required': False
                    },
                    'date2': {
                        'type': 'string',
                        'description': 'Second date (YYYY-MM-DD format)',
                        'required': False
                    },
                    'days_back': {
                        'type': 'integer',
                        'description': 'Days back for second date if not specified (default 30)',
                        'required': False,
                        'default': 30
                    }
                },
                'handler': self._treasury_yield_compare
            },
            'treasury_yield_maturity': {
                'description': 'Get historical time series for a specific maturity',
                'parameters': {
                    'maturity': {
                        'type': 'string',
                        'description': 'Maturity code (e.g., 10Y, 2Y, 3M)',
                        'required': True
                    },
                    'days_back': {
                        'type': 'integer',
                        'description': 'Historical lookback period in days (default 365)',
                        'required': False,
                        'default': 365
                    }
                },
                'handler': self._treasury_yield_maturity
            },
            
            # Repo Rate Monitor Tools (Phase 161)
            'repo_sofr_rates': {
                'description': 'Get SOFR rates including daily rate and moving averages (30d, 90d, 180d)',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days of historical data (default 90)',
                        'required': False,
                        'default': 90
                    }
                },
                'handler': self._repo_sofr_rates
            },
            'repo_rates': {
                'description': 'Get repo and reverse repo rates from NY Fed',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days of historical data (default 90)',
                        'required': False,
                        'default': 90
                    }
                },
                'handler': self._repo_rates
            },
            'repo_reverse_repo_operations': {
                'description': 'Get Fed reverse repo facility operations with volumes and rates',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days of data (default 90)',
                        'required': False,
                        'default': 90
                    }
                },
                'handler': self._repo_reverse_repo_operations
            },
            'repo_overnight_rates_dashboard': {
                'description': 'Get comprehensive overnight rates dashboard (SOFR, Fed Funds, OBFR, TGCR, BGCR)',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days of historical data (default 90)',
                        'required': False,
                        'default': 90
                    }
                },
                'handler': self._repo_overnight_rates_dashboard
            },
            'repo_compare_money_market_rates': {
                'description': 'Compare all major money market rates and calculate spreads',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days to analyze (default 90)',
                        'required': False,
                        'default': 90
                    }
                },
                'handler': self._repo_compare_money_market_rates
            },
            'repo_funding_stress_indicators': {
                'description': 'Calculate funding stress indicators from money market rates',
                'parameters': {},
                'handler': self._repo_funding_stress_indicators
            },
            
            # TIPS & Breakeven Inflation Tools (Phase 159)
            'tips_current': {
                'description': 'Get current TIPS (real) yields, breakeven inflation rates, and nominal yields across all maturities',
                'parameters': {
                    'include_inflation': {
                        'type': 'boolean',
                        'description': 'Include actual inflation measures (CPI, PCE) for comparison',
                        'required': False,
                        'default': True
                    }
                },
                'handler': self._tips_current
            },
            'breakeven_curve': {
                'description': 'Analyze the breakeven inflation curve shape, trends, and compare to actual inflation',
                'parameters': {
                    'format_table': {
                        'type': 'boolean',
                        'description': 'Include formatted ASCII table in output',
                        'required': False,
                        'default': False
                    }
                },
                'handler': self._breakeven_curve
            },
            'real_yield_history': {
                'description': 'Get historical TIPS real yield data for a specific maturity',
                'parameters': {
                    'maturity': {
                        'type': 'string',
                        'description': 'Maturity (5Y, 7Y, 10Y, 20Y, 30Y)',
                        'required': False,
                        'default': '10Y'
                    },
                    'days_back': {
                        'type': 'integer',
                        'description': 'Historical lookback period in days',
                        'required': False,
                        'default': 365
                    }
                },
                'handler': self._real_yield_history
            },
            'tips_vs_nominal': {
                'description': 'Compare TIPS (real) yields vs nominal Treasury yields to show implied inflation expectations',
                'parameters': {
                    'maturity': {
                        'type': 'string',
                        'description': 'Maturity to compare (5Y, 7Y, 10Y, 20Y, 30Y)',
                        'required': False,
                        'default': '10Y'
                    }
                },
                'handler': self._tips_vs_nominal
            },
            'inflation_expectations': {
                'description': 'Get comprehensive summary of market inflation expectations including breakeven rates, forward expectations, and actual inflation',
                'parameters': {},
                'handler': self._inflation_expectations
            },
            'breakeven_changes': {
                'description': 'Track how breakeven inflation rates have changed over a period',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Period to analyze in days',
                        'required': False,
                        'default': 30
                    }
                },
                'handler': self._breakeven_changes
            },
            
            # Inflation-Linked Bonds Tools (Phase 167)
            'global_linker_summary': {
                'description': 'Get comprehensive summary of global inflation-linked bond markets (US TIPS, Euro linkers, UK gilts)',
                'parameters': {},
                'handler': self._global_linker_summary
            },
            'us_tips_yields': {
                'description': 'Get current US TIPS (Treasury Inflation-Protected Securities) yields across maturities',
                'parameters': {
                    'maturities': {
                        'type': 'array',
                        'description': 'List of maturities to fetch (5Y, 7Y, 10Y, 20Y, 30Y). None = all',
                        'required': False
                    }
                },
                'handler': self._us_tips_yields
            },
            'euro_linker_yields': {
                'description': 'Get Eurozone inflation-linked bond yields from ECB',
                'parameters': {},
                'handler': self._euro_linker_yields
            },
            'uk_gilt_yields': {
                'description': 'Get UK index-linked gilt yields from Bank of England',
                'parameters': {},
                'handler': self._uk_gilt_yields
            },
            'compare_linker_yields': {
                'description': 'Compare inflation-linked bond yields across regions',
                'parameters': {
                    'region1': {
                        'type': 'string',
                        'description': 'First region (US, EURO, UK)',
                        'required': False,
                        'default': 'US'
                    },
                    'region2': {
                        'type': 'string',
                        'description': 'Second region (US, EURO, UK)',
                        'required': False,
                        'default': 'EURO'
                    }
                },
                'handler': self._compare_linker_yields
            },
            'linker_history': {
                'description': 'Get historical inflation-linked bond yields for a specific region and maturity',
                'parameters': {
                    'region': {
                        'type': 'string',
                        'description': 'Region code (US, EURO, UK)',
                        'required': False,
                        'default': 'US'
                    },
                    'maturity': {
                        'type': 'string',
                        'description': 'Maturity (5Y, 7Y, 10Y, 20Y, 30Y)',
                        'required': False,
                        'default': '10Y'
                    },
                    'days_back': {
                        'type': 'integer',
                        'description': 'Historical lookback period in days',
                        'required': False,
                        'default': 365
                    }
                },
                'handler': self._linker_history
            },
            'real_yield_trends': {
                'description': 'Analyze recent trends in real yields across all major linker markets',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Period to analyze in days',
                        'required': False,
                        'default': 30
                    }
                },
                'handler': self._real_yield_trends
            },
            
            # Commercial Paper Rates Tools (Phase 162)
            'cp_current_rates': {
                'description': 'Get current AA-rated commercial paper rates for financial and nonfinancial issuers across all maturities',
                'parameters': {},
                'handler': self._cp_current_rates
            },
            'cp_rate_history': {
                'description': 'Get historical commercial paper rates',
                'parameters': {
                    'days': {
                        'type': 'integer',
                        'description': 'Number of days of history (default 90)',
                        'required': False,
                        'default': 90
                    },
                    'category': {
                        'type': 'string',
                        'description': 'Filter by category: Financial or Nonfinancial',
                        'required': False
                    }
                },
                'handler': self._cp_rate_history
            },
            'cp_spread_analysis': {
                'description': 'Analyze spreads between financial and nonfinancial commercial paper rates',
                'parameters': {
                    'days': {
                        'type': 'integer',
                        'description': 'Number of days to analyze (default 90)',
                        'required': False,
                        'default': 90
                    }
                },
                'handler': self._cp_spread_analysis
            },
            'cp_rate_comparison': {
                'description': 'Side-by-side comparison of financial vs nonfinancial CP rates across maturities',
                'parameters': {},
                'handler': self._cp_rate_comparison
            },
            'cp_dashboard': {
                'description': 'Comprehensive commercial paper market dashboard with current rates, spreads, and trends',
                'parameters': {},
                'handler': self._cp_dashboard
            },
            
            # Bond New Issue Calendar Tools (Phase 165)
            'bond_upcoming_issues': {
                'description': 'Get calendar of upcoming bond issuances from SEC EDGAR filings',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days to search back (default 30)',
                        'required': False,
                        'default': 30
                    },
                    'min_amount_millions': {
                        'type': 'number',
                        'description': 'Minimum principal amount in millions (default 100)',
                        'required': False,
                        'default': 100
                    }
                },
                'handler': self._bond_upcoming_issues
            },
            'bond_issuer_history': {
                'description': 'Get historical bond issuance for a specific company by CIK',
                'parameters': {
                    'ticker_or_cik': {
                        'type': 'string',
                        'description': 'Company ticker or CIK number',
                        'required': True
                    },
                    'years': {
                        'type': 'integer',
                        'description': 'Years of history to retrieve (default 2)',
                        'required': False,
                        'default': 2
                    }
                },
                'handler': self._bond_issuer_history
            },
            'bond_company_filings': {
                'description': 'Get recent bond-related filings for a specific company',
                'parameters': {
                    'cik': {
                        'type': 'string',
                        'description': 'Company CIK number',
                        'required': True
                    },
                    'count': {
                        'type': 'integer',
                        'description': 'Number of filings to retrieve (default 20)',
                        'required': False,
                        'default': 20
                    }
                },
                'handler': self._bond_company_filings
            },
            'bond_analyze_filing': {
                'description': 'Analyze a specific SEC filing for bond issuance details',
                'parameters': {
                    'cik': {
                        'type': 'string',
                        'description': 'Company CIK number',
                        'required': True
                    },
                    'accession_number': {
                        'type': 'string',
                        'description': 'SEC accession number',
                        'required': True
                    }
                },
                'handler': self._bond_analyze_filing
            },
            'bond_dashboard': {
                'description': 'Comprehensive bond new issue dashboard with recent filings and issuance trends',
                'parameters': {},
                'handler': self._bond_dashboard
            },
            
            # Central Bank Rate Decisions Tools (Phase 166)
            'central_bank_rate': {
                'description': 'Get current policy rate for a specific central bank (40+ banks worldwide)',
                'parameters': {
                    'bank_code': {
                        'type': 'string',
                        'description': 'Central bank code (e.g., FED, ECB, BOJ, BOE, RBA, PBOC, RBI, etc.)',
                        'required': True
                    }
                },
                'handler': self._central_bank_rate
            },
            'central_bank_all_rates': {
                'description': 'Get current policy rates for all 40+ central banks worldwide',
                'parameters': {},
                'handler': self._central_bank_all_rates
            },
            'central_bank_compare': {
                'description': 'Compare policy rates across multiple central banks with statistics',
                'parameters': {
                    'bank_codes': {
                        'type': 'array',
                        'description': 'List of central bank codes to compare',
                        'required': True
                    }
                },
                'handler': self._central_bank_compare
            },
            'central_bank_heatmap': {
                'description': 'Global central bank rate change heatmap showing synchronized tightening/easing cycles',
                'parameters': {},
                'handler': self._central_bank_heatmap
            },
            'central_bank_search': {
                'description': 'Search for central banks by name, country, or currency',
                'parameters': {
                    'query': {
                        'type': 'string',
                        'description': 'Search query (e.g., "japan", "euro", "GBP")',
                        'required': True
                    }
                },
                'handler': self._central_bank_search
            },
            'central_bank_differential': {
                'description': 'Calculate interest rate differential between two central banks (useful for carry trade analysis)',
                'parameters': {
                    'bank_code_1': {
                        'type': 'string',
                        'description': 'First central bank code',
                        'required': True
                    },
                    'bank_code_2': {
                        'type': 'string',
                        'description': 'Second central bank code',
                        'required': True
                    }
                },
                'handler': self._central_bank_differential
            },
            'central_bank_list': {
                'description': 'List all available central banks with codes and details',
                'parameters': {},
                'handler': self._central_bank_list
            },
            
            # FX Carry Trade Monitor Tools (Phase 182)
            'fx_carry_opportunities': {
                'description': 'Identify FX carry trade opportunities with risk-adjusted carry ratios',
                'parameters': {
                    'min_differential': {
                        'type': 'number',
                        'description': 'Minimum interest rate differential in % (default 1.0)',
                        'required': False,
                        'default': 1.0
                    }
                },
                'handler': self._fx_carry_opportunities
            },
            'fx_carry_differential': {
                'description': 'Calculate interest rate differential and carry trade metrics between two currencies',
                'parameters': {
                    'currency1': {
                        'type': 'string',
                        'description': 'First currency code (USD, EUR, JPY, GBP, AUD, CAD, CHF, NZD, SEK, NOK)',
                        'required': True
                    },
                    'currency2': {
                        'type': 'string',
                        'description': 'Second currency code',
                        'required': True
                    }
                },
                'handler': self._fx_carry_differential
            },
            'fx_carry_dashboard': {
                'description': 'Comprehensive FX carry trade dashboard with top opportunities and market overview',
                'parameters': {},
                'handler': self._fx_carry_dashboard
            },
            'fx_carry_funding': {
                'description': 'Get currencies with lowest interest rates (best for funding carry trades)',
                'parameters': {
                    'n': {
                        'type': 'integer',
                        'description': 'Number of currencies to return (default 3)',
                        'required': False,
                        'default': 3
                    }
                },
                'handler': self._fx_carry_funding
            },
            'fx_carry_investment': {
                'description': 'Get currencies with highest interest rates (best for investment side of carry trades)',
                'parameters': {
                    'n': {
                        'type': 'integer',
                        'description': 'Number of currencies to return (default 3)',
                        'required': False,
                        'default': 3
                    }
                },
                'handler': self._fx_carry_investment
            },
            
            # Gold & Precious Metals Tools (Phase 171)
            'gold_prices': {
                'description': 'Get current spot prices for gold, silver, platinum, and palladium',
                'parameters': {},
                'handler': self._gold_prices
            },
            'gold_etf_holdings': {
                'description': 'Get holdings and NAV data for precious metals ETFs (GLD, SLV, PPLT, PALL)',
                'parameters': {},
                'handler': self._gold_etf_holdings
            },
            'gold_silver_ratio': {
                'description': 'Calculate current gold/silver price ratio with historical context and interpretation',
                'parameters': {},
                'handler': self._gold_silver_ratio
            },
            'gold_performance': {
                'description': 'Calculate performance metrics for all precious metals over specified period',
                'parameters': {
                    'period': {
                        'type': 'string',
                        'description': 'Time period: 1mo, 3mo, 6mo, 1y, 2y, 5y, ytd',
                        'required': False,
                        'default': '1y'
                    }
                },
                'handler': self._gold_performance
            },
            'gold_wgc_summary': {
                'description': 'Get World Gold Council market fundamentals (supply, demand, holdings)',
                'parameters': {},
                'handler': self._gold_wgc_summary
            },
            'gold_comprehensive_report': {
                'description': 'Generate comprehensive precious metals market report with all available data',
                'parameters': {},
                'handler': self._gold_comprehensive_report
            },
            
            # Industrial Metals Tools (Phase 172)
            'copper_price': {
                'description': 'Get LME copper price and analysis (Dr. Copper - leading economic indicator)',
                'parameters': {},
                'handler': self._copper_price
            },
            'aluminum_price': {
                'description': 'Get LME aluminum price and industrial demand signals',
                'parameters': {},
                'handler': self._aluminum_price
            },
            'zinc_price': {
                'description': 'Get LME zinc price and steel production correlation',
                'parameters': {},
                'handler': self._zinc_price
            },
            'nickel_price': {
                'description': 'Get LME nickel price and EV battery demand signals',
                'parameters': {},
                'handler': self._nickel_price
            },
            'metal_inventories': {
                'description': 'Estimate metal inventory levels and supply/demand balance (proxy indicators)',
                'parameters': {},
                'handler': self._metal_inventories
            },
            'metals_snapshot': {
                'description': 'Comprehensive snapshot of all industrial metals (copper, aluminum, zinc, nickel)',
                'parameters': {},
                'handler': self._metals_snapshot
            },
            'metals_correlation': {
                'description': 'Calculate correlation between industrial metals and economic indicators',
                'parameters': {},
                'handler': self._metals_correlation
            },
            # Crude Oil Fundamentals (Phase 169)
            'crude_oil_stocks': {
                'description': 'Get US commercial crude oil inventories (excluding SPR) from EIA - weekly data',
                'parameters': {
                    'weeks': {
                        'type': 'integer',
                        'description': 'Number of weeks of historical data (default 52)',
                        'required': False,
                        'default': 52
                    }
                },
                'handler': self._crude_oil_stocks
            },
            'crude_oil_cushing': {
                'description': 'Get Cushing, OK crude oil storage levels - NYMEX WTI delivery point',
                'parameters': {},
                'handler': self._crude_oil_cushing
            },
            'crude_oil_spr': {
                'description': 'Get Strategic Petroleum Reserve inventory levels',
                'parameters': {},
                'handler': self._crude_oil_spr
            },
            'crude_oil_production': {
                'description': 'Get US crude oil field production rates',
                'parameters': {},
                'handler': self._crude_oil_production
            },
            'crude_oil_trade': {
                'description': 'Get US crude oil imports and exports',
                'parameters': {},
                'handler': self._crude_oil_trade
            },
            'crude_oil_refinery': {
                'description': 'Get US refinery operations and utilization rates',
                'parameters': {},
                'handler': self._crude_oil_refinery
            },
            'opec_production': {
                'description': 'Get OPEC member production data from Monthly Oil Market Report',
                'parameters': {},
                'handler': self._opec_production
            },
            'opec_spare_capacity': {
                'description': 'Get OPEC spare production capacity analysis',
                'parameters': {},
                'handler': self._opec_spare_capacity
            },
            'us_vs_opec': {
                'description': 'Compare US vs OPEC production and market influence',
                'parameters': {},
                'handler': self._us_vs_opec
            },
            'crude_oil_dashboard': {
                'description': 'Comprehensive crude oil fundamentals dashboard combining EIA and OPEC data',
                'parameters': {},
                'handler': self._crude_oil_dashboard
            },
            'crude_oil_weekly_report': {
                'description': 'Weekly crude oil market report with market balance analysis',
                'parameters': {},
                'handler': self._crude_oil_weekly_report
            },
            
            # Natural Gas Supply/Demand (Phase 170)
            'natural_gas_storage': {
                'description': 'Get weekly natural gas storage report for Lower 48 states from EIA',
                'parameters': {
                    'weeks': {
                        'type': 'integer',
                        'description': 'Number of weeks of historical data (default 52)',
                        'required': False,
                        'default': 52
                    }
                },
                'handler': self._natural_gas_storage
            },
            'natural_gas_production': {
                'description': 'Get US natural gas production data (dry and marketed gas)',
                'parameters': {
                    'months': {
                        'type': 'integer',
                        'description': 'Number of months of historical data (default 12)',
                        'required': False,
                        'default': 12
                    }
                },
                'handler': self._natural_gas_production
            },
            'natural_gas_demand': {
                'description': 'Get US natural gas consumption/demand by sector (residential, commercial, industrial, electric power)',
                'parameters': {
                    'months': {
                        'type': 'integer',
                        'description': 'Number of months of historical data (default 12)',
                        'required': False,
                        'default': 12
                    }
                },
                'handler': self._natural_gas_demand
            },
            'natural_gas_balance': {
                'description': 'Get comprehensive natural gas supply/demand balance analysis',
                'parameters': {
                    'months': {
                        'type': 'integer',
                        'description': 'Number of months of historical data (default 12)',
                        'required': False,
                        'default': 12
                    }
                },
                'handler': self._natural_gas_balance
            },
            'natural_gas_series': {
                'description': 'Fetch specific EIA natural gas data series',
                'parameters': {
                    'series_key': {
                        'type': 'string',
                        'description': 'Series key from NG_SERIES (STORAGE_WORKING, PRODUCTION_DRY, etc.)',
                        'required': True
                    },
                    'limit': {
                        'type': 'integer',
                        'description': 'Maximum number of data points (default 5000)',
                        'required': False,
                        'default': 5000
                    }
                },
                'handler': self._natural_gas_series
            },
            'natural_gas_list_series': {
                'description': 'List all available natural gas data series',
                'parameters': {},
                'handler': self._natural_gas_list_series
            },
            
            # LNG & Gas Market Tracker (Phase 176)
            'lng_prices': {
                'description': 'Get LNG price benchmarks (Henry Hub, TTF)',
                'parameters': {
                    'days': {
                        'type': 'integer',
                        'description': 'Number of days of historical data (default 90)',
                        'required': False,
                        'default': 90
                    }
                },
                'handler': self._lng_prices
            },
            'lng_price_summary': {
                'description': 'Get current LNG price summary (latest prices only)',
                'parameters': {},
                'handler': self._lng_price_summary
            },
            'lng_trade_flows': {
                'description': 'Get global LNG trade flows between major exporters and importers',
                'parameters': {},
                'handler': self._lng_trade_flows
            },
            'lng_exporters': {
                'description': 'Get ranking of major LNG exporting countries',
                'parameters': {},
                'handler': self._lng_exporters
            },
            'lng_importers': {
                'description': 'Get ranking of major LNG importing countries',
                'parameters': {},
                'handler': self._lng_importers
            },
            'lng_terminals': {
                'description': 'Get major LNG terminal data with utilization estimates',
                'parameters': {},
                'handler': self._lng_terminals
            },
            'lng_terminal_detail': {
                'description': 'Get detailed data for a specific LNG terminal',
                'parameters': {
                    'terminal_id': {
                        'type': 'string',
                        'description': 'Terminal identifier (e.g., Sabine_Pass, Ras_Laffan)',
                        'required': True
                    }
                },
                'handler': self._lng_terminal_detail
            },
            'lng_market_summary': {
                'description': 'Get comprehensive LNG market summary with prices, flows, and terminals',
                'parameters': {},
                'handler': self._lng_market_summary
            },
            
            # Rare Earths & Strategic Minerals (Phase 178)
            'mineral_profile': {
                'description': 'Get comprehensive profile for a strategic mineral including production, reserves, and supply chain data',
                'parameters': {
                    'mineral': {
                        'type': 'string',
                        'description': 'Mineral name (rare_earths, lithium, cobalt, graphite, tungsten, gallium, germanium)',
                        'required': True
                    }
                },
                'handler': self._mineral_profile
            },
            'supply_risk_score': {
                'description': 'Calculate comprehensive supply chain risk score for a strategic mineral',
                'parameters': {
                    'mineral': {
                        'type': 'string',
                        'description': 'Mineral name',
                        'required': True
                    }
                },
                'handler': self._supply_risk_score
            },
            'supply_risk_rankings': {
                'description': 'Get all minerals ranked by supply chain risk score',
                'parameters': {},
                'handler': self._supply_risk_rankings
            },
            'sector_exposure': {
                'description': 'Get critical mineral exposure for a strategic sector (defense, energy, electronics, aerospace, medical)',
                'parameters': {
                    'sector': {
                        'type': 'string',
                        'description': 'Sector name (defense, energy, electronics, aerospace, medical)',
                        'required': True
                    }
                },
                'handler': self._sector_exposure
            },
            'country_production_profile': {
                'description': 'Get mineral production profile for a country',
                'parameters': {
                    'country': {
                        'type': 'string',
                        'description': 'Country name (china, united_states, australia, etc.)',
                        'required': True
                    }
                },
                'handler': self._country_production_profile
            },
            'rare_earths_detailed': {
                'description': 'Get detailed analysis of rare earth elements market structure and supply risks',
                'parameters': {},
                'handler': self._rare_earths_detailed
            },
            'minerals_comprehensive_report': {
                'description': 'Generate comprehensive strategic minerals report with all critical mineral data',
                'parameters': {},
                'handler': self._minerals_comprehensive_report
            },
            'list_critical_minerals': {
                'description': 'List all tracked minerals and critical minerals',
                'parameters': {},
                'handler': self._list_critical_minerals
            },
            
            # Patent Tracking (Phase 11)
            'patent_search': {
                'description': 'Search for patents filed by a company and analyze R&D velocity',
                'parameters': {
                    'company_name': {
                        'type': 'string',
                        'description': 'Company name to search (e.g., "Apple", "Microsoft", "Tesla")',
                        'required': True
                    },
                    'years': {
                        'type': 'integer',
                        'description': 'Number of years to look back (default 5)',
                        'required': False,
                        'default': 5
                    },
                    'limit': {
                        'type': 'integer',
                        'description': 'Maximum number of patents to return (default 100)',
                        'required': False,
                        'default': 100
                    }
                },
                'handler': self._patent_search
            },
            'patent_compare': {
                'description': 'Compare patent activity across multiple companies',
                'parameters': {
                    'companies': {
                        'type': 'array',
                        'description': 'List of company names to compare',
                        'required': True
                    },
                    'years': {
                        'type': 'integer',
                        'description': 'Number of years to analyze (default 5)',
                        'required': False,
                        'default': 5
                    }
                },
                'handler': self._patent_compare
            },
            'patent_trends': {
                'description': 'Analyze patent filing trends over time for a company',
                'parameters': {
                    'company': {
                        'type': 'string',
                        'description': 'Company name',
                        'required': True
                    },
                    'years': {
                        'type': 'integer',
                        'description': 'Number of years to analyze (default 10)',
                        'required': False,
                        'default': 10
                    }
                },
                'handler': self._patent_trends
            },
            'patent_industry_leaders': {
                'description': 'Get patent leaders in a specific industry',
                'parameters': {
                    'industry': {
                        'type': 'string',
                        'description': 'Industry name (tech, software, hardware, etc.)',
                        'required': True
                    },
                    'limit': {
                        'type': 'integer',
                        'description': 'Number of top companies to return (default 10)',
                        'required': False,
                        'default': 10
                    }
                },
                'handler': self._patent_industry_leaders
            },
            
            # Semiconductor Chip Data (Phase 195)
            'get_semiconductor_sales': {
                'description': 'Get monthly semiconductor chip sales by region (SIA data)',
                'parameters': {
                    'region': {
                        'type': 'string',
                        'description': 'Region filter: all, americas, europe, japan, asia_pacific',
                        'required': False,
                        'default': 'all'
                    },
                    'months': {
                        'type': 'integer',
                        'description': 'Number of months to retrieve',
                        'required': False,
                        'default': 12
                    }
                },
                'handler': self._get_semiconductor_sales
            },
            'get_chip_forecast': {
                'description': 'Get WSTS semiconductor market forecasts by segment and region',
                'parameters': {
                    'horizon': {
                        'type': 'string',
                        'description': 'Forecast horizon: monthly, quarterly, yearly',
                        'required': False,
                        'default': 'yearly'
                    }
                },
                'handler': self._get_chip_forecast
            },
            'get_fab_utilization': {
                'description': 'Get semiconductor fab utilization rates by region and company',
                'parameters': {
                    'granularity': {
                        'type': 'string',
                        'description': 'Data granularity: industry, regional, company',
                        'required': False,
                        'default': 'industry'
                    }
                },
                'handler': self._get_fab_utilization
            },
            'get_chip_market_summary': {
                'description': 'Get comprehensive semiconductor market summary with trends and forecasts',
                'parameters': {},
                'handler': self._get_chip_market_summary
            },
            
            # Agricultural Commodities (Phase 173)
            'ag_futures_all': {
                'description': 'Get current prices for all agricultural futures (grains and soft commodities)',
                'parameters': {},
                'handler': self._ag_futures_all
            },
            'ag_futures_commodity': {
                'description': 'Get current price for a specific agricultural commodity future',
                'parameters': {
                    'commodity': {
                        'type': 'string',
                        'description': 'Commodity name (CORN, WHEAT, SOYBEANS, SUGAR, COFFEE)',
                        'required': True
                    }
                },
                'handler': self._ag_futures_commodity
            },
            'ag_grains': {
                'description': 'Get current prices for grain futures (corn, wheat, soybeans)',
                'parameters': {},
                'handler': self._ag_grains
            },
            'ag_softs': {
                'description': 'Get current prices for soft commodity futures (sugar, coffee)',
                'parameters': {},
                'handler': self._ag_softs
            },
            'ag_usda_crop': {
                'description': 'Get USDA crop production data via NASS QuickStats API',
                'parameters': {
                    'commodity': {
                        'type': 'string',
                        'description': 'Commodity name (CORN, WHEAT, SOYBEANS, COTTON, RICE)',
                        'required': True
                    },
                    'metric': {
                        'type': 'string',
                        'description': 'Metric to fetch (PRODUCTION, YIELD, ACRES PLANTED, ACRES HARVESTED)',
                        'required': False,
                        'default': 'PRODUCTION'
                    },
                    'year': {
                        'type': 'integer',
                        'description': 'Specific year (optional, defaults to last 5 years)',
                        'required': False
                    }
                },
                'handler': self._ag_usda_crop
            },
            'ag_dashboard': {
                'description': 'Get comprehensive dashboard for a specific agricultural commodity (combines futures prices and USDA data)',
                'parameters': {
                    'commodity': {
                        'type': 'string',
                        'description': 'Commodity name (CORN, WHEAT, SOYBEANS, SUGAR, COFFEE)',
                        'required': True
                    }
                },
                'handler': self._ag_dashboard
            },
            'ag_list_commodities': {
                'description': 'List all available agricultural commodities',
                'parameters': {},
                'handler': self._ag_list_commodities
            },
            
            # Livestock & Meat Markets (Phase 174)
            'livestock_futures_all': {
                'description': 'Get current prices for all livestock futures (live cattle, feeder cattle, lean hogs)',
                'parameters': {},
                'handler': self._livestock_futures_all
            },
            'livestock_futures_specific': {
                'description': 'Get current price for a specific livestock future',
                'parameters': {
                    'livestock': {
                        'type': 'string',
                        'description': 'Livestock type (LIVE_CATTLE, FEEDER_CATTLE, LEAN_HOGS)',
                        'required': True
                    }
                },
                'handler': self._livestock_futures_specific
            },
            'livestock_cattle': {
                'description': 'Get cattle market prices (futures + USDA AMS cash market data)',
                'parameters': {},
                'handler': self._livestock_cattle
            },
            'livestock_hogs': {
                'description': 'Get hog market prices (futures + USDA AMS cash market + pork cutout values)',
                'parameters': {},
                'handler': self._livestock_hogs
            },
            'livestock_slaughter': {
                'description': 'Get weekly slaughter data for cattle and hogs from USDA AMS',
                'parameters': {},
                'handler': self._livestock_slaughter
            },
            'livestock_ams_report': {
                'description': 'Get specific USDA AMS market report by slug',
                'parameters': {
                    'slug': {
                        'type': 'string',
                        'description': 'Report slug (e.g., LM_CT150 for cattle, LM_HG200 for hogs)',
                        'required': True
                    },
                    'date': {
                        'type': 'string',
                        'description': 'Specific date (YYYY-MM-DD format, optional)',
                        'required': False
                    }
                },
                'handler': self._livestock_ams_report
            },
            'livestock_dashboard': {
                'description': 'Get comprehensive livestock market dashboard (all futures, cash markets, slaughter data)',
                'parameters': {},
                'handler': self._livestock_dashboard
            },
            'livestock_list_reports': {
                'description': 'List all available USDA AMS livestock reports',
                'parameters': {},
                'handler': self._livestock_list_reports
            },
            
            # OPEC Production Monitor (Phase 175)
            'opec_production': {
                'description': 'Get latest OPEC+ production data for all countries',
                'parameters': {},
                'handler': self._opec_production
            },
            'opec_summary': {
                'description': 'Get OPEC+ production summary with aggregates and compliance',
                'parameters': {},
                'handler': self._opec_summary
            },
            'opec_country': {
                'description': 'Get detailed production info for a specific OPEC+ country',
                'parameters': {
                    'country': {
                        'type': 'string',
                        'description': 'Country name (e.g., "Saudi Arabia", "Russia", "Iraq")',
                        'required': True
                    }
                },
                'handler': self._opec_country
            },
            'opec_compliance': {
                'description': 'Get compliance report showing countries meeting quotas, over-producers, and under-producers',
                'parameters': {},
                'handler': self._opec_compliance
            },
            'opec_quotas': {
                'description': 'Get history of OPEC+ quota changes and decisions',
                'parameters': {
                    'months': {
                        'type': 'integer',
                        'description': 'Number of months of history (default: 12)',
                        'required': False,
                        'default': 12
                    }
                },
                'handler': self._opec_quotas
            },
            
            # Carbon Credits & Emissions (Phase 177)
            'eu_ets_price_history': {
                'description': 'Get EU ETS carbon allowance (EUA) price history and statistics',
                'parameters': {
                    'days': {
                        'type': 'integer',
                        'description': 'Number of days of historical data (default: 365)',
                        'required': False,
                        'default': 365
                    }
                },
                'handler': self._eu_ets_price_history
            },
            'global_carbon_prices': {
                'description': 'Get current carbon prices across global compliance markets (EU, UK, China, California, etc.)',
                'parameters': {},
                'handler': self._global_carbon_prices
            },
            'carbon_market_statistics': {
                'description': 'Get comprehensive carbon market statistics, trends, and historical data',
                'parameters': {},
                'handler': self._carbon_market_statistics
            },
            'emissions_by_sector': {
                'description': 'Get emissions breakdown by sector for a jurisdiction (EU, UK, USA)',
                'parameters': {
                    'jurisdiction': {
                        'type': 'string',
                        'description': 'Jurisdiction code (EU, UK, USA)',
                        'required': False,
                        'default': 'EU'
                    }
                },
                'handler': self._emissions_by_sector
            },
            'compare_carbon_markets': {
                'description': 'Compare carbon pricing mechanisms across multiple jurisdictions',
                'parameters': {
                    'markets': {
                        'type': 'array',
                        'description': 'List of market codes to compare (default: top 5)',
                        'required': False
                    }
                },
                'handler': self._compare_carbon_markets
            },
            'carbon_offset_projects': {
                'description': 'Get information about carbon offset project types and voluntary carbon market registries',
                'parameters': {
                    'project_type': {
                        'type': 'string',
                        'description': 'Project type filter (forestry, renewable, cookstoves, methane, industrial, ocean, direct_air_capture)',
                        'required': False
                    }
                },
                'handler': self._carbon_offset_projects
            },
            
            # Container Port Throughput (Phase 193)
            'port_throughput': {
                'description': 'Get container throughput (TEU) for major global ports - Shanghai, Rotterdam, LA/Long Beach',
                'parameters': {
                    'port': {
                        'type': 'string',
                        'description': 'Port to query: shanghai, rotterdam, la_long_beach, or all (default: all)',
                        'required': False,
                        'default': 'all'
                    }
                },
                'handler': self._port_throughput
            },
            'port_compare': {
                'description': 'Compare container throughput across all major tracked ports with economic interpretation',
                'parameters': {},
                'handler': self._port_compare
            },
            'port_list': {
                'description': 'List all available container ports with metadata and reporting schedules',
                'parameters': {},
                'handler': self._port_list
            },
            'port_rankings': {
                'description': 'Get global top 20 container port rankings by TEU volume',
                'parameters': {},
                'handler': self._port_rankings
            },
            
            # CFTC Commitments of Traders Reports (Phase 180)
            'cot_latest': {
                'description': 'Get the most recent CFTC Commitments of Traders report',
                'parameters': {
                    'report_type': {
                        'type': 'string',
                        'description': 'Report type: legacy, disaggregated, or financial (default: legacy)',
                        'required': False,
                        'default': 'legacy'
                    }
                },
                'handler': self._cot_latest
            },
            'cot_contract': {
                'description': 'Get COT positioning data for a specific futures contract over time',
                'parameters': {
                    'contract_code': {
                        'type': 'string',
                        'description': 'CFTC contract code (e.g., 067651 for WTI Crude, 088691 for Gold)',
                        'required': True
                    },
                    'weeks': {
                        'type': 'integer',
                        'description': 'Number of weeks of historical data (default: 52)',
                        'required': False,
                        'default': 52
                    }
                },
                'handler': self._cot_contract
            },
            'cot_extremes': {
                'description': 'Identify futures contracts with extreme positioning levels (potential reversal signals)',
                'parameters': {
                    'report_type': {
                        'type': 'string',
                        'description': 'Report type: legacy, disaggregated, or financial (default: legacy)',
                        'required': False,
                        'default': 'legacy'
                    }
                },
                'handler': self._cot_extremes
            },
            'cot_summary': {
                'description': 'Get COT positioning summary across major asset classes (energy, metals, agriculture, financial)',
                'parameters': {},
                'handler': self._cot_summary
            },
            'cot_divergence': {
                'description': 'Find contracts with strong commercial vs speculative trader divergence (often precedes major price moves)',
                'parameters': {},
                'handler': self._cot_divergence
            },
            'cot_dashboard': {
                'description': 'Comprehensive COT dashboard with latest positioning, extremes, and divergences',
                'parameters': {},
                'handler': self._cot_dashboard
            },
            
            # FX Volatility Surface Tools (Phase 183)
            'fx_volatility_surface': {
                'description': 'Get full volatility surface for an FX pair (implied vol across tenors, risk reversals, butterflies)',
                'parameters': {
                    'pair': {
                        'type': 'string',
                        'description': 'FX pair (EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD, EURGBP, EURJPY, GBPJPY)',
                        'required': True
                    }
                },
                'handler': self._fx_volatility_surface
            },
            'fx_risk_reversals': {
                'description': 'Get risk reversal indicators for an FX pair (put/call skew across tenors)',
                'parameters': {
                    'pair': {
                        'type': 'string',
                        'description': 'FX pair name',
                        'required': True
                    }
                },
                'handler': self._fx_risk_reversals
            },
            'fx_butterflies': {
                'description': 'Get butterfly spreads for an FX pair (vol smile convexity across tenors)',
                'parameters': {
                    'pair': {
                        'type': 'string',
                        'description': 'FX pair name',
                        'required': True
                    }
                },
                'handler': self._fx_butterflies
            },
            'fx_vol_summary': {
                'description': 'Get volatility summary for all major FX pairs (ATM IV, RR, BF for 1M tenor)',
                'parameters': {},
                'handler': self._fx_vol_summary
            },
            'crypto_funding_rates': {
                'description': 'Get perpetual funding rates for a crypto symbol across exchanges',
                'parameters': {
                    'symbol': {
                        'type': 'string',
                        'description': 'Crypto symbol (e.g., BTC, ETH, SOL)',
                        'required': True
                    }
                },
                'handler': self._crypto_funding_rates
            },
            'crypto_futures_basis': {
                'description': 'Calculate futures basis (contango/backwardation) for a crypto symbol',
                'parameters': {
                    'symbol': {
                        'type': 'string',
                        'description': 'Crypto symbol (e.g., BTC, ETH, SOL)',
                        'required': True
                    }
                },
                'handler': self._crypto_futures_basis
            },
            'crypto_open_interest': {
                'description': 'Get open interest data for crypto futures across exchanges',
                'parameters': {
                    'symbol': {
                        'type': 'string',
                        'description': 'Crypto symbol (e.g., BTC, ETH, SOL)',
                        'required': True
                    },
                    'exchanges': {
                        'type': 'array',
                        'description': 'Optional list of exchanges to query',
                        'required': False
                    }
                },
                'handler': self._crypto_open_interest
            },
            'crypto_funding_arbitrage': {
                'description': 'Scan for funding rate arbitrage opportunities across multiple symbols',
                'parameters': {
                    'min_spread': {
                        'type': 'number',
                        'description': 'Minimum annual % spread to flag (default 0.5%)',
                        'required': False,
                        'default': 0.5
                    }
                },
                'handler': self._crypto_funding_arbitrage
            },
            'crypto_derivatives_snapshot': {
                'description': 'Get comprehensive derivatives market snapshot for multiple crypto symbols',
                'parameters': {
                    'symbols': {
                        'type': 'array',
                        'description': 'List of crypto symbols (default: BTC, ETH, SOL)',
                        'required': False
                    }
                },
                'handler': self._crypto_derivatives_snapshot
            },
            
            # Stablecoin Supply Monitor Tools (Phase 187)
            'stablecoin_all': {
                'description': 'Get all stablecoins with current supply and market metrics via DeFi Llama',
                'parameters': {},
                'handler': self._stablecoin_all
            },
            'stablecoin_detail': {
                'description': 'Get detailed data for a specific stablecoin including chain breakdown and recent mint/burn activity',
                'parameters': {
                    'stablecoin_id': {
                        'type': 'string',
                        'description': 'Stablecoin ID from DeFi Llama (e.g., "1" for USDT, "2" for USDC, "3" for DAI)',
                        'required': True
                    }
                },
                'handler': self._stablecoin_detail
            },
            'stablecoin_chain': {
                'description': 'Get all stablecoins on a specific blockchain',
                'parameters': {
                    'chain': {
                        'type': 'string',
                        'description': 'Blockchain name (e.g., "Ethereum", "BSC", "Polygon", "Arbitrum")',
                        'required': True
                    }
                },
                'handler': self._stablecoin_chain
            },
            'stablecoin_mint_burn': {
                'description': 'Analyze mint and burn events for a stablecoin over a specified period',
                'parameters': {
                    'stablecoin_id': {
                        'type': 'string',
                        'description': 'Stablecoin ID from DeFi Llama',
                        'required': True
                    },
                    'days': {
                        'type': 'integer',
                        'description': 'Number of days to analyze (default: 30)',
                        'required': False,
                        'default': 30
                    }
                },
                'handler': self._stablecoin_mint_burn
            },
            'stablecoin_dominance': {
                'description': 'Calculate market dominance percentage for top stablecoins',
                'parameters': {},
                'handler': self._stablecoin_dominance
            },
            
            # Cross-Chain Bridge Monitor Tools (Phase 190)
            'bridge_list': {
                'description': 'Get list of all cross-chain bridges with TVL and basic metrics',
                'parameters': {
                    'limit': {
                        'type': 'integer',
                        'description': 'Number of bridges to return (default: 10)',
                        'required': False,
                        'default': 10
                    },
                    'min_tvl': {
                        'type': 'number',
                        'description': 'Minimum TVL in USD (default: 1000000)',
                        'required': False,
                        'default': 1000000
                    }
                },
                'handler': self._bridge_list
            },
            'bridge_details': {
                'description': 'Get detailed information for a specific bridge including chain breakdown',
                'parameters': {
                    'bridge_id': {
                        'type': 'string',
                        'description': 'Bridge identifier from DeFi Llama (e.g., "multichain", "stargate", "across")',
                        'required': True
                    }
                },
                'handler': self._bridge_details
            },
            'bridge_volume': {
                'description': 'Get historical volume and flow data for a bridge',
                'parameters': {
                    'bridge_id': {
                        'type': 'string',
                        'description': 'Bridge identifier',
                        'required': True
                    },
                    'days': {
                        'type': 'integer',
                        'description': 'Number of days to analyze (default: 7)',
                        'required': False,
                        'default': 7
                    }
                },
                'handler': self._bridge_volume
            },
            'bridge_risk': {
                'description': 'Calculate comprehensive risk score for a bridge (0-10 scale)',
                'parameters': {
                    'bridge_id': {
                        'type': 'string',
                        'description': 'Bridge identifier',
                        'required': True
                    }
                },
                'handler': self._bridge_risk
            },
            'bridge_flow': {
                'description': 'Analyze cross-chain flow patterns and health for a bridge',
                'parameters': {
                    'bridge_id': {
                        'type': 'string',
                        'description': 'Bridge identifier',
                        'required': True
                    },
                    'days': {
                        'type': 'integer',
                        'description': 'Number of days to analyze (default: 30)',
                        'required': False,
                        'default': 30
                    }
                },
                'handler': self._bridge_flow
            },
            'bridge_report': {
                'description': 'Generate comprehensive bridge analysis report with all metrics',
                'parameters': {
                    'bridge_id': {
                        'type': 'string',
                        'description': 'Bridge identifier',
                        'required': True
                    }
                },
                'handler': self._bridge_report
            },
            
            # NFT Market Tracker Tools (Phase 189)
            'nft_collection_stats': {
                'description': 'Get NFT collection statistics (floor price, volume, sales, market cap, owners)',
                'parameters': {
                    'collection_slug': {
                        'type': 'string',
                        'description': 'Collection identifier (e.g., "boredapeyachtclub", "cryptopunks")',
                        'required': True
                    }
                },
                'handler': self._nft_collection_stats
            },
            'nft_top_collections': {
                'description': 'Get top NFT collections by trading volume',
                'parameters': {
                    'limit': {
                        'type': 'integer',
                        'description': 'Number of collections to return (default 20, max 50)',
                        'required': False,
                        'default': 20
                    }
                },
                'handler': self._nft_top_collections
            },
            'nft_wash_trading_detection': {
                'description': 'Detect potential wash trading in an NFT collection using heuristic indicators',
                'parameters': {
                    'collection_slug': {
                        'type': 'string',
                        'description': 'Collection identifier to analyze',
                        'required': True
                    }
                },
                'handler': self._nft_wash_trading
            },
            'nft_market_overview': {
                'description': 'Get comprehensive NFT market overview (top collections, total volume, market trends)',
                'parameters': {},
                'handler': self._nft_market_overview
            },
            'nft_compare_collections': {
                'description': 'Compare multiple NFT collections side-by-side',
                'parameters': {
                    'collection_slugs': {
                        'type': 'array',
                        'description': 'List of collection slugs to compare (2-5 collections)',
                        'required': True
                    }
                },
                'handler': self._nft_compare_collections
            },
            'nft_collection_history': {
                'description': 'Get historical floor price and volume data for a collection (limited by free APIs)',
                'parameters': {
                    'collection_slug': {
                        'type': 'string',
                        'description': 'Collection identifier',
                        'required': True
                    },
                    'days': {
                        'type': 'integer',
                        'description': 'Number of days of history (default 30)',
                        'required': False,
                        'default': 30
                    }
                },
                'handler': self._nft_collection_history
            },
            
            # Airport Traffic & Aviation Tools (Phase 192)
            'airport_operations': {
                'description': 'Get airport operations count as economic activity proxy (US: IATA codes, EU: ICAO codes)',
                'parameters': {
                    'airport_code': {
                        'type': 'string',
                        'description': 'Airport code (US: 3-letter IATA like "ATL", "LAX"; EU: 4-letter ICAO like "EGLL", "LFPG")',
                        'required': True
                    },
                    'days': {
                        'type': 'integer',
                        'description': 'Historical days to fetch (default 30)',
                        'required': False,
                        'default': 30
                    }
                },
                'handler': self._airport_operations
            },
            'airline_capacity_index': {
                'description': 'Get airline capacity utilization index as economic leading indicator (load factors, ASM)',
                'parameters': {},
                'handler': self._airline_capacity_index
            },
            'flight_delay_index': {
                'description': 'Get flight delay statistics as capacity constraint indicator',
                'parameters': {
                    'region': {
                        'type': 'string',
                        'description': 'Region code: "US" or "EU" (default "US")',
                        'required': False,
                        'default': 'US'
                    }
                },
                'handler': self._flight_delay_index
            },
            'regional_traffic_comparison': {
                'description': 'Compare air traffic across major regions (North America, Europe, Asia Pacific, Middle East) as global economic indicator',
                'parameters': {},
                'handler': self._regional_traffic_comparison
            },
            'aviation_economic_dashboard': {
                'description': 'Comprehensive aviation metrics dashboard - capacity, delays, regional traffic, top airports',
                'parameters': {},
                'handler': self._aviation_economic_dashboard
            },
            'list_airports': {
                'description': 'List all tracked airports with codes and names (US IATA codes, EU ICAO codes)',
                'parameters': {},
                'handler': self._list_airports
            },
            
            # Global Tourism Statistics Tools (Phase 194)
            'tourism_arrivals': {
                'description': 'Get international tourist arrivals for a country from World Bank data',
                'parameters': {
                    'country_code': {
                        'type': 'string',
                        'description': 'ISO 3-letter country code (e.g., USA, ESP, FRA) or WLD for global',
                        'required': False,
                        'default': 'WLD'
                    }
                },
                'handler': self._tourism_arrivals
            },
            'tourism_receipts': {
                'description': 'Get international tourism receipts (USD billions) for a country from World Bank data',
                'parameters': {
                    'country_code': {
                        'type': 'string',
                        'description': 'ISO 3-letter country code or WLD for global',
                        'required': False,
                        'default': 'WLD'
                    }
                },
                'handler': self._tourism_receipts
            },
            'tourism_country_profile': {
                'description': 'Get complete tourism profile including arrivals, receipts, dependency metrics',
                'parameters': {
                    'country_code': {
                        'type': 'string',
                        'description': 'ISO 3-letter country code (e.g., USA, ESP, THA)',
                        'required': True
                    }
                },
                'handler': self._tourism_country_profile
            },
            'tourism_global_overview': {
                'description': 'Get global tourism overview with top destinations and trends',
                'parameters': {},
                'handler': self._tourism_global_overview
            },
            'tourism_compare_countries': {
                'description': 'Compare tourism statistics between two countries',
                'parameters': {
                    'country1': {
                        'type': 'string',
                        'description': 'First country ISO code',
                        'required': True
                    },
                    'country2': {
                        'type': 'string',
                        'description': 'Second country ISO code',
                        'required': True
                    }
                },
                'handler': self._tourism_compare_countries
            },
            'hotel_occupancy': {
                'description': 'Get US hotel occupancy trends using hotel stock ETFs as proxy',
                'parameters': {},
                'handler': self._hotel_occupancy
            },
            'airline_passengers': {
                'description': 'Get airline passenger demand trends using airline stock performance as proxy',
                'parameters': {},
                'handler': self._airline_passengers
            },
            'tourism_recovery_tracker': {
                'description': 'Track global tourism recovery vs pre-pandemic (2019) baseline by region',
                'parameters': {},
                'handler': self._tourism_recovery_tracker
            },
            
            # Auto Sales & EV Registrations Tools (Phase 196)
            'get_auto_sales': {
                'description': 'Get US monthly auto sales data from FRED including total sales, light trucks, domestic vs foreign',
                'parameters': {
                    'country': {
                        'type': 'string',
                        'description': 'Country code (currently only US supported)',
                        'required': False,
                        'default': 'US'
                    },
                    'months': {
                        'type': 'integer',
                        'description': 'Number of months of data to fetch (default 12)',
                        'required': False,
                        'default': 12
                    }
                },
                'handler': self._get_auto_sales
            },
            'get_ev_registrations': {
                'description': 'Get EV registration data by country (US, EU, CN, JP, DE, FR, UK, IT, ES)',
                'parameters': {
                    'country': {
                        'type': 'string',
                        'description': 'Country code (US, EU, CN, JP, DE, FR, UK, IT, ES)',
                        'required': False,
                        'default': 'US'
                    },
                    'months': {
                        'type': 'integer',
                        'description': 'Number of months of data to fetch (default 12)',
                        'required': False,
                        'default': 12
                    }
                },
                'handler': self._get_ev_registrations
            },
            'get_auto_market_share': {
                'description': 'Get auto market share by manufacturer for a region (US, EU, CN)',
                'parameters': {
                    'region': {
                        'type': 'string',
                        'description': 'Region code (US, EU, CN)',
                        'required': False,
                        'default': 'US'
                    },
                    'months': {
                        'type': 'integer',
                        'description': 'Number of months to analyze (default 12)',
                        'required': False,
                        'default': 12
                    }
                },
                'handler': self._get_auto_market_share
            },
            'comprehensive_auto_report': {
                'description': 'Get comprehensive auto sales and EV market report covering US sales, global EV registrations, and manufacturer rankings',
                'parameters': {
                    'months': {
                        'type': 'integer',
                        'description': 'Number of months to analyze (default 12)',
                        'required': False,
                        'default': 12
                    }
                },
                'handler': self._get_comprehensive_auto_report
            },
            
            'search_bankruptcy_filings': {
                'description': 'Search recent SEC bankruptcy-related filings (8-K, 10-K, 10-Q) with Chapter 11, going concern warnings',
                'parameters': {
                    'days': {
                        'type': 'integer',
                        'description': 'Number of days to look back (default 30)',
                        'required': False,
                        'default': 30
                    },
                    'limit': {
                        'type': 'integer',
                        'description': 'Maximum number of results (default 50)',
                        'required': False,
                        'default': 50
                    }
                },
                'handler': self._search_bankruptcy_filings
            },
            'get_bankruptcy_tracker': {
                'description': 'Get bankruptcy risk status and related filings for a specific company by ticker',
                'parameters': {
                    'ticker': {
                        'type': 'string',
                        'description': 'Stock ticker symbol (e.g., AAPL, TSLA)',
                        'required': True
                    }
                },
                'handler': self._get_bankruptcy_tracker
            },
            'get_bankruptcy_stats': {
                'description': 'Get bankruptcy statistics by period - total filings, trends, sector breakdown',
                'parameters': {
                    'sector': {
                        'type': 'string',
                        'description': 'Optional sector filter',
                        'required': False
                    },
                    'year': {
                        'type': 'integer',
                        'description': 'Optional year filter (default: last 365 days)',
                        'required': False
                    }
                },
                'handler': self._get_bankruptcy_stats
            },
            
            # PE & VC Deal Flow Tools (Phase 198)
            'get_vc_deals': {
                'description': 'Get recent venture capital funding rounds from SEC Form D and Crunchbase',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days to look back (default 30)',
                        'required': False,
                        'default': 30
                    },
                    'min_amount': {
                        'type': 'number',
                        'description': 'Minimum deal size in millions USD (default 1.0)',
                        'required': False,
                        'default': 1.0
                    },
                    'max_results': {
                        'type': 'integer',
                        'description': 'Maximum number of results (default 20)',
                        'required': False,
                        'default': 20
                    },
                    'stage': {
                        'type': 'string',
                        'description': 'Funding stage filter (seed, series-a, series-b, etc)',
                        'required': False
                    }
                },
                'handler': self._get_vc_deals
            },
            'get_pe_deals': {
                'description': 'Get recent private equity transactions from SEC Form D filings',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days to look back (default 30)',
                        'required': False,
                        'default': 30
                    },
                    'min_amount': {
                        'type': 'number',
                        'description': 'Minimum deal size in millions USD (default 50.0)',
                        'required': False,
                        'default': 50.0
                    },
                    'max_results': {
                        'type': 'integer',
                        'description': 'Maximum number of results (default 20)',
                        'required': False,
                        'default': 20
                    },
                    'deal_type': {
                        'type': 'string',
                        'description': 'Type of PE deal (buyout, growth, distressed, etc)',
                        'required': False
                    }
                },
                'handler': self._get_pe_deals
            },
            'search_form_d': {
                'description': 'Search SEC Form D private placement filings',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days to look back (default 30)',
                        'required': False,
                        'default': 30
                    },
                    'min_amount': {
                        'type': 'number',
                        'description': 'Minimum offering amount in millions USD',
                        'required': False
                    },
                    'max_results': {
                        'type': 'integer',
                        'description': 'Maximum number of results (default 50)',
                        'required': False,
                        'default': 50
                    },
                    'keywords': {
                        'type': 'string',
                        'description': 'Keywords to search in company name/description',
                        'required': False
                    }
                },
                'handler': self._search_form_d
            },
            'deal_flow_summary': {
                'description': 'Get comprehensive summary of VC and PE deal flow with statistics',
                'parameters': {
                    'days_back': {
                        'type': 'integer',
                        'description': 'Number of days to analyze (default 30)',
                        'required': False,
                        'default': 30
                    }
                },
                'handler': self._deal_flow_summary
            },
            
            # Global Health Impact Monitor (Phase 199)
            'get_health_outbreaks': {
                'description': 'Track current disease outbreaks worldwide from WHO and other sources',
                'parameters': {
                    'country': {
                        'type': 'string',
                        'description': 'Optional country name to filter outbreaks',
                        'required': False
                    },
                    'disease': {
                        'type': 'string',
                        'description': 'Optional disease name to filter (e.g., Dengue, Cholera, Mpox)',
                        'required': False
                    },
                    'days': {
                        'type': 'integer',
                        'description': 'Lookback period in days (default 90)',
                        'required': False,
                        'default': 90
                    }
                },
                'handler': self._get_health_outbreaks
            },
            'get_pandemic_impact': {
                'description': 'Analyze economic impact from pandemics and health crises using FRED indicators',
                'parameters': {
                    'metric': {
                        'type': 'string',
                        'description': 'Type of metric: travel, retail, unemployment, or all (default all)',
                        'required': False,
                        'default': 'all'
                    },
                    'country': {
                        'type': 'string',
                        'description': 'Country code (default US)',
                        'required': False,
                        'default': 'US'
                    },
                    'start_date': {
                        'type': 'string',
                        'description': 'Start date in YYYY-MM-DD format (optional)',
                        'required': False
                    },
                    'end_date': {
                        'type': 'string',
                        'description': 'End date in YYYY-MM-DD format (optional)',
                        'required': False
                    }
                },
                'handler': self._get_pandemic_impact
            },
            'get_health_monitor': {
                'description': 'Global health surveillance dashboard with risk assessment',
                'parameters': {
                    'region': {
                        'type': 'string',
                        'description': 'Region to monitor: global, africa, asia, americas, europe (default global)',
                        'required': False,
                        'default': 'global'
                    },
                    'alert_threshold': {
                        'type': 'string',
                        'description': 'Minimum alert level to display: HIGH, MEDIUM, or LOW (default MEDIUM)',
                        'required': False,
                        'default': 'MEDIUM'
                    }
                },
                'handler': self._get_health_monitor
            },
            
            # Academic Finance Paper Tracker (Phase 200)
            'papers_latest': {
                'description': 'Get latest academic finance papers from arXiv, SSRN, and NBER',
                'parameters': {
                    'source': {
                        'type': 'string',
                        'description': 'Data source: arxiv, ssrn, nber, or all (default all)',
                        'required': False,
                        'default': 'all'
                    },
                    'days': {
                        'type': 'integer',
                        'description': 'Lookback period in days (default 7)',
                        'required': False,
                        'default': 7
                    },
                    'keywords': {
                        'type': 'string',
                        'description': 'Filter by keywords (e.g., "machine learning", "momentum")',
                        'required': False
                    },
                    'max_results': {
                        'type': 'integer',
                        'description': 'Maximum results per source (default 20)',
                        'required': False,
                        'default': 20
                    }
                },
                'handler': self._papers_latest
            },
            'papers_search': {
                'description': 'Search academic finance papers by keywords',
                'parameters': {
                    'query': {
                        'type': 'string',
                        'description': 'Search query string',
                        'required': True
                    },
                    'source': {
                        'type': 'string',
                        'description': 'Data source: arxiv, ssrn, nber, or all (default all)',
                        'required': False,
                        'default': 'all'
                    },
                    'max_results': {
                        'type': 'integer',
                        'description': 'Maximum results (default 20)',
                        'required': False,
                        'default': 20
                    }
                },
                'handler': self._papers_search
            },
            'papers_trending': {
                'description': 'Get trending/most downloaded academic finance papers',
                'parameters': {
                    'period': {
                        'type': 'string',
                        'description': 'Time period: week or month (default week)',
                        'required': False,
                        'default': 'week'
                    },
                    'source': {
                        'type': 'string',
                        'description': 'Data source: ssrn or arxiv (default ssrn)',
                        'required': False,
                        'default': 'ssrn'
                    },
                    'max_results': {
                        'type': 'integer',
                        'description': 'Maximum results (default 20)',
                        'required': False,
                        'default': 20
                    }
                },
                'handler': self._papers_trending
            },
            'papers_by_author': {
                'description': 'Search papers by author name',
                'parameters': {
                    'author_name': {
                        'type': 'string',
                        'description': 'Author name to search',
                        'required': True
                    },
                    'source': {
                        'type': 'string',
                        'description': 'Data source: arxiv or all (default all)',
                        'required': False,
                        'default': 'all'
                    },
                    'max_results': {
                        'type': 'integer',
                        'description': 'Maximum results (default 20)',
                        'required': False,
                        'default': 20
                    }
                },
                'handler': self._papers_by_author
            },
            'papers_report': {
                'description': 'Generate comprehensive academic papers report',
                'parameters': {
                    'format_type': {
                        'type': 'string',
                        'description': 'Report format: json, markdown, or summary (default summary)',
                        'required': False,
                        'default': 'summary'
                    },
                    'days': {
                        'type': 'integer',
                        'description': 'Lookback period in days (default 7)',
                        'required': False,
                        'default': 7
                    },
                    'source': {
                        'type': 'string',
                        'description': 'Data source: arxiv, ssrn, nber, or all (default all)',
                        'required': False,
                        'default': 'all'
                    }
                },
                'handler': self._papers_report
            },
            'sse_index': {
                'description': 'Get Shanghai Stock Exchange Composite Index (000001.SS) historical data',
                'parameters': {
                    'days': {
                        'type': 'integer',
                        'description': 'Number of days of historical data (default 30)',
                        'required': False,
                        'default': 30
                    }
                },
                'handler': self._sse_index
            },
            'sse_margin': {
                'description': 'Get Shanghai Stock Exchange margin trading data (simulated)',
                'parameters': {},
                'handler': self._sse_margin
            },
            'sse_northbound': {
                'description': 'Get Stock Connect northbound flow data (mainland → HK → A-shares)',
                'parameters': {
                    'days': {
                        'type': 'integer',
                        'description': 'Number of days to analyze (default 10)',
                        'required': False,
                        'default': 10
                    }
                },
                'handler': self._sse_northbound
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
    
    # EM Sovereign Spread Monitor handlers (Phase 158)
    def _em_embi_global(self) -> Dict:
        """Handler for em_embi_global tool"""
        return get_embi_global()
    
    def _em_regional_spreads(self) -> Dict:
        """Handler for em_regional_spreads tool"""
        return get_regional_spreads()
    
    def _em_credit_quality(self) -> Dict:
        """Handler for em_credit_quality tool"""
        return get_credit_quality_spreads()
    
    def _em_spread_history(self, series_id: str = "BAMLEMRECRPIUSEYGEY", days: int = 365) -> Dict:
        """Handler for em_spread_history tool"""
        return get_spread_history(series_id, days)
    
    def _em_comprehensive_report(self) -> Dict:
        """Handler for em_comprehensive_report tool"""
        return get_comprehensive_em_report()
    
    # EM Currency Crisis Monitor handlers (Phase 184)
    def _em_fx_reserves(self, country: str) -> Dict:
        """Handler for em_fx_reserves tool"""
        return get_fx_reserves(country)
    
    def _em_current_account(self, country: str) -> Dict:
        """Handler for em_current_account tool"""
        return get_current_account(country)
    
    def _em_reer(self, country: str) -> Dict:
        """Handler for em_reer tool"""
        return get_reer(country)
    
    def _em_crisis_risk(self, country: str) -> Dict:
        """Handler for em_crisis_risk tool"""
        return calculate_crisis_risk_score(country)
    
    def _em_regional_crisis_overview(self, region: str = 'all') -> Dict:
        """Handler for em_regional_crisis_overview tool"""
        results = get_regional_crisis_overview(region)
        return {
            'success': True,
            'region': region,
            'countries': results,
            'count': len(results)
        }
    
    # Crypto Exchange Flow Monitor handlers (Phase 185)
    def _crypto_exchange_flows(self, limit: int = 10) -> Dict:
        """Handler for crypto_exchange_flows tool"""
        from crypto_exchange_flow import get_exchange_flows
        return get_exchange_flows(limit)
    
    def _crypto_exchange_netflow(self, exchange_id: str, days: int = 7) -> Dict:
        """Handler for crypto_exchange_netflow tool"""
        from crypto_exchange_flow import get_exchange_netflow
        return get_exchange_netflow(exchange_id, days)
    
    def _crypto_whale_movements(self, min_value_usd: float = 1000000) -> Dict:
        """Handler for crypto_whale_movements tool"""
        from crypto_exchange_flow import get_whale_movements
        return get_whale_movements(min_value_usd)
    
    def _crypto_exchange_tvl(self) -> Dict:
        """Handler for crypto_exchange_tvl tool"""
        from crypto_exchange_flow import get_exchange_tvl
        return get_exchange_tvl()
    
    def _crypto_exchange_dominance(self) -> Dict:
        """Handler for crypto_exchange_dominance tool"""
        from crypto_exchange_flow import get_exchange_dominance
        return get_exchange_dominance()
    
    # DeFi TVL & Yield Aggregator handlers (Phase 186)
    def _defi_global_tvl(self) -> Dict:
        """Handler for defi_global_tvl tool"""
        result = get_global_tvl()
        if 'error' in result:
            return {'success': False, 'error': result['error']}
        return {'success': True, 'data': result}
    
    def _defi_protocol_tvl(self, protocol: str) -> Dict:
        """Handler for defi_protocol_tvl tool"""
        result = get_protocol_tvl(protocol)
        if 'error' in result:
            return {'success': False, 'error': result['error']}
        return {'success': True, 'data': result}
    
    def _defi_all_protocols(self) -> Dict:
        """Handler for defi_all_protocols tool"""
        result = get_all_protocols()
        if 'error' in result:
            return {'success': False, 'error': result['error']}
        return {'success': True, 'data': result}
    
    def _defi_chain_tvl(self, chain: str) -> Dict:
        """Handler for defi_chain_tvl tool"""
        result = get_chain_tvl(chain)
        if 'error' in result:
            return {'success': False, 'error': result['error']}
        return {'success': True, 'data': result}
    
    def _defi_chains_tvl(self) -> Dict:
        """Handler for defi_chains_tvl tool"""
        result = get_chains_tvl()
        if 'error' in result:
            return {'success': False, 'error': result['error']}
        return {'success': True, 'data': result}
    
    def _defi_yield_pools(self, chain: Optional[str] = None, min_tvl: float = 1000000) -> Dict:
        """Handler for defi_yield_pools tool"""
        result = get_yield_pools(chain=chain, min_tvl=min_tvl)
        if 'error' in result:
            return {'success': False, 'error': result['error']}
        return {'success': True, 'data': result}
    
    def _defi_stablecoin_yields(self, min_apy: float = 0) -> Dict:
        """Handler for defi_stablecoin_yields tool"""
        result = get_stablecoin_yields(min_apy=min_apy)
        if 'error' in result:
            return {'success': False, 'error': result['error']}
        return {'success': True, 'data': result}
    
    def _defi_protocol_yields(self, protocol: str) -> Dict:
        """Handler for defi_protocol_yields tool"""
        result = get_protocol_yields(protocol)
        if 'error' in result:
            return {'success': False, 'error': result['error']}
        return {'success': True, 'data': result}
    
    def _defi_tvl_rankings(self, category: Optional[str] = None, top_n: int = 25) -> Dict:
        """Handler for defi_tvl_rankings tool"""
        result = get_tvl_rankings(category=category, top_n=top_n)
        if 'error' in result:
            return {'success': False, 'error': result['error']}
        return {'success': True, 'data': result}
    
    def _defi_dashboard(self) -> Dict:
        """Handler for defi_dashboard tool"""
        result = get_defi_dashboard()
        if 'error' in result:
            return {'success': False, 'error': result['error']}
        return {'success': True, 'data': result}
    
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
    
    # Phase 181 handlers - Global FX Rates
    def _fx_rate(self, base: str, target: str, source: str = 'auto') -> Dict:
        """Handler for fx_rate tool"""
        result = get_fx_rate(base, target, source=source)
        return result
    
    def _fx_all_rates(self, base: str = 'USD') -> Dict:
        """Handler for fx_all_rates tool"""
        result = get_all_rates(base=base)
        return result
    
    def _fx_cross_rate(self, currency1: str, currency2: str, via: str = 'USD') -> Dict:
        """Handler for fx_cross_rate tool"""
        result = get_cross_rate(currency1, currency2, via=via)
        return result
    
    def _fx_matrix(self, currencies: List[str]) -> Dict:
        """Handler for fx_matrix tool"""
        result = get_fx_matrix(currencies)
        return result
    
    def _fx_convert(self, amount: float, from_currency: str, to_currency: str) -> Dict:
        """Handler for fx_convert tool"""
        result = convert_currency(amount, from_currency, to_currency)
        return result
    
    def _fx_strongest_weakest(self, base: str = 'USD', period: str = '1D') -> Dict:
        """Handler for fx_strongest_weakest tool"""
        result = get_strongest_weakest(base=base, period=period)
        return result
    
    def _fx_list_currencies(self) -> Dict:
        """Handler for fx_list_currencies tool"""
        result = list_supported_currencies()
        return result
    
    # Phase 156 handlers - Corporate Bond Spreads
    def _corporate_ig_spreads(self, days_back: int = 365) -> Dict:
        """Handler for corporate_ig_spreads tool"""
        return get_ig_spreads(days_back=days_back)
    
    def _corporate_hy_spreads(self, days_back: int = 365) -> Dict:
        """Handler for corporate_hy_spreads tool"""
        return get_hy_spreads(days_back=days_back)
    
    def _corporate_sector_spreads(self, sector: Optional[str] = None, days_back: int = 365) -> Dict:
        """Handler for corporate_sector_spreads tool"""
        return get_sector_spreads(sector=sector, days_back=days_back)
    
    def _corporate_ig_vs_hy(self, days_back: int = 365) -> Dict:
        """Handler for corporate_ig_vs_hy tool"""
        return compare_ig_vs_hy(days_back=days_back)
    
    def _corporate_spreads_by_maturity(self, days_back: int = 365) -> Dict:
        """Handler for corporate_spreads_by_maturity tool"""
        return get_spreads_by_maturity(days_back=days_back)
    
    def _corporate_credit_dashboard(self, days_back: int = 365) -> Dict:
        """Handler for corporate_credit_dashboard tool"""
        return get_credit_risk_dashboard(days_back=days_back)
    
    def _corporate_spread_trends(self, days_back: int = 90) -> Dict:
        """Handler for corporate_spread_trends tool"""
        return analyze_spread_trends(days_back=days_back)
    
    # Phase 157 handlers
    def _hy_spreads(self) -> Dict:
        """Handler for hy_spreads tool"""
        from modules.high_yield_bonds import get_hy_spreads
        result = get_hy_spreads()
        return {'success': True, 'data': result}
    
    def _distressed_debt(self) -> Dict:
        """Handler for distressed_debt tool"""
        from modules.high_yield_bonds import get_distressed_debt
        result = get_distressed_debt()
        return {'success': True, 'data': result}
    
    def _default_rates(self) -> Dict:
        """Handler for default_rates tool"""
        from modules.high_yield_bonds import get_default_rates
        result = get_default_rates()
        return {'success': True, 'data': result}
    
    def _hy_dashboard(self) -> Dict:
        """Handler for hy_dashboard tool"""
        from modules.high_yield_bonds import get_hy_dashboard
        result = get_hy_dashboard()
        return {'success': True, 'data': result}
    
    # CLO/ABS Market Monitor Handler Methods (Phase 163)
    def _clo_market_overview(self, days_back: int = 365) -> Dict:
        """Handler for clo_market_overview tool"""
        return get_clo_market_overview(days_back=days_back)
    
    def _abs_spreads_by_asset_class(self, asset_class: Optional[str] = None, days_back: int = 365) -> Dict:
        """Handler for abs_spreads_by_asset_class tool"""
        return get_abs_spreads_by_asset_class(asset_class=asset_class, days_back=days_back)
    
    def _cmbs_market_metrics(self, days_back: int = 365) -> Dict:
        """Handler for cmbs_market_metrics tool"""
        return get_cmbs_market_metrics(days_back=days_back)
    
    def _structured_finance_issuance(self, days_back: int = 730) -> Dict:
        """Handler for structured_finance_issuance tool"""
        return get_structured_finance_issuance(days_back=days_back)
    
    def _abs_delinquency_rates(self, days_back: int = 365) -> Dict:
        """Handler for abs_delinquency_rates tool"""
        return get_delinquency_rates(days_back=days_back)
    
    def _abs_liquidity_indicators(self, days_back: int = 365) -> Dict:
        """Handler for abs_liquidity_indicators tool"""
        return get_abs_liquidity_indicators(days_back=days_back)
    
    def _clo_abs_dashboard(self, days_back: int = 365) -> Dict:
        """Handler for clo_abs_dashboard tool"""
        return get_comprehensive_clo_abs_dashboard(days_back=days_back)
    
    def _abs_credit_quality(self, asset_class: str, days_back: int = 365) -> Dict:
        """Handler for abs_credit_quality tool"""
        return analyze_abs_credit_quality(asset_class=asset_class, days_back=days_back)
    
    def _nport_clo_abs_holdings(self, cik: Optional[str] = None, limit: int = 10) -> Dict:
        """Handler for nport_clo_abs_holdings tool"""
        return get_sec_nport_clo_abs_holdings(cik=cik, limit=limit)
    
    # Municipal Bond Monitor Handler Methods (Phase 155)
    def _muni_search(self, issuer_name: Optional[str] = None, state: Optional[str] = None,
                     cusip: Optional[str] = None, min_size: Optional[float] = None) -> Dict:
        """Handler for muni_search tool"""
        return search_muni_bonds(issuer_name=issuer_name, state=state, cusip=cusip, min_size=min_size)
    
    def _muni_trades(self, cusip: Optional[str] = None, state: Optional[str] = None,
                     days_back: int = 7, min_trade_size: Optional[float] = None) -> Dict:
        """Handler for muni_trades tool"""
        return get_recent_trades(cusip=cusip, state=state, days_back=days_back, min_trade_size=min_trade_size)
    
    def _muni_issuer(self, issuer_name: str) -> Dict:
        """Handler for muni_issuer tool"""
        return get_issuer_profile(issuer_name)
    
    def _muni_credit_events(self, state: Optional[str] = None, event_type: Optional[str] = None,
                            days_back: int = 30) -> Dict:
        """Handler for muni_credit_events tool"""
        return get_credit_events(state=state, event_type=event_type, days_back=days_back)
    
    def _muni_state_summary(self, state_code: str) -> Dict:
        """Handler for muni_state_summary tool"""
        return get_state_summary(state_code)
    
    def _muni_yield_curve(self, state: Optional[str] = None, rating: str = 'AAA') -> Dict:
        """Handler for muni_yield_curve tool"""
        return get_yield_curve(state=state, rating=rating)
    
    def _muni_compare_spreads(self, state1: str, state2: str, maturity_years: int = 10) -> Dict:
        """Handler for muni_compare_spreads tool"""
        return compare_spreads(state1, state2, maturity_years)
    
    # Money Market Fund Flows Handler Methods (Phase 168)
    def _mmf_aggregate_flows(self, months_back: int = 12) -> Dict:
        """Handler for mmf_aggregate_flows tool"""
        return get_mmf_aggregate_flows(months_back=months_back)
    
    def _mmf_sec_filings(self, cik: Optional[str] = None, fund_family: Optional[str] = None,
                         count: int = 20) -> Dict:
        """Handler for mmf_sec_filings tool"""
        return get_sec_mmf_filings(cik=cik, fund_family=fund_family, count=count)
    
    def _mmf_parse_filing(self, accession_number: str) -> Dict:
        """Handler for mmf_parse_filing tool"""
        return parse_nmfp_filing(accession_number)
    
    def _mmf_current_yields(self, fund_type: Optional[str] = None) -> Dict:
        """Handler for mmf_current_yields tool"""
        return get_mmf_yields(fund_type=fund_type)
    
    def _mmf_concentration_risk(self) -> Dict:
        """Handler for mmf_concentration_risk tool"""
        return get_mmf_concentration_risk()
    
    def _mmf_category_comparison(self, months_back: int = 6) -> Dict:
        """Handler for mmf_category_comparison tool"""
        return compare_mmf_categories(months_back=months_back)
    
    # Sovereign Rating Tracker Handler Methods (Phase 164)
    def _sovereign_ratings(self, days: int = 180) -> Dict:
        """Handler for sovereign_ratings tool"""
        from modules.sovereign_rating_tracker import get_all_ratings
        result = get_all_ratings(days)
        return {'success': True, 'data': result}
    
    def _sovereign_country(self, country: str) -> Dict:
        """Handler for sovereign_country tool"""
        from modules.sovereign_rating_tracker import get_country_ratings
        result = get_country_ratings(country)
        return {'success': True, 'data': result}
    
    def _sovereign_downgrades(self, days: int = 90) -> Dict:
        """Handler for sovereign_downgrades tool"""
        from modules.sovereign_rating_tracker import get_downgrades
        result = get_downgrades(days)
        return {'success': True, 'data': result}
    
    def _sovereign_upgrades(self, days: int = 90) -> Dict:
        """Handler for sovereign_upgrades tool"""
        from modules.sovereign_rating_tracker import get_upgrades
        result = get_upgrades(days)
        return {'success': True, 'data': result}
    
    def _sovereign_watch_list(self) -> Dict:
        """Handler for sovereign_watch_list tool"""
        from modules.sovereign_rating_tracker import get_watch_list
        result = get_watch_list()
        return {'success': True, 'data': result}
    
    def _sovereign_ig_changes(self, days: int = 180) -> Dict:
        """Handler for sovereign_ig_changes tool"""
        from modules.sovereign_rating_tracker import get_investment_grade_changes
        result = get_investment_grade_changes(days)
        return {'success': True, 'data': result}
    
    def _sovereign_dashboard(self) -> Dict:
        """Handler for sovereign_dashboard tool"""
        from modules.sovereign_rating_tracker import get_rating_dashboard
        result = get_rating_dashboard()
        return {'success': True, 'data': result}
    
    # Swap Rate Curves Handler Methods (Phase 160)
    def _usd_swap_curve(self) -> Dict:
        """Handler for usd_swap_curve tool"""
        from modules.swap_rate_curves import get_usd_swap_curve
        return get_usd_swap_curve()
    
    def _eur_swap_curve(self) -> Dict:
        """Handler for eur_swap_curve tool"""
        from modules.swap_rate_curves import get_eur_swap_curve
        return get_eur_swap_curve()
    
    def _compare_swap_curves(self) -> Dict:
        """Handler for compare_swap_curves tool"""
        from modules.swap_rate_curves import compare_usd_eur_curves
        return compare_usd_eur_curves()
    
    def _swap_spread(self, tenor: str = "10Y", currency: str = "USD") -> Dict:
        """Handler for swap_spread tool"""
        from modules.swap_rate_curves import get_swap_spread
        return get_swap_spread(tenor, currency)
    
    def _swap_inversion_signal(self) -> Dict:
        """Handler for swap_inversion_signal tool"""
        from modules.swap_rate_curves import get_curve_inversion_signal
        return get_curve_inversion_signal()
    
    # Treasury Yield Curve Handlers (Phase 154)
    def _treasury_yield_curve(self, format_table: bool = False) -> Dict:
        """Handler for treasury_yield_curve tool"""
        return get_current_curve(format_table=format_table)
    
    def _treasury_yield_history(self, start_date: Optional[str] = None, 
                               end_date: Optional[str] = None, 
                               days_back: int = 90) -> Dict:
        """Handler for treasury_yield_history tool"""
        return get_historical_curve(start_date=start_date, end_date=end_date, days_back=days_back)
    
    def _treasury_yield_analyze(self, curve_data: Optional[Dict] = None) -> Dict:
        """Handler for treasury_yield_analyze tool"""
        return analyze_curve_shape(curve_data=curve_data)
    
    def _treasury_yield_compare(self, date1: Optional[str] = None, 
                               date2: Optional[str] = None, 
                               days_back: int = 30) -> Dict:
        """Handler for treasury_yield_compare tool"""
        return compare_curves(date1=date1, date2=date2, days_back=days_back)
    
    def _treasury_yield_maturity(self, maturity: str, days_back: int = 365) -> Dict:
        """Handler for treasury_yield_maturity tool"""
        return get_specific_maturity(maturity=maturity, days_back=days_back)
    
    # TIPS & Breakeven Inflation Handlers (Phase 159)
    def _tips_current(self, include_inflation: bool = True) -> Dict:
        """Handler for tips_current tool"""
        return get_current_tips_data(include_inflation=include_inflation)
    
    def _breakeven_curve(self, format_table: bool = False) -> Dict:
        """Handler for breakeven_curve tool"""
        return analyze_breakeven_curve(format_table=format_table)
    
    def _real_yield_history(self, maturity: str = '10Y', days_back: int = 365) -> Dict:
        """Handler for real_yield_history tool"""
        return get_real_yield_history(maturity=maturity, days_back=days_back)
    
    def _tips_vs_nominal(self, maturity: str = '10Y') -> Dict:
        """Handler for tips_vs_nominal tool"""
        return compare_tips_vs_nominal(maturity=maturity)
    
    def _inflation_expectations(self) -> Dict:
        """Handler for inflation_expectations tool"""
        return get_inflation_expectations_summary()
    
    def _breakeven_changes(self, days_back: int = 30) -> Dict:
        """Handler for breakeven_changes tool"""
        return track_breakeven_changes(days_back=days_back)
    
    # Inflation-Linked Bonds Handlers (Phase 167)
    def _global_linker_summary(self) -> Dict:
        """Handler for global_linker_summary tool"""
        return get_global_linker_summary()
    
    def _us_tips_yields(self, maturities: Optional[List[str]] = None) -> Dict:
        """Handler for us_tips_yields tool"""
        return get_us_tips_yields(maturities=maturities)
    
    def _euro_linker_yields(self) -> Dict:
        """Handler for euro_linker_yields tool"""
        return get_euro_linker_yields()
    
    def _uk_gilt_yields(self) -> Dict:
        """Handler for uk_gilt_yields tool"""
        return get_uk_gilt_yields()
    
    def _compare_linker_yields(self, region1: str = 'US', region2: str = 'EURO') -> Dict:
        """Handler for compare_linker_yields tool"""
        return compare_linker_yields(region1=region1, region2=region2)
    
    def _linker_history(self, region: str = 'US', maturity: str = '10Y', days_back: int = 365) -> Dict:
        """Handler for linker_history tool"""
        return get_linker_history(region=region, maturity=maturity, days_back=days_back)
    
    def _real_yield_trends(self, days_back: int = 30) -> Dict:
        """Handler for real_yield_trends tool"""
        return analyze_real_yield_trends(days_back=days_back)
    
    # Commercial Paper Rates Handlers (Phase 162)
    def _cp_current_rates(self) -> Dict:
        """Handler for cp_current_rates tool"""
        return get_current_rates()
    
    def _cp_rate_history(self, days: int = 90, category: Optional[str] = None) -> Dict:
        """Handler for cp_rate_history tool"""
        return get_rate_history(days=days, category=category)
    
    def _cp_spread_analysis(self, days: int = 90) -> Dict:
        """Handler for cp_spread_analysis tool"""
        return analyze_spreads(days=days)
    
    def _cp_rate_comparison(self) -> Dict:
        """Handler for cp_rate_comparison tool"""
        return get_rate_comparison()
    
    def _cp_dashboard(self) -> Dict:
        """Handler for cp_dashboard tool"""
        return get_cp_dashboard()
    
    # Bond New Issue Calendar Handlers (Phase 165)
    def _bond_upcoming_issues(self, days_back: int = 30, min_amount_millions: float = 100) -> Dict:
        """Handler for bond_upcoming_issues tool"""
        return get_upcoming_issues(days_back=days_back, min_amount_millions=min_amount_millions)
    
    def _bond_issuer_history(self, ticker_or_cik: str, years: int = 2) -> Dict:
        """Handler for bond_issuer_history tool"""
        return get_issuer_history(ticker_or_cik=ticker_or_cik, years=years)
    
    def _bond_company_filings(self, cik: str, count: int = 20) -> Dict:
        """Handler for bond_company_filings tool"""
        return get_company_filings(cik=cik, count=count)
    
    def _bond_analyze_filing(self, cik: str, accession_number: str) -> Dict:
        """Handler for bond_analyze_filing tool"""
        return analyze_filing_content(cik=cik, accession_number=accession_number)
    
    def _bond_dashboard(self) -> Dict:
        """Handler for bond_dashboard tool"""
        return get_bond_dashboard()
    
    # Central Bank Rate Decisions Handlers (Phase 166)
    def _central_bank_rate(self, bank_code: str) -> Dict:
        """Handler for central_bank_rate tool"""
        return get_central_bank_rate(bank_code.upper())
    
    def _central_bank_all_rates(self) -> Dict:
        """Handler for central_bank_all_rates tool"""
        return get_all_central_bank_rates()
    
    def _central_bank_compare(self, bank_codes: List[str]) -> Dict:
        """Handler for central_bank_compare tool"""
        return compare_central_banks([code.upper() for code in bank_codes])
    
    def _central_bank_heatmap(self) -> Dict:
        """Handler for central_bank_heatmap tool"""
        return get_global_rate_heatmap()
    
    def _central_bank_search(self, query: str) -> Dict:
        """Handler for central_bank_search tool"""
        return search_central_banks(query)
    
    def _central_bank_differential(self, bank_code_1: str, bank_code_2: str) -> Dict:
        """Handler for central_bank_differential tool"""
        return get_rate_differential(bank_code_1.upper(), bank_code_2.upper())
    
    def _central_bank_list(self) -> Dict:
        """Handler for central_bank_list tool"""
        return list_all_banks()
    
    # FX Carry Trade Monitor Handlers (Phase 182)
    def _fx_carry_opportunities(self, min_differential: float = 1.0) -> Dict:
        """Handler for fx_carry_opportunities tool"""
        try:
            opportunities = get_carry_trade_opportunities(min_differential=min_differential)
            return {
                'success': True,
                'opportunities': opportunities,
                'count': len(opportunities)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _fx_carry_differential(self, currency1: str, currency2: str) -> Dict:
        """Handler for fx_carry_differential tool"""
        try:
            result = fx_get_rate_differential(currency1.upper(), currency2.upper())
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
    
    def _fx_carry_dashboard(self) -> Dict:
        """Handler for fx_carry_dashboard tool"""
        try:
            dashboard = get_fx_carry_dashboard()
            return {
                'success': True,
                'data': dashboard
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _fx_carry_funding(self, n: int = 3) -> Dict:
        """Handler for fx_carry_funding tool"""
        try:
            funding = get_top_funding_currencies(n=n)
            return {
                'success': True,
                'currencies': funding,
                'count': len(funding)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _fx_carry_investment(self, n: int = 3) -> Dict:
        """Handler for fx_carry_investment tool"""
        try:
            investment = get_top_investment_currencies(n=n)
            return {
                'success': True,
                'currencies': investment,
                'count': len(investment)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # Gold & Precious Metals Handlers (Phase 171)
    def _gold_prices(self) -> Dict:
        """Handler for gold_prices tool"""
        try:
            result = get_all_metals_prices()
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _gold_etf_holdings(self) -> Dict:
        """Handler for gold_etf_holdings tool"""
        try:
            result = get_all_etf_holdings()
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _gold_silver_ratio(self) -> Dict:
        """Handler for gold_silver_ratio tool"""
        try:
            result = calculate_gold_silver_ratio()
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _gold_performance(self, period: str = '1y') -> Dict:
        """Handler for gold_performance tool"""
        try:
            result = get_metals_performance(period)
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _gold_wgc_summary(self) -> Dict:
        """Handler for gold_wgc_summary tool"""
        try:
            result = get_world_gold_council_summary()
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _gold_comprehensive_report(self) -> Dict:
        """Handler for gold_comprehensive_report tool"""
        try:
            result = get_comprehensive_metals_report()
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # Industrial Metals Handlers (Phase 172)
    def _copper_price(self) -> Dict:
        """Handler for copper_price tool"""
        return get_copper_price()
    
    def _aluminum_price(self) -> Dict:
        """Handler for aluminum_price tool"""
        return get_aluminum_price()
    
    def _zinc_price(self) -> Dict:
        """Handler for zinc_price tool"""
        return get_zinc_price()
    
    def _nickel_price(self) -> Dict:
        """Handler for nickel_price tool"""
        return get_nickel_price()
    
    def _metal_inventories(self) -> Dict:
        """Handler for metal_inventories tool"""
        return get_metal_inventories()
    
    def _metals_snapshot(self) -> Dict:
        """Handler for metals_snapshot tool"""
        return get_metals_snapshot()
    
    def _metals_correlation(self) -> Dict:
        """Handler for metals_correlation tool"""
        return get_metals_correlation()
    
    # Crude Oil Fundamentals Handlers (Phase 169)
    def _crude_oil_stocks(self, weeks: int = 52) -> Dict:
        """Handler for crude_oil_stocks tool"""
        return get_eia_crude_stocks(weeks=weeks)
    
    def _crude_oil_cushing(self) -> Dict:
        """Handler for crude_oil_cushing tool"""
        return get_eia_cushing_stocks()
    
    def _crude_oil_spr(self) -> Dict:
        """Handler for crude_oil_spr tool"""
        return get_eia_spr_levels()
    
    def _crude_oil_production(self) -> Dict:
        """Handler for crude_oil_production tool"""
        return get_eia_production()
    
    def _crude_oil_trade(self) -> Dict:
        """Handler for crude_oil_trade tool"""
        return get_eia_trade_flows()
    
    def _crude_oil_refinery(self) -> Dict:
        """Handler for crude_oil_refinery tool"""
        return get_eia_refinery_operations()
    
    def _opec_production(self) -> Dict:
        """Handler for opec_production tool"""
        return scrape_opec_momr_production()
    
    def _opec_spare_capacity(self) -> Dict:
        """Handler for opec_spare_capacity tool"""
        return get_opec_spare_capacity()
    
    def _us_vs_opec(self) -> Dict:
        """Handler for us_vs_opec tool"""
        return compare_us_vs_opec()
    
    def _crude_oil_dashboard(self) -> Dict:
        """Handler for crude_oil_dashboard tool"""
        return get_crude_oil_fundamentals_dashboard()
    
    def _crude_oil_weekly_report(self) -> Dict:
        """Handler for crude_oil_weekly_report tool"""
        return get_weekly_oil_report()
    
    # Natural Gas Supply/Demand Handlers (Phase 170)
    def _natural_gas_storage(self, weeks: int = 52) -> Dict:
        """Handler for natural_gas_storage tool"""
        return get_weekly_storage_report(weeks=weeks)
    
    def _natural_gas_production(self, months: int = 12) -> Dict:
        """Handler for natural_gas_production tool"""
        return get_production_data(months=months)
    
    def _natural_gas_demand(self, months: int = 12) -> Dict:
        """Handler for natural_gas_demand tool"""
        return get_demand_data(months=months)
    
    def _natural_gas_balance(self, months: int = 12) -> Dict:
        """Handler for natural_gas_balance tool"""
        return get_supply_demand_balance(months=months)
    
    def _natural_gas_series(self, series_key: str, limit: int = 5000) -> Dict:
        """Handler for natural_gas_series tool"""
        return fetch_eia_series(series_key, limit=limit)
    
    def _natural_gas_list_series(self) -> Dict:
        """Handler for natural_gas_list_series tool"""
        return natural_gas_list_series()
    
    # LNG & Gas Market Tracker Handlers (Phase 176)
    def _lng_prices(self, days: int = 90) -> Dict:
        """Handler for lng_prices tool"""
        return lng_get_lng_prices(days=days)
    
    def _lng_price_summary(self) -> Dict:
        """Handler for lng_price_summary tool"""
        return lng_get_lng_price_summary()
    
    def _lng_trade_flows(self) -> Dict:
        """Handler for lng_trade_flows tool"""
        return lng_get_lng_trade_flows()
    
    def _lng_exporters(self) -> Dict:
        """Handler for lng_exporters tool"""
        return lng_get_lng_exporters()
    
    def _lng_importers(self) -> Dict:
        """Handler for lng_importers tool"""
        return lng_get_lng_importers()
    
    def _lng_terminals(self) -> Dict:
        """Handler for lng_terminals tool"""
        return lng_get_lng_terminals()
    
    def _lng_terminal_detail(self, terminal_id: str) -> Dict:
        """Handler for lng_terminal_detail tool"""
        return lng_get_terminal_by_name(terminal_id)
    
    def _lng_market_summary(self) -> Dict:
        """Handler for lng_market_summary tool"""
        return lng_get_lng_market_summary()
    
    # Rare Earths & Strategic Minerals Handlers (Phase 178)
    def _mineral_profile(self, mineral: str) -> Dict:
        """Handler for mineral_profile tool"""
        return get_mineral_profile(mineral)
    
    def _supply_risk_score(self, mineral: str) -> Dict:
        """Handler for supply_risk_score tool"""
        return calculate_supply_risk_score(mineral)
    
    def _supply_risk_rankings(self) -> Dict:
        """Handler for supply_risk_rankings tool"""
        return {'rankings': get_supply_risk_rankings()}
    
    def _sector_exposure(self, sector: str) -> Dict:
        """Handler for sector_exposure tool"""
        return get_sector_exposure(sector)
    
    def _country_production_profile(self, country: str) -> Dict:
        """Handler for country_production_profile tool"""
        return get_country_production_profile(country)
    
    def _rare_earths_detailed(self) -> Dict:
        """Handler for rare_earths_detailed tool"""
        return get_rare_earths_detailed()
    
    def _minerals_comprehensive_report(self) -> Dict:
        """Handler for minerals_comprehensive_report tool"""
        return get_comprehensive_minerals_report()
    
    def _list_critical_minerals(self) -> Dict:
        """Handler for list_critical_minerals tool"""
        return {
            'available_minerals': list(PRODUCTION_DATA.keys()),
            'critical_minerals': CRITICAL_MINERALS,
            'strategic_categories': STRATEGIC_CATEGORIES
        }
    
    # Patent Tracking Handlers (Phase 11)
    def _patent_search(self, company_name: str, years: int = 5, limit: int = 100) -> Dict:
        """Handler for patent_search tool"""
        return search_patents_by_company(company_name, years, limit)
    
    def _patent_compare(self, companies: List[str], years: int = 5) -> Dict:
        """Handler for patent_compare tool"""
        return patent_compare_companies(companies, years)
    
    def _patent_trends(self, company: str, years: int = 10) -> Dict:
        """Handler for patent_trends tool"""
        return patent_trend_analysis(company, years)
    
    def _patent_industry_leaders(self, industry: str, limit: int = 10) -> Dict:
        """Handler for patent_industry_leaders tool"""
        return get_industry_leaders(industry, limit)
    
    # Semiconductor Chip Data Handlers (Phase 195)
    def _get_semiconductor_sales(self, region: str = "all", months: int = 12) -> Dict:
        """Handler for get_semiconductor_sales tool"""
        return get_chip_sales(region, months)
    
    def _get_chip_forecast(self, horizon: str = "yearly") -> Dict:
        """Handler for get_chip_forecast tool"""
        return get_chip_forecast(horizon)
    
    def _get_fab_utilization(self, granularity: str = "industry") -> Dict:
        """Handler for get_fab_utilization tool"""
        return get_fab_utilization(granularity)
    
    def _get_chip_market_summary(self) -> Dict:
        """Handler for get_chip_market_summary tool"""
        return get_chip_market_summary()
    
    # Repo Rate Monitor Handlers (Phase 161)
    def _repo_sofr_rates(self, days_back: int = 90) -> Dict:
        """Handler for repo_sofr_rates tool"""
        return get_sofr_rates(days_back=days_back)
    
    def _repo_rates(self, days_back: int = 90) -> Dict:
        """Handler for repo_rates tool"""
        return get_repo_rates(days_back=days_back)
    
    def _repo_reverse_repo_operations(self, days_back: int = 90) -> Dict:
        """Handler for repo_reverse_repo_operations tool"""
        return get_reverse_repo_operations(days_back=days_back)
    
    def _repo_overnight_rates_dashboard(self, days_back: int = 90) -> Dict:
        """Handler for repo_overnight_rates_dashboard tool"""
        return get_overnight_rates_dashboard(days_back=days_back)
    
    def _repo_compare_money_market_rates(self, days_back: int = 90) -> Dict:
        """Handler for repo_compare_money_market_rates tool"""
        return compare_money_market_rates(days_back=days_back)
    
    def _repo_funding_stress_indicators(self) -> Dict:
        """Handler for repo_funding_stress_indicators tool"""
        return get_funding_stress_indicators()
    
    # Agricultural Commodities Handlers (Phase 173)
    def _ag_futures_all(self) -> Dict:
        """Handler for ag_futures_all tool"""
        return get_all_futures()
    
    def _ag_futures_commodity(self, commodity: str) -> Dict:
        """Handler for ag_futures_commodity tool"""
        commodity = commodity.upper()
        if commodity not in FUTURES_SYMBOLS:
            return {
                'success': False,
                'error': f'Unknown commodity: {commodity}. Available: {", ".join(FUTURES_SYMBOLS.keys())}'
            }
        symbol_info = FUTURES_SYMBOLS[commodity]
        price_data = get_yahoo_futures_price(symbol_info['symbol'])
        if not price_data['success']:
            return price_data
        return {
            'success': True,
            'commodity': commodity,
            'name': symbol_info['name'],
            'symbol': symbol_info['symbol'],
            'exchange': symbol_info['exchange'],
            'current_price': price_data['current_price'],
            'change': price_data['change'],
            'change_pct': price_data['change_pct'],
            'unit': symbol_info['unit'],
            'contract_size': symbol_info['contract_size'],
            'market_time': price_data['market_time'],
            'historical': price_data.get('historical', [])
        }
    
    def _ag_grains(self) -> Dict:
        """Handler for ag_grains tool"""
        return get_grain_futures()
    
    def _ag_softs(self) -> Dict:
        """Handler for ag_softs tool"""
        return get_soft_commodities()
    
    def _ag_usda_crop(self, commodity: str, metric: str = 'PRODUCTION', year: Optional[int] = None) -> Dict:
        """Handler for ag_usda_crop tool"""
        return get_usda_crop_data(commodity.upper(), metric.upper(), year)
    
    def _ag_dashboard(self, commodity: str) -> Dict:
        """Handler for ag_dashboard tool"""
        return get_commodity_dashboard(commodity.upper())
    
    def _ag_list_commodities(self) -> Dict:
        """Handler for ag_list_commodities tool"""
        return list_commodities()
    
    # OPEC Production Monitor Handlers (Phase 175)
    def _opec_production(self) -> Dict:
        """Handler for opec_production tool"""
        return get_opec_production_latest()
    
    def _opec_summary(self) -> Dict:
        """Handler for opec_summary tool"""
        return get_opec_summary()
    
    def _opec_country(self, country: str) -> Dict:
        """Handler for opec_country tool"""
        return get_country_production(country)
    
    def _opec_compliance(self) -> Dict:
        """Handler for opec_compliance tool"""
        return get_compliance_report()
    
    def _opec_quotas(self, months: int = 12) -> Dict:
        """Handler for opec_quotas tool"""
        return {'quota_changes': get_quota_changes(months)}
    
    # Carbon Credits & Emissions Handlers (Phase 177)
    def _eu_ets_price_history(self, days: int = 365) -> Dict:
        """Handler for eu_ets_price_history tool"""
        return get_eu_ets_price_history(days)
    
    def _global_carbon_prices(self) -> Dict:
        """Handler for global_carbon_prices tool"""
        return get_global_carbon_prices()
    
    def _carbon_market_statistics(self) -> Dict:
        """Handler for carbon_market_statistics tool"""
        return get_carbon_market_statistics()
    
    def _emissions_by_sector(self, jurisdiction: str = 'EU') -> Dict:
        """Handler for emissions_by_sector tool"""
        return get_emissions_by_sector(jurisdiction)
    
    def _compare_carbon_markets(self, markets: Optional[List[str]] = None) -> Dict:
        """Handler for compare_carbon_markets tool"""
        return compare_carbon_markets(markets)
    
    def _carbon_offset_projects(self, project_type: Optional[str] = None) -> Dict:
        """Handler for carbon_offset_projects tool"""
        return get_carbon_offset_projects(project_type)
    
    # Container Port Throughput Handlers (Phase 193)
    def _port_throughput(self, port: str = 'all') -> Dict:
        """Handler for port_throughput tool"""
        return get_port_throughput(port)
    
    def _port_compare(self) -> Dict:
        """Handler for port_compare tool"""
        return port_compare_ports()
    
    def _port_list(self) -> Dict:
        """Handler for port_list tool"""
        return get_port_list()
    
    def _port_rankings(self) -> Dict:
        """Handler for port_rankings tool"""
        return get_global_port_rankings()
    
    # CFTC COT Reports Handlers (Phase 180)
    def _cot_latest(self, report_type: str = 'legacy') -> Dict:
        """Handler for cot_latest tool"""
        return get_latest_cot_report(report_type)
    
    def _cot_contract(self, contract_code: str, weeks: int = 52) -> Dict:
        """Handler for cot_contract tool"""
        return get_cot_by_contract(contract_code, weeks)
    
    def _cot_extremes(self, report_type: str = 'legacy') -> Dict:
        """Handler for cot_extremes tool"""
        return get_cot_extremes(report_type)
    
    def _cot_summary(self) -> Dict:
        """Handler for cot_summary tool"""
        return get_cot_summary()
    
    def _cot_divergence(self) -> Dict:
        """Handler for cot_divergence tool"""
        return get_commercial_vs_spec_divergence()
    
    def _cot_dashboard(self) -> Dict:
        """Handler for cot_dashboard tool"""
        return get_cot_dashboard()
    
    # FX Volatility Surface Handlers (Phase 183)
    def _fx_volatility_surface(self, pair: str) -> Dict:
        """Handler for fx_volatility_surface tool"""
        try:
            result = get_volatility_surface(pair.upper())
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
    
    def _fx_risk_reversals(self, pair: str) -> Dict:
        """Handler for fx_risk_reversals tool"""
        try:
            result = get_risk_reversals(pair.upper())
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
    
    def _fx_butterflies(self, pair: str) -> Dict:
        """Handler for fx_butterflies tool"""
        try:
            result = get_butterflies(pair.upper())
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
    
    def _fx_vol_summary(self) -> Dict:
        """Handler for fx_vol_summary tool"""
        try:
            result = get_all_pairs_summary()
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
    
    # Livestock & Meat Markets Handlers (Phase 174)
    def _livestock_futures_all(self) -> Dict:
        """Handler for livestock_futures_all tool"""
        return get_all_livestock_futures()
    
    def _livestock_futures_specific(self, livestock: str) -> Dict:
        """Handler for livestock_futures_specific tool"""
        livestock = livestock.upper()
        if livestock not in LIVESTOCK_FUTURES:
            return {
                'success': False,
                'error': f'Unknown livestock: {livestock}. Available: {", ".join(LIVESTOCK_FUTURES.keys())}'
            }
        info = LIVESTOCK_FUTURES[livestock]
        price_data = get_yahoo_futures_price(info['symbol'])
        if not price_data['success']:
            return price_data
        return {
            'success': True,
            'livestock': livestock,
            'name': info['name'],
            'symbol': info['symbol'],
            'exchange': info['exchange'],
            'current_price': price_data['current_price'],
            'change': price_data['change'],
            'change_pct': price_data['change_pct'],
            'unit': info['unit'],
            'contract_size': info['contract_size'],
            'description': info['description'],
            'market_time': price_data['market_time'],
            'historical': price_data.get('historical', [])
        }
    
    def _livestock_cattle(self) -> Dict:
        """Handler for livestock_cattle tool"""
        return get_cattle_prices()
    
    def _livestock_hogs(self) -> Dict:
        """Handler for livestock_hogs tool"""
        return get_hog_prices()
    
    def _livestock_slaughter(self) -> Dict:
        """Handler for livestock_slaughter tool"""
        return get_slaughter_data()
    
    def _livestock_ams_report(self, slug: str, date: Optional[str] = None) -> Dict:
        """Handler for livestock_ams_report tool"""
        return get_ams_report(slug, date)
    
    def _livestock_dashboard(self) -> Dict:
        """Handler for livestock_dashboard tool"""
        return get_livestock_dashboard()
    
    def _livestock_list_reports(self) -> Dict:
        """Handler for livestock_list_reports tool"""
        return list_ams_reports()
    
    def _crypto_funding_rates(self, symbol: str) -> Dict:
        """Handler for crypto_funding_rates tool"""
        try:
            result = get_funding_rates(symbol.upper())
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _crypto_futures_basis(self, symbol: str) -> Dict:
        """Handler for crypto_futures_basis tool"""
        try:
            result = get_futures_basis(symbol.upper())
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _crypto_open_interest(self, symbol: str, exchanges: Optional[List[str]] = None) -> Dict:
        """Handler for crypto_open_interest tool"""
        try:
            result = get_open_interest(symbol.upper(), exchanges)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _crypto_funding_arbitrage(self, min_spread: float = 0.5) -> Dict:
        """Handler for crypto_funding_arbitrage tool"""
        try:
            result = scan_funding_arbitrage(min_spread)
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _crypto_derivatives_snapshot(self, symbols: Optional[List[str]] = None) -> Dict:
        """Handler for crypto_derivatives_snapshot tool"""
        try:
            if symbols:
                symbols = [s.upper() for s in symbols]
            result = get_market_snapshot(symbols)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # Stablecoin Supply Monitor Handlers (Phase 187)
    def _stablecoin_all(self) -> Dict:
        """Handler for stablecoin_all tool"""
        try:
            result = get_all_stablecoins()
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _stablecoin_detail(self, stablecoin_id: str) -> Dict:
        """Handler for stablecoin_detail tool"""
        try:
            result = get_stablecoin_detail(stablecoin_id)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _stablecoin_chain(self, chain: str) -> Dict:
        """Handler for stablecoin_chain tool"""
        try:
            result = get_chain_stablecoins(chain)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _stablecoin_mint_burn(self, stablecoin_id: str, days: int = 30) -> Dict:
        """Handler for stablecoin_mint_burn tool"""
        try:
            result = analyze_mint_burn_events(stablecoin_id, days)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _stablecoin_dominance(self) -> Dict:
        """Handler for stablecoin_dominance tool"""
        try:
            result = get_stablecoin_dominance()
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # Global Electricity Demand Handler Methods (Phase 191)
    def _electricity_entsoe_load(self, area_code: str, start_date: str = None, end_date: str = None) -> Dict:
        """Handler for electricity_entsoe_load tool"""
        try:
            result = get_entsoe_load(area_code, start_date, end_date)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _electricity_entsoe_forecast(self, area_code: str, start_date: str = None, end_date: str = None) -> Dict:
        """Handler for electricity_entsoe_forecast tool"""
        try:
            result = get_entsoe_forecast(area_code, start_date, end_date)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _electricity_europe_aggregate(self, start_date: str = None, end_date: str = None) -> Dict:
        """Handler for electricity_europe_aggregate tool"""
        try:
            result = get_europe_aggregate_load(start_date, end_date)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _electricity_eia_demand(self, sector: str = 'total', months: int = 12) -> Dict:
        """Handler for electricity_eia_demand tool"""
        try:
            result = get_eia_demand(sector, months)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _electricity_us_generation_mix(self) -> Dict:
        """Handler for electricity_us_generation_mix tool"""
        try:
            result = get_us_generation_mix()
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _electricity_caiso_load(self, days: int = 7) -> Dict:
        """Handler for electricity_caiso_load tool"""
        try:
            result = get_caiso_load(days)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _electricity_caiso_renewables(self) -> Dict:
        """Handler for electricity_caiso_renewables tool"""
        try:
            result = get_caiso_renewables()
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _electricity_global_dashboard(self) -> Dict:
        """Handler for electricity_global_dashboard tool"""
        try:
            result = get_global_demand_dashboard()
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _electricity_compare_regions(self, regions: List[str] = None) -> Dict:
        """Handler for electricity_compare_regions tool"""
        try:
            result = compare_regional_demand(regions)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # Cross-Chain Bridge Monitor Handler Methods (Phase 190)
    def _bridge_list(self, limit: int = 10, min_tvl: float = 1000000) -> Dict:
        """Handler for bridge_list tool"""
        try:
            result = get_top_bridges(limit=limit, min_tvl=min_tvl)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _bridge_details(self, bridge_id: str) -> Dict:
        """Handler for bridge_details tool"""
        try:
            result = get_bridge_details(bridge_id)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _bridge_volume(self, bridge_id: str, days: int = 7) -> Dict:
        """Handler for bridge_volume tool"""
        try:
            result = get_bridge_volume(bridge_id, days=days)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _bridge_risk(self, bridge_id: str) -> Dict:
        """Handler for bridge_risk tool"""
        try:
            result = calculate_bridge_risk_score(bridge_id)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _bridge_flow(self, bridge_id: str, days: int = 30) -> Dict:
        """Handler for bridge_flow tool"""
        try:
            result = get_flow_analysis(bridge_id, days=days)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _bridge_report(self, bridge_id: str) -> Dict:
        """Handler for bridge_report tool"""
        try:
            result = get_comprehensive_bridge_report(bridge_id)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # NFT Market Tracker Handler Methods (Phase 189)
    def _nft_collection_stats(self, collection_slug: str) -> Dict:
        """Handler for nft_collection_stats tool"""
        try:
            result = get_collection_stats(collection_slug)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _nft_top_collections(self, limit: int = 20) -> Dict:
        """Handler for nft_top_collections tool"""
        try:
            result = get_top_collections(limit=min(limit, 50))
            if result and isinstance(result, list) and len(result) > 0 and 'error' in result[0]:
                return {'success': False, 'error': result[0]['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _nft_wash_trading(self, collection_slug: str) -> Dict:
        """Handler for nft_wash_trading_detection tool"""
        try:
            result = detect_wash_trading(collection_slug)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _nft_market_overview(self) -> Dict:
        """Handler for nft_market_overview tool"""
        try:
            result = get_nft_market_overview()
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _nft_compare_collections(self, collection_slugs: List[str]) -> Dict:
        """Handler for nft_compare_collections tool"""
        try:
            result = compare_collections(collection_slugs)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _nft_collection_history(self, collection_slug: str, days: int = 30) -> Dict:
        """Handler for nft_collection_history tool"""
        try:
            result = get_collection_history(collection_slug, days=days)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # Airport Traffic & Aviation Handler Methods (Phase 192)
    def _airport_operations(self, airport_code: str, days: int = 30) -> Dict:
        """Handler for airport_operations tool"""
        try:
            result = get_airport_operations(airport_code, days)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _airline_capacity_index(self) -> Dict:
        """Handler for airline_capacity_index tool"""
        try:
            result = get_airline_capacity_index()
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _flight_delay_index(self, region: str = 'US') -> Dict:
        """Handler for flight_delay_index tool"""
        try:
            result = get_flight_delay_index(region)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _regional_traffic_comparison(self) -> Dict:
        """Handler for regional_traffic_comparison tool"""
        try:
            result = compare_regional_traffic()
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _aviation_economic_dashboard(self) -> Dict:
        """Handler for aviation_economic_dashboard tool"""
        try:
            result = get_aviation_economic_dashboard()
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _list_airports(self) -> Dict:
        """Handler for list_airports tool"""
        try:
            result = list_airports()
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # Global Tourism Statistics Handler Methods (Phase 194)
    def _tourism_arrivals(self, country_code: str = 'WLD') -> Dict:
        """Handler for tourism_arrivals tool"""
        try:
            result = get_international_arrivals(country_code.upper())
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _tourism_receipts(self, country_code: str = 'WLD') -> Dict:
        """Handler for tourism_receipts tool"""
        try:
            result = get_tourism_receipts(country_code.upper())
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _tourism_country_profile(self, country_code: str) -> Dict:
        """Handler for tourism_country_profile tool"""
        try:
            result = get_country_tourism_profile(country_code.upper())
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _tourism_global_overview(self) -> Dict:
        """Handler for tourism_global_overview tool"""
        try:
            result = get_global_tourism_overview()
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _tourism_compare_countries(self, country1: str, country2: str) -> Dict:
        """Handler for tourism_compare_countries tool"""
        try:
            result = compare_tourism_countries(country1.upper(), country2.upper())
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _hotel_occupancy(self) -> Dict:
        """Handler for hotel_occupancy tool"""
        try:
            result = get_us_hotel_occupancy()
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _airline_passengers(self) -> Dict:
        """Handler for airline_passengers tool"""
        try:
            result = get_airline_passenger_data()
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _tourism_recovery_tracker(self) -> Dict:
        """Handler for tourism_recovery_tracker tool"""
        try:
            result = get_tourism_recovery_tracker()
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # Auto Sales & EV Registrations Handler Methods (Phase 196)
    def _get_auto_sales(self, country: str = 'US', months: int = 12) -> Dict:
        """Handler for get_auto_sales tool"""
        try:
            if country.upper() == 'US':
                result = get_us_auto_sales(months)
            else:
                result = {'error': f'Country {country} not supported yet. Currently only US supported.'}
            
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_ev_registrations(self, country: str = 'US', months: int = 12) -> Dict:
        """Handler for get_ev_registrations tool"""
        try:
            result = get_ev_registrations(country.upper(), months)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_auto_market_share(self, region: str = 'US', months: int = 12) -> Dict:
        """Handler for get_auto_market_share tool"""
        try:
            result = get_auto_market_share(region.upper(), months)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_comprehensive_auto_report(self, months: int = 12) -> Dict:
        """Handler for comprehensive_auto_report tool"""
        try:
            result = get_comprehensive_auto_report(months)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # Bankruptcy Tracker Handler Methods (Phase 197)
    def _search_bankruptcy_filings(self, days: int = 30, limit: int = 50) -> Dict:
        """Handler for search_bankruptcy_filings tool"""
        try:
            result = search_bankruptcy_filings(days=days, limit=limit)
            return {'success': True, 'data': result, 'count': len(result)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_bankruptcy_tracker(self, ticker: str) -> Dict:
        """Handler for get_bankruptcy_tracker tool"""
        try:
            result = get_company_bankruptcy_status(ticker)
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_bankruptcy_stats(self, sector: Optional[str] = None, year: Optional[int] = None) -> Dict:
        """Handler for get_bankruptcy_stats tool"""
        try:
            result = get_bankruptcy_statistics(sector=sector, year=year)
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # PE & VC Deal Flow Handler Methods (Phase 198)
    def _get_vc_deals(self, days_back: int = 30, min_amount: float = 1.0, 
                      max_results: int = 20, stage: Optional[str] = None) -> Dict:
        """Handler for get_vc_deals tool"""
        try:
            result = get_vc_deals(
                days_back=days_back,
                min_amount=min_amount,
                max_results=max_results,
                stage=stage
            )
            return {'success': True, 'deals': result, 'count': len(result)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_pe_deals(self, days_back: int = 30, min_amount: float = 50.0,
                      max_results: int = 20, deal_type: Optional[str] = None) -> Dict:
        """Handler for get_pe_deals tool"""
        try:
            result = get_pe_deals(
                days_back=days_back,
                min_amount=min_amount,
                max_results=max_results,
                deal_type=deal_type
            )
            return {'success': True, 'deals': result, 'count': len(result)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _search_form_d(self, days_back: int = 30, min_amount: Optional[float] = None,
                       max_results: int = 50, keywords: Optional[str] = None) -> Dict:
        """Handler for search_form_d tool"""
        try:
            result = search_form_d_filings(
                days_back=days_back,
                min_amount=min_amount,
                max_results=max_results,
                keywords=keywords
            )
            return {'success': True, 'filings': result, 'count': len(result)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _deal_flow_summary(self, days_back: int = 30) -> Dict:
        """Handler for deal_flow_summary tool"""
        try:
            result = get_deal_flow_summary(days_back=days_back)
            return {'success': True, 'summary': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # Global Health Impact Monitor Handler Methods (Phase 199)
    def _get_health_outbreaks(self, country: Optional[str] = None, 
                              disease: Optional[str] = None, 
                              days: int = 90) -> Dict:
        """Handler for get_health_outbreaks tool"""
        try:
            result = get_health_outbreaks(country=country, disease=disease, days=days)
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_pandemic_impact(self, metric: str = 'all', 
                            country: str = 'US',
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> Dict:
        """Handler for get_pandemic_impact tool"""
        try:
            result = get_pandemic_impact(
                metric=metric,
                country=country,
                start_date=start_date,
                end_date=end_date
            )
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_health_monitor(self, region: str = 'global', 
                           alert_threshold: str = 'MEDIUM') -> Dict:
        """Handler for get_health_monitor tool"""
        try:
            result = get_health_monitor(region=region, alert_threshold=alert_threshold)
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # Academic Finance Paper Tracker Handler Methods (Phase 200)
    def _papers_latest(self, source: str = 'all', days: int = 7, 
                      keywords: Optional[str] = None, max_results: int = 20) -> Dict:
        """Handler for papers_latest tool"""
        try:
            result = get_latest_papers(
                source=source,
                days=days,
                keywords=keywords,
                max_results=max_results
            )
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _papers_search(self, query: str, source: str = 'all', max_results: int = 20) -> Dict:
        """Handler for papers_search tool"""
        try:
            result = search_papers(
                query=query,
                source=source,
                max_results=max_results
            )
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _papers_trending(self, period: str = 'week', source: str = 'ssrn', max_results: int = 20) -> Dict:
        """Handler for papers_trending tool"""
        try:
            result = get_trending_papers(
                period=period,
                source=source,
                max_results=max_results
            )
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _papers_by_author(self, author_name: str, source: str = 'all', max_results: int = 20) -> Dict:
        """Handler for papers_by_author tool"""
        try:
            result = search_by_author(
                author_name=author_name,
                source=source,
                max_results=max_results
            )
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _papers_report(self, format_type: str = 'summary', days: int = 7, source: str = 'all') -> Dict:
        """Handler for papers_report tool"""
        try:
            result = generate_report(
                format_type=format_type,
                days=days,
                source=source
            )
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
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
    
    # Bank of Israel Dashboard Handler Methods (Phase 629)
    def _boi_dashboard(self) -> Dict:
        """Handler for boi_dashboard tool"""
        return boi_get_dashboard()
    
    def _boi_policy_rate(self) -> Dict:
        """Handler for boi_policy_rate tool"""
        rate = boi_get_policy_rate()
        from datetime import datetime
        return {"policy_rate_pct": rate, "updated": datetime.now().isoformat()}
    
    def _boi_fx_reserves(self) -> Dict:
        """Handler for boi_fx_reserves tool"""
        return boi_get_fx_reserves()
    
    def _boi_exchange_rates(self) -> Dict:
        """Handler for boi_exchange_rates tool"""
        return boi_get_exchange_rates()
    
    def _boi_inflation(self) -> Dict:
        """Handler for boi_inflation tool"""
        return boi_get_inflation_data()
    
    def _boi_policy_history(self, months: int = 24) -> Dict:
        """Handler for boi_policy_history tool"""
        return {"history": boi_get_policy_history(months)}
    
    # TASE Handler Methods (Phase 631)
    def _tase_ta35_index(self, period: str = '1d') -> Dict:
        """Handler for tase_ta35_index tool"""
        return fetch_ta35_index(period)
    
    def _tase_stock(self, symbol: str, period: str = '1d') -> Dict:
        """Handler for tase_stock tool"""
        return fetch_israeli_stock(symbol, period)
    
    def _tase_market_summary(self) -> Dict:
        """Handler for tase_market_summary tool"""
        return tase_get_market_summary()
    
    def _tase_sector_performance(self) -> Dict:
        """Handler for tase_sector_performance tool"""
        sectors = tase_fetch_sector_performance()
        return {"sectors": sectors, "count": len(sectors)}
    
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
    
    def _sse_index(self, days: int = 30) -> Dict:
        """Handler for sse_index tool"""
        try:
            result = get_sse_index(days=days)
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _sse_margin(self) -> Dict:
        """Handler for sse_margin tool"""
        try:
            result = get_margin_trading()
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _sse_northbound(self, days: int = 10) -> Dict:
        """Handler for sse_northbound tool"""
        try:
            result = get_northbound_flow(days=days)
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
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
