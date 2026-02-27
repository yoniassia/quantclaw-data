#!/usr/bin/env python3
"""
Comprehensive Optimized Backtest for Alpha Picker V3
Parameter grid optimization with proper portfolio accounting
"""

import sys
import os
sys.path.insert(0, '/home/quant/apps/quantclaw-data')

from modules.alpha_picker import AlphaPickerV3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import yfinance as yf
from itertools import product
import json
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')


class Position:
    """Track individual position with pyramiding support"""
    def __init__(self, ticker: str, entry_date: datetime, entry_price: float, shares: float, score: float):
        self.ticker = ticker
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.shares = shares
        self.entry_score = score
        self.peak_price = entry_price
        self.pyramids = []  # List of (date, price, shares, cost)
        
    @property
    def total_shares(self) -> float:
        return self.shares + sum(p[2] for p in self.pyramids)
    
    @property
    def total_cost(self) -> float:
        base_cost = self.shares * self.entry_price
        pyramid_cost = sum(p[3] for p in self.pyramids)
        return base_cost + pyramid_cost
    
    @property
    def avg_entry_price(self) -> float:
        return self.total_cost / self.total_shares if self.total_shares > 0 else self.entry_price
    
    def add_pyramid(self, date: datetime, price: float, amount: float):
        """Add to position"""
        shares = amount / price
        self.pyramids.append((date, price, shares, amount))
        
    def current_value(self, current_price: float) -> float:
        """Current market value"""
        return self.total_shares * current_price
    
    def pnl(self, current_price: float) -> float:
        """Profit/loss"""
        return self.current_value(current_price) - self.total_cost
    
    def return_pct(self, current_price: float) -> float:
        """Return percentage based on total cost"""
        return (current_price / self.avg_entry_price - 1) if self.avg_entry_price > 0 else 0


