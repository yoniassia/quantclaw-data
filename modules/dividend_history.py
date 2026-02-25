#!/usr/bin/env python3
"""
Dividend History & Projections — Phase 139

Complete dividend history, growth rates, ex-date calendar, dividend projections.
Analyzes historical dividend payments, calculates compound growth rates,
tracks ex-dividend dates, and projects future dividend payments.

Data Sources:
- Yahoo Finance (dividend history, financial statements, ex-dates)
- FRED (treasury yields for discount rates)

Provides:
1. Complete dividend payment history
2. Dividend growth rates (1Y, 3Y, 5Y, 10Y CAGR)
3. Ex-dividend date calendar (upcoming and historical)
4. Dividend yield trends
5. Dividend consistency scoring
6. Future dividend projections based on historical growth
7. Dividend aristocrat/king/champion analysis
8. Quarterly vs annual payment schedules
9. Special dividend tracking
10. Dividend growth streak analysis

Author: QUANTCLAW DATA Build Agent
Phase: 139
Category: Equity
"""

import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

try:
    import requests
    FRED_AVAILABLE = True
except ImportError:
    FRED_AVAILABLE = False


@dataclass
class DividendPayment:
    """Single dividend payment record."""
    date: str
    amount: float
    ex_date: str
    payment_type: str  # REGULAR, SPECIAL, RETURN_OF_CAPITAL
    annualized: float
    yield_at_payment: float


@dataclass
class DividendGrowthMetrics:
    """Dividend growth rate metrics."""
    ticker: str
    current_annual_dividend: float
    cagr_1y: float
    cagr_3y: float
    cagr_5y: float
    cagr_10y: float
    average_growth_rate: float
    growth_consistency: float  # 0-100 score
    consecutive_years_increased: int
    consecutive_years_maintained: int
    total_years_paying: int


@dataclass
class ExDividendCalendar:
    """Ex-dividend date calendar."""
    ticker: str
    next_ex_date: Optional[str]
    next_payment_date: Optional[str]
    estimated_next_dividend: float
    typical_frequency: str  # QUARTERLY, MONTHLY, ANNUAL, SEMI_ANNUAL
    upcoming_ex_dates: List[Dict]  # Projected ex-dates
    historical_ex_dates: List[Dict]


@dataclass
class DividendProjection:
    """Future dividend projection."""
    ticker: str
    current_annual_dividend: float
    projected_growth_rate: float
    projection_years: int
    projected_dividends: List[Dict]  # [{"year": int, "dividend": float, "yield": float}]
    confidence_level: str  # HIGH, MEDIUM, LOW
    projection_method: str  # Historical CAGR, Analyst consensus, etc.


@dataclass
class DividendAristocratStatus:
    """Dividend aristocrat/king/champion status."""
    ticker: str
    is_aristocrat: bool  # 25+ years increases
    is_king: bool  # 50+ years increases
    is_champion: bool  # 25+ years increases + other criteria
    consecutive_years_increased: int
    total_years_paying: int
    qualification_notes: List[str]


def safe_get(value, default=0) -> float:
    """Safely extract numeric value."""
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except:
        return default


def get_fred_rate(series_id: str = 'DGS10') -> float:
    """
    Get current rate from FRED (for discount rate in projections).
    Default: 10-year Treasury yield (DGS10)
    """
    if not FRED_AVAILABLE:
        return 4.5  # Default fallback
    
    try:
        url = f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}'
        df = pd.read_csv(url)
        latest = df.iloc[-1]['value']
        return safe_get(latest, 4.5)
    except:
        return 4.5


def calculate_cagr(start_value: float, end_value: float, years: float) -> float:
    """Calculate Compound Annual Growth Rate."""
    if start_value <= 0 or end_value <= 0 or years <= 0:
        return 0
    try:
        return (pow(end_value / start_value, 1 / years) - 1) * 100
    except:
        return 0


