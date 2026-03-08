#!/usr/bin/env python3
"""
FinRL-Meta — Meta-Learning Framework for Financial Deep RL
Advanced deep reinforcement learning framework with meta-learning, ensemble methods,
AutoML for hyperparameter optimization, and multi-source data integration for quantitative trading.

Source: https://github.com/AI4Finance-Foundation/FinRL
Category: Quant Tools & ML & Meta-Learning
Free tier: True (open-source)
Update frequency: Quarterly GitHub updates
Generated: 2026-03-08

Data points: Multi-asset environments, ensemble agent performance, hyperparameter search results,
            market regime detection, data source integrations (stocks, crypto, forex)
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any

def check_installation() -> Dict[str, Any]:
    """
    Check if FinRL and required dependencies are installed.
    
    Returns:
        dict: Installation status for FinRL and key dependencies
    
    Example:
        >>> status = check_installation()
        >>> print(status['finrl']['installed'])
    """
    try:
        dependencies = {}
        
        # Check FinRL
        try:
            import finrl
            dependencies['finrl'] = {
                "installed": True,
                "version": getattr(finrl, '__version__', 'unknown'),
                "status": "ready"
            }
        except ImportError:
            dependencies['finrl'] = {
                "installed": False,
                "version": None,
                "status": "missing",
                "install_command": "pip install finrl"
            }
        
        # Check Stable Baselines3 (RL library)
        try:
            import stable_baselines3
            dependencies['stable_baselines3'] = {
                "installed": True,
                "version": stable_baselines3.__version__,
                "status": "ready"
            }
        except ImportError:
            dependencies['stable_baselines3'] = {
                "installed": False,
                "version": None,
                "status": "missing",
                "install_command": "pip install stable-baselines3"
            }
        
        # Check PyTorch (deep learning backend)
        try:
            import torch
            dependencies['torch'] = {
                "installed": True,
                "version": torch.__version__,
                "cuda_available": torch.cuda.is_available(),
                "status": "ready"
            }
        except ImportError:
            dependencies['torch'] = {
                "installed": False,
                "version": None,
                "status": "missing",
                "install_command": "pip install torch"
            }
        
        # Check Gym (RL environment framework)
        try:
            import gym
            dependencies['gym'] = {
                "installed": True,
                "version": gym.__version__,
                "status": "ready"
            }
        except ImportError:
            dependencies['gym'] = {
                "installed": False,
                "version": None,
                "status": "missing",
                "install_command": "pip install gym"
            }
        
        # Overall status
        all_installed = all(dep['installed'] for dep in dependencies.values())
        
        return {
            "overall_status": "ready" if all_installed else "incomplete",
            "dependencies": dependencies,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "overall_status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def get_data_sources() -> Dict[str, Any]:
    """
    Get available data sources for FinRL-Meta training.
    
    Returns:
        dict: Available free data sources with APIs and access methods
    
    Example:
        >>> sources = get_data_sources()
        >>> print(sources['stocks']['providers'])
    """
    return {
        "stocks": {
            "providers": [
                {
                    "name": "Yahoo Finance",
                    "api": "yfinance",
                    "markets": ["US", "International"],
                    "data_types": ["OHLCV", "Fundamentals", "Dividends"],
                    "free": True,
                    "rate_limit": "2000 requests/hour",
                    "install": "pip install yfinance"
                },
                {
                    "name": "Alpha Vantage",
                    "api": "alpha_vantage",
                    "markets": ["US", "Forex", "Crypto"],
                    "data_types": ["OHLCV", "Technical Indicators", "Fundamentals"],
                    "free": True,
                    "rate_limit": "5 requests/minute (free tier)",
                    "requires_key": True,
                    "install": "pip install alpha-vantage"
                }
            ],
            "recommended": "yfinance"
        },
        "crypto": {
            "providers": [
                {
                    "name": "CCXT",
                    "api": "ccxt",
                    "exchanges": ["Binance", "Coinbase", "Kraken", "100+ more"],
                    "data_types": ["OHLCV", "Order Book", "Trades"],
                    "free": True,
                    "rate_limit": "varies by exchange",
                    "install": "pip install ccxt"
                },
                {
                    "name": "CoinGecko",
                    "api": "pycoingecko",
                    "markets": ["Global"],
                    "data_types": ["Price", "Market Cap", "Volume"],
                    "free": True,
                    "rate_limit": "50 requests/minute",
                    "install": "pip install pycoingecko"
                }
            ],
            "recommended": "ccxt"
        },
        "forex": {
            "providers": [
                {
                    "name": "Alpha Vantage FX",
                    "api": "alpha_vantage",
                    "pairs": ["Major pairs", "Cross pairs"],
                    "data_types": ["OHLCV", "Real-time quotes"],
                    "free": True,
                    "requires_key": True
                }
            ],
            "recommended": "alpha_vantage"
        },
        "macro_data": {
            "providers": [
                {
                    "name": "FRED",
                    "api": "fredapi",
                    "data_types": ["GDP", "Interest Rates", "Unemployment", "CPI"],
                    "free": True,
                    "requires_key": True,
                    "install": "pip install fredapi"
                }
            ],
            "recommended": "fredapi"
        }
    }


def get_ensemble_strategies() -> Dict[str, Any]:
    """
    Get ensemble learning strategies for combining multiple RL agents.
    
    Returns:
        dict: Ensemble methods with implementation details
    
    Example:
        >>> strategies = get_ensemble_strategies()
        >>> print(strategies['majority_voting']['description'])
    """
    return {
        "majority_voting": {
            "name": "Majority Voting Ensemble",
            "description": "Combine predictions from multiple agents using majority vote",
            "use_case": "Discrete action spaces (Buy/Hold/Sell)",
            "agents_required": "3-7 agents trained with different algorithms",
            "advantages": ["Simple", "Robust to individual agent errors"],
            "implementation": {
                "step1": "Train multiple agents (PPO, A2C, SAC, TD3, DDPG)",
                "step2": "Get action predictions from each agent",
                "step3": "Select action with most votes",
                "step4": "Execute winning action"
            }
        },
        "weighted_average": {
            "name": "Weighted Average Ensemble",
            "description": "Weight agent predictions by validation performance",
            "use_case": "Continuous action spaces (Portfolio weights)",
            "agents_required": "3-5 agents",
            "advantages": ["Accounts for agent quality", "Smooth predictions"],
            "implementation": {
                "step1": "Train agents and measure validation Sharpe ratios",
                "step2": "Assign weights proportional to performance",
                "step3": "Weighted average of agent actions",
                "step4": "Normalize and execute"
            },
            "weight_formula": "weight_i = sharpe_i / sum(sharpe_all)"
        },
        "regime_switching": {
            "name": "Market Regime Switching",
            "description": "Use different agents for different market conditions",
            "use_case": "All scenarios, especially volatile markets",
            "agents_required": "3+ agents specialized for different regimes",
            "advantages": ["Adapts to market conditions", "Specialized performance"],
            "regimes": {
                "bull_market": "High returns, low volatility - use aggressive agents",
                "bear_market": "Negative returns - use defensive agents",
                "high_volatility": "Large swings - use conservative agents",
                "sideways": "Range-bound - use mean-reversion agents"
            },
            "detection_methods": ["Moving average crossover", "Volatility thresholds", "Hidden Markov Models"]
        },
        "stacking": {
            "name": "Meta-Learning Stacking",
            "description": "Train a meta-model to combine base agent predictions",
            "use_case": "Complex markets with non-linear relationships",
            "agents_required": "5-10 base agents + 1 meta-learner",
            "advantages": ["Learns optimal combination", "Can capture complex patterns"],
            "implementation": {
                "step1": "Train base RL agents on training set",
                "step2": "Generate predictions on validation set",
                "step3": "Train meta-model (RF/XGBoost) to map predictions to optimal action",
                "step4": "Use meta-model to combine base agent outputs in production"
            }
        }
    }


def get_hyperparameter_search_config() -> Dict[str, Any]:
    """
    Get hyperparameter search configurations for AutoML training.
    
    Returns:
        dict: Search spaces and optimization methods
    
    Example:
        >>> config = get_hyperparameter_search_config()
        >>> print(config['search_methods']['optuna'])
    """
    return {
        "search_methods": {
            "grid_search": {
                "name": "Grid Search",
                "description": "Exhaustive search over parameter grid",
                "pros": ["Complete coverage", "Reproducible"],
                "cons": ["Computationally expensive", "Scales poorly"],
                "use_when": "Small parameter space (<100 combinations)"
            },
            "random_search": {
                "name": "Random Search",
                "description": "Random sampling from parameter distributions",
                "pros": ["Faster than grid", "Good for high dimensions"],
                "cons": ["May miss optimal values"],
                "use_when": "Large parameter space, limited compute",
                "library": "sklearn.model_selection.RandomizedSearchCV"
            },
            "optuna": {
                "name": "Optuna Bayesian Optimization",
                "description": "Smart search using Bayesian optimization",
                "pros": ["Efficient", "Finds good params quickly", "Early stopping"],
                "cons": ["More complex setup"],
                "use_when": "Production systems, limited trials budget",
                "library": "optuna",
                "install": "pip install optuna"
            },
            "hyperopt": {
                "name": "HyperOpt Tree-Parzen Estimator",
                "description": "Bayesian optimization with TPE algorithm",
                "pros": ["Efficient", "Parallelizable"],
                "cons": ["Requires more setup"],
                "library": "hyperopt",
                "install": "pip install hyperopt"
            }
        },
        "search_spaces": {
            "ppo": {
                "learning_rate": {"type": "log_uniform", "range": [1e-5, 1e-2]},
                "n_steps": {"type": "choice", "values": [512, 1024, 2048, 4096]},
                "batch_size": {"type": "choice", "values": [32, 64, 128, 256]},
                "n_epochs": {"type": "int_uniform", "range": [5, 20]},
                "gamma": {"type": "uniform", "range": [0.95, 0.999]},
                "clip_range": {"type": "uniform", "range": [0.1, 0.4]}
            },
            "sac": {
                "learning_rate": {"type": "log_uniform", "range": [1e-5, 1e-2]},
                "buffer_size": {"type": "choice", "values": [100000, 500000, 1000000]},
                "batch_size": {"type": "choice", "values": [64, 128, 256, 512]},
                "tau": {"type": "log_uniform", "range": [0.001, 0.02]},
                "gamma": {"type": "uniform", "range": [0.95, 0.999]}
            },
            "ddpg": {
                "learning_rate": {"type": "log_uniform", "range": [1e-5, 1e-2]},
                "buffer_size": {"type": "choice", "values": [100000, 500000, 1000000]},
                "batch_size": {"type": "choice", "values": [64, 128, 256]},
                "tau": {"type": "log_uniform", "range": [0.001, 0.01]},
                "gamma": {"type": "uniform", "range": [0.95, 0.999]}
            }
        },
        "optimization_objective": {
            "primary": "Sharpe Ratio",
            "alternatives": ["Total Return", "Sortino Ratio", "Max Drawdown", "Calmar Ratio"],
            "multi_objective": ["Maximize Sharpe + Minimize Drawdown", "Maximize Return + Minimize Volatility"]
        }
    }


def get_market_regimes() -> Dict[str, Any]:
    """
    Get market regime detection methods and configurations.
    
    Returns:
        dict: Regime detection algorithms and thresholds
    
    Example:
        >>> regimes = get_market_regimes()
        >>> print(regimes['detection_methods']['hmm'])
    """
    return {
        "detection_methods": {
            "moving_average": {
                "name": "Moving Average Crossover",
                "description": "Detect regimes using SMA crossovers",
                "parameters": {
                    "fast_period": 50,
                    "slow_period": 200
                },
                "regimes": {
                    "bull": "Price > SMA200 AND SMA50 > SMA200",
                    "bear": "Price < SMA200 AND SMA50 < SMA200",
                    "sideways": "Price oscillates around SMA200"
                },
                "complexity": "Low",
                "computational_cost": "Very Low"
            },
            "volatility_based": {
                "name": "Volatility Regime Detection",
                "description": "Classify based on rolling volatility",
                "parameters": {
                    "window": 30,
                    "low_vol_threshold": 0.10,
                    "high_vol_threshold": 0.25
                },
                "regimes": {
                    "low_volatility": "vol < 10% annualized",
                    "medium_volatility": "10% <= vol < 25%",
                    "high_volatility": "vol >= 25%"
                },
                "complexity": "Low",
                "computational_cost": "Low"
            },
            "hmm": {
                "name": "Hidden Markov Model",
                "description": "Statistical model to infer hidden market states",
                "parameters": {
                    "n_states": 3,
                    "features": ["returns", "volatility", "volume"]
                },
                "regimes": {
                    "state_0": "Bull market",
                    "state_1": "Bear market",
                    "state_2": "High volatility / Crisis"
                },
                "complexity": "High",
                "computational_cost": "Medium",
                "library": "hmmlearn",
                "install": "pip install hmmlearn"
            },
            "clustering": {
                "name": "K-Means Clustering",
                "description": "Cluster market conditions using returns and volatility",
                "parameters": {
                    "n_clusters": 4,
                    "features": ["returns_1m", "volatility_1m", "volume_change"]
                },
                "regimes": "Data-driven, discovered automatically",
                "complexity": "Medium",
                "computational_cost": "Low",
                "library": "sklearn.cluster.KMeans"
            }
        },
        "regime_characteristics": {
            "bull_market": {
                "returns": "Positive",
                "volatility": "Low to Medium",
                "volume": "Increasing",
                "sentiment": "Optimistic",
                "recommended_strategy": "Aggressive long positions, momentum trading"
            },
            "bear_market": {
                "returns": "Negative",
                "volatility": "Medium to High",
                "volume": "Declining or spiking",
                "sentiment": "Pessimistic",
                "recommended_strategy": "Short positions, defensive stocks, cash"
            },
            "sideways_market": {
                "returns": "Near zero",
                "volatility": "Low",
                "volume": "Low",
                "sentiment": "Neutral",
                "recommended_strategy": "Mean reversion, range trading"
            },
            "high_volatility": {
                "returns": "Variable",
                "volatility": "High",
                "volume": "High",
                "sentiment": "Fearful",
                "recommended_strategy": "Reduce position sizes, increase cash, options strategies"
            }
        }
    }


def get_training_pipeline() -> Dict[str, Any]:
    """
    Get complete training pipeline for FinRL-Meta agents.
    
    Returns:
        dict: Step-by-step training workflow with code examples
    
    Example:
        >>> pipeline = get_training_pipeline()
        >>> for step in pipeline['steps']:
        ...     print(f"{step['phase']}: {step['description']}")
    """
    return {
        "steps": [
            {
                "phase": "1. Data Collection",
                "description": "Download and prepare market data",
                "code_example": """