class BacktestEngine:
    """
    Comprehensive backtest engine with parameter optimization
    """
    
    def __init__(self, 
                 starting_cash: float = 120000,
                 position_size: float = 5000,
                 rebalance_dates: List[datetime] = None,
                 sa_exclusions: List[str] = None):
        
        self.starting_cash = starting_cash
        self.position_size = position_size
        self.rebalance_dates = rebalance_dates or []
        self.sa_exclusions = set(sa_exclusions or [])
        
        # Initialize Alpha Picker
        self.picker = AlphaPickerV3()
        
        # State
        self.cash = starting_cash
        self.positions: Dict[str, Position] = {}
        self.closed_trades = []
        self.equity_curve = []
        self.rebalance_log = []
        
    def get_price(self, ticker: str, date: datetime) -> Optional[float]:
        """Get historical price for ticker on specific date"""
        try:
            stock = yf.Ticker(ticker)
            # Get data around the date
            start = date - timedelta(days=7)
            end = date + timedelta(days=7)
            hist = stock.history(start=start, end=end)
            
            if hist is None or len(hist) == 0:
                return None
            
            # Find closest date
            hist.index = pd.to_datetime(hist.index).tz_localize(None)
            closest_idx = hist.index.get_indexer([date], method='nearest')[0]
            
            if closest_idx >= 0 and closest_idx < len(hist):
                return float(hist['Close'].iloc[closest_idx])
            
            return None
        except:
            return None
    
    def get_current_portfolio_value(self, date: datetime) -> float:
        """Calculate total portfolio value"""
        positions_value = 0
        
        for ticker, pos in self.positions.items():
            price = self.get_price(ticker, date)
            if price:
                positions_value += pos.current_value(price)
        
        return self.cash + positions_value
    
    def check_exit_criteria(self, ticker: str, pos: Position, current_price: float, 
                           current_score: float, params: dict, date: datetime) -> Tuple[bool, str]:
        """Check if position should be closed"""
        
        # Stop loss
        stop_loss = params.get('stop_loss')
        if stop_loss and pos.return_pct(current_price) <= stop_loss:
            return True, f"stop_loss_{abs(stop_loss)*100:.0f}pct"
        
        # Take profit
        take_profit = params.get('take_profit')
        if take_profit and pos.return_pct(current_price) >= take_profit:
            return True, f"take_profit_{take_profit*100:.0f}pct"
        
        # Score-based exit
        score_exit = params.get('score_exit_threshold')
        if score_exit and current_score < score_exit:
            return True, f"score_below_{score_exit}"
        
        # Time-based exit
        max_hold_days = params.get('max_hold_days')
        if max_hold_days:
            days_held = (date - pos.entry_date).days
            if days_held >= max_hold_days:
                return True, f"max_hold_{max_hold_days}days"
        
        # Trailing stop
        trailing_stop = params.get('trailing_stop')
        if trailing_stop:
            # Update peak
            if current_price > pos.peak_price:
                pos.peak_price = current_price
            
            drawdown = (current_price / pos.peak_price - 1)
            if drawdown <= trailing_stop:
                return True, f"trailing_stop_{abs(trailing_stop)*100:.0f}pct"
        
        return False, ""
    
    def check_pyramid_opportunity(self, ticker: str, pos: Position, current_price: float,
                                  current_score: float, params: dict) -> Optional[float]:
        """Check if we should add to position (pyramid)"""
        pyramid_cfg = params.get('pyramid')
        if not pyramid_cfg or pyramid_cfg == 'none':
            return None
        
        # Check if score still strong
        if current_score <= 30:
            return None
        
        current_return = pos.return_pct(current_price)
        
        if pyramid_cfg == 'add_2.5k_at_15pct':
            if current_return >= 0.15 and len(pos.pyramids) == 0:
                return 2500
        
        elif pyramid_cfg == 'add_2.5k_at_15_and_30pct':
            if current_return >= 0.30 and len(pos.pyramids) == 1:
                return 2500
            elif current_return >= 0.15 and len(pos.pyramids) == 0:
                return 2500
        
        elif pyramid_cfg == 'double_down_5k_at_20pct':
            if current_return >= 0.20 and len(pos.pyramids) == 0:
                return 5000
        
        return None
    
    def run_backtest(self, params: dict, verbose: bool = False) -> dict:
        """Run single backtest with given parameters"""
        
        # Reset state
        self.cash = self.starting_cash
        self.positions = {}
        self.closed_trades = []
        self.equity_curve = []
        self.rebalance_log = []
        
        if verbose:
            print(f"\nRunning backtest with params: {params}")
        
        # Track metrics
        peak_value = self.starting_cash
        max_drawdown = 0
        
        for date in self.rebalance_dates:
            if verbose:
                print(f"\n{'='*60}")
                print(f"Rebalance date: {date.strftime('%Y-%m-%d')}")
            
            # Score all existing positions
            positions_to_close = []
            positions_to_pyramid = []
            
            for ticker, pos in self.positions.items():
                current_price = self.get_price(ticker, date)
                if not current_price:
                    if verbose:
                        print(f"  Warning: No price for {ticker}, skipping")
                    continue
                
                # Score the stock
                result = self.picker.score_stock(ticker, as_of_date=date)
                current_score = result.get('score', 0)
                
                # Check exit criteria
                should_exit, exit_reason = self.check_exit_criteria(
                    ticker, pos, current_price, current_score, params, date
                )
                
                if should_exit:
                    positions_to_close.append((ticker, pos, current_price, exit_reason))
                else:
                    # Check pyramid opportunity
                    pyramid_amount = self.check_pyramid_opportunity(
                        ticker, pos, current_price, current_score, params
                    )
                    if pyramid_amount and self.cash >= pyramid_amount:
                        positions_to_pyramid.append((ticker, pos, current_price, pyramid_amount))
            
            # Close positions
            for ticker, pos, exit_price, exit_reason in positions_to_close:
                pnl = pos.pnl(exit_price)
                ret_pct = pos.return_pct(exit_price)
                hold_days = (date - pos.entry_date).days
                
                self.cash += pos.current_value(exit_price)
                
                self.closed_trades.append({
                    'ticker': ticker,
                    'entry_date': pos.entry_date.strftime('%Y-%m-%d'),
                    'exit_date': date.strftime('%Y-%m-%d'),
                    'entry_price': pos.avg_entry_price,
                    'exit_price': exit_price,
                    'shares': pos.total_shares,
                    'cost': pos.total_cost,
                    'pnl': pnl,
                    'return_pct': ret_pct,
                    'hold_days': hold_days,
                    'exit_reason': exit_reason
                })
                
                del self.positions[ticker]
                
                if verbose:
                    print(f"  CLOSE {ticker}: {ret_pct:+.1%} ({exit_reason}) | Hold: {hold_days}d | P&L: ${pnl:,.0f}")
            
            # Pyramid positions
            for ticker, pos, price, amount in positions_to_pyramid:
                pos.add_pyramid(date, price, amount)
                self.cash -= amount
                
                if verbose:
                    print(f"  PYRAMID {ticker}: +${amount:,.0f} @ ${price:.2f} | Return: {pos.return_pct(price):+.1%}")
            
            # Score universe and find new picks
            max_positions = params.get('max_positions', 999)
            max_per_sector = params.get('max_per_sector', 999)
            min_score = params.get('min_entry_score', 25)
            cash_reserve_pct = params.get('cash_reserve_pct', 0)
            
            positions_to_open = max(0, max_positions - len(self.positions))
            
            if positions_to_open > 0:
                # Calculate available cash
                total_value = self.get_current_portfolio_value(date)
                min_cash = total_value * cash_reserve_pct
                available_cash = max(0, self.cash - min_cash)
                
                max_new_positions = min(positions_to_open, int(available_cash / self.position_size))
                
                if max_new_positions > 0:
                    # Pre-filter universe
                    candidates = self.picker.prefilter_universe(min_6m_return=0.05, as_of_date=date, verbose=False)
                    
                    # Remove SA exclusions and existing positions
                    candidates = [t for t in candidates if t not in self.sa_exclusions and t not in self.positions]
                    
                    if verbose:
                        print(f"  Candidates after filter: {len(candidates)}")
                    
                    # Score candidates
                    scored = []
                    for ticker in candidates[:100]:  # Limit to top 100 for speed
                        result = self.picker.score_stock(ticker, as_of_date=date)
                        if result['score'] >= min_score:
                            scored.append(result)
                    
                    # Sort by score
                    scored.sort(key=lambda x: x['score'], reverse=True)
                    
                    # Check sector limits
                    sector_counts = {}
                    for ticker, pos in self.positions.items():
                        result = self.picker.score_stock(ticker, as_of_date=date)
                        sector = result.get('sector', 'Unknown')
                        sector_counts[sector] = sector_counts.get(sector, 0) + 1
                    
                    # Open new positions
                    opened = 0
                    for result in scored:
                        if opened >= max_new_positions:
                            break
                        
                        ticker = result['ticker']
                        sector = result.get('sector', 'Unknown')
                        
                        # Check sector limit
                        if sector_counts.get(sector, 0) >= max_per_sector:
                            continue
                        
                        # Get entry price
                        entry_price = self.get_price(ticker, date)
                        if not entry_price:
                            continue
                        
                        # Open position
                        shares = self.position_size / entry_price
                        pos = Position(ticker, date, entry_price, shares, result['score'])
                        self.positions[ticker] = pos
                        self.cash -= self.position_size
                        
                        sector_counts[sector] = sector_counts.get(sector, 0) + 1
                        opened += 1
                        
                        if verbose:
                            print(f"  OPEN {ticker}: Score={result['score']:.1f} | ${entry_price:.2f} | {shares:.1f} shares | Sector={sector}")
            
            # Record equity curve
            portfolio_value = self.get_current_portfolio_value(date)
            self.equity_curve.append({
                'date': date.strftime('%Y-%m-%d'),
                'portfolio_value': portfolio_value,
                'cash': self.cash,
                'positions_value': portfolio_value - self.cash,
                'num_positions': len(self.positions)
            })
            
            # Update drawdown
            if portfolio_value > peak_value:
                peak_value = portfolio_value
            
            current_drawdown = (portfolio_value / peak_value - 1) if peak_value > 0 else 0
            max_drawdown = min(max_drawdown, current_drawdown)
            
            # Sanity check
            calculated_value = self.cash + sum(
                pos.current_value(self.get_price(ticker, date) or 0) 
                for ticker, pos in self.positions.items()
            )
            
            if abs(calculated_value - portfolio_value) > 1:
                print(f"  WARNING: Portfolio accounting mismatch! Calculated={calculated_value:.2f}, Recorded={portfolio_value:.2f}")
        
        # Close all remaining positions at end
        final_date = self.rebalance_dates[-1]
        for ticker, pos in list(self.positions.items()):
            exit_price = self.get_price(ticker, final_date)
            if exit_price:
                pnl = pos.pnl(exit_price)
                ret_pct = pos.return_pct(exit_price)
                hold_days = (final_date - pos.entry_date).days
                
                self.cash += pos.current_value(exit_price)
                
                self.closed_trades.append({
                    'ticker': ticker,
                    'entry_date': pos.entry_date.strftime('%Y-%m-%d'),
                    'exit_date': final_date.strftime('%Y-%m-%d'),
                    'entry_price': pos.avg_entry_price,
                    'exit_price': exit_price,
                    'shares': pos.total_shares,
                    'cost': pos.total_cost,
                    'pnl': pnl,
                    'return_pct': ret_pct,
                    'hold_days': hold_days,
                    'exit_reason': 'backtest_end'
                })
        
        self.positions = {}
        
        # Calculate metrics
        final_value = self.cash
        total_return = (final_value / self.starting_cash - 1)
        
        # Calculate annualized return
        days = (self.rebalance_dates[-1] - self.rebalance_dates[0]).days
        years = days / 365.25
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        # Calculate Sharpe ratio
        if len(self.equity_curve) > 1:
            returns = []
            for i in range(1, len(self.equity_curve)):
                prev_val = self.equity_curve[i-1]['portfolio_value']
                curr_val = self.equity_curve[i]['portfolio_value']
                ret = (curr_val / prev_val - 1) if prev_val > 0 else 0
                returns.append(ret)
            
            if len(returns) > 0 and np.std(returns) > 0:
                sharpe = np.mean(returns) / np.std(returns) * np.sqrt(24)  # 24 rebalances per year
            else:
                sharpe = 0
        else:
            sharpe = 0
        
        # Win rate
        winning_trades = [t for t in self.closed_trades if t['return_pct'] > 0]
        win_rate = len(winning_trades) / len(self.closed_trades) if self.closed_trades else 0
        
        # Avg win/loss
        avg_win = np.mean([t['return_pct'] for t in winning_trades]) if winning_trades else 0
        losing_trades = [t for t in self.closed_trades if t['return_pct'] <= 0]
        avg_loss = np.mean([t['return_pct'] for t in losing_trades]) if losing_trades else 0
        
        results = {
            'params': params,
            'final_value': final_value,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'num_trades': len(self.closed_trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_hold_days': np.mean([t['hold_days'] for t in self.closed_trades]) if self.closed_trades else 0,
            'equity_curve': self.equity_curve,
            'trades': self.closed_trades
        }
        
        return results


def generate_rebalance_dates(start: str, end: str) -> List[datetime]:
    """Generate 1st and 15th of each month between start and end"""
    start_dt = datetime.strptime(start, '%Y-%m-%d')
    end_dt = datetime.strptime(end, '%Y-%m-%d')
    
    dates = []
    current = start_dt
    
    while current <= end_dt:
        # 1st of month
        first = datetime(current.year, current.month, 1)
        if start_dt <= first <= end_dt:
            dates.append(first)
        
        # 15th of month
        fifteenth = datetime(current.year, current.month, 15)
        if start_dt <= fifteenth <= end_dt:
            dates.append(fifteenth)
        
        # Next month
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)
    
    return sorted(dates)


