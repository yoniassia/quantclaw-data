#!/usr/bin/env python3
"""
FinRL — Financial Reinforcement Learning Framework
Open-source framework for training RL agents for trading strategies using deep learning.
Integrates with Gym environments, Stable Baselines, PyTorch/TensorFlow for alpha generation.

Source: https://github.com/AI4Finance-Foundation/FinRL
Category: Quant Tools & ML
Free tier: True (open-source)
Update frequency: Quarterly GitHub updates
Generated: 2026-03-05

Data points: Trading environments (state spaces, rewards), agent performance metrics (profit, volatility),
            hyperparameters (learning rate, episodes), market data integrations (OHLCV, fundamentals)
"""

import json
from datetime import datetime

def check_installation():
    """
    Check if FinRL is installed and return installation status.
    
    Returns:
        dict: Installation status and version info
    """
    try:
        import finrl
        return {
            "installed": True,
            "version": getattr(finrl, '__version__', 'unknown'),
            "message": "FinRL is installed and ready to use"
        }
    except ImportError:
        return {
            "installed": False,
            "version": None,
            "message": "FinRL not installed. Install with: pip install finrl",
            "install_command": "pip install finrl"
        }

def get_environment_list():
    """
    Get list of available trading environments in FinRL.
    
    Returns:
        dict: Available environments and their descriptions
    """
    environments = {
        "single_stock": {
            "name": "StockTradingEnv",
            "description": "Single stock trading with continuous actions",
            "state_space": "price, volume, technical indicators",
            "action_space": "buy/sell/hold with amount"
        },
        "portfolio": {
            "name": "PortfolioAllocationEnv",
            "description": "Multi-asset portfolio allocation",
            "state_space": "prices, returns, correlations",
            "action_space": "portfolio weights"
        },
        "multiple_stock": {
            "name": "MultipleStockEnv",
            "description": "Trade multiple stocks simultaneously",
            "state_space": "OHLCV + indicators for all stocks",
            "action_space": "positions for each stock"
        }
    }
    return environments

def create_simple_env_config(ticker="AAPL", start_date="2020-01-01", end_date="2023-12-31"):
    """
    Create a basic environment configuration for FinRL training.
    
    Args:
        ticker: Stock ticker symbol
        start_date: Training start date (YYYY-MM-DD)
        end_date: Training end date (YYYY-MM-DD)
    
    Returns:
        dict: Environment configuration
    """
    config = {
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date,
        "technical_indicators": [
            "macd", "rsi", "cci", "adx"
        ],
        "initial_capital": 100000,
        "transaction_cost_pct": 0.001,
        "reward_scaling": 1e-4,
        "state_space": {
            "price": "close",
            "volume": "volume",
            "indicators": ["macd", "rsi", "cci", "adx"]
        },
        "action_space": {
            "type": "continuous",
            "range": [-1, 1],  # -1 = sell all, 0 = hold, 1 = buy all
        }
    }
    return config

def get_recommended_algorithms():
    """
    Get recommended RL algorithms for different trading scenarios.
    
    Returns:
        dict: Algorithm recommendations with hyperparameters
    """
    algorithms = {
        "ppo": {
            "name": "Proximal Policy Optimization",
            "use_case": "General purpose, stable training",
            "hyperparameters": {
                "learning_rate": 3e-4,
                "n_steps": 2048,
                "batch_size": 64,
                "n_epochs": 10,
                "gamma": 0.99
            },
            "library": "stable-baselines3"
        },
        "a2c": {
            "name": "Advantage Actor-Critic",
            "use_case": "Fast training, good for continuous actions",
            "hyperparameters": {
                "learning_rate": 7e-4,
                "n_steps": 5,
                "gamma": 0.99,
                "ent_coef": 0.01
            },
            "library": "stable-baselines3"
        },
        "ddpg": {
            "name": "Deep Deterministic Policy Gradient",
            "use_case": "Continuous action spaces, portfolio optimization",
            "hyperparameters": {
                "learning_rate": 1e-3,
                "buffer_size": 1000000,
                "batch_size": 100,
                "tau": 0.005,
                "gamma": 0.99
            },
            "library": "stable-baselines3"
        },
        "td3": {
            "name": "Twin Delayed DDPG",
            "use_case": "Improved DDPG, less overestimation",
            "hyperparameters": {
                "learning_rate": 1e-3,
                "buffer_size": 1000000,
                "batch_size": 100,
                "policy_delay": 2,
                "target_noise": 0.2
            },
            "library": "stable-baselines3"
        },
        "sac": {
            "name": "Soft Actor-Critic",
            "use_case": "Maximum entropy RL, robust policies",
            "hyperparameters": {
                "learning_rate": 3e-4,
                "buffer_size": 1000000,
                "batch_size": 256,
                "tau": 0.005,
                "gamma": 0.99
            },
            "library": "stable-baselines3"
        }
    }
    return algorithms

