#!/usr/bin/env python3
"""
BioPharmCatalyst Pipeline API — Healthcare & Biotech Catalysts

Provides biotech and pharmaceutical pipeline data, including upcoming FDA decisions,
clinical trial catalysts, and PDUFA dates. Aggregates data for event-based trading
signals in the healthcare sector.

Dual-mode operation:
- Primary: API endpoint (may be unstable)
- Fallback: Web scraping of calendar pages

Source: https://www.biopharmcatalyst.com/api
Category: Healthcare & Biotech
Free tier: True (100 requests/month, no API key needed)
Author: QuantClaw Data NightBuilder
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re

# API Configuration
API_BASE_URL = "https://api.biopharmcatalyst.com/v1"
CALENDAR_BASE_URL = "https://www.biopharmcatalyst.com/calendars"
REQUEST_TIMEOUT = 10
USER_AGENT = "QuantClaw-Data/1.0 (Healthcare Analytics)"

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/html",
}


def _try_api_endpoint(endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """
    Try to fetch from API endpoint with timeout and error handling.
    
    Args:
        endpoint: API endpoint path
        params: Query parameters
        
    Returns:
        Parsed JSON response or None if failed
    """
    try:
        url = f"{API_BASE_URL}/{endpoint}"
        response = requests.get(url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None


def _scrape_calendar_page(calendar_type: str) -> List[Dict]:
    """
    Fallback web scraper for calendar pages.
    
    Args:
        calendar_type: 'fda-calendar' or 'pdufa-calendar'
        
    Returns:
        List of parsed catalyst events
    """
    try:
        url = f"{CALENDAR_BASE_URL}/{calendar_type}"
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        
        if response.status_code != 200:
            return []
        
        html = response.text
        events = []
        
        # Simple regex-based extraction (would be better with BeautifulSoup, but keeping deps minimal)
        # Look for common patterns in catalyst calendar tables
        
        # Pattern: date, company, ticker, drug, event type
        date_pattern = r'(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})'
        ticker_pattern = r'\b([A-Z]{2,5})\b'
        
        # Extract table rows (this is a simplified approach)
        lines = html.split('\n')
        
        for line in lines:
            # Look for lines that might contain catalyst data
            if 'PDUFA' in line or 'FDA' in line or 'Phase' in line:
                dates = re.findall(date_pattern, line)
                tickers = re.findall(ticker_pattern, line)
                
                if dates and len(dates) > 0:
                    event = {
                        'date': dates[0],
                        'ticker': tickers[0] if tickers else 'N/A',
                        'event_type': 'PDUFA' if 'PDUFA' in line else 'FDA Decision',
                        'source': 'web_scrape',
                        'raw_text': line.strip()[:200]  # First 200 chars for context
                    }
                    events.append(event)
        
        return events[:50]  # Limit to 50 events
        
    except Exception as e:
        print(f"Scraping failed for {calendar_type}: {e}")
        return []


def get_fda_calendar(days_ahead: int = 90) -> List[Dict]:
    """
    Get upcoming FDA decision dates.
    
    Args:
        days_ahead: Number of days to look ahead (default 90)
        
    Returns:
        List of FDA catalyst events with dates, tickers, drugs, and event types
        
    Example:
        >>> events = get_fda_calendar(60)
        >>> print(f"Found {len(events)} FDA events in next 60 days")
    """
    # Try API first
    cutoff_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
    api_data = _try_api_endpoint('fda-calendar', {'days': days_ahead, 'limit': 100})
    
    if api_data and isinstance(api_data, dict) and 'events' in api_data:
        return api_data['events']
    
    # Fallback to scraping
    events = _scrape_calendar_page('fda-calendar')
    
    # Filter by date range
    filtered = []
    cutoff = datetime.now() + timedelta(days=days_ahead)
    
    for event in events:
        try:
            # Try parsing date
            date_str = event.get('date', '')
            if '/' in date_str:
                event_date = datetime.strptime(date_str, '%m/%d/%Y')
            else:
                event_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            if event_date <= cutoff:
                filtered.append(event)
        except Exception:
            # If date parsing fails, include it anyway
            filtered.append(event)
    
    return filtered


def get_pdufa_dates(days_ahead: int = 90) -> List[Dict]:
    """
    Get upcoming PDUFA (Prescription Drug User Fee Act) dates.
    
    PDUFA dates are critical FDA action deadlines for drug approvals.
    
    Args:
        days_ahead: Number of days to look ahead (default 90)
        
    Returns:
        List of PDUFA events with dates, companies, drugs, and probability estimates
        
    Example:
        >>> pdufa = get_pdufa_dates(30)
        >>> for event in pdufa[:3]:
        >>>     print(f"{event['date']}: {event.get('ticker', 'N/A')} - {event.get('drug', 'N/A')}")
    """
    # Try API first
    api_data = _try_api_endpoint('pdufa-calendar', {'days': days_ahead, 'limit': 100})
    
    if api_data and isinstance(api_data, dict) and 'events' in api_data:
        return api_data['events']
    
    # Fallback to scraping
    events = _scrape_calendar_page('pdufa-calendar')
    
    # Filter by date range
    filtered = []
    cutoff = datetime.now() + timedelta(days=days_ahead)
    
    for event in events:
        try:
            date_str = event.get('date', '')
            if '/' in date_str:
                event_date = datetime.strptime(date_str, '%m/%d/%Y')
            else:
                event_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            if event_date <= cutoff:
                # Mark as PDUFA
                event['event_type'] = 'PDUFA'
                filtered.append(event)
        except Exception:
            filtered.append(event)
    
    return filtered


def get_pipeline_by_ticker(ticker: str) -> Dict:
    """
    Get drug pipeline for a specific company by ticker symbol.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'MRNA', 'PFE')
        
    Returns:
        Dictionary with company pipeline data including drugs, phases, and catalysts
        
    Example:
        >>> pipeline = get_pipeline_by_ticker('MRNA')
        >>> print(f"Found {len(pipeline.get('drugs', []))} drugs in pipeline")
    """
    # Try API first
    api_data = _try_api_endpoint(f'pipeline/{ticker.upper()}')
    
    if api_data:
        return api_data
    
    # Fallback: search in scraped calendars
    all_events = get_upcoming_catalysts(limit=200)
    
    ticker_events = [e for e in all_events if e.get('ticker', '').upper() == ticker.upper()]
    
    return {
        'ticker': ticker.upper(),
        'drugs': len(ticker_events),
        'upcoming_catalysts': ticker_events,
        'source': 'calendar_aggregation',
        'note': 'Pipeline data aggregated from calendar events (API unavailable)'
    }


def get_upcoming_catalysts(limit: int = 20) -> List[Dict]:
    """
    Get upcoming catalyst events across all companies.
    
    Combines FDA decisions, PDUFA dates, and clinical trial readouts.
    
    Args:
        limit: Maximum number of events to return (default 20)
        
    Returns:
        List of catalyst events sorted by date
        
    Example:
        >>> catalysts = get_upcoming_catalysts(10)
        >>> for cat in catalysts:
        >>>     print(f"{cat['date']}: {cat.get('ticker')} - {cat.get('event_type')}")
    """
    # Try API first
    api_data = _try_api_endpoint('catalysts', {'limit': limit})
    
    if api_data and isinstance(api_data, (list, dict)):
        if isinstance(api_data, dict) and 'catalysts' in api_data:
            return api_data['catalysts'][:limit]
        elif isinstance(api_data, list):
            return api_data[:limit]
    
    # Fallback: merge FDA and PDUFA calendars
    fda_events = get_fda_calendar(days_ahead=180)
    pdufa_events = get_pdufa_dates(days_ahead=180)
    
    all_events = fda_events + pdufa_events
    
    # Sort by date
    def parse_date(event):
        try:
            date_str = event.get('date', '')
            if '/' in date_str:
                return datetime.strptime(date_str, '%m/%d/%Y')
            else:
                return datetime.strptime(date_str, '%Y-%m-%d')
        except Exception:
            return datetime.now() + timedelta(days=9999)
    
    all_events.sort(key=parse_date)
    
    return all_events[:limit]


def search_drugs(query: str) -> List[Dict]:
    """
    Search drug pipeline by drug name or company name.
    
    Args:
        query: Search term (drug name, company name, or indication)
        
    Returns:
        List of matching drugs and their pipeline status
        
    Example:
        >>> results = search_drugs('mRNA')
        >>> for drug in results:
        >>>     print(f"{drug.get('name')}: {drug.get('phase')}")
    """
    # Try API first
    api_data = _try_api_endpoint('search', {'q': query, 'limit': 50})
    
    if api_data and isinstance(api_data, (list, dict)):
        if isinstance(api_data, dict) and 'results' in api_data:
            return api_data['results']
        elif isinstance(api_data, list):
            return api_data
    
    # Fallback: filter calendar events by query
    all_events = get_upcoming_catalysts(limit=200)
    
    query_lower = query.lower()
    matches = []
    
    for event in all_events:
        # Search in all text fields
        searchable = json.dumps(event).lower()
        if query_lower in searchable:
            matches.append(event)
    
    return matches[:50]


def get_latest() -> Dict:
    """
    Get latest catalyst summary and pipeline statistics.
    
    Returns:
        Dictionary with recent catalysts and market overview
    """
    upcoming = get_upcoming_catalysts(limit=10)
    
    return {
        'timestamp': datetime.now().isoformat(),
        'upcoming_catalysts': upcoming,
        'next_7_days': len([e for e in upcoming if _is_within_days(e, 7)]),
        'next_30_days': len([e for e in upcoming if _is_within_days(e, 30)]),
        'data_source': 'biopharmcatalyst',
    }


def _is_within_days(event: Dict, days: int) -> bool:
    """Helper to check if event is within N days."""
    try:
        date_str = event.get('date', '')
        if '/' in date_str:
            event_date = datetime.strptime(date_str, '%m/%d/%Y')
        else:
            event_date = datetime.strptime(date_str, '%Y-%m-%d')
        
        return event_date <= datetime.now() + timedelta(days=days)
    except Exception:
        return False


if __name__ == "__main__":
    print(json.dumps({
        "module": "biopharmcatalyst_pipeline_api",
        "status": "active",
        "functions": [
            "get_fda_calendar(days_ahead=90)",
            "get_pdufa_dates(days_ahead=90)",
            "get_pipeline_by_ticker(ticker)",
            "get_upcoming_catalysts(limit=20)",
            "search_drugs(query)",
            "get_latest()"
        ],
        "mode": "dual (API + web scraping fallback)",
        "source": "https://www.biopharmcatalyst.com"
    }, indent=2))
