#!/usr/bin/env python3
"""
EFFICIENT Alpha Picker V3 Backtest
Optimized for speed: score universe ONCE, use top 100, simulate with price history
"""

import sys
import os
sys.path.insert(0, '/home/quant/apps/quantclaw-data')

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

from modules.alpha_picker import AlphaPickerV3

# Constants
START_DATE = '2023-05-01'
END_DATE = '2026-02-28'
STARTING_CASH = 120000
POSITION_SIZE = 5000
NEW_POSITIONS_PER_REBALANCE = 2

# Parameter grid (36 combinations)
PARAM_GRID = []
for stop_loss in [-0.15, -0.20]:
    for take_profit in [None, 0.75, 1.50]:
        for trailing_stop in [None, -0.15]:
            for pyramid in [None, 2500]:  # None or $2.5K at +15%
                for max_hold_months in [3, 6, None]:  # unlimited = None
                    PARAM_GRID.append({
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'trailing_stop': trailing_stop,
                        'pyramid': pyramid,
                        'max_hold_months': max_hold_months
                    })

print(f"Parameter grid: {len(PARAM_GRID)} combinations")


def load_sa_tickers() -> set:
    """Load Stock Advisor portfolio tickers to exclude"""
    df = pd.read_csv('/home/quant/apps/quantclaw-data/data/stock_picks.csv')
    return set(df['Symbol'].unique())


def generate_rebalance_dates(start: str, end: str) -> List[str]:
    """Generate rebalance dates (1st and 15th of each month)"""
    dates = []
    start_dt = pd.to_datetime(start)
    end_dt = pd.to_datetime(end)
    
    current = start_dt
    while current <= end_dt:
        # 1st of month
        first = current.replace(day=1)
        if first >= start_dt and first <= end_dt:
            dates.append(first.strftime('%Y-%m-%d'))
        
        # 15th of month
        fifteenth = current.replace(day=15)
        if fifteenth >= start_dt and fifteenth <= end_dt:
            dates.append(fifteenth.strftime('%Y-%m-%d'))
        
        # Next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    
    return sorted(dates)


def get_top_100_stocks() -> Tuple[List[str], Dict[str, float]]:
    """Run V3 scorer ONCE to get top 100 non-SA stocks with scores"""
    print("\n📊 Scoring universe with AlphaPickerV3...")
    
    # Load SA tickers to exclude
    sa_tickers = load_sa_tickers()
    print(f"Excluding {len(sa_tickers)} SA portfolio tickers")
    
    # Initialize picker
    picker = AlphaPickerV3()
    
    # Get top picks - request more to have room after filtering SA
    results = picker.get_top_picks(n=200, use_prefilter=True, verbose=True)
    
    # Filter out SA tickers and get top 100
    filtered = [(r['ticker'], r['score']) for r in results if r['ticker'] not in sa_tickers]
    top_100 = filtered[:100]
    
    tickers = [t[0] for t in top_100]
    scores = {t[0]: t[1] for t in top_100}
    
    print(f"✅ Top 100 non-SA stocks identified")
    print(f"Score range: {min(scores.values()):.1f} - {max(scores.values()):.1f}")
    
    return tickers, scores


def download_price_history(tickers: List[str]) -> Dict[str, pd.DataFrame]:
    """Download 3 years of price history for all tickers"""
    print(f"\n📥 Downloading price history for {len(tickers)} stocks...")
    
    price_data = {}
    failed = []
    
    for ticker in tqdm(tickers, desc="Downloading"):
        try:
            df = yf.download(ticker, start='2023-01-01', end=END_DATE, progress=False)
            if df is not None and len(df) > 0:
                price_data[ticker] = df
            else:
                failed.append(ticker)
        except Exception as e:
            failed.append(ticker)
    
    print(f"✅ Downloaded {len(price_data)} / {len(tickers)} stocks")
    if failed:
        print(f"⚠️  Failed: {len(failed)} stocks")
    
    return price_data


def get_price_on_date(price_data: Dict[str, pd.DataFrame], ticker: str, date: str) -> float:
    """Get closing price for a ticker on a specific date (or nearest prior)"""
    if ticker not in price_data:
        return None
    
    df = price_data[ticker]
    target_date = pd.to_datetime(date)
    
    # Get all prices up to target date
    prior_prices = df[df.index <= target_date]
    if len(prior_prices) == 0:
        return None
    
    return float(prior_prices['Close'].iloc[-1])


class Position:
    """Represents a stock position"""
    def __init__(self, ticker: str, shares: float, entry_price: float, entry_date: str, score: float):
        self.ticker = ticker
        self.shares = shares
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.score = score
        self.pyramid_added = False
        self.highest_price = entry_price
        self.pyramid_date = None


