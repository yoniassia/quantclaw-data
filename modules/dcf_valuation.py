#!/usr/bin/env python3
"""
DCF Valuation Engine — Phase 142

Automated discounted cash flow models from SEC XBRL financials + FRED rates
Comprehensive valuation analysis with sensitivity tables and scenario modeling

Methodology:
1. Extract historical financials from SEC XBRL (10-K/10-Q filings)
2. Project future free cash flows (5-10 year horizon)
3. Calculate WACC (Weighted Average Cost of Capital) using FRED data
4. Calculate terminal value using Gordon Growth Model
5. Discount all cash flows to present value
6. Perform sensitivity analysis on key assumptions

Data Sources:
- SEC EDGAR XBRL API: Historical financials (revenue, EBIT, capex, working capital)
- FRED API: Risk-free rate (10Y Treasury), market risk premium proxies
- Yahoo Finance: Beta, market cap, shares outstanding

Author: QUANTCLAW DATA Build Agent
Phase: 142
"""

import sys
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import time
import warnings
warnings.filterwarnings('ignore')

# Import SEC XBRL utilities
from sec_xbrl_financial_statements import (
    get_cik_from_ticker,
    get_financial_statements
)

# FRED API Configuration
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_API_KEY = ""  # Public access for basic queries

# FRED Series for DCF inputs
FRED_SERIES = {
    "DGS10": "10-Year Treasury Constant Maturity Rate",  # Risk-free rate
    "DGS3MO": "3-Month Treasury Bill",  # Short-term rate
    "DAAA": "Moody's Seasoned Aaa Corporate Bond Yield",  # Corporate bond benchmark
    "DBAA": "Moody's Seasoned Baa Corporate Bond Yield",  # Lower grade corporate
    "GDP": "Gross Domestic Product",  # GDP growth proxy
}

# DCF Model Defaults
DEFAULT_PROJECTION_YEARS = 5
DEFAULT_TERMINAL_GROWTH_RATE = 0.025  # 2.5% perpetual growth
DEFAULT_TAX_RATE = 0.21  # US corporate tax rate
DEFAULT_MARKET_RISK_PREMIUM = 0.055  # 5.5% historical equity risk premium


def get_fred_latest(series_id: str) -> Optional[float]:
    """Fetch latest value from FRED series"""
    try:
        url = f"{FRED_BASE_URL}/series/observations"
        params = {
            "series_id": series_id,
            "file_type": "json",
            "limit": 1,
            "sort_order": "desc"
        }
        
        if FRED_API_KEY:
            params["api_key"] = FRED_API_KEY
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "observations" in data and len(data["observations"]) > 0:
                value = data["observations"][0]["value"]
                if value != ".":
                    return float(value) / 100  # Convert percentage to decimal
        
        return None
    except Exception as e:
        print(f"FRED fetch error for {series_id}: {e}", file=sys.stderr)
        return None


def get_company_beta(ticker: str) -> float:
    """
    Get company beta from Yahoo Finance
    Beta measures systematic risk relative to market
    """
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info
        beta = info.get('beta', 1.0)
        return beta if beta and beta > 0 else 1.0
    except:
        return 1.0  # Default to market beta


def get_shares_outstanding(ticker: str) -> Optional[float]:
    """Get shares outstanding from Yahoo Finance"""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info
        shares = info.get('sharesOutstanding')
        return shares if shares else None
    except:
        return None


