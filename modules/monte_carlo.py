#!/usr/bin/env python3
"""
Monte Carlo Simulation Module
Phase 34: Scenario analysis, probabilistic forecasting, tail risk modeling

Uses:
- yfinance for historical returns
- numpy for GBM simulation
- scipy for distribution fitting
- VaR/CVaR calculations from simulations
"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
from scipy import stats
import sys
import argparse


class MonteCarloSimulator:
    """Monte Carlo simulation for stocks with GBM and bootstrap methods"""
    
    def __init__(self, ticker: str, lookback_days: int = 252):
        self.ticker = ticker
        self.lookback_days = lookback_days
        self.historical_data = None
        self.returns = None
        self.current_price = None
        
    def fetch_data(self) -> bool:
        """Fetch historical price data"""
        try:
            stock = yf.Ticker(self.ticker)
            hist = stock.history(period=f"{self.lookback_days}d")
            
            if hist.empty:
                print(f"Error: No data found for {self.ticker}", file=sys.stderr)
                return False
            
            self.historical_data = hist
            self.current_price = float(hist['Close'].iloc[-1])
            
            # Calculate log returns
            self.returns = np.log(hist['Close'] / hist['Close'].shift(1)).dropna()
            
            return True
        except Exception as e:
            print(f"Error fetching data: {e}", file=sys.stderr)
            return False
    
    def geometric_brownian_motion(
        self, 
        days: int = 252, 
        simulations: int = 10000,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Geometric Brownian Motion simulation
        S(t) = S(0) * exp((μ - σ²/2)t + σW(t))
        
        Returns: simulated paths, statistics, percentiles
        """
        if self.returns is None:
            if not self.fetch_data():
                return {'error': 'Failed to fetch data'}
        
        # Calculate drift (μ) and volatility (σ)
        mu = float(self.returns.mean())  # Daily drift
        sigma = float(self.returns.std())  # Daily volatility
        
        # Annualized metrics
        mu_annual = mu * 252
        sigma_annual = sigma * np.sqrt(252)
        
        # Set random seed for reproducibility
        if seed is not None:
            np.random.seed(seed)
        
        # Time steps
        dt = 1.0  # Daily steps
        
        # Generate random walks
        # Shape: (simulations, days)
        random_walks = np.random.standard_normal((simulations, days))
        
        # Calculate cumulative returns using GBM formula
        # Each step: exp((μ - σ²/2)dt + σ√dt * Z)
        drift = (mu - 0.5 * sigma**2) * dt
        shock = sigma * np.sqrt(dt) * random_walks
        
        # Cumulative product of returns
        price_paths = self.current_price * np.exp(np.cumsum(drift + shock, axis=1))
        
        # Add initial price column
        price_paths = np.column_stack([
            np.full(simulations, self.current_price),
            price_paths
        ])
        
        # Final prices (end of simulation period)
        final_prices = price_paths[:, -1]
        
        # Calculate statistics
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        percentile_values = np.percentile(final_prices, percentiles)
        
        # Calculate expected return and probability distributions
        expected_final = float(np.mean(final_prices))
        median_final = float(np.median(final_prices))
        std_final = float(np.std(final_prices))
        
        # Probability of profit/loss
        prob_profit = float(np.sum(final_prices > self.current_price) / simulations)
        prob_loss = 1.0 - prob_profit
        
        # Expected returns
        expected_return = ((expected_final / self.current_price) - 1) * 100
        median_return = ((median_final / self.current_price) - 1) * 100
        
        return {
            'ticker': self.ticker,
            'method': 'geometric_brownian_motion',
            'current_price': float(self.current_price),
            'simulations': int(simulations),
            'days': int(days),
            'lookback_days': int(self.lookback_days),
            'parameters': {
                'drift_daily': float(mu),
                'volatility_daily': float(sigma),
                'drift_annual': float(mu_annual),
                'volatility_annual': float(sigma_annual)
            },
            'statistics': {
                'expected_final_price': float(expected_final),
                'median_final_price': float(median_final),
                'std_final_price': float(std_final),
                'expected_return_pct': float(expected_return),
                'median_return_pct': float(median_return),
                'probability_profit': float(prob_profit),
                'probability_loss': float(prob_loss)
            },
            'percentiles': {
                f'p{p}': float(v) for p, v in zip(percentiles, percentile_values)
            },
            'tail_risk': {
                '1pct_worst_case': float(percentile_values[0]),
                '5pct_worst_case': float(percentile_values[1]),
                '1pct_best_case': float(percentile_values[-1]),
                '5pct_best_case': float(percentile_values[-2])
            },
            'analysis_date': datetime.now().isoformat()
        }
    
    def bootstrap_simulation(
        self,
        days: int = 252,
        simulations: int = 10000,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Bootstrap resampling simulation
        Randomly sample historical returns with replacement
        
        Returns: simulated paths, statistics, percentiles
        """
        if self.returns is None:
            if not self.fetch_data():
                return {'error': 'Failed to fetch data'}
        
        if seed is not None:
            np.random.seed(seed)
        
        # Bootstrap returns
        returns_array = self.returns.values
        
        # Sample with replacement
        # Shape: (simulations, days)
        sampled_returns = np.random.choice(
            returns_array, 
            size=(simulations, days),
            replace=True
        )
        
        # Calculate cumulative returns
        cumulative_returns = np.exp(np.cumsum(sampled_returns, axis=1))
        
        # Calculate price paths
        price_paths = self.current_price * cumulative_returns
        
        # Add initial price
        price_paths = np.column_stack([
            np.full(simulations, self.current_price),
            price_paths
        ])
        
        # Final prices
        final_prices = price_paths[:, -1]
        
        # Calculate statistics
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        percentile_values = np.percentile(final_prices, percentiles)
        
        expected_final = float(np.mean(final_prices))
        median_final = float(np.median(final_prices))
        std_final = float(np.std(final_prices))
        
        prob_profit = float(np.sum(final_prices > self.current_price) / simulations)
        prob_loss = 1.0 - prob_profit
        
        expected_return = ((expected_final / self.current_price) - 1) * 100
        median_return = ((median_final / self.current_price) - 1) * 100
        
        return {
            'ticker': self.ticker,
            'method': 'bootstrap_resampling',
            'current_price': float(self.current_price),
            'simulations': int(simulations),
            'days': int(days),
            'lookback_days': int(self.lookback_days),
            'historical_returns_count': len(returns_array),
            'statistics': {
                'expected_final_price': float(expected_final),
                'median_final_price': float(median_final),
                'std_final_price': float(std_final),
                'expected_return_pct': float(expected_return),
                'median_return_pct': float(median_return),
                'probability_profit': float(prob_profit),
                'probability_loss': float(prob_loss)
            },
            'percentiles': {
                f'p{p}': float(v) for p, v in zip(percentiles, percentile_values)
            },
            'tail_risk': {
                '1pct_worst_case': float(percentile_values[0]),
                '5pct_worst_case': float(percentile_values[1]),
                '1pct_best_case': float(percentile_values[-1]),
                '5pct_best_case': float(percentile_values[-2])
            },
            'analysis_date': datetime.now().isoformat()
        }
    
    def calculate_var_cvar(
        self,
        confidence_levels: List[float] = [0.95, 0.99],
        days: int = 252,
        simulations: int = 10000,
        method: str = 'gbm'
    ) -> Dict:
        """
        Calculate Value-at-Risk (VaR) and Conditional Value-at-Risk (CVaR)
        
        VaR: Maximum expected loss at given confidence level
        CVaR: Expected loss given that VaR threshold is exceeded
        
        Args:
            confidence_levels: List of confidence levels (e.g., [0.95, 0.99])
            days: Simulation horizon
            simulations: Number of simulations
            method: 'gbm' or 'bootstrap'
        """
        # Run simulation
        if method == 'gbm':
            sim_result = self.geometric_brownian_motion(days, simulations)
        elif method == 'bootstrap':
            sim_result = self.bootstrap_simulation(days, simulations)
        else:
            return {'error': f'Unknown method: {method}'}
        
        if 'error' in sim_result:
            return sim_result
        
        # Recalculate to get price paths for VaR
        if self.returns is None:
            if not self.fetch_data():
                return {'error': 'Failed to fetch data'}
        
        # Re-run simulation to get final prices
        if method == 'gbm':
            mu = float(self.returns.mean())
            sigma = float(self.returns.std())
            random_walks = np.random.standard_normal((simulations, days))
            drift = (mu - 0.5 * sigma**2)
            shock = sigma * np.sqrt(1.0) * random_walks
            price_paths = self.current_price * np.exp(np.cumsum(drift + shock, axis=1))
            final_prices = price_paths[:, -1]
        else:  # bootstrap
            returns_array = self.returns.values
            sampled_returns = np.random.choice(returns_array, size=(simulations, days), replace=True)
            cumulative_returns = np.exp(np.cumsum(sampled_returns, axis=1))
            price_paths = self.current_price * cumulative_returns
            final_prices = price_paths[:, -1]
        
        # Calculate returns from current price
        portfolio_returns = (final_prices - self.current_price) / self.current_price
        
        # Sort returns
        sorted_returns = np.sort(portfolio_returns)
        
        # Calculate VaR and CVaR for each confidence level
        var_cvar_results = {}
        
        for conf in confidence_levels:
            # VaR: percentile at (1-conf) level
            var_index = int((1 - conf) * simulations)
            var = float(sorted_returns[var_index])
            
            # CVaR: mean of all returns below VaR
            cvar = float(np.mean(sorted_returns[:var_index]))
            
            # Convert to dollar amounts
            var_dollar = var * self.current_price
            cvar_dollar = cvar * self.current_price
            
            var_cvar_results[f'confidence_{int(conf*100)}pct'] = {
                'var_return_pct': float(var * 100),
                'cvar_return_pct': float(cvar * 100),
                'var_dollar': float(var_dollar),
                'cvar_dollar': float(cvar_dollar),
                'interpretation_var': f'{conf*100}% confident losses will not exceed {abs(var)*100:.2f}%',
                'interpretation_cvar': f'Expected loss if VaR threshold is breached: {abs(cvar)*100:.2f}%'
            }
        
        return {
            'ticker': self.ticker,
            'method': method,
            'current_price': float(self.current_price),
            'simulations': int(simulations),
            'days': int(days),
            'risk_metrics': var_cvar_results,
            'analysis_date': datetime.now().isoformat()
        }
    
    def scenario_analysis(
        self,
        scenarios: Optional[List[Dict]] = None,
        days: int = 252
    ) -> Dict:
        """
        Scenario analysis with custom or predefined scenarios
        
        Scenarios:
        - Bull case: +2 sigma drift, -0.5 sigma volatility
        - Base case: historical drift and volatility
        - Bear case: -2 sigma drift, +0.5 sigma volatility
        - Crash case: -3 sigma drift, +1 sigma volatility
        """
        if self.returns is None:
            if not self.fetch_data():
                return {'error': 'Failed to fetch data'}
        
        mu = float(self.returns.mean())
        sigma = float(self.returns.std())
        
        # Default scenarios
        if scenarios is None:
            scenarios = [
                {
                    'name': 'bull',
                    'drift_adjustment': 2.0,  # +2 sigma
                    'vol_adjustment': -0.5     # -0.5 sigma (lower vol)
                },
                {
                    'name': 'base',
                    'drift_adjustment': 0.0,
                    'vol_adjustment': 0.0
                },
                {
                    'name': 'bear',
                    'drift_adjustment': -2.0,  # -2 sigma
                    'vol_adjustment': 0.5      # +0.5 sigma (higher vol)
                },
                {
                    'name': 'crash',
                    'drift_adjustment': -3.0,  # -3 sigma
                    'vol_adjustment': 1.0      # +1 sigma (much higher vol)
                }
            ]
        
        results = {}
        
        for scenario in scenarios:
            name = scenario['name']
            
            # Adjust parameters
            scenario_mu = mu + (scenario['drift_adjustment'] * sigma / np.sqrt(252))
            scenario_sigma = sigma + (scenario['vol_adjustment'] * sigma * 0.1)
            
            # Ensure positive volatility
            scenario_sigma = max(scenario_sigma, 0.001)
            
            # Single path simulation for each scenario
            t = np.arange(days + 1)
            random_walk = np.random.standard_normal(days)
            
            drift = (scenario_mu - 0.5 * scenario_sigma**2)
            shock = scenario_sigma * random_walk
            
            price_path = self.current_price * np.exp(np.cumsum(np.concatenate([[0], drift + shock])))
            
            final_price = float(price_path[-1])
            total_return = ((final_price / self.current_price) - 1) * 100
            
            # Max drawdown in scenario
            cummax = np.maximum.accumulate(price_path)
            drawdown = (price_path - cummax) / cummax
            max_drawdown = float(np.min(drawdown) * 100)
            
            results[name] = {
                'final_price': final_price,
                'total_return_pct': float(total_return),
                'max_drawdown_pct': max_drawdown,
                'parameters': {
                    'drift_daily': float(scenario_mu),
                    'volatility_daily': float(scenario_sigma),
                    'drift_annual': float(scenario_mu * 252),
                    'volatility_annual': float(scenario_sigma * np.sqrt(252))
                },
                'price_path_sample': [float(p) for p in price_path[::max(1, int(days/10))]]  # 10 points
            }
        
        return {
            'ticker': self.ticker,
            'current_price': float(self.current_price),
            'days': int(days),
            'scenarios': results,
            'analysis_date': datetime.now().isoformat()
        }


def cmd_monte_carlo(args):
    """Handle monte-carlo command"""
    parser = argparse.ArgumentParser(description='Monte Carlo simulation')
    parser.add_argument('ticker', help='Stock ticker symbol')
    parser.add_argument('--simulations', type=int, default=10000, help='Number of simulations (default: 10000)')
    parser.add_argument('--days', type=int, default=252, help='Simulation horizon in days (default: 252)')
    parser.add_argument('--method', choices=['gbm', 'bootstrap'], default='gbm', help='Simulation method')
    parser.add_argument('--lookback', type=int, default=252, help='Historical lookback days (default: 252)')
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility')
    
    parsed = parser.parse_args(args[1:])
    
    sim = MonteCarloSimulator(parsed.ticker.upper(), lookback_days=parsed.lookback)
    
    if parsed.method == 'gbm':
        result = sim.geometric_brownian_motion(
            days=parsed.days,
            simulations=parsed.simulations,
            seed=parsed.seed
        )
    else:
        result = sim.bootstrap_simulation(
            days=parsed.days,
            simulations=parsed.simulations,
            seed=parsed.seed
        )
    
    print(json.dumps(result, indent=2))


def cmd_var(args):
    """Handle var command for VaR/CVaR calculation"""
    parser = argparse.ArgumentParser(description='Calculate Value-at-Risk and CVaR')
    parser.add_argument('ticker', help='Stock ticker symbol')
    parser.add_argument('--confidence', type=float, nargs='+', default=[0.95, 0.99],
                       help='Confidence levels (default: 0.95 0.99)')
    parser.add_argument('--days', type=int, default=252, help='Risk horizon in days (default: 252)')
    parser.add_argument('--simulations', type=int, default=10000, help='Number of simulations')
    parser.add_argument('--method', choices=['gbm', 'bootstrap'], default='gbm', help='Simulation method')
    parser.add_argument('--lookback', type=int, default=252, help='Historical lookback days')
    
    parsed = parser.parse_args(args[1:])
    
    sim = MonteCarloSimulator(parsed.ticker.upper(), lookback_days=parsed.lookback)
    result = sim.calculate_var_cvar(
        confidence_levels=parsed.confidence,
        days=parsed.days,
        simulations=parsed.simulations,
        method=parsed.method
    )
    
    print(json.dumps(result, indent=2))


def cmd_scenario(args):
    """Handle scenario command for scenario analysis"""
    parser = argparse.ArgumentParser(description='Scenario analysis')
    parser.add_argument('ticker', help='Stock ticker symbol')
    parser.add_argument('--days', type=int, default=252, help='Scenario horizon in days')
    parser.add_argument('--lookback', type=int, default=252, help='Historical lookback days')
    
    parsed = parser.parse_args(args[1:])
    
    sim = MonteCarloSimulator(parsed.ticker.upper(), lookback_days=parsed.lookback)
    result = sim.scenario_analysis(days=parsed.days)
    
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: monte_carlo.py [monte-carlo|var|scenario] ...", file=sys.stderr)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'monte-carlo':
        cmd_monte_carlo(sys.argv[1:])
    elif command == 'var':
        cmd_var(sys.argv[1:])
    elif command == 'scenario':
        cmd_scenario(sys.argv[1:])
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)
