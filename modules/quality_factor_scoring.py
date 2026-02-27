#!/usr/bin/env python3
"""
Quality Factor Scoring Module

Scores stocks on quality metrics:
- ROE (Return on Equity)
- Leverage (Debt/Equity)
- Accruals (Cash flow vs earnings)
- Earnings Stability (CV of earnings)
- Profitability (Gross margin, operating margin)

Data sources: Yahoo Finance, SEC XBRL
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')


def calculate_roe(ticker: str) -> Optional[float]:
    """Calculate Return on Equity (ROE)."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        roe = info.get('returnOnEquity')
        return roe * 100 if roe else None
    except:
        return None


def calculate_leverage(ticker: str) -> Optional[float]:
    """Calculate Debt-to-Equity ratio."""
    try:
        stock = yf.Ticker(ticker)
        balance_sheet = stock.balance_sheet
        
        if balance_sheet.empty:
            return None
        
        # Get most recent data
        latest = balance_sheet.iloc[:, 0]
        total_debt = latest.get('Total Debt', 0)
        stockholder_equity = latest.get('Stockholders Equity', 1)
        
        if stockholder_equity == 0:
            return None
        
        return total_debt / stockholder_equity
    except:
        return None


def calculate_accruals_ratio(ticker: str) -> Optional[float]:
    """
    Calculate Accruals Ratio: (Net Income - Operating Cash Flow) / Total Assets
    Lower is better (indicates higher quality earnings).
    """
    try:
        stock = yf.Ticker(ticker)
        financials = stock.financials
        cashflow = stock.cashflow
        balance_sheet = stock.balance_sheet
        
        if financials.empty or cashflow.empty or balance_sheet.empty:
            return None
        
        # Most recent period
        net_income = financials.loc['Net Income', financials.columns[0]]
        operating_cf = cashflow.loc['Operating Cash Flow', cashflow.columns[0]]
        total_assets = balance_sheet.loc['Total Assets', balance_sheet.columns[0]]
        
        if total_assets == 0:
            return None
        
        accruals = (net_income - operating_cf) / total_assets
        return accruals
    except:
        return None


def calculate_earnings_stability(ticker: str, periods: int = 4) -> Optional[float]:
    """
    Calculate Coefficient of Variation (CV) of quarterly earnings.
    Lower CV = more stable earnings.
    """
    try:
        stock = yf.Ticker(ticker)
        quarterly_financials = stock.quarterly_financials
        
        if quarterly_financials.empty:
            return None
        
        if 'Net Income' not in quarterly_financials.index:
            return None
        
        earnings = quarterly_financials.loc['Net Income'].head(periods).values
        
        if len(earnings) < 2:
            return None
        
        mean_earnings = np.mean(earnings)
        if mean_earnings == 0:
            return None
        
        std_earnings = np.std(earnings)
        cv = (std_earnings / abs(mean_earnings))
        
        return cv
    except:
        return None


def calculate_gross_margin(ticker: str) -> Optional[float]:
    """Calculate Gross Profit Margin."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        margin = info.get('grossMargins')
        return margin * 100 if margin else None
    except:
        return None


def calculate_operating_margin(ticker: str) -> Optional[float]:
    """Calculate Operating Margin."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        margin = info.get('operatingMargins')
        return margin * 100 if margin else None
    except:
        return None