def calculate_wacc(
    ticker: str,
    risk_free_rate: float,
    market_risk_premium: float,
    tax_rate: float,
    debt_to_equity: Optional[float] = None
) -> Dict:
    """
    Calculate Weighted Average Cost of Capital (WACC)
    
    WACC = (E/V × Re) + (D/V × Rd × (1-Tc))
    
    Where:
    - E = Market value of equity
    - D = Market value of debt
    - V = E + D
    - Re = Cost of equity (CAPM)
    - Rd = Cost of debt
    - Tc = Corporate tax rate
    
    Cost of Equity (Re) = Rf + β(Rm - Rf)
    """
    # Get beta
    beta = get_company_beta(ticker)
    
    # Cost of equity using CAPM
    cost_of_equity = risk_free_rate + (beta * market_risk_premium)
    
    # Get cost of debt from FRED (use Baa corporate bond yield as proxy)
    cost_of_debt = get_fred_latest("DBAA")
    if not cost_of_debt:
        cost_of_debt = risk_free_rate + 0.03  # Default spread
    
    # Estimate debt-to-equity ratio if not provided
    if debt_to_equity is None:
        # Use industry average assumption
        debt_to_equity = 0.5  # Conservative assumption
    
    # Calculate weights
    equity_weight = 1 / (1 + debt_to_equity)
    debt_weight = debt_to_equity / (1 + debt_to_equity)
    
    # Calculate WACC
    wacc = (equity_weight * cost_of_equity) + (debt_weight * cost_of_debt * (1 - tax_rate))
    
    return {
        "wacc": wacc,
        "cost_of_equity": cost_of_equity,
        "cost_of_debt": cost_of_debt,
        "equity_weight": equity_weight,
        "debt_weight": debt_weight,
        "beta": beta,
        "risk_free_rate": risk_free_rate,
        "market_risk_premium": market_risk_premium,
        "tax_rate": tax_rate,
        "debt_to_equity_ratio": debt_to_equity
    }


def project_free_cash_flows(
    historical_fcf: List[float],
    growth_rates: Optional[List[float]] = None,
    years: int = 5
) -> List[float]:
    """
    Project future free cash flows
    
    Args:
        historical_fcf: List of historical FCF values (most recent last)
        growth_rates: Optional custom growth rates for each year
        years: Number of years to project
    
    Returns:
        List of projected FCF values
    """
    if not historical_fcf:
        return []
    
    # Use most recent FCF as base
    base_fcf = historical_fcf[-1]
    
    if base_fcf <= 0:
        # If FCF is negative, use average of positive years
        positive_fcf = [f for f in historical_fcf if f > 0]
        if positive_fcf:
            base_fcf = sum(positive_fcf) / len(positive_fcf)
        else:
            return [0] * years
    
    # Calculate historical growth rate if no custom rates provided
    if not growth_rates:
        if len(historical_fcf) >= 2:
            # Calculate CAGR from historical data
            periods = len(historical_fcf) - 1
            first_positive = next((f for f in historical_fcf if f > 0), None)
            if first_positive and base_fcf > 0:
                cagr = (base_fcf / first_positive) ** (1/periods) - 1
                # Cap growth rate at reasonable levels
                cagr = max(min(cagr, 0.20), -0.05)  # Between -5% and 20%
            else:
                cagr = 0.05  # Default 5% growth
        else:
            cagr = 0.05
        
        # Declining growth rate over projection period
        growth_rates = [cagr * (0.85 ** i) for i in range(years)]
    
    # Project cash flows
    projected_fcf = []
    current_fcf = base_fcf
    
    for i in range(years):
        growth = growth_rates[i] if i < len(growth_rates) else growth_rates[-1]
        current_fcf = current_fcf * (1 + growth)
        projected_fcf.append(current_fcf)
    
    return projected_fcf


def calculate_terminal_value(
    final_fcf: float,
    wacc: float,
    terminal_growth_rate: float = DEFAULT_TERMINAL_GROWTH_RATE
) -> float:
    """
    Calculate terminal value using Gordon Growth Model
    
    TV = FCF_n × (1 + g) / (WACC - g)
    
    Where:
    - FCF_n = Free cash flow in final projection year
    - g = Terminal growth rate (perpetuity)
    - WACC = Discount rate
    """
    if wacc <= terminal_growth_rate:
        # Invalid: WACC must be greater than terminal growth
        terminal_growth_rate = wacc * 0.5  # Use half of WACC
    
    terminal_value = (final_fcf * (1 + terminal_growth_rate)) / (wacc - terminal_growth_rate)
    return terminal_value


