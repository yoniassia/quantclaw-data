#!/usr/bin/env python3
"""
Share Float & Ownership Structure — Phase 138

Track share float, insider ownership %, institutional ownership %, 
public float %, restricted shares from SEC filings + Yahoo Finance.
Quarterly updates with change tracking.

Analyzes:
1. Total shares outstanding vs. float shares
2. Insider ownership % (officers, directors, 10% holders)
3. Institutional ownership % (13F filers)
4. Public float % (tradeable shares)
5. Restricted shares and lockup expirations
6. Ownership concentration metrics

Free data sources:
- Yahoo Finance (shares outstanding, float, insider %, institutional %)
- SEC EDGAR 13F filings (institutional holdings)
- SEC Form 4 (insider transactions)
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import time
import sys

# Headers for SEC requests
SEC_HEADERS = {
    'User-Agent': 'QuantClaw Data (quantclaw@moneyclaw.com)',
    'Accept': 'application/json'
}


@dataclass
class OwnershipStructure:
    """Complete ownership structure for a ticker."""
    ticker: str
    company_name: str
    shares_outstanding: int
    float_shares: int
    float_percent: float
    insider_percent: float
    institutional_percent: float
    public_percent: float
    restricted_shares: int
    restricted_percent: float
    ownership_concentration: str  # DISPERSED, MODERATE, CONCENTRATED
    implied_public_shares: int
    market_cap: float
    float_market_cap: float
    data_date: str
    source: str


@dataclass
class InsiderOwnership:
    """Insider ownership breakdown."""
    ticker: str
    total_insider_percent: float
    officers_directors_percent: float
    ten_percent_holders: List[Dict]  # [{"name": str, "percent": float, "shares": int}]
    total_insider_shares: int
    recent_form4_activity: str  # BUY, SELL, NEUTRAL, MIXED
    insider_trend: str  # INCREASING, STABLE, DECREASING
    last_updated: str


@dataclass
class InstitutionalOwnership:
    """Institutional ownership breakdown from 13F filings."""
    ticker: str
    total_institutional_percent: float
    total_institutional_shares: int
    num_holders: int
    top_10_holders: List[Dict]  # [{"name": str, "percent": float, "shares": int}]
    concentration_top10: float  # % of total held by top 10
    quarterly_change_percent: float
    quarterly_change_shares: int
    trend: str  # ACCUMULATION, DISTRIBUTION, STABLE
    last_filed_quarter: str


@dataclass
class FloatAnalysis:
    """Float analysis and metrics."""
    ticker: str
    float_shares: int
    float_percent: float
    float_category: str  # LOW (<20%), MODERATE (20-50%), HIGH (50-80%), VERY_HIGH (>80%)
    restricted_shares: int
    avg_daily_volume: int
    days_to_trade_float: float  # Float / ADV
    liquidity_score: float  # 0-100
    short_squeeze_risk: str  # Based on float size
    market_impact: str  # LOW, MODERATE, HIGH


@dataclass
class OwnershipChange:
    """Quarterly ownership change tracking."""
    ticker: str
    quarter: str
    insider_change_pct: float
    institutional_change_pct: float
    float_change_pct: float
    total_shares_change_pct: float
    major_events: List[str]  # Buybacks, offerings, lockup expirations
    smart_money_signal: str  # BULLISH, BEARISH, NEUTRAL


def get_yahoo_ownership(ticker: str) -> Optional[Dict]:
    """Get ownership data from Yahoo Finance via yfinance."""
    try:
        import yfinance as yf
        
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Convert yfinance format to expected format
        yahoo_data = {
            'defaultKeyStatistics': {
                'sharesOutstanding': {'raw': info.get('sharesOutstanding', 0)},
                'floatShares': {'raw': info.get('floatShares', 0)},
                'marketCap': {'raw': info.get('marketCap', 0)},
                'averageDailyVolume10Day': {'raw': info.get('averageDailyVolume10Day', 0)}
            },
            'majorHoldersBreakdown': {
                'insidersPercentHeld': {'raw': info.get('heldPercentInsiders', 0)},
                'institutionsPercentHeld': {'raw': info.get('heldPercentInstitutions', 0)}
            },
            'insiderHolders': {'holders': []},
            'institutionOwnership': {'ownershipList': []}
        }
        
        # Try to get institutional holders
        try:
            institutional_holders = stock.institutional_holders
            if institutional_holders is not None and not institutional_holders.empty:
                ownership_list = []
                for idx, row in institutional_holders.head(10).iterrows():
                    ownership_list.append({
                        'organization': row.get('Holder', 'Unknown'),
                        'position': {'raw': row.get('Shares', 0)},
                        'pctHeld': {'raw': row.get('% Out', 0) / 100 if '% Out' in row else 0}
                    })
                yahoo_data['institutionOwnership']['ownershipList'] = ownership_list
        except:
            pass
        
        # Try to get insider holders
        try:
            insider_holders = stock.insider_transactions
            if insider_holders is not None and not insider_holders.empty:
                holders_list = []
                for idx, row in insider_holders.head(10).iterrows():
                    holders_list.append({
                        'name': row.get('Insider', 'Unknown'),
                        'position': row.get('Position', ''),
                        'positionDirect': {'raw': row.get('Shares', 0)}
                    })
                yahoo_data['insiderHolders']['holders'] = holders_list
        except:
            pass
        
        return yahoo_data
    except Exception as e:
        print(f"Error fetching Yahoo data for {ticker}: {e}", file=sys.stderr)
        return None


def parse_ownership_structure(ticker: str, yahoo_data: Dict) -> Optional[OwnershipStructure]:
    """Parse complete ownership structure from Yahoo data."""
    try:
        key_stats = yahoo_data.get('defaultKeyStatistics', {})
        major_holders = yahoo_data.get('majorHoldersBreakdown', {})
        
        # Extract key metrics
        shares_outstanding = key_stats.get('sharesOutstanding', {}).get('raw', 0)
        float_shares = key_stats.get('floatShares', {}).get('raw', 0)
        market_cap = key_stats.get('marketCap', {}).get('raw', 0)
        
        # Ownership percentages
        insider_percent = major_holders.get('insidersPercentHeld', {}).get('raw', 0) * 100
        institutional_percent = major_holders.get('institutionsPercentHeld', {}).get('raw', 0) * 100
        
        # Calculate derived metrics
        float_percent = (float_shares / shares_outstanding * 100) if shares_outstanding > 0 else 0
        public_percent = 100 - insider_percent - institutional_percent
        restricted_shares = shares_outstanding - float_shares
        restricted_percent = 100 - float_percent
        float_market_cap = market_cap * (float_shares / shares_outstanding) if shares_outstanding > 0 else 0
        
        # Determine concentration
        if insider_percent + institutional_percent > 70:
            concentration = "CONCENTRATED"
        elif insider_percent + institutional_percent > 40:
            concentration = "MODERATE"
        else:
            concentration = "DISPERSED"
        
        # Implied public shares (not owned by insiders or institutions)
        implied_public_shares = int(shares_outstanding * public_percent / 100)
        
        # Get company name from Yahoo
        company_name = ticker.upper()
        
        return OwnershipStructure(
            ticker=ticker.upper(),
            company_name=company_name,
            shares_outstanding=shares_outstanding,
            float_shares=float_shares,
            float_percent=round(float_percent, 2),
            insider_percent=round(insider_percent, 2),
            institutional_percent=round(institutional_percent, 2),
            public_percent=round(public_percent, 2),
            restricted_shares=restricted_shares,
            restricted_percent=round(restricted_percent, 2),
            ownership_concentration=concentration,
            implied_public_shares=implied_public_shares,
            market_cap=market_cap,
            float_market_cap=float_market_cap,
            data_date=datetime.now().strftime('%Y-%m-%d'),
            source="Yahoo Finance"
        )
    except Exception as e:
        print(f"Error parsing ownership structure: {e}", file=sys.stderr)
        return None


def get_insider_ownership(ticker: str, yahoo_data: Dict) -> Optional[InsiderOwnership]:
    """Get detailed insider ownership breakdown."""
    try:
        major_holders = yahoo_data.get('majorHoldersBreakdown', {})
        insider_holders = yahoo_data.get('insiderHolders', {}).get('holders', [])
        
        total_insider_percent = major_holders.get('insidersPercentHeld', {}).get('raw', 0) * 100
        
        # Parse insider holders
        ten_percent_holders = []
        officers_directors_percent = 0
        total_insider_shares = 0
        
        for holder in insider_holders[:10]:  # Top 10 insiders
            name = holder.get('name', 'Unknown')
            position = holder.get('position', '')
            shares = holder.get('positionDirect', {}).get('raw', 0)
            
            # Calculate percent (approximation)
            if 'sharesOutstanding' in yahoo_data.get('defaultKeyStatistics', {}):
                shares_outstanding = yahoo_data['defaultKeyStatistics']['sharesOutstanding'].get('raw', 1)
                percent = (shares / shares_outstanding * 100) if shares_outstanding > 0 else 0
            else:
                percent = 0
            
            if percent >= 10 or 'director' in position.lower() or 'officer' in position.lower():
                ten_percent_holders.append({
                    'name': name,
                    'position': position,
                    'percent': round(percent, 2),
                    'shares': shares
                })
                officers_directors_percent += percent
                total_insider_shares += shares
        
        # Determine insider activity trend (simplified)
        recent_form4_activity = "NEUTRAL"  # Would need Form 4 parsing
        insider_trend = "STABLE"
        
        return InsiderOwnership(
            ticker=ticker.upper(),
            total_insider_percent=round(total_insider_percent, 2),
            officers_directors_percent=round(officers_directors_percent, 2),
            ten_percent_holders=ten_percent_holders,
            total_insider_shares=total_insider_shares,
            recent_form4_activity=recent_form4_activity,
            insider_trend=insider_trend,
            last_updated=datetime.now().strftime('%Y-%m-%d')
        )
    except Exception as e:
        print(f"Error parsing insider ownership: {e}", file=sys.stderr)
        return None


def get_institutional_ownership(ticker: str, yahoo_data: Dict) -> Optional[InstitutionalOwnership]:
    """Get detailed institutional ownership from 13F data."""
    try:
        major_holders = yahoo_data.get('majorHoldersBreakdown', {})
        institutional_holders = yahoo_data.get('institutionOwnership', {}).get('ownershipList', [])
        key_stats = yahoo_data.get('defaultKeyStatistics', {})
        
        shares_outstanding = key_stats.get('sharesOutstanding', {}).get('raw', 1)
        total_institutional_percent = major_holders.get('institutionsPercentHeld', {}).get('raw', 0) * 100
        
        # Parse institutional holders
        top_10_holders = []
        total_top10_percent = 0
        total_institutional_shares = 0
        num_holders = len(institutional_holders)
        
        for holder in institutional_holders[:10]:  # Top 10 institutions
            name = holder.get('organization', 'Unknown')
            shares = holder.get('position', {}).get('raw', 0)
            percent = (shares / shares_outstanding * 100) if shares_outstanding > 0 else 0
            
            top_10_holders.append({
                'name': name,
                'percent': round(percent, 2),
                'shares': shares
            })
            total_top10_percent += percent
            total_institutional_shares += shares
        
        # Estimate quarterly change (would need historical data)
        quarterly_change_percent = 0.0
        quarterly_change_shares = 0
        trend = "STABLE"
        
        # Determine concentration
        concentration_top10 = (total_top10_percent / total_institutional_percent * 100) if total_institutional_percent > 0 else 0
        
        return InstitutionalOwnership(
            ticker=ticker.upper(),
            total_institutional_percent=round(total_institutional_percent, 2),
            total_institutional_shares=total_institutional_shares,
            num_holders=num_holders,
            top_10_holders=top_10_holders,
            concentration_top10=round(concentration_top10, 2),
            quarterly_change_percent=round(quarterly_change_percent, 2),
            quarterly_change_shares=quarterly_change_shares,
            trend=trend,
            last_filed_quarter=datetime.now().strftime('%Y-Q%s' % ((datetime.now().month - 1) // 3 + 1))
        )
    except Exception as e:
        print(f"Error parsing institutional ownership: {e}", file=sys.stderr)
        return None


def get_float_analysis(ticker: str, yahoo_data: Dict) -> Optional[FloatAnalysis]:
    """Analyze float characteristics and liquidity."""
    try:
        key_stats = yahoo_data.get('defaultKeyStatistics', {})
        
        float_shares = key_stats.get('floatShares', {}).get('raw', 0)
        shares_outstanding = key_stats.get('sharesOutstanding', {}).get('raw', 1)
        avg_volume = key_stats.get('averageDailyVolume10Day', {}).get('raw', 0)
        
        float_percent = (float_shares / shares_outstanding * 100) if shares_outstanding > 0 else 0
        restricted_shares = shares_outstanding - float_shares
        
        # Categorize float
        if float_percent < 20:
            float_category = "LOW"
        elif float_percent < 50:
            float_category = "MODERATE"
        elif float_percent < 80:
            float_category = "HIGH"
        else:
            float_category = "VERY_HIGH"
        
        # Days to trade float
        days_to_trade = (float_shares / avg_volume) if avg_volume > 0 else 9999
        
        # Liquidity score (0-100)
        if days_to_trade < 1:
            liquidity_score = 100
        elif days_to_trade < 5:
            liquidity_score = 80
        elif days_to_trade < 10:
            liquidity_score = 60
        elif days_to_trade < 30:
            liquidity_score = 40
        else:
            liquidity_score = 20
        
        # Short squeeze risk
        if float_percent < 20 and days_to_trade > 10:
            short_squeeze_risk = "HIGH"
        elif float_percent < 40 and days_to_trade > 5:
            short_squeeze_risk = "MODERATE"
        else:
            short_squeeze_risk = "LOW"
        
        # Market impact
        if liquidity_score > 80:
            market_impact = "LOW"
        elif liquidity_score > 50:
            market_impact = "MODERATE"
        else:
            market_impact = "HIGH"
        
        return FloatAnalysis(
            ticker=ticker.upper(),
            float_shares=float_shares,
            float_percent=round(float_percent, 2),
            float_category=float_category,
            restricted_shares=restricted_shares,
            avg_daily_volume=avg_volume,
            days_to_trade_float=round(days_to_trade, 2),
            liquidity_score=liquidity_score,
            short_squeeze_risk=short_squeeze_risk,
            market_impact=market_impact
        )
    except Exception as e:
        print(f"Error analyzing float: {e}", file=sys.stderr)
        return None


def get_ownership_summary(ticker: str) -> Dict:
    """Get complete ownership summary for a ticker."""
    yahoo_data = get_yahoo_ownership(ticker)
    if not yahoo_data:
        return {
            'error': f'Could not fetch ownership data for {ticker}',
            'ticker': ticker.upper()
        }
    
    ownership = parse_ownership_structure(ticker, yahoo_data)
    insiders = get_insider_ownership(ticker, yahoo_data)
    institutions = get_institutional_ownership(ticker, yahoo_data)
    float_analysis = get_float_analysis(ticker, yahoo_data)
    
    result = {
        'ticker': ticker.upper(),
        'ownership_structure': asdict(ownership) if ownership else None,
        'insider_ownership': asdict(insiders) if insiders else None,
        'institutional_ownership': asdict(institutions) if institutions else None,
        'float_analysis': asdict(float_analysis) if float_analysis else None,
        'summary': {
            'total_shares': ownership.shares_outstanding if ownership else 0,
            'float_shares': ownership.float_shares if ownership else 0,
            'float_pct': ownership.float_percent if ownership else 0,
            'insider_pct': ownership.insider_percent if ownership else 0,
            'institutional_pct': ownership.institutional_percent if ownership else 0,
            'concentration': ownership.ownership_concentration if ownership else 'UNKNOWN',
            'liquidity': float_analysis.liquidity_score if float_analysis else 0,
            'squeeze_risk': float_analysis.short_squeeze_risk if float_analysis else 'UNKNOWN'
        }
    }
    
    return result


def compare_ownership(tickers: List[str]) -> pd.DataFrame:
    """Compare ownership structures across multiple tickers."""
    results = []
    
    for ticker in tickers:
        data = get_ownership_summary(ticker)
        if 'error' in data:
            continue
        
        summary = data['summary']
        results.append({
            'Ticker': ticker.upper(),
            'Float %': summary['float_pct'],
            'Insider %': summary['insider_pct'],
            'Institutional %': summary['institutional_pct'],
            'Concentration': summary['concentration'],
            'Liquidity Score': summary['liquidity'],
            'Squeeze Risk': summary['squeeze_risk']
        })
    
    return pd.DataFrame(results)


def scan_low_float(min_float: float = 0, max_float: float = 30, 
                   tickers: Optional[List[str]] = None) -> pd.DataFrame:
    """Scan for low float stocks (squeeze candidates)."""
    if not tickers:
        # Default watchlist (could be expanded)
        tickers = ['GME', 'AMC', 'BBBY', 'SPCE', 'BYND', 'PLUG', 'TLRY', 'CGC']
    
    results = []
    for ticker in tickers:
        data = get_ownership_summary(ticker)
        if 'error' in data:
            continue
        
        summary = data['summary']
        float_pct = summary['float_pct']
        
        if min_float <= float_pct <= max_float:
            results.append({
                'Ticker': ticker.upper(),
                'Float %': float_pct,
                'Float Shares': f"{summary['float_shares']:,}",
                'Insider %': summary['insider_pct'],
                'Institutional %': summary['institutional_pct'],
                'Squeeze Risk': summary['squeeze_risk'],
                'Liquidity': summary['liquidity']
            })
    
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values('Float %')
    return df


# CLI Commands
def main():
    if len(sys.argv) < 2:
        print("Usage: share_float_and_ownership_structure.py <command> [args]")
        print("\nCommands:")
        print("  ownership-summary <ticker>      Full ownership breakdown")
        print("  insider-detail <ticker>         Insider ownership detail")
        print("  institutional-detail <ticker>   Institutional holdings")
        print("  float-analysis <ticker>         Float and liquidity analysis")
        print("  compare <ticker1> <ticker2>...  Compare ownership structures")
        print("  scan-low-float [max_pct]        Scan for low float stocks")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'ownership-summary':
        if len(sys.argv) < 3:
            print("Usage: ownership-summary <ticker>")
            sys.exit(1)
        ticker = sys.argv[2]
        result = get_ownership_summary(ticker)
        print(json.dumps(result, indent=2))
    
    elif command == 'insider-detail':
        if len(sys.argv) < 3:
            print("Usage: insider-detail <ticker>")
            sys.exit(1)
        ticker = sys.argv[2]
        yahoo_data = get_yahoo_ownership(ticker)
        if yahoo_data:
            insiders = get_insider_ownership(ticker, yahoo_data)
            if insiders:
                print(json.dumps(asdict(insiders), indent=2))
        else:
            print(json.dumps({'error': f'Could not fetch data for {ticker}'}))
    
    elif command == 'institutional-detail':
        if len(sys.argv) < 3:
            print("Usage: institutional-detail <ticker>")
            sys.exit(1)
        ticker = sys.argv[2]
        yahoo_data = get_yahoo_ownership(ticker)
        if yahoo_data:
            institutions = get_institutional_ownership(ticker, yahoo_data)
            if institutions:
                print(json.dumps(asdict(institutions), indent=2))
        else:
            print(json.dumps({'error': f'Could not fetch data for {ticker}'}))
    
    elif command == 'float-analysis':
        if len(sys.argv) < 3:
            print("Usage: float-analysis <ticker>")
            sys.exit(1)
        ticker = sys.argv[2]
        yahoo_data = get_yahoo_ownership(ticker)
        if yahoo_data:
            float_analysis = get_float_analysis(ticker, yahoo_data)
            if float_analysis:
                print(json.dumps(asdict(float_analysis), indent=2))
        else:
            print(json.dumps({'error': f'Could not fetch data for {ticker}'}))
    
    elif command == 'compare':
        if len(sys.argv) < 4:
            print("Usage: compare <ticker1> <ticker2> [ticker3...]")
            sys.exit(1)
        tickers = sys.argv[2:]
        df = compare_ownership(tickers)
        print(df.to_string(index=False))
    
    elif command == 'scan-low-float':
        max_float = float(sys.argv[2]) if len(sys.argv) > 2 else 30
        df = scan_low_float(max_float=max_float)
        print(df.to_string(index=False))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