def score_quality_factor(ticker: str) -> Dict:
    """
    Score a stock on quality factors (0-100 scale).
    
    Scoring:
    - ROE: Higher is better (normalize 0-30% → 0-100)
    - Leverage: Lower is better (normalize 0-2 → 100-0)
    - Accruals: Lower is better (normalize -0.1 to 0.1 → 100-0)
    - Earnings Stability: Lower CV is better (normalize 0-1 → 100-0)
    - Gross Margin: Higher is better (normalize 0-50% → 0-100)
    - Operating Margin: Higher is better (normalize 0-30% → 0-100)
    """
    
    roe = calculate_roe(ticker)
    leverage = calculate_leverage(ticker)
    accruals = calculate_accruals_ratio(ticker)
    earnings_stability = calculate_earnings_stability(ticker)
    gross_margin = calculate_gross_margin(ticker)
    operating_margin = calculate_operating_margin(ticker)
    
    scores = {}
    
    # ROE Score (0-30% → 0-100)
    if roe is not None:
        roe_score = min(100, max(0, (roe / 30) * 100))
        scores['roe'] = {'value': roe, 'score': roe_score}
    
    # Leverage Score (0-2 → 100-0, lower is better)
    if leverage is not None:
        leverage_score = max(0, 100 - (leverage / 2) * 100)
        scores['leverage'] = {'value': leverage, 'score': leverage_score}
    
    # Accruals Score (-0.1 to 0.1 → 100-0, lower is better)
    if accruals is not None:
        # Normalize: accruals at -0.1 = 100, at 0.1 = 0
        accruals_score = max(0, 100 - ((accruals + 0.1) / 0.2) * 100)
        scores['accruals'] = {'value': accruals, 'score': accruals_score}
    
    # Earnings Stability Score (CV 0-1 → 100-0, lower is better)
    if earnings_stability is not None:
        stability_score = max(0, 100 - (earnings_stability * 100))
        scores['earnings_stability'] = {'value': earnings_stability, 'score': stability_score}
    
    # Gross Margin Score (0-50% → 0-100)
    if gross_margin is not None:
        gross_margin_score = min(100, max(0, (gross_margin / 50) * 100))
        scores['gross_margin'] = {'value': gross_margin, 'score': gross_margin_score}
    
    # Operating Margin Score (0-30% → 0-100)
    if operating_margin is not None:
        operating_margin_score = min(100, max(0, (operating_margin / 30) * 100))
        scores['operating_margin'] = {'value': operating_margin, 'score': operating_margin_score}
    
    # Composite Score (average of available scores)
    if scores:
        composite_score = np.mean([v['score'] for v in scores.values()])
    else:
        composite_score = None
    
    return {
        'ticker': ticker,
        'composite_score': composite_score,
        'components': scores
    }


def quality_screen(tickers: List[str], min_score: float = 60.0) -> pd.DataFrame:
    """
    Screen multiple tickers for quality.
    
    Args:
        tickers: List of ticker symbols
        min_score: Minimum composite quality score (0-100)
    
    Returns:
        DataFrame with quality scores, sorted by composite score
    """
    results = []
    
    for ticker in tickers:
        print(f"Analyzing {ticker}...", end=' ')
        score_data = score_quality_factor(ticker)
        
        if score_data['composite_score'] is not None:
            row = {
                'ticker': ticker,
                'composite_score': score_data['composite_score']
            }
            
            for component, data in score_data['components'].items():
                row[f'{component}_value'] = data['value']
                row[f'{component}_score'] = data['score']
            
            results.append(row)
            print(f"Score: {score_data['composite_score']:.1f}")
        else:
            print("No data")
    
    if not results:
        return pd.DataFrame()
    
    df = pd.DataFrame(results)
    df = df[df['composite_score'] >= min_score]
    df = df.sort_values('composite_score', ascending=False).reset_index(drop=True)
    
    return df


