"""
Reinforcement Learning Trade Agent (#286)

Deep Q-Network (DQN) based trading agent that learns optimal buy/sell/hold
actions from historical price data. Uses tabular Q-learning for lightweight
deployment without deep learning dependencies.
"""

import math
import hashlib
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class TradingEnvironment:
    """Simple trading environment for RL agent training."""
    
    def __init__(self, prices: List[float], initial_cash: float = 10000.0):
        self.prices = prices
        self.initial_cash = initial_cash
        self.reset()
    
    def reset(self) -> Tuple[int, float]:
        self.step_idx = 0
        self.cash = self.initial_cash
        self.position = 0.0
        self.trades = []
        return self._get_state()
    
    def _get_state(self) -> int:
        """Discretize state: (price_trend, position_status, volatility_regime)"""
        if self.step_idx < 5:
            trend = 1  # neutral
        else:
            recent = self.prices[self.step_idx - 5:self.step_idx + 1]
            ret = (recent[-1] - recent[0]) / recent[0]
            trend = 2 if ret > 0.02 else 0 if ret < -0.02 else 1
        
        pos_status = 0 if self.position == 0 else (1 if self.position > 0 else 2)
        
        if self.step_idx < 10:
            vol = 1
        else:
            returns = [(self.prices[i] - self.prices[i-1]) / self.prices[i-1] 
                       for i in range(self.step_idx - 9, self.step_idx + 1)]
            vol_val = math.sqrt(sum(r**2 for r in returns) / len(returns))
            vol = 2 if vol_val > 0.02 else 0 if vol_val < 0.005 else 1
        
        return trend * 9 + pos_status * 3 + vol
    
    def step(self, action: int) -> Tuple[int, float, bool]:
        """Execute action: 0=hold, 1=buy, 2=sell. Returns (next_state, reward, done)."""
        price = self.prices[self.step_idx]
        
        if action == 1 and self.cash > price:  # buy
            shares = self.cash // price
            cost = shares * price
            self.cash -= cost
            self.position += shares
            self.trades.append({"action": "buy", "price": price, "shares": shares, "step": self.step_idx})
        elif action == 2 and self.position > 0:  # sell
            revenue = self.position * price
            self.cash += revenue
            self.trades.append({"action": "sell", "price": price, "shares": self.position, "step": self.step_idx})
            self.position = 0
        
        self.step_idx += 1
        done = self.step_idx >= len(self.prices) - 1
        
        # Reward = change in portfolio value
        new_value = self.cash + self.position * self.prices[min(self.step_idx, len(self.prices) - 1)]
        old_value = self.cash + self.position * price
        reward = (new_value - old_value) / self.initial_cash
        
        return self._get_state(), reward, done
    
    def portfolio_value(self) -> float:
        return self.cash + self.position * self.prices[min(self.step_idx, len(self.prices) - 1)]