from finrl.meta.data_processors.processor_yahoofinance import YahooFinanceProcessor

# Download data
processor = YahooFinanceProcessor()
df = processor.download_data(
    ticker_list=['AAPL', 'MSFT', 'GOOGL'],
    start_date='2020-01-01',
    end_date='2023-12-31',
    time_interval='1D'
)
                """,
                "outputs": ["Raw OHLCV data", "Volume data"],
                "validation": "Check for missing dates, outliers"
            },
            {
                "phase": "2. Feature Engineering",
                "description": "Add technical indicators and features",
                "code_example": """
from finrl.meta.preprocessor.preprocessors import FeatureEngineer

fe = FeatureEngineer(
    use_technical_indicator=True,
    tech_indicator_list=['macd', 'rsi', 'cci', 'dx'],
    use_vix=True,
    use_turbulence=True
)
processed_df = fe.preprocess_data(df)
                """,
                "outputs": ["Technical indicators", "Market regime features"],
                "validation": "Check indicator ranges, no NaN values"
            },
            {
                "phase": "3. Environment Setup",
                "description": "Create trading environment",
                "code_example": """
from finrl.meta.env_stock_trading.env_stocktrading import StockTradingEnv

env = StockTradingEnv(
    df=processed_df,
    stock_dim=len(ticker_list),
    initial_amount=100000,
    transaction_cost_pct=0.001,
    reward_scaling=1e-4,
    state_space=stock_dim * (n_indicators + 3),  # price + indicators
    action_space=stock_dim,
    tech_indicator_list=tech_indicator_list
)
                """,
                "outputs": ["Gym environment", "State/action spaces defined"],
                "validation": "Test environment reset and step functions"
            },
            {
                "phase": "4. Agent Training",
                "description": "Train RL agent with selected algorithm",
                "code_example": """
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv

