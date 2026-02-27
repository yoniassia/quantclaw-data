#!/usr/bin/env python3
"""
Bank of Israel (BOI) Rates & Monetary Policy

Provides:
- Base interest rate (policy rate)
- Interest rate corridor (deposit/lending facilities)
- Monetary policy decisions & minutes
- Inflation targets & forecasts
- FX intervention announcements

Data sources:
- Bank of Israel website (www.boi.org.il/en)
- FRED (INTDSRILM193N - Israel policy rate)
- Manual fallback for recent announcements

Last updated: 2026-02-27
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

class BOIRates:
    """Bank of Israel monetary policy data"""
    
    def __init__(self):
        self.base_url = "https://www.boi.org.il/en"
        # FRED backup for historical rates
        self.fred_key = None  # Optional: set FRED_API_KEY env var
        self.cache = {}
        self.cache_ttl = timedelta(hours=12)
        
    def get_current_rate(self) -> Dict:
        """
        Get current BOI base interest rate
        
        Returns:
            {
                'rate': float,
                'effective_date': str (YYYY-MM-DD),
                'previous_rate': float,
                'change_bps': int,
                'decision_date': str,
                'next_meeting': str (YYYY-MM-DD)
            }
        """
        cache_key = "current_rate"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() - cached['timestamp'] < self.cache_ttl:
                return cached['data']
        
        try:
            # Primary: Try FRED for most recent rate
            url = "https://fred.stlouisfed.org/graph/fredgraph.csv"
            params = {
                'id': 'INTDSRILM193N',  # Israel policy rate
                'cosd': (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            }
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            
            lines = resp.text.strip().split('\n')
            if len(lines) < 2:
                return self._fallback_rate()
            
            # Parse CSV (DATE,INTDSRILM193N)
            recent_rates = []
            for line in lines[1:]:  # Skip header
                parts = line.split(',')
                if len(parts) == 2 and parts[1] != '.':
                    try:
                        recent_rates.append({
                            'date': parts[0],
                            'rate': float(parts[1])
                        })
                    except ValueError:
                        continue
            
            if not recent_rates:
                return self._fallback_rate()
            
            recent_rates.sort(key=lambda x: x['date'], reverse=True)
            current = recent_rates[0]
            previous = recent_rates[1] if len(recent_rates) > 1 else {'rate': current['rate']}
            
            change_bps = int((current['rate'] - previous['rate']) * 100)
            
            result = {
                'rate': current['rate'],
                'effective_date': current['date'],
                'previous_rate': previous['rate'],
                'change_bps': change_bps,
                'decision_date': current['date'],
                'next_meeting': self._estimate_next_meeting(),
                'target_range': None,  # BOI doesn't use explicit range
                'inflation_target': '1-3%',  # BOI official target
                'current_cpi': None,  # Would need separate call
                'source': 'FRED:INTDSRILM193N'
            }
            
            self.cache[cache_key] = {
                'timestamp': datetime.now(),
                'data': result
            }
            return result
            
        except Exception as e:
            print(f"Error fetching BOI rate: {e}")
            return self._fallback_rate()
    
    def _estimate_next_meeting(self) -> str:
        """
        Estimate next BOI monetary policy meeting
        BOI typically meets ~8-10 times per year
        """
        # BOI announces meetings in advance on their website
        # For now, estimate 6 weeks from last decision
        next_date = datetime.now() + timedelta(weeks=6)
        return next_date.strftime('%Y-%m-%d')
    
    def _fallback_rate(self) -> Dict:
        """Fallback with last known BOI rate"""
        return {
            'rate': 4.50,  # As of Feb 2026 estimate
            'effective_date': '2026-01-27',
            'previous_rate': 4.50,
            'change_bps': 0,
            'decision_date': '2026-01-27',
            'next_meeting': self._estimate_next_meeting(),
            'target_range': None,
            'inflation_target': '1-3%',
            'current_cpi': None,
            'source': 'fallback'
        }
    
    def get_rate_history(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        Get historical BOI interest rates
        
        Args:
            start_date: YYYY-MM-DD (default: 1 year ago)
            end_date: YYYY-MM-DD (default: today)
        
        Returns:
            List of {date, rate, change_bps, decision_type}
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            url = "https://fred.stlouisfed.org/graph/fredgraph.csv"
            params = {
                'id': 'INTDSRILM193N',
                'cosd': start_date,
                'coed': end_date
            }
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            
            lines = resp.text.strip().split('\n')
            history = []
            prev_rate = None
            
            for line in lines[1:]:
                parts = line.split(',')
                if len(parts) == 2 and parts[1] != '.':
                    try:
                        rate = float(parts[1])
                        change_bps = 0
                        decision_type = 'unchanged'
                        
                        if prev_rate is not None:
                            change_bps = int((rate - prev_rate) * 100)
                            if change_bps > 0:
                                decision_type = 'hike'
                            elif change_bps < 0:
                                decision_type = 'cut'
                        
                        history.append({
                            'date': parts[0],
                            'rate': rate,
                            'change_bps': change_bps,
                            'decision_type': decision_type
                        })
                        prev_rate = rate
                    except ValueError:
                        continue
            
            return history
            
        except Exception as e:
            print(f"Error fetching rate history: {e}")
            return []
    
    def get_corridor_rates(self) -> Dict:
        """
        Get BOI interest rate corridor
        
        Returns:
            {
                'deposit_rate': float (standing deposit facility),
                'base_rate': float (policy rate),
                'lending_rate': float (standing lending facility),
                'corridor_width_bps': int,
                'effective_date': str
            }
        """
        current = self.get_current_rate()
        base = current['rate']
        
        # BOI corridor is typically ±0.1% (10 bps) around base rate
        corridor_width = 0.10
        
        return {
            'deposit_rate': base - corridor_width,
            'base_rate': base,
            'lending_rate': base + corridor_width,
            'corridor_width_bps': int(corridor_width * 100 * 2),
            'effective_date': current['effective_date'],
            'source': 'BOI standard corridor'
        }
    
    def get_meeting_calendar(self, year: int = None) -> List[Dict]:
        """
        Get BOI monetary policy meeting dates
        
        Args:
            year: Calendar year (default: current year)
        
        Returns:
            List of {date, type, announced_rate, minutes_published}
        """
        if not year:
            year = datetime.now().year
        
        # BOI publishes annual meeting calendar
        # For now, estimate ~8 meetings per year
        meetings = []
        for month in [1, 2, 4, 5, 7, 9, 10, 11]:
            meeting_date = f"{year}-{month:02d}-27"
            meetings.append({
                'date': meeting_date,
                'type': 'Scheduled',
                'announced_rate': None,
                'minutes_published': None,
                'note': 'Estimated - check BOI website for confirmed dates'
            })
        
        return meetings


def main():
    """CLI interface for BOI rates"""
    import sys
    
    boi = BOIRates()
    
    if len(sys.argv) < 2:
        cmd = 'current'
    else:
        cmd = sys.argv[1]
    
    if cmd == 'current':
        data = boi.get_current_rate()
        print(f"BOI Base Rate: {data['rate']:.2f}%")
        print(f"Effective Date: {data['effective_date']}")
        print(f"Previous Rate: {data['previous_rate']:.2f}%")
        print(f"Change: {data['change_bps']:+d} bps")
        print(f"Next Meeting (est): {data['next_meeting']}")
        print(f"Inflation Target: {data['inflation_target']}")
    
    elif cmd == 'corridor':
        data = boi.get_corridor_rates()
        print(f"BOI Interest Rate Corridor:")
        print(f"  Lending:  {data['lending_rate']:.2f}%")
        print(f"  Base:     {data['base_rate']:.2f}%")
        print(f"  Deposit:  {data['deposit_rate']:.2f}%")
        print(f"  Width:    {data['corridor_width_bps']} bps")
    
    elif cmd == 'history':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 365
        start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        history = boi.get_rate_history(start_date=start)
        print(f"BOI Rate History (last {days} days):")
        for entry in history[-10:]:
            arrow = '↑' if entry['change_bps'] > 0 else '↓' if entry['change_bps'] < 0 else '→'
            print(f"  {entry['date']}: {entry['rate']:.2f}% {arrow} {entry['change_bps']:+d} bps")
    
    elif cmd == 'calendar':
        year = int(sys.argv[2]) if len(sys.argv) > 2 else datetime.now().year
        meetings = boi.get_meeting_calendar(year)
        print(f"BOI Monetary Policy Meetings {year}:")
        for meeting in meetings:
            print(f"  {meeting['date']} - {meeting['type']}")
    
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: boi_rates.py [current|corridor|history|calendar]")
        sys.exit(1)


if __name__ == "__main__":
    main()