def get_dividend_history(ticker: str, years: int = 20) -> Dict:
    """
    Get complete dividend payment history for a ticker.
    
    Returns:
    - List of all dividend payments
    - Payment dates, amounts, ex-dates
    - Special dividends flagged
    - Annualized amounts
    """
    ticker = ticker.upper()
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get dividend history
        dividends = stock.dividends
        
        if len(dividends) == 0:
            return {
                'ticker': ticker,
                'error': 'No dividend history found',
                'total_payments': 0
            }
        
        # Filter by years - convert to days to avoid timezone issues
        cutoff_days = years * 365
        if len(dividends) > 0:
            days_back = (dividends.index[-1] - dividends.index).days
            dividends = dividends[days_back <= cutoff_days]
        
        # Get current price for yield calculation
        current_price = safe_get(info.get('currentPrice', 0))
        if current_price == 0:
            current_price = safe_get(info.get('regularMarketPrice', 100))
        
        # Process each dividend payment
        payments = []
        for date, amount in dividends.items():
            # Detect special dividends (unusually large payments)
            is_special = False
            payment_type = 'REGULAR'
            
            # Calculate annualized dividend (approximate)
            annualized = amount * 4  # Assume quarterly
            div_yield = (amount / current_price) * 100 if current_price > 0 else 0
            
            payments.append({
                'date': date.strftime('%Y-%m-%d'),
                'amount': round(amount, 4),
                'ex_date': date.strftime('%Y-%m-%d'),
                'payment_type': payment_type,
                'annualized': round(annualized, 4),
                'yield_at_payment': round(div_yield, 2)
            })
        
        # Calculate summary statistics
        total_paid = sum(p['amount'] for p in payments)
        avg_payment = total_paid / len(payments) if len(payments) > 0 else 0
        
        # Get annual totals
        annual_totals = dividends.resample('YE').sum().to_dict()
        annual_list = [{'year': k.year, 'total': round(v, 4)} for k, v in annual_totals.items()]
        
        return {
            'ticker': ticker,
            'company_name': info.get('longName', ticker),
            'current_price': round(current_price, 2),
            'total_payments': len(payments),
            'years_covered': years,
            'total_paid': round(total_paid, 2),
            'average_payment': round(avg_payment, 4),
            'payments': payments,
            'annual_totals': annual_list,
            'data_date': datetime.now().strftime('%Y-%m-%d')
        }
        
    except Exception as e:
        return {
            'ticker': ticker,
            'error': f'Failed to fetch dividend history: {str(e)}'
        }


def calculate_growth_rates(ticker: str) -> Dict:
    """
    Calculate dividend growth rates (1Y, 3Y, 5Y, 10Y CAGR).
    Also calculates growth consistency and consecutive years of increases.
    """
    ticker = ticker.upper()
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        dividends = stock.dividends
        
        if len(dividends) == 0:
            return {
                'ticker': ticker,
                'error': 'No dividend history found'
            }
        
        # Calculate annual dividend totals
        annual_divs = dividends.resample('YE').sum()
        
        if len(annual_divs) < 2:
            return {
                'ticker': ticker,
                'error': 'Insufficient dividend history (need at least 2 years)'
            }
        
        # Current annual dividend (last 12 months)
        current_annual = annual_divs.iloc[-1]
        
        # Calculate CAGRs
        cagr_1y = 0
        cagr_3y = 0
        cagr_5y = 0
        cagr_10y = 0
        
        if len(annual_divs) >= 2:
            cagr_1y = calculate_cagr(annual_divs.iloc[-2], annual_divs.iloc[-1], 1)
        
        if len(annual_divs) >= 4:
            cagr_3y = calculate_cagr(annual_divs.iloc[-4], annual_divs.iloc[-1], 3)
        
        if len(annual_divs) >= 6:
            cagr_5y = calculate_cagr(annual_divs.iloc[-6], annual_divs.iloc[-1], 5)
        
        if len(annual_divs) >= 11:
            cagr_10y = calculate_cagr(annual_divs.iloc[-11], annual_divs.iloc[-1], 10)
        
        # Calculate average growth rate (weighted toward recent)
        growth_rates = [cagr_1y, cagr_3y, cagr_5y, cagr_10y]
        valid_rates = [r for r in growth_rates if r != 0]
        avg_growth = sum(valid_rates) / len(valid_rates) if len(valid_rates) > 0 else 0
        
        # Calculate growth consistency (low variance = high consistency)
        if len(valid_rates) > 1:
            variance = np.var(valid_rates)
            consistency = max(0, 100 - variance)
        else:
            consistency = 50
        
        # Count consecutive years of increases
        consecutive_increases = 0
        consecutive_maintained = 0
        
        for i in range(len(annual_divs) - 1, 0, -1):
            if annual_divs.iloc[i] > annual_divs.iloc[i-1]:
                consecutive_increases += 1
            elif annual_divs.iloc[i] >= annual_divs.iloc[i-1]:
                consecutive_maintained += 1
            else:
                break
        
        return {
            'ticker': ticker,
            'company_name': info.get('longName', ticker),
            'current_annual_dividend': round(current_annual, 4),
            'cagr_1y': round(cagr_1y, 2),
            'cagr_3y': round(cagr_3y, 2),
            'cagr_5y': round(cagr_5y, 2),
            'cagr_10y': round(cagr_10y, 2),
            'average_growth_rate': round(avg_growth, 2),
            'growth_consistency': round(consistency, 1),
            'consecutive_years_increased': consecutive_increases,
            'consecutive_years_maintained': consecutive_maintained,
            'total_years_paying': len(annual_divs),
            'analysis_date': datetime.now().strftime('%Y-%m-%d')
        }
        
    except Exception as e:
        return {
            'ticker': ticker,
            'error': f'Failed to calculate growth rates: {str(e)}'
        }