# Vectorize environment
env_train = DummyVecEnv([lambda: env])

# Train agent
model = PPO(
    "MlpPolicy",
    env_train,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    verbose=1
)
model.learn(total_timesteps=100000)
                """,
                "outputs": ["Trained model weights", "Training logs"],
                "validation": "Monitor training reward, check convergence"
            },
            {
                "phase": "5. Backtesting",
                "description": "Test agent on out-of-sample data",
                "code_example": """
# Create test environment with unseen data
env_test = StockTradingEnv(df=test_df, ...)

# Run backtest
obs = env_test.reset()
for i in range(len(test_df)):
    action, _states = model.predict(obs)
    obs, rewards, done, info = env_test.step(action)
    if done:
        break

# Get results
results = env_test.get_sb_env().env_method('get_performance')
                """,
                "outputs": ["Portfolio value over time", "Trade history", "Performance metrics"],
                "validation": "Sharpe ratio > 1.0, Max drawdown < 20%"
            },
            {
                "phase": "6. Ensemble Creation",
                "description": "Combine multiple agents for robustness",
                "code_example": """
# Train multiple agents
agents = {
    'ppo': PPO(...).learn(100000),
    'sac': SAC(...).learn(100000),
    'td3': TD3(...).learn(100000)
}

# Ensemble prediction (majority voting)
def ensemble_predict(obs):
    actions = [agent.predict(obs)[0] for agent in agents.values()]
    return np.mean(actions, axis=0)  # or use voting for discrete actions
                """,
                "outputs": ["Ensemble model", "Combined predictions"],
                "validation": "Ensemble Sharpe > individual agents"
            }
        ],
        "recommended_timeline": {
            "data_collection": "1-2 hours",
            "feature_engineering": "2-4 hours",
            "environment_setup": "1-2 hours",
            "single_agent_training": "4-12 hours (depends on data size)",
            "ensemble_training": "1-3 days",
            "total": "2-5 days for full pipeline"
        },
        "computational_requirements": {
            "minimum": "CPU: 4 cores, RAM: 8GB, Storage: 10GB",
            "recommended": "CPU: 8+ cores, RAM: 16GB, GPU: NVIDIA 8GB+, Storage: 50GB",
            "cloud_options": ["Google Colab (free GPU)", "AWS EC2 p3.2xlarge", "Paperspace Gradient"]
        }
    }


def get_performance_metrics() -> Dict[str, Any]:
    """
    Get comprehensive performance metrics for evaluating RL trading agents.
    
    Returns:
        dict: Metrics with formulas and interpretation guidelines
    
    Example:
        >>> metrics = get_performance_metrics()
        >>> print(metrics['sharpe_ratio']['formula'])
    """
    return {
        "sharpe_ratio": {
            "name": "Sharpe Ratio",
            "formula": "(mean_return - risk_free_rate) / std_return",
            "interpretation": {
                "> 2.0": "Excellent",
                "1.0 - 2.0": "Good",
                "0.5 - 1.0": "Acceptable",
                "< 0.5": "Poor"
            },
            "use_case": "Overall risk-adjusted performance",
            "pros": ["Widely used", "Easy to understand"],
            "cons": ["Penalizes upside volatility equally"]
        },
        "sortino_ratio": {
            "name": "Sortino Ratio",
            "formula": "(mean_return - risk_free_rate) / downside_deviation",
            "interpretation": {
                "> 2.0": "Excellent",
                "1.0 - 2.0": "Good",
                "< 1.0": "Needs improvement"
            },
            "use_case": "Risk-adjusted return focusing on downside",
            "pros": ["Only penalizes downside volatility"],
            "cons": ["Less common than Sharpe"]
        },
        "max_drawdown": {
            "name": "Maximum Drawdown",
            "formula": "max((peak - trough) / peak)",
            "interpretation": {
                "< 10%": "Excellent",
                "10-20%": "Good",
                "20-30%": "Acceptable",
                "> 30%": "High risk"
            },
            "use_case": "Worst-case loss measurement",
            "pros": ["Shows worst historical loss"],
            "cons": ["Doesn't capture frequency"]
        },
        "calmar_ratio": {
            "name": "Calmar Ratio",
            "formula": "annualized_return / max_drawdown",
            "interpretation": {
                "> 3.0": "Excellent",
                "1.0 - 3.0": "Good",
                "< 1.0": "Poor"
            },
            "use_case": "Return per unit of drawdown risk",
            "pros": ["Combines return and drawdown"],
            "cons": ["Sensitive to observation period"]
        },
        "win_rate": {
            "name": "Win Rate",
            "formula": "winning_trades / total_trades",
            "interpretation": {
                "> 60%": "Excellent",
                "50-60%": "Good",
                "40-50%": "Acceptable (if R > 1)",
                "< 40%": "Poor"
            },
            "use_case": "Trade success frequency",
            "pros": ["Intuitive"],
            "cons": ["Doesn't account for trade size"]
        },
        "profit_factor": {
            "name": "Profit Factor",
            "formula": "gross_profit / gross_loss",
            "interpretation": {
                "> 2.0": "Excellent",
                "1.5 - 2.0": "Good",
                "1.0 - 1.5": "Marginal",
                "< 1.0": "Losing system"
            },
            "use_case": "Profitability measure",
            "pros": ["Shows profit per dollar risked"],
            "cons": ["Can be skewed by outliers"]
        },
        "annualized_return": {
            "name": "Annualized Return",
            "formula": "(final_value / initial_value) ^ (252 / trading_days) - 1",
            "interpretation": {
                "> 20%": "Excellent",
                "10-20%": "Good",
                "5-10%": "Market-like",
                "< 5%": "Below market"
            },
            "use_case": "Standardized return comparison",
            "pros": ["Easy to compare across periods"],
            "cons": ["Doesn't account for risk"]
        },
        "alpha": {
            "name": "Alpha (vs Benchmark)",
            "formula": "portfolio_return - (risk_free_rate + beta * (market_return - risk_free_rate))",
            "interpretation": {
                "> 3%": "Strong outperformance",
                "0-3%": "Mild outperformance",
                "< 0%": "Underperformance"
            },
            "use_case": "Excess return vs market",
            "pros": ["Shows skill vs luck"],
            "cons": ["Requires benchmark selection"]
        },
        "beta": {
            "name": "Beta (Market Correlation)",
            "formula": "covariance(portfolio, market) / variance(market)",
            "interpretation": {
                "> 1.0": "More volatile than market",
                "= 1.0": "Moves with market",
                "< 1.0": "Less volatile than market",
                "< 0": "Inverse correlation"
            },
            "use_case": "Market sensitivity",
            "pros": ["Shows diversification"],
            "cons": ["Assumes linear relationship"]
        }
    }


def get_common_pitfalls() -> Dict[str, Any]:
    """
    Get common pitfalls and debugging tips for FinRL-Meta development.
    
    Returns:
        dict: Pitfalls, symptoms, causes, and solutions
    
    Example:
        >>> pitfalls = get_common_pitfalls()
        >>> print(pitfalls['overfitting']['solutions'])
    """
    return {
        "overfitting": {
            "symptom": "Great backtest, poor live performance",
            "causes": [
                "Too many parameters",
                "Insufficient training data",
                "Look-ahead bias in features",
                "Not enough out-of-sample testing"
            ],
            "solutions": [
                "Use walk-forward validation",
                "Simplify model (fewer features/params)",
                "Add regularization",
                "Test on completely unseen data (different time period)",
                "Cross-validation with time-series splits"
            ],
            "prevention": "Always maintain strict train/validation/test separation"
        },
        "exploding_gradients": {
            "symptom": "Training loss goes to NaN, model diverges",
            "causes": [
                "Learning rate too high",
                "Poor reward scaling",
                "Extreme state values",
                "Unstable environment"
            ],
            "solutions": [
                "Reduce learning rate (try 1e-4 or 1e-5)",
                "Normalize states (StandardScaler)",
                "Scale rewards to [-1, 1]",
                "Gradient clipping (usually automatic in stable-baselines3)",
                "Check for NaN/Inf values in data"
            ]
        },
        "poor_exploration": {
            "symptom": "Agent gets stuck in suboptimal strategy",
            "causes": [
                "Exploration noise too low",
                "Entropy coefficient too small",
                "Deterministic policy too early"
            ],
            "solutions": [
                "Increase entropy coefficient (PPO, A2C)",
                "Add noise to actions (SAC, TD3)",
                "Longer training with epsilon-greedy",
                "Use curiosity-driven exploration"
            ]
        },
        "data_quality_issues": {
            "symptom": "Erratic agent behavior, unexpected trades",
            "causes": [
                "Missing data (NaN values)",
                "Stock splits/dividends not adjusted",
                "Outliers in prices",
                "Misaligned timestamps"
            ],
            "solutions": [
                "Use adjusted close prices",
                "Forward-fill missing values (df.fillna(method='ffill'))",
                "Remove or clip outliers (>5 std from mean)",
                "Validate data quality before training",
                "Use reputable data sources (yfinance auto-adjusts)"
            ]
        },
        "transaction_costs": {
            "symptom": "Backtest profit disappears in live trading",
            "causes": [
                "Not modeling spreads",
                "Ignoring slippage",
                "Too frequent trading",
                "Unrealistic fill assumptions"
            ],
            "solutions": [
                "Add transaction costs to environment (0.1-0.3% per trade)",
                "Model slippage (especially for large orders)",
                "Penalize frequent trading in reward function",
                "Test with conservative cost assumptions"
            ],
            "realistic_costs": {
                "stocks": "0.1-0.5% round-trip",
                "crypto": "0.1-0.3% (market orders)",
                "forex": "2-5 pips spread"
            }
        }
    }


def get_deployment_checklist() -> List[Dict[str, Any]]:
    """
    Get pre-deployment checklist for RL trading agents.
    
    Returns:
        list: Checklist items with validation criteria
    
    Example:
        >>> checklist = get_deployment_checklist()
        >>> for item in checklist:
        ...     print(f"[ ] {item['task']}")
    """
    return [
        {
            "category": "Model Validation",
            "task": "Walk-forward validation completed",
            "criteria": "Tested on at least 3 separate time periods",
            "status": "required"
        },
        {
            "category": "Model Validation",
            "task": "Out-of-sample Sharpe > 1.0",
            "criteria": "Consistent across all test periods",
            "status": "required"
        },
        {
            "category": "Model Validation",
            "task": "Max drawdown < 25%",
            "criteria": "Acceptable risk level for strategy",
            "status": "required"
        },
        {
            "category": "Risk Management",
            "task": "Position sizing rules implemented",
            "criteria": "Max 5% of portfolio per position",
            "status": "required"
        },
        {
            "category": "Risk Management",
            "task": "Stop-loss mechanism active",
            "criteria": "Per-trade and portfolio-level stops",
            "status": "required"
        },
        {
            "category": "Risk Management",
            "task": "Maximum daily loss limit set",
            "criteria": "Kill switch at -5% daily drawdown",
            "status": "required"
        },
        {
            "category": "Data Pipeline",
            "task": "Real-time data feed tested",
            "criteria": "< 1 second latency, 99.9% uptime",
            "status": "required"
        },
        {
            "category": "Data Pipeline",
            "task": "Backup data sources configured",
            "criteria": "Auto-failover to secondary provider",
            "status": "recommended"
        },
        {
            "category": "Execution",
            "task": "Broker API integration tested",
            "criteria": "Paper trading successful for 1 week",
            "status": "required"
        },
        {
            "category": "Execution",
            "task": "Order validation logic implemented",
            "criteria": "Sanity checks on all orders (price, size)",
            "status": "required"
        },
        {
            "category": "Monitoring",
            "task": "Performance dashboard deployed",
            "criteria": "Real-time PnL, positions, metrics",
            "status": "required"
        },
        {
            "category": "Monitoring",
            "task": "Alert system configured",
            "criteria": "Notifications for errors, large losses, anomalies",
            "status": "required"
        },
        {
            "category": "Monitoring",
            "task": "Logging infrastructure ready",
            "criteria": "All trades, decisions, errors logged",
            "status": "required"
        },
        {
            "category": "Disaster Recovery",
            "task": "Emergency shutdown procedure documented",
            "criteria": "Can close all positions in < 5 minutes",
            "status": "required"
        },
        {
            "category": "Disaster Recovery",
            "task": "Model rollback capability tested",
            "criteria": "Can revert to previous model version",
            "status": "recommended"
        },
        {
            "category": "Compliance",
            "task": "Regulatory requirements checked",
            "criteria": "Compliant with local trading laws",
            "status": "required"
        },
        {
            "category": "Capital Allocation",
            "task": "Starting capital determined",
            "criteria": "Start with 10% of intended capital",
            "status": "recommended"
        },
        {
            "category": "Capital Allocation",
            "task": "Scaling plan defined",
            "criteria": "Incremental capital increase based on performance",
            "status": "recommended"
        }
    ]


# Module metadata
__all__ = [
    'check_installation',
    'get_data_sources',
    'get_ensemble_strategies',
    'get_hyperparameter_search_config',
    'get_market_regimes',
    'get_training_pipeline',
    'get_performance_metrics',
    'get_common_pitfalls',
    'get_deployment_checklist'
]

__version__ = '1.0.0'
__author__ = 'QuantClaw Data - NightBuilder #4'
__description__ = 'FinRL-Meta module for deep RL trading with ensemble methods and AutoML'
