"""
TensorTrade - RL-Driven Trading Framework (#287)

Reinforcement learning framework for algorithmic trading inspired by TensorTrade.
Provides environment setup, observation spaces, reward schemes, and basic
RL agent training utilities for quantitative trading strategies.

Uses lightweight numpy-based implementations for deployment without TensorFlow.
Focus on practical reward functions, position management, and portfolio optimization.

Phase: 287 | Category: AI/ML Models | Source: github.com/tensortrade-org/tensortrade
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any


class TradingEnvironment:
    """
    Trading environment for RL agents with configurable reward schemes.
    
    Supports multiple reward functions: simple returns, Sharpe ratio,
    risk-adjusted returns, and portfolio value changes.
    """
    
    def __init__(
        self,
        prices: List[float],
        initial_balance: float = 10000.0,
        commission: float = 0.001,
        reward_scheme: str = "simple"
    ):
        """
        Initialize trading environment.
        
        Args:
            prices: Historical price data
            initial_balance: Starting cash balance
            commission: Transaction fee (0.001 = 0.1%)
            reward_scheme: One of 'simple', 'sharpe', 'risk_adjusted', 'pnl'
        """
        if len(prices) < 2:
            raise ValueError("Need at least 2 price points")
        
        self.prices = np.array(prices, dtype=np.float64)
        self.initial_balance = initial_balance
        self.commission = commission
        self.reward_scheme = reward_scheme
        self.reset()
    
    def reset(self) -> Dict[str, Any]:
        """Reset environment to initial state."""
        self.current_step = 0
        self.balance = self.initial_balance
        self.shares = 0.0
        self.net_worth = self.initial_balance
        self.trades_history = []
        self.net_worth_history = [self.initial_balance]
        
        return self._get_observation()
    
    def _get_observation(self) -> Dict[str, Any]:
        """Get current market observation."""
        lookback = min(20, self.current_step + 1)
        window_prices = self.prices[max(0, self.current_step - lookback + 1):self.current_step + 1]
        
        # Calculate technical features
        if len(window_prices) > 1:
            returns = np.diff(window_prices) / window_prices[:-1]
            volatility = np.std(returns) if len(returns) > 0 else 0.0
            momentum = (window_prices[-1] - window_prices[0]) / window_prices[0]
        else:
            volatility = 0.0
            momentum = 0.0
        
        current_price = self.prices[self.current_step]
        position_value = self.shares * current_price
        
        return {
            "step": self.current_step,
            "price": float(current_price),
            "balance": float(self.balance),
            "shares": float(self.shares),
            "net_worth": float(self.net_worth),
            "position_ratio": float(position_value / self.net_worth if self.net_worth > 0 else 0),
            "volatility": float(volatility),
            "momentum": float(momentum),
            "prices_window": window_prices.tolist()
        }
    
    def step(self, action: int) -> Tuple[Dict[str, Any], float, bool, Dict[str, Any]]:
        """
        Execute trading action.
        
        Args:
            action: 0=hold, 1=buy 25%, 2=buy 50%, 3=sell 50%, 4=sell 100%
        
        Returns:
            (observation, reward, done, info)
        """
        current_price = self.prices[self.current_step]
        old_net_worth = self.net_worth
        
        # Execute action
        trade_info = None
        if action == 1:  # Buy 25%
            trade_info = self._execute_buy(current_price, 0.25)
        elif action == 2:  # Buy 50%
            trade_info = self._execute_buy(current_price, 0.50)
        elif action == 3:  # Sell 50%
            trade_info = self._execute_sell(current_price, 0.50)
        elif action == 4:  # Sell 100%
            trade_info = self._execute_sell(current_price, 1.0)
        
        # Update net worth
        self.net_worth = self.balance + self.shares * current_price
        self.net_worth_history.append(self.net_worth)
        
        # Calculate reward
        reward = self._calculate_reward(old_net_worth, self.net_worth)
        
        # Move to next step
        self.current_step += 1
        done = self.current_step >= len(self.prices) - 1
        
        observation = self._get_observation() if not done else {}
        info = {
            "trade": trade_info,
            "portfolio_value": float(self.net_worth),
            "return": float((self.net_worth - self.initial_balance) / self.initial_balance)
        }
        
        return observation, reward, done, info
    
    def _execute_buy(self, price: float, fraction: float) -> Optional[Dict[str, Any]]:
        """Execute buy order."""
        available = self.balance * fraction
        if available < price * 0.1:  # Min 0.1 share
            return None
        
        shares_to_buy = available / (price * (1 + self.commission))
        cost = shares_to_buy * price * (1 + self.commission)
        
        if cost <= self.balance:
            self.balance -= cost
            self.shares += shares_to_buy
            
            trade = {
                "type": "buy",
                "step": self.current_step,
                "price": float(price),
                "shares": float(shares_to_buy),
                "cost": float(cost),
                "fraction": fraction
            }
            self.trades_history.append(trade)
            return trade
        
        return None
    
    def _execute_sell(self, price: float, fraction: float) -> Optional[Dict[str, Any]]:
        """Execute sell order."""
        shares_to_sell = self.shares * fraction
        if shares_to_sell < 0.01:
            return None
        
        revenue = shares_to_sell * price * (1 - self.commission)
        self.balance += revenue
        self.shares -= shares_to_sell
        
        trade = {
            "type": "sell",
            "step": self.current_step,
            "price": float(price),
            "shares": float(shares_to_sell),
            "revenue": float(revenue),
            "fraction": fraction
        }
        self.trades_history.append(trade)
        return trade
    
    def _calculate_reward(self, old_worth: float, new_worth: float) -> float:
        """Calculate reward based on configured scheme."""
        if self.reward_scheme == "simple":
            # Simple return
            return (new_worth - old_worth) / old_worth if old_worth > 0 else 0.0
        
        elif self.reward_scheme == "pnl":
            # Absolute PnL normalized by initial balance
            return (new_worth - old_worth) / self.initial_balance
        
        elif self.reward_scheme == "sharpe":
            # Approximate Sharpe using recent returns
            if len(self.net_worth_history) < 2:
                return 0.0
            returns = np.diff(self.net_worth_history[-20:]) / self.net_worth_history[-20:-1]
            if len(returns) > 1:
                mean_ret = np.mean(returns)
                std_ret = np.std(returns) + 1e-8
                return mean_ret / std_ret
            return 0.0
        
        elif self.reward_scheme == "risk_adjusted":
            # Return minus volatility penalty
            ret = (new_worth - old_worth) / old_worth if old_worth > 0 else 0.0
            if len(self.net_worth_history) >= 10:
                recent = np.array(self.net_worth_history[-10:])
                vol = np.std(np.diff(recent) / recent[:-1])
                return ret - 0.5 * vol
            return ret
        
        return 0.0


def create_trading_env(
    prices: List[float],
    initial_balance: float = 10000.0,
    commission: float = 0.001,
    reward_scheme: str = "simple"
) -> Dict[str, Any]:
    """
    Create a trading environment configuration.
    
    Args:
        prices: Historical price data
        initial_balance: Starting cash
        commission: Transaction fee rate
        reward_scheme: Reward calculation method
    
    Returns:
        Environment configuration dict
    """
    try:
        env = TradingEnvironment(prices, initial_balance, commission, reward_scheme)
        obs = env.reset()
        
        return {
            "success": True,
            "environment": env,
            "initial_observation": obs,
            "action_space": {
                "type": "discrete",
                "n": 5,
                "actions": ["hold", "buy_25%", "buy_50%", "sell_50%", "sell_100%"]
            },
            "observation_space": {
                "price": "float",
                "balance": "float",
                "shares": "float",
                "net_worth": "float",
                "position_ratio": "float",
                "volatility": "float",
                "momentum": "float"
            },
            "config": {
                "initial_balance": initial_balance,
                "commission": commission,
                "reward_scheme": reward_scheme,
                "steps": len(prices)
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


def train_random_agent(
    prices: List[float],
    episodes: int = 10,
    reward_scheme: str = "simple"
) -> Dict[str, Any]:
    """
    Train a random baseline agent for benchmarking.
    
    Args:
        prices: Historical price data
        episodes: Number of training episodes
        reward_scheme: Reward calculation method
    
    Returns:
        Training results dict
    """
    try:
        env = TradingEnvironment(prices, reward_scheme=reward_scheme)
        results = []
        
        for episode in range(episodes):
            obs = env.reset()
            episode_reward = 0.0
            done = False
            steps = 0
            
            while not done:
                action = np.random.randint(0, 5)  # Random action
                obs, reward, done, info = env.step(action)
                episode_reward += reward
                steps += 1
            
            final_return = (env.net_worth - env.initial_balance) / env.initial_balance
            results.append({
                "episode": episode,
                "total_reward": float(episode_reward),
                "final_return": float(final_return),
                "final_net_worth": float(env.net_worth),
                "trades": len(env.trades_history),
                "steps": steps
            })
        
        returns = [r["final_return"] for r in results]
        
        return {
            "success": True,
            "episodes": episodes,
            "results": results,
            "statistics": {
                "mean_return": float(np.mean(returns)),
                "std_return": float(np.std(returns)),
                "min_return": float(np.min(returns)),
                "max_return": float(np.max(returns)),
                "sharpe": float(np.mean(returns) / (np.std(returns) + 1e-8))
            },
            "reward_scheme": reward_scheme
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


def backtest_strategy(
    prices: List[float],
    actions: List[int],
    initial_balance: float = 10000.0,
    commission: float = 0.001
) -> Dict[str, Any]:
    """
    Backtest a predefined action sequence.
    
    Args:
        prices: Historical price data
        actions: List of actions (0=hold, 1=buy25%, 2=buy50%, 3=sell50%, 4=sell100%)
        initial_balance: Starting cash
        commission: Transaction fee rate
    
    Returns:
        Backtest results dict
    """
    try:
        if len(actions) != len(prices):
            raise ValueError(f"Actions length {len(actions)} must match prices length {len(prices)}")
        
        env = TradingEnvironment(prices, initial_balance, commission)
        obs = env.reset()
        
        total_reward = 0.0
        for action in actions:
            obs, reward, done, info = env.step(action)
            total_reward += reward
            if done:
                break
        
        final_return = (env.net_worth - initial_balance) / initial_balance
        
        # Calculate buy & hold benchmark
        shares_bh = initial_balance / prices[0]
        bh_value = shares_bh * prices[-1]
        bh_return = (bh_value - initial_balance) / initial_balance
        
        return {
            "success": True,
            "strategy_return": float(final_return),
            "buy_hold_return": float(bh_return),
            "outperformance": float(final_return - bh_return),
            "final_balance": float(env.balance),
            "final_shares": float(env.shares),
            "final_net_worth": float(env.net_worth),
            "total_trades": len(env.trades_history),
            "total_reward": float(total_reward),
            "trades": env.trades_history,
            "net_worth_history": [float(x) for x in env.net_worth_history]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.0) -> Dict[str, Any]:
    """
    Calculate Sharpe ratio for a return series.
    
    Args:
        returns: List of period returns
        risk_free_rate: Risk-free rate (annualized)
    
    Returns:
        Sharpe ratio and statistics dict
    """
    try:
        if len(returns) < 2:
            raise ValueError("Need at least 2 returns")
        
        returns_arr = np.array(returns, dtype=np.float64)
        excess_returns = returns_arr - risk_free_rate / 252  # Daily risk-free
        
        mean_excess = np.mean(excess_returns)
        std_excess = np.std(excess_returns, ddof=1)
        
        sharpe = mean_excess / std_excess if std_excess > 0 else 0.0
        annualized_sharpe = sharpe * np.sqrt(252)  # Assuming daily returns
        
        return {
            "success": True,
            "sharpe_ratio": float(sharpe),
            "annualized_sharpe": float(annualized_sharpe),
            "mean_return": float(mean_excess),
            "std_return": float(std_excess),
            "periods": len(returns)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


def optimize_portfolio(
    prices_matrix: List[List[float]],
    risk_aversion: float = 1.0
) -> Dict[str, Any]:
    """
    Simple mean-variance portfolio optimization.
    
    Args:
        prices_matrix: List of price series for each asset
        risk_aversion: Risk aversion parameter (higher = more conservative)
    
    Returns:
        Optimal weights dict
    """
    try:
        if len(prices_matrix) < 1 or len(prices_matrix[0]) < 2:
            raise ValueError("Need at least 1 asset with 2 prices")
        
        # Calculate returns
        returns_matrix = []
        for prices in prices_matrix:
            prices_arr = np.array(prices, dtype=np.float64)
            returns = np.diff(prices_arr) / prices_arr[:-1]
            returns_matrix.append(returns)
        
        returns_matrix = np.array(returns_matrix)
        
        # Calculate mean returns and covariance
        mean_returns = np.mean(returns_matrix, axis=1)
        cov_matrix = np.cov(returns_matrix)
        
        # Simple optimization: maximize (return - risk_aversion * variance)
        n_assets = len(prices_matrix)
        weights = np.ones(n_assets) / n_assets  # Start with equal weights
        
        # Grid search for better weights (simplified)
        best_score = -np.inf
        best_weights = weights.copy()
        
        for _ in range(100):
            w = np.random.dirichlet(np.ones(n_assets))
            portfolio_return = np.dot(w, mean_returns)
            portfolio_var = np.dot(w, np.dot(cov_matrix, w))
            score = portfolio_return - risk_aversion * portfolio_var
            
            if score > best_score:
                best_score = score
                best_weights = w
        
        portfolio_return = np.dot(best_weights, mean_returns)
        portfolio_vol = np.sqrt(np.dot(best_weights, np.dot(cov_matrix, best_weights)))
        
        return {
            "success": True,
            "weights": [float(w) for w in best_weights],
            "expected_return": float(portfolio_return),
            "expected_volatility": float(portfolio_vol),
            "sharpe": float(portfolio_return / portfolio_vol if portfolio_vol > 0 else 0),
            "risk_aversion": risk_aversion,
            "n_assets": n_assets
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


# Public API
__all__ = [
    "TradingEnvironment",
    "create_trading_env",
    "train_random_agent",
    "backtest_strategy",
    "calculate_sharpe_ratio",
    "optimize_portfolio"
]