def cli_quality_score(ticker: str):
    """CLI: Score a single ticker on quality factors."""
    result = score_quality_factor(ticker)
    
    print(f"\n{'='*60}")
    print(f"Quality Factor Score: {ticker}")
    print(f"{'='*60}")
    
    if result['composite_score'] is None:
        print("❌ No quality data available")
        return
    
    print(f"\n🎯 Composite Score: {result['composite_score']:.1f}/100")
    print(f"\n📊 Component Scores:")
    print(f"{'─'*60}")
    
    for component, data in result['components'].items():
        score = data['score']
        value = data['value']
        
        # Format value based on component
        if component == 'roe':
            value_str = f"{value:.2f}%"
            label = "ROE"
        elif component == 'leverage':
            value_str = f"{value:.2f}x"
            label = "Debt/Equity"
        elif component == 'accruals':
            value_str = f"{value:.4f}"
            label = "Accruals Ratio"
        elif component == 'earnings_stability':
            value_str = f"{value:.4f}"
            label = "Earnings CV"
        elif component == 'gross_margin':
            value_str = f"{value:.2f}%"
            label = "Gross Margin"
        elif component == 'operating_margin':
            value_str = f"{value:.2f}%"
            label = "Operating Margin"
        else:
            value_str = f"{value:.2f}"
            label = component.replace('_', ' ').title()
        
        # Quality indicator
        if score >= 80:
            indicator = "🟢"
        elif score >= 60:
            indicator = "🟡"
        else:
            indicator = "🔴"
        
        print(f"{indicator} {label:20s}: {value_str:10s} → Score: {score:5.1f}/100")
    
    print(f"{'─'*60}")
    
    # Overall assessment
    if result['composite_score'] >= 80:
        print("\n✅ HIGH QUALITY: Strong fundamentals across the board")
    elif result['composite_score'] >= 60:
        print("\n⚠️  MODERATE QUALITY: Some strengths, some concerns")
    else:
        print("\n❌ LOW QUALITY: Weak fundamentals, avoid")


def cli_quality_screen(tickers: str, min_score: float = 60.0):
    """CLI: Screen multiple tickers for quality."""
    ticker_list = [t.strip().upper() for t in tickers.split(',')]
    
    print(f"\n{'='*60}")
    print(f"Quality Factor Screening")
    print(f"Tickers: {', '.join(ticker_list)}")
    print(f"Min Score: {min_score}/100")
    print(f"{'='*60}\n")
    
    df = quality_screen(ticker_list, min_score)
    
    if df.empty:
        print("\n❌ No tickers passed the quality screen")
        return
    
    print(f"\n✅ {len(df)} tickers passed quality screen:\n")
    
    # Display results
    display_cols = ['ticker', 'composite_score']
    
    # Add available component scores
    for col in ['roe_score', 'leverage_score', 'accruals_score', 
                'earnings_stability_score', 'gross_margin_score', 'operating_margin_score']:
        if col in df.columns:
            display_cols.append(col)
    
    df_display = df[display_cols].copy()
    
    # Rename columns for display
    df_display.columns = [col.replace('_score', '').replace('_', ' ').title() 
                          for col in df_display.columns]
    
    print(df_display.to_string(index=False))
    
    print(f"\n{'='*60}")
    print(f"Top Pick: {df.iloc[0]['ticker']} (Score: {df.iloc[0]['composite_score']:.1f})")
    print(f"{'='*60}")


if __name__ == "__main__":
    import sys
    
    # When called via CLI dispatcher, argv[1] is the command name, argv[2+] are args
    # When called directly, argv[1] is the first arg
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single ticker: python quality_factor_scoring.py quality-score AAPL")
        print("  Screen multiple: python quality_factor_scoring.py quality-screen 'AAPL,MSFT,GOOGL' --min-score 70")
        sys.exit(1)
    
    # Determine if called via CLI dispatcher or directly
    command = sys.argv[1]
    
    if command in ['quality-score', 'quality-screen']:
        # Called via CLI dispatcher
        if len(sys.argv) < 3:
            print(f"Usage: python cli.py {command} <ticker(s)> [--min-score N]")
            sys.exit(1)
        
        tickers_arg = sys.argv[2]
        start_idx = 3
    else:
        # Called directly
        tickers_arg = sys.argv[1]
        start_idx = 2
    
    if ',' in tickers_arg or command == 'quality-screen':
        # Multiple tickers - screen mode
        min_score = 60.0
        if '--min-score' in sys.argv:
            idx = sys.argv.index('--min-score')
            min_score = float(sys.argv[idx + 1])
        
        cli_quality_screen(tickers_arg, min_score)
    else:
        # Single ticker - score mode
        cli_quality_score(tickers_arg)
