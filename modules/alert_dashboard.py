#!/usr/bin/env python3
"""
Alert Backtesting Dashboard
Visualize historical alert performance with profit factor and Sharpe ratio
"""

import sys
import argparse
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
from collections import defaultdict

class AlertBacktester:
    """Backtest alert strategies and calculate performance metrics"""
    
    def __init__(self, ticker: str, years: int = 3):
        self.ticker = ticker
        self.years = years
        self.df = self._fetch_data()
        
    def _fetch_data(self) -> pd.DataFrame:
        """Fetch historical price data from Yahoo Finance"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.years * 365)
        
        try:
            data = yf.download(self.ticker, start=start_date, end=end_date, progress=False)
            if data.empty:
                raise ValueError(f"No data found for {self.ticker}")
            
            # Flatten multi-index columns if present
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            
            return data
        except Exception as e:
            print(f"❌ Error fetching data for {self.ticker}: {e}", file=sys.stderr)
            sys.exit(1)
    
    def _calculate_rsi(self, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = self.df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _detect_volume_spike(self, threshold: float = 2.0) -> pd.Series:
        """Detect volume spikes (volume > threshold * avg volume)"""
        avg_volume = self.df['Volume'].rolling(window=20).mean()
        return self.df['Volume'] > (threshold * avg_volume)
    
    def _detect_price_breakout(self, window: int = 20) -> pd.Series:
        """Detect price breakouts above resistance"""
        rolling_high = self.df['High'].rolling(window=window).max()
        return self.df['Close'] > rolling_high.shift(1)
    
    def _simulate_trades(self, signals: pd.Series, hold_days: int = 5) -> List[Dict]:
        """Simulate trades based on signals"""
        trades = []
        in_position = False
        entry_price = 0
        entry_date = None
        entry_idx = 0
        
        # Convert signals to list for iteration
        dates = signals.index.tolist()
        signal_values = signals.values.tolist()
        
        for i, (date, signal) in enumerate(zip(dates, signal_values)):
            # Skip NaN values
            if pd.isna(signal):
                continue
                
            if signal and not in_position:
                # Enter position
                entry_price = float(self.df.loc[date, 'Close'])
                entry_date = date
                entry_idx = i
                in_position = True
                
            elif in_position:
                days_held = i - entry_idx
                
                # Exit after hold_days or at the end
                if days_held >= hold_days or i == len(dates) - 1:
                    exit_price = float(self.df.loc[date, 'Close'])
                    exit_date = date
                    
                    pnl = float(exit_price - entry_price)
                    pnl_pct = float((pnl / entry_price) * 100)
                    
                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': exit_date,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'hold_days': days_held
                    })
                    
                    in_position = False
        
        return trades
    
    def _calculate_metrics(self, trades: List[Dict]) -> Dict:
        """Calculate performance metrics from trades"""
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'total_pnl': 0,
                'total_pnl_pct': 0
            }
        
        pnls = [t['pnl'] for t in trades]
        pnl_pcts = [t['pnl_pct'] for t in trades]
        
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        
        win_rate = (len(wins) / len(trades)) * 100 if trades else 0
        
        total_wins = sum(wins) if wins else 0
        total_losses = abs(sum(losses)) if losses else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else (float('inf') if total_wins > 0 else 0)
        
        # Sharpe ratio (annualized)
        returns = np.array(pnl_pcts)
        sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252 / 5) if np.std(returns) > 0 else 0
        
        # Max drawdown
        cumulative = np.cumsum(pnls)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = running_max - cumulative
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
        
        return {
            'total_trades': len(trades),
            'win_rate': win_rate,
            'profit_factor': profit_factor if profit_factor != float('inf') else 999.99,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'avg_win': np.mean(wins) if wins else 0,
            'avg_loss': np.mean(losses) if losses else 0,
            'total_pnl': sum(pnls),
            'total_pnl_pct': sum(pnl_pcts)
        }
    
    def backtest_rsi(self, oversold: int = 30, overbought: int = 70, hold_days: int = 5) -> Dict:
        """Backtest RSI oversold/overbought alerts"""
        rsi = self._calculate_rsi()
        signals = rsi < oversold  # Buy when oversold
        
        trades = self._simulate_trades(signals, hold_days)
        metrics = self._calculate_metrics(trades)
        
        return {
            'strategy': 'RSI Oversold',
            'params': {'oversold': oversold, 'hold_days': hold_days},
            'trades': trades,
            'metrics': metrics
        }
    
    def backtest_volume_spike(self, threshold: float = 2.0, hold_days: int = 5) -> Dict:
        """Backtest volume spike alerts"""
        signals = self._detect_volume_spike(threshold)
        
        trades = self._simulate_trades(signals, hold_days)
        metrics = self._calculate_metrics(trades)
        
        return {
            'strategy': 'Volume Spike',
            'params': {'threshold': threshold, 'hold_days': hold_days},
            'trades': trades,
            'metrics': metrics
        }
    
    def backtest_price_breakout(self, window: int = 20, hold_days: int = 5) -> Dict:
        """Backtest price breakout alerts"""
        signals = self._detect_price_breakout(window)
        
        trades = self._simulate_trades(signals, hold_days)
        metrics = self._calculate_metrics(trades)
        
        return {
            'strategy': 'Price Breakout',
            'params': {'window': window, 'hold_days': hold_days},
            'trades': trades,
            'metrics': metrics
        }
    
    def backtest_earnings(self, hold_days: int = 5) -> Dict:
        """Backtest earnings-based alerts (simulated quarterly signals)"""
        # Simulate quarterly earnings (every ~63 trading days)
        signals = pd.Series(False, index=self.df.index)
        for i in range(0, len(self.df), 63):
            if i < len(signals):
                signals.iloc[i] = True
        
        trades = self._simulate_trades(signals, hold_days)
        metrics = self._calculate_metrics(trades)
        
        return {
            'strategy': 'Earnings Calendar',
            'params': {'hold_days': hold_days},
            'trades': trades,
            'metrics': metrics
        }

def backtest_alert(ticker: str, alert_type: str, years: int = 3, **kwargs):
    """Backtest a specific alert type"""
    backtester = AlertBacktester(ticker, years)
    
    alert_types = {
        'rsi': backtester.backtest_rsi,
        'volume': backtester.backtest_volume_spike,
        'breakout': backtester.backtest_price_breakout,
        'earnings': backtester.backtest_earnings
    }
    
    if alert_type not in alert_types:
        print(f"❌ Unknown alert type: {alert_type}", file=sys.stderr)
        print(f"Available types: {', '.join(alert_types.keys())}", file=sys.stderr)
        sys.exit(1)
    
    result = alert_types[alert_type](**kwargs)
    
    print(f"\n📊 {result['strategy']} Backtest: {ticker} ({years}Y)")
    print(f"Parameters: {result['params']}")
    print(f"\n📈 Performance Metrics:")
    metrics = result['metrics']
    print(f"  Total Trades:    {metrics['total_trades']}")
    print(f"  Win Rate:        {metrics['win_rate']:.2f}%")
    print(f"  Profit Factor:   {metrics['profit_factor']:.2f}")
    print(f"  Sharpe Ratio:    {metrics['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown:    ${metrics['max_drawdown']:.2f}")
    print(f"  Avg Win:         ${metrics['avg_win']:.2f}")
    print(f"  Avg Loss:        ${metrics['avg_loss']:.2f}")
    print(f"  Total P&L:       ${metrics['total_pnl']:.2f} ({metrics['total_pnl_pct']:.2f}%)")
    
    if result['trades']:
        print(f"\n📋 Recent Trades (last 5):")
        for trade in result['trades'][-5:]:
            entry = trade['entry_date'].strftime('%Y-%m-%d')
            exit = trade['exit_date'].strftime('%Y-%m-%d')
            pnl_sign = "✅" if trade['pnl'] > 0 else "❌"
            print(f"  {pnl_sign} {entry} → {exit}: ${trade['entry_price']:.2f} → ${trade['exit_price']:.2f} "
                  f"({trade['pnl_pct']:+.2f}%)")

def alert_performance(years: int = 3):
    """Compare performance of all alert types across multiple tickers"""
    tickers = ['AAPL', 'TSLA', 'SPY', 'NVDA']
    alert_types = ['rsi', 'volume', 'breakout', 'earnings']
    
    results = defaultdict(list)
    
    print(f"\n📊 Alert Performance Comparison ({years}Y Backtest)")
    print("=" * 80)
    
    for ticker in tickers:
        print(f"\n🔍 Analyzing {ticker}...")
        backtester = AlertBacktester(ticker, years)
        
        for alert_type in alert_types:
            try:
                if alert_type == 'rsi':
                    result = backtester.backtest_rsi()
                elif alert_type == 'volume':
                    result = backtester.backtest_volume_spike()
                elif alert_type == 'breakout':
                    result = backtester.backtest_price_breakout()
                elif alert_type == 'earnings':
                    result = backtester.backtest_earnings()
                
                results[alert_type].append({
                    'ticker': ticker,
                    'metrics': result['metrics']
                })
            except Exception as e:
                print(f"  ⚠️  {alert_type}: Error - {e}")
    
    # Print summary table
    print(f"\n📈 Performance Summary:")
    print(f"{'Strategy':<20} {'Avg Win Rate':<15} {'Avg Profit Factor':<20} {'Avg Sharpe':<15}")
    print("-" * 80)
    
    for alert_type, ticker_results in results.items():
        avg_win_rate = np.mean([r['metrics']['win_rate'] for r in ticker_results])
        avg_pf = np.mean([r['metrics']['profit_factor'] for r in ticker_results if r['metrics']['profit_factor'] < 999])
        avg_sharpe = np.mean([r['metrics']['sharpe_ratio'] for r in ticker_results])
        
        print(f"{alert_type.upper():<20} {avg_win_rate:>12.2f}%   {avg_pf:>16.2f}   {avg_sharpe:>12.2f}")

def optimize_alert(ticker: str, alert_type: str = 'rsi', years: int = 3):
    """Optimize alert parameters for best performance"""
    backtester = AlertBacktester(ticker, years)
    
    print(f"\n🔧 Optimizing {alert_type.upper()} alerts for {ticker} ({years}Y)")
    print("=" * 80)
    
    best_params = None
    best_sharpe = -float('inf')
    results = []
    
    if alert_type == 'rsi':
        for oversold in [20, 25, 30, 35, 40]:
            for hold_days in [3, 5, 7, 10]:
                result = backtester.backtest_rsi(oversold=oversold, hold_days=hold_days)
                metrics = result['metrics']
                sharpe = metrics['sharpe_ratio']
                
                results.append({
                    'oversold': oversold,
                    'hold_days': hold_days,
                    'sharpe': sharpe,
                    'profit_factor': metrics['profit_factor'],
                    'win_rate': metrics['win_rate']
                })
                
                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_params = {'oversold': oversold, 'hold_days': hold_days}
    
    elif alert_type == 'volume':
        for threshold in [1.5, 2.0, 2.5, 3.0]:
            for hold_days in [3, 5, 7, 10]:
                result = backtester.backtest_volume_spike(threshold=threshold, hold_days=hold_days)
                metrics = result['metrics']
                sharpe = metrics['sharpe_ratio']
                
                results.append({
                    'threshold': threshold,
                    'hold_days': hold_days,
                    'sharpe': sharpe,
                    'profit_factor': metrics['profit_factor'],
                    'win_rate': metrics['win_rate']
                })
                
                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_params = {'threshold': threshold, 'hold_days': hold_days}
    
    elif alert_type == 'breakout':
        for window in [10, 20, 30, 50]:
            for hold_days in [3, 5, 7, 10]:
                result = backtester.backtest_price_breakout(window=window, hold_days=hold_days)
                metrics = result['metrics']
                sharpe = metrics['sharpe_ratio']
                
                results.append({
                    'window': window,
                    'hold_days': hold_days,
                    'sharpe': sharpe,
                    'profit_factor': metrics['profit_factor'],
                    'win_rate': metrics['win_rate']
                })
                
                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_params = {'window': window, 'hold_days': hold_days}
    
    # Sort by Sharpe ratio
    results.sort(key=lambda x: x['sharpe'], reverse=True)
    
    print(f"\n🏆 Best Parameters (Sharpe: {best_sharpe:.2f}):")
    print(f"  {best_params}")
    
    print(f"\n📊 Top 5 Parameter Combinations:")
    for i, r in enumerate(results[:5], 1):
        params = {k: v for k, v in r.items() if k not in ['sharpe', 'profit_factor', 'win_rate']}
        print(f"  {i}. {params}")
        print(f"     Sharpe: {r['sharpe']:.2f} | PF: {r['profit_factor']:.2f} | WR: {r['win_rate']:.2f}%")

def generate_report(output_file: str = None):
    """Generate comprehensive alert performance report"""
    tickers = ['AAPL', 'TSLA', 'MSFT', 'NVDA', 'SPY']
    alert_types = ['rsi', 'volume', 'breakout', 'earnings']
    years = 3
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'period_years': years,
        'tickers': tickers,
        'results': {}
    }
    
    print(f"\n📄 Generating Alert Performance Report")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Period: {years} years")
    print("=" * 80)
    
    for ticker in tickers:
        print(f"\n🔍 Backtesting {ticker}...")
        backtester = AlertBacktester(ticker, years)
        report['results'][ticker] = {}
        
        for alert_type in alert_types:
            try:
                if alert_type == 'rsi':
                    result = backtester.backtest_rsi()
                elif alert_type == 'volume':
                    result = backtester.backtest_volume_spike()
                elif alert_type == 'breakout':
                    result = backtester.backtest_price_breakout()
                elif alert_type == 'earnings':
                    result = backtester.backtest_earnings()
                
                # Store metrics only (not full trade list)
                report['results'][ticker][alert_type] = {
                    'strategy': result['strategy'],
                    'params': result['params'],
                    'metrics': result['metrics']
                }
                
                print(f"  ✅ {alert_type.upper()}: Sharpe={result['metrics']['sharpe_ratio']:.2f}, "
                      f"WR={result['metrics']['win_rate']:.2f}%")
                
            except Exception as e:
                print(f"  ❌ {alert_type.upper()}: {e}")
                report['results'][ticker][alert_type] = {'error': str(e)}
    
    # Calculate aggregate statistics
    print(f"\n📊 Aggregate Statistics:")
    for alert_type in alert_types:
        all_sharpes = []
        all_win_rates = []
        all_profit_factors = []
        
        for ticker in tickers:
            if ticker in report['results'] and alert_type in report['results'][ticker]:
                metrics = report['results'][ticker][alert_type].get('metrics', {})
                if 'sharpe_ratio' in metrics:
                    all_sharpes.append(metrics['sharpe_ratio'])
                    all_win_rates.append(metrics['win_rate'])
                    if metrics['profit_factor'] < 999:
                        all_profit_factors.append(metrics['profit_factor'])
        
        if all_sharpes:
            print(f"\n  {alert_type.upper()}:")
            print(f"    Avg Sharpe:        {np.mean(all_sharpes):.2f}")
            print(f"    Avg Win Rate:      {np.mean(all_win_rates):.2f}%")
            print(f"    Avg Profit Factor: {np.mean(all_profit_factors):.2f}")
    
    # Save report if output file specified
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n💾 Report saved to: {output_file}")
    
    return report

def main():
    parser = argparse.ArgumentParser(description='Alert Backtesting Dashboard')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # dashboard-backtest
    backtest_parser = subparsers.add_parser('dashboard-backtest', help='Backtest specific alert type')
    backtest_parser.add_argument('alert_type', choices=['rsi', 'volume', 'breakout', 'earnings'],
                                  help='Alert type to backtest')
    backtest_parser.add_argument('--ticker', required=True, help='Stock ticker')
    backtest_parser.add_argument('--years', type=int, default=3, help='Years of historical data')
    backtest_parser.add_argument('--hold-days', type=int, default=5, help='Days to hold position')
    
    # dashboard-performance
    performance_parser = subparsers.add_parser('dashboard-performance', 
                                               help='Compare all alert types performance')
    performance_parser.add_argument('--years', type=int, default=3, help='Years of historical data')
    
    # dashboard-optimize
    optimize_parser = subparsers.add_parser('dashboard-optimize', help='Optimize alert parameters')
    optimize_parser.add_argument('ticker', help='Stock ticker')
    optimize_parser.add_argument('--alert-type', default='rsi', 
                                 choices=['rsi', 'volume', 'breakout'],
                                 help='Alert type to optimize')
    optimize_parser.add_argument('--years', type=int, default=3, help='Years of historical data')
    
    # dashboard-report
    report_parser = subparsers.add_parser('dashboard-report', help='Generate performance report')
    report_parser.add_argument('--output', help='Output JSON file path')
    
    args = parser.parse_args()
    
    if args.command == 'dashboard-backtest':
        kwargs = {}
        if args.hold_days:
            kwargs['hold_days'] = args.hold_days
        backtest_alert(args.ticker, args.alert_type, args.years, **kwargs)
    
    elif args.command == 'dashboard-performance':
        alert_performance(args.years)
    
    elif args.command == 'dashboard-optimize':
        optimize_alert(args.ticker, args.alert_type, args.years)
    
    elif args.command == 'dashboard-report':
        generate_report(args.output)
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
