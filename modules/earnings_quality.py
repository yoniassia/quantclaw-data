#!/usr/bin/env python3
"""
Earnings Quality Metrics Module — Accruals Ratio, Beneish M-Score, Altman Z-Score

Detects potential earnings manipulation and financial distress:
- Accruals Ratio: (Net Income - Operating Cash Flow) / Total Assets
  High positive accruals (>0.1) indicate potential earnings manipulation
- Beneish M-Score: 8-variable fraud detection model
  Score > -2.22 suggests possible earnings manipulation
- Altman Z-Score: Bankruptcy prediction model
  Z < 1.81 indicates high distress risk, Z > 2.99 indicates safety

Data Sources: 
- Yahoo Finance (financial statements, cash flow, balance sheet)
- SEC EDGAR XBRL (machine-readable financial data when available)

Author: QUANTCLAW DATA Build Agent
Phase: 59
"""

import sys
import json
from datetime import datetime
from typing import Dict, List, Optional
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

def safe_get_value(value, default=0) -> float:
    """Safely extract numeric value"""
    try:
        if value is None:
            return default
        return float(value)
    except:
        return default

def calculate_accruals_ratio(net_income: float, operating_cash_flow: float, total_assets: float) -> float:
    """
    Calculate Accruals Ratio (Sloan 1996)
    Accruals Ratio = (Net Income - Operating Cash Flow) / Total Assets
    
    Interpretation:
    - High positive (>0.1): Potential earnings manipulation
    - Negative: Cash flow exceeds earnings (good quality)
    - Near zero: Earnings align with cash flow (high quality)
    """
    if total_assets <= 0:
        return 0
    return (net_income - operating_cash_flow) / total_assets

def calculate_beneish_m_score(data: Dict) -> float:
    """
    Calculate Beneish M-Score (1999) — 8-Variable Fraud Detection Model
    
    M = -4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI + 0.115*DEPI 
        - 0.172*SGAI + 4.679*TATA - 0.327*LVGI
    
    Variables:
    - DSRI (Days Sales in Receivables Index): Measures receivables growth vs revenue
    - GMI (Gross Margin Index): Deteriorating margins signal manipulation
    - AQI (Asset Quality Index): Non-current assets growth
    - SGI (Sales Growth Index): Revenue growth
    - DEPI (Depreciation Index): Declining depreciation rate
    - SGAI (SG&A Index): Rising SG&A costs
    - TATA (Total Accruals to Total Assets): Accruals quality
    - LVGI (Leverage Index): Increasing leverage
    
    Interpretation:
    - M > -2.22: Likely manipulator
    - M < -2.22: Unlikely manipulator
    """
    dsri = data.get('dsri', 1.0)
    gmi = data.get('gmi', 1.0)
    aqi = data.get('aqi', 1.0)
    sgi = data.get('sgi', 1.0)
    depi = data.get('depi', 1.0)
    sgai = data.get('sgai', 1.0)
    tata = data.get('tata', 0.0)
    lvgi = data.get('lvgi', 1.0)
    
    m_score = (-4.84 + 0.920 * dsri + 0.528 * gmi + 0.404 * aqi + 
               0.892 * sgi + 0.115 * depi - 0.172 * sgai + 
               4.679 * tata - 0.327 * lvgi)
    
    return m_score

def calculate_altman_z_score(working_capital: float, retained_earnings: float, ebit: float, 
                             market_cap: float, total_liabilities: float, sales: float, 
                             total_assets: float) -> float:
    """
    Calculate Altman Z-Score (1968) — Bankruptcy Prediction Model
    
    For public companies:
    Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
    
    Where:
    - X1 = Working Capital / Total Assets (liquidity)
    - X2 = Retained Earnings / Total Assets (profitability)
    - X3 = EBIT / Total Assets (operating efficiency)
    - X4 = Market Cap / Total Liabilities (leverage)
    - X5 = Sales / Total Assets (asset turnover)
    
    Interpretation:
    - Z > 2.99: Safe zone (low bankruptcy risk)
    - 1.81 < Z < 2.99: Grey zone (moderate risk)
    - Z < 1.81: Distress zone (high bankruptcy risk)
    """
    if total_assets <= 0:
        return 0
    
    x1 = working_capital / total_assets
    x2 = retained_earnings / total_assets
    x3 = ebit / total_assets
    x4 = market_cap / total_liabilities if total_liabilities > 0 else 0
    x5 = sales / total_assets
    
    z_score = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5
    
    return z_score