def load_sa_exclusions() -> List[str]:
    """Load SA portfolio exclusions"""
    df = pd.read_csv('/home/quant/apps/quantclaw-data/data/stock_picks.csv')
    return df['Symbol'].unique().tolist()


def generate_parameter_grid() -> List[dict]:
    """Generate all parameter combinations to test"""
    
    # Exit strategies
    stop_losses = [None, -0.10, -0.15, -0.20, -0.25]
    take_profits = [None, 0.50, 0.75, 1.00, 1.50]
    score_exits = [None, 10, 15, 20, 25]
    max_holds = [None, 30, 60, 90, 180, 365]
    trailing_stops = [None, -0.10, -0.15, -0.20]
    
    # Pyramid strategies
    pyramids = ['none', 'add_2.5k_at_15pct', 'add_2.5k_at_15_and_30pct', 'double_down_5k_at_20pct']
    
    # Risk management
    max_positions = [5, 10, 15, 20, 999]
    max_per_sectors = [2, 3, 5, 999]
    min_entry_scores = [20, 25, 30, 35, 40]
    cash_reserves = [0, 0.10, 0.20]
    
    # Generate smart combinations (not full factorial - would be too many)
    params_list = []
    
    # Strategy 1: Conservative (tight stops, limits)
    for sl, tp, me in product([-0.10, -0.15], [0.50, 0.75], [30, 35, 40]):
        params_list.append({
            'stop_loss': sl,
            'take_profit': tp,
            'score_exit_threshold': 20,
            'max_hold_days': 90,
            'trailing_stop': None,
            'pyramid': 'none',
            'max_positions': 10,
            'max_per_sector': 3,
            'min_entry_score': me,
            'cash_reserve_pct': 0.10,
            'strategy_type': 'conservative'
        })
    
    # Strategy 2: Aggressive (wider stops, pyramiding)
    for sl, tp, pyr in product([-0.20, -0.25], [1.00, 1.50], ['add_2.5k_at_15pct', 'double_down_5k_at_20pct']):
        params_list.append({
            'stop_loss': sl,
            'take_profit': tp,
            'score_exit_threshold': 15,
            'max_hold_days': 180,
            'trailing_stop': None,
            'pyramid': pyr,
            'max_positions': 20,
            'max_per_sector': 5,
            'min_entry_score': 25,
            'cash_reserve_pct': 0,
            'strategy_type': 'aggressive'
        })
    
    # Strategy 3: Trailing stop focused
    for ts, me in product([-0.10, -0.15, -0.20], [25, 30, 35]):
        params_list.append({
            'stop_loss': None,
            'take_profit': None,
            'score_exit_threshold': 15,
            'max_hold_days': None,
            'trailing_stop': ts,
            'pyramid': 'none',
            'max_positions': 15,
            'max_per_sector': 3,
            'min_entry_score': me,
            'cash_reserve_pct': 0.10,
            'strategy_type': 'trailing_stop'
        })
    
    # Strategy 4: Score-based exits
    for se, me in product([15, 20, 25], [30, 35, 40]):
        params_list.append({
            'stop_loss': -0.15,
            'take_profit': 1.00,
            'score_exit_threshold': se,
            'max_hold_days': 180,
            'trailing_stop': None,
            'pyramid': 'add_2.5k_at_15pct',
            'max_positions': 15,
            'max_per_sector': 5,
            'min_entry_score': me,
            'cash_reserve_pct': 0,
            'strategy_type': 'score_based'
        })
    
    # Strategy 5: Time-based with pyramiding
    for mh, pyr in product([60, 90, 180], ['add_2.5k_at_15pct', 'add_2.5k_at_15_and_30pct']):
        params_list.append({
            'stop_loss': -0.15,
            'take_profit': 1.00,
            'score_exit_threshold': None,
            'max_hold_days': mh,
            'trailing_stop': None,
            'pyramid': pyr,
            'max_positions': 15,
            'max_per_sector': 5,
            'min_entry_score': 30,
            'cash_reserve_pct': 0,
            'strategy_type': 'time_based'
        })
    
    print(f"Generated {len(params_list)} parameter combinations")
    return params_list