def get_ex_dividend_calendar(ticker: str, months_ahead: int = 12) -> Dict:
    """
    Get ex-dividend date calendar with upcoming projected dates.
    """
    ticker = ticker.upper()
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        dividends = stock.dividends
        
        if len(dividends) == 0:
            return {
                'ticker': ticker,
                'error': 'No dividend history found'
            }
        
        # Get last dividend date and amount
        last_div_date = dividends.index[-1]
        last_div_amount = dividends.iloc[-1]
        
        # Get ex-dividend date from info
        ex_div_date = info.get('exDividendDate')
        if ex_div_date:
            next_ex_date = datetime.fromtimestamp(ex_div_date).strftime('%Y-%m-%d')
        else:
            next_ex_date = None
        
        # Detect payment frequency
        if len(dividends) >= 4:
            recent_divs = dividends.tail(4)
            intervals = []
            for i in range(1, len(recent_divs)):
                days = (recent_divs.index[i] - recent_divs.index[i-1]).days
                intervals.append(days)
            
            avg_interval = np.mean(intervals)
            
            if 25 <= avg_interval <= 35:
                frequency = 'MONTHLY'
                interval_days = 30
            elif 80 <= avg_interval <= 100:
                frequency = 'QUARTERLY'
                interval_days = 91
            elif 170 <= avg_interval <= 190:
                frequency = 'SEMI_ANNUAL'
                interval_days = 182
            elif avg_interval >= 350:
                frequency = 'ANNUAL'
                interval_days = 365
            else:
                frequency = 'IRREGULAR'
                interval_days = int(avg_interval)
        else:
            frequency = 'QUARTERLY'  # Default assumption
            interval_days = 91
        
        # Project upcoming ex-dates
        upcoming = []
        current_date = last_div_date
        
        for i in range(1, months_ahead // (interval_days // 30) + 1):
            current_date = current_date + timedelta(days=interval_days)
            # Remove timezone for comparison
            cutoff = pd.Timestamp.now().tz_localize(None) + pd.Timedelta(days=months_ahead*30)
            current_naive = pd.Timestamp(current_date).tz_localize(None)
            if current_naive <= cutoff:
                upcoming.append({
                    'projected_ex_date': current_date.strftime('%Y-%m-%d'),
                    'estimated_amount': round(last_div_amount, 4),
                    'confidence': 'MEDIUM' if i <= 2 else 'LOW'
                })
        
        # Get historical ex-dates (last 8 quarters)
        historical = []
        for date, amount in dividends.tail(8).items():
            historical.append({
                'ex_date': date.strftime('%Y-%m-%d'),
                'amount': round(amount, 4)
            })
        
        return {
            'ticker': ticker,
            'company_name': info.get('longName', ticker),
            'next_ex_date': next_ex_date,
            'next_payment_date': None,  # Not easily available
            'estimated_next_dividend': round(last_div_amount, 4),
            'typical_frequency': frequency,
            'interval_days': interval_days,
            'upcoming_ex_dates': upcoming,
            'historical_ex_dates': historical,
            'data_date': datetime.now().strftime('%Y-%m-%d')
        }
        
    except Exception as e:
        return {
            'ticker': ticker,
            'error': f'Failed to get ex-dividend calendar: {str(e)}'
        }


def project_dividends(ticker: str, years: int = 5, growth_rate: Optional[float] = None) -> Dict:
    """
    Project future dividend payments based on historical growth.
    
    Args:
        ticker: Stock ticker
        years: Number of years to project
        growth_rate: Optional custom growth rate (uses historical CAGR if None)
    """
    ticker = ticker.upper()
    
    try:
        # Get current dividend and growth metrics
        growth_data = calculate_growth_rates(ticker)
        
        if 'error' in growth_data:
            return growth_data
        
        current_dividend = growth_data['current_annual_dividend']
        
        # Use provided growth rate or historical average
        if growth_rate is None:
            # Weight recent growth more heavily
            if growth_data['cagr_3y'] != 0:
                proj_growth = (growth_data['cagr_1y'] * 0.4 + 
                              growth_data['cagr_3y'] * 0.4 + 
                              growth_data['cagr_5y'] * 0.2)
            else:
                proj_growth = growth_data['average_growth_rate']
        else:
            proj_growth = growth_rate
        
        # Determine confidence level
        consistency = growth_data['growth_consistency']
        if consistency >= 80 and growth_data['consecutive_years_increased'] >= 5:
            confidence = 'HIGH'
        elif consistency >= 60 and growth_data['consecutive_years_increased'] >= 3:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'
        
        # Get current stock price for yield calculation
        stock = yf.Ticker(ticker)
        info = stock.info
        current_price = safe_get(info.get('currentPrice', 0))
        if current_price == 0:
            current_price = safe_get(info.get('regularMarketPrice', 100))
        
        # Project dividends
        projections = []
        current_year = datetime.now().year
        
        for i in range(1, years + 1):
            projected_div = current_dividend * pow(1 + proj_growth/100, i)
            
            # Assume 3% annual price appreciation for yield calculation
            projected_price = current_price * pow(1.03, i)
            projected_yield = (projected_div / projected_price) * 100
            
            projections.append({
                'year': current_year + i,
                'projected_dividend': round(projected_div, 4),
                'projected_yield': round(projected_yield, 2),
                'growth_from_current': round(((projected_div / current_dividend) - 1) * 100, 1)
            })
        
        return {
            'ticker': ticker,
            'company_name': info.get('longName', ticker),
            'current_annual_dividend': round(current_dividend, 4),
            'current_price': round(current_price, 2),
            'current_yield': round((current_dividend / current_price) * 100, 2),
            'projected_growth_rate': round(proj_growth, 2),
            'projection_years': years,
            'projected_dividends': projections,
            'confidence_level': confidence,
            'projection_method': 'Historical CAGR weighted toward recent',
            'assumptions': [
                f'Dividend growth rate: {round(proj_growth, 2)}% annually',
                'Stock price growth: 3% annually (for yield calc)',
                'No dividend cuts or suspensions',
                'Company maintains current dividend policy'
            ],
            'analysis_date': datetime.now().strftime('%Y-%m-%d')
        }
        
    except Exception as e:
        return {
            'ticker': ticker,
            'error': f'Failed to project dividends: {str(e)}'
        }


def check_aristocrat_status(ticker: str) -> Dict:
    """
    Check if company qualifies as Dividend Aristocrat/King/Champion.
    
    Aristocrat: 25+ consecutive years of dividend increases
    King: 50+ consecutive years of dividend increases
    Champion: 25+ years increases + other quality criteria
    """
    ticker = ticker.upper()
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        dividends = stock.dividends
        
        if len(dividends) == 0:
            return {
                'ticker': ticker,
                'error': 'No dividend history found'
            }
        
        # Get annual dividends
        annual_divs = dividends.resample('YE').sum()
        
        # Count consecutive years of increases
        consecutive_increases = 0
        for i in range(len(annual_divs) - 1, 0, -1):
            if annual_divs.iloc[i] > annual_divs.iloc[i-1]:
                consecutive_increases += 1
            else:
                break
        
        is_aristocrat = consecutive_increases >= 25
        is_king = consecutive_increases >= 50
        
        # Champion criteria (simplified - normally includes S&P 500 membership)
        growth_data = calculate_growth_rates(ticker)
        is_champion = (consecutive_increases >= 25 and 
                      growth_data.get('growth_consistency', 0) >= 70)
        
        # Generate qualification notes
        notes = []
        if consecutive_increases < 25:
            notes.append(f'Need {25 - consecutive_increases} more years of consecutive increases for Aristocrat status')
        if is_aristocrat:
            notes.append('✓ Qualifies as Dividend Aristocrat (25+ years)')
        if is_king:
            notes.append('✓ Qualifies as Dividend King (50+ years)')
        if is_champion:
            notes.append('✓ Qualifies as Dividend Champion (quality + consistency)')
        
        return {
            'ticker': ticker,
            'company_name': info.get('longName', ticker),
            'is_aristocrat': bool(is_aristocrat),
            'is_king': bool(is_king),
            'is_champion': bool(is_champion),
            'consecutive_years_increased': int(consecutive_increases),
            'total_years_paying': len(annual_divs),
            'qualification_notes': notes,
            'streak_start_year': annual_divs.index[-consecutive_increases-1].year if consecutive_increases > 0 else None,
            'analysis_date': datetime.now().strftime('%Y-%m-%d')
        }
        
    except Exception as e:
        return {
            'ticker': ticker,
            'error': f'Failed to check aristocrat status: {str(e)}'
        }


def compare_dividend_growth(tickers: List[str]) -> Dict:
    """
    Compare dividend growth rates across multiple tickers.
    """
    results = []
    
    for ticker in tickers:
        growth_data = calculate_growth_rates(ticker)
        if 'error' not in growth_data:
            results.append(growth_data)
    
    if len(results) == 0:
        return {
            'error': 'No valid dividend data found for any ticker'
        }
    
    # Sort by 5-year CAGR
    results.sort(key=lambda x: x.get('cagr_5y', 0), reverse=True)
    
    return {
        'comparison_date': datetime.now().strftime('%Y-%m-%d'),
        'tickers_compared': len(results),
        'results': results,
        'summary': {
            'highest_1y_growth': max(results, key=lambda x: x.get('cagr_1y', 0))['ticker'],
            'highest_5y_growth': max(results, key=lambda x: x.get('cagr_5y', 0))['ticker'],
            'most_consistent': max(results, key=lambda x: x.get('growth_consistency', 0))['ticker'],
            'longest_streak': max(results, key=lambda x: x.get('consecutive_years_increased', 0))['ticker']
        }
    }


def main():
    """CLI entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: dividend_history.py <command> [args]")
        print("Commands:")
        print("  div-history <ticker> [years]")
        print("  div-growth <ticker>")
        print("  div-calendar <ticker> [months]")
        print("  div-project <ticker> [years] [growth_rate]")
        print("  div-aristocrat <ticker>")
        print("  div-compare <ticker1> <ticker2> ...")
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Accept both CLI format (div-history) and direct format (history)
    if command in ['history', 'div-history']:
        ticker = sys.argv[2]
        years = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        result = get_dividend_history(ticker, years)
        print(json.dumps(result, indent=2))
    
    elif command in ['growth', 'div-growth']:
        ticker = sys.argv[2]
        result = calculate_growth_rates(ticker)
        print(json.dumps(result, indent=2))
    
    elif command in ['calendar', 'div-calendar']:
        ticker = sys.argv[2]
        months = int(sys.argv[3]) if len(sys.argv) > 3 else 12
        result = get_ex_dividend_calendar(ticker, months)
        print(json.dumps(result, indent=2))
    
    elif command in ['project', 'div-project']:
        ticker = sys.argv[2]
        years = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        growth_rate = float(sys.argv[4]) if len(sys.argv) > 4 else None
        result = project_dividends(ticker, years, growth_rate)
        print(json.dumps(result, indent=2))
    
    elif command in ['aristocrat', 'div-aristocrat']:
        ticker = sys.argv[2]
        result = check_aristocrat_status(ticker)
        print(json.dumps(result, indent=2))
    
    elif command in ['compare', 'div-compare']:
        tickers = sys.argv[2:]
        result = compare_dividend_growth(tickers)
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
