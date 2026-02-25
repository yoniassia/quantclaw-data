# Portfolio Construction Tool — Phase 81

**MPT Optimizer, Black-Litterman, ESG Constraints, Tax-Aware Rebalancing**

## Overview

Comprehensive portfolio construction toolkit implementing Modern Portfolio Theory with advanced constraints and tax optimization:

- **Mean-Variance Optimization (Markowitz)**: Classic MPT optimizer for maximum Sharpe ratio portfolios
- **Efficient Frontier**: Generate and visualize the efficient frontier with customizable constraints
- **Black-Litterman Model**: Combine market equilibrium with investor views for robust allocation
- **ESG Constraints**: Optimize portfolios subject to minimum ESG score requirements
- **Tax-Aware Rebalancing**: Minimize capital gains taxes while rebalancing, with wash sale awareness
- **Risk Decomposition**: Analyze marginal risk contributions by asset

## Data Sources

- **Yahoo Finance**: Historical prices, fundamentals, ESG scores
- **FRED API**: 10-Year Treasury rate (risk-free rate proxy)
- **Free APIs only**: No paid subscriptions required

## CLI Commands

### 1. Mean-Variance Optimization

Optimize portfolio weights using Markowitz MPT to maximize Sharpe ratio:

```bash
python cli.py mpt-optimize AAPL,MSFT,GOOGL,AMZN,META
python cli.py mpt-optimize AAPL,MSFT,GOOGL --target-return 0.15
python cli.py mpt-optimize AAPL,TSLA,NVDA --esg-min 60
```

**Parameters:**
- `--target-return R`: Target annual return (e.g., 0.15 for 15%)
- `--esg-min SCORE`: Minimum weighted ESG score (0-100)

**Output:**
- Expected annual return
- Annual volatility (standard deviation)
- Sharpe ratio
- Optimal weights for each asset
- ESG score (if constraint applied)

### 2. Efficient Frontier

Generate the efficient frontier to visualize the risk-return tradeoff:

```bash
python cli.py efficient-frontier AAPL,TSLA,NVDA,JPM,JNJ
python cli.py efficient-frontier AAPL,MSFT,GOOGL --esg-min 60
```

**Parameters:**
- `--esg-min SCORE`: Apply ESG constraint to all portfolios

**Output:**
- CSV file with 50 efficient portfolios
- Top 5 portfolios by Sharpe ratio
- Maximum Sharpe ratio portfolio (tangency portfolio)
- Return, volatility, and Sharpe for each portfolio
- Individual asset weights

### 3. Tax-Aware Rebalancing

Generate tax-efficient rebalancing plan with wash sale awareness:

```bash
python cli.py rebalance-plan
```

**Features:**
- Calculates current vs target allocation
- Estimates capital gains taxes (short-term: 37%, long-term: 20%)
- Identifies wash sale risks (30-day rule)
- Optimizes trade order to minimize tax impact
- Harvest losses first, then low-tax-impact changes

**Output:**
- Current and target allocations
- Recommended trades (buy/sell with shares and values)
- Tax liability per trade
- Total tax cost
- Wash sale warnings

### 4. Portfolio Risk Decomposition

Analyze risk contribution by asset:

```bash
python cli.py portfolio-risk AAPL,MSFT,GOOGL
python cli.py portfolio-risk AAPL,MSFT,GOOGL --weights 0.33,0.33,0.34
```

**Parameters:**
- `--weights W1,W2,...`: Portfolio weights (default: equal weights)

**Output:**
- Portfolio volatility (annualized)
- Risk contribution by asset (% of total risk)
- Marginal risk (∂σ/∂w) — how much risk increases per 1% allocation
- Component contribution to risk (CCR)

## API Endpoints

### GET /api/v1/portfolio-construction

**1. MPT Optimization**

```
GET /api/v1/portfolio-construction?action=mpt-optimize&tickers=AAPL,MSFT,GOOGL&target_return=0.15&esg_min=60
```

**2. Efficient Frontier**

```
GET /api/v1/portfolio-construction?action=efficient-frontier&tickers=AAPL,TSLA,NVDA&esg_min=60
```

**3. Rebalancing Plan**