def simulate_strategy(
    price_data: Dict[str, pd.DataFrame],
    scores: Dict[str, float],
    rebalance_dates: List[str],
    params: Dict
) -> Dict:
    """Simulate the strategy with given parameters"""
    
    # Unpack parameters
    stop_loss = params['stop_loss']
    take_profit = params['take_profit']
    trailing_stop = params['trailing_stop']
    pyramid = params['pyramid']
    max_hold_months = params['max_hold_months']
    
    # Initialize
    cash = STARTING_CASH
    positions = []  # List of Position objects
    portfolio_value_history = []
    trades = []
    
    for date in rebalance_dates:
        date_dt = pd.to_datetime(date)
        
        # 1. Update trailing stops and check exit conditions
        positions_to_close = []
        for i, pos in enumerate(positions):
            current_price = get_price_on_date(price_data, pos.ticker, date)
            if current_price is None:
                continue
            
            # Update highest price for trailing stop
            if current_price > pos.highest_price:
                pos.highest_price = current_price
            
            # Calculate returns
            pnl_pct = (current_price - pos.entry_price) / pos.entry_price
            drawdown_from_high = (current_price - pos.highest_price) / pos.highest_price
            
            # Check exit conditions
            should_exit = False
            exit_reason = ""
            
            # Stop loss
            if stop_loss and pnl_pct <= stop_loss:
                should_exit = True
                exit_reason = "stop_loss"
            
            # Take profit
            elif take_profit and pnl_pct >= take_profit:
                should_exit = True
                exit_reason = "take_profit"
            
            # Trailing stop
            elif trailing_stop and drawdown_from_high <= trailing_stop:
                should_exit = True
                exit_reason = "trailing_stop"
            
            # Max hold period
            elif max_hold_months:
                months_held = (date_dt - pd.to_datetime(pos.entry_date)).days / 30.4
                if months_held >= max_hold_months:
                    should_exit = True
                    exit_reason = "max_hold"
            
            if should_exit:
                positions_to_close.append((i, current_price, exit_reason))
        
        # Close positions
        for i, exit_price, reason in reversed(positions_to_close):
            pos = positions.pop(i)
            exit_value = pos.shares * exit_price
            cash += exit_value
            trades.append({
                'date': date,
                'ticker': pos.ticker,
                'action': 'sell',
                'shares': pos.shares,
                'price': exit_price,
                'reason': reason
            })
        
        # 2. Check for pyramid opportunities (before buying new)
        if pyramid:
            for pos in positions:
                if pos.pyramid_added:
                    continue
                
                current_price = get_price_on_date(price_data, pos.ticker, date)
                if current_price is None:
                    continue
                
                pnl_pct = (current_price - pos.entry_price) / pos.entry_price
                
                # Pyramid at +15%
                if pnl_pct >= 0.15 and cash >= pyramid:
                    shares_to_add = pyramid / current_price
                    pos.shares += shares_to_add
                    cash -= pyramid
                    pos.pyramid_added = True
                    pos.pyramid_date = date
                    trades.append({
                        'date': date,
                        'ticker': pos.ticker,
                        'action': 'pyramid',
                        'shares': shares_to_add,
                        'price': current_price
                    })
        
        # 3. Buy new positions (2 per rebalance)
        current_tickers = {pos.ticker for pos in positions}
        available_tickers = [t for t in scores.keys() if t not in current_tickers]
        
        # Sort by score
        available_tickers.sort(key=lambda t: scores[t], reverse=True)
        
        new_buys = 0
        for ticker in available_tickers:
            if new_buys >= NEW_POSITIONS_PER_REBALANCE:
                break
            
            if cash < POSITION_SIZE:
                break
            
            entry_price = get_price_on_date(price_data, ticker, date)
            if entry_price is None or entry_price <= 0:
                continue
            
            shares = POSITION_SIZE / entry_price
            positions.append(Position(ticker, shares, entry_price, date, scores[ticker]))
            cash -= POSITION_SIZE
            new_buys += 1
            
            trades.append({
                'date': date,
                'ticker': ticker,
                'action': 'buy',
                'shares': shares,
                'price': entry_price
            })
        
        # 4. Calculate portfolio value
        positions_value = 0
        for pos in positions:
            current_price = get_price_on_date(price_data, pos.ticker, date)
            if current_price:
                positions_value += pos.shares * current_price
        
        total_value = cash + positions_value
        
        portfolio_value_history.append({
            'date': date,
            'cash': cash,
            'positions_value': positions_value,
            'total_value': total_value,
            'num_positions': len(positions)
        })
        
        # Sanity check
        assert abs(cash + positions_value - total_value) < 0.01, f"Accounting error on {date}"
    
    # Calculate metrics
    returns = [(h['total_value'] / STARTING_CASH - 1) for h in portfolio_value_history]
    final_return = returns[-1] if returns else 0
    
    # Sharpe ratio (annualized)
    if len(returns) > 1:
        return_series = pd.Series(returns)
        daily_returns = return_series.diff().dropna()
        if len(daily_returns) > 0 and daily_returns.std() > 0:
            sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
        else:
            sharpe = 0
    else:
        sharpe = 0
    
    # Max drawdown
    max_dd = 0
    peak = STARTING_CASH
    for h in portfolio_value_history:
        if h['total_value'] > peak:
            peak = h['total_value']
        dd = (h['total_value'] - peak) / peak
        if dd < max_dd:
            max_dd = dd
    
    return {
        'params': params,
        'final_value': portfolio_value_history[-1]['total_value'] if portfolio_value_history else STARTING_CASH,
        'final_return': final_return,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_dd,
        'num_trades': len(trades),
        'portfolio_history': portfolio_value_history,
        'trades': trades
    }


