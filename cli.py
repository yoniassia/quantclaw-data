#!/usr/bin/env python3
"""
QUANTCLAW DATA CLI
Central dispatcher for all quantitative data modules
"""

import sys
import subprocess
from pathlib import Path

MODULES_DIR = Path(__file__).parent / "modules"

# Module registry
MODULES = {
    'cds': {
        'file': 'cds_spreads.py',
        'commands': ['sovereign-spreads', 'corporate-spreads', 'spread-compare', 'credit-risk-score']
    },
    'pairs': {
        'file': 'pairs_trading.py',
        'commands': ['pairs-scan', 'cointegration', 'spread-monitor']
    },
    'sector': {
        'file': 'sector_rotation.py',
        'commands': ['sector-rotation', 'sector-momentum', 'economic-cycle']
    },
    'monte_carlo': {
        'file': 'monte_carlo.py',
        'commands': ['monte-carlo', 'var', 'scenario']
    },
    'backtest': {
        'file': 'backtesting_engine.py',
        'commands': ['backtest', 'backtest-strategies', 'backtest-optimize', 'backtest-walkforward', 
                     'backtest-compare', 'backtest-report', 'backtest-history']
    },
    'volatility_surface': {
        'file': 'volatility_surface.py',
        'commands': ['iv-smile', 'vol-arbitrage', 'straddle-scan', 'strangle-scan']
    },
    'black_litterman': {
        'file': 'black_litterman.py',
        'commands': ['black-litterman', 'equilibrium-returns', 'portfolio-optimize']
    },
    'walk_forward': {
        'file': 'walk_forward.py',
        'commands': ['walk-forward', 'overfit-check', 'param-stability']
    },
    'kalman': {
        'file': 'kalman_filter.py',
        'commands': ['kalman', 'adaptive-ma', 'regime-detect']
    },
    'kostat': {
        'file': 'kostat.py',
        'commands': ['kostat-gdp', 'kostat-cpi', 'kostat-dashboard']
    },
    'multi_timeframe': {
        'file': 'multi_timeframe.py',
        'commands': ['mtf', 'trend-alignment', 'signal-confluence']
    },
    'alerts': {
        'file': 'smart_alerts.py',
        'commands': ['alert-create', 'alert-list', 'alert-check', 'alert-delete', 'alert-history', 'alert-stats']
    },
    'alpha_picker': {
        'file': 'alpha_picker.py',
        'commands': ['alpha-score', 'alpha-picks', 'alpha-validate', 'alpha-scan', 'alpha-top-momentum']
    },
    'sa_quant': {
        'file': 'sa_quant_replica.py',
        'commands': ['sa-score', 'sa-strong-buys', 'sa-validate', 'sa-backtest']
    },
    'order_book': {
        'file': 'order_book.py',
        'commands': ['order-book', 'bid-ask', 'liquidity', 'imbalance', 'support-resistance']
    },
    'options_flow': {
        'file': 'options_flow_scanner.py',
        'commands': ['options-flow-scan', 'options-flow-market', 'options-flow-darkpool']
    },
    'paper_trading': {
        'file': 'paper_trading.py',
        'commands': ['paper-create', 'paper-buy', 'paper-sell', 'paper-positions', 'paper-pnl', 
                     'paper-trades', 'paper-orders', 'paper-cancel', 'paper-risk', 'paper-snapshot', 'paper-chart']
    },
    'live_paper_trading': {
        'file': 'live_paper_trading.py',
        'commands': ['paper-run', 'paper-status', 'paper-history']
    },
    'alert_dsl': {
        'file': 'alert_dsl.py',
        'commands': ['dsl-eval', 'dsl-scan', 'dsl-help']
    },
    'alert_backtest': {
        'file': 'alert_backtest.py',
        'commands': ['alert-backtest', 'signal-quality', 'alert-potential']
    },
    'commodity_futures': {
        'file': 'commodity_futures.py',
        'commands': ['futures-curve', 'contango', 'roll-yield', 'term-structure']
    },
    'industrial_metals': {
        'file': 'industrial_metals.py',
        'commands': ['copper-price', 'aluminum-price', 'zinc-price', 'nickel-price', 'metal-inventories', 'metals-snapshot', 'metals-correlation']
    },
    'crude_oil': {
        'file': 'crude_oil_fundamentals.py',
        'commands': ['stocks', 'cushing', 'spr', 'production', 'trade', 'refinery', 'opec-production', 'spare-capacity', 'us-vs-opec', 'dashboard', 'weekly-report']
    },
    'natural_gas': {
        'file': 'natural_gas_supply_demand.py',
        'commands': ['ng-storage', 'ng-production', 'ng-demand', 'ng-balance', 'ng-series', 'ng-list']
    },
    'lng_gas': {
        'file': 'lng_gas.py',
        'commands': ['lng-prices', 'lng-summary', 'lng-trade-flows', 'lng-exporters', 'lng-importers', 'lng-terminals', 'lng-terminal', 'lng-market-overview']
    },
    'satellite': {
        'file': 'satellite_proxies.py',
        'commands': ['satellite-proxy', 'shipping-index', 'construction-activity', 'foot-traffic', 'economic-index']
    },
    'nighttime_lights': {
        'file': 'nighttime_lights_satellite.py',
        'commands': ['lights-country', 'lights-region', 'lights-compare', 'lights-trend']
    },
    'fed_policy': {
        'file': 'fed_policy.py',
        'commands': ['fed-watch', 'rate-probability', 'fomc-calendar', 'dot-plot', 'yield-curve', 'current-rate']
    },
    'em_sovereign_spreads': {
        'file': 'em_sovereign_spreads.py',
        'commands': ['embi-global', 'regional-spreads', 'credit-quality', 'spread-history', 'em-report']
    },
    'tips_breakeven': {
        'file': 'tips_breakeven.py',
        'commands': ['tips-current', 'breakeven-curve', 'real-yield-history', 'tips-vs-nominal', 'inflation-expectations', 'breakeven-changes']
    },
    'inflation_linked_bonds': {
        'file': 'inflation_linked_bonds.py',
        'commands': ['global-summary', 'us-tips', 'euro-linkers', 'uk-gilts', 'compare', 'history', 'trends']
    },
    'central_bank_rates': {
        'file': 'central_bank_rates.py',
        'commands': ['cb-all-rates', 'cb-rate', 'cb-compare', 'cb-heatmap', 'cb-search', 'cb-differential', 'cb-list']
    },
    'fx_carry_trade': {
        'file': 'fx_carry_trade.py',
        'commands': ['carry-opportunities', 'carry-differential', 'carry-dashboard', 'carry-funding', 'carry-investment']
    },
    'fx_volatility_surface': {
        'file': 'fx_volatility_surface.py',
        'commands': ['fx-vol-surface', 'fx-risk-reversal', 'fx-butterfly', 'fx-vol-summary']
    },
    'em_currency_crisis': {
        'file': 'em_currency_crisis.py',
        'commands': ['em-fx-reserves', 'em-current-account', 'em-reer', 'em-crisis-risk', 'em-regional-overview']
    },
    'crypto_onchain': {
        'file': 'crypto_onchain.py',
        'commands': ['onchain', 'whale-watch', 'dex-volume', 'gas-fees', 'token-flows']
    },
    'nft_market': {
        'file': 'nft_market.py',
        'commands': ['collection-stats', 'top-collections', 'wash-trading', 'market-overview', 'compare-collections', 'collection-history']
    },
    'earnings_nlp': {
        'file': 'earnings_nlp.py',
        'commands': ['dodge-detect']
    },
    'product_launches': {
        'file': 'product_launches.py',
        'commands': ['launch-summary', 'buzz-tracking', 'reddit-sentiment', 'news-coverage', 'preorder-velocity', 'trending-products']
    },
    'revenue_quality': {
        'file': 'revenue_quality.py',
        'commands': ['revenue-quality', 'dso-trends', 'channel-stuffing', 'cash-flow-divergence']
    },
    'earnings_quality': {
        'file': 'earnings_quality.py',
        'commands': ['earnings-quality', 'accruals-trend', 'fraud-indicators']
    },
    'quality_factor': {
        'file': 'quality_factor_scoring.py',
        'commands': ['quality-score', 'quality-screen']
    },
    'patent': {
        'file': 'patent_tracking.py',
        'commands': ['patent-search', 'patent-compare', 'patent-trends', 'industry-leaders']
    },
    'peer_network': {
        'file': 'peer_network.py',
        'commands': ['peer-network', 'compare-networks', 'map-dependencies']
    },
    'political_risk': {
        'file': 'political_risk.py',
        'commands': ['geopolitical-events', 'sanctions-search', 'regulatory-changes', 'country-risk']
    },
    'executive_comp': {
        'file': 'exec_compensation.py',
        'commands': ['exec-comp', 'pay-performance', 'comp-peer-compare', 'shareholder-alignment']
    },
    'peer_earnings': {
        'file': 'peer_earnings.py',
        'commands': ['peer-earnings', 'beat-miss-history', 'guidance-tracker', 'estimate-dispersion']
    },
    'estimate_revision': {
        'file': 'estimate_revision_tracker.py',
        'commands': ['recommendations', 'revisions', 'velocity', 'targets', 'summary']
    },
    'analyst_targets': {
        'file': 'analyst_target_price.py',
        'commands': ['analyst-consensus', 'analyst-recs', 'analyst-revisions', 'analyst-summary', 'analyst-compare']
    },
    'tax_loss_harvesting': {
        'file': 'tax_loss_harvesting.py',
        'commands': ['tlh-scan', 'wash-sale-check', 'tax-savings', 'tlh-replacements']
    },
    'crypto_correlation': {
        'file': 'crypto_correlation.py',
        'commands': ['btc-dominance', 'altcoin-season', 'defi-tvl-correlation', 'crypto-equity-corr']
    },
    'defi_tvl_yield': {
        'file': 'defi_tvl_yield.py',
        'commands': ['global-tvl', 'protocol', 'all-protocols', 'chain', 'chains', 'yields', 'stable-yields', 'protocol-yields', 'rankings', 'dashboard']
    },
    'crypto_exchange_flow': {
        'file': 'crypto_exchange_flow.py',
        'commands': ['exchange-flows', 'exchange-netflow', 'whale-movements', 'exchange-tvl', 'exchange-dominance']
    },
    'cdp_carbon': {
        'file': 'cdp_carbon_disclosure.py',
        'commands': ['cdp-epa', 'cdp-eprtr', 'cdp-sec', 'cdp-footprint']
    },
    'crypto_derivatives': {
        'file': 'crypto_derivatives.py',
        'commands': ['funding', 'basis', 'oi', 'arb-scan', 'snapshot']
    },
    'cross_chain_bridge': {
        'file': 'cross_chain_bridge_monitor.py',
        'commands': ['bridge-list', 'bridge-details', 'bridge-volume', 'bridge-risk', 'bridge-flow', 'bridge-report']
    },
    'airport_traffic_aviation': {
        'file': 'airport_traffic_aviation.py',
        'commands': ['airport-operations', 'airline-capacity', 'flight-delays', 'regional-traffic', 'aviation-dashboard', 'airport-list']
    },
    'auto_sales_ev': {
        'file': 'auto_sales_ev.py',
        'commands': ['auto-sales', 'ev-registrations', 'auto-market', 'comprehensive-report']
    },
    'dividend_sustainability': {
        'file': 'dividend_sustainability.py',
        'commands': ['dividend-health', 'payout-ratio', 'fcf-coverage', 'dividend-cut-risk']
    },
    'dividend_history': {
        'file': 'dividend_history.py',
        'commands': ['div-history', 'div-growth', 'div-calendar', 'div-project', 'div-aristocrat', 'div-compare']
    },
    'share_buyback': {
        'file': 'share_buyback.py',
        'commands': ['buyback-analysis', 'share-count-trend', 'buyback-yield', 'dilution-impact']
    },
    'institutional_ownership': {
        'file': 'institutional_ownership.py',
        'commands': ['13f-changes', 'whale-accumulation', 'top-holders', 'smart-money']
    },
    'insider_heatmap': {
        'file': 'insider_transaction_heatmap.py',
        'commands': ['insider-summary', 'insider-sector', 'insider-ticker']
    },
    'share_float': {
        'file': 'share_float_and_ownership_structure.py',
        'commands': ['ownership-summary', 'insider-detail', 'institutional-detail', 'float-analysis', 'compare', 'scan-low-float']
    },
    'index_reconstitution': {
        'file': 'index_reconstitution_tracker.py',
        'commands': ['sp500-changes', 'russell-calendar', 'russell-candidates', 'msci-schedule', 'analyze-opportunity', 'historical-stats']
    },
    'relative_valuation': {
        'file': 'relative_valuation.py',
        'commands': ['valuation-heatmap', 'valuation-sector', 'valuation-stock', 'valuation-peers', 'valuation-screen', 'valuation-sectors']
    },
    'adr_gdr': {
        'file': 'adr_gdr_arbitrage.py',
        'commands': ['adr-spread', 'adr-scan', 'adr-compare', 'adr-list']
    },
    'short_squeeze': {
        'file': 'short_squeeze.py',
        'commands': ['squeeze-scan', 'squeeze-score', 'short-interest', 'days-to-cover']
    },
    'stock_loan': {
        'file': 'stock_loan_borrow_costs.py',
        'commands': ['stock-loan', 'threshold-list', 'htb-scan', 'borrow-compare']
    },
    'corporate_actions': {
        'file': 'corporate_actions.py',
        'commands': ['corporate-calendar', 'split-history', 'dividend-calendar', 'spinoff-tracker']
    },
    'stock_split_events': {
        'file': 'stock_split_corporate_events.py',
        'commands': ['stock-split-history', 'stock-split-impact', 'stock-corporate-actions', 'stock-compare-splits']
    },
    'etf_flow': {
        'file': 'etf_flow_tracker.py',
        'commands': ['etf-flows', 'flow-signals', 'top-flows', 'sector-flows']
    },
    'dark_pool': {
        'file': 'dark_pool.py',
        'commands': ['dark-pool-volume', 'block-trades', 'institutional-accumulation', 'off-exchange-ratio']
    },
    'market_regime': {
        'file': 'market_regime.py',
        'commands': ['market-regime', 'regime-history', 'risk-dashboard', 'correlation-regime']
    },
    'correlation_anomaly': {
        'file': 'correlation_anomaly.py',
        'commands': ['corr-breakdown', 'corr-scan', 'corr-regime', 'corr-arbitrage']
    },
    'convertible_bonds': {
        'file': 'convertible_bonds.py',
        'commands': ['convertible-scan', 'conversion-premium', 'convertible-arb', 'convertible-greeks']
    },
    'slb': {
        'file': 'slb.py',
        'commands': ['slb-market', 'slb-issuer', 'slb-kpi-tracker', 'slb-coupon-forecast']
    },
    'filing_alerts': {
        'file': 'filing_alerts.py',
        'commands': ['filing-alerts-recent', 'filing-alerts-search', 'filing-alerts-activists', 'filing-alerts-watch']
    },
    'proxy_fights': {
        'file': 'proxy_fights.py',
        'commands': ['proxy-filings', 'proxy-contests', 'proxy-voting', 'proxy-advisory', 'proxy-summary']
    },
    'activist_success': {
        'file': 'activist_success_predictor.py',
        'commands': ['activist-predict', 'activist-scan', 'activist-historical', 'activist-13d', 
                     'activist-history', 'activist-targets', 'governance-score']
    },
    'climate_risk': {
        'file': 'climate_risk.py',
        'commands': ['climate-risk', 'physical-risk', 'transition-risk', 'carbon-scenario']
    },
    'factor_timing': {
        'file': 'factor_timing.py',
        'commands': ['factor-timing', 'factor-rotation', 'factor-performance', 'factor-regime-history']
    },
    'ml_factor_discovery': {
        'file': 'ml_factor_discovery.py',
        'commands': ['discover-factors', 'factor-ic', 'factor-backtest', 'feature-importance']
    },
    'cross_exchange_arb': {
        'file': 'cross_exchange_arb.py',
        'commands': ['arb-scan', 'arb-spread', 'arb-history', 'exchange-latency']
    },
    'alert_dashboard': {
        'file': 'alert_dashboard.py',
        'commands': ['dashboard-backtest', 'dashboard-performance', 'dashboard-optimize', 'dashboard-report']
    },
    'sec_xbrl': {
        'file': 'sec_xbrl_financial_statements.py',
        'commands': ['financials', 'compare', 'search', 'cik']
    },
    'dcf': {
        'file': 'dcf_valuation.py',
        'commands': ['dcf', 'dcf-sensitivity', 'dcf-compare', 'dcf-quick']
    },
    'comparable_companies': {
        'file': 'comparable_companies.py',
        'commands': ['comp-metrics', 'comps-table', 'comp-compare', 'comp-sector', 'peer-groups']
    },
    'earnings_surprise_history': {
        'file': 'earnings_surprise_history.py',
        'commands': ['earnings-history', 'surprise-patterns', 'whisper-numbers', 'post-earnings-drift', 'earnings-quality-score', 'compare-surprises']
    },
    'pdf_exporter': {
        'file': 'pdf_exporter.py',
        'commands': ['export-pdf', 'batch-report', 'report-template']
    },
    'regulatory_calendar': {
        'file': 'regulatory_calendar.py',
        'commands': ['econ-calendar', 'event-reaction', 'event-volatility', 'event-backtest']
    },
    'ai_earnings': {
        'file': 'ai_earnings_analyzer.py',
        'commands': ['earnings-tone', 'confidence-score', 'language-shift', 'hedging-detector']
    },
    'mutual_fund_flow': {
        'file': 'mutual_fund_flow_analysis.py',
        'commands': ['fund-flows', 'compare-flows', 'sector-rotation', 'smart-money', 'fund-performance', 'n-port-filings']
    },
    'smart_prefetch': {
        'file': 'smart_prefetch.py',
        'commands': ['prefetch-stats', 'prefetch-warmup', 'cache-status', 'prefetch-config']
    },
    'data_reconciliation': {
        'file': 'data_reconciliation.py',
        'commands': ['reconcile-price', 'data-quality-report', 'source-reliability', 'discrepancy-log']
    },
    'live_earnings': {
        'file': 'live_earnings.py',
        'commands': ['calendar', 'status', 'simulate', 'transcribe']
    },
    'live_transcription': {
        'file': 'live_transcription.py',
        'commands': ['earnings-schedule', 'transcript-signals', 'earnings-countdown', 'transcript-compare']
    },
    'portfolio_construction': {
        'file': 'portfolio_construction.py',
        'commands': ['mpt-optimize', 'efficient-frontier', 'rebalance-plan', 'portfolio-risk']
    },
    'neural_prediction': {
        'file': 'neural_prediction.py',
        'commands': ['predict-price', 'prediction-confidence', 'model-comparison', 'prediction-backtest']
    },
    'deep_learning_sentiment': {
        'file': 'deep_learning_sentiment.py',
        'commands': ['finbert-earnings', 'finbert-sec', 'finbert-news', 'finbert-trend', 'finbert-compare']
    },
    'transaction_cost': {
        'file': 'transaction_cost.py',
        'commands': ['tca-spread', 'tca-impact', 'tca-shortfall', 'tca-optimize', 'tca-compare']
    },
    'imf_weo': {
        'file': 'imf_weo.py',
        'commands': ['imf-country', 'imf-compare', 'imf-global', 'imf-group', 'imf-projections', 'imf-search']
    },
    'worldbank': {
        'file': 'worldbank.py',
        'commands': ['country-profile', 'countries', 'indicator', 'compare', 'search', 'regional', 'indicators']
    },
    'global_pmi': {
        'file': 'global_pmi.py',
        'commands': ['pmi-country', 'pmi-global', 'pmi-compare', 'pmi-regional', 'pmi-divergence', 'pmi-search', 'pmi-list']
    },
    'census': {
        'file': 'census.py',
        'commands': ['retail-sales', 'housing-starts', 'building-permits', 'trade-deficit', 'economic-snapshot']
    },
    'eurostat': {
        'file': 'eurostat.py',
        'commands': ['eu-country-profile', 'eu-countries', 'eu-indicator', 'eu-compare', 'eu27-aggregate', 'eu-search', 'eu-indicators']
    },
    'bls': {
        'file': 'bls.py',
        'commands': ['cpi', 'ppi', 'employment', 'nfp', 'wages', 'productivity', 'inflation-summary', 'employment-summary', 'bls-dashboard']
    },
    'cia_factbook': {
        'file': 'cia_factbook.py',
        'commands': ['cia-factbook', 'cia-factbook-compare', 'cia-factbook-scan', 'cia-factbook-demographics', 'cia-factbook-military', 'cia-factbook-trade', 'cia-factbook-resources']
    },
    'comtrade': {
        'file': 'comtrade.py',
        'commands': ['reporters', 'partners', 'commodities', 'search-country', 'search-commodity', 'bilateral', 'top-partners', 'trade-balance', 'commodity-trade', 'concentration', 'dependencies']
    },
    'inegi': {
        'file': 'inegi.py',
        'commands': ['mx-snapshot', 'mx-indicator', 'mx-gdp', 'mx-inflation', 'mx-employment', 'mx-remittances', 'mx-trade', 'mx-compare', 'mx-indicators', 'mx-states']
    },
    'turkish_institute': {
        'file': 'turkish_institute.py',
        'commands': ['tuik-indicator', 'tuik-inflation', 'tuik-gdp', 'tuik-trade', 'tuik-unemployment', 'tuik-monetary', 'tuik-fx', 'tuik-snapshot', 'tuik-indicators']
    },
    'oecd': {
        'file': 'oecd.py',
        'commands': ['cli', 'housing', 'productivity', 'compare', 'snapshot', 'countries']
    },
    'oecd_mei': {
        'file': 'oecd_mei.py',
        'commands': ['mei-cpi', 'mei-ppi', 'mei-ipi', 'mei-unemp', 'mei-bci', 'mei-cci', 'mei-retail', 'mei-all', 'mei-snapshot']
    },
    'boj': {
        'file': 'boj.py',
        'commands': ['tankan', 'monetary-base', 'fx-reserves', 'rates', 'boj-watch', 'compare-fed', 'meeting-schedule']
    },
    'rbi': {
        'file': 'rbi.py',
        'commands': ['gdp', 'wpi', 'cpi', 'fx-reserves', 'repo-rate', 'india-watch', 'mpc-calendar', 'compare-brics']
    },
    'india_nso': {
        'file': 'india_nso.py',
        'commands': ['india-gdp', 'india-cpi', 'india-iip', 'india-labor', 'india-trade', 'india-stats']
    },
    'bcb': {
        'file': 'bcb.py',
        'commands': ['brazil-selic', 'brazil-ipca', 'brazil-gdp', 'brazil-trade-balance', 'brazil-dashboard', 'brazil-exchange-rate']
    },
    'saudi_arabia_gastat': {
        'file': 'saudi_arabia_gastat.py',
        'commands': ['saudi-gdp', 'saudi-cpi', 'saudi-oil', 'saudi-diversification', 'saudi-dashboard', 'saudi-gcc-compare', 'saudi-indicators']
    },
    'ecb': {
        'file': 'ecb.py',
        'commands': ['ecb-indicator', 'ecb-rates', 'ecb-fx', 'ecb-dashboard', 'ecb-indicators', 'ecb-countries']
    },
    'china_nbs': {
        'file': 'china_nbs.py',
        'commands': ['pmi', 'gdp', 'trade', 'fx-reserves', 'yuan', 'industrial', 'inflation', 'dashboard']
    },
    'kosis': {
        'file': 'kosis.py',
        'commands': ['korea-gdp', 'korea-cpi', 'korea-semiconductors', 'korea-trade', 'korea-bok-rate', 'korea-fx-reserves', 'korea-exchange-rate', 'korea-dashboard', 'korea-indicators', 'korea-semiconductor-breakdown']
    },
    'nigeria_nbs': {
        'file': 'nigeria_nbs.py',
        'commands': ['ng-snapshot', 'ng-gdp', 'ng-inflation', 'ng-oil', 'ng-trade', 'ng-indicator', 'ng-compare', 'ng-indicators']
    },
    'argentina_indec': {
        'file': 'argentina_indec.py',
        'commands': ['ar-snapshot', 'ar-indicator', 'ar-inflation', 'ar-gdp', 'ar-poverty', 'ar-trade', 'ar-employment', 'ar-production', 'ar-compare', 'ar-indicators']
    },
    'singapore_dos': {
        'file': 'singapore_dos.py',
        'commands': ['singapore-gdp', 'singapore-cpi', 'singapore-trade', 'singapore-mas', 'singapore-dashboard']
    },
    'mas_singapore': {
        'file': 'mas_singapore.py',
        'commands': ['mas-policy', 'mas-reserves', 'mas-banking', 'mas-indicators', 'mas-stability', 'mas-summary']
    },
    'fred_enhanced': {
        'file': 'fred_enhanced.py',
        'commands': ['fred-series', 'fred-yield-curve', 'fred-money-supply', 'fred-financial-conditions', 'fred-leading-indicators', 'fred-consumer-credit', 'fred-category', 'fred-snapshot', 'fred-categories', 'fred-search']
    },
    'global_bonds': {
        'file': 'global_bonds.py',
        'commands': ['list-countries', 'yield', 'compare', 'spreads', 'us-curve', 'us-real', 'us-breakeven', 'comprehensive']
    },
    'eia_energy': {
        'file': 'eia_energy.py',
        'commands': ['crude-inventories', 'spr', 'natgas-storage', 'refinery-util', 'gasoline', 'distillate', 'weekly-report', 'dashboard']
    },
    'swf': {
        'file': 'swf_tracker.py',
        'commands': ['swf-list', 'swf-country', 'swf-details', 'swf-top', 'swf-allocations', 'swf-sec-filers', 'swf-by-source', 'swf-compare', 'swf-search', 'swf-stats']
    },
    'central_bank': {
        'file': 'central_bank_balance.py',
        'commands': ['cb-fed', 'cb-ecb', 'cb-boj', 'cb-pboc', 'cb-global', 'cb-reserves']
    },
    'global_shipping': {
        'file': 'global_shipping.py',
        'commands': ['bdi', 'container-freight', 'port-congestion', 'shipping-dashboard']
    },
    'container_port': {
        'file': 'container_port_throughput.py',
        'commands': ['port-all', 'port-shanghai', 'port-rotterdam', 'port-la-long-beach', 'port-compare', 'port-list', 'port-rankings']
    },
    'global_debt': {
        'file': 'global_debt.py',
        'commands': ['country', 'compare', 'high-debt', 'trends', 'bis-countries', 'us-fred']
    },
    'global_real_estate': {
        'file': 'global_real_estate.py',
        'commands': ['re-country', 're-compare', 're-list', 're-search', 're-snapshot']
    },
    'bis_banking': {
        'file': 'bis_banking.py',
        'commands': ['dataflows', 'cross-border', 'derivatives', 'derivatives-by-type', 'fx-turnover', 'fx-centers', 'global-liquidity', 'debt-securities', 'property-prices', 'country-profile', 'countries']
    },
    'bis_credit_gap': {
        'file': 'bis_credit_gap.py',
        'commands': ['credit-gap', 'g20-credit-heatmap', 'crisis-probability']
    },
    'ilo_labor': {
        'file': 'ilo_labor.py',
        'commands': ['labor-profile', 'labor-unemployment', 'labor-employment', 'labor-force', 'youth-unemployment', 'working-poverty', 'informal-employment', 'labor-compare', 'labor-countries', 'labor-search', 'labor-indicators']
    },
    'muni_bonds': {
        'file': 'muni_bonds.py',
        'commands': ['muni-search', 'muni-trades', 'muni-issuer', 'muni-events', 'muni-state', 'muni-curve', 'muni-compare']
    },
    'mmf_flows': {
        'file': 'mmf_flows.py',
        'commands': ['mmf-flows', 'mmf-filings', 'mmf-parse', 'mmf-yields', 'mmf-concentration', 'mmf-compare']
    },
    'repo_rate_monitor': {
        'file': 'repo_rate_monitor.py',
        'commands': ['sofr', 'repo', 'reverse-repo', 'overnight', 'compare', 'stress']
    },
    'treasury_auctions': {
        'file': 'treasury_auctions.py',
        'commands': ['treasury-recent', 'treasury-upcoming', 'treasury-tic', 'treasury-debt', 'treasury-performance', 'treasury-dashboard']
    },
    'commercial_paper': {
        'file': 'commercial_paper.py',
        'commands': ['cp-current', 'cp-history', 'cp-spreads', 'cp-compare', 'cp-dashboard']
    },
    'bond_new_issue': {
        'file': 'bond_new_issue.py',
        'commands': ['bond-upcoming', 'bond-issuer', 'bond-company', 'bond-analyze', 'bond-dashboard']
    },
    'corporate_bond_spreads': {
        'file': 'corporate_bond_spreads.py',
        'commands': ['ig-spreads', 'hy-spreads', 'sector-spreads', 'ig-vs-hy', 'spreads-by-maturity', 'credit-dashboard', 'spread-trends']
    },
    'treasury_curve': {
        'file': 'treasury_curve.py',
        'commands': ['yield-curve', 'yield-history', 'yield-analyze', 'yield-compare', 'yield-maturity']
    },
    'swap_rate_curves': {
        'file': 'swap_rate_curves.py',
        'commands': ['usd-curve', 'eur-curve', 'compare-curves', 'swap-spread', 'inversion-signal']
    },
    'usda_agriculture': {
        'file': 'usda_agriculture.py',
        'commands': ['crop-production', 'livestock', 'farm-prices', 'wasde-summary', 'ag-dashboard', 'list-commodities']
    },
    'wto': {
        'file': 'wto_trade.py',
        'commands': ['members', 'tariff', 'compare-tariffs', 'antidumping', 'disputes', 'dispute-detail', 'agreements', 'tpr']
    },
    'abs': {
        'file': 'abs.py',
        'commands': ['abs-gdp', 'abs-cpi', 'abs-employment', 'abs-housing', 'abs-cash-rate', 'abs-building', 'abs-retail', 'abs-snapshot', 'abs-list']
    },
    'south_africa': {
        'file': 'south_africa_reserve_bank.py',
        'commands': ['south-africa', 'sa-snapshot', 'sa-indicator', 'sa-repo-rate', 'sa-zar-rate', 'sa-mining', 'sa-brics-compare', 'sa-indicators']
    },
    'israel_cbs': {
        'file': 'israel_cbs.py',
        'commands': ['israel-gdp', 'israel-cpi', 'israel-housing', 'israel-tech-exports', 'israel-dashboard']
    },
    'bank_of_israel': {
        'file': 'bank_of_israel_dashboard.py',
        'commands': ['boi-dashboard', 'boi-policy-rate', 'boi-fx-reserves', 'boi-exchange-rates', 'boi-inflation', 'boi-policy-history']
    },
    'israel_cbs': {
        'file': 'israel_cbs_statistics.py',
        'commands': ['israel-cbs-dashboard', 'israel-cbs-cpi', 'israel-cbs-labor', 'israel-cbs-industrial', 
                     'israel-cbs-trade', 'israel-cbs-rates', 'israel-cbs-reserves']
    },
    'tase': {
        'file': 'tase.py',
        'commands': ['tase-index', 'tase-stock', 'tase-summary', 'tase-sectors', 'tase-history']
    },
    'reserve_bank_india': {
        'file': 'reserve_bank_india.py',
        'commands': ['rbi-dashboard', 'rbi-rates', 'rbi-forex', 'rbi-money', 'rbi-credit', 
                     'rbi-inflation', 'rbi-bop', 'rbi-banking']
    },
    'bse_nse': {
        'file': 'bse_nse.py',
        'commands': ['india-sensex', 'india-nifty', 'india-nifty-bank', 'india-nifty-it', 
                     'india-all-indices', 'india-fii-dii', 'india-breadth', 'india-gainers', 'india-losers', 'india-active', 'india-market-status', 'india-market-dashboard']
    },
    'abs_australia': {
        'file': 'abs_australia_stats.py',
        'commands': ['aus-gdp', 'aus-cpi', 'aus-employment', 'aus-unemployment', 
                     'aus-trade', 'aus-building', 'aus-retail', 'aus-wages', 'aus-dashboard']
    },
    'asx': {
        'file': 'asx.py',
        'commands': ['asx-summary', 'asx-holdings', 'asx-quote', 'asx-actions', 'asx-sectors', 
                     'asx-depth', 'asx-history', 'asx-compare', 'asx-movers', 'asx-indices']
    },
    'bank_of_korea': {
        'file': 'bank_of_korea.py',
        'commands': ['bok-dashboard', 'bok-base-rate', 'bok-money', 'bok-fx-reserves', 
                     'bok-inflation', 'bok-gdp', 'bok-current-account']
    },
    'poland_gus': {
        'file': 'poland_gus.py',
        'commands': ['poland-indicator', 'poland-gdp', 'poland-inflation', 'poland-employment', 
                     'poland-industrial', 'poland-trade', 'poland-dashboard', 'poland-indicators', 
                     'poland-voivodeships']
    },
    'switzerland_snb': {
        'file': 'switzerland_snb.py',
        'commands': ['swiss-gdp', 'swiss-cpi', 'swiss-fx-reserves', 'swiss-sight-deposits', 
                     'swiss-rates', 'swiss-trade', 'swiss-dashboard']
    },
    'global_inflation': {
        'file': 'global_inflation.py',
        'commands': ['inflation-country', 'inflation-compare', 'inflation-heatmap', 
                     'inflation-divergence', 'inflation-search', 'inflation-countries']
    },
    'equity_screener': {
        'file': 'equity_screener.py',
        'commands': ['screen', 'preset', 'rank', 'factors', 'presets']
    },
    'global_stock_exchange_holidays': {
        'file': 'global_stock_exchange_holidays.py',
        'commands': ['exchange-holidays', 'exchange-info', 'is-trading-day', 'next-trading-day',
                     'month-calendar', 'global-holidays-today', 'compare-holidays', 'list-exchanges']
    },
    'spac_lifecycle': {
        'file': 'spac_lifecycle.py',
        'commands': ['spac-list', 'spac-trust', 'spac-timeline', 'spac-redemptions', 'spac-arbitrage', 'spac-search']
    },
    'secondary_offering': {
        'file': 'secondary_offering_monitor.py',
        'commands': ['secondary-recent', 'secondary-by-ticker', 'secondary-shelf-status', 'secondary-impact', 'secondary-upcoming', 'secondary-search']
    },
    'global_index_returns': {
        'file': 'global_equity_index_returns.py',
        'commands': ['daily-returns', 'performance', 'regional', 'correlation', 'compare', 'list']
    },
    'high_yield_bonds': {
        'file': 'high_yield_bonds.py',
        'commands': ['hy-spreads', 'distressed-debt', 'default-rates', 'hy-dashboard']
    },
    'clo_abs': {
        'file': 'clo_abs.py',
        'commands': ['clo-overview', 'abs-asset-class', 'cmbs-market', 'issuance-trends', 'delinquency-rates', 'abs-liquidity', 'clo-abs-dashboard', 'credit-quality', 'nport-holdings']
    },
    'sovereign_rating_tracker': {
        'file': 'sovereign_rating_tracker.py',
        'commands': ['sovereign-ratings', 'sovereign-downgrades', 'sovereign-upgrades', 'sovereign-watch', 'sovereign-ig-changes', 'sovereign-dashboard', 'sovereign-country']
    },
    'gold_precious_metals': {
        'file': 'gold_precious_metals.py',
        'commands': ['prices', 'etf-holdings', 'gold-silver-ratio', 'performance', 'wgc-summary', 'comprehensive-report']
    },
    'agricultural_commodities': {
        'file': 'agricultural_commodities.py',
        'commands': ['ag-futures', 'ag-grains', 'ag-softs', 'ag-usda', 'ag-dashboard', 'ag-list']
    },
    'carbon_credits': {
        'file': 'carbon_credits.py',
        'commands': ['eu-ets-price', 'global-prices', 'market-stats', 'emissions-by-sector', 'compare-markets', 'offset-projects']
    },
    'eu_taxonomy': {
        'file': 'eu_taxonomy_alignment.py',
        'commands': ['taxonomy-score', 'taxonomy-leaders', 'taxonomy-sector']
    },
    'rare_earths': {
        'file': 'rare_earths.py',
        'commands': ['mineral-profile', 'supply-risk', 'risk-rankings', 'sector-exposure', 'country-profile', 'rare-earths-detailed', 'comprehensive-report', 'list-minerals', 'list-sectors']
    },
    'semiconductor_chip': {
        'file': 'semiconductor_chip.py',
        'commands': ['chip-sales', 'chip-forecast', 'fab-util', 'chip-summary']
    },
    'livestock_meat': {
        'file': 'livestock_meat.py',
        'commands': ['livestock-futures', 'livestock-cattle', 'livestock-hogs', 'livestock-slaughter', 'livestock-ams', 'livestock-dashboard', 'livestock-reports']
    },
    'opec': {
        'file': 'opec.py',
        'commands': ['opec-monitor', 'opec-summary', 'opec-country', 'opec-compliance', 'opec-quota-history', 'opec-dashboard']
    },
    'cftc_cot': {
        'file': 'cftc_cot.py',
        'commands': ['cot-latest', 'cot-contract', 'cot-extremes', 'cot-summary', 'cot-divergence', 'cot-dashboard']
    },
    'global_fx': {
        'file': 'global_fx_rates.py',
        'commands': ['fx-rate', 'fx-all', 'fx-cross', 'fx-matrix', 'fx-convert', 'fx-strongest', 'fx-currencies']
    },
    'stablecoin': {
        'file': 'stablecoin_supply.py',
        'commands': ['stablecoin-all', 'stablecoin-detail', 'stablecoin-chain', 'stablecoin-mint-burn', 'stablecoin-dominance']
    },
    'global_electricity': {
        'file': 'global_electricity_demand.py',
        'commands': ['entsoe-load', 'entsoe-forecast', 'europe-aggregate', 'eia-demand', 'us-generation-mix', 'caiso-load', 'caiso-renewables', 'global-dashboard', 'compare-regions']
    },
    'global_tourism': {
        'file': 'global_tourism_statistics.py',
        'commands': ['tourism-arrivals', 'tourism-receipts', 'tourism-country', 'tourism-global-overview', 'tourism-compare', 'hotel-occupancy', 'airline-passengers', 'tourism-recovery']
    },
    'bankruptcy_tracker': {
        'file': 'bankruptcy_tracker.py',
        'commands': ['bankruptcy-search', 'bankruptcy-tracker', 'bankruptcy-stats']
    },
    'pe_vc_deals': {
        'file': 'pe_vc_deals.py',
        'commands': ['vc-deals', 'pe-deals', 'form-d', 'deal-summary']
    },
    'health_impact': {
        'file': 'health_impact.py',
        'commands': ['health-outbreaks', 'pandemic-impact', 'health-monitor']
    },
    'academic_papers': {
        'file': 'academic_papers.py',
        'commands': ['papers-latest', 'papers-search', 'papers-trending', 'papers-by-author', 'papers-report']
    },
    'sse': {
        'file': 'shanghai_stock_exchange.py',
        'commands': ['sse-index', 'sse-margin', 'sse-northbound']
    },
    'szse': {
        'file': 'shenzhen_stock_exchange.py',
        'commands': ['szse-index', 'szse-chinext', 'szse-summary', 'szse-performance']
    },
    'flight': {
        'file': 'flight_data.py',
        'commands': ['flight-live', 'flight-index', 'flight-regional', 'flight-report']
    },
    'satellite': {
        'file': 'satellite_lights.py',
        'commands': ['satellite-monthly', 'satellite-urban-growth', 'satellite-gdp', 'satellite-blackouts', 'satellite-settlements', 'satellite-summary']
    },
    'dtcc': {
        'file': 'dtcc_trade_reporting.py',
        'commands': ['dtcc-swaps', 'dtcc-repo', 'dtcc-triparty', 'dtcc-lending', 'dtcc-clearing', 'dtcc-ftd', 'dtcc-risk']
    },
    'safe_china': {
        'file': 'safe_china_fx_reserves.py',
        'commands': ['safe-reserves', 'safe-capital-flows', 'safe-interventions', 'safe-composition', 'safe-gold', 'safe-dashboard']
    }
}