def main():
    """Main optimization runner"""
    
    print("="*80)
    print("ALPHA PICKER V3 - COMPREHENSIVE BACKTEST OPTIMIZATION")
    print("="*80)
    
    # Load exclusions
    print("\nLoading SA portfolio exclusions...")
    sa_exclusions = load_sa_exclusions()
    print(f"Loaded {len(sa_exclusions)} tickers to exclude")
    
    # Generate rebalance dates
    print("\nGenerating rebalance dates (1st and 15th of each month)...")
    rebalance_dates = generate_rebalance_dates('2023-05-01', '2026-02-27')
    print(f"Generated {len(rebalance_dates)} rebalance dates")
    print(f"Start: {rebalance_dates[0].strftime('%Y-%m-%d')}")
    print(f"End: {rebalance_dates[-1].strftime('%Y-%m-%d')}")
    
    # Generate parameter grid
    print("\nGenerating parameter grid...")
    param_grid = generate_parameter_grid()
    
    # Run optimization
    print(f"\nRunning {len(param_grid)} backtests...")
    print("This will take a while...\n")
    
    results = []
    
    for i, params in enumerate(tqdm(param_grid, desc="Backtests")):
        engine = BacktestEngine(
            starting_cash=120000,
            position_size=5000,
            rebalance_dates=rebalance_dates,
            sa_exclusions=sa_exclusions
        )
        
        result = engine.run_backtest(params, verbose=False)
        results.append(result)
        
        # Print progress every 10
        if (i + 1) % 10 == 0:
            best_so_far = max(results, key=lambda x: x['sharpe_ratio'])
            print(f"\nProgress: {i+1}/{len(param_grid)}")
            print(f"Best Sharpe so far: {best_so_far['sharpe_ratio']:.3f} (Return: {best_so_far['annualized_return']:.1%})")
    
    # Sort by Sharpe ratio (with return > 50% filter)
    qualified = [r for r in results if r['annualized_return'] > 0.50]
    qualified.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
    
    if not qualified:
        print("\nNo strategies met the 50% annualized return threshold!")
        print("Showing top performers by Sharpe regardless of return threshold:\n")
        qualified = sorted(results, key=lambda x: x['sharpe_ratio'], reverse=True)[:10]
    
    # Show top 10
    print("\n" + "="*80)
    print("TOP 10 PARAMETER COMBINATIONS (Ranked by Sharpe Ratio)")
    print("="*80)
    
    for i, r in enumerate(qualified[:10], 1):
        print(f"\n#{i}")
        print(f"  Strategy Type: {r['params'].get('strategy_type', 'unknown')}")
        print(f"  Sharpe Ratio: {r['sharpe_ratio']:.3f}")
        print(f"  Annualized Return: {r['annualized_return']:.1%}")
        print(f"  Total Return: {r['total_return']:.1%}")
        print(f"  Max Drawdown: {r['max_drawdown']:.1%}")
        print(f"  Win Rate: {r['win_rate']:.1%}")
        print(f"  Avg Win: {r['avg_win']:.1%} | Avg Loss: {r['avg_loss']:.1%}")
        print(f"  Num Trades: {r['num_trades']}")
        print(f"  Avg Hold: {r['avg_hold_days']:.1f} days")
        print(f"  Final Value: ${r['final_value']:,.2f}")
        print(f"  Parameters:")
        for k, v in r['params'].items():
            if k != 'strategy_type':
                print(f"    {k}: {v}")
    
    # Save results
    print("\n" + "="*80)
    print("Saving results...")
    
    best = qualified[0] if qualified else results[0]
    
    output = {
        'optimization_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'backtest_period': {
            'start': rebalance_dates[0].strftime('%Y-%m-%d'),
            'end': rebalance_dates[-1].strftime('%Y-%m-%d'),
            'num_rebalances': len(rebalance_dates)
        },
        'config': {
            'starting_cash': 120000,
            'position_size': 5000,
            'sa_exclusions_count': len(sa_exclusions)
        },
        'best_strategy': {
            'params': best['params'],
            'metrics': {
                'sharpe_ratio': best['sharpe_ratio'],
                'annualized_return': best['annualized_return'],
                'total_return': best['total_return'],
                'max_drawdown': best['max_drawdown'],
                'win_rate': best['win_rate'],
                'avg_win': best['avg_win'],
                'avg_loss': best['avg_loss'],
                'num_trades': best['num_trades'],
                'avg_hold_days': best['avg_hold_days'],
                'final_value': best['final_value']
            },
            'equity_curve': best['equity_curve'],
            'trades': best['trades']
        },
        'top_10_strategies': [
            {
                'rank': i + 1,
                'params': r['params'],
                'sharpe_ratio': r['sharpe_ratio'],
                'annualized_return': r['annualized_return'],
                'total_return': r['total_return'],
                'max_drawdown': r['max_drawdown'],
                'win_rate': r['win_rate'],
                'num_trades': r['num_trades']
            }
            for i, r in enumerate(qualified[:10])
        ]
    }
    
    # Save JSON
    output_file = '/home/quant/apps/quantclaw-data/data/optimized_backtest.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"✓ Saved detailed results to {output_file}")
    
    # Generate WhatsApp summary
    summary = f"""📈 ALPHA PICKER V3 - BACKTEST OPTIMIZATION COMPLETE

PERIOD: {rebalance_dates[0].strftime('%Y-%m-%d')} to {rebalance_dates[-1].strftime('%Y-%m-%d')}
REBALANCES: {len(rebalance_dates)} (1st & 15th of each month)
STRATEGIES TESTED: {len(param_grid)}

🏆 OPTIMAL STRATEGY:
Strategy Type: {best['params'].get('strategy_type', 'unknown').upper()}

📊 PERFORMANCE:
• Sharpe Ratio: {best['sharpe_ratio']:.3f}
• Annualized Return: {best['annualized_return']:.1%}
• Total Return: {best['total_return']:.1%}
• Max Drawdown: {best['max_drawdown']:.1%}
• Final Value: ${best['final_value']:,.0f} (from $120,000)

📈 TRADING STATS:
• Win Rate: {best['win_rate']:.1%}
• Avg Win: {best['avg_win']:.1%}
• Avg Loss: {best['avg_loss']:.1%}
• Total Trades: {best['num_trades']}
• Avg Hold: {best['avg_hold_days']:.0f} days

⚙️ PARAMETERS:
• Stop Loss: {best['params'].get('stop_loss', 'None')}
• Take Profit: {best['params'].get('take_profit', 'None')}
• Score Exit: {best['params'].get('score_exit_threshold', 'None')}
• Max Hold: {best['params'].get('max_hold_days', 'None')} days
• Trailing Stop: {best['params'].get('trailing_stop', 'None')}
• Pyramid: {best['params'].get('pyramid', 'none')}
• Max Positions: {best['params'].get('max_positions', 999)}
• Max Per Sector: {best['params'].get('max_per_sector', 999)}
• Min Entry Score: {best['params'].get('min_entry_score', 25)}
• Cash Reserve: {best['params'].get('cash_reserve_pct', 0):.0%}

🎯 TOP 5 PERFORMERS:
"""
    
    for i, r in enumerate(qualified[:5], 1):
        summary += f"{i}. {r['params'].get('strategy_type', 'unknown')} - Sharpe: {r['sharpe_ratio']:.3f}, Return: {r['annualized_return']:.1%}\n"
    
    summary += f"\n✅ Full results saved to:\n{output_file}"
    
    summary_file = '/home/quant/apps/quantclaw-data/data/optimized_backtest_summary.txt'
    with open(summary_file, 'w') as f:
        f.write(summary)
    print(f"✓ Saved WhatsApp summary to {summary_file}")
    
    print("\n" + "="*80)
    print("OPTIMIZATION COMPLETE!")
    print("="*80)
    print(summary)


if __name__ == '__main__':
    main()
