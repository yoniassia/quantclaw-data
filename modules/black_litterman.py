"""
Black-Litterman Portfolio Allocation Module

Implements:
1. Reverse optimization to derive equilibrium returns from market cap weights
2. Black-Litterman formula to combine prior (equilibrium) with investor views
3. Posterior expected returns and covariance matrix
4. Mean-variance optimization for portfolio construction

References:
- Black, F. and Litterman, R. (1992) "Global Portfolio Optimization"
- He, G. and Litterman, R. (1999) "The Intuition Behind Black-Litterman Model Portfolios"
"""

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import minimize
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class BlackLittermanModel:
    """Black-Litterman portfolio allocation model"""
    
    def __init__(self, tickers: List[str], risk_free_rate: float = 0.04, tau: float = 0.025):
        """
        Initialize Black-Litterman model
        
        Args:
            tickers: List of stock tickers
            risk_free_rate: Risk-free rate (default 4%)
            tau: Uncertainty scalar (default 0.025 per He & Litterman)
        """
        self.tickers = tickers
        self.risk_free_rate = risk_free_rate
        self.tau = tau
        self.returns = None
        self.cov_matrix = None
        self.market_caps = None
        self.market_weights = None
        
    def fetch_data(self, period: str = "1y") -> None:
        """Fetch historical price data and market caps"""
        print(f"📊 Fetching data for {len(self.tickers)} tickers...")
        
        # Download historical prices
        raw_data = yf.download(self.tickers, period=period, progress=False)
        
        # Handle different return formats
        if raw_data.empty:
            raise ValueError("No data downloaded - check tickers and internet connection")
        
        # yfinance returns MultiIndex columns: (Price, Ticker)
        # We want the 'Close' prices for all tickers
        if isinstance(raw_data.columns, pd.MultiIndex):
            # Try 'Close' first (newer yfinance), fallback to 'Adj Close'
            try:
                data = raw_data['Close']
            except KeyError:
                try:
                    data = raw_data['Adj Close']
                except KeyError:
                    # Fallback: just take first price level
                    data = raw_data.xs(raw_data.columns.levels[0][0], level=0, axis=1)
        else:
            # Single ticker case
            if 'Close' in raw_data.columns:
                data = raw_data[['Close']]
                data.columns = [self.tickers[0]]
            elif 'Adj Close' in raw_data.columns:
                data = raw_data[['Adj Close']]
                data.columns = [self.tickers[0]]
            else:
                data = raw_data
        
        # Calculate daily returns
        self.returns = data.pct_change().dropna()
        
        # Calculate annualized covariance matrix (252 trading days)
        self.cov_matrix = self.returns.cov() * 252
        
        # Fetch current market caps
        market_caps = {}
        for ticker in self.tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                market_cap = info.get('marketCap', 0)
                if market_cap > 0:
                    market_caps[ticker] = market_cap
                else:
                    # Fallback: use shares * current price
                    shares = info.get('sharesOutstanding', 0)
                    price = data[ticker].iloc[-1] if ticker in data.columns else 0
                    market_caps[ticker] = shares * price if shares > 0 else 1e9
            except Exception as e:
                print(f"⚠️  Warning: Could not fetch market cap for {ticker}, using default")
                market_caps[ticker] = 1e9  # Default 1B
        
        self.market_caps = market_caps
        
        # Calculate market cap weights
        total_cap = sum(market_caps.values())
        self.market_weights = np.array([market_caps[t] / total_cap for t in self.tickers])
        
        print(f"✅ Data fetched: {len(self.returns)} days of returns")
        
    def equilibrium_returns(self, delta: float = 2.5) -> np.ndarray:
        """
        Reverse optimization: derive implied equilibrium returns from market weights
        
        Using CAPM formula: π = δ * Σ * w_mkt
        where:
        - π = equilibrium excess returns
        - δ = risk aversion coefficient
        - Σ = covariance matrix
        - w_mkt = market cap weights
        
        Args:
            delta: Risk aversion coefficient (default 2.5)
            
        Returns:
            Equilibrium expected returns (annual)
        """
        if self.cov_matrix is None or self.market_weights is None:
            raise ValueError("Must call fetch_data() first")
        
        # π = δ * Σ * w_mkt
        pi = delta * self.cov_matrix.values @ self.market_weights
        
        return pi
    
    def black_litterman(
        self, 
        views: Dict[str, float],
        view_confidence: float = 0.25,
        delta: float = 2.5
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Combine market equilibrium with investor views using Black-Litterman formula
        
        Args:
            views: Dict mapping ticker -> expected return (e.g., {"AAPL": 0.15, "MSFT": 0.10})
            view_confidence: Confidence in views (0-1). Lower = less confident, higher tau effect
            delta: Risk aversion coefficient
            
        Returns:
            (posterior_returns, posterior_cov): Updated returns and covariance
        """
        if self.cov_matrix is None:
            raise ValueError("Must call fetch_data() first")
        
        # Get equilibrium returns (prior)
        pi = self.equilibrium_returns(delta)
        
        # Build view matrix P and view vector Q
        n_assets = len(self.tickers)
        n_views = len(views)
        
        P = np.zeros((n_views, n_assets))
        Q = np.zeros(n_views)
        
        for i, (ticker, expected_return) in enumerate(views.items()):
            if ticker in self.tickers:
                idx = self.tickers.index(ticker)
                P[i, idx] = 1.0
                Q[i] = expected_return
            else:
                print(f"⚠️  Warning: {ticker} not in portfolio, skipping view")
        
        # Uncertainty in views: Ω = diag(P * τΣ * P')
        # Diagonal assumption per He & Litterman (1999)
        omega = np.diag(np.diag(P @ (self.tau * self.cov_matrix.values) @ P.T)) / view_confidence
        
        # Black-Litterman master formula:
        # E[R] = [(τΣ)^-1 + P'Ω^-1P]^-1 [(τΣ)^-1 π + P'Ω^-1 Q]
        
        tau_cov = self.tau * self.cov_matrix.values
        tau_cov_inv = np.linalg.inv(tau_cov)
        omega_inv = np.linalg.inv(omega)
        
        # Posterior precision matrix
        M_inv = tau_cov_inv + P.T @ omega_inv @ P
        M = np.linalg.inv(M_inv)
        
        # Posterior expected returns (combined prior + views)
        posterior_returns = M @ (tau_cov_inv @ pi + P.T @ omega_inv @ Q)
        
        # Posterior covariance: Σ_post = Σ + M
        posterior_cov = self.cov_matrix.values + M
        
        return posterior_returns, posterior_cov
    
    def optimize_portfolio(
        self, 
        expected_returns: np.ndarray, 
        cov_matrix: np.ndarray,
        target_return: Optional[float] = None,
        allow_short: bool = False
    ) -> Dict[str, float]:
        """
        Mean-variance optimization to find optimal portfolio weights
        
        Args:
            expected_returns: Expected returns vector
            cov_matrix: Covariance matrix
            target_return: Target portfolio return (None = max Sharpe ratio)
            allow_short: Allow short positions (default False)
            
        Returns:
            Dict mapping ticker -> weight
        """
        n = len(self.tickers)
        
        # Objective: minimize portfolio variance
        def portfolio_variance(weights):
            return weights @ cov_matrix @ weights
        
        # Constraints: weights sum to 1
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
        
        # If target return specified, add constraint
        if target_return is not None:
            constraints.append({
                'type': 'eq',
                'fun': lambda w: w @ expected_returns - target_return
            })
        
        # Bounds: 0 <= w <= 1 (long only) or -1 <= w <= 1 (allow short)
        if allow_short:
            bounds = [(-1, 1) for _ in range(n)]
        else:
            bounds = [(0, 1) for _ in range(n)]
        
        # Initial guess: equal weights
        w0 = np.array([1/n] * n)
        
        # Optimize
        result = minimize(
            portfolio_variance,
            w0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )
        
        if not result.success:
            print(f"⚠️  Optimization warning: {result.message}")
        
        # Return as dict
        weights = {ticker: weight for ticker, weight in zip(self.tickers, result.x)}
        return weights
    
    def max_sharpe_portfolio(
        self, 
        expected_returns: np.ndarray, 
        cov_matrix: np.ndarray,
        allow_short: bool = False
    ) -> Dict[str, float]:
        """
        Find portfolio with maximum Sharpe ratio
        
        Args:
            expected_returns: Expected returns vector
            cov_matrix: Covariance matrix
            allow_short: Allow short positions
            
        Returns:
            Dict mapping ticker -> weight
        """
        n = len(self.tickers)
        
        # Objective: maximize Sharpe ratio = (R - Rf) / σ
        # Equivalent to minimizing -Sharpe
        def neg_sharpe(weights):
            ret = weights @ expected_returns
            vol = np.sqrt(weights @ cov_matrix @ weights)
            sharpe = (ret - self.risk_free_rate) / vol if vol > 0 else 0
            return -sharpe
        
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
        
        if allow_short:
            bounds = [(-1, 1) for _ in range(n)]
        else:
            bounds = [(0, 1) for _ in range(n)]
        
        w0 = np.array([1/n] * n)
        
        result = minimize(
            neg_sharpe,
            w0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )
        
        if not result.success:
            print(f"⚠️  Optimization warning: {result.message}")
        
        weights = {ticker: weight for ticker, weight in zip(self.tickers, result.x)}
        return weights


def equilibrium_returns_cli(tickers: List[str], period: str = "1y") -> dict:
    """CLI wrapper for equilibrium returns"""
    model = BlackLittermanModel(tickers)
    model.fetch_data(period)
    
    pi = model.equilibrium_returns()
    
    results = {
        "tickers": tickers,
        "market_weights": {t: float(w) for t, w in zip(tickers, model.market_weights)},
        "equilibrium_returns": {t: float(r) for t, r in zip(tickers, pi)},
        "market_caps": model.market_caps,
    }
    
    return results


def black_litterman_cli(
    tickers: List[str], 
    views: Dict[str, float],
    view_confidence: float = 0.25,
    period: str = "1y"
) -> dict:
    """CLI wrapper for Black-Litterman allocation"""
    model = BlackLittermanModel(tickers)
    model.fetch_data(period)
    
    # Get prior (equilibrium)
    pi = model.equilibrium_returns()
    
    # Get posterior (combined with views)
    posterior_returns, posterior_cov = model.black_litterman(views, view_confidence)
    
    # Optimize portfolio with posterior returns
    optimal_weights = model.max_sharpe_portfolio(posterior_returns, posterior_cov)
    
    # Calculate portfolio metrics
    portfolio_return = sum(optimal_weights[t] * posterior_returns[i] 
                          for i, t in enumerate(tickers))
    portfolio_vol = np.sqrt(
        sum(optimal_weights[t1] * optimal_weights[t2] * posterior_cov[i, j]
            for i, t1 in enumerate(tickers)
            for j, t2 in enumerate(tickers))
    )
    sharpe = (portfolio_return - model.risk_free_rate) / portfolio_vol if portfolio_vol > 0 else 0
    
    results = {
        "tickers": tickers,
        "views": views,
        "view_confidence": view_confidence,
        "market_weights": {t: float(w) for t, w in zip(tickers, model.market_weights)},
        "equilibrium_returns": {t: float(r) for t, r in zip(tickers, pi)},
        "posterior_returns": {t: float(r) for t, r in zip(tickers, posterior_returns)},
        "optimal_weights": {t: float(w) for t, w in optimal_weights.items()},
        "portfolio_metrics": {
            "expected_return": float(portfolio_return),
            "volatility": float(portfolio_vol),
            "sharpe_ratio": float(sharpe),
            "risk_free_rate": model.risk_free_rate
        }
    }
    
    return results


def portfolio_optimize_cli(
    tickers: List[str],
    target_return: Optional[float] = None,
    allow_short: bool = False,
    period: str = "1y"
) -> dict:
    """CLI wrapper for portfolio optimization (max Sharpe)"""
    model = BlackLittermanModel(tickers)
    model.fetch_data(period)
    
    # Use equilibrium returns as baseline
    expected_returns = model.equilibrium_returns()
    
    if target_return is not None:
        weights = model.optimize_portfolio(
            expected_returns, 
            model.cov_matrix.values,
            target_return=target_return,
            allow_short=allow_short
        )
    else:
        weights = model.max_sharpe_portfolio(
            expected_returns,
            model.cov_matrix.values,
            allow_short=allow_short
        )
    
    # Calculate metrics
    portfolio_return = sum(weights[t] * expected_returns[i] for i, t in enumerate(tickers))
    portfolio_vol = np.sqrt(
        sum(weights[t1] * weights[t2] * model.cov_matrix.values[i, j]
            for i, t1 in enumerate(tickers)
            for j, t2 in enumerate(tickers))
    )
    sharpe = (portfolio_return - model.risk_free_rate) / portfolio_vol if portfolio_vol > 0 else 0
    
    results = {
        "tickers": tickers,
        "weights": {t: float(w) for t, w in weights.items()},
        "expected_returns": {t: float(r) for t, r in zip(tickers, expected_returns)},
        "portfolio_metrics": {
            "expected_return": float(portfolio_return),
            "volatility": float(portfolio_vol),
            "sharpe_ratio": float(sharpe),
            "target_return": target_return,
            "allow_short": allow_short
        }
    }
    
    return results


if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Black-Litterman Portfolio Allocation")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # black-litterman command
    bl_parser = subparsers.add_parser('black-litterman', help='Black-Litterman allocation with investor views')
    bl_parser.add_argument('--tickers', type=str, required=True, help='Comma-separated tickers')
    bl_parser.add_argument('--views', type=str, help='Views as TICKER:RETURN,... (e.g., AAPL:0.15,MSFT:0.10)')
    bl_parser.add_argument('--confidence', type=float, default=0.25, help='View confidence (0-1)')
    bl_parser.add_argument('--period', type=str, default='1y', help='Data period (e.g., 1y, 6mo, 2y)')
    
    # equilibrium-returns command
    eq_parser = subparsers.add_parser('equilibrium-returns', help='Calculate market equilibrium returns')
    eq_parser.add_argument('--tickers', type=str, required=True, help='Comma-separated tickers')
    eq_parser.add_argument('--period', type=str, default='1y', help='Data period')
    
    # portfolio-optimize command
    opt_parser = subparsers.add_parser('portfolio-optimize', help='Mean-variance optimization')
    opt_parser.add_argument('--tickers', type=str, required=True, help='Comma-separated tickers')
    opt_parser.add_argument('--target-return', type=float, help='Target portfolio return (annual)')
    opt_parser.add_argument('--allow-short', action='store_true', help='Allow short positions')
    opt_parser.add_argument('--period', type=str, default='1y', help='Data period')
    
    args = parser.parse_args()
    
    if args.command == 'black-litterman':
        tickers = [t.strip().upper() for t in args.tickers.split(',')]
        
        # Parse views
        views = {}
        if args.views:
            for view in args.views.split(','):
                ticker, ret = view.split(':')
                views[ticker.strip().upper()] = float(ret.strip())
        
        result = black_litterman_cli(tickers, views, args.confidence, args.period)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'equilibrium-returns':
        tickers = [t.strip().upper() for t in args.tickers.split(',')]
        result = equilibrium_returns_cli(tickers, args.period)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'portfolio-optimize':
        tickers = [t.strip().upper() for t in args.tickers.split(',')]
        result = portfolio_optimize_cli(
            tickers, 
            target_return=args.target_return,
            allow_short=args.allow_short,
            period=args.period
        )
        print(json.dumps(result, indent=2))
    
    else:
        # Quick test mode
        print("🧪 Running test mode...")
        tickers = ["AAPL", "MSFT", "GOOGL"]
        model = BlackLittermanModel(tickers)
        model.fetch_data()
        
        print("\n📊 Market Weights:")
        for t, w in zip(tickers, model.market_weights):
            print(f"  {t}: {w:.2%}")
        
        print("\n📈 Equilibrium Returns:")
        pi = model.equilibrium_returns()
        for t, r in zip(tickers, pi):
            print(f"  {t}: {r:.2%}")
        
        # Test with views
        views = {"AAPL": 0.20, "GOOGL": 0.12}
        print(f"\n🎯 Investor Views: {views}")
        
        posterior_returns, posterior_cov = model.black_litterman(views)
        
        print("\n📊 Posterior Returns (After Views):")
        for t, r in zip(tickers, posterior_returns):
            print(f"  {t}: {r:.2%}")
        
        weights = model.max_sharpe_portfolio(posterior_returns, posterior_cov)
        print("\n💼 Optimal Portfolio Weights:")
        for t, w in weights.items():
            print(f"  {t}: {w:.2%}")
