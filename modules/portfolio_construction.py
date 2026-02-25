#!/usr/bin/env python3
"""
Portfolio Construction Module - Phase 81

Implements:
1. Modern Portfolio Theory (Markowitz mean-variance optimization)
2. Black-Litterman with investor views
3. ESG-constrained optimization
4. Tax-aware rebalancing with wash sale awareness
5. Risk decomposition and efficient frontier visualization

APIs:
- Yahoo Finance: price data, fundamentals
- FRED API: risk-free rate (10Y Treasury)
"""

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import minimize, NonlinearConstraint
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
import sys
import json
import requests

warnings.filterwarnings('ignore')


class PortfolioOptimizer:
    """Modern Portfolio Theory optimizer with ESG and tax constraints"""
    
    def __init__(self, tickers: List[str], risk_free_rate: Optional[float] = None):
        """
        Initialize Portfolio Optimizer
        
        Args:
            tickers: List of stock tickers
            risk_free_rate: Risk-free rate (fetched from FRED if None)
        """
        self.tickers = tickers
        self.risk_free_rate = risk_free_rate or self._fetch_risk_free_rate()
        self.returns = None
        self.mean_returns = None
        self.cov_matrix = None
        self.prices = None
        self.esg_scores = {}
        
    def _fetch_risk_free_rate(self) -> float:
        """Fetch 10-Year Treasury rate from FRED API"""
        try:
            # FRED API endpoint for 10-Year Treasury Constant Maturity Rate (DGS10)
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': 'DGS10',
                'api_key': 'your_fred_api_key_here',  # Free API key from fred.stlouisfed.org
                'file_type': 'json',
                'sort_order': 'desc',
                'limit': 1
            }
            
            # Try without API key first (some endpoints work)
            url_no_key = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10"
            response = requests.get(url_no_key, timeout=5)
            
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                if len(lines) > 1:
                    last_line = lines[-1].split(',')
                    if len(last_line) > 1 and last_line[1] not in ['', '.']:
                        rate = float(last_line[1]) / 100  # Convert percentage to decimal
                        print(f"📊 Risk-free rate (10Y Treasury): {rate*100:.2f}%")
                        return rate
        except Exception as e:
            print(f"⚠️  Could not fetch risk-free rate from FRED: {e}")
        
        # Fallback to default 4%
        print("📊 Using default risk-free rate: 4.00%")
        return 0.04
    
    def fetch_data(self, period: str = "2y") -> None:
        """Fetch historical price data"""
        print(f"📊 Fetching {period} of data for {len(self.tickers)} tickers...")
        
        # Download historical prices
        raw_data = yf.download(self.tickers, period=period, progress=False)
        
        if raw_data.empty:
            raise ValueError("No data downloaded - check tickers")
        
        # Extract closing prices
        if isinstance(raw_data.columns, pd.MultiIndex):
            try:
                data = raw_data['Close']
            except KeyError:
                data = raw_data['Adj Close']
        else:
            if 'Close' in raw_data.columns:
                data = raw_data[['Close']]
                data.columns = [self.tickers[0]]
            else:
                data = raw_data
        
        self.prices = data
        self.returns = data.pct_change().dropna()
        self.mean_returns = self.returns.mean() * 252  # Annualized
        self.cov_matrix = self.returns.cov() * 252  # Annualized
        
        print(f"✅ Data loaded: {len(self.returns)} days")
    
    def _fetch_esg_scores(self) -> Dict[str, float]:
        """
        Fetch ESG scores from Yahoo Finance
        Returns normalized scores (0-100)
        """
        print("🌱 Fetching ESG scores...")
        
        for ticker in self.tickers:
            try:
                stock = yf.Ticker(ticker)
                esg_data = stock.sustainability
                
                if esg_data is not None and not esg_data.empty:
                    # Get total ESG score (ranges 0-100 typically)
                    total_score = esg_data.loc['totalEsg', 'Value'] if 'totalEsg' in esg_data.index else 50
                    self.esg_scores[ticker] = float(total_score)
                else:
                    # Default neutral score if no data
                    self.esg_scores[ticker] = 50.0
                    print(f"  ⚠️  No ESG data for {ticker}, using default 50")
            except Exception as e:
                print(f"  ⚠️  Error fetching ESG for {ticker}: {e}")
                self.esg_scores[ticker] = 50.0
        
        print(f"✅ ESG scores: {self.esg_scores}")
        return self.esg_scores
    
    def optimize_portfolio(
        self,
        target_return: Optional[float] = None,
        target_risk: Optional[float] = None,
        esg_min_score: Optional[float] = None,
        constraints: Optional[List] = None
    ) -> Dict:
        """
        Mean-variance portfolio optimization (Markowitz)
        
        Args:
            target_return: Target annual return (e.g., 0.15 for 15%)
            target_risk: Target annual volatility (e.g., 0.20 for 20%)
            esg_min_score: Minimum weighted ESG score (0-100)
            constraints: Additional constraints
        
        Returns:
            dict with weights, return, risk, sharpe
        """
        n = len(self.tickers)
        
        # Initial guess: equal weights
        x0 = np.ones(n) / n
        
        # Bounds: each weight between 0 and 1 (long-only)
        bounds = tuple((0, 1) for _ in range(n))
        
        # Constraints
        cons = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]  # Weights sum to 1
        
        if target_return is not None:
            cons.append({
                'type': 'eq',
                'fun': lambda x: self._portfolio_return(x) - target_return
            })
        
        if target_risk is not None:
            cons.append({
                'type': 'eq',
                'fun': lambda x: self._portfolio_volatility(x) - target_risk
            })
        
        # ESG constraint
        if esg_min_score is not None:
            if not self.esg_scores:
                self._fetch_esg_scores()
            
            esg_array = np.array([self.esg_scores.get(t, 50) for t in self.tickers])
            cons.append({
                'type': 'ineq',
                'fun': lambda x: np.dot(x, esg_array) - esg_min_score
            })
        
        if constraints:
            cons.extend(constraints)
        
        # Objective: minimize risk for given return (or maximize Sharpe if no target)
        if target_return is not None or target_risk is not None:
            objective = lambda x: self._portfolio_volatility(x)
        else:
            objective = lambda x: -self._sharpe_ratio(x)
        
        # Optimize
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=cons,
            options={'maxiter': 1000}
        )
        
        if not result.success:
            print(f"⚠️  Optimization warning: {result.message}")
        
        weights = result.x
        port_return = self._portfolio_return(weights)
        port_risk = self._portfolio_volatility(weights)
        sharpe = (port_return - self.risk_free_rate) / port_risk
        
        # Build result
        portfolio = {
            'weights': {ticker: float(w) for ticker, w in zip(self.tickers, weights)},
            'expected_return': float(port_return),
            'volatility': float(port_risk),
            'sharpe_ratio': float(sharpe),
            'risk_free_rate': float(self.risk_free_rate)
        }
        
        if esg_min_score is not None:
            esg_array = np.array([self.esg_scores.get(t, 50) for t in self.tickers])
            portfolio['esg_score'] = float(np.dot(weights, esg_array))
        
        return portfolio
    
    def efficient_frontier(self, n_portfolios: int = 50, esg_min_score: Optional[float] = None) -> pd.DataFrame:
        """
        Generate efficient frontier portfolios
        
        Args:
            n_portfolios: Number of portfolios to generate
            esg_min_score: Optional minimum ESG score constraint
        
        Returns:
            DataFrame with returns, risks, Sharpe ratios, and weights
        """
        print(f"📈 Generating efficient frontier ({n_portfolios} portfolios)...")
        
        # Range of target returns
        min_ret = self.mean_returns.min()
        max_ret = self.mean_returns.max()
        target_returns = np.linspace(min_ret, max_ret, n_portfolios)
        
        results = []
        
        for target_return in target_returns:
            try:
                portfolio = self.optimize_portfolio(
                    target_return=target_return,
                    esg_min_score=esg_min_score
                )
                
                results.append({
                    'return': portfolio['expected_return'],
                    'volatility': portfolio['volatility'],
                    'sharpe_ratio': portfolio['sharpe_ratio'],
                    **portfolio['weights']
                })
            except Exception as e:
                # Skip infeasible portfolios
                continue
        
        df = pd.DataFrame(results)
        print(f"✅ Generated {len(df)} efficient portfolios")
        return df
    
    def portfolio_risk_decomposition(self, weights: Dict[str, float]) -> Dict:
        """
        Decompose portfolio risk into individual asset contributions
        
        Args:
            weights: Dictionary of {ticker: weight}
        
        Returns:
            Risk contribution analysis
        """
        w = np.array([weights.get(t, 0) for t in self.tickers])
        
        # Portfolio variance
        port_var = np.dot(w, np.dot(self.cov_matrix, w))
        port_vol = np.sqrt(port_var)
        
        # Marginal contribution to risk (MCR)
        mcr = np.dot(self.cov_matrix, w) / port_vol
        
        # Component contribution to risk (CCR)
        ccr = w * mcr
        
        # Percentage contribution
        pct_contribution = ccr / port_vol
        
        return {
            'portfolio_volatility': float(port_vol),
            'marginal_risk': {ticker: float(mcr[i]) for i, ticker in enumerate(self.tickers)},
            'risk_contribution': {ticker: float(ccr[i]) for i, ticker in enumerate(self.tickers)},
            'risk_contribution_pct': {ticker: float(pct_contribution[i]) for i, ticker in enumerate(self.tickers)}
        }
    
    def _portfolio_return(self, weights: np.ndarray) -> float:
        """Calculate portfolio expected return"""
        return np.dot(weights, self.mean_returns)
    
    def _portfolio_volatility(self, weights: np.ndarray) -> float:
        """Calculate portfolio volatility (standard deviation)"""
        return np.sqrt(np.dot(weights, np.dot(self.cov_matrix, weights)))
    
    def _sharpe_ratio(self, weights: np.ndarray) -> float:
        """Calculate Sharpe ratio"""
        ret = self._portfolio_return(weights)
        vol = self._portfolio_volatility(weights)
        return (ret - self.risk_free_rate) / vol