def dispatch_command(args):
    """Route command to appropriate module"""
    if len(args) < 1:
        print_help()
        return 1
    
    command = args[0]
    
    # Find which module handles this command
    for module_key, module_info in MODULES.items():
        if command in module_info['commands']:
            module_path = MODULES_DIR / module_info['file']
            if not module_path.exists():
                print(f"Error: Module {module_info['file']} not found", file=sys.stderr)
                return 1
            
            # Execute the module with remaining args
            result = subprocess.run(
                ['python3', str(module_path)] + args,
                cwd=Path(__file__).parent
            )
            return result.returncode
    
    print(f"Error: Unknown command '{command}'", file=sys.stderr)
    print_help()
    return 1

def print_help():
    """Print CLI help"""
    print("QUANTCLAW DATA CLI")
    print("\nAvailable commands:\n")
    
    print("Pairs Trading (Phase 32):")
    print("  python cli.py pairs-scan SECTOR [--limit N]")
    print("  python cli.py cointegration SYMBOL1 SYMBOL2 [--lookback DAYS]")
    print("  python cli.py spread-monitor SYMBOL1 SYMBOL2 [--period PERIOD]")
    
    print("\nCDS Spreads (Phase 30):")
    print("  python cli.py sovereign-spreads [COUNTRY]")
    print("  python cli.py corporate-spreads [RATING]")
    print("  python cli.py spread-compare")
    print("  python cli.py credit-risk-score TICKER")
    
    print("\nSector Rotation (Phase 33):")
    print("  python cli.py sector-rotation [LOOKBACK_DAYS]")
    print("  python cli.py sector-momentum [LOOKBACK_DAYS]")
    print("  python cli.py economic-cycle")
    
    print("\nMonte Carlo Simulation (Phase 34):")
    print("  python cli.py monte-carlo SYMBOL [--simulations N] [--days N] [--method gbm|bootstrap]")
    print("  python cli.py var SYMBOL [--confidence 0.95 0.99] [--days N]")
    print("  python cli.py scenario SYMBOL [--days N]")
    
    print("\nBacktesting Framework with Walk-Forward Optimization:")
    print("  python cli.py backtest-strategies                 # List all available strategies")
    print("  python cli.py backtest <strategy> <ticker> --start YYYY-MM-DD --end YYYY-MM-DD [--cash 100000] [--params '{\"fast\": 10}']")
    print("                                                    # Run single backtest")
    print("  python cli.py backtest-optimize <strategy> <ticker> --start YYYY-MM-DD --end YYYY-MM-DD [--method grid|random] [--metric sharpe|return|calmar] [--n-trials 100]")
    print("                                                    # Optimize strategy parameters")
    print("  python cli.py backtest-walkforward <strategy> <ticker> --start YYYY-MM-DD --end YYYY-MM-DD [--train-months 12] [--test-months 3] [--metric sharpe]")
    print("                                                    # Walk-forward optimization")
    print("  python cli.py backtest-compare <ticker> --start YYYY-MM-DD --end YYYY-MM-DD --strategies sma_crossover,rsi_mean_reversion,momentum")
    print("                                                    # Compare multiple strategies")
    print("  python cli.py backtest-report <run_id>            # Get detailed report for a run")
    print("  python cli.py backtest-history [--limit 10]       # List past backtest runs")
    
    print("\nWalk-Forward Optimization (Phase 37):")
    print("  python cli.py walk-forward SYMBOL [--strategy sma-crossover]")
    print("  python cli.py overfit-check SYMBOL")
    print("  python cli.py param-stability SYMBOL")
    
    print("\nKalman Filter Trends (Phase 35):")
    print("  python cli.py kalman SYMBOL [--period PERIOD]")
    print("  python cli.py adaptive-ma SYMBOL [--period PERIOD]")
    print("  python cli.py regime-detect SYMBOL [--period PERIOD] [--window WINDOW]")
    
    print("\nMulti-Timeframe Analysis (Phase 38):")
    print("  python cli.py mtf SYMBOL")
    print("  python cli.py trend-alignment SYMBOL")
    print("  python cli.py signal-confluence SYMBOL")
    
    print("\nSmart Alerts (Phase 40):")
    print("  python cli.py alert-create SYMBOL --condition 'price>200' [--channels console,file,webhook]")
    print("  python cli.py alert-list [--active]")
    print("  python cli.py alert-check [--symbols AAPL,TSLA]")
    print("  python cli.py alert-delete ALERT_ID")
    print("  python cli.py alert-history [--symbol AAPL] [--limit 50]")
    print("  python cli.py alert-stats")
    
    print("\nAlert Backtesting (Phase 41):")
    print("  python cli.py alert-backtest SYMBOL --condition 'CONDITION' [--period PERIOD]")
    print("  python cli.py signal-quality SYMBOL [--period PERIOD]")
    print("  python cli.py alert-potential SYMBOL [--period PERIOD]")
    
    print("\nOrder Book Depth (Phase 39):")
    print("  python cli.py order-book SYMBOL [--levels N]")
    print("  python cli.py bid-ask SYMBOL")
    print("  python cli.py liquidity SYMBOL")
    print("  python cli.py imbalance SYMBOL [--period 1d|5d|1mo]")
    print("  python cli.py support-resistance SYMBOL [--period 3mo]")
    
    print("\nCustom Alert DSL (Phase 42):")
    print("  python cli.py dsl-eval SYMBOL \"EXPRESSION\"")
    print("  python cli.py dsl-scan \"EXPRESSION\" [--universe SP500] [--limit N]")
    print("  python cli.py dsl-help")
    
    print("\nCommodity Futures Curves (Phase 44):")
    print("  python cli.py futures-curve SYMBOL [--limit N]")
    print("  python cli.py contango")
    print("  python cli.py roll-yield SYMBOL [--lookback DAYS]")
    print("  python cli.py term-structure SYMBOL")
    
    print("\nSatellite Imagery Proxies (Phase 46):")
    print("  python cli.py satellite-proxy TICKER")
    print("  python cli.py shipping-index")
    print("  python cli.py construction-activity")
    print("  python cli.py foot-traffic TICKER")
    print("  python cli.py economic-index")
    
    print("\nFed Policy Prediction (Phase 45):")
    print("  python cli.py fed-watch              # Comprehensive Fed policy analysis")
    print("  python cli.py rate-probability       # Calculate rate hike/cut probabilities")
    print("  python cli.py fomc-calendar          # Show upcoming FOMC meeting dates")
    print("  python cli.py dot-plot               # Dot plot consensus analysis")
    print("  python cli.py yield-curve            # Treasury yield curve analysis")
    print("  python cli.py current-rate           # Current fed funds rate & target range")
    
    print("\nEM Sovereign Spread Monitor (Phase 158):")
    print("  python cli.py embi-global            # JPMorgan EMBI Global spread (main benchmark)")
    print("  python cli.py regional-spreads       # Regional breakdown (LatAm, Asia, Europe, MENA)")
    print("  python cli.py credit-quality         # High yield vs investment grade comparison")
    print("  python cli.py spread-history [DAYS] [SERIES_ID]  # Historical spread trends")
    print("  python cli.py em-report              # Comprehensive EM sovereign analysis")
    
    print("\nEM Currency Crisis Monitor (Phase 184):")
    print("  python cli.py em-fx-reserves Brazil           # Get FX reserves data for EM country")
    print("  python cli.py em-current-account Turkey       # Get current account balance data")
    print("  python cli.py em-reer Argentina               # Get real effective exchange rate")
    print("  python cli.py em-crisis-risk India            # Calculate comprehensive crisis risk score")
    print("  python cli.py em-regional-overview latam      # Regional overview (all/latam/asia/emea)")
    print("  Countries: Brazil, Mexico, Argentina, China, India, Indonesia, Thailand,")
    print("            Philippines, Malaysia, Russia, Turkey, South Africa, Poland")
    
    print("\nCrypto On-Chain Analytics (Phase 43):")
    print("  python cli.py onchain ETH                          # Get Ethereum on-chain metrics")
    print("  python cli.py whale-watch BTC [--min 100]          # Track Bitcoin whale wallets")
    print("  python cli.py dex-volume [--protocol uniswap] [--chain ethereum]")
    print("  python cli.py gas-fees                             # Current Ethereum gas fees")
    print("  python cli.py token-flows USDT [--hours 24]        # Track token transfer volumes")
    
    print("\nPeer Network Analysis (Phase 48):")
    print("  python cli.py peer-network TICKER                  # Analyze company relationships")
    print("  python cli.py compare-networks AAPL,MSFT,GOOGL    # Compare multiple companies")
    print("  python cli.py map-dependencies TICKER              # Map revenue dependencies")
    
    print("\nPolitical Risk Scoring (Phase 49):")
    print("  python cli.py geopolitical-events [--country COUNTRY] [--keywords KEYWORDS] [--hours HOURS]")
    print("  python cli.py sanctions-search [--entity NAME] [--type country|individual|entity]")
    print("  python cli.py regulatory-changes [--sector SECTOR] [--country COUNTRY] [--days DAYS]")
    print("  python cli.py country-risk COUNTRY_CODE            # Get World Bank governance indicators")
    
    print("\nRevenue Quality Analysis (Phase 52):")
    print("  python cli.py revenue-quality TICKER              # Comprehensive revenue quality analysis")
    print("  python cli.py dso-trends TICKER                   # Days Sales Outstanding trend analysis")
    print("  python cli.py channel-stuffing TICKER             # Detect channel stuffing red flags")
    print("  python cli.py cash-flow-divergence TICKER         # CFO vs net income divergence")
    
    print("\nEarnings Quality Metrics (Phase 59):")
    print("  python cli.py earnings-quality TICKER             # Accruals ratio, Beneish M-Score, Altman Z-Score")
    print("  python cli.py accruals-trend TICKER               # Accruals ratio trend over 4 periods")
    print("  python cli.py fraud-indicators TICKER             # Quick fraud/distress red flags summary")
    
    print("\nQuality Factor Scoring (Phase 400):")
    print("  python cli.py quality-score TICKER                # Score stock on quality factors (ROE, leverage, accruals, stability)")
    print("  python cli.py quality-screen AAPL,MSFT,GOOGL --min-score 70")
    print("                                                    # Screen multiple tickers for quality")
    
    print("\nExecutive Compensation (Phase 51):")
    print("  python cli.py exec-comp TICKER                    # Executive compensation breakdown (CEO, CFO, top officers)")
    print("  python cli.py pay-performance TICKER              # Pay-for-performance correlation analysis")
    print("  python cli.py comp-peer-compare TICKER            # Peer compensation comparison with percentile rankings")
    print("  python cli.py shareholder-alignment TICKER        # Shareholder alignment metrics and insider ownership")
    
    print("\nShare Buyback Analysis (Phase 56):")
    print("  python cli.py buyback-analysis TICKER             # Full buyback report: authorization vs execution, dilution, ROI")
    print("  python cli.py share-count-trend TICKER            # Shares outstanding history and quarter-over-quarter changes")
    print("  python cli.py buyback-yield TICKER                # Buyback yield calculation (buybacks/market cap)")
    print("  python cli.py dilution-impact TICKER              # Stock-based compensation dilution vs buyback offset")
    
    print("\nPeer Earnings Comparison (Phase 53):")
    print("  python cli.py peer-earnings TICKER                # Compare earnings patterns across sector peers")
    print("  python cli.py beat-miss-history TICKER            # Detailed beat/miss pattern analysis")
    print("  python cli.py guidance-tracker TICKER             # Track management guidance and analyst trends")
    print("  python cli.py estimate-dispersion TICKER          # Analyze analyst estimate spread and uncertainty")
    
    print("\nTax Loss Harvesting (Phase 55):")
    print("  python cli.py tlh-scan AAPL,TSLA,MSFT,AMZN,META  # Scan portfolio for TLH opportunities")
    print("  python cli.py wash-sale-check TSLA 2025-01-15    # Check wash sale rule window (30 days)")
    print("  python cli.py tax-savings AAPL --cost-basis 180 --shares 100  # Estimate tax savings")
    print("  python cli.py tlh-replacements TSLA              # Suggest sector replacement securities")
    
    print("\nDividend Sustainability (Phase 57):")
    print("  python cli.py dividend-health TICKER              # Comprehensive dividend sustainability report")
    print("  python cli.py payout-ratio TICKER                 # Payout ratio trend analysis")
    print("  python cli.py fcf-coverage TICKER                 # Free cash flow dividend coverage analysis")
    print("  python cli.py dividend-cut-risk TICKER            # Probability of dividend cut score (0-100)")
    
    print("\nCrypto Correlation Indicators (Phase 54):")
    print("  python cli.py btc-dominance                       # BTC dominance trend and altcoin season signal")
    print("  python cli.py altcoin-season                      # Altcoin season index (% of top 50 outperforming BTC)")
    print("  python cli.py defi-tvl-correlation                # DeFi TVL correlation with NASDAQ/tech stocks")
    print("  python cli.py crypto-equity-corr                  # Crypto-equity correlation matrix (BTC/ETH/BNB vs FAANG)")
    
    print("\nInstitutional Ownership (Phase 58):")
    print("  python cli.py 13f-changes TICKER                  # Track institutional 13F changes (new/increased/decreased/exited)")
    print("  python cli.py whale-accumulation TICKER           # Detect whale accumulation or distribution patterns")
    print("  python cli.py top-holders TICKER [--limit 20]     # Get top institutional holders and concentration metrics")
    print("  python cli.py smart-money TICKER                  # Track famous investor (Buffett, Ackman, Burry) positions")
    
    print("\nInsider Transaction Heatmap (Phase 137):")
    print("  python cli.py insider-summary [--days 7]          # Sector-wide insider buying/selling patterns")
    print("  python cli.py insider-sector SECTOR [--days 30]   # Deep dive: insider clusters in specific sector")
    print("  python cli.py insider-ticker TICKER [--days 90]   # Insider transaction history for a ticker")
    
    print("\nConvertible Bond Arbitrage (Phase 64):")
    print("  python cli.py convertible-scan                    # Scan for convertible bond opportunities")
    print("  python cli.py conversion-premium TSLA             # Conversion premium analysis")
    print("  python cli.py convertible-arb MSTR                # Arbitrage opportunity analysis")
    print("  python cli.py convertible-greeks COIN             # Delta/gamma for convertible positions")
    
    print("\nSustainability-Linked Bonds (Phase 71):")
    print("  python cli.py slb-market                          # Overall SLB market dashboard")
    print("  python cli.py slb-issuer ENEL                     # Issuer SLB analysis")
    print("  python cli.py slb-kpi-tracker                     # Track upcoming KPI measurement dates")
    print("  python cli.py slb-coupon-forecast                 # Forecast potential coupon step-ups")
    
    print("\nShort Squeeze Detector (Phase 65):")
    print("  python cli.py squeeze-scan [--tickers GME,AMC]    # Scan market for high short interest squeeze candidates")
    print("  python cli.py squeeze-score GME                   # Calculate squeeze probability score (0-100)")
    print("  python cli.py short-interest TSLA                 # Detailed short interest analysis")
    print("  python cli.py days-to-cover AMC                   # Days to cover & borrow cost estimate")
    
    print("\nDark Pool Tracker (Phase 61):")
    print("  python cli.py dark-pool-volume TICKER             # Estimate dark pool volume percentage (OTC vs lit)")
    print("  python cli.py block-trades TICKER                 # Detect large block trades (institutional activity)")
    print("  python cli.py institutional-accumulation TICKER [--period DAYS]  # Accumulation/distribution pattern")
    print("  python cli.py off-exchange-ratio TICKER [--period DAYS]          # Off-exchange vs lit exchange ratio trend")
    
    print("\nMarket Regime Detection (Phase 66):")
    print("  python cli.py market-regime                       # Current market regime classification (risk-on/off/crisis)")
    print("  python cli.py regime-history                      # Regime timeline over last 60 days")
    print("  python cli.py risk-dashboard                      # Comprehensive risk-on/off dashboard with volatility & correlations")
    print("  python cli.py correlation-regime                  # Cross-asset correlation state and breakdown detection")
    
    print("\nCorrelation Anomaly Detector (Phase 87):")
    print("  python cli.py corr-breakdown --ticker1 AAPL --ticker2 MSFT  # Detect correlation breakdown between two assets")
    print("  python cli.py corr-scan --tickers SPY,TLT,GLD,QQQ           # Scan correlation matrix for anomalies")
    print("  python cli.py corr-regime --tickers SPY,TLT,GLD,DBC         # Detect market regime shifts via correlation structure")
    print("  python cli.py corr-arbitrage --tickers XLF,XLK,XLE          # Find statistical arbitrage opportunities from correlation breakdowns")
    
    print("\nCorporate Action Calendar (Phase 63):")
    print("  python cli.py corporate-calendar TICKER           # Upcoming corporate actions (dividends, splits, special events)")
    print("  python cli.py split-history TICKER                # Stock split history with price impact analysis")
    print("  python cli.py dividend-calendar [TICKERS]         # Upcoming dividend ex-dates across watchlist")
    print("  python cli.py spinoff-tracker                     # Recent/upcoming spin-offs and special distributions")
    
    print("\nStock Split & Corporate Events (Phase 146):")
    print("  python cli.py stock-split-history TICKER [--years N]           # Complete split history with cumulative factors")
    print("  python cli.py stock-split-impact TICKER [--date YYYY-MM-DD]    # Pre/post split price impact analysis")
    print("  python cli.py stock-corporate-actions TICKER [--years N]       # All corporate actions with impact metrics")
    print("  python cli.py stock-compare-splits TICKER1,TICKER2,... [--days N]  # Compare split performance across tickers")
    
    print("\n13D/13G Filing Alerts (Phase 68):")
    print("  python cli.py filing-alerts-recent [--hours 24] [--type 'SC 13D']    # Recent activist filings")
    print("  python cli.py filing-alerts-search TESLA [--type '13D']              # Search company filings")
    print("  python cli.py filing-alerts-activists [--min-filings 3]              # Active filers with multiple campaigns")
    print("  python cli.py filing-alerts-watch [--interval 15] [--iterations 4]   # Monitor for new filings")
    
    print("\nProxy Fight Tracker (Phase 69):")
    print("  python cli.py proxy-filings TICKER [--years 3]    # Fetch proxy-related filings (DEF 14A, DEFA14A, 8-K)")
    print("  python cli.py proxy-contests TICKER               # Detect proxy contests (PREC14A, DEFC14A)")
    print("  python cli.py proxy-voting TICKER                 # Fetch voting results from 8-K Item 5.07")
    print("  python cli.py proxy-advisory TICKER               # Information on ISS/Glass Lewis data sources")
    print("  python cli.py proxy-summary TICKER                # Comprehensive proxy fight analysis with risk score")
    
    print("\nActivist Success Predictor (Phase 67):")
    print("  python cli.py activist-predict TICKER             # Predict activist campaign success probability")
    print("  python cli.py activist-history                    # Historical activist campaign outcomes and patterns")
    print("  python cli.py activist-targets [--sector SECTOR]  # Scan for likely activist targets")
    print("  python cli.py governance-score TICKER             # Company governance quality score (0-100)")
    
    print("\nClimate Risk Scoring (Phase 72):")
    print("  python cli.py climate-risk TICKER                 # Composite climate risk score (physical + transition)")
    print("  python cli.py physical-risk TICKER                # Physical risk exposure (floods, hurricanes, drought, wildfire)")
    print("  python cli.py transition-risk TICKER              # Carbon transition risk (pricing, regulation, stranded assets)")
    print("  python cli.py carbon-scenario TICKER              # Scenario analysis (1.5°C vs 2°C vs 3°C pathways)")
    
    print("\nFactor Timing Model (Phase 73):")
    print("  python cli.py factor-timing                       # Current factor regime and recommended allocation")
    print("  python cli.py factor-rotation                     # Adaptive factor rotation signals (STRONG_BUY, OVERWEIGHT, etc.)")
    print("  python cli.py factor-performance [PERIOD]         # Factor returns comparison (1y, 6m, 3m)")
    print("  python cli.py factor-regime-history [--days N]    # Historical regime timeline (RISK_ON, RISK_OFF, NEUTRAL)")
    
    print("\nML Factor Discovery (Phase 74):")
    print("  python cli.py discover-factors TICKERS            # Auto-discover predictive factors (price, volume, fundamentals)")
    print("  python cli.py factor-ic [--top-n 20]              # Information Coefficient rankings for all factors")
    print("  python cli.py factor-backtest FACTOR_NAME         # Walk-forward backtest of specific factor")
    print("  python cli.py feature-importance [--top-n 20]     # ML ensemble feature importance (RF, GBM, Lasso)")
    
    print("\nAI Earnings Call Analyzer (Phase 76):")
    print("  python cli.py earnings-tone TICKER                # Real-time tone detection with LLM-style analysis")
    print("  python cli.py confidence-score TICKER             # Executive confidence scoring via multi-factor analysis")
    print("  python cli.py language-shift TICKER               # Quarter-over-quarter language change detection")
    print("  python cli.py hedging-detector TICKER             # Advanced hedging language detection with examples")
    
    print("\nRegulatory Event Calendar (Phase 78):")
    print("  python cli.py econ-calendar                       # Upcoming economic events (FOMC, CPI, GDP, NFP)")
    print("  python cli.py event-reaction CPI [--years 5]      # Historical market reaction to CPI releases")
    print("  python cli.py event-volatility FOMC               # Volatility forecast around next FOMC meeting")
    print("  python cli.py event-backtest NFP --years 5        # Backtest NFP employment report reactions")
    
    print("\nAlert Backtesting Dashboard (Phase 80):")
    print("  python cli.py dashboard-backtest rsi --ticker AAPL [--years 3] [--hold-days 5]  # Backtest RSI alerts")
    print("  python cli.py dashboard-backtest volume --ticker TSLA [--years 3]                # Backtest volume spike alerts")
    print("  python cli.py dashboard-backtest breakout --ticker NVDA [--years 3]              # Backtest price breakout alerts")
    print("  python cli.py dashboard-performance [--years 3]       # Compare all alert types across tickers")
    print("  python cli.py dashboard-optimize TICKER [--alert-type rsi] [--years 3]           # Optimize alert parameters")
    print("  python cli.py dashboard-report [--output report.json]  # Generate comprehensive performance report")
    
    print("\nPDF Report Exporter (Phase 79):")
    print("  python cli.py export-pdf AAPL --modules all                        # Full PDF report")
    print("  python cli.py export-pdf TSLA --modules earnings,technicals        # Selective modules")
    print("  python cli.py batch-report AAPL,MSFT,GOOGL                         # Batch reports")
    print("  python cli.py report-template list                                 # Available templates")
    
    print("\nSmart Data Prefetching (Phase 83):")
    print("  python cli.py prefetch-stats                      # Show usage patterns and predictions")
    print("  python cli.py prefetch-warmup                     # Warm cache with predicted data")
    print("  python cli.py cache-status                        # Show cache hit rates and statistics")
    print("  python cli.py prefetch-config --top 20            # Configure prefetch pool size")
    print("  python cli.py prefetch-config --confidence 0.6    # Set minimum confidence threshold")
    print("  python cli.py prefetch-config --enable true       # Enable/disable prefetching")
    
    print("\nMulti-Source Data Reconciliation (Phase 84):")
    print("  python cli.py reconcile-price SYMBOL              # Compare price across Yahoo/CoinGecko/FRED")
    print("  python cli.py data-quality-report                 # Overall data quality metrics and discrepancies")
    print("  python cli.py source-reliability                  # Source reliability rankings with confidence scores")
    print("  python cli.py discrepancy-log [--hours 24]        # Recent data discrepancies across sources")
    print("  python cli.py discrepancy-log --symbol AAPL       # Filter discrepancies by symbol")
    
    print("\nLive Earnings Transcription (Phase 82):")
    print("  python cli.py earnings-schedule [DAYS]            # Upcoming earnings this week/period")
    print("  python cli.py transcript-signals TICKER           # Extract trading signals from latest transcript")
    print("  python cli.py earnings-countdown TICKER           # Days until next earnings report")
    print("  python cli.py transcript-compare TICKER           # Compare latest vs prior quarter transcript")
    
    print("\nCross-Exchange Arbitrage (Phase 77):")
    print("  python cli.py arb-scan [SYMBOLS]                  # Scan for price discrepancies across exchanges")
    print("  python cli.py arb-spread SYMBOL                   # Detailed cross-exchange spread analysis")
    print("  python cli.py arb-history SYMBOL [--days N]       # Historical arbitrage profitability")
    print("  python cli.py exchange-latency                    # Exchange execution speed comparison")
    
    print("\nNeural Price Prediction (Phase 85):")
    print("  python cli.py predict-price AAPL --horizon 5d    # LSTM price forecast (1d/5d/20d)")
    print("  python cli.py prediction-confidence TSLA          # Uncertainty quantification with CI")
    print("  python cli.py model-comparison NVDA               # Compare LSTM vs statistical models")
    print("  python cli.py prediction-backtest MSFT --years 1  # Historical prediction accuracy")
    
    print("\nSPAC Lifecycle Tracker (Phase 148):")
    print("  python cli.py spac-list [--status searching|announced|completed]  # List tracked SPACs")
    print("  python cli.py spac-trust TICKER                                   # Calculate trust value per share")
    print("  python cli.py spac-timeline TICKER                                # Show deal timeline")
    print("  python cli.py spac-redemptions TICKER                             # Estimate redemption risk")
    print("  python cli.py spac-arbitrage                                      # Find arbitrage opportunities")
    print("  python cli.py spac-search [KEYWORD]                               # Search for SPACs")
    
    print("\nExamples:")
    print("  python cli.py cointegration KO PEP")
    print("  python cli.py pairs-scan beverage --limit 5")
    print("  python cli.py spread-monitor AAPL MSFT --period 60d")
    print("  python cli.py sector-rotation 90")
    print("  python cli.py economic-cycle")
    print("  python cli.py kalman AAPL")
    print("  python cli.py adaptive-ma TSLA --period 1y")
    print("  python cli.py regime-detect SPY --window 30")
    print("  python cli.py black-litterman --tickers AAPL,MSFT,GOOGL --views AAPL:0.20,GOOGL:0.12")
    print("  python cli.py equilibrium-returns --tickers SPY,QQQ,IWM")
    print("  python cli.py portfolio-optimize --tickers AAPL,MSFT,GOOGL --target-return 0.15")
    print("  python cli.py monte-carlo AAPL --simulations 10000 --days 252")
    print("  python cli.py var TSLA --confidence 0.95 0.99")
    print("  python cli.py scenario NVDA --days 180")
    print("  python cli.py walk-forward SPY --strategy sma-crossover")
    print("  python cli.py overfit-check AAPL")
    print("  python cli.py param-stability TSLA")
    print("  python cli.py mtf AAPL")
    print("  python cli.py trend-alignment TSLA")
    print("  python cli.py signal-confluence NVDA")
    print("  python cli.py dsl-eval AAPL \"price > 200 AND rsi < 30\"")
    print("  python cli.py dsl-scan \"rsi < 25\" --universe SP500 --limit 10")
    print("  python cli.py dsl-eval TSLA \"sma(20) crosses_above sma(50)\"")
    print("  python cli.py futures-curve CL --limit 6")
    print("  python cli.py contango")
    print("  python cli.py roll-yield GC --lookback 90")
    print("  python cli.py term-structure NG")
    print("  python cli.py satellite-proxy WMT")
    print("  python cli.py shipping-index")
    print("  python cli.py construction-activity")
    print("  python cli.py foot-traffic AAPL")
    print("  python cli.py economic-index")
    print("  python cli.py country-risk USA")
    print("  python cli.py geopolitical-events --country Russia --hours 24")
    print("  python cli.py sanctions-search --entity Iran")
    print("  python cli.py regulatory-changes --sector finance --days 30")
    print("  python cli.py buyback-analysis AAPL")
    print("  python cli.py share-count-trend MSFT")
    print("  python cli.py buyback-yield GOOGL")
    print("  python cli.py dilution-impact META")
    print("  python cli.py 13f-changes AAPL")
    print("  python cli.py whale-accumulation TSLA")
    print("  python cli.py top-holders NVDA --limit 20")
    print("  python cli.py smart-money GOOGL")
    print("  python cli.py squeeze-scan --min-score 50 --limit 10")
    print("  python cli.py squeeze-score GME")
    print("  python cli.py short-interest TSLA")
    print("  python cli.py days-to-cover AMC")
    print("  python cli.py corporate-calendar AAPL")
    print("  python cli.py split-history TSLA")
    print("  python cli.py dividend-calendar AAPL,MSFT,JNJ,KO")
    print("  python cli.py spinoff-tracker")
    print("  python cli.py dark-pool-volume AAPL")
    print("  python cli.py block-trades TSLA")
    print("  python cli.py institutional-accumulation NVDA --period 30")
    print("  python cli.py off-exchange-ratio SPY --period 20")
    print("  python cli.py market-regime")
    print("  python cli.py regime-history")
    print("  python cli.py risk-dashboard")
    print("  python cli.py correlation-regime")
    print("  python cli.py corr-breakdown --ticker1 AAPL --ticker2 MSFT")
    print("  python cli.py corr-scan --tickers SPY,TLT,GLD,QQQ")
    print("  python cli.py corr-regime --tickers SPY,TLT,GLD,DBC")
    print("  python cli.py corr-arbitrage --tickers XLF,XLK,XLE")
    print("  python cli.py filing-alerts-recent --hours 48")
    print("  python cli.py filing-alerts-search TESLA")
    print("  python cli.py filing-alerts-activists --min-filings 3")
    print("  python cli.py activist-predict AAPL")
    print("  python cli.py activist-history")
    print("  python cli.py activist-targets --sector Technology")
    print("  python cli.py governance-score MSFT")
    print("  python cli.py climate-risk AAPL")
    print("  python cli.py physical-risk XOM")
    print("  python cli.py transition-risk BP")
    print("  python cli.py carbon-scenario TSLA")
    print("  python cli.py factor-timing")
    print("  python cli.py factor-rotation")
    print("  python cli.py factor-performance 6m")
    print("  python cli.py factor-regime-history --days 90")
    print("  python cli.py discover-factors AAPL,MSFT,GOOGL,AMZN,META")
    print("  python cli.py factor-ic --top-n 30")
    print("  python cli.py factor-backtest momentum_3m")
    print("  python cli.py feature-importance --horizon 5d")
    print("  python cli.py earnings-tone AAPL")
    print("  python cli.py confidence-score TSLA")
    print("  python cli.py language-shift MSFT")
    print("  python cli.py hedging-detector NVDA")
    print("  python cli.py econ-calendar")
    print("  python cli.py event-reaction CPI --years 3")
    print("  python cli.py event-volatility FOMC")
    print("  python cli.py event-backtest NFP --years 5")
    print("  python cli.py arb-scan AAPL TSLA NVDA")
    print("  python cli.py arb-spread AAPL")
    print("  python cli.py arb-history TSLA --days 60")
    print("  python cli.py exchange-latency")
    print("  python cli.py dashboard-backtest rsi --ticker AAPL --years 3")
    print("  python cli.py dashboard-backtest volume --ticker TSLA --hold-days 7")
    print("  python cli.py dashboard-performance")
    print("  python cli.py dashboard-optimize NVDA --alert-type breakout")
    print("  python cli.py dashboard-report --output alert_performance.json")
    print("  python cli.py export-pdf AAPL --modules all")
    print("  python cli.py export-pdf TSLA --modules earnings,technicals")
    print("  python cli.py batch-report AAPL,MSFT,GOOGL")
    print("  python cli.py report-template list")
    print("  python cli.py prefetch-stats")
    print("  python cli.py prefetch-warmup")
    print("  python cli.py cache-status")
    print("  python cli.py prefetch-config --top 20 --confidence 0.6")
    print("  python cli.py reconcile-price AAPL")
    print("  python cli.py reconcile-price BTC --type crypto")
    print("  python cli.py data-quality-report")
    print("  python cli.py source-reliability")
    print("  python cli.py discrepancy-log --hours 48 --symbol TSLA")
    print("  python cli.py predict-price AAPL --horizon 5d")
    print("  python cli.py prediction-confidence TSLA")
    print("  python cli.py model-comparison NVDA")
    print("  python cli.py prediction-backtest MSFT --years 1")
    print("  python cli.py country-profile USA")
    print("  python cli.py country-profile CHN --indicators GDP,INFLATION,FDI")
    print("  python cli.py countries --region EAS")
    print("  python cli.py indicator USA GDP")
    print("  python cli.py compare USA,CHN,JPN,DEU,GBR --indicator GDP")
    print("  python cli.py search United")
    print("  python cli.py regional EAS --indicator GDP_GROWTH")
    print("  python cli.py indicators")
    print("  python cli.py spac-list --status announced")
    print("  python cli.py spac-trust DWAC")
    print("  python cli.py spac-timeline LCID")
    print("  python cli.py spac-redemptions DWAC")
    print("  python cli.py spac-arbitrage")
    print("  python cli.py spac-search lucid")
    
    print("\nGlobal PMI Aggregator (Phase 106):")
    print("  python cli.py pmi-country USA                     # US Manufacturing & Services PMI")
    print("  python cli.py pmi-country CHN --type both         # China PMI (both sectors)")
    print("  python cli.py pmi-global manufacturing            # Global PMI snapshot (30+ countries)")
    print("  python cli.py pmi-compare USA,CHN,DEU,JPN        # Compare PMI across major economies")
    print("  python cli.py pmi-regional Europe --type services # European services PMI")
    print("  python cli.py pmi-divergence --months 12          # Mfg vs Services divergence")
    print("  python cli.py pmi-list                            # List all 30+ countries")
    
    print("\nCentral Bank Balance Sheets (Phase 109):")
    print("  python cli.py cb-fed                              # Federal Reserve H.4.1 balance sheet (weekly)")
    print("  python cli.py cb-ecb                              # European Central Bank balance sheet (weekly)")
    print("  python cli.py cb-boj                              # Bank of Japan balance sheet (monthly)")
    print("  python cli.py cb-pboc                             # People's Bank of China balance sheet (monthly)")
    print("  python cli.py cb-global                           # Compare all major central banks (QE/QT status)")
    print("  python cli.py cb-reserves                         # Fed reserve balances detail (liquidity analysis)")
    print("  python cli.py cb-fed --api-key YOUR_KEY          # Use FRED API key for real-time data")
    
    print("  python cli.py pmi")
    print("  python cli.py gdp")
    print("  python cli.py trade")
    print("  python cli.py fx-reserves")
    print("  python cli.py yuan")
    print("  python cli.py industrial")
    print("  python cli.py inflation")
    print("  python cli.py dashboard")
    print("  python cli.py cia-factbook 'United States'")
    print("  python cli.py cia-factbook-compare China 'United States' Russia")
    print("  python cli.py cia-factbook-demographics India")
    print("  python cli.py cia-factbook-military Israel")
    print("  python cli.py cia-factbook-trade Germany")
    print("  python cli.py cia-factbook-resources Brazil")
    print("  python cli.py cia-factbook-scan --output factbook_all.json")
    
    print("\nUS Treasury Auctions & Debt (Phase 118):")
    print("  python cli.py treasury-recent [days] [type]       # Recent auction results (default: 30 days)")
    print("  python cli.py treasury-upcoming [days]            # Upcoming auction schedule")
    print("  python cli.py treasury-tic [country]              # Foreign holdings of US Treasuries")
    print("  python cli.py treasury-debt                       # Current US debt outstanding")
    print("  python cli.py treasury-performance [days]         # Auction performance analysis")
    print("  python cli.py treasury-dashboard                  # Comprehensive dashboard")
    print("  Types: Bill, Note, Bond, TIPS, FRN")
    
    print("\nTreasury Yield Curve (Phase 154):")
    print("  python cli.py yield-curve                         # Current yield curve (1M to 30Y)")
    print("  python cli.py yield-history [days]                # Historical curves (default: 90 days)")
    print("  python cli.py yield-analyze                       # Curve shape analysis & inversions")
    print("  python cli.py yield-compare [days]                # Compare curves (default: 30 days)")
    print("  python cli.py yield-maturity 10Y [days]           # Specific maturity time series")
    
    print("\nSovereign Rating Tracker (Phase 164):")
    print("  python cli.py sovereign-ratings [days]            # All rating changes across S&P/Moody's/Fitch")
    print("  python cli.py sovereign-country <name>            # Ratings for a specific country")
    print("  python cli.py sovereign-downgrades [days]         # Recent sovereign downgrades")
    print("  python cli.py sovereign-upgrades [days]           # Recent sovereign upgrades")
    print("  python cli.py sovereign-watch                     # Countries on negative watch/outlook")
    print("  python cli.py sovereign-ig-changes [days]         # Investment grade transitions (fallen angels/rising stars)")
    print("  python cli.py sovereign-dashboard                 # Comprehensive rating dashboard")
    
    print("\nRelative Valuation Matrix (Phase 143):")
    print("  python cli.py valuation-heatmap [--format text|json]    # Cross-sector valuation comparison heatmap")
    print("  python cli.py valuation-sector Technology               # Get valuation metrics for all stocks in a sector")
    print("  python cli.py valuation-stock AAPL                      # Comprehensive valuation metrics for single stock")
    print("  python cli.py valuation-peers AAPL MSFT GOOGL           # Compare peer group valuation")
    print("  python cli.py valuation-screen pe_trailing 15           # Screen for stocks with P/E below 15")
    print("  python cli.py valuation-screen peg_ratio 1.5 --comparison above  # Find stocks with high PEG")
    print("  python cli.py valuation-sectors                         # List all available sectors")
    
    print("\nADR/GDR Arbitrage Monitor (Phase 147):")
    print("  python cli.py adr-spread BP                             # Calculate arbitrage spread for BP ADR vs London ordinary shares")
    print("  python cli.py adr-scan [--min-spread 50] [--sort-by spread|volume|alpha]")
    print("                                                          # Scan all ADRs for arbitrage opportunities")
    print("  python cli.py adr-compare BABA JD BIDU                  # Compare Chinese ADR spreads side-by-side")
    print("  python cli.py adr-list [--currency JPY]                 # List all known ADR/GDR pairs, optionally filter by currency")
    
    print("\nBIS Global Banking Statistics (Phase 117):")
    print("  python cli.py dataflows                           # List all BIS datasets")
    print("  python cli.py cross-border --reporting US --counterparty CN")
    print("                                                    # Cross-border banking positions")
    print("  python cli.py derivatives                         # OTC derivatives statistics")
    print("  python cli.py derivatives-by-type                 # Derivatives by instrument type")
    print("  python cli.py fx-turnover --year 2022             # FX market turnover (Triennial)")
    print("  python cli.py fx-centers --countries GB,US,SG     # Compare FX market centers")
    print("  python cli.py global-liquidity                    # Global liquidity indicators")
    print("  python cli.py debt-securities --sector financial --currency USD")
    print("                                                    # International debt securities")
    print("  python cli.py property-prices US --type residential")
    print("                                                    # Property price indices")
    print("  python cli.py country-profile GB                  # Comprehensive BIS profile")
    print("  python cli.py countries                           # List BIS reporting countries")
    
    print("\nBIS Credit-to-GDP Gap (Phase 695):")
    print("  python cli.py credit-gap US                       # Get credit gap for a country (early warning indicator)")
    print("  python cli.py g20-credit-heatmap                  # G20 countries credit gap heatmap")
    print("  python cli.py crisis-probability US               # Estimate 3-year crisis probability")
    
    print("\nDTCC Trade Reporting (Phase 696):")
    print("  python cli.py dtcc-swaps [asset_class]            # OTC derivatives cleared volumes (rates, credit, equity, fx, commodity)")
    print("  python cli.py dtcc-repo [days]                    # NY Fed reverse repo operations history")
    print("  python cli.py dtcc-triparty                       # Tri-party repo market statistics")
    print("  python cli.py dtcc-lending                        # Securities lending market data")
    print("  python cli.py dtcc-clearing                       # Central counterparty clearing volumes")
    print("  python cli.py dtcc-ftd [ticker]                   # SEC fails-to-deliver data")
    print("  python cli.py dtcc-risk                           # DTCC systemic risk metrics")
    
    print("\nSAFE China FX Reserves (Phase 699 — FINAL):")
    print("  python cli.py safe-reserves                       # Latest China FX reserves ($3.2T+)")
    print("  python cli.py safe-capital-flows                  # Capital account flows (FDI, portfolio, hot money)")
    print("  python cli.py safe-interventions                  # Estimated PBOC FX intervention activity")
    print("  python cli.py safe-composition                    # Reserves currency composition (USD/EUR/JPY/gold)")
    print("  python cli.py safe-gold                           # PBOC gold reserve purchases (de-dollarization)")
    print("  python cli.py safe-dashboard                      # Comprehensive FX reserves dashboard")
    
    print("\nCarbon Credits & Emissions (Phase 177):")
    print("  python cli.py eu-ets-price [days]                 # EU ETS carbon allowance (EUA) price history")
    print("  python cli.py global-prices                       # Current carbon prices across global compliance markets")
    print("  python cli.py market-stats                        # Comprehensive carbon market statistics and trends")
    print("  python cli.py emissions-by-sector [jurisdiction]  # Emissions breakdown by sector (EU, UK, USA)")
    print("  python cli.py compare-markets [market1,market2]   # Compare carbon pricing mechanisms across jurisdictions")
    print("  python cli.py offset-projects [type]              # Carbon offset project types and registries (forestry, renewable, etc.)")
    
    print("\nCDP Carbon Disclosure (Phase 680):")
    print("  python cli.py cdp-epa TICKER [--year 2023]       # EPA FLIGHT facility-level emissions for US company")
    print("  python cli.py cdp-eprtr COMPANY [--year 2021] [--country DE]")
    print("                                                    # E-PRTR European facility emissions")
    print("  python cli.py cdp-sec CIK [--years 3]            # Search SEC filings for climate disclosures")
    print("  python cli.py cdp-footprint TICKER [--year 2023] [--scope3]")
    print("                                                    # Aggregated carbon footprint from multiple sources")
    
    print("\nEU Taxonomy Alignment (Phase 681):")
    print("  python cli.py taxonomy-score TICKER              # Estimate % revenue aligned with EU Taxonomy")
    print("  python cli.py taxonomy-leaders [--sector renewable_energy] [--min-alignment 50]")
    print("                                                    # Show companies with high taxonomy alignment")
    print("  python cli.py taxonomy-sector renewable_energy   # Sector-specific taxonomy analysis")
    
    print("\nContainer Port Throughput (Phase 193):")
    print("  python cli.py port-all                            # All major ports (Shanghai, Rotterdam, LA/Long Beach) summary")
    print("  python cli.py port-shanghai                       # Shanghai port TEU volumes (world's largest)")
    print("  python cli.py port-rotterdam                      # Rotterdam port TEU volumes (Europe's largest)")
    print("  python cli.py port-la-long-beach                  # LA/Long Beach combined TEU volumes (US gateway)")
    print("  python cli.py port-compare                        # Compare throughput across all tracked ports")
    print("  python cli.py port-list                           # List all available ports with metadata")
    print("  python cli.py port-rankings                       # Global top 20 container port rankings")
    
    print("\nAuto Sales & EV Registrations (Phase 196):")
    print("  python cli.py auto-sales [--country US] [--months 12]")
    print("                                                    # US monthly auto sales from FRED")
    print("  python cli.py ev-registrations [--country US] [--months 12]")
    print("                                                    # EV registration data by country (US, EU, CN, JP, DE, FR, UK, IT, ES)")
    print("  python cli.py auto-market [--region US] [--months 12]")
    print("                                                    # Auto market share by manufacturer (US, EU, CN)")
    print("  python cli.py comprehensive-report [--months 12] # Complete auto sales & EV market report")
    
    print("\nBankruptcy & Default Tracker (Phase 197):")
    print("  python cli.py bankruptcy-search [--days 30] [--limit 50]")
    print("                                                    # Search recent SEC bankruptcy filings")
    print("  python cli.py bankruptcy-tracker --ticker AAPL   # Track bankruptcy risk for specific company")
    print("  python cli.py bankruptcy-stats [--year 2025]     # Bankruptcy statistics by period")
    
    print("\nSatellite Nighttime Lights (Phase 691):")
    print("  python cli.py satellite-monthly [--year 2024] [--month 1] [--region global]")
    print("                                                    # Monthly VIIRS nighttime lights composite")
    print("  python cli.py satellite-urban-growth <city> --years 2012,2024")
    print("                                                    # Urban growth index from multi-year lights")
    print("  python cli.py satellite-gdp <country> [--year 2024]")
    print("                                                    # Economic activity proxy from lights")
    print("  python cli.py satellite-blackouts <region> --start 2024-01-01 --end 2024-03-01")
    print("                                                    # Detect blackouts/disasters from light drops")
    print("  python cli.py satellite-settlements <lat>,<lon> [--radius 10]")
    print("                                                    # Detect new settlements (refugee camps)")
    print("  python cli.py satellite-summary               # Full satellite lights capabilities demo")
    
    print("\nPaper Trading Engine:")
    print("  python cli.py paper-create <name> [--cash 100000]")
    print("                                                    # Create new paper trading portfolio")
    print("  python cli.py paper-buy <ticker> <qty> [--limit price] [--portfolio default]")
    print("                                                    # Execute paper buy order")
    print("  python cli.py paper-sell <ticker> <qty> [--limit price] [--portfolio default]")
    print("                                                    # Execute paper sell order")
    print("  python cli.py paper-positions [--portfolio default]")
    print("                                                    # Show all positions with live P&L")
    print("  python cli.py paper-pnl [--portfolio default]    # Show comprehensive P&L summary")
    print("  python cli.py paper-trades [--portfolio default] [--days 30]")
    print("                                                    # Show trade history")
    print("  python cli.py paper-risk [--portfolio default]   # Show risk metrics")
    print("  python cli.py paper-snapshot [--portfolio default]")
    print("                                                    # Take daily snapshot")
    print("  python cli.py paper-chart [--portfolio default]  # Show ASCII equity curve")
    
    print("\nLIVE Paper Trading - SA Quant Replica (Auto-rebalance on 1st & 15th):")
    print("  python cli.py paper-run [--dry-run]              # Execute rebalance (score → trade → report)")
    print("  python cli.py paper-status                       # Show current portfolio + performance")
    print("  python cli.py paper-history [--limit 50]         # Show trade history")

if __name__ == '__main__':
    sys.exit(dispatch_command(sys.argv[1:]))

    print("\nNighttime Lights Satellite (Phase 691):")
    print("  python cli.py lights-country <CODE> [--year YYYY] # Country nighttime lights intensity")
    print("  python cli.py lights-region --lat <LAT> --lon <LON> [--radius KM]")
    print("                                                    # Regional lights around coordinates")
    print("  python cli.py lights-compare <CODE1,CODE2,...>    # Compare countries by radiance")
    print("  python cli.py lights-trend <CODE> --years YYYY-YYYY")
    print("                                                    # Multi-year economic activity trend")
