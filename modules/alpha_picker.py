#!/usr/bin/env python3
"""
Alpha Picker Strategy Module v3 - FOUR LAYER SCORING
Combines momentum, fundamentals, earnings catalyst, and thematic/sector timing

SCORING LAYERS:
1. Momentum (max 20 pts): 52w high proximity, 3M/6M returns, RSI, 200MA
2. Fundamentals (max 15 pts): Revenue growth, margins, P/E, debt, FCF
3. Earnings Catalyst (max 10 pts): Earnings surprises, consecutive beats
4. Thematic/Sector (max 10 pts): Sector ETF momentum, gold/small-cap themes
5. Penalties (max -15 pts): Mega/micro caps, energy, weak technicals

TOTAL MAX SCORE: ~55 points

IMPORTANT LIMITATION:
- ticker.info returns CURRENT fundamentals, not historical
- For true blind backtesting, only price-based factors (Layer 1) are truly historical
- Fundamental/earnings data (Layers 2-3) use current info as proxy
- This is a reasonable approximation since fundamental quality persists
"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import sys
import os
import sqlite3
import pickle
from pathlib import Path
from tqdm import tqdm


class AlphaPickerV3:
    """
    4-Layer momentum + fundamentals + earnings + thematic scoring system
    """
    
    # Sector to ETF mapping
    SECTOR_ETF_MAP = {
        'Industrials': 'XLI',
        'Technology': 'XLK',
        'Information Technology': 'XLK',
        'Basic Materials': 'XLB',
        'Materials': 'XLB',
        'Financial Services': 'XLF',
        'Financials': 'XLF',
        'Consumer Discretionary': 'XLY',
        'Consumer Cyclical': 'XLY',
    }
    
    def __init__(self, initial_cash: float = 100000, cache_dir: str = None):
        """Initialize strategy with cash and cache directory"""
        self.initial_cash = initial_cash
        self.cache_dir = Path(cache_dir or '/home/quant/apps/quantclaw-data/.cache/alpha_picker')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_db = self.cache_dir / 'yfinance_cache.db'
        self._init_cache_db()
        
        # Load universe and price cache
        self.data_dir = Path(__file__).parent.parent / 'data'
        self.universe_path = self.data_dir / 'us_stock_universe.txt'
        self.price_cache_path = self.data_dir / 'price_history_cache.pkl'
        self.universe = self._load_universe()
        self.price_cache = self._load_price_cache()
        
        # Download sector ETFs for thematic scoring
        self.sector_etfs = ['SPY', 'IWM', 'XLI', 'XLK', 'XLB', 'XLF', 'XLY', 'GLD']
        self._download_sector_etfs()
        
    def _init_cache_db(self):
        """Initialize SQLite cache database"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history_cache (
                ticker TEXT,
                period TEXT,
                data BLOB,
                updated TEXT,
                PRIMARY KEY (ticker, period)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS info_cache (
                ticker TEXT PRIMARY KEY,
                data TEXT,
                updated TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def _load_universe(self) -> List[str]:
        """Load universe from us_stock_universe.txt"""
        if not self.universe_path.exists():
            print(f"Warning: Universe file not found at {self.universe_path}", file=sys.stderr)
            return []
        
        with open(self.universe_path, 'r') as f:
            tickers = [line.strip() for line in f if line.strip()]
        
        print(f"Loaded {len(tickers)} tickers from universe", file=sys.stderr)
        return tickers
    
    def _load_price_cache(self) -> dict:
        """Load price history cache and convert to dict of DataFrames"""
        if not self.price_cache_path.exists():
            print(f"Warning: Price cache not found at {self.price_cache_path}", file=sys.stderr)
            return {}
        
        with open(self.price_cache_path, 'rb') as f:
            raw_cache = pickle.load(f)
        
        # Convert from (ticker, column) dict to ticker -> DataFrame dict
        cache = {}
        
        # Group by ticker
        tickers = set(k[0] for k in raw_cache.keys() if isinstance(k, tuple))
        
        for ticker in tickers:
            # Extract all columns for this ticker
            ticker_data = {}
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                key = (ticker, col)
                if key in raw_cache:
                    ticker_data[col] = raw_cache[key]
            
            if ticker_data:
                # Convert to DataFrame
                df = pd.DataFrame(ticker_data)
                cache[ticker] = df
        
        print(f"Loaded price cache with {len(cache)} tickers", file=sys.stderr)
        return cache
    
    def _download_sector_etfs(self):
        """Download sector ETF data for thematic scoring"""
        print("Downloading sector ETF data...", file=sys.stderr)
        
        for etf in self.sector_etfs:
            if etf not in self.price_cache:
                try:
                    # Use yfinance directly to avoid cache loop
                    stock = yf.Ticker(etf)
                    hist = stock.history(period='2y')
                    if hist is not None and len(hist) > 0:
                        self.price_cache[etf] = hist
                        print(f"  Downloaded {etf}", file=sys.stderr)
                except Exception as e:
                    print(f"  Error downloading {etf}: {e}", file=sys.stderr)
    
    def _get_info(self, ticker: str) -> dict:
        """Get ticker info with 24-hour cache"""
        # Check cache
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute('SELECT data, updated FROM info_cache WHERE ticker = ?', (ticker,))
        row = cursor.fetchone()
        
        if row:
            updated = datetime.fromisoformat(row[1])
            if datetime.now() - updated < timedelta(hours=24):
                conn.close()
                return json.loads(row[0])
        
        # Fetch from yfinance
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Cache it
            cursor.execute('''
                INSERT OR REPLACE INTO info_cache (ticker, data, updated)
                VALUES (?, ?, ?)
            ''', (ticker, json.dumps(info), datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return info
        except Exception as e:
            conn.close()
            print(f"Error fetching info for {ticker}: {e}", file=sys.stderr)
            return {}
    
    def _get_history(self, ticker: str, period: str = '2y', as_of_date: Optional[datetime] = None) -> Optional[pd.DataFrame]:
        """
        Get ticker history with 6-hour cache
        If as_of_date is provided, return only data up to that date (for blind backtesting)
        """
        # Check price cache first
        if ticker in self.price_cache:
            hist = self.price_cache[ticker].copy()
            if as_of_date:
                # Make as_of_date timezone-aware if needed
                if hist.index.tzinfo is not None and as_of_date.tzinfo is None:
                    as_of_date = as_of_date.replace(tzinfo=hist.index.tzinfo)
                hist = hist[hist.index <= as_of_date]
            return hist if len(hist) > 0 else None
        
        # Check SQLite cache
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute('SELECT data, updated FROM history_cache WHERE ticker = ? AND period = ?', 
                      (ticker, period))
        row = cursor.fetchone()
        
        if row:
            updated = datetime.fromisoformat(row[1])
            if datetime.now() - updated < timedelta(hours=6):
                hist = pickle.loads(row[0])
                conn.close()
                if as_of_date:
                    hist = hist[hist.index <= as_of_date]
                return hist if len(hist) > 0 else None
        
        # Fetch from yfinance
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            
            if hist is None or len(hist) == 0:
                conn.close()
                return None
            
            # Cache it
            cursor.execute('''
                INSERT OR REPLACE INTO history_cache (ticker, period, data, updated)
                VALUES (?, ?, ?, ?)
            ''', (ticker, period, pickle.dumps(hist), datetime.now().isoformat()))
            conn.commit()
            conn.close()
            
            if as_of_date:
                hist = hist[hist.index <= as_of_date]
            
            return hist if len(hist) > 0 else None
        except Exception as e:
            conn.close()
            print(f"Error fetching history for {ticker}: {e}", file=sys.stderr)
            return None
    
    def _calc_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return 50.0
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
    
    def _calc_sector_etf_momentum(self, sector: str, as_of_date: Optional[datetime] = None) -> float:
        """Calculate 3M momentum for sector ETF"""
        etf = self.SECTOR_ETF_MAP.get(sector)
        if not etf:
            return 0.0
        
        hist = self._get_history(etf, period='1y', as_of_date=as_of_date)
        if hist is None or len(hist) < 63:
            return 0.0
        
        close = hist['Close'].dropna()
        if len(close) < 63:
            return 0.0
        
        mom_3m = (close.iloc[-1] / close.iloc[-63] - 1)
        return mom_3m
    
    def score_stock(self, ticker: str, as_of_date: Optional[datetime] = None, verbose: bool = False) -> dict:
        """
        Score stock using 4-layer system
        
        Args:
            ticker: Stock symbol
            as_of_date: If provided, only use data available up to this date (for blind backtesting)
            verbose: Print detailed scoring breakdown
        
        Returns:
            Dict with score, factors, and metadata
        """
        score = 0
        factors = {}
        
        # Get data
        info = self._get_info(ticker)
        hist = self._get_history(ticker, period='2y', as_of_date=as_of_date)
        
        if hist is None or len(hist) < 200:
            return {'ticker': ticker, 'score': -999, 'factors': {'error': 'insufficient_data'}}
        
        close = hist['Close'].dropna()
        if len(close) < 200:
            return {'ticker': ticker, 'score': -999, 'factors': {'error': 'insufficient_data'}}
        
        price = close.iloc[-1]
        
        # ============================================================
        # LAYER 1: MOMENTUM (max 20 points)
        # ============================================================
        
        # Near 52w high (max +5)
        high_52w = close.iloc[-252:].max() if len(close) >= 252 else close.max()
        pct_from_high = (high_52w - price) / high_52w
        if pct_from_high <= 0.03:
            score += 5; factors['near_52w_high'] = 5
        elif pct_from_high <= 0.05:
            score += 4; factors['near_52w_high'] = 4
        elif pct_from_high <= 0.10:
            score += 2; factors['near_52w_high'] = 2
        
        # 3M momentum (max +4)
        if len(close) >= 63:
            mom_3m = (price / close.iloc[-63] - 1)
            if mom_3m > 0.40:
                score += 4; factors['mom_3m'] = 4
            elif mom_3m > 0.25:
                score += 3; factors['mom_3m'] = 3
            elif mom_3m > 0.10:
                score += 2; factors['mom_3m'] = 2
            elif mom_3m > 0:
                score += 1; factors['mom_3m'] = 1
        else:
            mom_3m = 0
        
        # 6M momentum (max +4)
        if len(close) >= 126:
            mom_6m = (price / close.iloc[-126] - 1)
            if mom_6m > 0.75:
                score += 4; factors['mom_6m'] = 4
            elif mom_6m > 0.50:
                score += 3; factors['mom_6m'] = 3
            elif mom_6m > 0.25:
                score += 2; factors['mom_6m'] = 2
        else:
            mom_6m = 0
        
        # RSI (max +3)
        rsi = self._calc_rsi(close, 14)
        if rsi > 75:
            score += 3; factors['rsi_strong'] = 3
        elif rsi > 65:
            score += 2; factors['rsi_strong'] = 2
        elif rsi > 55:
            score += 1; factors['rsi_ok'] = 1
        
        # Price vs 200MA (max +4)
        ma200 = close.rolling(200).mean().iloc[-1]
        pct_above_200ma = (price / ma200 - 1) if ma200 > 0 else 0
        if pct_above_200ma > 0.50:
            score += 4; factors['above_200ma'] = 4
        elif pct_above_200ma > 0.30:
            score += 3; factors['above_200ma'] = 3
        elif pct_above_200ma > 0.15:
            score += 2; factors['above_200ma'] = 2
        
        # ============================================================
        # LAYER 2: FUNDAMENTALS (max 15 points)
        # ============================================================
        
        # Revenue growth (max +4)
        rev_growth = info.get('revenueGrowth', 0) or 0
        if rev_growth > 0.30:
            score += 4; factors['rev_growth_high'] = 4
        elif rev_growth > 0.15:
            score += 3; factors['rev_growth_good'] = 3
        elif rev_growth > 0.05:
            score += 2; factors['rev_growth_ok'] = 2
        
        # Earnings positive (+2) or negative (-2)
        net_income = info.get('netIncomeToCommon', 0) or 0
        if net_income > 0:
            score += 2; factors['earnings_positive'] = 2
        elif net_income < 0:
            score -= 2; factors['earnings_negative'] = -2
        
        # Gross margin (max +2)
        gross_margin = info.get('grossMargins', 0) or 0
        if gross_margin > 0.40:
            score += 2; factors['margin_high'] = 2
        elif gross_margin > 0.25:
            score += 1; factors['margin_ok'] = 1
        
        # Forward P/E (max +4)
        forward_pe = info.get('forwardPE', 0) or 0
        if 0 < forward_pe < 15:
            score += 4; factors['deep_value'] = 4
        elif 0 < forward_pe < 25:
            score += 3; factors['fair_value'] = 3
        
        # Debt/Equity < 1.0 (+1)
        debt_equity = info.get('debtToEquity', 0) or 0
        if debt_equity > 0:
            debt_equity = debt_equity / 100  # yfinance returns as percentage
        if 0 <= debt_equity < 1.0:
            score += 1; factors['low_debt'] = 1
        
        # Free cash flow positive (+2)
        free_cf = info.get('freeCashflow', 0) or 0
        if free_cf > 0:
            score += 2; factors['fcf_positive'] = 2
        
        # ============================================================
        # LAYER 3: EARNINGS CATALYST (max 10 points)
        # ============================================================
        
        # Earnings quarterly growth (proxy for surprise)
        earnings_growth = info.get('earningsQuarterlyGrowth', 0) or 0
        if earnings_growth > 0.10:
            score += 4; factors['earnings_surprise_high'] = 4
        elif earnings_growth > 0.05:
            score += 3; factors['earnings_surprise_good'] = 3
        elif earnings_growth > 0:
            score += 2; factors['earnings_surprise_ok'] = 2
        
        # Revenue quarterly growth (proxy for revenue surprise)
        if rev_growth > 0.05:
            score += 3; factors['revenue_surprise_good'] = 3
        elif rev_growth > 0:
            score += 2; factors['revenue_surprise_ok'] = 2
        
        # Consecutive beats (approximated by earnings growth + revenue growth both positive)
        if earnings_growth > 0 and rev_growth > 0:
            score += 3; factors['consecutive_beats'] = 3
        
        # ============================================================
        # LAYER 4: THEMATIC / SECTOR TIMING (max 10 points)
        # ============================================================
        
        sector = info.get('sector', '')
        
        # Sector ETF momentum
        sector_mom = self._calc_sector_etf_momentum(sector, as_of_date)
        if sector_mom > 0.10:
            score += 5; factors['sector_on_fire'] = 5
        elif sector_mom > 0.05:
            score += 3; factors['sector_in_favor'] = 3
        elif sector_mom < -0.05:
            score -= 3; factors['sector_out_favor'] = -3
        
        # Gold theme (if GLD up and stock is Materials)
        gld_hist = self._get_history('GLD', period='1y', as_of_date=as_of_date)
        if gld_hist is not None and len(gld_hist) >= 63 and sector == 'Materials':
            gld_close = gld_hist['Close'].dropna()
            if len(gld_close) >= 63:
                gld_mom = (gld_close.iloc[-1] / gld_close.iloc[-63] - 1)
                if gld_mom > 0.05:
                    score += 3; factors['gold_theme'] = 3
        
        # Small cap momentum (IWM outperforming SPY)
        iwm_hist = self._get_history('IWM', period='1y', as_of_date=as_of_date)
        spy_hist = self._get_history('SPY', period='1y', as_of_date=as_of_date)
        
        if iwm_hist is not None and spy_hist is not None:
            if len(iwm_hist) >= 63 and len(spy_hist) >= 63:
                iwm_close = iwm_hist['Close'].dropna()
                spy_close = spy_hist['Close'].dropna()
                
                if len(iwm_close) >= 63 and len(spy_close) >= 63:
                    iwm_mom = (iwm_close.iloc[-1] / iwm_close.iloc[-63] - 1)
                    spy_mom = (spy_close.iloc[-1] / spy_close.iloc[-63] - 1)
                    
                    if iwm_mom > spy_mom:
                        score += 2; factors['small_cap_favor'] = 2
        
        # ============================================================
        # LAYER 5: PENALTIES (max -15)
        # ============================================================
        
        # Market cap penalties
        mcap = info.get('marketCap', 0)
        mcap_b = mcap / 1e9 if mcap else 0
        
        if mcap_b > 50:
            score -= 5; factors['mega_cap_penalty'] = -5
        elif mcap_b < 0.3:
            score -= 3; factors['micro_cap_penalty'] = -3
        
        # Energy sector penalty
        if sector == 'Energy':
            score -= 3; factors['energy_penalty'] = -3
        
        # RSI too low
        if rsi < 35:
            score -= 3; factors['rsi_weak_penalty'] = -3
        
        # Below 200MA penalty
        if pct_above_200ma < -0.10:
            score -= 3; factors['below_200ma_penalty'] = -3
        
        # Negative 6M momentum penalty
        if mom_6m < 0:
            score -= 3; factors['mom_6m_neg_penalty'] = -3
        
        result = {
            'ticker': ticker,
            'score': score,
            'factors': factors,
            'sector': sector,
            'mcap_b': mcap_b,
            'mom_3m': mom_3m,
            'mom_6m': mom_6m,
            'rsi': rsi,
            'pct_from_high': pct_from_high,
            'pct_above_200ma': pct_above_200ma,
            'rev_growth': rev_growth,
            'forward_pe': forward_pe,
        }
        
        if verbose:
            print(f"\n{ticker} Score Breakdown:")
            print(f"  Total Score: {score}")
            print(f"  Factors: {json.dumps(factors, indent=4)}")
            print(f"  Sector: {sector}")
            print(f"  Market Cap: ${mcap_b:.2f}B")
            print(f"  Momentum: 3M={mom_3m:.1%}, 6M={mom_6m:.1%}")
            print(f"  RSI: {rsi:.1f}")
            print(f"  From 52w high: {pct_from_high:.1%}")
        
        return result
    
    def prefilter_universe(self, min_6m_return: float = 0.10, 
                          as_of_date: Optional[datetime] = None,
                          verbose: bool = True) -> List[str]:
        """
        Fast pre-filter: 6M return > 10% AND price > 50MA
        Uses price cache for speed (lowered threshold to 10% to ensure more candidates)
        """
        if verbose:
            print(f"\nPre-filtering with price cache ({len(self.price_cache)} tickers)...", file=sys.stderr)
        
        filtered = []
        
        cache_tickers = list(self.price_cache.keys())
        if verbose:
            cache_iter = tqdm(cache_tickers, desc="Pre-filter", file=sys.stderr)
        else:
            cache_iter = cache_tickers
        
        for ticker in cache_iter:
            # Skip ETFs
            if ticker in self.sector_etfs:
                continue
            
            try:
                hist = self.price_cache[ticker].copy()
                
                # Filter by as_of_date
                if as_of_date:
                    # Make as_of_date timezone-aware if needed
                    if hist.index.tzinfo is not None and as_of_date.tzinfo is None:
                        as_of_date = as_of_date.replace(tzinfo=hist.index.tzinfo)
                    hist = hist[hist.index <= as_of_date]
                
                if len(hist) < 126:
                    continue
                
                close = hist['Close'].dropna()
                if len(close) < 126:
                    continue
                
                # 6M momentum check
                mom_6m = (close.iloc[-1] / close.iloc[-126] - 1)
                
                if mom_6m <= min_6m_return:
                    continue
                
                # 50MA check
                ma50 = close.rolling(50).mean().iloc[-1]
                price = close.iloc[-1]
                
                if price <= ma50:
                    continue
                
                filtered.append(ticker)
                
            except Exception as e:
                continue
        
        if verbose:
            print(f"Pre-filter complete: {len(filtered)} stocks passed", file=sys.stderr)
        
        return filtered
    
    def get_top_picks(self, n: int = 10, as_of_date: Optional[datetime] = None,
                     use_prefilter: bool = True, verbose: bool = True) -> List[dict]:
        """Score stocks and return top N picks"""
        
        # Determine universe to score
        if use_prefilter:
            universe = self.prefilter_universe(as_of_date=as_of_date, verbose=verbose)
            # Fallback: if pre-filter returns nothing, use a smaller random sample
            if len(universe) == 0 and len(self.price_cache) > 0:
                import random
                # Use top 100 tickers by alphabet (simple fallback)
                stock_tickers = [t for t in sorted(self.price_cache.keys()) if t not in self.sector_etfs]
                universe = stock_tickers[:100]
                if verbose:
                    print(f"Pre-filter returned 0, using fallback sample of {len(universe)} stocks", file=sys.stderr)
        else:
            universe = self.universe
        
        if len(universe) == 0:
            if verbose:
                print("No stocks to score!", file=sys.stderr)
            return []
        
        results = []
        
        if verbose:
            print(f"\nScoring {len(universe)} stocks...", file=sys.stderr)
            universe_iter = tqdm(universe, desc="Scoring", file=sys.stderr)
        else:
            universe_iter = universe
        
        for ticker in universe_iter:
            result = self.score_stock(ticker, as_of_date=as_of_date)
            if result['score'] > -999:
                results.append(result)
        
        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        
        if verbose:
            print(f"\nScoring complete. {len(results)} valid scores.", file=sys.stderr)
        
        return results[:n]
    
    def run_blind_backtest(self, picks_csv: str, verbose: bool = True) -> dict:
        """
        Run blind backtest on historical pick dates
        
        Strategy:
        - Pick dates: 1st and 15th of each month, May 2023 → Feb 2026
        - At each date, score ALL stocks using ONLY data available up to that date
        - Pick top 2 by score
        - Buy at pick date, sell at next pick date
        - 4% allocation per pick from $100K base
        - Track all trades, P&L, win rate
        - Compare overlap with actual picks
        """
        print("\n" + "="*80, file=sys.stderr)
        print("BLIND BACKTEST - Alpha Picker v3", file=sys.stderr)
        print("="*80, file=sys.stderr)
        
        # Load historical picks
        historical_df = pd.read_csv(picks_csv)
        historical_df['PickDate'] = pd.to_datetime(historical_df['PickDate'])
        historical_tickers = set(historical_df['Symbol'].unique())
        
        # Generate pick dates (1st and 15th, May 2023 → Feb 2026)
        pick_dates = []
        start = datetime(2023, 5, 1)
        end = datetime(2026, 2, 15)
        
        current = start
        while current <= end:
            pick_dates.append(current)
            
            # Next date is either 15th of same month or 1st of next month
            if current.day == 1:
                pick_dates.append(datetime(current.year, current.month, 15))
                # Move to next month
                if current.month == 12:
                    current = datetime(current.year + 1, 1, 1)
                else:
                    current = datetime(current.year, current.month + 1, 1)
            else:
                # Already at 15th, skip to next iteration
                if current.month == 12:
                    current = datetime(current.year + 1, 1, 1)
                else:
                    current = datetime(current.year, current.month + 1, 1)
        
        print(f"\nBacktest period: {pick_dates[0].date()} to {pick_dates[-1].date()}", file=sys.stderr)
        print(f"Pick dates: {len(pick_dates)}", file=sys.stderr)
        print(f"Historical picks to compare: {len(historical_tickers)} unique tickers", file=sys.stderr)
        
        # Run backtest
        portfolio_value = self.initial_cash
        cash = self.initial_cash
        trades = []
        positions = []  # Current positions
        
        algo_picks_all = []  # All algo picks across all dates
        overlap_count = 0
        
        for i, pick_date in enumerate(tqdm(pick_dates, desc="Backtesting", file=sys.stderr)):
            # Get top 2 picks as of this date
            top_picks = self.get_top_picks(n=2, as_of_date=pick_date, use_prefilter=True, verbose=False)
            
            if len(top_picks) == 0:
                continue
            
            # Close existing positions (sell at current date)
            for pos in positions:
                ticker = pos['ticker']
                shares = pos['shares']
                buy_price = pos['buy_price']
                buy_date = pos['buy_date']
                
                # Get sell price
                hist = self._get_history(ticker, period='2y', as_of_date=pick_date)
                if hist is None or len(hist) == 0:
                    sell_price = buy_price  # No data, assume flat
                else:
                    sell_price = hist['Close'].iloc[-1]
                
                proceeds = shares * sell_price
                cash += proceeds
                
                pnl = proceeds - pos['cost']
                pnl_pct = (sell_price / buy_price - 1) * 100
                
                trades.append({
                    'ticker': ticker,
                    'buy_date': buy_date,
                    'sell_date': pick_date,
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'shares': shares,
                    'cost': pos['cost'],
                    'proceeds': proceeds,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'hold_days': (pick_date - buy_date).days
                })
            
            positions = []
            
            # Open new positions (buy at current date)
            allocation_per_pick = self.initial_cash * 0.04  # 4% per pick
            
            for pick in top_picks:
                ticker = pick['ticker']
                
                # Get buy price
                hist = self._get_history(ticker, period='2y', as_of_date=pick_date)
                if hist is None or len(hist) == 0:
                    continue
                
                buy_price = hist['Close'].iloc[-1]
                shares = allocation_per_pick / buy_price
                cost = shares * buy_price
                
                if cost > cash:
                    # Not enough cash, skip
                    continue
                
                cash -= cost
                
                positions.append({
                    'ticker': ticker,
                    'buy_date': pick_date,
                    'buy_price': buy_price,
                    'shares': shares,
                    'cost': cost
                })
                
                # Track algo picks
                algo_picks_all.append({
                    'ticker': ticker,
                    'date': pick_date,
                    'score': pick['score']
                })
                
                # Check overlap with historical
                if ticker in historical_tickers:
                    overlap_count += 1
        
        # Close final positions at end date
        final_date = pick_dates[-1]
        for pos in positions:
            ticker = pos['ticker']
            shares = pos['shares']
            buy_price = pos['buy_price']
            buy_date = pos['buy_date']
            
            hist = self._get_history(ticker, period='2y', as_of_date=final_date)
            if hist is None or len(hist) == 0:
                sell_price = buy_price
            else:
                sell_price = hist['Close'].iloc[-1]
            
            proceeds = shares * sell_price
            cash += proceeds
            
            pnl = proceeds - pos['cost']
            pnl_pct = (sell_price / buy_price - 1) * 100
            
            trades.append({
                'ticker': ticker,
                'buy_date': buy_date,
                'sell_date': final_date,
                'buy_price': buy_price,
                'sell_price': sell_price,
                'shares': shares,
                'cost': pos['cost'],
                'proceeds': proceeds,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'hold_days': (final_date - buy_date).days
            })
        
        final_value = cash
        total_return = (final_value / self.initial_cash - 1) * 100
        
        # Calculate metrics
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] <= 0]
        win_rate = len(winning_trades) / len(trades) * 100 if trades else 0
        
        avg_win = np.mean([t['pnl_pct'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl_pct'] for t in losing_trades]) if losing_trades else 0
        
        # SPY benchmark
        spy_start = self._get_history('SPY', period='2y', as_of_date=pick_dates[0])
        spy_end = self._get_history('SPY', period='2y', as_of_date=pick_dates[-1])
        
        if spy_start is not None and spy_end is not None and len(spy_start) > 0 and len(spy_end) > 0:
            spy_return = (spy_end['Close'].iloc[-1] / spy_start['Close'].iloc[-1] - 1) * 100
        else:
            spy_return = 0
        
        # Overlap analysis
        algo_tickers = set([p['ticker'] for p in algo_picks_all])
        overlap_tickers = algo_tickers & historical_tickers
        overlap_pct = (len(overlap_tickers) / len(historical_tickers)) * 100 if historical_tickers else 0
        
        # Summary
        result = {
            'start_date': pick_dates[0],
            'end_date': pick_dates[-1],
            'pick_dates_count': len(pick_dates),
            'initial_cash': self.initial_cash,
            'final_value': final_value,
            'total_return_pct': total_return,
            'spy_return_pct': spy_return,
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate_pct': win_rate,
            'avg_win_pct': avg_win,
            'avg_loss_pct': avg_loss,
            'algo_picks_count': len(algo_picks_all),
            'historical_picks_count': len(historical_tickers),
            'overlap_count': len(overlap_tickers),
            'overlap_pct': overlap_pct,
            'overlap_tickers': sorted(overlap_tickers),
            'trades': trades,
            'algo_picks_all': algo_picks_all,
        }
        
        return result


def main():
    """CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Alpha Picker v3 - 4-Layer Scoring + Backtest')
    parser.add_argument('command', choices=[
        'alpha-score', 'alpha-picks', 'alpha-backtest'
    ])
    parser.add_argument('ticker', nargs='?', help='Ticker symbol')
    parser.add_argument('--n', type=int, default=10, help='Number of picks')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    strategy = AlphaPickerV3()
    
    if args.command == 'alpha-score':
        if not args.ticker:
            print("Error: ticker required for alpha-score", file=sys.stderr)
            sys.exit(1)
        
        result = strategy.score_stock(args.ticker, verbose=True)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'alpha-picks':
        picks = strategy.get_top_picks(n=args.n, verbose=True)
        print(json.dumps(picks, indent=2))
    
    elif args.command == 'alpha-backtest':
        csv_path = '/home/quant/apps/quantclaw-data/data/stock_picks.csv'
        result = strategy.run_blind_backtest(csv_path, verbose=True)
        
        print(f"\n{'='*80}")
        print("BACKTEST RESULTS")
        print(f"{'='*80}")
        print(f"Period: {result['start_date'].date()} → {result['end_date'].date()}")
        print(f"Pick dates: {result['pick_dates_count']}")
        print(f"\nPerformance:")
        print(f"  Initial cash: ${result['initial_cash']:,.0f}")
        print(f"  Final value: ${result['final_value']:,.0f}")
        print(f"  Total return: {result['total_return_pct']:.2f}%")
        print(f"  SPY return: {result['spy_return_pct']:.2f}%")
        print(f"  Alpha: {result['total_return_pct'] - result['spy_return_pct']:.2f}%")
        print(f"\nTrades:")
        print(f"  Total: {result['total_trades']}")
        print(f"  Winners: {result['winning_trades']} ({result['win_rate_pct']:.1f}%)")
        print(f"  Losers: {result['losing_trades']}")
        print(f"  Avg win: {result['avg_win_pct']:.2f}%")
        print(f"  Avg loss: {result['avg_loss_pct']:.2f}%")
        print(f"\nOverlap with Historical Picks:")
        print(f"  Historical picks: {result['historical_picks_count']}")
        print(f"  Algo picks: {result['algo_picks_count']}")
        print(f"  Overlap: {result['overlap_count']} ({result['overlap_pct']:.1f}%)")
        print(f"  Overlap tickers: {', '.join(result['overlap_tickers'])}")
        
        # Show sample trades
        print(f"\nSample Trades (first 10):")
        for i, trade in enumerate(result['trades'][:10], 1):
            print(f"  {i:2d}. {trade['ticker']:6s} "
                  f"{trade['buy_date'].date()} → {trade['sell_date'].date()} "
                  f"${trade['buy_price']:.2f} → ${trade['sell_price']:.2f} "
                  f"({trade['pnl_pct']:+.1f}%)")
        
        # Analysis: True positives, False positives, Missed picks
        print(f"\n{'='*80}")
        print("ANALYSIS")
        print(f"{'='*80}")
        
        # True positives (algo picks that match historical)
        algo_tickers = set([p['ticker'] for p in result['algo_picks_all']])
        historical_df = pd.read_csv('/home/quant/apps/quantclaw-data/data/stock_picks.csv')
        historical_tickers = set(historical_df['Symbol'].unique())
        
        true_positives = algo_tickers & historical_tickers
        false_positives = algo_tickers - historical_tickers
        missed_picks = historical_tickers - algo_tickers
        
        print(f"\nTrue Positives (Algo picked AND in historical):")
        for ticker in sorted(true_positives)[:20]:
            picks = [p for p in result['algo_picks_all'] if p['ticker'] == ticker]
            avg_score = np.mean([p['score'] for p in picks])
            print(f"  {ticker:6s} - picked {len(picks)} times, avg score {avg_score:.1f}")
        
        print(f"\nFalse Positives (Algo picked but NOT in historical) - Top 20:")
        fp_counts = {}
        for pick in result['algo_picks_all']:
            if pick['ticker'] in false_positives:
                if pick['ticker'] not in fp_counts:
                    fp_counts[pick['ticker']] = []
                fp_counts[pick['ticker']].append(pick['score'])
        
        fp_sorted = sorted(fp_counts.items(), key=lambda x: np.mean(x[1]), reverse=True)
        for ticker, scores in fp_sorted[:20]:
            print(f"  {ticker:6s} - picked {len(scores)} times, avg score {np.mean(scores):.1f}")
        
        print(f"\nMissed Picks (Historical but algo DIDN'T pick) - First 20:")
        for ticker in sorted(missed_picks)[:20]:
            # Score this ticker to see why it was missed
            score_result = strategy.score_stock(ticker)
            if score_result['score'] > -999:
                print(f"  {ticker:6s} - score {score_result['score']:.1f}, "
                      f"mom_6m={score_result.get('mom_6m', 0):.1%}, "
                      f"sector={score_result.get('sector', 'Unknown')}")
            else:
                print(f"  {ticker:6s} - insufficient data")


if __name__ == '__main__':
    main()