def discount_cash_flows(
    cash_flows: List[float],
    discount_rate: float,
    terminal_value: float = 0
) -> Dict:
    """
    Discount cash flows to present value
    
    PV = CF_t / (1 + r)^t
    """
    pv_cash_flows = []
    
    for year, cf in enumerate(cash_flows, start=1):
        pv = cf / ((1 + discount_rate) ** year)
        pv_cash_flows.append({
            "year": year,
            "cash_flow": cf,
            "discount_factor": 1 / ((1 + discount_rate) ** year),
            "present_value": pv
        })
    
    # Discount terminal value
    terminal_year = len(cash_flows)
    pv_terminal = terminal_value / ((1 + discount_rate) ** terminal_year)
    
    total_pv = sum(cf["present_value"] for cf in pv_cash_flows) + pv_terminal
    
    return {
        "pv_cash_flows": pv_cash_flows,
        "pv_terminal_value": pv_terminal,
        "terminal_value": terminal_value,
        "total_enterprise_value": total_pv
    }


def perform_dcf_valuation(
    ticker: str,
    projection_years: int = DEFAULT_PROJECTION_YEARS,
    terminal_growth_rate: float = DEFAULT_TERMINAL_GROWTH_RATE,
    tax_rate: float = DEFAULT_TAX_RATE,
    market_risk_premium: float = DEFAULT_MARKET_RISK_PREMIUM,
    custom_growth_rates: Optional[List[float]] = None
) -> Dict:
    """
    Complete DCF valuation for a company
    
    Returns comprehensive valuation with sensitivity analysis
    """
    ticker = ticker.upper()
    
    try:
        # Step 1: Fetch historical financials from SEC XBRL (last 5 years)
        historical_fcf = []
        historical_data = []
        company_name = ticker
        latest_financials = None
        
        current_year = datetime.now().year
        years_to_fetch = list(range(current_year - 5, current_year + 1))
        
        for year in years_to_fetch:
            stmt = get_financial_statements(ticker, form_type='10-K', fiscal_year=year)
            
            if 'error' not in stmt:
                ocf = stmt.get('cash_flow', {}).get('operating_cash_flow', 0) or 0
                capex = abs(stmt.get('cash_flow', {}).get('capital_expenditure', 0) or 0)
                fcf = ocf - capex
                
                if fcf != 0:  # Only include years with data
                    historical_fcf.append(fcf)
                    historical_data.append({
                        "period": str(year),
                        "operating_cash_flow": ocf,
                        "capex": capex,
                        "free_cash_flow": fcf
                    })
                    
                    # Store most recent successful fetch
                    if latest_financials is None:
                        latest_financials = stmt
                        company_name = stmt.get('metadata', {}).get('company_name', ticker)
        
        if not historical_fcf:
            return {
                "error": f"No historical cash flow data available for {ticker}",
                "ticker": ticker
            }
        
        if latest_financials is None:
            return {
                "error": f"Could not fetch recent financials for {ticker}",
                "ticker": ticker
            }
        
        # Step 3: Get risk-free rate from FRED
        risk_free_rate = get_fred_latest("DGS10")
        if not risk_free_rate:
            risk_free_rate = 0.04  # Default 4% if FRED unavailable
        
        # Step 4: Calculate debt-to-equity from balance sheet
        total_debt = latest_financials.get('balance_sheet', {}).get('long_term_debt', 0) or 0
        equity = latest_financials.get('balance_sheet', {}).get('stockholders_equity', 0) or 0
        cash = latest_financials.get('balance_sheet', {}).get('cash', 0) or 0
        
        debt_to_equity = total_debt / equity if equity > 0 else 0.5
        
        # Step 5: Calculate WACC
        wacc_data = calculate_wacc(
            ticker=ticker,
            risk_free_rate=risk_free_rate,
            market_risk_premium=market_risk_premium,
            tax_rate=tax_rate,
            debt_to_equity=debt_to_equity
        )
        
        wacc = wacc_data["wacc"]
        
        # Step 6: Project future free cash flows
        projected_fcf = project_free_cash_flows(
            historical_fcf=historical_fcf,
            growth_rates=custom_growth_rates,
            years=projection_years
        )
        
        # Step 7: Calculate terminal value
        terminal_value = calculate_terminal_value(
            final_fcf=projected_fcf[-1],
            wacc=wacc,
            terminal_growth_rate=terminal_growth_rate
        )
        
        # Step 8: Discount cash flows to present value
        dcf_result = discount_cash_flows(
            cash_flows=projected_fcf,
            discount_rate=wacc,
            terminal_value=terminal_value
        )
        
        enterprise_value = dcf_result["total_enterprise_value"]
        
        # Step 9: Calculate equity value
        # Equity Value = Enterprise Value + Cash - Debt
        equity_value = enterprise_value + cash - total_debt
        
        # Step 10: Calculate intrinsic value per share
        shares_outstanding = get_shares_outstanding(ticker)
        
        if shares_outstanding and shares_outstanding > 0:
            intrinsic_value_per_share = equity_value / shares_outstanding
        else:
            intrinsic_value_per_share = None
        
        # Step 11: Get current market price
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            current_price = stock.info.get('currentPrice') or stock.info.get('regularMarketPrice')
            
            if current_price and intrinsic_value_per_share:
                upside_downside = ((intrinsic_value_per_share - current_price) / current_price) * 100
                recommendation = "BUY" if upside_downside > 20 else "HOLD" if upside_downside > -10 else "SELL"
            else:
                upside_downside = None
                recommendation = None
        except:
            current_price = None
            upside_downside = None
            recommendation = None
        
        # Step 12: Sensitivity analysis
        sensitivity = perform_sensitivity_analysis(
            projected_fcf=projected_fcf,
            terminal_growth_base=terminal_growth_rate,
            wacc_base=wacc,
            shares_outstanding=shares_outstanding
        )
        
        return {
            "ticker": ticker,
            "valuation_date": datetime.now().strftime("%Y-%m-%d"),
            "company_name": company_name,
            
            # Valuation Summary
            "enterprise_value": enterprise_value,
            "equity_value": equity_value,
            "intrinsic_value_per_share": intrinsic_value_per_share,
            "current_price": current_price,
            "upside_downside_pct": upside_downside,
            "recommendation": recommendation,
            
            # Key Inputs
            "assumptions": {
                "projection_years": projection_years,
                "terminal_growth_rate": terminal_growth_rate,
                "tax_rate": tax_rate,
                "market_risk_premium": market_risk_premium,
                "wacc": wacc,
                "risk_free_rate": risk_free_rate
            },
            
            # WACC Components
            "wacc_breakdown": wacc_data,
            
            # Historical Analysis
            "historical_fcf": historical_data,
            
            # Projections
            "projected_fcf": [
                {"year": i+1, "free_cash_flow": fcf}
                for i, fcf in enumerate(projected_fcf)
            ],
            
            # DCF Calculation
            "dcf_details": dcf_result,
            
            # Balance Sheet Items
            "balance_sheet": {
                "cash": cash,
                "total_debt": total_debt,
                "stockholders_equity": equity,
                "debt_to_equity": debt_to_equity
            },
            
            # Share Information
            "shares_outstanding": shares_outstanding,
            
            # Sensitivity Analysis
            "sensitivity_analysis": sensitivity
        }
        
    except Exception as e:
        return {
            "error": f"DCF valuation failed for {ticker}: {str(e)}",
            "ticker": ticker
        }


