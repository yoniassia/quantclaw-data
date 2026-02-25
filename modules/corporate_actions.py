#!/usr/bin/env python3
"""
Corporate Action Calendar Module — Dividend Ex-Dates, Splits, Spin-offs, Rights Offerings

Comprehensive calendar of corporate actions with historical impact analysis:
- Dividend ex-dates and payment schedules
- Stock splits and reverse splits with price impact
- Spin-offs and special distributions
- Rights offerings and special situations
- Historical impact analysis (pre/post action price movements)

Data Sources: 
- Yahoo Finance (dividends, splits, corporate actions)
- SEC EDGAR (8-K filings for corporate events)

Author: QUANTCLAW DATA Build Agent
Phase: 63
"""

import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
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

def safe_get_date(value) -> Optional[str]:
    """Safely convert date to ISO string"""
    try:
        if value is None:
            return None
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')
        return str(value)
    except:
        return None

def calculate_price_impact(ticker_obj, action_date, window_days=5) -> Dict:
    """
    Calculate price impact around corporate action
    
    Args:
        ticker_obj: yfinance Ticker object
        action_date: datetime of the corporate action
        window_days: days before/after to analyze (default 5)
    
    Returns:
        Dict with pre/post prices and percent change
    """
    try:
        # Get historical data around the event
        start_date = action_date - timedelta(days=window_days + 10)  # Extra buffer for weekends
        end_date = action_date + timedelta(days=window_days + 10)
        
        hist = ticker_obj.history(start=start_date, end=end_date)
        
        if len(hist) == 0:
            return {
                "pre_price": None,
                "post_price": None,
                "change_pct": None,
                "error": "No price data available"
            }
        
        # Find closest trading day before action
        pre_data = hist[hist.index < action_date]
        if len(pre_data) == 0:
            pre_price = None
        else:
            pre_price = float(pre_data.iloc[-1]['Close'])
        
        # Find closest trading day after action
        post_data = hist[hist.index >= action_date]
        if len(post_data) < window_days:
            # Not enough post data yet
            if len(post_data) > 0:
                post_price = float(post_data.iloc[-1]['Close'])
            else:
                post_price = None
        else:
            post_price = float(post_data.iloc[window_days - 1]['Close'])
        
        # Calculate change
        if pre_price and post_price:
            change_pct = ((post_price - pre_price) / pre_price) * 100
        else:
            change_pct = None
        
        return {
            "pre_price": round(pre_price, 2) if pre_price else None,
            "post_price": round(post_price, 2) if post_price else None,
            "change_pct": round(change_pct, 2) if change_pct else None,
            "window_days": window_days
        }
    except Exception as e:
        return {
            "pre_price": None,
            "post_price": None,
            "change_pct": None,
            "error": str(e)
        }

