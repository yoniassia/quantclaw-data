# Monte Carlo Simulation Module
**Phase 34: Scenario Analysis, Probabilistic Forecasting, Tail Risk Modeling**

## Overview
Monte Carlo simulation for stocks using two methods:
1. **Geometric Brownian Motion (GBM)** - Parametric approach modeling stock prices as continuous-time stochastic processes
2. **Bootstrap Resampling** - Non-parametric approach sampling from historical returns

## Features

### 1. Monte Carlo Simulation
- **GBM**: S(t) = S(0) * exp((μ - σ²/2)t + σW(t))
- **Bootstrap**: Random sampling with replacement from historical returns
- Outputs: percentiles, tail risk metrics, probability distributions
- Customizable: simulations count, horizon, method, random seed

### 2. Value-at-Risk (VaR) & Conditional VaR (CVaR)
- **VaR**: Maximum expected loss at confidence level (95%, 99%)
- **CVaR**: Expected loss given VaR threshold breach (tail risk)
- Risk metrics in both percentage and dollar terms
- Confidence intervals: customizable

### 3. Scenario Analysis
- **Bull Case**: +2σ drift, -0.5σ volatility
- **Base Case**: Historical drift and volatility
- **Bear Case**: -2σ drift, +0.5σ volatility
- **Crash Case**: -3σ drift, +1σ volatility
- Outputs: final prices, returns, max drawdown per scenario

## Usage

### CLI Commands

```bash
# 1. Monte Carlo Simulation (GBM)
python cli.py monte-carlo AAPL --simulations 10000 --days 252 --method gbm

# 2. Monte Carlo Simulation (Bootstrap)
python cli.py monte-carlo TSLA --simulations 10000 --days 252 --method bootstrap --seed 42

# 3. Value-at-Risk (VaR/CVaR)
python cli.py var NVDA --confidence 0.95 0.99 --days 21 --simulations 10000

# 4. Scenario Analysis
python cli.py scenario AAPL --days 90
```

### API Endpoints

```bash
# 1. Monte Carlo Simulation
GET /api/v1/monte-carlo?action=simulate&ticker=AAPL&simulations=10000&days=252&method=gbm

# 2. VaR/CVaR
GET /api/v1/monte-carlo?action=var&ticker=TSLA&confidence=0.95 0.99&days=21

# 3. Scenario Analysis
GET /api/v1/monte-carlo?action=scenario&ticker=NVDA&days=90

# 4. Help
GET /api/v1/monte-carlo?action=help
```

## Example Output

### Monte Carlo GBM Simulation
```json
{
  "ticker": "AAPL",
  "method": "geometric_brownian_motion",
  "current_price": 272.22,
  "simulations": 10000,
  "days": 252,
  "parameters": {
    "drift_daily": 0.0004,
    "volatility_daily": 0.0202,
    "drift_annual": 0.1016,
    "volatility_annual": 0.3214
  },
  "statistics": {
    "expected_final_price": 303.45,
    "median_final_price": 298.12,
    "expected_return_pct": 11.47,
    "probability_profit": 0.578
  },
  "percentiles": {
    "p1": 168.23,
    "p50": 298.12,
    "p99": 512.89
  },
  "tail_risk": {
    "1pct_worst_case": 168.23,
    "5pct_worst_case": 195.44,
    "1pct_best_case": 512.89,
    "5pct_best_case": 445.67
  }
}
```

### VaR/CVaR Output
```json
{
  "ticker": "TSLA",
  "method": "gbm",
  "simulations": 10000,
  "days": 21,
  "risk_metrics": {
    "confidence_95pct": {
      "var_return_pct": -18.45,
      "cvar_return_pct": -24.32,
      "var_dollar": -75.42,
      "cvar_dollar": -99.47,
      "interpretation_var": "95.0% confident losses will not exceed 18.45%",
      "interpretation_cvar": "Expected loss if VaR threshold is breached: 24.32%"
    },
    "confidence_99pct": {
      "var_return_pct": -28.67,
      "cvar_return_pct": -35.21,
      "var_dollar": -117.23,
      "cvar_dollar": -143.96,
      "interpretation_var": "99.0% confident losses will not exceed 28.67%",
      "interpretation_cvar": "Expected loss if VaR threshold is breached: 35.21%"
    }
  }
}
```

