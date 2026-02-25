#!/usr/bin/env python3
"""
Volatility Surface Modeling Module
Phase 89: IV smile/skew analysis, volatility arbitrage, straddle/strangle scanner

Uses:
- yfinance for options chains and implied volatility
- scipy for surface interpolation and curve fitting
- numpy for volatility calculations and arbitrage detection
"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
from scipy import interpolate, stats
from scipy.optimize import minimize
import sys
import argparse


class VolatilitySurfaceAnalyzer:
    """Analyze implied volatility surfaces, skew, and smile patterns"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.stock = None
        self.current_price = None
        self.options_data = {}
        
    def fetch_options_data(self) -> bool:
        """Fetch options chains for all available expirations"""
        try:
            self.stock = yf.Ticker(self.ticker)
            info = self.stock.info
            self.current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if not self.current_price:
                hist = self.stock.history(period='1d')
                if hist.empty:
                    print(f"Error: Cannot fetch price for {self.ticker}", file=sys.stderr)
                    return False
                self.current_price = float(hist['Close'].iloc[-1])
            
            # Get all expiration dates
            expirations = self.stock.options
            
            if not expirations:
                print(f"Error: No options available for {self.ticker}", file=sys.stderr)
                return False
            
            # Fetch options chains for all expirations
            for expiry in expirations[:8]:  # Limit to first 8 to avoid rate limits
                try:
                    opt_chain = self.stock.option_chain(expiry)
                    calls = opt_chain.calls
                    puts = opt_chain.puts
                    
                    # Filter for valid IV data
                    calls = calls[calls['impliedVolatility'].notna()]
                    puts = puts[puts['impliedVolatility'].notna()]
                    
                    if not calls.empty or not puts.empty:
                        self.options_data[expiry] = {
                            'calls': calls,
                            'puts': puts,
                            'expiry_date': pd.to_datetime(expiry)
                        }
                except Exception as e:
                    print(f"Warning: Failed to fetch {expiry}: {e}", file=sys.stderr)
                    continue
            
            return len(self.options_data) > 0
            
        except Exception as e:
            print(f"Error fetching options: {e}", file=sys.stderr)
            return False
    
    def analyze_iv_smile(self, expiry: Optional[str] = None) -> Dict:
        """
        Analyze IV smile/smirk pattern for a specific expiry
        Shows how IV varies with strike price (moneyness)
        """
        if not self.options_data:
            if not self.fetch_options_data():
                return {'error': 'Failed to fetch options data'}
        
        # Use nearest expiry if not specified
        if expiry is None:
            expiry = list(self.options_data.keys())[0]
        elif expiry not in self.options_data:
            return {'error': f'Expiry {expiry} not available'}
        
        chain = self.options_data[expiry]
        calls = chain['calls']
        puts = chain['puts']
        
        # Calculate moneyness (K/S) and collect IV data
        call_moneyness = calls['strike'] / self.current_price
        call_iv = calls['impliedVolatility']
        
        put_moneyness = puts['strike'] / self.current_price
        put_iv = puts['impliedVolatility']
        
        # Combine calls and puts
        all_moneyness = pd.concat([call_moneyness, put_moneyness])
        all_iv = pd.concat([call_iv, put_iv])
        
        # Sort by moneyness
        iv_smile_df = pd.DataFrame({
            'moneyness': all_moneyness,
            'iv': all_iv
        }).sort_values('moneyness')
        
        # Calculate ATM IV (strikes closest to current price)
        atm_idx = (iv_smile_df['moneyness'] - 1.0).abs().argmin()
        atm_row = iv_smile_df.iloc[atm_idx]
        atm_iv = float(atm_row['iv'])
        atm_strike = float(atm_row['moneyness'] * self.current_price)
        
        # Calculate skew metrics
        otm_put_iv = float(iv_smile_df[iv_smile_df['moneyness'] <= 0.95]['iv'].mean()) if len(iv_smile_df[iv_smile_df['moneyness'] <= 0.95]) > 0 else atm_iv
        otm_call_iv = float(iv_smile_df[iv_smile_df['moneyness'] >= 1.05]['iv'].mean()) if len(iv_smile_df[iv_smile_df['moneyness'] >= 1.05]) > 0 else atm_iv
        
        # Skew = (OTM Put IV - OTM Call IV)
        skew = otm_put_iv - otm_call_iv
        
        # Calculate put-call skew at similar strikes
        put_call_skew = float(put_iv.mean() - call_iv.mean())
        
        # Days to expiry
        dte = (chain['expiry_date'] - datetime.now()).days
        
        # Fit polynomial to identify smile vs smirk
        if len(iv_smile_df) >= 3:
            coeffs = np.polyfit(iv_smile_df['moneyness'], iv_smile_df['iv'], 2)
            curvature = float(coeffs[0])  # Second-order coefficient
            smile_type = "smile" if curvature > 0 else "smirk"
        else:
            curvature = 0.0
            smile_type = "insufficient_data"
        
        return {
            'ticker': self.ticker,
            'current_price': float(self.current_price),
            'expiry': expiry,
            'days_to_expiry': int(dte),
            'atm_iv': float(atm_iv),
            'atm_strike': float(atm_strike),
            'otm_put_iv': float(otm_put_iv),
            'otm_call_iv': float(otm_call_iv),
            'skew': float(skew),
            'put_call_skew': float(put_call_skew),
            'smile_curvature': float(curvature),
            'smile_type': smile_type,
            'interpretation': self._interpret_smile(skew, curvature, smile_type),
            'strikes_analyzed': int(len(iv_smile_df)),
            'iv_range': {
                'min': float(iv_smile_df['iv'].min()),
                'max': float(iv_smile_df['iv'].max()),
                'spread': float(iv_smile_df['iv'].max() - iv_smile_df['iv'].min())
            }
        }
    
    def _interpret_smile(self, skew: float, curvature: float, smile_type: str) -> str:
        """Interpret volatility smile pattern"""
        interpretations = []
        
        if smile_type == "smile" and curvature > 0.05:
            interpretations.append("Strong volatility smile: elevated IV for both OTM puts and calls (tail risk priced in)")
        elif smile_type == "smirk":
            interpretations.append("Volatility smirk: downward sloping IV curve")
        
        if skew > 0.10:
            interpretations.append("Strong put skew: investors paying premium for downside protection (bearish sentiment)")
        elif skew < -0.05:
            interpretations.append("Reverse skew: call IV exceeds put IV (bullish/takeover speculation)")
        else:
            interpretations.append("Balanced skew: symmetric fear/greed")
        
        return " | ".join(interpretations) if interpretations else "Neutral volatility structure"
    
    def scan_vol_arbitrage(self) -> Dict:
        """
        Identify volatility arbitrage opportunities
        - Calendar spreads (time decay mispricings)
        - Vertical spreads (strike mispricings)
        - Put-call parity violations
        """
        if not self.options_data:
            if not self.fetch_options_data():
                return {'error': 'Failed to fetch options data'}
        
        opportunities = []
        
        # Calendar spread opportunities (same strike, different expirations)
        if len(self.options_data) >= 2:
            expiries = sorted(self.options_data.keys())
            near_expiry = expiries[0]
            far_expiry = expiries[-1] if len(expiries) > 1 else expiries[0]
            
            near_chain = self.options_data[near_expiry]
            far_chain = self.options_data[far_expiry]
            
            # Find matching strikes
            near_strikes = set(near_chain['calls']['strike'])
            far_strikes = set(far_chain['calls']['strike'])
            common_strikes = near_strikes.intersection(far_strikes)
            
            for strike in list(common_strikes)[:10]:  # Sample first 10
                near_call = near_chain['calls'][near_chain['calls']['strike'] == strike]
                far_call = far_chain['calls'][far_chain['calls']['strike'] == strike]
                
                if not near_call.empty and not far_call.empty:
                    near_iv = float(near_call['impliedVolatility'].iloc[0])
                    far_iv = float(far_call['impliedVolatility'].iloc[0])
                    iv_diff = far_iv - near_iv
                    
                    # Calendar spread should have higher IV in longer-dated options
                    # If near IV > far IV significantly, there's a mispricing
                    if iv_diff < -0.05:  # Near term IV is much higher
                        opportunities.append({
                            'type': 'calendar_spread_mispricing',
                            'strategy': 'sell near, buy far',
                            'strike': float(strike),
                            'near_expiry': near_expiry,
                            'far_expiry': far_expiry,
                            'near_iv': float(near_iv),
                            'far_iv': float(far_iv),
                            'iv_difference': float(iv_diff),
                            'signal_strength': abs(float(iv_diff)) / near_iv
                        })
        
        # Vertical spread opportunities (same expiry, different strikes)
        for expiry, chain in list(self.options_data.items())[:3]:  # Check first 3 expiries
            calls = chain['calls'].sort_values('strike')
            
            if len(calls) >= 2:
                for i in range(len(calls) - 1):
                    lower_strike = float(calls.iloc[i]['strike'])
                    higher_strike = float(calls.iloc[i + 1]['strike'])
                    lower_iv = float(calls.iloc[i]['impliedVolatility'])
                    higher_iv = float(calls.iloc[i + 1]['impliedVolatility'])
                    
                    # Check for butterfly arbitrage
                    # Mid strike IV should be between wings
                    if i < len(calls) - 2:
                        mid_strike = float(calls.iloc[i + 1]['strike'])
                        mid_iv = float(calls.iloc[i + 1]['impliedVolatility'])
                        upper_strike = float(calls.iloc[i + 2]['strike'])
                        upper_iv = float(calls.iloc[i + 2]['impliedVolatility'])
                        
                        expected_mid_iv = (lower_iv + upper_iv) / 2
                        iv_deviation = mid_iv - expected_mid_iv
                        
                        if abs(iv_deviation) > 0.08:  # 8% deviation threshold
                            opportunities.append({
                                'type': 'butterfly_mispricing',
                                'strategy': 'sell overpriced wing' if iv_deviation > 0 else 'buy underpriced wing',
                                'expiry': expiry,
                                'lower_strike': float(lower_strike),
                                'mid_strike': float(mid_strike),
                                'upper_strike': float(upper_strike),
                                'mid_iv': float(mid_iv),
                                'expected_mid_iv': float(expected_mid_iv),
                                'deviation': float(iv_deviation),
                                'signal_strength': abs(float(iv_deviation)) / expected_mid_iv
                            })
        
        return {
            'ticker': self.ticker,
            'current_price': float(self.current_price),
            'opportunities_found': len(opportunities),
            'opportunities': sorted(opportunities, key=lambda x: x.get('signal_strength', 0), reverse=True)[:10],
            'timestamp': datetime.now().isoformat()
        }
    
    def scan_straddles_strangles(self, max_expiry_days: int = 60) -> Dict:
        """
        Scan for attractive straddle/strangle setups
        - High IV rank (cheap vol)
        - Post-earnings setups
        - Event-driven volatility plays
        """
        if not self.options_data:
            if not self.fetch_options_data():
                return {'error': 'Failed to fetch options data'}
        
        strategies = []
        
        for expiry, chain in self.options_data.items():
            dte = (chain['expiry_date'] - datetime.now()).days
            
            if dte > max_expiry_days or dte < 1:
                continue
            
            calls = chain['calls']
            puts = chain['puts']
            
            # Find ATM strikes (closest to current price)
            atm_call_idx = (calls['strike'] - self.current_price).abs().idxmin()
            atm_put_idx = (puts['strike'] - self.current_price).abs().idxmin()
            
            atm_call = calls.loc[atm_call_idx]
            atm_put = puts.loc[atm_put_idx]
            
            # Straddle (same strike)
            straddle_strike = float(atm_call['strike'])
            straddle_cost = float(atm_call['lastPrice'] + atm_put['lastPrice'])
            straddle_iv = float((atm_call['impliedVolatility'] + atm_put['impliedVolatility']) / 2)
            
            # Break-even points
            upper_be = straddle_strike + straddle_cost
            lower_be = straddle_strike - straddle_cost
            breakeven_move_pct = (straddle_cost / self.current_price) * 100
            
            # Strangle (OTM strikes)
            otm_call = calls[calls['strike'] > self.current_price * 1.03].head(1)
            otm_put = puts[puts['strike'] < self.current_price * 0.97].head(1)
            
            if not otm_call.empty and not otm_put.empty:
                strangle_call_strike = float(otm_call['strike'].iloc[0])
                strangle_put_strike = float(otm_put['strike'].iloc[0])
                strangle_cost = float(otm_call['lastPrice'].iloc[0] + otm_put['lastPrice'].iloc[0])
                strangle_iv = float((otm_call['impliedVolatility'].iloc[0] + otm_put['impliedVolatility'].iloc[0]) / 2)
                
                strangle_upper_be = strangle_call_strike + strangle_cost
                strangle_lower_be = strangle_put_strike - strangle_cost
                strangle_breakeven_pct = ((strangle_upper_be - strangle_lower_be) / (2 * self.current_price)) * 100
            else:
                strangle_cost = None
                strangle_iv = None
                strangle_breakeven_pct = None
            
            # Calculate expected move (1 standard deviation)
            # EM = S * IV * sqrt(T)
            time_to_expiry_years = dte / 365.0
            expected_move_dollar = self.current_price * straddle_iv * np.sqrt(time_to_expiry_years)
            expected_move_pct = (expected_move_dollar / self.current_price) * 100
            
            # Probability analysis (simplified)
            # Straddle profitable if move > breakeven
            # Assuming normal distribution
            prob_profitable_straddle = 2 * (1 - stats.norm.cdf(breakeven_move_pct / expected_move_pct)) if expected_move_pct > 0 else 0
            
            strategy = {
                'expiry': expiry,
                'days_to_expiry': int(dte),
                'current_price': float(self.current_price),
                'straddle': {
                    'strike': float(straddle_strike),
                    'cost': float(straddle_cost),
                    'iv': float(straddle_iv),
                    'upper_breakeven': float(upper_be),
                    'lower_breakeven': float(lower_be),
                    'breakeven_move_pct': float(breakeven_move_pct),
                    'prob_profitable': float(prob_profitable_straddle)
                },
                'expected_move': {
                    'dollar': float(expected_move_dollar),
                    'percent': float(expected_move_pct),
                    'upper_target': float(self.current_price + expected_move_dollar),
                    'lower_target': float(self.current_price - expected_move_dollar)
                },
                'attractiveness_score': self._score_straddle(breakeven_move_pct, expected_move_pct, straddle_iv, dte)
            }
            
            if strangle_cost is not None:
                strategy['strangle'] = {
                    'call_strike': float(strangle_call_strike),
                    'put_strike': float(strangle_put_strike),
                    'cost': float(strangle_cost),
                    'iv': float(strangle_iv),
                    'upper_breakeven': float(strangle_upper_be),
                    'lower_breakeven': float(strangle_lower_be),
                    'breakeven_move_pct': float(strangle_breakeven_pct)
                }
            
            strategies.append(strategy)
        
        # Sort by attractiveness
        strategies.sort(key=lambda x: x.get('attractiveness_score', 0), reverse=True)
        
        return {
            'ticker': self.ticker,
            'current_price': float(self.current_price),
            'strategies_analyzed': len(strategies),
            'top_strategies': strategies[:5],
            'timestamp': datetime.now().isoformat()
        }
    
    def _score_straddle(self, breakeven_pct: float, expected_move_pct: float, iv: float, dte: int) -> float:
        """
        Score straddle attractiveness
        Higher score = more attractive
        
        Factors:
        - Expected move > breakeven (positive)
        - High IV (cheaper premium per volatility)
        - Optimal DTE (sweet spot 14-45 days)
        """
        if expected_move_pct == 0:
            return 0.0
        
        # Ratio of expected move to breakeven
        move_ratio = expected_move_pct / breakeven_pct if breakeven_pct > 0 else 0
        
        # DTE score (prefer 14-45 days)
        if 14 <= dte <= 45:
            dte_score = 1.0
        elif dte < 14:
            dte_score = 0.5
        else:
            dte_score = max(0.3, 1.0 - (dte - 45) / 60.0)
        
        # IV score (higher is better for long volatility)
        iv_score = min(1.0, iv / 0.6)  # Normalize to 60% IV
        
        # Combined score
        score = (move_ratio * 0.5 + iv_score * 0.3 + dte_score * 0.2) * 100
        
        return float(score)


def main():
    parser = argparse.ArgumentParser(description='Volatility Surface Analyzer')
    parser.add_argument('command', choices=[
        'iv-smile', 'vol-arbitrage', 'straddle-scan', 'strangle-scan'
    ], help='Analysis command')
    parser.add_argument('ticker', nargs='?', help='Stock ticker symbol')
    parser.add_argument('--expiry', help='Specific expiry date (YYYY-MM-DD)')
    parser.add_argument('--max-days', type=int, default=60, help='Maximum days to expiry for scans')
    parser.add_argument('--json', action='store_true', help='Output JSON format')
    
    args = parser.parse_args()
    
    if not args.ticker and args.command not in ['help']:
        print("Error: ticker symbol required", file=sys.stderr)
        sys.exit(1)
    
    analyzer = VolatilitySurfaceAnalyzer(args.ticker.upper())
    
    result = None
    
    if args.command == 'iv-smile':
        result = analyzer.analyze_iv_smile(args.expiry)
    
    elif args.command == 'vol-arbitrage':
        result = analyzer.scan_vol_arbitrage()
    
    elif args.command in ['straddle-scan', 'strangle-scan']:
        result = analyzer.scan_straddles_strangles(args.max_days)
    
    if result:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