def get_training_workflow():
    """
    Get step-by-step workflow for training a FinRL agent.
    
    Returns:
        dict: Training workflow steps
    """
    workflow = {
        "steps": [
            {
                "step": 1,
                "title": "Install FinRL",
                "command": "pip install finrl",
                "description": "Install the FinRL library and dependencies"
            },
            {
                "step": 2,
                "title": "Prepare Data",
                "code": "from finrl.meta.preprocessor.yahoodownloader import YahooDownloader\ndf = YahooDownloader(start_date='2020-01-01', end_date='2023-12-31', ticker_list=['AAPL']).fetch_data()",
                "description": "Download and preprocess market data"
            },
            {
                "step": 3,
                "title": "Feature Engineering",
                "code": "from finrl.meta.preprocessor.preprocessors import FeatureEngineer\nfe = FeatureEngineer(use_technical_indicator=True, tech_indicator_list=['macd', 'rsi'])\nprocessed_df = fe.preprocess_data(df)",
                "description": "Add technical indicators and features"
            },
            {
                "step": 4,
                "title": "Create Environment",
                "code": "from finrl.meta.env_stock_trading.env_stocktrading import StockTradingEnv\nenv = StockTradingEnv(df=processed_df, **config)",
                "description": "Initialize the trading environment"
            },
            {
                "step": 5,
                "title": "Train Agent",
                "code": "from stable_baselines3 import PPO\nmodel = PPO('MlpPolicy', env, verbose=1)\nmodel.learn(total_timesteps=100000)",
                "description": "Train the RL agent using chosen algorithm"
            },
            {
                "step": 6,
                "title": "Backtest",
                "code": "from finrl.meta.env_stock_trading.env_stocktrading import StockTradingEnv\ntest_env = StockTradingEnv(df=test_df, turbulence_threshold=None)\nobs = test_env.reset()\nfor i in range(len(test_df)):\n    action, _ = model.predict(obs)\n    obs, rewards, dones, info = test_env.step(action)",
                "description": "Test the trained agent on out-of-sample data"
            },
            {
                "step": 7,
                "title": "Evaluate Performance",
                "code": "from finrl.meta.data_processors.processor_alpaca import AlpacaProcessor\nstats = AlpacaProcessor().get_trading_stats()",
                "description": "Calculate Sharpe ratio, returns, drawdown"
            }
        ],
        "example_notebook": "https://github.com/AI4Finance-Foundation/FinRL/blob/master/tutorials/1-Introduction/FinRL_StockTrading_NeurIPS_2018.ipynb"
    }
    return workflow

def get_performance_metrics_guide():
    """
    Get guide for evaluating RL agent performance.
    
    Returns:
        dict: Performance metrics and evaluation methods
    """
    metrics = {
        "key_metrics": {
            "cumulative_returns": "Total return over the trading period",
            "sharpe_ratio": "Risk-adjusted returns (returns / volatility)",
            "max_drawdown": "Maximum peak-to-trough decline",
            "sortino_ratio": "Downside risk-adjusted returns",
            "calmar_ratio": "Return / max drawdown",
            "win_rate": "Percentage of profitable trades",
            "profit_factor": "Gross profit / gross loss"
        },
        "comparison_benchmarks": [
            "Buy and Hold (B&H) strategy",
            "S&P 500 index",
            "Technical indicators (MACD, RSI)",
            "Random walk baseline"
        ],
        "overfitting_checks": [
            "Train/validation/test split (70/15/15)",
            "Walk-forward analysis",
            "Monte Carlo simulation of strategies",
            "Out-of-sample testing on different time periods"
        ]
    }
    return metrics

def get_common_pitfalls():
    """
    Get common pitfalls and best practices for FinRL.
    
    Returns:
        dict: Common issues and solutions
    """
    pitfalls = {
        "lookahead_bias": {
            "problem": "Using future information in training",
            "solution": "Ensure data preprocessing is done chronologically, split data before any processing"
        },
        "overfitting": {
            "problem": "Agent performs well in training but fails in testing",
            "solution": "Use regularization, early stopping, and test on multiple out-of-sample periods"
        },
        "unrealistic_costs": {
            "problem": "Not accounting for transaction costs and slippage",
            "solution": "Set realistic transaction_cost_pct (0.1-0.5%), model slippage based on volume"
        },
        "reward_engineering": {
            "problem": "Poorly designed reward function leads to unexpected behavior",
            "solution": "Start with simple returns-based rewards, add penalties for excessive trading/risk"
        },
        "insufficient_training": {
            "problem": "Agent hasn't converged or explored enough",
            "solution": "Increase total_timesteps, monitor training curves, use curriculum learning"
        }
    }
    return pitfalls

def get_resources():
    """
    Get learning resources and documentation links.
    
    Returns:
        dict: Resources for learning FinRL
    """
    resources = {
        "official_docs": "https://finrl.readthedocs.io/",
        "github_repo": "https://github.com/AI4Finance-Foundation/FinRL",
        "paper": "https://arxiv.org/abs/2011.09607",
        "tutorials": [
            "https://github.com/AI4Finance-Foundation/FinRL/tree/master/tutorials",
            "https://towardsdatascience.com/finrl-for-quantitative-finance-tutorial-for-single-stock-trading-37d6d7c30aac"
        ],
        "discord_community": "https://discord.gg/trsr8SXpW5",
        "stable_baselines3_docs": "https://stable-baselines3.readthedocs.io/"
    }
    return resources

def get_info():
    """
    Get comprehensive information about FinRL module.
    
    Returns:
        dict: Complete module information
    """
    install_status = check_installation()
    
    return {
        "module": "finrl",
        "description": "Financial Reinforcement Learning Framework for algorithmic trading",
        "installation": install_status,
        "environments": get_environment_list(),
        "algorithms": get_recommended_algorithms(),
        "workflow": get_training_workflow(),
        "metrics": get_performance_metrics_guide(),
        "pitfalls": get_common_pitfalls(),
        "resources": get_resources(),
        "generated": datetime.now().isoformat(),
        "source": "https://github.com/AI4Finance-Foundation/FinRL"
    }

if __name__ == "__main__":
    info = get_info()
    print(json.dumps(info, indent=2))