class TaxAwareRebalancer:
    """Tax-aware portfolio rebalancing with wash sale rules"""
    
    WASH_SALE_DAYS = 30  # IRS wash sale rule: 30 days before/after
    
    def __init__(self, current_holdings: Dict[str, Dict], target_weights: Dict[str, float]):
        """
        Initialize tax-aware rebalancer
        
        Args:
            current_holdings: {ticker: {'shares': N, 'cost_basis': price, 'purchase_date': 'YYYY-MM-DD'}}
            target_weights: {ticker: weight} (must sum to 1.0)
        """
        self.current_holdings = current_holdings
        self.target_weights = target_weights
        self.tax_rate_short = 0.37  # Short-term cap gains (< 1 year)
        self.tax_rate_long = 0.20   # Long-term cap gains (>= 1 year)
        
    def generate_rebalance_plan(self, total_portfolio_value: float) -> Dict:
        """
        Generate tax-efficient rebalancing plan
        
        Args:
            total_portfolio_value: Total portfolio value in dollars
        
        Returns:
            Rebalancing plan with trades and tax implications
        """
        print("💰 Generating tax-aware rebalancing plan...")
        
        # Fetch current prices
        tickers = list(set(list(self.current_holdings.keys()) + list(self.target_weights.keys())))
        prices = self._fetch_current_prices(tickers)
        
        # Calculate current allocation
        current_values = {}
        current_weights = {}
        
        for ticker, holding in self.current_holdings.items():
            shares = holding['shares']
            current_price = prices.get(ticker, 0)
            current_values[ticker] = shares * current_price
            current_weights[ticker] = current_values[ticker] / total_portfolio_value
        
        # Calculate target allocation
        target_values = {ticker: weight * total_portfolio_value for ticker, weight in self.target_weights.items()}
        
        # Generate trades
        trades = []
        total_tax_liability = 0
        
        for ticker in tickers:
            current_value = current_values.get(ticker, 0)
            target_value = target_values.get(ticker, 0)
            delta_value = target_value - current_value
            
            if abs(delta_value) < 0.01:  # Skip tiny trades
                continue
            
            current_price = prices.get(ticker, 0)
            if current_price == 0:
                continue
            
            delta_shares = delta_value / current_price
            
            # For sells, calculate tax implications
            tax_impact = 0
            wash_sale_risk = False
            
            if delta_shares < 0 and ticker in self.current_holdings:
                # Selling shares
                holding = self.current_holdings[ticker]
                cost_basis = holding['cost_basis']
                gain_per_share = current_price - cost_basis
                
                purchase_date = datetime.strptime(holding['purchase_date'], '%Y-%m-%d')
                holding_period = (datetime.now() - purchase_date).days
                
                # Determine tax rate
                if holding_period < 365:
                    tax_rate = self.tax_rate_short
                    holding_type = "short-term"
                else:
                    tax_rate = self.tax_rate_long
                    holding_type = "long-term"
                
                # Calculate tax
                total_gain = gain_per_share * abs(delta_shares)
                tax_impact = total_gain * tax_rate if total_gain > 0 else 0
                total_tax_liability += tax_impact
                
                # Check wash sale risk (if loss and planning to rebuy)
                if gain_per_share < 0 and ticker in self.target_weights and self.target_weights[ticker] > 0:
                    wash_sale_risk = True
            
            trades.append({
                'ticker': ticker,
                'action': 'BUY' if delta_shares > 0 else 'SELL',
                'shares': abs(delta_shares),
                'current_price': current_price,
                'trade_value': abs(delta_value),
                'tax_impact': tax_impact,
                'holding_type': holding_type if delta_shares < 0 and ticker in self.current_holdings else None,
                'wash_sale_risk': wash_sale_risk
            })
        
        # Sort by tax efficiency (harvest losses first, then low-tax-impact changes)
        trades.sort(key=lambda x: (x['tax_impact'], -x['trade_value']))
        
        return {
            'trades': trades,
            'total_tax_liability': total_tax_liability,
            'net_rebalancing_cost': total_tax_liability,
            'current_allocation': {k: f"{v*100:.2f}%" for k, v in current_weights.items()},
            'target_allocation': {k: f"{v*100:.2f}%" for k, v in self.target_weights.items()}
        }
    
    def check_wash_sale(self, ticker: str, sale_date: str) -> Dict:
        """
        Check if a sale would trigger IRS wash sale rule
        
        Args:
            ticker: Stock ticker
            sale_date: Sale date in 'YYYY-MM-DD' format
        
        Returns:
            Wash sale risk analysis
        """
        sale_dt = datetime.strptime(sale_date, '%Y-%m-%d')
        window_start = sale_dt - timedelta(days=self.WASH_SALE_DAYS)
        window_end = sale_dt + timedelta(days=self.WASH_SALE_DAYS)
        
        # Check if we have holdings in the 30-day window
        if ticker in self.current_holdings:
            holding = self.current_holdings[ticker]
            purchase_dt = datetime.strptime(holding['purchase_date'], '%Y-%m-%d')
            
            in_window = window_start <= purchase_dt <= window_end
            
            return {
                'ticker': ticker,
                'sale_date': sale_date,
                'wash_sale_risk': in_window,
                'wash_sale_window': f"{window_start.strftime('%Y-%m-%d')} to {window_end.strftime('%Y-%m-%d')}",
                'purchase_date': holding['purchase_date'],
                'recommendation': 'WAIT' if in_window else 'SAFE TO SELL'
            }
        
        return {
            'ticker': ticker,
            'wash_sale_risk': False,
            'recommendation': 'SAFE TO SELL (no current holdings)'
        }
    
    def _fetch_current_prices(self, tickers: List[str]) -> Dict[str, float]:
        """Fetch current prices for tickers"""
        prices = {}
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period='1d')
                if not hist.empty:
                    prices[ticker] = hist['Close'].iloc[-1]
            except Exception as e:
                print(f"⚠️  Error fetching price for {ticker}: {e}")
                prices[ticker] = 0
        return prices