def get_upcoming_dividends(ticker: str) -> Dict:
    """
    Get upcoming dividend information
    
    Returns:
        Next ex-date, payment date, amount, yield
    """
    try:
        ticker_obj = yf.Ticker(ticker)
        
        # Get dividend history
        dividends = ticker_obj.dividends
        if len(dividends) == 0:
            return {
                "ticker": ticker,
                "status": "no_dividends",
                "message": "No dividend history found"
            }
        
        # Get info for yield and frequency
        info = ticker_obj.info
        dividend_yield = safe_get_value(info.get('dividendYield', 0)) * 100
        dividend_rate = safe_get_value(info.get('dividendRate', 0))
        ex_dividend_date = info.get('exDividendDate')
        
        # Convert ex-dividend date
        if ex_dividend_date:
            if isinstance(ex_dividend_date, (int, float)):
                ex_div_date = datetime.fromtimestamp(ex_dividend_date)
            else:
                ex_div_date = ex_dividend_date
        else:
            ex_div_date = None
        
        # Calculate average frequency from history
        dividend_dates = dividends.index.tolist()
        if len(dividend_dates) >= 2:
            # Calculate average days between dividends
            date_diffs = [(dividend_dates[i] - dividend_dates[i-1]).days 
                          for i in range(1, min(5, len(dividend_dates)))]
            avg_days = sum(date_diffs) / len(date_diffs)
            
            if avg_days < 45:
                frequency = "Monthly"
            elif avg_days < 120:
                frequency = "Quarterly"
            elif avg_days < 250:
                frequency = "Semi-Annual"
            else:
                frequency = "Annual"
        else:
            frequency = "Unknown"
        
        # Last dividend info
        last_dividend_date = dividend_dates[-1]
        last_dividend_amount = float(dividends.iloc[-1])
        
        # Estimate next ex-date if not provided
        if not ex_div_date and len(dividend_dates) >= 2:
            # Use average frequency to predict
            date_diffs = [(dividend_dates[i] - dividend_dates[i-1]).days 
                          for i in range(1, min(5, len(dividend_dates)))]
            avg_days = sum(date_diffs) / len(date_diffs)
            estimated_next = last_dividend_date + timedelta(days=int(avg_days))
            
            # Only show if it's in the future
            if estimated_next > datetime.now(estimated_next.tzinfo):
                ex_div_date = estimated_next
                estimated = True
            else:
                estimated = False
        else:
            estimated = False
        
        return {
            "ticker": ticker,
            "dividend_yield": round(dividend_yield, 2),
            "annual_dividend": round(dividend_rate, 2),
            "frequency": frequency,
            "last_ex_date": safe_get_date(last_dividend_date),
            "last_amount": round(last_dividend_amount, 2),
            "next_ex_date": safe_get_date(ex_div_date) if ex_div_date else None,
            "next_ex_date_estimated": estimated,
            "status": "active"
        }
    
    except Exception as e:
        return {
            "ticker": ticker,
            "status": "error",
            "error": str(e)
        }

def get_split_history(ticker: str, lookback_years: int = 10) -> Dict:
    """
    Get stock split history with impact analysis
    
    Args:
        ticker: Stock ticker symbol
        lookback_years: Years of history to retrieve
    
    Returns:
        Dict with split history and impact metrics
    """
    try:
        ticker_obj = yf.Ticker(ticker)
        
        # Get splits
        splits = ticker_obj.splits
        if len(splits) == 0:
            return {
                "ticker": ticker,
                "status": "no_splits",
                "message": f"No splits found in last {lookback_years} years"
            }
        
        # Filter by lookback period
        cutoff_date = datetime.now()
        # Make cutoff_date timezone-aware if splits index is timezone-aware
        if splits.index.tz is not None:
            import pytz
            cutoff_date = cutoff_date.replace(tzinfo=pytz.UTC)
        cutoff_date = cutoff_date - timedelta(days=lookback_years * 365)
        recent_splits = splits[splits.index >= cutoff_date]
        
        if len(recent_splits) == 0:
            return {
                "ticker": ticker,
                "status": "no_recent_splits",
                "message": f"No splits in last {lookback_years} years",
                "total_historical_splits": len(splits)
            }
        
        # Analyze each split
        split_details = []
        for split_date, split_ratio in recent_splits.items():
            # Determine if forward or reverse split
            if split_ratio > 1:
                split_type = "forward"
                ratio_str = f"{int(split_ratio)}:1"
            else:
                split_type = "reverse"
                ratio_str = f"1:{int(1/split_ratio)}"
            
            # Calculate price impact
            impact = calculate_price_impact(ticker_obj, split_date)
            
            split_details.append({
                "date": safe_get_date(split_date),
                "ratio": float(split_ratio),
                "type": split_type,
                "ratio_display": ratio_str,
                "price_impact": impact
            })
        
        # Summary statistics
        forward_splits = sum(1 for s in split_details if s['type'] == 'forward')
        reverse_splits = sum(1 for s in split_details if s['type'] == 'reverse')
        
        # Calculate average impact (excluding None values)
        impacts = [s['price_impact']['change_pct'] for s in split_details 
                   if s['price_impact']['change_pct'] is not None]
        avg_impact = sum(impacts) / len(impacts) if impacts else None
        
        return {
            "ticker": ticker,
            "status": "success",
            "lookback_years": lookback_years,
            "total_splits": len(split_details),
            "forward_splits": forward_splits,
            "reverse_splits": reverse_splits,
            "avg_price_impact_pct": round(avg_impact, 2) if avg_impact else None,
            "splits": split_details
        }
    
    except Exception as e:
        return {
            "ticker": ticker,
            "status": "error",
            "error": str(e)
        }

