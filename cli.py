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
    'multi_timeframe': {
        'file': 'multi_timeframe.py',
        'commands': ['mtf', 'trend-alignment', 'signal-confluence']
    },
    'alerts': {
        'file': 'smart_alerts.py',
        'commands': ['alert-create', 'alert-list', 'alert-check', 'alert-delete', 'alert-history', 'alert-stats']
    },
    'order_book': {
        'file': 'order_book.py',
        'commands': ['order-book', 'bid-ask', 'liquidity', 'imbalance', 'support-resistance']
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
    'satellite': {
        'file': 'satellite_proxies.py',
        'commands': ['satellite-proxy', 'shipping-index', 'construction-activity', 'foot-traffic', 'economic-index']
    },
    'fed_policy': {
        'file': 'fed_policy.py',
        'commands': ['fed-watch', 'rate-probability', 'fomc-calendar', 'dot-plot', 'yield-curve', 'current-rate']
    },
    'crypto_onchain': {
        'file': 'crypto_onchain.py',
        'commands': ['onchain', 'whale-watch', 'dex-volume', 'gas-fees', 'token-flows']
    },
    'earnings_nlp': {
        'file': 'earnings_nlp.py',
        'commands': ['earnings-tone', 'confidence-score', 'dodge-detect']
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
    
    print("\nCrypto On-Chain Analytics (Phase 43):")
    print("  python cli.py onchain ETH                          # Get Ethereum on-chain metrics")
    print("  python cli.py whale-watch BTC [--min 100]          # Track Bitcoin whale wallets")
    print("  python cli.py dex-volume [--protocol uniswap] [--chain ethereum]")
    print("  python cli.py gas-fees                             # Current Ethereum gas fees")
    print("  python cli.py token-flows USDT [--hours 24]        # Track token transfer volumes")
    
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

if __name__ == '__main__':
    sys.exit(dispatch_command(sys.argv[1:]))
