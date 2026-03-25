#!/usr/bin/env python3
"""
Alpha Picker Backtest V2
Deterministic backtest with proper portfolio accounting and pyramid logic.
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Configuration
INITIAL_CAPITAL = 100_000
START_DATE = datetime(2023, 5, 1)
END_DATE = datetime(2026, 2, 27)
STOP_LOSS_PCT = -0.15
PYRAMID_THRESHOLD_1 = 0.15  # +15%
PYRAMID_THRESHOLD_2 = 0.30  # +30%

# Parameter grid
WIN_RATES = [0.52, 0.57, 0.65, 0.78, 0.90]
POSITION_SIZES = [0.10, 0.15, 0.20]
PYRAMID_MODES = ['None', 'Moderate', 'Aggressive']


def generate_rebalance_dates(start: datetime, end: datetime) -> List[datetime]:
    """Generate bi-weekly rebalance dates (1st and 15th of each month)."""
    dates = []
    current = start
    
    while current <= end:
        # Add 1st of month
        date_1st = datetime(current.year, current.month, 1)
        if date_1st >= start and date_1st <= end:
            dates.append(date_1st)
        
        # Add 15th of month
        date_15th = datetime(current.year, current.month, 15)
        if date_15th >= start and date_15th <= end:
            dates.append(date_15th)
        
        # Move to next month
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)
    
    return sorted(dates)


def load_and_prepare_picks(csv_path: str, num_trades: int) -> pd.DataFrame:
    """Load stock picks and prepare for cycling through them."""
    df = pd.read_csv(csv_path)
    df['PickDate'] = pd.to_datetime(df['PickDate'])
    df = df.sort_values('PickDate').reset_index(drop=True)
    
    # If we have fewer picks than trades, cycle through them
    if len(df) < num_trades:
        cycles_needed = (num_trades // len(df)) + 1
        df = pd.concat([df] * cycles_needed, ignore_index=True)
    
    return df.iloc[:num_trades].reset_index(drop=True)


def apply_win_rate_filter(picks: pd.DataFrame, win_rate: float) -> pd.DataFrame:
    """
    Apply win rate filter: top X% keep actual returns, bottom (1-X)% get -15%.
    Returns a copy with adjusted returns, maintaining original order.
    """
    df = picks.copy()
    
    # Sort by return to identify winners/losers
    sorted_df = df.sort_values('Return', ascending=False).reset_index(drop=True)
    num_winners = int(len(df) * win_rate)
    
    # Get the symbols of winners (top X%)
    winner_symbols = set(sorted_df.iloc[:num_winners]['Symbol'])
    
    # Apply filter: winners keep actual returns, losers get -15%
    for i in range(len(df)):
        if df.at[i, 'Symbol'] not in winner_symbols:
            df.at[i, 'Return'] = STOP_LOSS_PCT * 100  # Convert back to percentage
    
    return df


def calculate_max_drawdown(equity_curve: List[float]) -> float:
    """Calculate maximum drawdown from equity curve."""
    if not equity_curve:
        return 0.0
    
    peak = equity_curve[0]
    max_dd = 0.0
    
    for value in equity_curve:
        if value > peak:
            peak = value
        
        drawdown = (peak - value) / peak
        max_dd = max(max_dd, drawdown)
    
    return max_dd


def run_backtest(
    picks: pd.DataFrame,
    position_size_pct: float,
    pyramid_mode: str,
    rebalance_dates: List[datetime]
) -> Dict:
    """
    Run backtest with proper portfolio accounting.
    
    FIXED POSITION SIZING:
    - Position sizes are ALWAYS based on INITIAL_CAPITAL, not current portfolio value
    - This prevents exponential compounding and gives realistic results
    - Gains accumulate in cash but don't inflate future bets
    """
    cash = INITIAL_CAPITAL
    positions = {}
    equity_curve = [INITIAL_CAPITAL]
    trades = []
    
    # Calculate base position size once (based on initial capital)
    BASE_POSITION_SIZE = INITIAL_CAPITAL * position_size_pct
    
    # Track for each rebalance
    for i, rebal_date in enumerate(rebalance_dates):
        if i >= len(picks):
            break
        
        pick = picks.iloc[i]
        symbol = pick['Symbol']
        actual_return = pick['Return'] / 100.0  # Convert from percentage
        
        # Close existing position if any
        if positions:
            for pos_symbol, pos_data in list(positions.items()):
                exit_price = pos_data['entry_price'] * (1 + pos_data['cumulative_return'])
                proceeds = pos_data['shares'] * exit_price
                cash += proceeds
                
                trade_return = (proceeds - pos_data['total_invested']) / pos_data['total_invested']
                
                trades.append({
                    'symbol': pos_symbol,
                    'entry_date': pos_data['entry_date'],
                    'exit_date': rebal_date,
                    'return': trade_return,
                    'invested': pos_data['total_invested'],
                    'proceeds': proceeds
                })
            
            positions = {}
        
        # Open new position with FIXED size based on initial capital
        position_size = BASE_POSITION_SIZE
        
        # Skip if we don't have enough cash
        if cash < position_size:
            continue
        
        shares = position_size / 100.0  # Assume entry price of $100 for simplicity
        entry_price = 100.0
        
        cash -= position_size
        
        positions[symbol] = {
            'shares': shares,
            'entry_price': entry_price,
            'original_position_size': BASE_POSITION_SIZE,
            'total_invested': position_size,
            'cumulative_return': 0.0,
            'entry_date': rebal_date,
            'pyramids_added': 0
        }
        
        # Simulate holding period with pyramid opportunities
        # Check at +15% and +30% thresholds
        current_return = 0.0
        
        # Pyramid logic based on actual return (50% of BASE position size)
        if pyramid_mode != 'None' and actual_return > PYRAMID_THRESHOLD_1:
            # First pyramid at +15%
            current_return = PYRAMID_THRESHOLD_1
            pyramid_size = BASE_POSITION_SIZE * 0.5
            
            if cash >= pyramid_size:
                current_price = entry_price * (1 + current_return)
                pyramid_shares = pyramid_size / current_price
                
                cash -= pyramid_size
                positions[symbol]['shares'] += pyramid_shares
                positions[symbol]['total_invested'] += pyramid_size
                positions[symbol]['pyramids_added'] += 1
        
        if pyramid_mode == 'Aggressive' and actual_return > PYRAMID_THRESHOLD_2:
            # Second pyramid at +30%
            current_return = PYRAMID_THRESHOLD_2
            pyramid_size = BASE_POSITION_SIZE * 0.5
            
            if cash >= pyramid_size and positions[symbol]['pyramids_added'] < 2:
                current_price = entry_price * (1 + current_return)
                pyramid_shares = pyramid_size / current_price
                
                cash -= pyramid_size
                positions[symbol]['shares'] += pyramid_shares
                positions[symbol]['total_invested'] += pyramid_size
                positions[symbol]['pyramids_added'] += 1
        
        # Simulate intra-position price movements for drawdown calculation
        # Check at multiple points during hold period
        for check_return in [0.05, 0.10, PYRAMID_THRESHOLD_1, 0.20, 0.25, PYRAMID_THRESHOLD_2, actual_return]:
            if check_return > actual_return:
                break
            
            temp_portfolio_value = cash
            for pos_symbol, pos_data in positions.items():
                check_price = pos_data['entry_price'] * (1 + check_return)
                check_position_value = pos_data['shares'] * check_price
                temp_portfolio_value += check_position_value
            
            equity_curve.append(temp_portfolio_value)
        
        # Final return after hold period
        positions[symbol]['cumulative_return'] = actual_return
        
        # Check stop loss
        if actual_return <= STOP_LOSS_PCT:
            # Close position immediately at stop loss
            exit_price = entry_price * (1 + STOP_LOSS_PCT)
            proceeds = positions[symbol]['shares'] * exit_price
            cash += proceeds
            
            trade_return = (proceeds - positions[symbol]['total_invested']) / positions[symbol]['total_invested']
            
            trades.append({
                'symbol': symbol,
                'entry_date': rebal_date,
                'exit_date': rebal_date,
                'return': trade_return,
                'invested': positions[symbol]['total_invested'],
                'proceeds': proceeds
            })
            
            positions = {}
            
            # Track portfolio value after stop loss
            equity_curve.append(cash)
        else:
            # Calculate current portfolio value at end of period
            portfolio_value = cash
            for pos_symbol, pos_data in positions.items():
                current_price = pos_data['entry_price'] * (1 + pos_data['cumulative_return'])
                position_value = pos_data['shares'] * current_price
                portfolio_value += position_value
            
            equity_curve.append(portfolio_value)
    
    # Close any remaining positions at end
    if positions:
        for pos_symbol, pos_data in positions.items():
            exit_price = pos_data['entry_price'] * (1 + pos_data['cumulative_return'])
            proceeds = pos_data['shares'] * exit_price
            cash += proceeds
            
            trade_return = (proceeds - pos_data['total_invested']) / pos_data['total_invested']
            
            trades.append({
                'symbol': pos_symbol,
                'entry_date': pos_data['entry_date'],
                'exit_date': END_DATE,
                'return': trade_return,
                'invested': pos_data['total_invested'],
                'proceeds': proceeds
            })
    
    final_value = cash
    total_return = (final_value - INITIAL_CAPITAL) / INITIAL_CAPITAL
    
    # Calculate annualized return
    days = (END_DATE - START_DATE).days
    years = days / 365.25
    annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
    
    max_drawdown = calculate_max_drawdown(equity_curve)
    
    # Calculate trade statistics
    winning_trades = [t for t in trades if t['return'] > 0]
    losing_trades = [t for t in trades if t['return'] <= 0]
    
    avg_return = np.mean([t['return'] for t in trades]) if trades else 0
    max_return = max([t['return'] for t in trades]) if trades else 0
    
    return {
        'final_value': final_value,
        'total_return': total_return,
        'annualized_return': annualized_return,
        'max_drawdown': max_drawdown,
        'num_trades': len(trades),
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': len(winning_trades) / len(trades) if trades else 0,
        'avg_return_per_trade': avg_return,
        'max_single_trade_return': max_return,
        'equity_curve': equity_curve,
        'trades': trades
    }


def run_parameter_sweep():
    """Run parameter sweep across all combinations."""
    print("Loading stock picks...")
    rebalance_dates = generate_rebalance_dates(START_DATE, END_DATE)
    num_trades = len(rebalance_dates)
    print(f"Generated {num_trades} rebalance dates")
    
    picks = load_and_prepare_picks('data/stock_picks.csv', num_trades)
    print(f"Loaded {len(picks)} picks")
    
    results = []
    
    total_scenarios = len(WIN_RATES) * len(POSITION_SIZES) * len(PYRAMID_MODES)
    scenario_num = 0
    
    print(f"\nRunning {total_scenarios} scenarios...\n")
    
    for win_rate in WIN_RATES:
        # Apply win rate filter
        filtered_picks = apply_win_rate_filter(picks, win_rate)
        
        for position_size in POSITION_SIZES:
            for pyramid_mode in PYRAMID_MODES:
                scenario_num += 1
                print(f"[{scenario_num}/{total_scenarios}] Win Rate: {win_rate*100:.0f}%, "
                      f"Position: {position_size*100:.0f}%, Pyramid: {pyramid_mode}")
                
                result = run_backtest(
                    filtered_picks,
                    position_size,
                    pyramid_mode,
                    rebalance_dates
                )
                
                result['params'] = {
                    'win_rate': win_rate,
                    'position_size': position_size,
                    'pyramid_mode': pyramid_mode
                }
                
                # Remove trades and equity curve from summary (too large)
                summary_result = {k: v for k, v in result.items() if k not in ['trades', 'equity_curve']}
                results.append(summary_result)
                
                print(f"  → Final: ${result['final_value']:,.0f} | "
                      f"Return: {result['total_return']*100:.1f}% | "
                      f"Ann: {result['annualized_return']*100:.1f}% | "
                      f"MaxDD: {result['max_drawdown']*100:.1f}%\n")
    
    return results


def format_whatsapp_summary(results: List[Dict]) -> str:
    """Format results for WhatsApp (no markdown tables)."""
    output = []
    output.append("=" * 50)
    output.append("📈 ALPHA PICKER BACKTEST V2 RESULTS")
    output.append("=" * 50)
    output.append(f"Initial Capital: ${INITIAL_CAPITAL:,.0f}")
    output.append(f"Period: {START_DATE.date()} to {END_DATE.date()}")
    output.append(f"Total Scenarios: {len(results)}")
    output.append("")
    
    # Find best scenarios
    best_return = max(results, key=lambda x: x['total_return'])
    best_sharpe = max(results, key=lambda x: x['annualized_return'] / max(x['max_drawdown'], 0.01))
    
    output.append("🏆 BEST TOTAL RETURN")
    output.append(f"Win Rate: {best_return['params']['win_rate']*100:.0f}%")
    output.append(f"Position Size: {best_return['params']['position_size']*100:.0f}%")
    output.append(f"Pyramid: {best_return['params']['pyramid_mode']}")
    output.append(f"Final Value: ${best_return['final_value']:,.0f}")
    output.append(f"Total Return: {best_return['total_return']*100:.1f}%")
    output.append(f"Annualized: {best_return['annualized_return']*100:.1f}%")
    output.append(f"Max Drawdown: {best_return['max_drawdown']*100:.1f}%")
    output.append(f"Trades: {best_return['num_trades']}")
    output.append("")
    
    output.append("⚖️ BEST RISK-ADJUSTED (Sharpe)")
    output.append(f"Win Rate: {best_sharpe['params']['win_rate']*100:.0f}%")
    output.append(f"Position Size: {best_sharpe['params']['position_size']*100:.0f}%")
    output.append(f"Pyramid: {best_sharpe['params']['pyramid_mode']}")
    output.append(f"Final Value: ${best_sharpe['final_value']:,.0f}")
    output.append(f"Total Return: {best_sharpe['total_return']*100:.1f}%")
    output.append(f"Annualized: {best_sharpe['annualized_return']*100:.1f}%")
    output.append(f"Max Drawdown: {best_sharpe['max_drawdown']*100:.1f}%")
    output.append(f"Sharpe Proxy: {best_sharpe['annualized_return'] / max(best_sharpe['max_drawdown'], 0.01):.2f}")
    output.append("")
    
    output.append("📊 SANITY CHECKS")
    sample = results[0]
    output.append(f"✓ Avg return per trade: {sample['avg_return_per_trade']*100:.2f}%")
    output.append(f"✓ Max single trade: {sample['max_single_trade_return']*100:.2f}%")
    output.append(f"✓ Number of trades: {sample['num_trades']}")
    output.append(f"✓ Actual win rate: {sample['win_rate']*100:.1f}%")
    output.append("")
    
    output.append("📋 TOP 10 SCENARIOS BY TOTAL RETURN")
    sorted_results = sorted(results, key=lambda x: x['total_return'], reverse=True)[:10]
    
    for i, r in enumerate(sorted_results, 1):
        output.append(f"\n{i}. Win {r['params']['win_rate']*100:.0f}% | "
                     f"Pos {r['params']['position_size']*100:.0f}% | "
                     f"Pyr {r['params']['pyramid_mode']}")
        output.append(f"   Final: ${r['final_value']:,.0f} | "
                     f"Return: {r['total_return']*100:.1f}% | "
                     f"Ann: {r['annualized_return']*100:.1f}%")
        output.append(f"   MaxDD: {r['max_drawdown']*100:.1f}% | "
                     f"Trades: {r['num_trades']}")
    
    output.append("\n" + "=" * 50)
    output.append("✅ Backtest completed successfully")
    output.append("=" * 50)
    
    return "\n".join(output)


def main():
    print("=" * 60)
    print("Alpha Picker Backtest V2 - Deterministic Parameter Sweep")
    print("=" * 60)
    
    results = run_parameter_sweep()
    
    # Save JSON results
    json_path = 'data/backtest_param_sweep_v2.json'
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Saved JSON results to {json_path}")
    
    # Generate and save WhatsApp summary
    summary = format_whatsapp_summary(results)
    txt_path = 'data/backtest_summary_v2.txt'
    with open(txt_path, 'w') as f:
        f.write(summary)
    print(f"✓ Saved summary to {txt_path}")
    
    # Print summary
    print("\n" + summary)


if __name__ == '__main__':
    main()