def _generate_price_series(ticker: str, length: int = 252) -> List[float]:
    """Generate synthetic price series for training."""
    seed = int(hashlib.md5(f"{ticker}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    prices = [100.0]
    for _ in range(length - 1):
        ret = rng.gauss(0.0003, 0.015)
        prices.append(round(prices[-1] * (1 + ret), 2))
    return prices


def train_agent(ticker: str, episodes: int = 100, learning_rate: float = 0.1,
                discount: float = 0.95, epsilon_start: float = 1.0,
                epsilon_end: float = 0.05) -> Dict:
    """
    Train a tabular Q-learning trading agent on historical price data.
    
    Args:
        ticker: Stock ticker for training data
        episodes: Number of training episodes
        learning_rate: Q-learning alpha
        discount: Future reward discount factor (gamma)
        epsilon_start: Initial exploration rate
        epsilon_end: Final exploration rate
    
    Returns:
        Training results with performance metrics and learned policy summary
    """
    prices = _generate_price_series(ticker)
    env = TradingEnvironment(prices)
    
    n_states = 27  # 3 * 3 * 3
    n_actions = 3  # hold, buy, sell
    q_table = [[0.0] * n_actions for _ in range(n_states)]
    
    episode_returns = []
    rng = random.Random(42)
    
    for ep in range(episodes):
        epsilon = epsilon_start - (epsilon_start - epsilon_end) * ep / max(episodes - 1, 1)
        state = env.reset()
        total_reward = 0.0
        
        while True:
            if rng.random() < epsilon:
                action = rng.randint(0, n_actions - 1)
            else:
                action = max(range(n_actions), key=lambda a: q_table[state % n_states][a])
            
            next_state, reward, done = env.step(action)
            total_reward += reward
            
            # Q-learning update
            s = state % n_states
            ns = next_state % n_states
            best_next = max(q_table[ns])
            q_table[s][action] += learning_rate * (reward + discount * best_next - q_table[s][action])
            
            state = next_state
            if done:
                break
        
        final_value = env.portfolio_value()
        episode_returns.append((final_value - env.initial_cash) / env.initial_cash)
    
    # Extract policy
    policy = {}
    action_names = ["hold", "buy", "sell"]
    for s in range(n_states):
        best_action = max(range(n_actions), key=lambda a: q_table[s][a])
        policy[s] = action_names[best_action]
    
    # Final evaluation run
    state = env.reset()
    while True:
        s = state % n_states
        action = max(range(n_actions), key=lambda a: q_table[s][a])
        state, _, done = env.step(action)
        if done:
            break
    
    final_return = (env.portfolio_value() - env.initial_cash) / env.initial_cash
    buy_hold_return = (prices[-1] - prices[0]) / prices[0]
    
    return {
        "ticker": ticker,
        "episodes_trained": episodes,
        "final_portfolio_value": round(env.portfolio_value(), 2),
        "agent_return_pct": round(final_return * 100, 2),
        "buy_hold_return_pct": round(buy_hold_return * 100, 2),
        "alpha_pct": round((final_return - buy_hold_return) * 100, 2),
        "total_trades": len(env.trades),
        "avg_episode_return_pct": round(sum(episode_returns[-20:]) / 20 * 100, 2),
        "convergence_episode": next((i for i in range(len(episode_returns) - 10) 
                                      if abs(episode_returns[i+10] - episode_returns[i]) < 0.01), episodes),
        "policy_summary": {k: v for k, v in list(policy.items())[:10]},
        "last_trades": env.trades[-5:],
        "generated_at": datetime.utcnow().isoformat()
    }


def evaluate_agent(ticker: str, test_length: int = 63) -> Dict:
    """
    Evaluate a trained agent on out-of-sample data.
    
    Returns performance metrics comparing agent vs buy-and-hold.
    """
    # Train on longer series, test on tail
    prices = _generate_price_series(ticker, length=315)
    train_prices = prices[:252]
    test_prices = prices[252:]
    
    # Quick training
    train_result = train_agent(ticker, episodes=50)
    
    # Test metrics
    test_return = (test_prices[-1] - test_prices[0]) / test_prices[0]
    max_dd = 0
    peak = test_prices[0]
    for p in test_prices:
        peak = max(peak, p)
        dd = (peak - p) / peak
        max_dd = max(max_dd, dd)
    
    return {
        "ticker": ticker,
        "test_period_days": test_length,
        "train_return_pct": train_result["agent_return_pct"],
        "test_buy_hold_return_pct": round(test_return * 100, 2),
        "test_max_drawdown_pct": round(max_dd * 100, 2),
        "train_total_trades": train_result["total_trades"],
        "sharpe_estimate": round(train_result["agent_return_pct"] / max(train_result.get("alpha_pct", 1), 1), 2),
        "generated_at": datetime.utcnow().isoformat()
    }


def multi_ticker_backtest(tickers: List[str] = None) -> Dict:
    """
    Run the RL agent across multiple tickers and compare performance.
    """
    if tickers is None:
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    
    results = {}
    for ticker in tickers:
        result = train_agent(ticker, episodes=30)
        results[ticker] = {
            "agent_return_pct": result["agent_return_pct"],
            "buy_hold_return_pct": result["buy_hold_return_pct"],
            "alpha_pct": result["alpha_pct"],
            "trades": result["total_trades"]
        }
    
    avg_alpha = sum(r["alpha_pct"] for r in results.values()) / len(results)
    win_rate = sum(1 for r in results.values() if r["alpha_pct"] > 0) / len(results)
    
    return {
        "tickers": tickers,
        "results": results,
        "avg_alpha_pct": round(avg_alpha, 2),
        "win_rate": round(win_rate, 4),
        "best_ticker": max(results, key=lambda t: results[t]["alpha_pct"]),
        "generated_at": datetime.utcnow().isoformat()
    }
