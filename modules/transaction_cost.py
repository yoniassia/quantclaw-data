#!/usr/bin/env python3
"""
Transaction Cost Analysis (TCA) — Phase 75

Analyze trading costs for large orders:
1. Market Impact — price movement from executing large trades
2. Bid-Ask Spread — cost of crossing the spread
3. Implementation Shortfall — difference between decision price and execution price
4. Execution Optimization — VWAP/TWAP strategies, optimal trade sizing

Uses free data from Yahoo Finance (bid/ask, volume, historical prices).
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json


def get_realtime_bid_ask(ticker: str) -> Dict:
    """Get current bid/ask spread from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        bid = info.get('bid', 0)
        ask = info.get('ask', 0)
        last_price = info.get('regularMarketPrice', info.get('currentPrice', 0))
        volume = info.get('volume', 0)
        avg_volume = info.get('averageVolume', info.get('averageVolume10days', 0))
        market_cap = info.get('marketCap', 0)
        
        spread = ask - bid if (ask and bid) else 0
        spread_bps = (spread / last_price * 10000) if last_price > 0 else 0
        
        return {
            'ticker': ticker,
            'bid': bid,
            'ask': ask,
            'last_price': last_price,
            'spread': round(spread, 4),
            'spread_bps': round(spread_bps, 2),
            'volume': volume,
            'avg_volume_10d': avg_volume,
            'market_cap': market_cap,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': f"Could not fetch bid/ask for {ticker}: {e}"}


def estimate_market_impact(ticker: str, trade_size_usd: float, period: str = '1mo') -> Dict:
    """
    Estimate market impact using volume-based models.
    
    Market impact models:
    - Kyle's Lambda: Price impact ∝ sqrt(Order Size / Average Daily Volume)
    - Almgren-Chriss: Permanent + Temporary impact components
    
    Args:
        ticker: Stock ticker symbol
        trade_size_usd: Order size in USD
        period: Historical period for volatility estimation
    
    Returns:
        Estimated market impact in basis points
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get historical data for volatility
        hist = stock.history(period=period)
        if hist.empty:
            return {'error': f"No historical data for {ticker}"}
        
        # Current price and volume metrics
        current_price = info.get('regularMarketPrice', hist['Close'].iloc[-1])
        avg_volume = info.get('averageVolume', info.get('averageVolume10days', hist['Volume'].mean()))
        avg_dollar_volume = avg_volume * current_price
        
        # Trade size as % of ADV (Average Daily Volume)
        trade_shares = trade_size_usd / current_price
        participation_rate = trade_shares / avg_volume if avg_volume > 0 else 0
        
        # Daily volatility (annualized)
        returns = hist['Close'].pct_change().dropna()
        daily_volatility = returns.std()
        annual_volatility = daily_volatility * np.sqrt(252)
        
        # Kyle's Lambda model: MI ∝ σ * sqrt(Q / V)
        # where σ = volatility, Q = order size, V = average volume
        # Empirical coefficient ~ 0.1 to 1.0 depending on liquidity
        kyle_coefficient = 0.5  # Conservative estimate
        
        if participation_rate > 0:
            market_impact_bps = kyle_coefficient * daily_volatility * np.sqrt(participation_rate) * 10000
        else:
            market_impact_bps = 0
        
        # Almgren-Chriss decomposition
        # Permanent impact: ~40-60% of total (doesn't revert)
        # Temporary impact: ~40-60% of total (reverts after trade)
        permanent_impact_bps = market_impact_bps * 0.5
        temporary_impact_bps = market_impact_bps * 0.5
        
        # Price impact in USD
        impact_usd = (market_impact_bps / 10000) * trade_size_usd
        
        # Execution urgency factor
        if participation_rate < 0.01:
            urgency = "low"
            recommended_strategy = "TWAP over full day"
        elif participation_rate < 0.05:
            urgency = "moderate"
            recommended_strategy = "VWAP or split into 4-6 child orders"
        elif participation_rate < 0.15:
            urgency = "high"
            recommended_strategy = "Aggressive VWAP, expect significant impact"
        else:
            urgency = "extreme"
            recommended_strategy = "Block trade or dark pool required"
        
        return {
            'ticker': ticker,
            'trade_size_usd': trade_size_usd,
            'trade_shares': int(trade_shares),
            'current_price': round(current_price, 2),
            'avg_daily_volume': int(avg_volume),
            'avg_dollar_volume': round(avg_dollar_volume, 2),
            'participation_rate_pct': round(participation_rate * 100, 2),
            'daily_volatility_pct': round(daily_volatility * 100, 2),
            'annual_volatility_pct': round(annual_volatility * 100, 2),
            'market_impact': {
                'total_bps': round(market_impact_bps, 2),
                'permanent_bps': round(permanent_impact_bps, 2),
                'temporary_bps': round(temporary_impact_bps, 2),
                'impact_usd': round(impact_usd, 2)
            },
            'execution_profile': {
                'urgency': urgency,
                'recommended_strategy': recommended_strategy,
                'estimated_execution_time_minutes': estimate_execution_time(participation_rate)
            },
            'warnings': generate_impact_warnings(participation_rate, market_impact_bps)
        }
    except Exception as e:
        return {'error': f"Could not estimate market impact for {ticker}: {e}"}


def estimate_execution_time(participation_rate: float) -> int:
    """Estimate optimal execution time based on participation rate."""
    if participation_rate < 0.01:
        return 60  # 1 hour
    elif participation_rate < 0.05:
        return 120  # 2 hours
    elif participation_rate < 0.10:
        return 240  # 4 hours
    elif participation_rate < 0.20:
        return 390  # Full trading day
    else:
        return 780  # Multiple days


def generate_impact_warnings(participation_rate: float, impact_bps: float) -> List[str]:
    """Generate warnings based on market impact estimates."""
    warnings = []
    
    if participation_rate > 0.25:
        warnings.append("⚠️ EXTREME: Order size >25% of ADV — major market impact expected")
    elif participation_rate > 0.15:
        warnings.append("⚠️ HIGH: Order size >15% of ADV — significant slippage likely")
    elif participation_rate > 0.05:
        warnings.append("⚠️ MODERATE: Order size >5% of ADV — use algorithmic execution")
    
    if impact_bps > 100:
        warnings.append("⚠️ Expected impact >100 bps — consider dark pool or block trade")
    elif impact_bps > 50:
        warnings.append("⚠️ Expected impact >50 bps — split order across multiple sessions")
    
    if participation_rate < 0.01 and impact_bps < 10:
        warnings.append("✓ Low impact trade — minimal market footprint expected")
    
    return warnings


def calculate_implementation_shortfall(
    ticker: str,
    decision_price: float,
    execution_prices: List[float],
    execution_sizes: List[int],
    side: str = 'buy'
) -> Dict:
    """
    Calculate implementation shortfall (Perold 1988).
    
    Implementation Shortfall = (Decision Price - Avg Execution Price) / Decision Price
    
    Components:
    - Delay Cost: Price movement between decision and first fill
    - Market Impact Cost: Price impact during execution
    - Opportunity Cost: Unfilled portion if order doesn't complete
    
    Args:
        ticker: Stock ticker
        decision_price: Price when trade decision was made
        execution_prices: List of fill prices
        execution_sizes: List of fill sizes (shares)
        side: 'buy' or 'sell'
    
    Returns:
        Implementation shortfall breakdown
    """
    try:
        total_shares = sum(execution_sizes)
        
        # Volume-weighted average execution price
        vwap = sum([p * s for p, s in zip(execution_prices, execution_sizes)]) / total_shares
        
        # Implementation shortfall
        if side.lower() == 'buy':
            shortfall = vwap - decision_price
            shortfall_bps = (shortfall / decision_price) * 10000
        else:  # sell
            shortfall = decision_price - vwap
            shortfall_bps = (shortfall / decision_price) * 10000
        
        # Cost in dollars
        total_cost_usd = abs(shortfall) * total_shares
        
        # Delay cost (first fill vs decision price)
        delay_cost = execution_prices[0] - decision_price if side.lower() == 'buy' else decision_price - execution_prices[0]
        delay_cost_bps = (delay_cost / decision_price) * 10000
        
        # Market impact cost (price progression during execution)
        if len(execution_prices) > 1:
            impact_cost = execution_prices[-1] - execution_prices[0] if side.lower() == 'buy' else execution_prices[0] - execution_prices[-1]
            impact_cost_bps = (impact_cost / decision_price) * 10000
        else:
            impact_cost = 0
            impact_cost_bps = 0
        
        return {
            'ticker': ticker,
            'side': side,
            'total_shares': total_shares,
            'decision_price': round(decision_price, 4),
            'vwap_execution_price': round(vwap, 4),
            'implementation_shortfall': {
                'total_bps': round(shortfall_bps, 2),
                'total_usd': round(total_cost_usd, 2),
                'delay_cost_bps': round(delay_cost_bps, 2),
                'market_impact_bps': round(impact_cost_bps, 2)
            },
            'execution_summary': {
                'num_fills': len(execution_prices),
                'price_range': [round(min(execution_prices), 4), round(max(execution_prices), 4)],
                'avg_fill_size': int(total_shares / len(execution_prices))
            },
            'performance_grade': grade_execution(shortfall_bps, side)
        }
    except Exception as e:
        return {'error': f"Could not calculate implementation shortfall: {e}"}


def grade_execution(shortfall_bps: float, side: str) -> str:
    """Grade execution performance based on implementation shortfall."""
    # For buys, negative shortfall is good (bought below decision price)
    # For sells, positive shortfall is good (sold above decision price)
    
    if side.lower() == 'buy':
        if shortfall_bps < -20:
            return "A+ (Excellent: Beat decision price by >20 bps)"
        elif shortfall_bps < -10:
            return "A (Very Good: Beat decision price by >10 bps)"
        elif shortfall_bps < 0:
            return "B (Good: Beat decision price)"
        elif shortfall_bps < 20:
            return "C (Acceptable: <20 bps slippage)"
        elif shortfall_bps < 50:
            return "D (Poor: 20-50 bps slippage)"
        else:
            return "F (Very Poor: >50 bps slippage)"
    else:  # sell
        if shortfall_bps > 20:
            return "A+ (Excellent: Beat decision price by >20 bps)"
        elif shortfall_bps > 10:
            return "A (Very Good: Beat decision price by >10 bps)"
        elif shortfall_bps > 0:
            return "B (Good: Beat decision price)"
        elif shortfall_bps > -20:
            return "C (Acceptable: <20 bps slippage)"
        elif shortfall_bps > -50:
            return "D (Poor: 20-50 bps slippage)"
        else:
            return "F (Very Poor: >50 bps slippage)"


def optimize_execution_schedule(
    ticker: str,
    total_shares: int,
    execution_window_minutes: int,
    strategy: str = 'vwap'
) -> Dict:
    """
    Generate optimal execution schedule for a large order.
    
    Strategies:
    - TWAP: Time-Weighted Average Price (equal slices over time)
    - VWAP: Volume-Weighted Average Price (trade more during high volume periods)
    - POV: Percentage of Volume (maintain constant participation rate)
    
    Args:
        ticker: Stock ticker
        total_shares: Total order size in shares
        execution_window_minutes: Time window for execution
        strategy: 'twap', 'vwap', or 'pov'
    
    Returns:
        Optimal execution schedule with child orders
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        current_price = info.get('regularMarketPrice', info.get('currentPrice', 0))
        avg_volume = info.get('averageVolume', info.get('averageVolume10days', 0))
        
        # Intraday volume profile (typical U-shaped pattern)
        # Hour 1 (9:30-10:30): 25% of volume
        # Hour 2-5: 10% each
        # Hour 6 (3:00-4:00): 20% of volume
        volume_profile = {
            '09:30-10:30': 0.25,
            '10:30-11:30': 0.10,
            '11:30-12:30': 0.10,
            '12:30-13:30': 0.10,
            '13:30-14:30': 0.10,
            '14:30-15:30': 0.15,
            '15:30-16:00': 0.20
        }
        
        # Number of child orders
        num_children = max(4, min(20, execution_window_minutes // 15))
        
        if strategy.lower() == 'twap':
            # Equal size slices
            child_shares = [total_shares // num_children] * num_children
            # Handle remainder
            child_shares[-1] += total_shares % num_children
            
            schedule = []
            for i, shares in enumerate(child_shares):
                schedule.append({
                    'order_num': i + 1,
                    'shares': shares,
                    'pct_of_total': round(shares / total_shares * 100, 1),
                    'estimated_time_minutes': (i + 1) * (execution_window_minutes / num_children),
                    'strategy_note': 'Equal-weighted slice'
                })
        
        elif strategy.lower() == 'vwap':
            # Weight by typical volume profile
            schedule = []
            remaining_shares = total_shares
            
            for i, (time_bucket, volume_weight) in enumerate(volume_profile.items()):
                if i < num_children:
                    shares = int(total_shares * volume_weight)
                    remaining_shares -= shares
                    schedule.append({
                        'order_num': i + 1,
                        'time_bucket': time_bucket,
                        'shares': shares,
                        'pct_of_total': round(shares / total_shares * 100, 1),
                        'volume_weight': round(volume_weight * 100, 1),
                        'strategy_note': 'Volume-weighted slice'
                    })
            
            # Add remainder to largest bucket
            if remaining_shares > 0 and schedule:
                schedule[0]['shares'] += remaining_shares
        
        elif strategy.lower() == 'pov':
            # Percentage of Volume strategy (e.g., 5% of volume)
            target_participation = 0.05
            estimated_volume = avg_volume
            shares_per_interval = int(estimated_volume * target_participation / num_children)
            
            schedule = []
            for i in range(num_children):
                schedule.append({
                    'order_num': i + 1,
                    'shares': shares_per_interval,
                    'pct_of_total': round(shares_per_interval / total_shares * 100, 1),
                    'estimated_time_minutes': (i + 1) * (execution_window_minutes / num_children),
                    'participation_rate_pct': round(target_participation * 100, 1),
                    'strategy_note': 'Constant participation rate'
                })
        
        else:
            return {'error': f"Unknown strategy: {strategy}. Use 'twap', 'vwap', or 'pov'"}
        
        # Summary metrics
        notional_value = total_shares * current_price
        avg_child_size = total_shares / len(schedule)
        
        return {
            'ticker': ticker,
            'strategy': strategy.upper(),
            'total_shares': total_shares,
            'notional_value_usd': round(notional_value, 2),
            'current_price': round(current_price, 2),
            'execution_window_minutes': execution_window_minutes,
            'num_child_orders': len(schedule),
            'avg_child_size': int(avg_child_size),
            'schedule': schedule,
            'execution_guidance': generate_execution_guidance(strategy, total_shares, avg_volume)
        }
    except Exception as e:
        return {'error': f"Could not generate execution schedule: {e}"}


def generate_execution_guidance(strategy: str, total_shares: int, avg_volume: int) -> List[str]:
    """Generate execution guidance based on strategy and order size."""
    guidance = []
    participation = total_shares / avg_volume if avg_volume > 0 else 0
    
    if strategy.lower() == 'twap':
        guidance.append("TWAP: Equal-sized orders at regular intervals")
        guidance.append("Best for: Low urgency, minimizing timing risk")
        guidance.append("Risk: May underperform if volume is unevenly distributed")
    
    elif strategy.lower() == 'vwap':
        guidance.append("VWAP: Trade more during high volume periods (open/close)")
        guidance.append("Best for: Benchmark execution, institutional orders")
        guidance.append("Risk: Predictable pattern may be front-run")
    
    elif strategy.lower() == 'pov':
        guidance.append("POV: Maintain constant % of market volume")
        guidance.append("Best for: Adapting to changing liquidity conditions")
        guidance.append("Risk: Completion time is uncertain")
    
    if participation > 0.10:
        guidance.append("⚠️ High participation rate — consider dark pool for first 50%")
    
    return guidance


def compare_execution_costs(ticker: str, trade_size_usd: float) -> Dict:
    """
    Compare estimated costs across different execution strategies.
    
    Returns comparative analysis of TWAP vs VWAP vs POV vs immediate execution.
    """
    try:
        # Get market impact estimate
        impact = estimate_market_impact(ticker, trade_size_usd)
        if 'error' in impact:
            return impact
        
        # Get bid-ask spread
        spread_data = get_realtime_bid_ask(ticker)
        spread_bps = spread_data.get('spread_bps', 0)
        
        # Estimate costs for each strategy
        strategies = {
            'immediate': {
                'description': 'Market order (immediate execution)',
                'spread_cost_bps': spread_bps,
                'market_impact_bps': impact['market_impact']['total_bps'],
                'timing_risk_bps': 0,
                'total_cost_bps': spread_bps + impact['market_impact']['total_bps']
            },
            'twap': {
                'description': 'TWAP over 4 hours',
                'spread_cost_bps': spread_bps,
                'market_impact_bps': impact['market_impact']['total_bps'] * 0.5,  # Lower impact with split
                'timing_risk_bps': 15,  # Risk of adverse price movement
                'total_cost_bps': spread_bps + (impact['market_impact']['total_bps'] * 0.5) + 15
            },
            'vwap': {
                'description': 'VWAP over full day',
                'spread_cost_bps': spread_bps,
                'market_impact_bps': impact['market_impact']['total_bps'] * 0.4,  # Lower impact
                'timing_risk_bps': 20,  # Higher timing risk over full day
                'total_cost_bps': spread_bps + (impact['market_impact']['total_bps'] * 0.4) + 20
            },
            'dark_pool': {
                'description': 'Dark pool / block trade',
                'spread_cost_bps': spread_bps * 0.5,  # Tighter spreads in dark pools
                'market_impact_bps': impact['market_impact']['permanent_bps'],  # Only permanent impact
                'timing_risk_bps': 5,  # Lower timing risk
                'total_cost_bps': (spread_bps * 0.5) + impact['market_impact']['permanent_bps'] + 5
            }
        }
        
        # Calculate USD costs
        for strategy_name, strategy_data in strategies.items():
            strategy_data['total_cost_usd'] = round(
                (strategy_data['total_cost_bps'] / 10000) * trade_size_usd, 2
            )
        
        # Find optimal strategy
        optimal = min(strategies.items(), key=lambda x: x[1]['total_cost_bps'])
        
        return {
            'ticker': ticker,
            'trade_size_usd': trade_size_usd,
            'strategies': strategies,
            'recommended_strategy': {
                'name': optimal[0],
                'description': optimal[1]['description'],
                'total_cost_bps': round(optimal[1]['total_cost_bps'], 2),
                'total_cost_usd': optimal[1]['total_cost_usd'],
                'cost_savings_vs_immediate_usd': round(
                    strategies['immediate']['total_cost_usd'] - optimal[1]['total_cost_usd'], 2
                )
            },
            'analysis': generate_cost_analysis(strategies, impact['participation_rate_pct'])
        }
    except Exception as e:
        return {'error': f"Could not compare execution costs: {e}"}


def generate_cost_analysis(strategies: Dict, participation_rate: float) -> List[str]:
    """Generate analysis comparing execution strategies."""
    analysis = []
    
    immediate_cost = strategies['immediate']['total_cost_bps']
    dark_pool_cost = strategies['dark_pool']['total_cost_bps']
    
    if participation_rate > 15:
        analysis.append("High participation rate — dark pool strongly recommended")
    elif participation_rate > 5:
        analysis.append("Moderate participation rate — consider VWAP or dark pool")
    else:
        analysis.append("Low participation rate — any strategy should work well")
    
    savings = immediate_cost - dark_pool_cost
    if savings > 30:
        analysis.append(f"Dark pool could save {savings:.0f} bps vs immediate execution")
    
    return analysis


if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Transaction Cost Analysis')
    parser.add_argument('command', choices=['tca-spread', 'tca-impact', 'tca-shortfall', 'tca-optimize', 'tca-compare'])
    parser.add_argument('ticker', help='Stock ticker symbol')
    parser.add_argument('--trade-size', type=float, help='Trade size in USD')
    parser.add_argument('--decision-price', type=float, help='Decision price for shortfall calculation')
    parser.add_argument('--exec-prices', nargs='+', type=float, help='Execution prices')
    parser.add_argument('--exec-sizes', nargs='+', type=int, help='Execution sizes')
    parser.add_argument('--side', choices=['buy', 'sell'], default='buy', help='Trade side')
    parser.add_argument('--total-shares', type=int, help='Total shares for optimization')
    parser.add_argument('--window', type=int, default=240, help='Execution window in minutes')
    parser.add_argument('--strategy', choices=['twap', 'vwap', 'pov'], default='vwap', help='Execution strategy')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'tca-spread':
            result = get_realtime_bid_ask(args.ticker.upper())
        
        elif args.command == 'tca-impact':
            if not args.trade_size:
                print("Error: --trade-size required for tca-impact", file=sys.stderr)
                sys.exit(1)
            result = estimate_market_impact(args.ticker.upper(), args.trade_size)
        
        elif args.command == 'tca-shortfall':
            if not all([args.decision_price, args.exec_prices, args.exec_sizes]):
                print("Error: --decision-price, --exec-prices, and --exec-sizes required for tca-shortfall", file=sys.stderr)
                sys.exit(1)
            result = calculate_implementation_shortfall(
                args.ticker.upper(),
                args.decision_price,
                args.exec_prices,
                args.exec_sizes,
                args.side
            )
        
        elif args.command == 'tca-optimize':
            if not args.total_shares:
                print("Error: --total-shares required for tca-optimize", file=sys.stderr)
                sys.exit(1)
            result = optimize_execution_schedule(
                args.ticker.upper(),
                args.total_shares,
                args.window,
                args.strategy
            )
        
        elif args.command == 'tca-compare':
            if not args.trade_size:
                print("Error: --trade-size required for tca-compare", file=sys.stderr)
                sys.exit(1)
            result = compare_execution_costs(args.ticker.upper(), args.trade_size)
        
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