def main():
    print("=" * 80)
    print("ALPHA PICKER V3 - OPTIMIZED BACKTEST")
    print("=" * 80)
    
    # Step 1: Get top 100 stocks
    tickers, scores = get_top_100_stocks()
    
    # Step 2: Download price history
    price_data = download_price_history(tickers)
    
    # Step 3: Generate rebalance dates
    rebalance_dates = generate_rebalance_dates(START_DATE, END_DATE)
    print(f"\n📅 Rebalance dates: {len(rebalance_dates)} ({rebalance_dates[0]} to {rebalance_dates[-1]})")
    
    # Step 4: Run backtests for all parameter combinations
    print(f"\n🔄 Running {len(PARAM_GRID)} parameter combinations...")
    
    results = []
    for i, params in enumerate(tqdm(PARAM_GRID, desc="Backtesting")):
        result = simulate_strategy(price_data, scores, rebalance_dates, params)
        results.append(result)
    
    # Step 5: Sort by Sharpe ratio
    results.sort(key=lambda r: r['sharpe_ratio'], reverse=True)
    
    # Step 6: Save results
    output_path = '/home/quant/apps/quantclaw-data/data/optimized_backtest.json'
    with open(output_path, 'w') as f:
        # Convert to JSON-serializable format
        output = {
            'metadata': {
                'start_date': START_DATE,
                'end_date': END_DATE,
                'starting_cash': STARTING_CASH,
                'position_size': POSITION_SIZE,
                'new_positions_per_rebalance': NEW_POSITIONS_PER_REBALANCE,
                'num_combinations': len(PARAM_GRID),
                'top_100_tickers': tickers,
                'scores': scores
            },
            'results': results
        }
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Results saved to {output_path}")
    
    # Step 7: Generate WhatsApp-friendly summary
    summary = []
    summary.append("🎯 ALPHA PICKER V3 - BACKTEST RESULTS")
    summary.append("=" * 50)
    summary.append(f"Period: {START_DATE} to {END_DATE}")
    summary.append(f"Starting Cash: ${STARTING_CASH:,.0f}")
    summary.append(f"Parameter Combos Tested: {len(PARAM_GRID)}")
    summary.append("")
    summary.append("📊 TOP 5 BY SHARPE RATIO:")
    summary.append("")
    
    for i, result in enumerate(results[:5], 1):
        p = result['params']
        summary.append(f"#{i}")
        summary.append(f"Stop Loss: {p['stop_loss']*100:.0f}%")
        summary.append(f"Take Profit: {p['take_profit']*100:.0f}%" if p['take_profit'] else "Take Profit: None")
        summary.append(f"Trailing Stop: {p['trailing_stop']*100:.0f}%" if p['trailing_stop'] else "Trailing Stop: None")
        summary.append(f"Pyramid: ${p['pyramid']:,.0f} at +15%" if p['pyramid'] else "Pyramid: None")
        summary.append(f"Max Hold: {p['max_hold_months']}mo" if p['max_hold_months'] else "Max Hold: Unlimited")
        summary.append(f"Final Value: ${result['final_value']:,.0f}")
        summary.append(f"Return: {result['final_return']*100:.1f}%")
        summary.append(f"Sharpe: {result['sharpe_ratio']:.2f}")
        summary.append(f"Max DD: {result['max_drawdown']*100:.1f}%")
        summary.append(f"Trades: {result['num_trades']}")
        summary.append("")
    
    summary_text = "\n".join(summary)
    summary_path = '/home/quant/apps/quantclaw-data/data/optimized_backtest_summary.txt'
    with open(summary_path, 'w') as f:
        f.write(summary_text)
    
    print(f"✅ Summary saved to {summary_path}")
    print("\n" + summary_text)
    
    # Sanity check on best result
    best = results[0]
    print("\n🔍 SANITY CHECK (Best Result):")
    for i, h in enumerate(best['portfolio_history'][:3]):
        print(f"{h['date']}: Cash=${h['cash']:,.0f} + Positions=${h['positions_value']:,.0f} = ${h['total_value']:,.0f}")


if __name__ == '__main__':
    main()