def calculate_beneish_variables(current: Dict, prior: Dict) -> Dict:
    """Calculate all 8 Beneish M-Score variables"""
    
    # Extract current period values
    receivables_curr = current.get('receivables', 0)
    revenue_curr = current.get('revenue', 1)
    cogs_curr = current.get('cogs', 0)
    current_assets_curr = current.get('current_assets', 0)
    ppe_curr = current.get('ppe', 0)
    total_assets_curr = current.get('total_assets', 1)
    depreciation_curr = current.get('depreciation', 0)
    sga_curr = current.get('sga', 0)
    net_income_curr = current.get('net_income', 0)
    cfo_curr = current.get('cfo', 0)
    current_liabilities_curr = current.get('current_liabilities', 0)
    long_term_debt_curr = current.get('long_term_debt', 0)
    
    # Extract prior period values
    receivables_prior = prior.get('receivables', 1)
    revenue_prior = prior.get('revenue', 1)
    cogs_prior = prior.get('cogs', 0)
    current_assets_prior = prior.get('current_assets', 1)
    ppe_prior = prior.get('ppe', 1)
    total_assets_prior = prior.get('total_assets', 1)
    depreciation_prior = prior.get('depreciation', 1)
    sga_prior = prior.get('sga', 1)
    long_term_debt_prior = prior.get('long_term_debt', 0)
    
    # Avoid division by zero
    revenue_prior = max(revenue_prior, 1)
    receivables_prior = max(receivables_prior, 1)
    cogs_prior = max(cogs_prior, 1)
    total_assets_prior = max(total_assets_prior, 1)
    ppe_prior = max(ppe_prior, 1)
    depreciation_prior = max(depreciation_prior, 1)
    sga_prior = max(sga_prior, 1)
    
    # 1. DSRI (Days Sales in Receivables Index)
    dsr_curr = receivables_curr / revenue_curr if revenue_curr > 0 else 0
    dsr_prior = receivables_prior / revenue_prior
    dsri = dsr_curr / dsr_prior if dsr_prior > 0 else 1.0
    
    # 2. GMI (Gross Margin Index)
    gm_prior = (revenue_prior - cogs_prior) / revenue_prior if revenue_prior > 0 else 0
    gm_curr = (revenue_curr - cogs_curr) / revenue_curr if revenue_curr > 0 else 0
    gmi = gm_prior / gm_curr if gm_curr > 0 else 1.0
    
    # 3. AQI (Asset Quality Index)
    # Non-current assets other than PPE
    nca_curr = max(0, total_assets_curr - current_assets_curr - ppe_curr)
    nca_prior = max(0, total_assets_prior - current_assets_prior - ppe_prior)
    aqi_curr = nca_curr / total_assets_curr if total_assets_curr > 0 else 0
    aqi_prior = nca_prior / total_assets_prior if total_assets_prior > 0 else 0
    aqi = aqi_curr / aqi_prior if aqi_prior > 0 else 1.0
    
    # 4. SGI (Sales Growth Index)
    sgi = revenue_curr / revenue_prior if revenue_prior > 0 else 1.0
    
    # 5. DEPI (Depreciation Index)
    depr_rate_prior = depreciation_prior / (depreciation_prior + ppe_prior)
    depr_rate_curr = depreciation_curr / (depreciation_curr + ppe_curr) if (depreciation_curr + ppe_curr) > 0 else 0
    depi = depr_rate_prior / depr_rate_curr if depr_rate_curr > 0 else 1.0
    
    # 6. SGAI (SG&A Index)
    sga_ratio_curr = sga_curr / revenue_curr if revenue_curr > 0 else 0
    sga_ratio_prior = sga_prior / revenue_prior if revenue_prior > 0 else 0
    sgai = sga_ratio_curr / sga_ratio_prior if sga_ratio_prior > 0 else 1.0
    
    # 7. TATA (Total Accruals to Total Assets)
    working_capital_change = ((current_assets_curr - current_liabilities_curr) - 
                             (current_assets_prior - current_liabilities_curr))
    total_accruals = net_income_curr - cfo_curr
    tata = total_accruals / total_assets_curr if total_assets_curr > 0 else 0
    
    # 8. LVGI (Leverage Index)
    leverage_curr = (long_term_debt_curr + current_liabilities_curr) / total_assets_curr if total_assets_curr > 0 else 0
    leverage_prior = (long_term_debt_prior + current_liabilities_curr) / total_assets_prior if total_assets_prior > 0 else 0
    lvgi = leverage_curr / leverage_prior if leverage_prior > 0 else 1.0
    
    return {
        'dsri': dsri,
        'gmi': gmi,
        'aqi': aqi,
        'sgi': sgi,
        'depi': depi,
        'sgai': sgai,
        'tata': tata,
        'lvgi': lvgi
    }

