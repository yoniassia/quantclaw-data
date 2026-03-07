#!/usr/bin/env python3
"""
FinRL Library — Financial Reinforcement Learning Framework

Open-source framework for financial reinforcement learning, providing tools to 
build and train ML models for trading strategies. Includes pre-built environments 
for stock trading, portfolio allocation, and risk management using deep RL algorithms.

Installation:
    pip install finrl
    
Optional dependencies:
    pip install yfinance pandas numpy

This module works with or without FinRL installed, providing fallback utilities.

Source: https://github.com/AI4Finance-Foundation/FinRL
Category: Quant Tools & ML
Free tier: True
Update frequency: as-needed (repository updates quarterly)
Author: QuantClaw Data NightBuilder
Phase: 106
"""

import json
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Try to import finrl - gracefully handle if not installed
try:
    import finrl
    FINRL_AVAILABLE = True
except ImportError:
    FINRL_AVAILABLE = False
    warnings.warn("FinRL not installed. Install with: pip install finrl")

# Try to import yfinance for data download fallback
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# Try to import pandas
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# ========== FINRL CONFIGURATION ==========

# Supported RL algorithms in FinRL
FINRL_ALGORITHMS = {
    'a2c': {
        'name': 'Advantage Actor-Critic (A2C)',
        'type': 'on-policy',
        'framework': 'stable-baselines3',
        'description': 'Actor-critic method that reduces variance using advantage function'
    },
    'ppo': {
        'name': 'Proximal Policy Optimization (PPO)',
        'type': 'on-policy',
        'framework': 'stable-baselines3',
        'description': 'Trust region method with clipped objective for stable training'
    },
    'ddpg': {
        'name': 'Deep Deterministic Policy Gradient (DDPG)',
        'type': 'off-policy',
        'framework': 'stable-baselines3',
        'description': 'Actor-critic for continuous action spaces with replay buffer'
    },
    'td3': {
        'name': 'Twin Delayed DDPG (TD3)',
        'type': 'off-policy',
        'framework': 'stable-baselines3',
        'description': 'Improved DDPG with twin critics and delayed policy updates'
    },
    'sac': {
        'name': 'Soft Actor-Critic (SAC)',
        'type': 'off-policy',
        'framework': 'stable-baselines3',
        'description': 'Maximum entropy RL with automatic temperature tuning'
    },
    'dqn': {
        'name': 'Deep Q-Network (DQN)',
        'type': 'off-policy',
        'framework': 'stable-baselines3',
        'description': 'Value-based method using experience replay and target network'
    }
}

# Supported trading environments
FINRL_ENVIRONMENTS = {
    'single_stock': {
        'name': 'Single Stock Trading',
        'description': 'Trade a single stock with buy/sell/hold actions',
        'action_space': 'discrete or continuous',
        'state_space': 'OHLCV + technical indicators'
    },
    'multiple_stock': {
        'name': 'Multiple Stock Trading',
        'description': 'Trade multiple stocks with portfolio allocation',
        'action_space': 'continuous (allocation weights)',
        'state_space': 'OHLCV + technical indicators per stock'
    },
    'portfolio_allocation': {
        'name': 'Portfolio Allocation',
        'description': 'Optimize portfolio weights across assets',
        'action_space': 'continuous (weights)',
        'state_space': 'Returns, volatility, correlations'
    },
    'crypto_trading': {
        'name': 'Cryptocurrency Trading',
        'description': 'Trade cryptocurrencies 24/7',
        'action_space': 'discrete or continuous',
        'state_space': 'OHLCV + on-chain metrics'
    }
}


