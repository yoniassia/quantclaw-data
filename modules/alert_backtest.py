"""
Alert Backtesting Module
Test alert strategies historically, measure signal quality, false positive rates.
Phase 41: Infrastructure
"""

import yfinance as yf
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import sys
import warnings
warnings.filterwarnings('ignore')


@dataclass
class AlertSignal:
    """Single alert signal instance"""
    date: str
    price: float
    condition: str
    direction: str  # 'long' or 'short' expected move
    actual_move_1d: float  # 1-day forward return
    actual_move_5d: float  # 5-day forward return
    actual_move_20d: float  # 20-day forward return
    hit_1d: bool  # Did move in expected direction?
    hit_5d: bool
    hit_20d: bool


@dataclass
class BacktestResults:
    """Complete backtest results for an alert condition"""
    symbol: str
    condition: str
    total_signals: int
    hit_rate_1d: float
    hit_rate_5d: float
    hit_rate_20d: float
    false_positive_rate: float
    false_negative_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    signal_quality_score: float  # 0-100
    sharpe_ratio: float
    max_drawdown: float
    signals: List[AlertSignal]


def fetch_data_with_indicators(symbol: str, period: str = '1y') -> pd.DataFrame:
    """Fetch price data and calculate technical indicators"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        if df.empty:
            raise ValueError(f"No data found for {symbol}")
        
        # Calculate technical indicators
        df['returns'] = df['Close'].pct_change()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # Bollinger Bands
        df['sma_20'] = df['Close'].rolling(window=20).mean()
        df['bb_std'] = df['Close'].rolling(window=20).std()
        df['bb_upper'] = df['sma_20'] + (df['bb_std'] * 2)
        df['bb_lower'] = df['sma_20'] - (df['bb_std'] * 2)
        
        # Moving averages
        df['sma_50'] = df['Close'].rolling(window=50).mean()
        df['sma_200'] = df['Close'].rolling(window=200).mean()
        
        # Volume indicators
        df['volume_sma_20'] = df['Volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['Volume'] / df['volume_sma_20']
        
        # Forward returns for hit rate calculation
        df['fwd_return_1d'] = df['Close'].pct_change(1).shift(-1)
        df['fwd_return_5d'] = df['Close'].pct_change(5).shift(-5)
        df['fwd_return_20d'] = df['Close'].pct_change(20).shift(-20)
        
        return df
    except Exception as e:
        raise Exception(f"Error fetching data for {symbol}: {str(e)}")


def parse_condition(condition: str) -> Tuple[str, str, float]:
    """
    Parse alert condition string into components
    Examples: "rsi<30", "macd>0", "price>sma_50", "volume_ratio>2"
    Returns: (indicator, operator, threshold)
    """
    operators = ['>=', '<=', '>', '<', '==']
    
    for op in operators:
        if op in condition:
            parts = condition.split(op)
            if len(parts) == 2:
                indicator = parts[0].strip().lower()
                threshold_str = parts[1].strip()
                
                # Handle both numeric thresholds and column references
                try:
                    threshold = float(threshold_str)
                except ValueError:
                    threshold = threshold_str.lower()
                
                return indicator, op, threshold
    
    raise ValueError(f"Invalid condition format: {condition}")


def evaluate_condition(row: pd.Series, indicator: str, operator: str, threshold) -> bool:
    """Evaluate if condition is met for a given row"""
    if indicator not in row.index:
        return False
    
    value = row[indicator]
    
    # Handle NaN values
    if pd.isna(value):
        return False
    
    # If threshold is a column reference
    if isinstance(threshold, str) and threshold in row.index:
        threshold_value = row[threshold]
        if pd.isna(threshold_value):
            return False
    else:
        threshold_value = threshold
    
    # Evaluate condition
    if operator == '>':
        return value > threshold_value
    elif operator == '<':
        return value < threshold_value
    elif operator == '>=':
        return value >= threshold_value
    elif operator == '<=':
        return value <= threshold_value
    elif operator == '==':
        return abs(value - threshold_value) < 1e-6
    
    return False


def determine_direction(condition: str) -> str:
    """
    Determine expected price direction from condition
    - RSI < 30 → oversold → expect bounce (long)
    - RSI > 70 → overbought → expect pullback (short)
    - MACD > 0 → bullish → long
    - Price > SMA → uptrend → long
    """
    condition_lower = condition.lower()
    
    # Oversold conditions (bullish)
    if 'rsi<' in condition_lower or 'rsi <' in condition_lower:
        threshold = float(condition.split('<')[1].strip())
        if threshold <= 35:
            return 'long'
    
    # Overbought conditions (bearish)
    if 'rsi>' in condition_lower or 'rsi >' in condition_lower:
        threshold = float(condition.split('>')[1].strip())
        if threshold >= 65:
            return 'short'
    
    # MACD conditions
    if 'macd>' in condition_lower and ('0' in condition_lower or 'signal' in condition_lower):
        return 'long'
    if 'macd<' in condition_lower and ('0' in condition_lower or 'signal' in condition_lower):
        return 'short'
    
    # Price above moving average (bullish)
    if 'price>sma' in condition_lower or 'close>sma' in condition_lower:
        return 'long'
    if 'price<sma' in condition_lower or 'close<sma' in condition_lower:
        return 'short'
    
    # Bollinger bands
    if 'bb_lower' in condition_lower and '<' in condition:
        return 'long'
    if 'bb_upper' in condition_lower and '>' in condition:
        return 'short'
    
    # Volume spike (usually continuation)
    if 'volume_ratio>' in condition_lower:
        return 'long'  # Assume uptrend by default
    
    # Default to long bias
    return 'long'


def backtest_alert(symbol: str, condition: str, period: str = '1y') -> BacktestResults:
    """
    Backtest an alert condition on historical data
    """
    # Fetch data with indicators
    df = fetch_data_with_indicators(symbol, period)
    
    # Parse condition
    indicator, operator, threshold = parse_condition(condition)
    
    # Determine expected direction
    direction = determine_direction(condition)
    
    # Find all dates where condition triggered
    signals = []
    
    for idx, row in df.iterrows():
        if evaluate_condition(row, indicator, operator, threshold):
            # Check if we have forward return data
            if pd.notna(row['fwd_return_1d']):
                # Determine if signal was successful
                expected_positive = (direction == 'long')
                
                hit_1d = (row['fwd_return_1d'] > 0) == expected_positive
                hit_5d = (row['fwd_return_5d'] > 0) == expected_positive if pd.notna(row['fwd_return_5d']) else None
                hit_20d = (row['fwd_return_20d'] > 0) == expected_positive if pd.notna(row['fwd_return_20d']) else None
                
                signal = AlertSignal(
                    date=idx.strftime('%Y-%m-%d'),
                    price=float(row['Close']),
                    condition=condition,
                    direction=direction,
                    actual_move_1d=float(row['fwd_return_1d']) * 100,
                    actual_move_5d=float(row['fwd_return_5d']) * 100 if pd.notna(row['fwd_return_5d']) else 0,
                    actual_move_20d=float(row['fwd_return_20d']) * 100 if pd.notna(row['fwd_return_20d']) else 0,
                    hit_1d=hit_1d,
                    hit_5d=hit_5d if hit_5d is not None else False,
                    hit_20d=hit_20d if hit_20d is not None else False
                )
                signals.append(signal)
    
    if len(signals) == 0:
        return BacktestResults(
            symbol=symbol,
            condition=condition,
            total_signals=0,
            hit_rate_1d=0.0,
            hit_rate_5d=0.0,
            hit_rate_20d=0.0,
            false_positive_rate=0.0,
            false_negative_rate=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            profit_factor=0.0,
            signal_quality_score=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            signals=[]
        )
    
    # Calculate metrics
    total_signals = len(signals)
    hit_rate_1d = sum(s.hit_1d for s in signals) / total_signals
    hit_rate_5d = sum(s.hit_5d for s in signals) / total_signals
    hit_rate_20d = sum(s.hit_20d for s in signals) / total_signals
    
    # False positive: signal fired but wrong direction
    # False negative: should have fired but didn't (harder to measure)
    false_positive_rate = 1 - hit_rate_1d
    false_negative_rate = 0.0  # Would need different analysis
    
    # Win/loss analysis
    wins = [s.actual_move_1d for s in signals if s.hit_1d]
    losses = [s.actual_move_1d for s in signals if not s.hit_1d]
    
    avg_win = np.mean(wins) if wins else 0.0
    avg_loss = np.mean(losses) if losses else 0.0
    
    # Profit factor: (sum of wins) / (abs(sum of losses))
    total_win = sum(wins) if wins else 0.0
    total_loss = abs(sum(losses)) if losses else 0.0
    profit_factor = total_win / total_loss if total_loss > 0 else 0.0
    
    # Signal quality score (0-100)
    # Weighted: 40% hit rate, 30% profit factor, 30% consistency
    hit_rate_score = hit_rate_1d * 40
    pf_score = min(profit_factor / 3.0, 1.0) * 30  # Cap at 3.0 for scoring
    consistency_score = (1 - abs(hit_rate_5d - hit_rate_1d)) * 30
    signal_quality_score = hit_rate_score + pf_score + consistency_score
    
    # Portfolio metrics
    returns = [s.actual_move_1d / 100 for s in signals]
    sharpe_ratio = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if len(returns) > 1 and np.std(returns) > 0 else 0.0
    
    # Max drawdown
    cumulative = np.cumsum(returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = cumulative - running_max
    max_drawdown = abs(np.min(drawdown)) if len(drawdown) > 0 else 0.0
    
    return BacktestResults(
        symbol=symbol,
        condition=condition,
        total_signals=total_signals,
        hit_rate_1d=hit_rate_1d,
        hit_rate_5d=hit_rate_5d,
        hit_rate_20d=hit_rate_20d,
        false_positive_rate=false_positive_rate,
        false_negative_rate=false_negative_rate,
        avg_win=avg_win,
        avg_loss=avg_loss,
        profit_factor=profit_factor,
        signal_quality_score=signal_quality_score,
        sharpe_ratio=sharpe_ratio,
        max_drawdown=max_drawdown,
        signals=signals
    )


def signal_quality_analysis(symbol: str, period: str = '1y') -> Dict:
    """
    Test multiple common alert conditions and rank by quality
    """
    common_conditions = [
        "rsi<30",
        "rsi>70",
        "rsi<25",
        "rsi>75",
        "macd>macd_signal",
        "macd<macd_signal",
        "close<bb_lower",
        "close>bb_upper",
        "volume_ratio>2",
        "volume_ratio>3",
    ]
    
    results = []
    
    for condition in common_conditions:
        try:
            backtest = backtest_alert(symbol, condition, period)
            if backtest.total_signals > 0:
                results.append({
                    'condition': condition,
                    'signals': backtest.total_signals,
                    'hit_rate_1d': backtest.hit_rate_1d,
                    'profit_factor': backtest.profit_factor,
                    'quality_score': backtest.signal_quality_score,
                    'sharpe': backtest.sharpe_ratio
                })
        except Exception as e:
            continue
    
    # Sort by quality score
    results.sort(key=lambda x: x['quality_score'], reverse=True)
    
    return {
        'symbol': symbol,
        'period': period,
        'conditions_tested': len(common_conditions),
        'conditions_with_signals': len(results),
        'top_conditions': results
    }


def alert_stats_summary(symbol: str, period: str = '1y') -> Dict:
    """
    Summary statistics for alert potential on a symbol
    """
    df = fetch_data_with_indicators(symbol, period)
    
    # Calculate how often each condition triggers
    stats = {
        'symbol': symbol,
        'period': period,
        'trading_days': len(df),
        'conditions': {
            'rsi_oversold_30': int((df['rsi'] < 30).sum()),
            'rsi_overbought_70': int((df['rsi'] > 70).sum()),
            'rsi_oversold_25': int((df['rsi'] < 25).sum()),
            'rsi_overbought_75': int((df['rsi'] > 75).sum()),
            'macd_bullish_cross': int((df['macd'] > df['macd_signal']).sum()),
            'macd_bearish_cross': int((df['macd'] < df['macd_signal']).sum()),
            'below_bb_lower': int((df['Close'] < df['bb_lower']).sum()),
            'above_bb_upper': int((df['Close'] > df['bb_upper']).sum()),
            'volume_spike_2x': int((df['volume_ratio'] > 2).sum()),
            'volume_spike_3x': int((df['volume_ratio'] > 3).sum()),
        },
        'volatility': {
            'daily_returns_std': float(df['returns'].std() * 100),
            'annualized_vol': float(df['returns'].std() * np.sqrt(252) * 100),
            'avg_daily_range': float(((df['High'] - df['Low']) / df['Close']).mean() * 100)
        }
    }
    
    return stats


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python cli.py alert-backtest SYMBOL --condition 'CONDITION' [--period PERIOD]")
        print("  python cli.py signal-quality SYMBOL [--period PERIOD]")
        print("  python cli.py alert-potential SYMBOL [--period PERIOD]")
        print()
        print("Examples:")
        print("  python cli.py alert-backtest AAPL --condition 'rsi<30' --period 1y")
        print("  python cli.py signal-quality TSLA --period 2y")
        print("  python cli.py alert-potential NVDA")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == 'alert-backtest':
            if len(sys.argv) < 3:
                print("Error: SYMBOL required")
                sys.exit(1)
            
            symbol = sys.argv[2].upper()
            
            # Parse args
            condition = None
            period = '1y'
            
            i = 3
            while i < len(sys.argv):
                if sys.argv[i] == '--condition' and i + 1 < len(sys.argv):
                    condition = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == '--period' and i + 1 < len(sys.argv):
                    period = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1
            
            if not condition:
                print("Error: --condition required")
                sys.exit(1)
            
            results = backtest_alert(symbol, condition, period)
            
            # Print summary
            print(f"\n🎯 Alert Backtest: {symbol} - {condition}")
            print(f"Period: {period}")
            print(f"\n📊 Results:")
            print(f"  Total Signals: {results.total_signals}")
            print(f"  Hit Rate (1d): {results.hit_rate_1d:.2%}")
            print(f"  Hit Rate (5d): {results.hit_rate_5d:.2%}")
            print(f"  Hit Rate (20d): {results.hit_rate_20d:.2%}")
            print(f"  False Positive Rate: {results.false_positive_rate:.2%}")
            print(f"  Avg Win: {results.avg_win:.2f}%")
            print(f"  Avg Loss: {results.avg_loss:.2f}%")
            print(f"  Profit Factor: {results.profit_factor:.2f}")
            print(f"  Signal Quality Score: {results.signal_quality_score:.1f}/100")
            print(f"  Sharpe Ratio: {results.sharpe_ratio:.2f}")
            print(f"  Max Drawdown: {results.max_drawdown:.2%}")
            
            # Print recent signals
            if results.signals:
                print(f"\n📅 Recent Signals (last 5):")
                for signal in results.signals[-5:]:
                    status = "✅" if signal.hit_1d else "❌"
                    print(f"  {status} {signal.date}: ${signal.price:.2f} → {signal.actual_move_1d:+.2f}% (1d)")
            
            # JSON output - convert to dict and ensure all values are JSON-serializable
            result_dict = asdict(results)
            # Convert all booleans explicitly to ensure JSON compatibility
            for signal in result_dict.get('signals', []):
                signal['hit_1d'] = bool(signal['hit_1d'])
                signal['hit_5d'] = bool(signal['hit_5d'])
                signal['hit_20d'] = bool(signal['hit_20d'])
            
            print("\n" + json.dumps(result_dict, indent=2, default=str))
        
        elif command == 'signal-quality':
            if len(sys.argv) < 3:
                print("Error: SYMBOL required")
                sys.exit(1)
            
            symbol = sys.argv[2].upper()
            period = sys.argv[4] if len(sys.argv) > 4 and sys.argv[3] == '--period' else '1y'
            
            results = signal_quality_analysis(symbol, period)
            
            print(f"\n🔍 Signal Quality Analysis: {symbol}")
            print(f"Period: {period}")
            print(f"Conditions tested: {results['conditions_tested']}")
            print(f"Conditions with signals: {results['conditions_with_signals']}")
            print(f"\n🏆 Top Alert Conditions:")
            
            for i, cond in enumerate(results['top_conditions'][:10], 1):
                print(f"\n{i}. {cond['condition']}")
                print(f"   Quality Score: {cond['quality_score']:.1f}/100")
                print(f"   Hit Rate: {cond['hit_rate_1d']:.2%}")
                print(f"   Profit Factor: {cond['profit_factor']:.2f}")
                print(f"   Signals: {cond['signals']}")
                print(f"   Sharpe: {cond['sharpe']:.2f}")
            
            print("\n" + json.dumps(results, indent=2))
        
        elif command == 'alert-potential':
            if len(sys.argv) < 3:
                print("Error: SYMBOL required")
                sys.exit(1)
            
            symbol = sys.argv[2].upper()
            period = sys.argv[4] if len(sys.argv) > 4 and sys.argv[3] == '--period' else '1y'
            
            stats = alert_stats_summary(symbol, period)
            
            print(f"\n📈 Alert Potential: {symbol}")
            print(f"Period: {period} ({stats['trading_days']} trading days)")
            print(f"\n🚨 Alert Trigger Frequency:")
            
            for condition, count in stats['conditions'].items():
                pct = (count / stats['trading_days']) * 100
                print(f"  {condition:.<30} {count:>4} ({pct:>5.1f}%)")
            
            print(f"\n📊 Volatility Metrics:")
            vol = stats['volatility']
            print(f"  Daily Returns Std: {vol['daily_returns_std']:.2f}%")
            print(f"  Annualized Vol: {vol['annualized_vol']:.2f}%")
            print(f"  Avg Daily Range: {vol['avg_daily_range']:.2f}%")
            
            print("\n" + json.dumps(stats, indent=2))
        
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