def perform_sensitivity_analysis(
    projected_fcf: List[float],
    terminal_growth_base: float,
    wacc_base: float,
    shares_outstanding: Optional[float]
) -> Dict:
    """
    Perform sensitivity analysis on WACC and terminal growth rate
    
    Creates a matrix of valuations with varying assumptions
    """
    # Sensitivity ranges
    terminal_growth_range = [
        terminal_growth_base - 0.01,
        terminal_growth_base,
        terminal_growth_base + 0.01
    ]
    
    wacc_range = [
        wacc_base - 0.01,
        wacc_base,
        wacc_base + 0.01
    ]
    
    sensitivity_matrix = []
    
    for tg in terminal_growth_range:
        row = []
        for w in wacc_range:
            if w <= tg:
                row.append(None)  # Invalid case
                continue
            
            # Calculate terminal value
            tv = calculate_terminal_value(projected_fcf[-1], w, tg)
            
            # Discount cash flows
            result = discount_cash_flows(projected_fcf, w, tv)
            ev = result["total_enterprise_value"]
            
            # Calculate per-share value if shares available
            if shares_outstanding and shares_outstanding > 0:
                value_per_share = ev / shares_outstanding
            else:
                value_per_share = None
            
            row.append({
                "enterprise_value": ev,
                "value_per_share": value_per_share,
                "wacc": w,
                "terminal_growth": tg
            })
        
        sensitivity_matrix.append(row)
    
    return {
        "terminal_growth_range": terminal_growth_range,
        "wacc_range": wacc_range,
        "sensitivity_matrix": sensitivity_matrix
    }