def get_supported_environments() -> Dict[str, Any]:
    """
    Get list of supported trading environments in FinRL.
    
    Returns:
        Dict with environment details and availability status
    """
    try:
        return {
            'success': True,
            'finrl_available': FINRL_AVAILABLE,
            'environments': FINRL_ENVIRONMENTS,
            'count': len(FINRL_ENVIRONMENTS),
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


def list_available_algorithms() -> Dict[str, Any]:
    """
    List available RL algorithms supported by FinRL.
    
    Returns:
        Dict with algorithm details and framework info
    """
    try:
        return {
            'success': True,
            'finrl_available': FINRL_AVAILABLE,
            'algorithms': FINRL_ALGORITHMS,
            'count': len(FINRL_ALGORITHMS),
            'frameworks': ['stable-baselines3'],
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


def get_sample_config(algorithm: str = 'ppo') -> Dict[str, Any]:
    """
    Get sample configuration for a specific RL algorithm.
    
    Args:
        algorithm: Algorithm name (ppo, a2c, ddpg, td3, sac, dqn)
        
    Returns:
        Dict with sample hyperparameters and training config
    """
    try:
        if algorithm.lower() not in FINRL_ALGORITHMS:
            return {
                'success': False,
                'error': f'Unknown algorithm: {algorithm}. Available: {list(FINRL_ALGORITHMS.keys())}',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Sample configurations for each algorithm
        configs = {
            'ppo': {
                'learning_rate': 0.0003,
                'n_steps': 2048,
                'batch_size': 64,
                'n_epochs': 10,
                'gamma': 0.99,
                'gae_lambda': 0.95,
                'clip_range': 0.2,
                'ent_coef': 0.01
            },
            'a2c': {
                'learning_rate': 0.0007,
                'n_steps': 5,
                'gamma': 0.99,
                'gae_lambda': 1.0,
                'ent_coef': 0.01,
                'vf_coef': 0.5
            },
            'ddpg': {
                'learning_rate': 0.001,
                'buffer_size': 1000000,
                'learning_starts': 100,
                'batch_size': 100,
                'tau': 0.005,
                'gamma': 0.99
            },
            'td3': {
                'learning_rate': 0.001,
                'buffer_size': 1000000,
                'learning_starts': 100,
                'batch_size': 100,
                'tau': 0.005,
                'gamma': 0.99,
                'policy_delay': 2
            },
            'sac': {
                'learning_rate': 0.0003,
                'buffer_size': 1000000,
                'learning_starts': 100,
                'batch_size': 256,
                'tau': 0.005,
                'gamma': 0.99,
                'ent_coef': 'auto'
            },
            'dqn': {
                'learning_rate': 0.0001,
                'buffer_size': 1000000,
                'learning_starts': 50000,
                'batch_size': 32,
                'tau': 1.0,
                'gamma': 0.99,
                'exploration_fraction': 0.1
            }
        }
        
        return {
            'success': True,
            'algorithm': algorithm.lower(),
            'algorithm_info': FINRL_ALGORITHMS[algorithm.lower()],
            'config': configs[algorithm.lower()],
            'training_steps': 100000,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


def download_training_data(
    tickers: List[str],
    start_date: str,
    end_date: str,
    interval: str = '1d'
) -> Dict[str, Any]:
    """
    Download training data for RL models using yfinance.
    Works without FinRL installed.
    
    Args:
        tickers: List of stock tickers (e.g., ['AAPL', 'MSFT'])
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        interval: Data interval (1d, 1h, etc.)
        
    Returns:
        Dict with downloaded data and metadata
    """
    try:
        if not YFINANCE_AVAILABLE:
            return {
                'success': False,
                'error': 'yfinance not installed. Install with: pip install yfinance',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        if not PANDAS_AVAILABLE:
            return {
                'success': False,
                'error': 'pandas not installed. Install with: pip install pandas',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Download data for each ticker
        data_dict = {}
        failed_tickers = []
        
        for ticker in tickers:
            try:
                df = yf.download(
                    ticker,
                    start=start_date,
                    end=end_date,
                    interval=interval,
                    progress=False
                )
                
                if not df.empty:
                    data_dict[ticker] = {
                        'rows': len(df),
                        'columns': list(df.columns),
                        'start_date': df.index[0].strftime('%Y-%m-%d'),
                        'end_date': df.index[-1].strftime('%Y-%m-%d'),
                        'sample': df.tail(3).to_dict()
                    }
                else:
                    failed_tickers.append(ticker)
            except Exception as e:
                failed_tickers.append(f"{ticker} ({str(e)})")
        
        return {
            'success': True,
            'tickers_requested': tickers,
            'tickers_downloaded': list(data_dict.keys()),
            'failed_tickers': failed_tickers,
            'data': data_dict,
            'period': {'start': start_date, 'end': end_date},
            'interval': interval,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


def create_stock_trading_env(
    ticker_list: List[str],
    start_date: str,
    end_date: str,
    initial_amount: float = 100000.0
) -> Dict[str, Any]:
    """
    Create a stock trading environment configuration.
    Returns config dict that can be used to initialize FinRL environment.
    
    Args:
        ticker_list: List of stock tickers
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        initial_amount: Initial portfolio value
        
    Returns:
        Dict with environment configuration
    """
    try:
        # Download data to validate tickers
        data_result = download_training_data(ticker_list, start_date, end_date)
        
        if not data_result['success']:
            return data_result
        
        env_config = {
            'ticker_list': ticker_list,
            'start_date': start_date,
            'end_date': end_date,
            'initial_amount': initial_amount,
            'transaction_cost_pct': 0.001,  # 0.1% transaction cost
            'tech_indicator_list': [
                'macd', 'rsi_30', 'cci_30', 'dx_30',
                'close_30_sma', 'close_60_sma'
            ],
            'state_space': len(ticker_list) * (6 + len(['macd', 'rsi_30', 'cci_30', 'dx_30', 'close_30_sma', 'close_60_sma'])),
            'action_space': len(ticker_list),
            'reward_scaling': 1e-4
        }
        
        return {
            'success': True,
            'finrl_available': FINRL_AVAILABLE,
            'env_config': env_config,
            'data_validation': {
                'tickers_available': data_result['tickers_downloaded'],
                'data_points': {k: v['rows'] for k, v in data_result['data'].items()}
            },
            'usage': 'Use this config to initialize FinRL StockTradingEnv' if FINRL_AVAILABLE else 'Install FinRL to use this config',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


def backtest_strategy(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Backtest a trained RL strategy (placeholder - requires trained model).
    
    Args:
        config: Backtest configuration with model path, data, etc.
        
    Returns:
        Dict with backtest results
    """
    try:
        if not FINRL_AVAILABLE:
            return {
                'success': False,
                'error': 'FinRL not installed. Install with: pip install finrl',
                'note': 'This function requires FinRL to run backtests',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Placeholder for actual backtesting logic
        return {
            'success': False,
            'error': 'Backtest requires trained model - use FinRL training pipeline first',
            'required_config': {
                'model_path': 'path/to/trained/model.zip',
                'test_data': 'path/to/test/data.csv',
                'initial_amount': 100000,
                'transaction_cost_pct': 0.001
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


def describe_module() -> Dict[str, Any]:
    """
    Get module metadata and capabilities.
    
    Returns:
        Dict with module description and status
    """
    try:
        return {
            'success': True,
            'module': 'finrl_library',
            'description': 'Financial Reinforcement Learning framework wrapper',
            'source': 'https://github.com/AI4Finance-Foundation/FinRL',
            'category': 'Quant Tools & ML',
            'installation': {
                'finrl': FINRL_AVAILABLE,
                'yfinance': YFINANCE_AVAILABLE,
                'pandas': PANDAS_AVAILABLE,
                'install_command': 'pip install finrl yfinance pandas'
            },
            'capabilities': {
                'environments': len(FINRL_ENVIRONMENTS),
                'algorithms': len(FINRL_ALGORITHMS),
                'data_download': YFINANCE_AVAILABLE,
                'backtesting': FINRL_AVAILABLE
            },
            'functions': [
                'get_supported_environments()',
                'list_available_algorithms()',
                'get_sample_config(algorithm)',
                'download_training_data(tickers, start, end)',
                'create_stock_trading_env(tickers, start, end)',
                'backtest_strategy(config)',
                'describe_module()'
            ],
            'free_tier': True,
            'api_keys_required': False,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


# Main execution for testing
if __name__ == "__main__":
    print(json.dumps(describe_module(), indent=2))
