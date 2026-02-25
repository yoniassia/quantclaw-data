#!/usr/bin/env python3
"""
Sector Rotation Model Module
Phase 33: Economic cycle indicators, relative strength rotation strategies

Uses:
- yfinance for sector ETF data (XLK, XLF, XLE, XLV, XLI, XLP, XLU, XLRE, XLC, XLB, XLY)
- FRED API for economic cycle indicators (yield curve, ISM, CLI)
- Relative strength analysis for rotation signals
"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import sys
import os
from urllib.request import urlopen


class SectorRotationAnalyzer:
    """Sector rotation analysis with economic cycle context"""
    
    # Sector ETF mapping
    SECTOR_ETFS = {
        'XLK': 'Technology',
        'XLF': 'Financials',
        'XLE': 'Energy',
        'XLV': 'Healthcare',
        'XLI': 'Industrials',
        'XLP': 'Consumer Staples',
        'XLU': 'Utilities',
        'XLRE': 'Real Estate',
        'XLC': 'Communication Services',
        'XLB': 'Materials',
        'XLY': 'Consumer Discretionary'
    }
    
    # Economic cycle phases
    CYCLE_PHASES = ['Early', 'Mid', 'Late', 'Recession']
    
    # Sector performance by cycle phase (historical tendency)
    CYCLE_PERFORMANCE = {
        'Early': ['XLF', 'XLI', 'XLB', 'XLE'],  # Financials, Industrials, Materials, Energy
        'Mid': ['XLK', 'XLI', 'XLY', 'XLB'],    # Technology, Industrials, Consumer Disc, Materials
        'Late': ['XLE', 'XLB', 'XLI'],          # Energy, Materials, Industrials
        'Recession': ['XLP', 'XLU', 'XLV']      # Staples, Utilities, Healthcare
    }
    
    def __init__(self):
        self.fred_api_key = os.getenv('FRED_API_KEY', 'demo')  # Use demo mode if no key
        
    def fetch_sector_data(self, period: str = "6mo") -> Dict[str, pd.DataFrame]:
        """Fetch historical data for all sector ETFs"""
        data = {}
        for ticker, sector in self.SECTOR_ETFS.items():
            try:
                etf = yf.Ticker(ticker)
                hist = etf.history(period=period)
                if not hist.empty:
                    data[ticker] = hist
            except Exception as e:
                print(f"Warning: Could not fetch {ticker}: {e}", file=sys.stderr)
        return data
    
    def calculate_relative_strength(self, data: Dict[str, pd.DataFrame], lookback: int = 60) -> Dict:
        """
        Calculate relative strength for each sector vs SPY
        Returns momentum scores and rankings
        """
        results = {}
        
        # Fetch SPY as benchmark
        try:
            spy = yf.Ticker('SPY')
            spy_hist = spy.history(period=f"{lookback + 30}d")
            spy_returns = spy_hist['Close'].pct_change(lookback).iloc[-1]
        except Exception as e:
            print(f"Warning: Could not fetch SPY benchmark: {e}", file=sys.stderr)
            spy_returns = 0
        
        for ticker, df in data.items():
            if len(df) < lookback:
                continue
                
            # Calculate returns
            close_prices = df['Close']
            period_return = (close_prices.iloc[-1] / close_prices.iloc[-lookback] - 1) * 100
            
            # Calculate relative strength vs SPY
            relative_strength = period_return - (spy_returns * 100)
            
            # Calculate price momentum (ROC)
            roc_20 = (close_prices.iloc[-1] / close_prices.iloc[-20] - 1) * 100 if len(close_prices) >= 20 else 0
            roc_60 = period_return
            
            # Calculate volatility
            returns = close_prices.pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) * 100  # Annualized
            
            # Sharpe-like score (return / volatility)
            risk_adjusted_return = period_return / volatility if volatility > 0 else 0
            
            results[ticker] = {
                'sector': self.SECTOR_ETFS[ticker],
                'period_return': float(period_return),
                'relative_strength': float(relative_strength),
                'roc_20d': float(roc_20),
                'roc_60d': float(roc_60),
                'volatility': float(volatility),
                'risk_adjusted_return': float(risk_adjusted_return),
                'current_price': float(close_prices.iloc[-1])
            }
        
        # Rank by relative strength
        sorted_sectors = sorted(results.items(), key=lambda x: x[1]['relative_strength'], reverse=True)
        
        for rank, (ticker, data) in enumerate(sorted_sectors, 1):
            results[ticker]['rank'] = rank
            results[ticker]['quartile'] = 'Q1' if rank <= 3 else 'Q2' if rank <= 6 else 'Q3' if rank <= 9 else 'Q4'
        
        return results
    
    def fetch_fred_data(self, series_id: str, lookback_months: int = 12) -> Optional[pd.Series]:
        """
        Fetch economic data from FRED API
        Falls back to demo data if API unavailable
        """
        if self.fred_api_key == 'demo':
            # Return simulated data for demo mode
            return self._get_demo_fred_data(series_id, lookback_months)
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_months * 30)
            
            url = (f"https://api.stlouisfed.org/fred/series/observations"
                   f"?series_id={series_id}"
                   f"&api_key={self.fred_api_key}"
                   f"&file_type=json"
                   f"&observation_start={start_date.strftime('%Y-%m-%d')}"
                   f"&observation_end={end_date.strftime('%Y-%m-%d')}")
            
            with urlopen(url) as response:
                data = json.loads(response.read().decode())
                
            if 'observations' not in data:
                return None
                
            # Parse into pandas Series
            df = pd.DataFrame(data['observations'])
            df['date'] = pd.to_datetime(df['date'])
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df = df.dropna(subset=['value'])
            df = df.set_index('date')
            
            return df['value']
        except Exception as e:
            print(f"Warning: FRED API error for {series_id}: {e}", file=sys.stderr)
            return self._get_demo_fred_data(series_id, lookback_months)
    
    def _get_demo_fred_data(self, series_id: str, lookback_months: int) -> pd.Series:
        """Generate demo data when FRED API unavailable"""
        dates = pd.date_range(end=datetime.now(), periods=lookback_months, freq='ME')
        n_periods = len(dates)  # Use actual length
        
        # Simulated values based on series type
        if series_id == 'T10Y2Y':  # Yield curve
            values = np.random.normal(0.5, 0.3, n_periods)
        elif series_id == 'NAPM':  # ISM Manufacturing PMI
            values = np.random.normal(52, 3, n_periods)
        elif series_id == 'UNRATE':  # Unemployment rate
            values = np.random.normal(4.2, 0.5, n_periods)
        else:
            values = np.random.normal(50, 5, n_periods)
        
        return pd.Series(values, index=dates)
    
    def analyze_economic_cycle(self) -> Dict:
        """
        Analyze economic cycle indicators
        Returns cycle phase and supporting data
        """
        indicators = {}
        
        # 1. Yield Curve (10Y - 2Y Treasury)
        yield_curve = self.fetch_fred_data('T10Y2Y', lookback_months=24)
        if yield_curve is not None and len(yield_curve) > 0:
            current_spread = float(yield_curve.iloc[-1])
            avg_6m = float(yield_curve.tail(6).mean())
            trend = 'inverting' if current_spread < avg_6m else 'steepening'
            
            indicators['yield_curve'] = {
                'current_spread_bps': current_spread * 100,
                'avg_6m_spread_bps': avg_6m * 100,
                'trend': trend,
                'inverted': current_spread < 0,
                'signal': 'recession_risk' if current_spread < -0.2 else 'expanding' if current_spread > 1 else 'neutral'
            }
        
        # 2. ISM Manufacturing PMI
        ism_pmi = self.fetch_fred_data('NAPM', lookback_months=24)
        if ism_pmi is not None and len(ism_pmi) > 0:
            current_ism = float(ism_pmi.iloc[-1])
            prev_ism = float(ism_pmi.iloc[-2]) if len(ism_pmi) > 1 else current_ism
            
            indicators['ism_manufacturing'] = {
                'current': current_ism,
                'previous': prev_ism,
                'trend': 'expanding' if current_ism > prev_ism else 'contracting',
                'expansion': current_ism > 50,
                'signal': 'strong' if current_ism > 55 else 'weak' if current_ism < 45 else 'neutral'
            }
        
        # 3. Leading Economic Index (simulated via composite)
        # Using unemployment rate as proxy
        unemployment = self.fetch_fred_data('UNRATE', lookback_months=24)
        if unemployment is not None and len(unemployment) > 0:
            current_unemp = float(unemployment.iloc[-1])
            avg_12m = float(unemployment.tail(12).mean())
            
            indicators['unemployment'] = {
                'current': current_unemp,
                'avg_12m': avg_12m,
                'trend': 'rising' if current_unemp > avg_12m else 'falling',
                'signal': 'weak' if current_unemp > 5 else 'strong' if current_unemp < 4 else 'neutral'
            }
        
        # Determine overall cycle phase
        cycle_phase = self._determine_cycle_phase(indicators)
        
        return {
            'cycle_phase': cycle_phase,
            'indicators': indicators,
            'favorable_sectors': self.CYCLE_PERFORMANCE.get(cycle_phase, []),
            'analysis_date': datetime.now().isoformat(),
            'data_mode': 'demo' if self.fred_api_key == 'demo' else 'live'
        }
    
    def _determine_cycle_phase(self, indicators: Dict) -> str:
        """
        Determine economic cycle phase from indicators
        Simplified heuristic model
        """
        score = 0
        
        # Yield curve contribution
        if 'yield_curve' in indicators:
            if indicators['yield_curve']['inverted']:
                score -= 2
            elif indicators['yield_curve']['current_spread_bps'] > 100:
                score += 2
        
        # ISM contribution
        if 'ism_manufacturing' in indicators:
            ism = indicators['ism_manufacturing']['current']
            if ism > 55:
                score += 2
            elif ism < 45:
                score -= 2
        
        # Unemployment contribution
        if 'unemployment' in indicators:
            unemp = indicators['unemployment']['current']
            if unemp < 4:
                score += 1
            elif unemp > 6:
                score -= 2
        
        # Map score to phase
        if score >= 3:
            return 'Early'
        elif score >= 1:
            return 'Mid'
        elif score >= -1:
            return 'Late'
        else:
            return 'Recession'
    
    def generate_rotation_signals(self, lookback: int = 60) -> Dict:
        """
        Generate complete sector rotation analysis
        Combines relative strength + economic cycle
        """
        # Fetch sector data
        sector_data = self.fetch_sector_data(period=f"{lookback + 60}d")
        
        if not sector_data:
            return {'error': 'Could not fetch sector data'}
        
        # Calculate relative strength
        momentum = self.calculate_relative_strength(sector_data, lookback=lookback)
        
        # Analyze economic cycle
        cycle = self.analyze_economic_cycle()
        
        # Generate signals
        signals = []
        for ticker, data in momentum.items():
            # Check if sector is favored by current cycle
            cycle_favored = ticker in cycle['favorable_sectors']
            
            # Strong momentum + cycle alignment = BUY
            if data['rank'] <= 3 and cycle_favored:
                signal = 'STRONG_BUY'
            elif data['rank'] <= 3:
                signal = 'BUY'
            elif data['rank'] >= 9:
                signal = 'AVOID'
            elif cycle_favored:
                signal = 'HOLD'
            else:
                signal = 'NEUTRAL'
            
            signals.append({
                'ticker': ticker,
                'sector': data['sector'],
                'signal': signal,
                'rank': data['rank'],
                'relative_strength': data['relative_strength'],
                'period_return': data['period_return'],
                'cycle_favored': cycle_favored,
                'risk_adjusted_return': data['risk_adjusted_return']
            })
        
        # Sort by signal strength
        signal_order = {'STRONG_BUY': 0, 'BUY': 1, 'HOLD': 2, 'NEUTRAL': 3, 'AVOID': 4}
        signals.sort(key=lambda x: (signal_order[x['signal']], -x['relative_strength']))
        
        return {
            'signals': signals,
            'cycle_phase': cycle['cycle_phase'],
            'lookback_days': lookback,
            'analysis_date': datetime.now().isoformat(),
            'summary': {
                'strong_buy': len([s for s in signals if s['signal'] == 'STRONG_BUY']),
                'buy': len([s for s in signals if s['signal'] == 'BUY']),
                'hold': len([s for s in signals if s['signal'] == 'HOLD']),
                'avoid': len([s for s in signals if s['signal'] == 'AVOID'])
            }
        }


def main():
    """CLI handler"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'error': 'No command specified',
            'available_commands': ['sector-rotation', 'sector-momentum', 'economic-cycle']
        }))
        sys.exit(1)
    
    command = sys.argv[1]
    analyzer = SectorRotationAnalyzer()
    
    if command == 'sector-rotation':
        # Full rotation analysis
        lookback = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        result = analyzer.generate_rotation_signals(lookback=lookback)
        print(json.dumps(result, indent=2))
    
    elif command == 'sector-momentum':
        # Just momentum rankings
        lookback = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        sector_data = analyzer.fetch_sector_data(period=f"{lookback + 60}d")
        
        if not sector_data:
            print(json.dumps({'error': 'Could not fetch sector data'}))
            sys.exit(1)
        
        momentum = analyzer.calculate_relative_strength(sector_data, lookback=lookback)
        
        # Convert to sorted list
        sorted_sectors = sorted(momentum.items(), key=lambda x: x[1]['rank'])
        
        result = {
            'sectors': [
                {
                    'ticker': ticker,
                    'sector': data['sector'],
                    'rank': data['rank'],
                    'relative_strength': data['relative_strength'],
                    'period_return': data['period_return'],
                    'roc_20d': data['roc_20d'],
                    'volatility': data['volatility'],
                    'risk_adjusted_return': data['risk_adjusted_return']
                }
                for ticker, data in sorted_sectors
            ],
            'lookback_days': lookback,
            'analysis_date': datetime.now().isoformat()
        }
        
        print(json.dumps(result, indent=2))
    
    elif command == 'economic-cycle':
        # Economic cycle analysis only
        result = analyzer.analyze_economic_cycle()
        print(json.dumps(result, indent=2))
    
    else:
        print(json.dumps({
            'error': f'Unknown command: {command}',
            'available_commands': ['sector-rotation', 'sector-momentum', 'economic-cycle']
        }))
        sys.exit(1)


if __name__ == '__main__':
    main()