def analyze_earnings_quality(ticker: str) -> Dict:
    """
    Comprehensive earnings quality analysis with all three metrics
    """
    ticker = ticker.upper()
    
    try:
        # Fetch data using yfinance
        stock = yf.Ticker(ticker)
        
        # Get financials
        income_stmt = stock.financials.T  # Transpose to have dates as rows
        balance_sheet = stock.balance_sheet.T
        cashflow = stock.cashflow.T
        info = stock.info
        
        if income_stmt.empty or balance_sheet.empty or cashflow.empty:
            return {
                "error": f"No historical financial data available for {ticker}",
                "ticker": ticker
            }
        
        # Sort by date (most recent first)
        income_stmt = income_stmt.sort_index(ascending=False)
        balance_sheet = balance_sheet.sort_index(ascending=False)
        cashflow = cashflow.sort_index(ascending=False)
        
        # ===== MOST RECENT PERIOD (for Accruals Ratio and Altman Z-Score) =====
        current_period = income_stmt.index[0].strftime('%Y-%m-%d')
        
        net_income = safe_get_value(income_stmt.iloc[0].get('Net Income', 0))
        revenue = safe_get_value(income_stmt.iloc[0].get('Total Revenue', 0))
        cogs = safe_get_value(income_stmt.iloc[0].get('Cost Of Revenue', 0))
        gross_profit = safe_get_value(income_stmt.iloc[0].get('Gross Profit', 0))
        ebit = safe_get_value(income_stmt.iloc[0].get('EBIT', gross_profit))
        
        # Balance sheet (most recent)
        try:
            bs_curr = balance_sheet.loc[income_stmt.index[0]]
        except:
            bs_curr = balance_sheet.iloc[0]
        
        total_assets = safe_get_value(bs_curr.get('Total Assets', 0))
        current_assets = safe_get_value(bs_curr.get('Current Assets', 0))
        current_liabilities = safe_get_value(bs_curr.get('Current Liabilities', 0))
        total_liabilities = safe_get_value(bs_curr.get('Total Liabilities Net Minority Interest', 0))
        retained_earnings = safe_get_value(bs_curr.get('Retained Earnings', 0))
        receivables = safe_get_value(bs_curr.get('Accounts Receivable', bs_curr.get('Net Receivables', 0)))
        ppe = safe_get_value(bs_curr.get('Net PPE', bs_curr.get('Property Plant Equipment', 0)))
        long_term_debt = safe_get_value(bs_curr.get('Long Term Debt', 0))
        
        # Cash flow (most recent)
        try:
            cf_curr = cashflow.loc[income_stmt.index[0]]
        except:
            cf_curr = cashflow.iloc[0]
        
        operating_cash_flow = safe_get_value(cf_curr.get('Operating Cash Flow', 0))
        depreciation = safe_get_value(cf_curr.get('Depreciation And Amortization', 0))
        
        # Get SG&A from operating expenses
        sga = safe_get_value(income_stmt.iloc[0].get('Selling General And Administrative', 
                                                       income_stmt.iloc[0].get('Operating Expense', 0)))
        
        # Market cap
        market_cap = safe_get_value(info.get('marketCap', 0))
        
        # ===== 1. ACCRUALS RATIO =====
        accruals_ratio = calculate_accruals_ratio(net_income, operating_cash_flow, total_assets)
        
        accruals_flag = "HIGH RISK" if accruals_ratio > 0.1 else "MODERATE" if accruals_ratio > 0.05 else "GOOD"
        accruals_interpretation = (
            "High positive accruals suggest potential earnings manipulation" if accruals_ratio > 0.1
            else "Moderate accruals - monitor trend" if accruals_ratio > 0.05
            else "Low accruals indicate high earnings quality"
        )
        
        # ===== 2. BENEISH M-SCORE (requires 2 periods) =====
        m_score_result = None
        beneish_variables = None
        
        if len(income_stmt) >= 2:
            # Current period data
            current_data = {
                'receivables': receivables,
                'revenue': revenue,
                'cogs': cogs,
                'current_assets': current_assets,
                'ppe': ppe,
                'total_assets': total_assets,
                'depreciation': depreciation,
                'sga': sga,
                'net_income': net_income,
                'cfo': operating_cash_flow,
                'current_liabilities': current_liabilities,
                'long_term_debt': long_term_debt
            }
            
            # Prior period data
            prior_period = income_stmt.index[1].strftime('%Y-%m-%d')
            
            net_income_prior = safe_get_value(income_stmt.iloc[1].get('Net Income', 0))
            revenue_prior = safe_get_value(income_stmt.iloc[1].get('Total Revenue', 0))
            cogs_prior = safe_get_value(income_stmt.iloc[1].get('Cost Of Revenue', 0))
            
            try:
                bs_prior = balance_sheet.loc[income_stmt.index[1]]
            except:
                bs_prior = balance_sheet.iloc[1]
            
            total_assets_prior = safe_get_value(bs_prior.get('Total Assets', 1))
            current_assets_prior = safe_get_value(bs_prior.get('Current Assets', 1))
            current_liabilities_prior = safe_get_value(bs_prior.get('Current Liabilities', 0))
            receivables_prior = safe_get_value(bs_prior.get('Accounts Receivable', bs_prior.get('Net Receivables', 1)))
            ppe_prior = safe_get_value(bs_prior.get('Net PPE', bs_prior.get('Property Plant Equipment', 1)))
            long_term_debt_prior = safe_get_value(bs_prior.get('Long Term Debt', 0))
            
            try:
                cf_prior = cashflow.loc[income_stmt.index[1]]
            except:
                cf_prior = cashflow.iloc[1]
            
            cfo_prior = safe_get_value(cf_prior.get('Operating Cash Flow', 0))
            depreciation_prior = safe_get_value(cf_prior.get('Depreciation And Amortization', 1))
            
            sga_prior = safe_get_value(income_stmt.iloc[1].get('Selling General And Administrative',
                                                                income_stmt.iloc[1].get('Operating Expense', 1)))
            
            prior_data = {
                'receivables': receivables_prior,
                'revenue': revenue_prior,
                'cogs': cogs_prior,
                'current_assets': current_assets_prior,
                'ppe': ppe_prior,
                'total_assets': total_assets_prior,
                'depreciation': depreciation_prior,
                'sga': sga_prior,
                'net_income': net_income_prior,
                'cfo': cfo_prior,
                'current_liabilities': current_liabilities_prior,
                'long_term_debt': long_term_debt_prior
            }
            
            beneish_variables = calculate_beneish_variables(current_data, prior_data)
            m_score = calculate_beneish_m_score(beneish_variables)
            
            m_score_flag = "LIKELY MANIPULATOR" if m_score > -2.22 else "UNLIKELY MANIPULATOR"
            m_score_interpretation = (
                f"M-Score of {m_score:.2f} suggests likely earnings manipulation" if m_score > -2.22
                else f"M-Score of {m_score:.2f} suggests earnings are unlikely manipulated"
            )
            
            m_score_result = {
                "m_score": round(m_score, 3),
                "threshold": -2.22,
                "flag": m_score_flag,
                "interpretation": m_score_interpretation,
                "variables": {k: round(v, 3) for k, v in beneish_variables.items()}
            }
        
        # ===== 3. ALTMAN Z-SCORE =====
        working_capital = current_assets - current_liabilities
        
        z_score = calculate_altman_z_score(
            working_capital, retained_earnings, ebit,
            market_cap, total_liabilities, revenue, total_assets
        )
        
        if z_score > 2.99:
            z_flag = "SAFE ZONE"
            z_interpretation = "Low bankruptcy risk — financially healthy"
        elif z_score > 1.81:
            z_flag = "GREY ZONE"
            z_interpretation = "Moderate distress risk — monitor closely"
        else:
            z_flag = "DISTRESS ZONE"
            z_interpretation = "High bankruptcy risk — significant financial distress"
        
        # ===== BUILD RESPONSE =====
        result = {
            "ticker": ticker,
            "company_name": info.get('longName', ticker),
            "period": current_period,
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            
            "accruals_ratio": {
                "value": round(accruals_ratio, 4),
                "flag": accruals_flag,
                "interpretation": accruals_interpretation,
                "components": {
                    "net_income": f"${net_income:,.0f}",
                    "operating_cash_flow": f"${operating_cash_flow:,.0f}",
                    "total_assets": f"${total_assets:,.0f}"
                }
            },
            
            "altman_z_score": {
                "z_score": round(z_score, 3),
                "flag": z_flag,
                "interpretation": z_interpretation,
                "zones": {
                    "safe": "> 2.99",
                    "grey": "1.81 - 2.99",
                    "distress": "< 1.81"
                }
            },
            
            "summary": {
                "overall_risk": "HIGH" if (accruals_ratio > 0.1 or z_score < 1.81 or (m_score_result and m_score_result['m_score'] > -2.22)) 
                                else "MODERATE" if (accruals_ratio > 0.05 or z_score < 2.99)
                                else "LOW",
                "earnings_quality": accruals_flag,
                "distress_risk": z_flag,
                "manipulation_risk": m_score_result['flag'] if m_score_result else "N/A (requires 2 periods)"
            }
        }
        
        if m_score_result:
            result["beneish_m_score"] = m_score_result
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "ticker": ticker,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }

