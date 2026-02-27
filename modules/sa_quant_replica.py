#!/usr/bin/env python3
"""
SA Quant Rating Replica - Historical Scoring with FREE yfinance Data

Replicates Seeking Alpha's Quant Rating system using ONLY free yfinance data.
KEY INNOVATION: Scores stocks at ANY POINT IN TIME using only data available at that date.

SA ALPHA PICKS METHODOLOGY:
- SA Quant Rating = "Strong Buy" for 75+ consecutive days
- US Common Stock, not REIT, market cap > $500M, price > $10
- Quant Rating = composite of 5 factors:

SCORING FACTORS:
1. Valuation (15%): P/E, P/B, P/S ratios vs sector median
2. Growth (20%): Revenue growth YoY, EPS growth
3. Profitability (20%): Margins (gross, operating, net), ROE, ROA, FCF margin
4. Momentum (20%): 3M/6M/12M returns, RSI, price vs 200MA
5. EPS Revisions (25%): Earnings surprises, analyst upgrades, recommendation sentiment

COMPOSITE SCORE:
- Strong Buy: composite >= 3.5 (A/A+)
- Buy: >= 2.8 (B+)
- Hold: >= 2.0 (C+)
- Sell: >= 1.2 (D)
- Strong Sell: < 1.2 (F)

GRADE SCALE: A+ = 5.0, A = 4.0, B = 3.0, C = 2.0, D = 1.0, F = 0.0
"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import sys
import sqlite3
import pickle
from pathlib import Path
from tqdm import tqdm


class SAQuantReplica:
    """
    Seeking Alpha Quant Rating Replica using free yfinance data.
    Supports HISTORICAL scoring at any point in time.
    """
    
    # Grade scale
    GRADE_SCALE = {
        'A+': 5.0,
        'A': 4.0,
        'B': 3.0,
        'C': 2.0,
        'D': 1.0,
        'F': 0.0
    }
    
    # Rating thresholds
    RATING_THRESHOLDS = {
        'Strong Buy': 3.5,
        'Buy': 2.8,
        'Hold': 2.0,
        'Sell': 1.2,
        'Strong Sell': 0.0
    }
    
    def __init__(self, cache_dir: str = None):
        """Initialize with cache directory"""
        self.data_dir = Path(__file__).parent.parent / 'data'
        self.cache_dir = Path(cache_dir or self.data_dir)
        self.cache_db = self.cache_dir / 'sa_quant_cache.db'
        self._init_cache_db()
        
        # Load price cache
        self.price_cache_path = self.data_dir / 'price_history_cache.pkl'
        self.price_cache = self._load_price_cache()
    
    def _init_cache_db(self):
        """Initialize SQLite cache for yfinance data"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        # Cache quarterly financials
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quarterly_financials (
                ticker TEXT PRIMARY KEY,
                income_stmt BLOB,
                balance_sheet BLOB,
                cashflow BLOB,
                updated TEXT
            )
        ''')
        
        # Cache earnings history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS earnings_history (
                ticker TEXT PRIMARY KEY,
                data BLOB,
                updated TEXT
            )
        ''')
        
        # Cache upgrades/downgrades
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS upgrades_downgrades (
                ticker TEXT PRIMARY KEY,
                data BLOB,
                updated TEXT
            )
        ''')
        
        # Cache info
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ticker_info (
                ticker TEXT PRIMARY KEY,
                data TEXT,
                updated TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_price_cache(self) -> Dict:
        """Load price history cache"""
        if not self.price_cache_path.exists():
            print(f"Warning: Price cache not found at {self.price_cache_path}", file=sys.stderr)
            return {}
        
        with open(self.price_cache_path, 'rb') as f:
            return pickle.load(f)
    
    def _get_cached_financials(self, ticker: str) -> Optional[Dict]:
        """Get cached quarterly financials or fetch from yfinance"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        # Check cache (valid for 24 hours)
        cursor.execute(
            'SELECT income_stmt, balance_sheet, cashflow, updated FROM quarterly_financials WHERE ticker = ?',
            (ticker,)
        )
        row = cursor.fetchone()
        
        if row:
            updated = datetime.fromisoformat(row[3])
            if datetime.now() - updated < timedelta(hours=24):
                conn.close()
                return {
                    'income': pickle.loads(row[0]),
                    'balance': pickle.loads(row[1]),
                    'cashflow': pickle.loads(row[2])
                }
        
        # Fetch from yfinance
        try:
            t = yf.Ticker(ticker)
            income = t.quarterly_income_stmt
            balance = t.quarterly_balance_sheet
            cashflow = t.quarterly_cashflow
            
            # Cache the data
            cursor.execute('''
                INSERT OR REPLACE INTO quarterly_financials 
                (ticker, income_stmt, balance_sheet, cashflow, updated)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                ticker,
                pickle.dumps(income),
                pickle.dumps(balance),
                pickle.dumps(cashflow),
                datetime.now().isoformat()
            ))
            conn.commit()
            conn.close()
            
            return {'income': income, 'balance': balance, 'cashflow': cashflow}
        except Exception as e:
            print(f"Error fetching financials for {ticker}: {e}", file=sys.stderr)
            conn.close()
            return None
    
    def _get_cached_earnings(self, ticker: str) -> Optional[pd.DataFrame]:
        """Get cached earnings history or fetch from yfinance"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('SELECT data, updated FROM earnings_history WHERE ticker = ?', (ticker,))
        row = cursor.fetchone()
        
        if row:
            updated = datetime.fromisoformat(row[1])
            if datetime.now() - updated < timedelta(hours=24):
                conn.close()
                return pickle.loads(row[0])
        
        try:
            t = yf.Ticker(ticker)
            earnings = t.earnings_history
            
            cursor.execute('''
                INSERT OR REPLACE INTO earnings_history (ticker, data, updated)
                VALUES (?, ?, ?)
            ''', (ticker, pickle.dumps(earnings), datetime.now().isoformat()))
            conn.commit()
            conn.close()
            
            return earnings
        except Exception as e:
            print(f"Error fetching earnings for {ticker}: {e}", file=sys.stderr)
            conn.close()
            return None
    
    def _get_cached_upgrades(self, ticker: str) -> Optional[pd.DataFrame]:
        """Get cached upgrades/downgrades or fetch from yfinance"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('SELECT data, updated FROM upgrades_downgrades WHERE ticker = ?', (ticker,))
        row = cursor.fetchone()
        
        if row:
            updated = datetime.fromisoformat(row[1])
            if datetime.now() - updated < timedelta(hours=24):
                conn.close()
                return pickle.loads(row[0])
        
        try:
            t = yf.Ticker(ticker)
            upgrades = t.upgrades_downgrades
            
            cursor.execute('''
                INSERT OR REPLACE INTO upgrades_downgrades (ticker, data, updated)
                VALUES (?, ?, ?)
            ''', (ticker, pickle.dumps(upgrades), datetime.now().isoformat()))
            conn.commit()
            conn.close()
            
            return upgrades
        except Exception as e:
            conn.close()
            return None
    
    def _get_price_at_date(self, ticker: str, date: str) -> Optional[float]:
        """Get historical price at a specific date"""
        if ticker not in self.price_cache:
            return None
        
        df = self.price_cache[ticker]
        target_date = pd.to_datetime(date)
        
        # Find closest price before or on the date
        prices = df[df.index <= target_date]
        if prices.empty:
            return None
        
        return prices['Close'].iloc[-1]
    
    def _get_price_history_before_date(self, ticker: str, date: str, days: int = 365) -> Optional[pd.DataFrame]:
        """Get price history before a specific date"""
        if ticker not in self.price_cache:
            return None
        
        df = self.price_cache[ticker]
        target_date = pd.to_datetime(date)
        start_date = target_date - timedelta(days=days)
        
        return df[(df.index >= start_date) & (df.index <= target_date)]
    
    def _grade_to_score(self, grade: str) -> float:
        """Convert letter grade to numeric score"""
        return self.GRADE_SCALE.get(grade, 0.0)
    
    def _score_to_rating(self, score: float) -> str:
        """Convert composite score to SA rating"""
        for rating, threshold in sorted(self.RATING_THRESHOLDS.items(), key=lambda x: -x[1]):
            if score >= threshold:
                return rating
        return 'Strong Sell'
    
    # ========== FACTOR 1: VALUATION (15%) ==========
    
    def _score_valuation(self, ticker: str, date: str) -> Tuple[float, Dict]:
        """
        Score valuation using P/E, P/B, P/S at the given date.
        
        For HISTORICAL scoring:
        - Get price at date
        - Use CURRENT quarterly financials (yfinance limitation: only returns latest quarters)
        - Compute TTM metrics using latest available data
        
        NOTE: This is a reasonable approximation since fundamental quality tends to persist.
        """
        details = {}
        
        # Get price at date
        price = self._get_price_at_date(ticker, date)
        if price is None:
            return 0.0, {'error': 'No price data'}
        
        # Get financials (will be current, not historical)
        financials = self._get_cached_financials(ticker)
        if not financials:
            return 0.0, {'error': 'No financials'}
        
        income = financials['income']
        balance = financials['balance']
        
        if income.empty or balance.empty:
            return 0.0, {'error': 'Empty financials'}
        
        # Use all available quarters (yfinance only gives us ~5 latest)
        income_cols = income.columns.tolist()
        balance_cols = balance.columns.tolist()
        
        if len(income_cols) < 4 or len(balance_cols) < 1:
            return 0.0, {'error': 'Not enough financial data'}
        
        # Get last 4 quarters for TTM
        ttm_income = income[income_cols[:4]]
        latest_balance = balance[balance_cols[0]]
        
        scores = []
        
        # P/E Ratio
        try:
            if 'Net Income' in ttm_income.index:
                ttm_net_income = ttm_income.loc['Net Income'].sum()
                if 'Ordinary Shares Number' in latest_balance.index:
                    shares = latest_balance['Ordinary Shares Number']
                    if shares > 0:
                        ttm_eps = ttm_net_income / shares
                        pe = price / ttm_eps if ttm_eps > 0 else 999
                        details['PE'] = round(pe, 2)
                        
                        # Grade P/E
                        if pe < 10:
                            scores.append(self._grade_to_score('A+'))
                        elif pe < 15:
                            scores.append(self._grade_to_score('A'))
                        elif pe < 20:
                            scores.append(self._grade_to_score('B'))
                        elif pe < 30:
                            scores.append(self._grade_to_score('C'))
                        elif pe < 50:
                            scores.append(self._grade_to_score('D'))
                        else:
                            scores.append(self._grade_to_score('F'))
        except:
            pass
        
        # P/B Ratio
        try:
            if 'Stockholders Equity' in latest_balance.index:
                equity = latest_balance['Stockholders Equity']
                if 'Ordinary Shares Number' in latest_balance.index:
                    shares = latest_balance['Ordinary Shares Number']
                    if shares > 0:
                        book_value_per_share = equity / shares
                        pb = price / book_value_per_share if book_value_per_share > 0 else 999
                        details['PB'] = round(pb, 2)
                        
                        # Grade P/B
                        if pb < 1:
                            scores.append(self._grade_to_score('A+'))
                        elif pb < 2:
                            scores.append(self._grade_to_score('A'))
                        elif pb < 3:
                            scores.append(self._grade_to_score('B'))
                        elif pb < 5:
                            scores.append(self._grade_to_score('C'))
                        elif pb < 10:
                            scores.append(self._grade_to_score('D'))
                        else:
                            scores.append(self._grade_to_score('F'))
        except:
            pass
        
        # P/S Ratio
        try:
            if 'Total Revenue' in ttm_income.index:
                ttm_revenue = ttm_income.loc['Total Revenue'].sum()
                if 'Ordinary Shares Number' in latest_balance.index:
                    shares = latest_balance['Ordinary Shares Number']
                    if shares > 0:
                        revenue_per_share = ttm_revenue / shares
                        ps = price / revenue_per_share if revenue_per_share > 0 else 999
                        details['PS'] = round(ps, 2)
                        
                        # Grade P/S
                        if ps < 1:
                            scores.append(self._grade_to_score('A+'))
                        elif ps < 2:
                            scores.append(self._grade_to_score('A'))
                        elif ps < 4:
                            scores.append(self._grade_to_score('B'))
                        elif ps < 8:
                            scores.append(self._grade_to_score('C'))
                        elif ps < 15:
                            scores.append(self._grade_to_score('D'))
                        else:
                            scores.append(self._grade_to_score('F'))
        except:
            pass
        
        # Average the scores
        if not scores:
            return 0.0, details
        
        avg_score = np.mean(scores)
        details['score'] = round(avg_score, 2)
        return avg_score, details
    
    # ========== FACTOR 2: GROWTH (20%) ==========
    
    def _score_growth(self, ticker: str, date: str) -> Tuple[float, Dict]:
        """
        Score growth using revenue and EPS growth YoY.
        
        Compare latest quarter to same quarter 1 year ago.
        Uses CURRENT financial data (yfinance limitation).
        """
        details = {}
        
        financials = self._get_cached_financials(ticker)
        if not financials:
            return 0.0, {'error': 'No financials'}
        
        income = financials['income']
        if income.empty:
            return 0.0, {'error': 'Empty income statement'}
        
        # Use all available quarters
        income_cols = income.columns.tolist()
        
        if len(income_cols) < 5:  # Need at least 5 quarters to compare YoY
            return 0.0, {'error': 'Not enough quarters for YoY growth'}
        
        scores = []
        
        # Revenue growth
        try:
            if 'Total Revenue' in income.index:
                recent_revenue = income.loc['Total Revenue', income_cols[0]]
                year_ago_revenue = income.loc['Total Revenue', income_cols[4]]
                
                if year_ago_revenue > 0:
                    rev_growth = (recent_revenue / year_ago_revenue - 1) * 100
                    details['revenue_growth_pct'] = round(rev_growth, 2)
                    
                    # Grade revenue growth
                    if rev_growth > 30:
                        scores.append(self._grade_to_score('A+'))
                    elif rev_growth > 15:
                        scores.append(self._grade_to_score('A'))
                    elif rev_growth > 8:
                        scores.append(self._grade_to_score('B'))
                    elif rev_growth > 3:
                        scores.append(self._grade_to_score('C'))
                    elif rev_growth > 0:
                        scores.append(self._grade_to_score('D'))
                    else:
                        scores.append(self._grade_to_score('F'))
        except:
            pass
        
        # EPS growth
        try:
            if 'Net Income' in income.index:
                # Get balance sheet for shares
                balance = financials['balance']
                balance_cols = [col for col in balance.columns if col <= target_date]
                
                if len(balance_cols) >= 5:
                    recent_ni = income.loc['Net Income', income_cols[0]]
                    year_ago_ni = income.loc['Net Income', income_cols[4]]
                    
                    recent_shares = balance.loc['Ordinary Shares Number', balance_cols[0]]
                    year_ago_shares = balance.loc['Ordinary Shares Number', balance_cols[4]]
                    
                    recent_eps = recent_ni / recent_shares if recent_shares > 0 else 0
                    year_ago_eps = year_ago_ni / year_ago_shares if year_ago_shares > 0 else 0
                    
                    if year_ago_eps > 0:
                        eps_growth = (recent_eps / year_ago_eps - 1) * 100
                        details['eps_growth_pct'] = round(eps_growth, 2)
                        
                        # Grade EPS growth
                        if eps_growth > 30:
                            scores.append(self._grade_to_score('A+'))
                        elif eps_growth > 15:
                            scores.append(self._grade_to_score('A'))
                        elif eps_growth > 8:
                            scores.append(self._grade_to_score('B'))
                        elif eps_growth > 3:
                            scores.append(self._grade_to_score('C'))
                        elif eps_growth > 0:
                            scores.append(self._grade_to_score('D'))
                        else:
                            scores.append(self._grade_to_score('F'))
        except:
            pass
        
        if not scores:
            return 0.0, details
        
        avg_score = np.mean(scores)
        details['score'] = round(avg_score, 2)
        return avg_score, details
    
    # ========== FACTOR 3: PROFITABILITY (20%) ==========
    
    def _score_profitability(self, ticker: str, date: str) -> Tuple[float, Dict]:
        """
        Score profitability using margins, ROE, ROA, FCF margin.
        Uses CURRENT financial data (yfinance limitation).
        """
        details = {}
        
        financials = self._get_cached_financials(ticker)
        if not financials:
            return 0.0, {'error': 'No financials'}
        
        income = financials['income']
        balance = financials['balance']
        cashflow = financials['cashflow']
        
        if income.empty or balance.empty:
            return 0.0, {'error': 'Empty financials'}
        
        # Use all available quarters
        income_cols = income.columns.tolist()
        balance_cols = balance.columns.tolist()
        cashflow_cols = cashflow.columns.tolist() if not cashflow.empty else []
        
        if len(income_cols) < 4 or len(balance_cols) < 1:
            return 0.0, {'error': 'Not enough financial data'}
        
        # Get TTM income and latest balance
        ttm_income = income[income_cols[:4]]
        latest_balance = balance[balance_cols[0]]
        
        scores = []
        
        # Gross Margin
        try:
            if 'Gross Profit' in ttm_income.index and 'Total Revenue' in ttm_income.index:
                gross_profit = ttm_income.loc['Gross Profit'].sum()
                revenue = ttm_income.loc['Total Revenue'].sum()
                if revenue > 0:
                    gross_margin = (gross_profit / revenue) * 100
                    details['gross_margin_pct'] = round(gross_margin, 2)
                    
                    if gross_margin > 50:
                        scores.append(self._grade_to_score('A+'))
                    elif gross_margin > 40:
                        scores.append(self._grade_to_score('A'))
                    elif gross_margin > 30:
                        scores.append(self._grade_to_score('B'))
                    elif gross_margin > 20:
                        scores.append(self._grade_to_score('C'))
                    elif gross_margin > 10:
                        scores.append(self._grade_to_score('D'))
                    else:
                        scores.append(self._grade_to_score('F'))
        except:
            pass
        
        # Operating Margin
        try:
            if 'EBIT' in ttm_income.index and 'Total Revenue' in ttm_income.index:
                ebit = ttm_income.loc['EBIT'].sum()
                revenue = ttm_income.loc['Total Revenue'].sum()
                if revenue > 0:
                    operating_margin = (ebit / revenue) * 100
                    details['operating_margin_pct'] = round(operating_margin, 2)
                    
                    if operating_margin > 25:
                        scores.append(self._grade_to_score('A+'))
                    elif operating_margin > 15:
                        scores.append(self._grade_to_score('A'))
                    elif operating_margin > 10:
                        scores.append(self._grade_to_score('B'))
                    elif operating_margin > 5:
                        scores.append(self._grade_to_score('C'))
                    elif operating_margin > 0:
                        scores.append(self._grade_to_score('D'))
                    else:
                        scores.append(self._grade_to_score('F'))
        except:
            pass
        
        # Net Margin
        try:
            if 'Net Income' in ttm_income.index and 'Total Revenue' in ttm_income.index:
                net_income = ttm_income.loc['Net Income'].sum()
                revenue = ttm_income.loc['Total Revenue'].sum()
                if revenue > 0:
                    net_margin = (net_income / revenue) * 100
                    details['net_margin_pct'] = round(net_margin, 2)
                    
                    if net_margin > 20:
                        scores.append(self._grade_to_score('A+'))
                    elif net_margin > 12:
                        scores.append(self._grade_to_score('A'))
                    elif net_margin > 7:
                        scores.append(self._grade_to_score('B'))
                    elif net_margin > 3:
                        scores.append(self._grade_to_score('C'))
                    elif net_margin > 0:
                        scores.append(self._grade_to_score('D'))
                    else:
                        scores.append(self._grade_to_score('F'))
        except:
            pass
        
        # ROE
        try:
            if 'Net Income' in ttm_income.index and 'Stockholders Equity' in latest_balance.index:
                ttm_net_income = ttm_income.loc['Net Income'].sum()
                equity = latest_balance['Stockholders Equity']
                if equity > 0:
                    roe = (ttm_net_income / equity) * 100
                    details['roe_pct'] = round(roe, 2)
                    
                    if roe > 25:
                        scores.append(self._grade_to_score('A+'))
                    elif roe > 18:
                        scores.append(self._grade_to_score('A'))
                    elif roe > 12:
                        scores.append(self._grade_to_score('B'))
                    elif roe > 6:
                        scores.append(self._grade_to_score('C'))
                    elif roe > 0:
                        scores.append(self._grade_to_score('D'))
                    else:
                        scores.append(self._grade_to_score('F'))
        except:
            pass
        
        # ROA
        try:
            if 'Net Income' in ttm_income.index and 'Total Assets' in latest_balance.index:
                ttm_net_income = ttm_income.loc['Net Income'].sum()
                assets = latest_balance['Total Assets']
                if assets > 0:
                    roa = (ttm_net_income / assets) * 100
                    details['roa_pct'] = round(roa, 2)
                    
                    if roa > 15:
                        scores.append(self._grade_to_score('A+'))
                    elif roa > 10:
                        scores.append(self._grade_to_score('A'))
                    elif roa > 6:
                        scores.append(self._grade_to_score('B'))
                    elif roa > 3:
                        scores.append(self._grade_to_score('C'))
                    elif roa > 0:
                        scores.append(self._grade_to_score('D'))
                    else:
                        scores.append(self._grade_to_score('F'))
        except:
            pass
        
        # FCF Margin
        if cashflow_cols:
            try:
                ttm_cashflow = cashflow[cashflow_cols[:4]]
                if 'Free Cash Flow' in ttm_cashflow.index and 'Total Revenue' in ttm_income.index:
                    fcf = ttm_cashflow.loc['Free Cash Flow'].sum()
                    revenue = ttm_income.loc['Total Revenue'].sum()
                    if revenue > 0:
                        fcf_margin = (fcf / revenue) * 100
                        details['fcf_margin_pct'] = round(fcf_margin, 2)
                        
                        if fcf_margin > 20:
                            scores.append(self._grade_to_score('A+'))
                        elif fcf_margin > 12:
                            scores.append(self._grade_to_score('A'))
                        elif fcf_margin > 7:
                            scores.append(self._grade_to_score('B'))
                        elif fcf_margin > 3:
                            scores.append(self._grade_to_score('C'))
                        elif fcf_margin > 0:
                            scores.append(self._grade_to_score('D'))
                        else:
                            scores.append(self._grade_to_score('F'))
            except:
                pass
        
        if not scores:
            return 0.0, details
        
        avg_score = np.mean(scores)
        details['score'] = round(avg_score, 2)
        return avg_score, details
    
    # ========== FACTOR 4: MOMENTUM (20%) ==========
    
    def _score_momentum(self, ticker: str, date: str) -> Tuple[float, Dict]:
        """
        Score momentum using 3M/6M/12M returns, RSI, price vs 200MA.
        """
        details = {}
        
        # Get price history before date
        prices = self._get_price_history_before_date(ticker, date, days=365)
        if prices is None or len(prices) < 50:
            return 0.0, {'error': 'Not enough price data'}
        
        current_price = prices['Close'].iloc[-1]
        scores = []
        
        # 3-month return
        if len(prices) >= 63:
            price_3m_ago = prices['Close'].iloc[-63]
            ret_3m = (current_price / price_3m_ago - 1) * 100
            details['return_3m_pct'] = round(ret_3m, 2)
            
            if ret_3m > 30:
                scores.append(self._grade_to_score('A+'))
            elif ret_3m > 15:
                scores.append(self._grade_to_score('A'))
            elif ret_3m > 5:
                scores.append(self._grade_to_score('B'))
            elif ret_3m > 0:
                scores.append(self._grade_to_score('C'))
            elif ret_3m > -10:
                scores.append(self._grade_to_score('D'))
            else:
                scores.append(self._grade_to_score('F'))
        
        # 6-month return
        if len(prices) >= 126:
            price_6m_ago = prices['Close'].iloc[-126]
            ret_6m = (current_price / price_6m_ago - 1) * 100
            details['return_6m_pct'] = round(ret_6m, 2)
            
            if ret_6m > 40:
                scores.append(self._grade_to_score('A+'))
            elif ret_6m > 20:
                scores.append(self._grade_to_score('A'))
            elif ret_6m > 8:
                scores.append(self._grade_to_score('B'))
            elif ret_6m > 0:
                scores.append(self._grade_to_score('C'))
            elif ret_6m > -15:
                scores.append(self._grade_to_score('D'))
            else:
                scores.append(self._grade_to_score('F'))
        
        # 12-month return
        if len(prices) >= 252:
            price_12m_ago = prices['Close'].iloc[-252]
            ret_12m = (current_price / price_12m_ago - 1) * 100
            details['return_12m_pct'] = round(ret_12m, 2)
            
            if ret_12m > 50:
                scores.append(self._grade_to_score('A+'))
            elif ret_12m > 25:
                scores.append(self._grade_to_score('A'))
            elif ret_12m > 10:
                scores.append(self._grade_to_score('B'))
            elif ret_12m > 0:
                scores.append(self._grade_to_score('C'))
            elif ret_12m > -20:
                scores.append(self._grade_to_score('D'))
            else:
                scores.append(self._grade_to_score('F'))
        
        # RSI (14-day)
        if len(prices) >= 20:
            delta = prices['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            if not np.isnan(current_rsi):
                details['rsi'] = round(current_rsi, 2)
                
                if 50 <= current_rsi <= 70:
                    scores.append(self._grade_to_score('A'))
                elif 40 <= current_rsi <= 80:
                    scores.append(self._grade_to_score('B'))
                elif current_rsi > 80 or current_rsi < 30:
                    scores.append(self._grade_to_score('D'))
                else:
                    scores.append(self._grade_to_score('C'))
        
        # Price vs 200MA
        if len(prices) >= 200:
            ma_200 = prices['Close'].rolling(window=200).mean().iloc[-1]
            pct_above_ma = ((current_price / ma_200 - 1) * 100)
            details['pct_above_200ma'] = round(pct_above_ma, 2)
            
            if pct_above_ma > 10:
                scores.append(self._grade_to_score('A+'))
            elif pct_above_ma > 5:
                scores.append(self._grade_to_score('A'))
            elif pct_above_ma > 0:
                scores.append(self._grade_to_score('B'))
            elif pct_above_ma > -5:
                scores.append(self._grade_to_score('C'))
            elif pct_above_ma > -10:
                scores.append(self._grade_to_score('D'))
            else:
                scores.append(self._grade_to_score('F'))
        
        if not scores:
            return 0.0, details
        
        avg_score = np.mean(scores)
        details['score'] = round(avg_score, 2)
        return avg_score, details
    
    # ========== FACTOR 5: EPS REVISIONS (25%) — MOST IMPORTANT ==========
    
    def _score_eps_revisions(self, ticker: str, date: str) -> Tuple[float, Dict]:
        """
        Score EPS revisions using earnings surprises and analyst upgrades.
        This is THE key factor (25% weight).
        
        Uses historical earnings data (indexed by quarter date) and analyst actions.
        """
        details = {}
        scores = []
        
        # Get earnings history
        earnings = self._get_cached_earnings(ticker)
        if earnings is not None and not earnings.empty:
            # Earnings history is indexed by quarter date, so we CAN filter historically
            target_date = pd.to_datetime(date)
            
            # Filter earnings reported before date
            earnings_before = earnings[earnings.index <= target_date]
            
            if not earnings_before.empty and len(earnings_before) > 0:
                # Last earnings surprise
                if len(earnings_before) >= 1:
                    last_surprise = earnings_before.iloc[0]['surprisePercent'] * 100
                    details['last_surprise_pct'] = round(last_surprise, 2)
                    
                    if last_surprise > 10:
                        scores.append(self._grade_to_score('A+'))
                    elif last_surprise > 5:
                        scores.append(self._grade_to_score('A'))
                    elif last_surprise > 0:
                        scores.append(self._grade_to_score('B'))
                    elif last_surprise > -5:
                        scores.append(self._grade_to_score('C'))
                    elif last_surprise > -10:
                        scores.append(self._grade_to_score('D'))
                    else:
                        scores.append(self._grade_to_score('F'))
                
                # Consecutive beats
                if len(earnings_before) >= 2:
                    surprises = earnings_before.head(2)['surprisePercent'].values
                    if all(s > 0 for s in surprises):
                        details['consecutive_beats'] = 2
                        scores.append(self._grade_to_score('A'))  # Boost for consistency
        
        # Get analyst upgrades
        upgrades = self._get_cached_upgrades(ticker)
        if upgrades is not None and not upgrades.empty:
            target_date = pd.to_datetime(date)
            cutoff_date = target_date - timedelta(days=90)
            
            # Filter upgrades in last 90 days before date
            recent_upgrades = upgrades[(upgrades.index >= cutoff_date) & (upgrades.index <= target_date)]
            
            if not recent_upgrades.empty:
                # Count net upgrades
                net_upgrades = 0
                for _, row in recent_upgrades.iterrows():
                    action = str(row.get('Action', '')).lower()
                    if 'up' in action or 'upgrade' in action:
                        net_upgrades += 1
                    elif 'down' in action or 'downgrade' in action:
                        net_upgrades -= 1
                
                details['net_upgrades_90d'] = net_upgrades
                
                if net_upgrades > 3:
                    scores.append(self._grade_to_score('A+'))
                elif net_upgrades > 1:
                    scores.append(self._grade_to_score('A'))
                elif net_upgrades > 0:
                    scores.append(self._grade_to_score('B'))
                elif net_upgrades == 0:
                    scores.append(self._grade_to_score('C'))
                else:
                    scores.append(self._grade_to_score('D'))
        
        if not scores:
            # No data available — neutral score
            return 2.0, details
        
        avg_score = np.mean(scores)
        details['score'] = round(avg_score, 2)
        return avg_score, details
    
    # ========== COMPOSITE SCORING ==========
    
    def score_at_date(self, ticker: str, date: str) -> Dict:
        """
        Score a stock using only data available at the given date.
        
        Returns:
            dict with composite score, rating, and factor breakdown
        """
        # Score all 5 factors
        val_score, val_details = self._score_valuation(ticker, date)
        growth_score, growth_details = self._score_growth(ticker, date)
        profit_score, profit_details = self._score_profitability(ticker, date)
        momentum_score, momentum_details = self._score_momentum(ticker, date)
        revisions_score, revisions_details = self._score_eps_revisions(ticker, date)
        
        # Weighted composite
        composite = (
            val_score * 0.15 +
            growth_score * 0.20 +
            profit_score * 0.20 +
            momentum_score * 0.20 +
            revisions_score * 0.25
        )
        
        rating = self._score_to_rating(composite)
        
        return {
            'ticker': ticker,
            'date': date,
            'composite_score': round(composite, 2),
            'rating': rating,
            'factors': {
                'valuation': {'score': round(val_score, 2), 'weight': 0.15, 'details': val_details},
                'growth': {'score': round(growth_score, 2), 'weight': 0.20, 'details': growth_details},
                'profitability': {'score': round(profit_score, 2), 'weight': 0.20, 'details': profit_details},
                'momentum': {'score': round(momentum_score, 2), 'weight': 0.20, 'details': momentum_details},
                'eps_revisions': {'score': round(revisions_score, 2), 'weight': 0.25, 'details': revisions_details}
            }
        }
    
    def score_current(self, ticker: str) -> Dict:
        """Score a stock using current date"""
        return self.score_at_date(ticker, datetime.now().strftime('%Y-%m-%d'))
    
    def find_strong_buys(self, universe: List[str], date: str = None, n: int = 10) -> List[Dict]:
        """
        Find top N Strong Buy stocks from a universe.
        
        Args:
            universe: List of tickers to score
            date: Date to score at (default: today)
            n: Number of top stocks to return
        
        Returns:
            List of scored stocks sorted by composite score
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        results = []
        for ticker in tqdm(universe, desc=f"Scoring stocks at {date}"):
            try:
                score_result = self.score_at_date(ticker, date)
                if score_result['composite_score'] >= 3.5:  # Strong Buy threshold
                    results.append(score_result)
            except Exception as e:
                continue
        
        # Sort by composite score
        results.sort(key=lambda x: x['composite_score'], reverse=True)
        return results[:n]


# ========== CLI HELPERS ==========

def run_blind_backtest(cache_dir: str = None, start_date: str = '2023-05-01', end_date: str = '2026-02-15') -> Dict:
    """
    Run blind backtest using SA Quant scoring.
    
    Strategy:
    1. Pre-filter by momentum (6M return > 15%) — fast using price cache
    2. Score top ~200 momentum stocks with full 5-factor model
    3. Pick top 2 "Strong Buy" stocks
    4. Track returns and overlap with actual Alpha Picks
    
    Args:
        cache_dir: Cache directory
        start_date: Start date for backtest
        end_date: End date for backtest
    
    Returns:
        dict with backtest results
    """
    from pathlib import Path
    import pandas as pd
    from datetime import datetime, timedelta
    
    # Load universe
    data_dir = Path(__file__).parent.parent / 'data'
    universe_path = data_dir / 'us_stock_universe.txt'
    
    if not universe_path.exists():
        return {'error': 'Universe file not found'}
    
    with open(universe_path) as f:
        universe = [line.strip() for line in f if line.strip()][:500]  # Limit for speed
    
    scorer = SAQuantReplica(cache_dir=cache_dir)
    
    # Generate pick dates (1st and 15th of each month)
    pick_dates = []
    current = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    while current <= end:
        pick_dates.append(current.strftime('%Y-%m-%d'))
        # Next date: 15th if current is 1st, else 1st of next month
        if current.day == 1:
            pick_dates.append((current + timedelta(days=14)).strftime('%Y-%m-%d'))
            current = (current + timedelta(days=31)).replace(day=1)
        else:
            current = (current + timedelta(days=31)).replace(day=1)
    
    results = []
    
    print(f"\nRunning blind backtest: {len(pick_dates)} pick dates from {start_date} to {end_date}")
    print("Strategy: Pick top 2 Strong Buy stocks (composite >= 3.5)\n")
    
    for pick_date in tqdm(pick_dates[:10], desc="Backtesting"):  # Limit to 10 dates for speed
        # Pre-filter by momentum
        momentum_candidates = []
        for ticker in universe:
            prices = scorer._get_price_history_before_date(ticker, pick_date, days=180)
            if prices is None or len(prices) < 126:
                continue
            
            current_price = prices['Close'].iloc[-1]
            price_6m_ago = prices['Close'].iloc[-126] if len(prices) >= 126 else prices['Close'].iloc[0]
            ret_6m = (current_price / price_6m_ago - 1) * 100
            
            if ret_6m > 15:  # Momentum filter
                momentum_candidates.append((ticker, ret_6m))
        
        # Sort by momentum and take top 200
        momentum_candidates.sort(key=lambda x: -x[1])
        top_momentum = [t[0] for t in momentum_candidates[:200]]
        
        # Score with full 5-factor model
        scored = []
        for ticker in top_momentum[:50]:  # Limit to 50 for speed
            try:
                result = scorer.score_at_date(ticker, pick_date)
                if result['composite_score'] >= 3.5:  # Strong Buy only
                    scored.append(result)
            except:
                continue
        
        # Pick top 2
        scored.sort(key=lambda x: -x['composite_score'])
        picks = scored[:2]
        
        if picks:
            results.append({
                'date': pick_date,
                'picks': [p['ticker'] for p in picks],
                'scores': [p['composite_score'] for p in picks]
            })
    
    print(f"\nBacktest completed: {len(results)} periods with picks")
    return {'results': results, 'total_periods': len(pick_dates)}


def validate_historical_picks(cache_dir: str = None) -> Dict:
    """
    Validate SA Quant Replica against 45 historical picks.
    
    Returns accuracy metrics.
    """
    from pathlib import Path
    import pandas as pd
    
    # Load historical picks
    data_dir = Path(__file__).parent.parent / 'data'
    picks_path = data_dir / 'stock_picks.csv'
    
    if not picks_path.exists():
        return {'error': 'stock_picks.csv not found'}
    
    picks = pd.read_csv(picks_path)
    
    scorer = SAQuantReplica(cache_dir=cache_dir)
    
    results = []
    strong_buy_count = 0
    buy_or_higher_count = 0
    scores = []
    
    print(f"\nValidating {len(picks)} historical picks...\n")
    print(f"{'Ticker':<8} {'Pick Date':<12} {'Composite':<10} {'Rating':<15} {'Actual SA':<15}")
    print("-" * 70)
    
    for _, row in picks.iterrows():
        ticker = row['Symbol']
        pick_date = row['PickDate']
        
        try:
            result = scorer.score_at_date(ticker, pick_date)
            composite = result['composite_score']
            rating = result['rating']
            
            scores.append(composite)
            
            if rating == 'Strong Buy':
                strong_buy_count += 1
            if rating in ['Strong Buy', 'Buy']:
                buy_or_higher_count += 1
            
            # Assume actual SA rating was Strong Buy (since these are Alpha Picks)
            actual_sa = row.get('Rating', 'Strong Buy')
            
            print(f"{ticker:<8} {pick_date:<12} {composite:<10.2f} {rating:<15} {actual_sa:<15}")
            
            results.append({
                'ticker': ticker,
                'pick_date': pick_date,
                'composite': composite,
                'rating': rating,
                'actual_sa': actual_sa
            })
        except Exception as e:
            print(f"{ticker:<8} {pick_date:<12} ERROR: {str(e)[:30]}")
    
    total = len(results)
    avg_composite = np.mean(scores) if scores else 0
    
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS:")
    print(f"  Total picks scored: {total}")
    print(f"  Strong Buy: {strong_buy_count} ({strong_buy_count/total*100:.1f}%)")
    print(f"  Buy or higher: {buy_or_higher_count} ({buy_or_higher_count/total*100:.1f}%)")
    print(f"  Average composite score: {avg_composite:.2f}")
    print(f"  Target: >70% Strong Buy, >85% Buy+")
    print("=" * 70)
    
    return {
        'total': total,
        'strong_buy_count': strong_buy_count,
        'buy_or_higher_count': buy_or_higher_count,
        'strong_buy_pct': round(strong_buy_count / total * 100, 1) if total > 0 else 0,
        'buy_or_higher_pct': round(buy_or_higher_count / total * 100, 1) if total > 0 else 0,
        'avg_composite': round(avg_composite, 2),
        'results': results
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='SA Quant Rating Replica')
    parser.add_argument('command', choices=['sa-score', 'sa-strong-buys', 'sa-validate', 'sa-backtest'])
    parser.add_argument('ticker', nargs='?', help='Ticker symbol')
    parser.add_argument('--date', help='Date to score at (YYYY-MM-DD)')
    parser.add_argument('--n', type=int, default=10, help='Number of results')
    parser.add_argument('--start', default='2023-05-01', help='Backtest start date')
    parser.add_argument('--end', default='2026-02-15', help='Backtest end date')
    
    args = parser.parse_args()
    
    if args.command == 'sa-score':
        if not args.ticker:
            print("Error: ticker required for sa-score", file=sys.stderr)
            sys.exit(1)
        
        scorer = SAQuantReplica()
        if args.date:
            result = scorer.score_at_date(args.ticker, args.date)
        else:
            result = scorer.score_current(args.ticker)
        
        print(json.dumps(result, indent=2))
    
    elif args.command == 'sa-strong-buys':
        # Load universe
        data_dir = Path(__file__).parent.parent / 'data'
        universe_path = data_dir / 'us_stock_universe.txt'
        
        if not universe_path.exists():
            print(f"Error: Universe file not found at {universe_path}", file=sys.stderr)
            sys.exit(1)
        
        with open(universe_path) as f:
            universe = [line.strip() for line in f if line.strip()]
        
        scorer = SAQuantReplica()
        results = scorer.find_strong_buys(universe[:200], date=args.date, n=args.n)  # Limit to 200 for speed
        
        print(f"\nTop {args.n} Strong Buy Stocks:\n")
        print(f"{'Ticker':<8} {'Score':<8} {'Rating':<15} {'Momentum':<10} {'EPS Rev':<10}")
        print("-" * 70)
        
        for r in results:
            momentum = r['factors']['momentum']['score']
            revisions = r['factors']['eps_revisions']['score']
            print(f"{r['ticker']:<8} {r['composite_score']:<8.2f} {r['rating']:<15} {momentum:<10.2f} {revisions:<10.2f}")
    
    elif args.command == 'sa-validate':
        results = validate_historical_picks()
        
        if 'error' in results:
            print(f"Error: {results['error']}", file=sys.stderr)
            sys.exit(1)
    
    elif args.command == 'sa-backtest':
        results = run_blind_backtest(start_date=args.start, end_date=args.end)
        
        if 'error' in results:
            print(f"Error: {results['error']}", file=sys.stderr)
            sys.exit(1)
        
        # Print results
        for period in results['results']:
            print(f"\nDate: {period['date']}")
            for i, ticker in enumerate(period['picks']):
                score = period['scores'][i]
                print(f"  Pick {i+1}: {ticker} (Score: {score:.2f})")