### Scenario Analysis Output
```json
{
  "ticker": "NVDA",
  "current_price": 192.37,
  "days": 90,
  "scenarios": {
    "bull": {
      "final_price": 256.89,
      "total_return_pct": 33.52,
      "max_drawdown_pct": -8.34
    },
    "base": {
      "final_price": 205.12,
      "total_return_pct": 6.63,
      "max_drawdown_pct": -15.67
    },
    "bear": {
      "final_price": 167.45,
      "total_return_pct": -12.97,
      "max_drawdown_pct": -24.89
    },
    "crash": {
      "final_price": 134.56,
      "total_return_pct": -30.06,
      "max_drawdown_pct": -38.12
    }
  }
}
```

## Mathematical Background

### Geometric Brownian Motion
The GBM model assumes stock prices follow:
```
dS = μS dt + σS dW
```

Where:
- `S` = stock price
- `μ` = drift (expected return)
- `σ` = volatility (standard deviation)
- `dW` = Wiener process (random walk)

Solution (discrete time):
```
S(t+dt) = S(t) * exp((μ - σ²/2)dt + σ√dt * Z)
```
Where `Z ~ N(0,1)` is standard normal.

### Bootstrap Resampling
Non-parametric approach:
1. Calculate historical log returns: `r_t = ln(S_t / S_{t-1})`
2. Randomly sample from historical returns with replacement
3. Reconstruct price paths: `S(t) = S(0) * exp(Σ r_i)`

Advantages: Captures empirical distribution, no normality assumption

### Value-at-Risk (VaR)
```
VaR(α) = -F⁻¹(1-α)
```
Where `F` is the cumulative return distribution.

95% VaR = loss threshold exceeded only 5% of the time.

### Conditional VaR (CVaR)
```
CVaR(α) = E[Loss | Loss > VaR(α)]
```
Expected loss in the worst α% of cases (tail expectation).

CVaR is a coherent risk measure (satisfies subadditivity).

## Dependencies
```bash
pip install yfinance numpy scipy
```

## Parameters

### monte-carlo
- `ticker` (required): Stock symbol
- `--simulations` (default: 10000): Number of simulation paths
- `--days` (default: 252): Simulation horizon (trading days)
- `--method` (default: 'gbm'): 'gbm' or 'bootstrap'
- `--lookback` (default: 252): Historical data period
- `--seed` (optional): Random seed for reproducibility

### var
- `ticker` (required): Stock symbol
- `--confidence` (default: [0.95, 0.99]): Confidence levels
- `--days` (default: 252): Risk horizon
- `--simulations` (default: 10000): Number of simulations
- `--method` (default: 'gbm'): 'gbm' or 'bootstrap'

### scenario
- `ticker` (required): Stock symbol
- `--days` (default: 252): Scenario horizon
- `--lookback` (default: 252): Historical lookback period

## Use Cases

1. **Portfolio Risk Assessment**: Calculate VaR/CVaR for risk budgeting
2. **Options Pricing Validation**: Compare Monte Carlo prices to Black-Scholes
3. **Stress Testing**: Analyze portfolio under crash scenarios
4. **Probability Estimation**: "What's the chance TSLA hits $500 in 3 months?"
5. **Expected Return Distribution**: Visualize full return distribution
6. **Tail Risk Analysis**: Understand worst-case outcomes
7. **Backtesting Strategy**: Simulate strategy performance across many paths

## Performance
- **10,000 simulations × 252 days**: ~2-3 seconds
- **100,000 simulations × 252 days**: ~20-30 seconds
- Bootstrap is slightly faster than GBM for same parameters

## Limitations
1. **GBM Assumptions**: 
   - Constant drift and volatility (not realistic)
   - Log-normal returns (fat tails underestimated)
   - No jumps or regime changes
   
2. **Bootstrap Limitations**:
   - Limited by historical sample size
   - Assumes past distribution = future distribution
   - No forward-looking information

3. **General**:
   - No correlation modeling (single-asset only)
   - No dividends or corporate actions
   - Transaction costs not modeled

## Extensions (Future)
- Multi-asset correlation modeling
- Jump-diffusion processes (Merton model)
- GARCH volatility forecasting
- Option payoff simulation
- Portfolio-level VaR with correlation

## References
- Hull, J. (2018). *Options, Futures, and Other Derivatives*
- Glasserman, P. (2003). *Monte Carlo Methods in Financial Engineering*
- Jorion, P. (2006). *Value at Risk: The New Benchmark for Managing Financial Risk*

---

**Phase 34 Complete** | 518 lines of code | 2026-02-24
