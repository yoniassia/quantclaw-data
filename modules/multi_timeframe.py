#!/usr/bin/env python3
"""
Multi-Timeframe Analysis Module
Phase 38: Combine signals from daily/weekly/monthly charts for confirmation

Uses:
- yfinance for price data across multiple timeframes
- numpy/pandas for calculations
- RSI, MACD, SMA indicators across daily, weekly, monthly timeframes
- Signal confluence scoring (agreement across timeframes)
- Trend alignment detection (all timeframes agree on direction)
"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
import sys


class TechnicalIndicators:
    """Calculate technical indicators for multi-timeframe analysis"""
    
    @staticmethod
    def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI)
        
        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        MACD Line = EMA(fast) - EMA(slow)
        Signal Line = EMA(MACD, signal)
        Histogram = MACD - Signal
        """
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def sma(prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def ema(prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return prices.ewm(span=period, adjust=False).mean()


class TimeframeAnalyzer:
    """Analyze a single timeframe with multiple indicators"""
    
    def __init__(self, prices: pd.Series, timeframe: str):
        self.prices = prices
        self.timeframe = timeframe
        self.indicators = TechnicalIndicators()
    
    def analyze(self) -> Dict:
        """Run full technical analysis on this timeframe"""
        # Calculate indicators
        rsi = self.indicators.rsi(self.prices)
        macd_data = self.indicators.macd(self.prices)
        sma_20 = self.indicators.sma(self.prices, 20)
        sma_50 = self.indicators.sma(self.prices, 50)
        sma_200 = self.indicators.sma(self.prices, 200) if len(self.prices) >= 200 else None
        
        # Get current values
        current_price = float(self.prices.iloc[-1])
        current_rsi = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
        current_macd = float(macd_data['macd'].iloc[-1]) if not pd.isna(macd_data['macd'].iloc[-1]) else None
        current_signal = float(macd_data['signal'].iloc[-1]) if not pd.isna(macd_data['signal'].iloc[-1]) else None
        current_histogram = float(macd_data['histogram'].iloc[-1]) if not pd.isna(macd_data['histogram'].iloc[-1]) else None
        current_sma20 = float(sma_20.iloc[-1]) if not pd.isna(sma_20.iloc[-1]) else None
        current_sma50 = float(sma_50.iloc[-1]) if not pd.isna(sma_50.iloc[-1]) else None
        current_sma200 = float(sma_200.iloc[-1]) if sma_200 is not None and not pd.isna(sma_200.iloc[-1]) else None
        
        # Generate signals
        signals = self._generate_signals(
            current_price, current_rsi, current_macd, current_signal,
            current_sma20, current_sma50, current_sma200
        )
        
        return {
            'timeframe': self.timeframe,
            'price': current_price,
            'rsi': current_rsi,
            'rsi_signal': signals['rsi'],
            'macd': {
                'macd': current_macd,
                'signal': current_signal,
                'histogram': current_histogram,
                'signal_type': signals['macd']
            },
            'sma': {
                'sma_20': current_sma20,
                'sma_50': current_sma50,
                'sma_200': current_sma200,
                'signal_type': signals['sma']
            },
            'overall_signal': signals['overall'],
            'signal_strength': signals['strength']
        }
    
    def _generate_signals(self, price: float, rsi: Optional[float], 
                          macd: Optional[float], signal: Optional[float],
                          sma20: Optional[float], sma50: Optional[float],
                          sma200: Optional[float]) -> Dict:
        """Generate trading signals from indicators"""
        signals = []
        
        # RSI signal
        rsi_signal = 'neutral'
        if rsi is not None:
            if rsi < 30:
                rsi_signal = 'oversold'
                signals.append(1)  # Bullish
            elif rsi > 70:
                rsi_signal = 'overbought'
                signals.append(-1)  # Bearish
            else:
                rsi_signal = 'neutral'
                signals.append(0)
        
        # MACD signal
        macd_signal = 'neutral'
        if macd is not None and signal is not None:
            if macd > signal:
                macd_signal = 'bullish'
                signals.append(1)
            elif macd < signal:
                macd_signal = 'bearish'
                signals.append(-1)
            else:
                macd_signal = 'neutral'
                signals.append(0)
        
        # SMA trend signal
        sma_signal = 'neutral'
        if sma20 is not None and sma50 is not None:
            # Golden cross / Death cross
            if price > sma20 > sma50:
                sma_signal = 'strong_uptrend'
                signals.append(2)  # Strong bullish
            elif price < sma20 < sma50:
                sma_signal = 'strong_downtrend'
                signals.append(-2)  # Strong bearish
            elif price > sma20:
                sma_signal = 'uptrend'
                signals.append(1)
            elif price < sma20:
                sma_signal = 'downtrend'
                signals.append(-1)
            else:
                signals.append(0)
            
            # Add SMA200 if available
            if sma200 is not None:
                if price > sma200:
                    signals.append(1)
                elif price < sma200:
                    signals.append(-1)
        
        # Overall signal
        if not signals:
            overall = 'neutral'
            strength = 0.0
        else:
            avg_signal = np.mean(signals)
            strength = abs(avg_signal)
            
            if avg_signal > 0.5:
                overall = 'bullish'
            elif avg_signal < -0.5:
                overall = 'bearish'
            else:
                overall = 'neutral'
        
        return {
            'rsi': rsi_signal,
            'macd': macd_signal,
            'sma': sma_signal,
            'overall': overall,
            'strength': strength
        }


class MultiTimeframeAnalysis:
    """Combine signals from daily, weekly, and monthly timeframes"""
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.timeframes = {}
    
    def fetch_data(self) -> None:
        """Fetch price data for all timeframes"""
        try:
            ticker = yf.Ticker(self.symbol)
            
            # Daily data (2 years for enough weekly/monthly samples)
            daily = ticker.history(period="2y", interval="1d")
            if daily.empty:
                raise ValueError(f"No data found for {self.symbol}")
            
            # Weekly data (resample from daily)
            weekly = daily['Close'].resample('W-FRI').last()
            
            # Monthly data (resample from daily)
            monthly = daily['Close'].resample('ME').last()
            
            self.timeframes = {
                'daily': daily['Close'],
                'weekly': weekly,
                'monthly': monthly
            }
            
        except Exception as e:
            print(f"Error fetching data for {self.symbol}: {e}", file=sys.stderr)
            sys.exit(1)
    
    def analyze_all_timeframes(self) -> Dict:
        """Analyze all timeframes and return results"""
        if not self.timeframes:
            self.fetch_data()
        
        results = {}
        
        for tf_name, prices in self.timeframes.items():
            analyzer = TimeframeAnalyzer(prices, tf_name)
            results[tf_name] = analyzer.analyze()
        
        return results
    
    def signal_confluence(self) -> Dict:
        """
        Calculate signal confluence across timeframes
        
        Returns:
            Dict with confluence score, agreement level, recommended action
        """
        analyses = self.analyze_all_timeframes()
        
        # Extract overall signals
        signals = {
            'daily': analyses['daily']['overall_signal'],
            'weekly': analyses['weekly']['overall_signal'],
            'monthly': analyses['monthly']['overall_signal']
        }
        
        strengths = {
            'daily': analyses['daily']['signal_strength'],
            'weekly': analyses['weekly']['signal_strength'],
            'monthly': analyses['monthly']['signal_strength']
        }
        
        # Calculate confluence
        bullish_count = sum(1 for s in signals.values() if s == 'bullish')
        bearish_count = sum(1 for s in signals.values() if s == 'bearish')
        neutral_count = sum(1 for s in signals.values() if s == 'neutral')
        
        # Confluence score (-1 to 1)
        signal_values = {
            'bullish': 1,
            'neutral': 0,
            'bearish': -1
        }
        
        confluence_score = np.mean([signal_values[s] for s in signals.values()])
        avg_strength = np.mean(list(strengths.values()))
        
        # Determine agreement level
        if bullish_count == 3:
            agreement = 'strong_agreement'
            recommendation = 'STRONG BUY'
        elif bearish_count == 3:
            agreement = 'strong_agreement'
            recommendation = 'STRONG SELL'
        elif bullish_count == 2:
            agreement = 'moderate_agreement'
            recommendation = 'BUY'
        elif bearish_count == 2:
            agreement = 'moderate_agreement'
            recommendation = 'SELL'
        else:
            agreement = 'no_agreement'
            recommendation = 'HOLD'
        
        return {
            'symbol': self.symbol,
            'confluence_score': float(confluence_score),
            'agreement_level': agreement,
            'recommendation': recommendation,
            'signal_strength': float(avg_strength),
            'timeframe_signals': signals,
            'timeframe_strengths': {k: float(v) for k, v in strengths.items()},
            'bullish_timeframes': bullish_count,
            'bearish_timeframes': bearish_count,
            'neutral_timeframes': neutral_count,
            'detailed_analysis': analyses
        }
    
    def trend_alignment(self) -> Dict:
        """
        Check if all timeframes are aligned in the same trend direction
        
        Returns:
            Dict with alignment status, trend direction, strength
        """
        analyses = self.analyze_all_timeframes()
        
        # Extract SMA signals for trend
        trends = {}
        for tf_name, analysis in analyses.items():
            sma_signal = analysis['sma']['signal_type']
            
            if 'uptrend' in sma_signal:
                trends[tf_name] = 'bullish'
            elif 'downtrend' in sma_signal:
                trends[tf_name] = 'bearish'
            else:
                trends[tf_name] = 'neutral'
        
        # Check alignment
        trend_values = list(trends.values())
        bullish_trends = trend_values.count('bullish')
        bearish_trends = trend_values.count('bearish')
        
        if bullish_trends == 3:
            alignment = 'fully_aligned'
            trend_direction = 'bullish'
            confidence = 'high'
        elif bearish_trends == 3:
            alignment = 'fully_aligned'
            trend_direction = 'bearish'
            confidence = 'high'
        elif bullish_trends >= 2:
            alignment = 'partially_aligned'
            trend_direction = 'bullish'
            confidence = 'medium'
        elif bearish_trends >= 2:
            alignment = 'partially_aligned'
            trend_direction = 'bearish'
            confidence = 'medium'
        else:
            alignment = 'misaligned'
            trend_direction = 'neutral'
            confidence = 'low'
        
        # Get price data for context
        current_price = float(self.timeframes['daily'].iloc[-1])
        
        return {
            'symbol': self.symbol,
            'current_price': current_price,
            'alignment_status': alignment,
            'trend_direction': trend_direction,
            'confidence': confidence,
            'timeframe_trends': trends,
            'bullish_timeframes': bullish_trends,
            'bearish_timeframes': bearish_trends,
            'detailed_analysis': analyses
        }


def cmd_mtf(args):
    """
    Multi-timeframe analysis with all indicators
    
    Usage: python cli.py mtf SYMBOL
    """
    if len(args) < 2:
        print("Usage: python cli.py mtf SYMBOL", file=sys.stderr)
        sys.exit(1)
    
    symbol = args[1]
    
    mtf = MultiTimeframeAnalysis(symbol)
    mtf.fetch_data()
    
    results = mtf.analyze_all_timeframes()
    
    output = {
        'symbol': symbol,
        'timestamp': datetime.now().isoformat(),
        'timeframes': results
    }
    
    print(json.dumps(output, indent=2))


def cmd_trend_alignment(args):
    """
    Check trend alignment across timeframes
    
    Usage: python cli.py trend-alignment SYMBOL
    """
    if len(args) < 2:
        print("Usage: python cli.py trend-alignment SYMBOL", file=sys.stderr)
        sys.exit(1)
    
    symbol = args[1]
    
    mtf = MultiTimeframeAnalysis(symbol)
    result = mtf.trend_alignment()
    
    print(json.dumps(result, indent=2))


def cmd_signal_confluence(args):
    """
    Calculate signal confluence across timeframes
    
    Usage: python cli.py signal-confluence SYMBOL
    """
    if len(args) < 2:
        print("Usage: python cli.py signal-confluence SYMBOL", file=sys.stderr)
        sys.exit(1)
    
    symbol = args[1]
    
    mtf = MultiTimeframeAnalysis(symbol)
    result = mtf.signal_confluence()
    
    print(json.dumps(result, indent=2))


def main():
    """CLI dispatcher"""
    if len(sys.argv) < 2:
        print("Usage: python multi_timeframe.py COMMAND [OPTIONS]", file=sys.stderr)
        print("\nCommands:", file=sys.stderr)
        print("  mtf SYMBOL                    - Full multi-timeframe analysis", file=sys.stderr)
        print("  trend-alignment SYMBOL        - Check trend alignment", file=sys.stderr)
        print("  signal-confluence SYMBOL      - Calculate signal confluence", file=sys.stderr)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "mtf":
        cmd_mtf(sys.argv[1:])
    elif command == "trend-alignment":
        cmd_trend_alignment(sys.argv[1:])
    elif command == "signal-confluence":
        cmd_signal_confluence(sys.argv[1:])
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