def get_accruals_trend(ticker: str, periods: int = 4) -> Dict:
    """Get accruals ratio trend over multiple periods"""
    ticker = ticker.upper()
    
    try:
        stock = yf.Ticker(ticker)
        income_stmt = stock.financials.T.sort_index(ascending=False)
        balance_sheet = stock.balance_sheet.T.sort_index(ascending=False)
        cashflow = stock.cashflow.T.sort_index(ascending=False)
        
        if income_stmt.empty:
            return {"error": f"No data for {ticker}"}
        
        trend = []
        num_periods = min(periods, len(income_stmt))
        
        for i in range(num_periods):
            period_date = income_stmt.index[i].strftime('%Y-%m-%d')
            
            net_income = safe_get_value(income_stmt.iloc[i].get('Net Income', 0))
            
            try:
                bs = balance_sheet.loc[income_stmt.index[i]]
            except:
                bs = balance_sheet.iloc[i] if i < len(balance_sheet) else None
            
            if bs is not None:
                total_assets = safe_get_value(bs.get('Total Assets', 0))
            else:
                total_assets = 0
            
            try:
                cf = cashflow.loc[income_stmt.index[i]]
            except:
                cf = cashflow.iloc[i] if i < len(cashflow) else None
            
            if cf is not None:
                operating_cash_flow = safe_get_value(cf.get('Operating Cash Flow', 0))
            else:
                operating_cash_flow = 0
            
            accruals_ratio = calculate_accruals_ratio(net_income, operating_cash_flow, total_assets)
            
            trend.append({
                "period": period_date,
                "accruals_ratio": round(accruals_ratio, 4),
                "net_income": f"${net_income:,.0f}",
                "operating_cash_flow": f"${operating_cash_flow:,.0f}",
                "flag": "HIGH RISK" if accruals_ratio > 0.1 else "MODERATE" if accruals_ratio > 0.05 else "GOOD"
            })
        
        return {
            "ticker": ticker,
            "periods_analyzed": num_periods,
            "trend": trend,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
        
    except Exception as e:
        return {"error": str(e), "ticker": ticker}

def get_fraud_indicators(ticker: str) -> Dict:
    """Quick fraud/distress red flags summary"""
    ticker = ticker.upper()
    
    try:
        result = analyze_earnings_quality(ticker)
        
        if "error" in result:
            return result
        
        red_flags = []
        
        # Accruals check
        if result['accruals_ratio']['flag'] == "HIGH RISK":
            red_flags.append("⚠️ High accruals ratio (>0.1) — potential earnings manipulation")
        
        # Z-Score check
        if result['altman_z_score']['flag'] == "DISTRESS ZONE":
            red_flags.append("🚨 Altman Z-Score in distress zone — high bankruptcy risk")
        elif result['altman_z_score']['flag'] == "GREY ZONE":
            red_flags.append("⚠️ Altman Z-Score in grey zone — moderate distress risk")
        
        # Beneish check
        if 'beneish_m_score' in result:
            if result['beneish_m_score']['flag'] == "LIKELY MANIPULATOR":
                red_flags.append("🚨 Beneish M-Score suggests likely earnings manipulation")
        
        return {
            "ticker": ticker,
            "overall_risk": result['summary']['overall_risk'],
            "red_flags": red_flags if red_flags else ["✅ No major red flags detected"],
            "metrics": {
                "accruals_ratio": result['accruals_ratio']['value'],
                "altman_z_score": result['altman_z_score']['z_score'],
                "beneish_m_score": result.get('beneish_m_score', {}).get('m_score', 'N/A')
            },
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
        
    except Exception as e:
        return {"error": str(e), "ticker": ticker}

def main():
    """CLI entry point"""
    if len(sys.argv) < 3:
        print(json.dumps({
            "error": "Usage: python earnings_quality.py <command> <ticker>",
            "commands": {
                "earnings-quality": "Comprehensive earnings quality analysis (all 3 metrics)",
                "accruals-trend": "Accruals ratio trend over 4 periods",
                "fraud-indicators": "Quick red flags summary"
            }
        }, indent=2))
        sys.exit(1)
    
    command = sys.argv[1].lower()
    ticker = sys.argv[2].upper()
    
    # Map CLI commands to internal actions
    if command in ["analyze", "earnings-quality"]:
        result = analyze_earnings_quality(ticker)
    elif command == "accruals-trend":
        result = get_accruals_trend(ticker)
    elif command == "fraud-indicators":
        result = get_fraud_indicators(ticker)
    else:
        result = {
            "error": f"Unknown command: {command}",
            "available": ["earnings-quality", "accruals-trend", "fraud-indicators"]
        }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