def compare_valuations(tickers: List[str]) -> Dict:
    """
    Compare DCF valuations across multiple companies
    """
    results = {}
    
    for ticker in tickers:
        print(f"Analyzing {ticker}...", file=sys.stderr)
        valuation = perform_dcf_valuation(ticker)
        results[ticker] = valuation
        time.sleep(0.5)  # Rate limiting
    
    # Create comparison table
    comparison = []
    
    for ticker, val in results.items():
        if "error" not in val:
            comparison.append({
                "ticker": ticker,
                "intrinsic_value": val.get("intrinsic_value_per_share"),
                "current_price": val.get("current_price"),
                "upside_downside_pct": val.get("upside_downside_pct"),
                "recommendation": val.get("recommendation"),
                "wacc": val["assumptions"]["wacc"],
                "enterprise_value": val["enterprise_value"]
            })
    
    # Sort by upside potential
    comparison.sort(
        key=lambda x: x.get("upside_downside_pct") or -999,
        reverse=True
    )
    
    return {
        "comparison_date": datetime.now().strftime("%Y-%m-%d"),
        "companies": comparison,
        "detailed_results": results
    }


def main():
    """CLI interface for DCF valuation"""
    if len(sys.argv) < 3:
        print(json.dumps({
            "error": "Usage: dcf_valuation.py <command> <ticker|tickers>",
            "commands": [
                "dcf <ticker>",
                "dcf-sensitivity <ticker>",
                "dcf-compare <ticker1> <ticker2> ...",
                "dcf-quick <ticker>"
            ],
            "examples": [
                "dcf_valuation.py dcf AAPL",
                "dcf_valuation.py dcf-compare AAPL MSFT GOOGL",
                "dcf_valuation.py dcf-quick TSLA"
            ]
        }))
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "dcf":
        ticker = sys.argv[2].upper()
        result = perform_dcf_valuation(ticker)
        print(json.dumps(result, indent=2))
    
    elif command in ["dcf-sensitivity", "sensitivity"]:
        ticker = sys.argv[2].upper()
        result = perform_dcf_valuation(ticker)
        if "error" not in result:
            print(json.dumps(result["sensitivity_analysis"], indent=2))
        else:
            print(json.dumps(result, indent=2))
    
    elif command in ["dcf-compare", "compare"]:
        tickers = [t.upper() for t in sys.argv[2:]]
        result = compare_valuations(tickers)
        print(json.dumps(result, indent=2))
    
    elif command in ["dcf-quick", "quick"]:
        # Quick valuation with key metrics only
        ticker = sys.argv[2].upper()
        result = perform_dcf_valuation(ticker)
        
        if "error" not in result:
            quick_summary = {
                "ticker": result["ticker"],
                "intrinsic_value_per_share": result["intrinsic_value_per_share"],
                "current_price": result["current_price"],
                "upside_downside_pct": result["upside_downside_pct"],
                "recommendation": result["recommendation"],
                "wacc": result["assumptions"]["wacc"],
                "enterprise_value": result["enterprise_value"]
            }
            print(json.dumps(quick_summary, indent=2))
        else:
            print(json.dumps(result, indent=2))
    
    else:
        print(json.dumps({
            "error": f"Unknown command: {command}",
            "available": ["dcf", "dcf-sensitivity", "dcf-compare", "dcf-quick"]
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
