#!/usr/bin/env python3
"""
Kalman Filter Trends Module
Phase 35: Adaptive moving averages, regime change signals with state-space models

Uses:
- yfinance for price data
- numpy for Kalman filter implementation (state-space models)
- Real Kalman filter math: predict/update cycle with innovation variance

State-space model:
- State: [price, velocity]
- Observation: [price]
- Process noise: market uncertainty
- Measurement noise: bid-ask spread / observation error
"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
import sys


class KalmanFilter:
    """
    1D Kalman Filter for price trend extraction
    
    State-space model:
    x(t) = F * x(t-1) + w(t)    # State transition (process noise w ~ N(0, Q))
    z(t) = H * x(t) + v(t)      # Observation (measurement noise v ~ N(0, R))
    
    where:
    - x = [price, velocity]^T (2x1 state vector)
    - z = [observed_price] (1x1 observation)
    - F = state transition matrix (2x2)
    - H = observation matrix (1x2)
    - Q = process noise covariance (2x2)
    - R = measurement noise variance (scalar)
    """
    
    def __init__(self, process_noise: float = 1e-5, measurement_noise: float = 1e-3):
        """
        Initialize Kalman filter
        
        Args:
            process_noise: Process noise (Q) - how much we expect state to change
            measurement_noise: Measurement noise (R) - observation uncertainty
        """
        self.dt = 1.0  # Time step (1 day for daily data)
        
        # State transition matrix (constant velocity model)
        self.F = np.array([
            [1, self.dt],   # price(t) = price(t-1) + velocity * dt
            [0, 1]          # velocity(t) = velocity(t-1)
        ])
        
        # Observation matrix (we only observe price, not velocity)
        self.H = np.array([[1, 0]])
        
        # Process noise covariance
        self.Q = np.eye(2) * process_noise
        
        # Measurement noise covariance
        self.R = np.array([[measurement_noise]])
        
        # State estimate and covariance (initialized on first observation)
        self.x = None  # State [price, velocity]
        self.P = None  # Covariance matrix
        
        # Innovation tracking for regime detection
        self.innovations = []
        self.innovation_variance = []
    
    def predict(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prediction step: propagate state and covariance forward
        
        x̂(t|t-1) = F * x̂(t-1|t-1)
        P(t|t-1) = F * P(t-1|t-1) * F^T + Q
        
        Returns:
            x_pred: Predicted state
            P_pred: Predicted covariance
        """
        if self.x is None:
            raise ValueError("Filter not initialized. Call update() first.")
        
        x_pred = self.F @ self.x
        P_pred = self.F @ self.P @ self.F.T + self.Q
        
        return x_pred, P_pred
    
    def update(self, z: float, x_pred: Optional[np.ndarray] = None, 
               P_pred: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Update step: incorporate new observation
        
        Innovation: ỹ(t) = z(t) - H * x̂(t|t-1)
        Innovation covariance: S(t) = H * P(t|t-1) * H^T + R
        Kalman gain: K(t) = P(t|t-1) * H^T * S(t)^-1
        State update: x̂(t|t) = x̂(t|t-1) + K(t) * ỹ(t)
        Covariance update: P(t|t) = (I - K(t) * H) * P(t|t-1)
        
        Args:
            z: Observation (price)
            x_pred: Predicted state (if None, initialize)
            P_pred: Predicted covariance (if None, initialize)
        
        Returns:
            x: Updated state
            P: Updated covariance
        """
        z_obs = np.array([[z]])
        
        # Initialize on first observation
        if self.x is None:
            self.x = np.array([[z], [0]])  # Initial state: [price, 0 velocity]
            self.P = np.eye(2) * 1.0       # Initial covariance
            return self.x, self.P
        
        # Use predicted values or predict if not provided
        if x_pred is None or P_pred is None:
            x_pred, P_pred = self.predict()
        
        # Innovation (measurement residual)
        y = z_obs - self.H @ x_pred
        self.innovations.append(y[0, 0])
        
        # Innovation covariance
        S = self.H @ P_pred @ self.H.T + self.R
        self.innovation_variance.append(S[0, 0])
        
        # Kalman gain
        K = P_pred @ self.H.T @ np.linalg.inv(S)
        
        # State update
        self.x = x_pred + K @ y
        
        # Covariance update (Joseph form for numerical stability)
        I_KH = np.eye(2) - K @ self.H
        self.P = I_KH @ P_pred @ I_KH.T + K @ self.R @ K.T
        
        return self.x, self.P
    
    def filter_series(self, prices: pd.Series) -> Dict:
        """
        Apply Kalman filter to entire price series
        
        Returns:
            Dict with filtered prices, velocities, innovation stats
        """
        filtered_prices = []
        velocities = []
        uncertainties = []
        
        self.innovations = []
        self.innovation_variance = []
        
        for price in prices:
            x, P = self.update(price)
            filtered_prices.append(x[0, 0])
            velocities.append(x[1, 0])
            uncertainties.append(np.sqrt(P[0, 0]))
        
        return {
            'filtered_prices': np.array(filtered_prices),
            'velocities': np.array(velocities),
            'uncertainties': np.array(uncertainties),
            'innovations': np.array(self.innovations),
            'innovation_variance': np.array(self.innovation_variance)
        }


class AdaptiveMovingAverage:
    """
    Adaptive moving average using Kalman filter
    Automatically adjusts smoothing based on market conditions
    """
    
    def __init__(self, fast_noise: float = 1e-5, slow_noise: float = 1e-6):
        self.fast_filter = KalmanFilter(process_noise=fast_noise, measurement_noise=1e-3)
        self.slow_filter = KalmanFilter(process_noise=slow_noise, measurement_noise=1e-3)
    
    def compute(self, prices: pd.Series) -> Dict:
        """
        Compute fast and slow adaptive moving averages
        
        Returns:
            Dict with fast_ma, slow_ma, signal (1=buy, -1=sell, 0=hold)
        """
        fast_result = self.fast_filter.filter_series(prices)
        slow_result = self.slow_filter.filter_series(prices)
        
        fast_ma = fast_result['filtered_prices']
        slow_ma = slow_result['filtered_prices']
        
        # Generate trading signals (MA crossover)
        signal = np.zeros(len(fast_ma))
        signal[fast_ma > slow_ma] = 1   # Buy signal
        signal[fast_ma < slow_ma] = -1  # Sell signal
        
        return {
            'fast_ma': fast_ma,
            'slow_ma': slow_ma,
            'signal': signal,
            'fast_velocity': fast_result['velocities'],
            'slow_velocity': slow_result['velocities']
        }


class RegimeDetector:
    """
    Detect market regime changes using Kalman filter innovation variance
    
    High innovation variance = volatile regime (trending/uncertain)
    Low innovation variance = stable regime (mean-reverting/predictable)
    """
    
    def __init__(self, process_noise: float = 1e-5):
        self.kf = KalmanFilter(process_noise=process_noise, measurement_noise=1e-3)
    
    def detect_regimes(self, prices: pd.Series, window: int = 20) -> Dict:
        """
        Detect regime changes based on innovation variance
        
        Args:
            prices: Price series
            window: Rolling window for regime classification
        
        Returns:
            Dict with regime labels, innovation stats, change points
        """
        # Apply Kalman filter
        result = self.kf.filter_series(prices)
        
        innovations = result['innovations']
        innovation_var = result['innovation_variance']
        
        # Rolling innovation variance
        rolling_var = pd.Series(innovation_var).rolling(window=window, min_periods=1).mean()
        
        # Classify regimes based on variance percentiles
        var_25 = rolling_var.quantile(0.25)
        var_75 = rolling_var.quantile(0.75)
        
        regimes = np.zeros(len(rolling_var))
        regimes[rolling_var < var_25] = -1   # Low volatility (mean-reverting)
        regimes[rolling_var > var_75] = 1    # High volatility (trending)
        # Middle = 0 (neutral/transition)
        
        # Detect regime changes
        regime_changes = np.where(np.diff(regimes) != 0)[0]
        
        return {
            'regimes': regimes,
            'innovation_variance': innovation_var,
            'rolling_variance': rolling_var.values,
            'change_points': regime_changes,
            'filtered_prices': result['filtered_prices'],
            'regime_labels': {-1: 'Mean-Reverting', 0: 'Neutral', 1: 'Trending'}
        }


def fetch_price_data(symbol: str, period: str = "6mo") -> pd.Series:
    """Fetch historical price data"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        if hist.empty:
            raise ValueError(f"No data found for {symbol}")
        return hist['Close']
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_kalman(args):
    """
    Apply Kalman filter to extract smooth price trend
    
    Usage: python cli.py kalman SYMBOL [--period PERIOD]
    """
    if len(args) < 2:
        print("Usage: python cli.py kalman SYMBOL [--period PERIOD]", file=sys.stderr)
        sys.exit(1)
    
    symbol = args[1]
    period = "6mo"
    
    # Parse options
    for i, arg in enumerate(args[2:], start=2):
        if arg == "--period" and i+1 < len(args):
            period = args[i+1]
    
    # Fetch data
    prices = fetch_price_data(symbol, period)
    
    # Apply Kalman filter
    kf = KalmanFilter(process_noise=1e-5, measurement_noise=1e-3)
    result = kf.filter_series(prices)
    
    # Prepare output
    output = {
        'symbol': symbol,
        'period': period,
        'data_points': len(prices),
        'latest_price': float(prices.iloc[-1]),
        'filtered_price': float(result['filtered_prices'][-1]),
        'velocity': float(result['velocities'][-1]),
        'uncertainty': float(result['uncertainties'][-1]),
        'trend': 'Bullish' if result['velocities'][-1] > 0 else 'Bearish',
        'recent_data': [
            {
                'date': str(prices.index[i].date()),
                'raw_price': float(prices.iloc[i]),
                'filtered_price': float(result['filtered_prices'][i]),
                'velocity': float(result['velocities'][i])
            }
            for i in range(max(0, len(prices) - 10), len(prices))
        ]
    }
    
    print(json.dumps(output, indent=2))


def cmd_adaptive_ma(args):
    """
    Compute adaptive moving averages with trading signals
    
    Usage: python cli.py adaptive-ma SYMBOL [--period PERIOD]
    """
    if len(args) < 2:
        print("Usage: python cli.py adaptive-ma SYMBOL [--period PERIOD]", file=sys.stderr)
        sys.exit(1)
    
    symbol = args[1]
    period = "6mo"
    
    # Parse options
    for i, arg in enumerate(args[2:], start=2):
        if arg == "--period" and i+1 < len(args):
            period = args[i+1]
    
    # Fetch data
    prices = fetch_price_data(symbol, period)
    
    # Compute adaptive MAs
    ama = AdaptiveMovingAverage(fast_noise=1e-5, slow_noise=1e-6)
    result = ama.compute(prices)
    
    # Find last signal change
    signals = result['signal']
    current_signal = signals[-1]
    last_change_idx = len(signals) - 1
    for i in range(len(signals) - 2, -1, -1):
        if signals[i] != current_signal:
            last_change_idx = i + 1
            break
    
    signal_labels = {1: 'BUY', -1: 'SELL', 0: 'HOLD'}
    
    # Prepare output
    output = {
        'symbol': symbol,
        'period': period,
        'current_price': float(prices.iloc[-1]),
        'fast_ma': float(result['fast_ma'][-1]),
        'slow_ma': float(result['slow_ma'][-1]),
        'current_signal': signal_labels[int(current_signal)],
        'signal_since': str(prices.index[last_change_idx].date()),
        'days_in_signal': len(signals) - last_change_idx,
        'recent_data': [
            {
                'date': str(prices.index[i].date()),
                'price': float(prices.iloc[i]),
                'fast_ma': float(result['fast_ma'][i]),
                'slow_ma': float(result['slow_ma'][i]),
                'signal': signal_labels[int(result['signal'][i])]
            }
            for i in range(max(0, len(prices) - 10), len(prices))
        ]
    }
    
    print(json.dumps(output, indent=2))


def cmd_regime_detect(args):
    """
    Detect market regime changes using innovation variance
    
    Usage: python cli.py regime-detect SYMBOL [--period PERIOD] [--window WINDOW]
    """
    if len(args) < 2:
        print("Usage: python cli.py regime-detect SYMBOL [--period PERIOD] [--window WINDOW]", file=sys.stderr)
        sys.exit(1)
    
    symbol = args[1]
    period = "6mo"
    window = 20
    
    # Parse options
    for i, arg in enumerate(args[2:], start=2):
        if arg == "--period" and i+1 < len(args):
            period = args[i+1]
        elif arg == "--window" and i+1 < len(args):
            window = int(args[i+1])
    
    # Fetch data
    prices = fetch_price_data(symbol, period)
    
    # Detect regimes
    detector = RegimeDetector(process_noise=1e-5)
    result = detector.detect_regimes(prices, window=window)
    
    current_regime = int(result['regimes'][-1])
    regime_label = result['regime_labels'][current_regime]
    
    # Find regime changes in last 60 days
    recent_changes = [
        idx for idx in result['change_points']
        if idx >= len(prices) - 60
    ]
    
    # Prepare output
    output = {
        'symbol': symbol,
        'period': period,
        'current_regime': regime_label,
        'current_regime_code': current_regime,
        'total_regime_changes': len(result['change_points']),
        'recent_regime_changes': [
            {
                'date': str(prices.index[idx].date()),
                'from_regime': result['regime_labels'][int(result['regimes'][idx-1])],
                'to_regime': result['regime_labels'][int(result['regimes'][idx])],
                'price': float(prices.iloc[idx])
            }
            for idx in recent_changes
        ],
        'regime_distribution': {
            'mean_reverting_days': int(np.sum(result['regimes'] == -1)),
            'neutral_days': int(np.sum(result['regimes'] == 0)),
            'trending_days': int(np.sum(result['regimes'] == 1))
        },
        'recent_data': [
            {
                'date': str(prices.index[i].date()),
                'price': float(prices.iloc[i]),
                'filtered_price': float(result['filtered_prices'][i]),
                'regime': result['regime_labels'][int(result['regimes'][i])],
                'innovation_variance': float(result['innovation_variance'][i]) if i < len(result['innovation_variance']) else 0.0
            }
            for i in range(max(0, len(prices) - 10), min(len(prices), len(result['innovation_variance'])))
        ]
    }
    
    print(json.dumps(output, indent=2))


def main():
    """CLI dispatcher"""
    if len(sys.argv) < 2:
        print("Usage: python kalman_filter.py COMMAND [OPTIONS]", file=sys.stderr)
        print("\nCommands:", file=sys.stderr)
        print("  kalman SYMBOL [--period PERIOD]", file=sys.stderr)
        print("  adaptive-ma SYMBOL [--period PERIOD]", file=sys.stderr)
        print("  regime-detect SYMBOL [--period PERIOD] [--window WINDOW]", file=sys.stderr)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "kalman":
        cmd_kalman(sys.argv[1:])
    elif command == "adaptive-ma":
        cmd_adaptive_ma(sys.argv[1:])
    elif command == "regime-detect":
        cmd_regime_detect(sys.argv[1:])
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