def get_dividend_calendar(tickers: List[str]) -> Dict:
    """
    Get upcoming dividend ex-dates across a watchlist
    
    Args:
        tickers: List of ticker symbols
    
    Returns:
        Calendar of upcoming dividends sorted by date
    """
    try:
        upcoming = []
        
        for ticker in tickers:
            div_info = get_upcoming_dividends(ticker)
            
            if div_info['status'] == 'active' and div_info.get('next_ex_date'):
                upcoming.append({
                    "ticker": ticker,
                    "ex_date": div_info['next_ex_date'],
                    "estimated": div_info.get('next_ex_date_estimated', False),
                    "amount": div_info.get('last_amount'),
                    "yield": div_info.get('dividend_yield'),
                    "frequency": div_info.get('frequency')
                })
        
        # Sort by ex-date
        upcoming.sort(key=lambda x: x['ex_date'])
        
        # Filter to next 90 days
        cutoff = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
        upcoming = [d for d in upcoming if d['ex_date'] <= cutoff]
        
        return {
            "status": "success",
            "calendar_range_days": 90,
            "total_tickers_checked": len(tickers),
            "upcoming_dividends": len(upcoming),
            "dividends": upcoming
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def get_spinoff_tracker() -> Dict:
    """
    Track recent and upcoming spin-offs
    
    Note: This is a simplified version as true spin-off data requires
    more sophisticated SEC filing parsing. This version detects unusual
    corporate actions and special distributions.
    
    Returns:
        List of potential spin-offs and special situations
    """
    try:
        # Common spin-off candidates or recent spin-offs
        # In production, this would query SEC EDGAR for Form 8-K Item 1.01
        # For now, we'll check for special distributions
        
        # Popular tickers that might have had recent activity
        check_tickers = ['GE', 'JNJ', 'PFE', 'BA', 'HON', 'MMM', 'IBM']
        
        potential_spinoffs = []
        
        for ticker in check_tickers:
            try:
                ticker_obj = yf.Ticker(ticker)
                
                # Check for unusual dividends (could be special distributions)
                dividends = ticker_obj.dividends
                if len(dividends) >= 2:
                    recent_divs = dividends.tail(10)
                    
                    # Calculate median dividend
                    median_div = recent_divs.median()
                    
                    # Find dividends > 2x median (potential special distribution)
                    special = recent_divs[recent_divs > median_div * 2]
                    
                    if len(special) > 0:
                        for date, amount in special.items():
                            # Only include last 2 years
                            if date >= datetime.now() - timedelta(days=730):
                                potential_spinoffs.append({
                                    "ticker": ticker,
                                    "date": safe_get_date(date),
                                    "type": "special_distribution",
                                    "amount": round(float(amount), 2),
                                    "median_dividend": round(float(median_div), 2),
                                    "multiple": round(float(amount / median_div), 1)
                                })
            except:
                continue
        
        return {
            "status": "success",
            "note": "Spin-off detection is limited. Full implementation requires SEC EDGAR Form 8-K parsing.",
            "tickers_checked": len(check_tickers),
            "potential_events": len(potential_spinoffs),
            "events": potential_spinoffs
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def corporate_calendar_command(ticker: str):
    """CLI: Get upcoming corporate actions for a ticker"""
    print(f"📅 CORPORATE ACTION CALENDAR: {ticker}\n")
    
    # Get dividend info
    div_info = get_upcoming_dividends(ticker)
    
    if div_info['status'] == 'active':
        print("💰 DIVIDEND INFORMATION")
        print(f"  Yield: {div_info['dividend_yield']}%")
        print(f"  Annual Dividend: ${div_info['annual_dividend']}")
        print(f"  Frequency: {div_info['frequency']}")
        print(f"  Last Ex-Date: {div_info['last_ex_date']} (${div_info['last_amount']})")
        if div_info.get('next_ex_date'):
            estimated_tag = " (estimated)" if div_info.get('next_ex_date_estimated') else ""
            print(f"  Next Ex-Date: {div_info['next_ex_date']}{estimated_tag}")
        print()
    elif div_info['status'] == 'no_dividends':
        print("💰 DIVIDEND INFORMATION")
        print(f"  Status: {div_info['message']}\n")
    
    # Get recent splits
    split_info = get_split_history(ticker, lookback_years=5)
    
    if split_info['status'] == 'success':
        print("📊 STOCK SPLIT HISTORY (Last 5 Years)")
        print(f"  Total Splits: {split_info['total_splits']}")
        print(f"  Forward Splits: {split_info['forward_splits']}")
        print(f"  Reverse Splits: {split_info['reverse_splits']}")
        if split_info['avg_price_impact_pct'] is not None:
            print(f"  Avg 5-Day Impact: {split_info['avg_price_impact_pct']:+.2f}%")
        print()
        
        for split in split_info['splits'][:3]:  # Show last 3
            print(f"  {split['date']}: {split['ratio_display']} ({split['type']})")
            if split['price_impact']['change_pct'] is not None:
                print(f"    Impact: {split['price_impact']['change_pct']:+.2f}% " +
                      f"(${split['price_impact']['pre_price']} → ${split['price_impact']['post_price']})")
        print()
    elif split_info['status'] == 'no_recent_splits':
        print("📊 STOCK SPLIT HISTORY")
        print(f"  {split_info['message']}\n")
    
    # Summary
    print("✅ Use 'split-history' for detailed split analysis")
    print("✅ Use 'dividend-calendar' to see upcoming ex-dates across watchlist")

def split_history_command(ticker: str):
    """CLI: Get detailed split history with impact analysis"""
    print(f"📊 STOCK SPLIT HISTORY: {ticker}\n")
    
    split_info = get_split_history(ticker, lookback_years=20)
    
    if split_info['status'] == 'success':
        print(f"📈 SPLIT SUMMARY ({split_info['lookback_years']} years)")
        print(f"  Total Splits: {split_info['total_splits']}")
        print(f"  Forward Splits: {split_info['forward_splits']}")
        print(f"  Reverse Splits: {split_info['reverse_splits']}")
        if split_info['avg_price_impact_pct'] is not None:
            print(f"  Average 5-Day Price Impact: {split_info['avg_price_impact_pct']:+.2f}%")
        print()
        
        print("📅 DETAILED SPLIT HISTORY\n")
        for split in split_info['splits']:
            print(f"Date: {split['date']}")
            print(f"  Type: {split['type'].title()} Split")
            print(f"  Ratio: {split['ratio_display']}")
            
            impact = split['price_impact']
            if impact['change_pct'] is not None:
                print(f"  Price Before: ${impact['pre_price']}")
                print(f"  Price After ({impact['window_days']} days): ${impact['post_price']}")
                print(f"  Impact: {impact['change_pct']:+.2f}%")
            else:
                print(f"  Impact: Data unavailable")
            print()
        
        # Insights
        print("💡 INSIGHTS")
        if split_info['reverse_splits'] > 0:
            print("  ⚠️  Reverse splits detected - often indicates stock price distress")
        if split_info['avg_price_impact_pct'] and split_info['avg_price_impact_pct'] > 5:
            print(f"  📈 Splits have shown positive momentum (+{split_info['avg_price_impact_pct']:.1f}% avg)")
        elif split_info['avg_price_impact_pct'] and split_info['avg_price_impact_pct'] < -5:
            print(f"  📉 Splits have shown negative momentum ({split_info['avg_price_impact_pct']:.1f}% avg)")
        else:
            print("  ➡️  Splits show neutral price impact")
    
    elif split_info['status'] in ['no_splits', 'no_recent_splits']:
        print(f"ℹ️  {split_info['message']}")
        if 'total_historical_splits' in split_info:
            print(f"   (Total historical splits: {split_info['total_historical_splits']})")
    else:
        print(f"❌ Error: {split_info.get('error', 'Unknown error')}")

def dividend_calendar_command(tickers_str: str = None):
    """CLI: Show upcoming dividend ex-dates across watchlist"""
    print("📅 DIVIDEND CALENDAR - Upcoming Ex-Dates\n")
    
    # Default watchlist if none provided
    if not tickers_str:
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'JNJ', 'PG', 'KO', 'PEP', 'WMT', 'V', 'MA']
        print("Using default watchlist (pass tickers as argument to customize)")
        print(f"Tickers: {', '.join(tickers)}\n")
    else:
        tickers = [t.strip().upper() for t in tickers_str.split(',')]
        print(f"Checking {len(tickers)} tickers: {', '.join(tickers)}\n")
    
    calendar = get_dividend_calendar(tickers)
    
    if calendar['status'] == 'success':
        print(f"📊 SUMMARY")
        print(f"  Tickers Checked: {calendar['total_tickers_checked']}")
        print(f"  Upcoming Dividends (90 days): {calendar['upcoming_dividends']}")
        print()
        
        if calendar['upcoming_dividends'] > 0:
            print("📅 UPCOMING EX-DATES\n")
            
            for div in calendar['dividends']:
                estimated = " *" if div['estimated'] else ""
                print(f"{div['ex_date']}{estimated}: {div['ticker']}")
                print(f"  Amount: ${div['amount']:.2f} | Yield: {div['yield']:.2f}% | {div['frequency']}")
                print()
            
            if any(d['estimated'] for d in calendar['dividends']):
                print("* = Estimated date based on historical pattern")
        else:
            print("No upcoming dividends in the next 90 days for this watchlist.")
    else:
        print(f"❌ Error: {calendar.get('error', 'Unknown error')}")

def spinoff_tracker_command():
    """CLI: Track recent/upcoming spin-offs"""
    print("🔄 SPIN-OFF & SPECIAL DISTRIBUTION TRACKER\n")
    
    tracker = get_spinoff_tracker()
    
    if tracker['status'] == 'success':
        print("📊 SCAN SUMMARY")
        print(f"  Tickers Checked: {tracker['tickers_checked']}")
        print(f"  Potential Events: {tracker['potential_events']}")
        print(f"\n⚠️  Note: {tracker['note']}")
        print()
        
        if tracker['potential_events'] > 0:
            print("📅 DETECTED EVENTS (Last 2 Years)\n")
            
            for event in tracker['events']:
                print(f"{event['ticker']} - {event['date']}")
                print(f"  Type: {event['type'].replace('_', ' ').title()}")
                print(f"  Amount: ${event['amount']:.2f} " +
                      f"({event['multiple']}x normal dividend of ${event['median_dividend']:.2f})")
                print()
            
            print("💡 TIP: Special distributions may indicate spin-offs, asset sales, or special dividends.")
            print("     Review SEC Form 8-K filings for full details.")
        else:
            print("No special distributions detected in scanned tickers.")
    else:
        print(f"❌ Error: {tracker.get('error', 'Unknown error')}")

def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python corporate_actions.py corporate-calendar TICKER")
        print("  python corporate_actions.py split-history TICKER")
        print("  python corporate_actions.py dividend-calendar [TICKER,TICKER,...]")
        print("  python corporate_actions.py spinoff-tracker")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'corporate-calendar':
        if len(sys.argv) < 3:
            print("Error: Ticker required")
            print("Usage: python corporate_actions.py corporate-calendar TICKER")
            sys.exit(1)
        ticker = sys.argv[2].upper()
        corporate_calendar_command(ticker)
    
    elif command == 'split-history':
        if len(sys.argv) < 3:
            print("Error: Ticker required")
            print("Usage: python corporate_actions.py split-history TICKER")
            sys.exit(1)
        ticker = sys.argv[2].upper()
        split_history_command(ticker)
    
    elif command == 'dividend-calendar':
        tickers_str = sys.argv[2] if len(sys.argv) > 2 else None
        dividend_calendar_command(tickers_str)
    
    elif command == 'spinoff-tracker':
        spinoff_tracker_command()
    
    else:
        print(f"Error: Unknown command '{command}'")
        sys.exit(1)

if __name__ == '__main__':
    main()