class BlackLittermanOptimizer:
    """Black-Litterman model with investor views"""
    
    def __init__(self, tickers: List[str], risk_free_rate: float = 0.04, tau: float = 0.025):
        self.tickers = tickers
        self.risk_free_rate = risk_free_rate
        self.tau = tau
        self.returns = None
        self.cov_matrix = None
        self.market_weights = None
        
    def optimize_with_views(
        self,
        views: Dict[str, float],
        view_confidence: float = 0.5,
        period: str = "2y"
    ) -> Dict:
        """
        Black-Litterman optimization with investor views
        
        Args:
            views: {ticker: expected_return} (e.g., {'AAPL': 0.15, 'GOOGL': 0.12})
            view_confidence: Confidence in views (0-1), higher = trust views more
            period: Historical data period
        
        Returns:
            Optimized portfolio with posterior returns
        """
        print(f"🧠 Running Black-Litterman optimization with {len(views)} views...")
        
        # Fetch data
        optimizer = PortfolioOptimizer(self.tickers, self.risk_free_rate)
        optimizer.fetch_data(period)
        
        self.returns = optimizer.returns
        self.cov_matrix = optimizer.cov_matrix
        
        # Equal market weights (simplified - could use market cap)
        n = len(self.tickers)
        self.market_weights = np.ones(n) / n
        
        # Implied equilibrium returns (reverse optimization)
        pi = self._implied_returns(self.market_weights, self.cov_matrix)
        
        # Construct view matrix
        P, Q = self._construct_views(views)
        
        # Omega (uncertainty in views) - diagonal matrix
        # Lower confidence = higher uncertainty
        omega = np.diag(np.diag(P @ (self.tau * self.cov_matrix) @ P.T)) / view_confidence
        
        # Black-Litterman formula
        # Posterior covariance
        M_inv = np.linalg.inv(self.tau * self.cov_matrix) + P.T @ np.linalg.inv(omega) @ P
        posterior_cov = np.linalg.inv(M_inv)
        
        # Posterior returns
        posterior_returns = posterior_cov @ (
            np.linalg.inv(self.tau * self.cov_matrix) @ pi + P.T @ np.linalg.inv(omega) @ Q
        )
        
        # Optimize portfolio with posterior returns
        weights = self._optimize_weights(posterior_returns, self.cov_matrix)
        
        port_return = np.dot(weights, posterior_returns)
        port_vol = np.sqrt(np.dot(weights, np.dot(self.cov_matrix, weights)))
        sharpe = (port_return - self.risk_free_rate) / port_vol
        
        return {
            'weights': {ticker: float(w) for ticker, w in zip(self.tickers, weights)},
            'posterior_returns': {ticker: float(r) for ticker, r in zip(self.tickers, posterior_returns)},
            'implied_returns': {ticker: float(r) for ticker, r in zip(self.tickers, pi)},
            'expected_return': float(port_return),
            'volatility': float(port_vol),
            'sharpe_ratio': float(sharpe),
            'views': views
        }
    
    def _implied_returns(self, weights: np.ndarray, cov: np.ndarray) -> np.ndarray:
        """Reverse optimization to get implied equilibrium returns"""
        return self.risk_free_rate + np.dot(cov, weights)
    
    def _construct_views(self, views: Dict[str, float]) -> Tuple[np.ndarray, np.ndarray]:
        """Construct P (pick matrix) and Q (view returns) matrices"""
        n = len(self.tickers)
        k = len(views)
        
        P = np.zeros((k, n))
        Q = np.zeros(k)
        
        for i, (ticker, view_return) in enumerate(views.items()):
            if ticker in self.tickers:
                idx = self.tickers.index(ticker)
                P[i, idx] = 1.0
                Q[i] = view_return
        
        return P, Q
    
    def _optimize_weights(self, returns: np.ndarray, cov: np.ndarray) -> np.ndarray:
        """Optimize portfolio weights given returns and covariance"""
        n = len(returns)
        
        def objective(w):
            return -((np.dot(w, returns) - self.risk_free_rate) / np.sqrt(np.dot(w, np.dot(cov, w))))
        
        constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
        bounds = tuple((0, 1) for _ in range(n))
        x0 = np.ones(n) / n
        
        result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
        return result.x


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'mpt-optimize':
        if len(sys.argv) < 3:
            print("Usage: python portfolio_construction.py mpt-optimize AAPL,MSFT,GOOGL [--target-return 0.15] [--esg-min 60]")
            sys.exit(1)
        
        tickers = sys.argv[2].split(',')
        target_return = None
        esg_min = None
        
        # Parse optional args
        for i, arg in enumerate(sys.argv[3:], start=3):
            if arg == '--target-return' and i+1 < len(sys.argv):
                target_return = float(sys.argv[i+1])
            elif arg == '--esg-min' and i+1 < len(sys.argv):
                esg_min = float(sys.argv[i+1])
        
        optimizer = PortfolioOptimizer(tickers)
        optimizer.fetch_data()
        portfolio = optimizer.optimize_portfolio(target_return=target_return, esg_min_score=esg_min)
        
        print("\n" + "="*60)
        print("OPTIMIZED PORTFOLIO")
        print("="*60)
        print(f"\n📊 Expected Return: {portfolio['expected_return']*100:.2f}% annually")
        print(f"📉 Volatility: {portfolio['volatility']*100:.2f}% annually")
        print(f"📈 Sharpe Ratio: {portfolio['sharpe_ratio']:.3f}")
        if 'esg_score' in portfolio:
            print(f"🌱 ESG Score: {portfolio['esg_score']:.1f}/100")
        print(f"\n💼 Allocation:")
        for ticker, weight in sorted(portfolio['weights'].items(), key=lambda x: -x[1]):
            print(f"  {ticker:6s}: {weight*100:6.2f}%")
        
        # Save to JSON
        with open('portfolio_optimized.json', 'w') as f:
            json.dump(portfolio, f, indent=2)
        print(f"\n✅ Saved to portfolio_optimized.json")
    
    elif command == 'efficient-frontier':
        if len(sys.argv) < 3:
            print("Usage: python portfolio_construction.py efficient-frontier AAPL,TSLA,NVDA,JPM,JNJ [--esg-min 60]")
            sys.exit(1)
        
        tickers = sys.argv[2].split(',')
        esg_min = None
        
        for i, arg in enumerate(sys.argv[3:], start=3):
            if arg == '--esg-min' and i+1 < len(sys.argv):
                esg_min = float(sys.argv[i+1])
        
        optimizer = PortfolioOptimizer(tickers)
        optimizer.fetch_data()
        frontier = optimizer.efficient_frontier(n_portfolios=50, esg_min_score=esg_min)
        
        print("\n" + "="*60)
        print("EFFICIENT FRONTIER")
        print("="*60)
        print(f"\nGenerated {len(frontier)} efficient portfolios")
        print("\nTop 5 by Sharpe Ratio:")
        top = frontier.nlargest(5, 'sharpe_ratio')
        print(top[['return', 'volatility', 'sharpe_ratio']].to_string(index=False))
        
        # Save to CSV
        frontier.to_csv('efficient_frontier.csv', index=False)
        print(f"\n✅ Saved full frontier to efficient_frontier.csv")
        
        # Find max Sharpe portfolio
        max_sharpe_idx = frontier['sharpe_ratio'].idxmax()
        max_sharpe = frontier.loc[max_sharpe_idx]
        print("\n🏆 Maximum Sharpe Ratio Portfolio:")
        print(f"   Return: {max_sharpe['return']*100:.2f}%")
        print(f"   Volatility: {max_sharpe['volatility']*100:.2f}%")
        print(f"   Sharpe: {max_sharpe['sharpe_ratio']:.3f}")
        print("   Allocation:")
        for ticker in tickers:
            if ticker in max_sharpe:
                print(f"     {ticker:6s}: {max_sharpe[ticker]*100:6.2f}%")
    
    elif command == 'rebalance-plan':
        print("Usage: python portfolio_construction.py rebalance-plan")
        print("\nExample portfolio for demo purposes...")
        
        # Demo: current holdings
        current_holdings = {
            'AAPL': {'shares': 100, 'cost_basis': 150.0, 'purchase_date': '2023-01-15'},
            'MSFT': {'shares': 50, 'cost_basis': 300.0, 'purchase_date': '2023-06-20'},
            'GOOGL': {'shares': 75, 'cost_basis': 120.0, 'purchase_date': '2024-11-10'}
        }
        
        # Demo: target allocation
        target_weights = {
            'AAPL': 0.30,
            'MSFT': 0.40,
            'GOOGL': 0.20,
            'AMZN': 0.10
        }
        
        total_value = 100000  # $100k portfolio
        
        rebalancer = TaxAwareRebalancer(current_holdings, target_weights)
        plan = rebalancer.generate_rebalance_plan(total_value)
        
        print("\n" + "="*60)
        print("TAX-AWARE REBALANCING PLAN")
        print("="*60)
        
        print("\n📊 Current Allocation:")
        for ticker, pct in plan['current_allocation'].items():
            print(f"  {ticker:6s}: {pct}")
        
        print("\n🎯 Target Allocation:")
        for ticker, pct in plan['target_allocation'].items():
            print(f"  {ticker:6s}: {pct}")
        
        print(f"\n💰 Total Tax Liability: ${plan['total_tax_liability']:,.2f}")
        print(f"💸 Net Rebalancing Cost: ${plan['net_rebalancing_cost']:,.2f}")
        
        print("\n🔄 Recommended Trades:")
        for trade in plan['trades']:
            action_emoji = "🔴" if trade['action'] == 'SELL' else "🟢"
            print(f"\n  {action_emoji} {trade['action']} {trade['shares']:.1f} shares of {trade['ticker']}")
            print(f"     Trade Value: ${trade['trade_value']:,.2f}")
            if trade['tax_impact'] > 0:
                print(f"     Tax Impact: ${trade['tax_impact']:,.2f} ({trade['holding_type']})")
            if trade['wash_sale_risk']:
                print(f"     ⚠️  WASH SALE RISK: Consider waiting 30 days")
        
        # Save to JSON
        with open('rebalance_plan.json', 'w') as f:
            json.dump(plan, f, indent=2, default=str)
        print(f"\n✅ Saved to rebalance_plan.json")
    
    elif command == 'portfolio-risk':
        if len(sys.argv) < 3:
            print("Usage: python portfolio_construction.py portfolio-risk AAPL,MSFT,GOOGL [--weights 0.33,0.33,0.34]")
            sys.exit(1)
        
        tickers = sys.argv[2].split(',')
        weights = None
        
        for i, arg in enumerate(sys.argv[3:], start=3):
            if arg == '--weights' and i+1 < len(sys.argv):
                weights = [float(w) for w in sys.argv[i+1].split(',')]
        
        # Default to equal weights
        if weights is None:
            weights = [1.0 / len(tickers)] * len(tickers)
        
        weight_dict = {ticker: w for ticker, w in zip(tickers, weights)}
        
        optimizer = PortfolioOptimizer(tickers)
        optimizer.fetch_data()
        risk_decomp = optimizer.portfolio_risk_decomposition(weight_dict)
        
        print("\n" + "="*60)
        print("PORTFOLIO RISK DECOMPOSITION")
        print("="*60)
        print(f"\n📊 Portfolio Volatility: {risk_decomp['portfolio_volatility']*100:.2f}% annually")
        
        print("\n🔍 Risk Contribution by Asset:")
        for ticker in sorted(tickers, key=lambda t: -risk_decomp['risk_contribution_pct'][t]):
            pct = risk_decomp['risk_contribution_pct'][ticker]
            contrib = risk_decomp['risk_contribution'][ticker]
            print(f"  {ticker:6s}: {pct*100:6.2f}% of total risk (σ contribution: {contrib*100:.3f}%)")
        
        print("\n📈 Marginal Risk (∂σ/∂w):")
        for ticker, mcr in risk_decomp['marginal_risk'].items():
            print(f"  {ticker:6s}: {mcr*100:.2f}%")
        
        # Save to JSON
        with open('portfolio_risk.json', 'w') as f:
            json.dump(risk_decomp, f, indent=2)
        print(f"\n✅ Saved to portfolio_risk.json")
    
    else:
        print(f"Unknown command: {command}")
        print_help()
        sys.exit(1)


def print_help():
    """Print CLI help"""
    print("""
Portfolio Construction Tool - Phase 81

Commands:
  mpt-optimize TICKERS [OPTIONS]         Optimize portfolio weights (MPT)
  efficient-frontier TICKERS [OPTIONS]   Generate efficient frontier
  rebalance-plan                         Tax-aware rebalancing plan
  portfolio-risk TICKERS [OPTIONS]       Risk decomposition

Options:
  --target-return R    Target annual return (e.g., 0.15 for 15%)
  --esg-min SCORE      Minimum ESG score (0-100)
  --weights W1,W2,...  Portfolio weights (for risk decomposition)

Examples:
  python portfolio_construction.py mpt-optimize AAPL,MSFT,GOOGL,AMZN,META
  python portfolio_construction.py efficient-frontier AAPL,TSLA,NVDA,JPM,JNJ --esg-min 60
  python portfolio_construction.py rebalance-plan
  python portfolio_construction.py portfolio-risk AAPL,MSFT,GOOGL --weights 0.4,0.3,0.3
""")


if __name__ == '__main__':
    main()