```
GET /api/v1/portfolio-construction?action=rebalance-plan
```

**4. Risk Decomposition**

```
GET /api/v1/portfolio-construction?action=portfolio-risk&tickers=AAPL,MSFT,GOOGL&weights=0.33,0.33,0.34
```

## Implementation Details

### Optimization Constraints

**Standard constraints:**
- Weights sum to 1.0 (fully invested)
- Long-only (no short positions): 0 ≤ w_i ≤ 1
- Target return constraint (optional)
- Target risk constraint (optional)

**ESG constraint:**
- Weighted ESG score ≥ minimum threshold
- ESG scores fetched from Yahoo Finance sustainability data
- Default neutral score (50) if data unavailable

### Tax Optimization

**Holding period rules:**
- Short-term: < 365 days → 37% tax rate
- Long-term: ≥ 365 days → 20% tax rate

**Wash sale rule (IRS):**
- Cannot claim loss if security repurchased within 30 days before/after sale
- Flagged automatically in rebalancing plan
- Recommendation: Wait 30 days or use ETF replacement

### Risk Metrics

**Marginal Contribution to Risk (MCR):**
```
MCR_i = (Σw_j * Cov(i,j)) / σ_portfolio
```

**Component Contribution to Risk (CCR):**
```
CCR_i = w_i * MCR_i
```

**Percentage Contribution:**
```
% Contribution_i = CCR_i / σ_portfolio
```

## Black-Litterman Model

The Black-Litterman optimizer combines:
1. **Market Equilibrium (Prior)**: Implied returns from market cap weights
2. **Investor Views**: Your expected returns for specific assets
3. **Posterior Returns**: Bayesian combination of prior + views

**Formula:**
```
E[R] = [(τΣ)^(-1) + P'Ω^(-1)P]^(-1) [(τΣ)^(-1)π + P'Ω^(-1)Q]
```

Where:
- π = implied equilibrium returns
- P = view matrix (which assets)
- Q = view returns (expected returns)
- Ω = view uncertainty matrix
- τ = uncertainty scalar (default 0.025)

**Confidence parameter:**
- Higher confidence (0.8-1.0) → trust views more
- Lower confidence (0.2-0.5) → stay closer to equilibrium

## Example Use Cases

### 1. Maximum Sharpe Portfolio

```bash
python cli.py mpt-optimize AAPL,MSFT,GOOGL,AMZN,META
```

Finds the tangency portfolio (maximum Sharpe ratio) on the efficient frontier.

### 2. ESG-Constrained Allocation

```bash
python cli.py mpt-optimize AAPL,MSFT,GOOGL --esg-min 70
```

Optimize subject to minimum ESG score of 70/100.

### 3. Target Return Optimization

```bash
python cli.py mpt-optimize AAPL,MSFT,GOOGL --target-return 0.20
```

Find minimum-volatility portfolio that achieves 20% expected annual return.

### 4. Tax-Loss Harvesting

```bash
python cli.py rebalance-plan
```

Review tax implications before rebalancing. Harvest losses first, avoid wash sales.

### 5. Risk Attribution

```bash
python cli.py portfolio-risk AAPL,MSFT,GOOGL --weights 0.5,0.3,0.2
```

Understand which assets contribute most to portfolio risk.

## Output Files

All commands save results to JSON files for programmatic access:

- `portfolio_optimized.json` — Optimal weights and metrics
- `efficient_frontier.csv` — Full frontier data
- `rebalance_plan.json` — Tax-aware trade recommendations
- `portfolio_risk.json` — Risk decomposition metrics

## Technical Notes

**Solver:** SLSQP (Sequential Least Squares Programming)
- Handles inequality and equality constraints
- Gradient-based optimization
- Robust convergence for convex problems

**Annualization:**
- Returns: 252 trading days
- Volatility: sqrt(252) scaling

**Data period:**
- Default: 2 years of daily data
- Configurable via `period` parameter

**Limitations:**
- Yahoo Finance ESG data incomplete (many stocks missing)
- Risk-free rate from FRED may lag (updated weekly)
- Rebalancing plan uses demo portfolio (customize in production)

## License

Part of QUANTCLAW DATA — Phase 81
