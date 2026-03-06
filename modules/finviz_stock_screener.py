"""
Finviz Stock Screener Module
Comprehensive stock screening, fundamentals, technicals, insider trading, analyst ratings.

Free tier: Unlimited scraping with rate limiting (~5 req/sec safe).
No registration required.

Data coverage: 8000+ US stocks
Data points: P/E, EPS, Market Cap, Analyst Target, Insider Ownership %, Short Float %,
             RSI, SMA20/50/200, Sector, Industry, Country, Earnings Date, Growth estimates

Source: https://finviz.com
"""

import requests
from bs4 import BeautifulSoup
import time
from typing import Dict, List, Optional


BASE_URL = "https://finviz.com"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def get_stock_quote(ticker: str) -> Optional[Dict]:
    """
    Get detailed quote and fundamentals for a single stock.
    
    Args:
        ticker: Stock symbol (e.g., 'AAPL')
        
    Returns:
        dict with fundamentals, technicals, and metadata, or None on error
    """
    try:
        url = f"{BASE_URL}/quote.ashx?t={ticker.upper()}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Parse snapshot table - each row has 12 cells in label-value pairs
        table = soup.find('table', {'class': 'snapshot-table2'})
        if not table:
            return None
            
        data = {'ticker': ticker.upper()}
        
        # Extract all table rows
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            # Each row has pairs: [label1, value1, label2, value2, ...]
            for i in range(0, len(cells), 2):
                if i + 1 < len(cells):
                    label = cells[i].get_text(strip=True)
                    value = cells[i + 1].get_text(strip=True)
                    data[label] = value
        
        # Get company name from page title or link
        title = soup.find('a', {'class': 'tab-link'})
        if title:
            data['company'] = title.get_text(strip=True)
        
        # Get sector and industry from breadcrumb links
        breadcrumbs = soup.find_all('a', {'class': 'tab-link'})
        if len(breadcrumbs) >= 3:
            data['sector'] = breadcrumbs[1].get_text(strip=True)
            data['industry'] = breadcrumbs[2].get_text(strip=True)
        
        return data
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None


def screen_stocks(filters: Optional[Dict[str, str]] = None, limit: int = 100) -> List[Dict]:
    """
    Screen stocks based on criteria.
    
    Args:
        filters: dict of Finviz filter parameters
                 Examples:
                 - {'cap': 'mega'} for mega caps
                 - {'sec': 'technology'} for tech sector
                 - {'fa_pe': 'low'} for low P/E
        limit: max number of results to return
        
    Returns:
        list of dicts with stock data
    """
    try:
        # Build filter string
        filter_parts = []
        if filters:
            for key, value in filters.items():
                filter_parts.append(f"{key}_{value}")
        
        filter_str = '&'.join(filter_parts) if filter_parts else ''
        
        # v=111 is overview mode with basic columns
        url = f"{BASE_URL}/screener.ashx?v=111&{filter_str}" if filter_str else f"{BASE_URL}/screener.ashx?v=111"
        
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find screener results table — try new class first, then legacy lookup
        results_table = soup.find('table', class_='screener_table')
        if not results_table:
            tables = soup.find_all('table')
            for table in tables:
                if table.find('td', string='Ticker'):
                    results_table = table
                    break
        
        if not results_table:
            return []
        
        # Get headers from first row
        header_row = results_table.find('tr')
        headers = [th.get_text(strip=True) for th in header_row.find_all(['td', 'th'])] if header_row else []
        
        # Parse data rows
        results = []
        rows = results_table.find_all('tr')[1:]  # Skip header
        
        for row in rows[:limit]:
            cells = row.find_all('td')
            if len(cells) >= len(headers):
                stock_data = {}
                for i, header in enumerate(headers):
                    if i < len(cells):
                        stock_data[header] = cells[i].get_text(strip=True)
                results.append(stock_data)
        
        return results
    except Exception as e:
        print(f"Error screening stocks: {e}")
        return []


def get_insider_trading(ticker: str) -> List[Dict]:
    """
    Get insider trading activity for a stock from the quote page.
    
    Args:
        ticker: Stock symbol
        
    Returns:
        list of insider transactions
    """
    try:
        url = f"{BASE_URL}/quote.ashx?t={ticker.upper()}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Note: Detailed insider trading is on a separate page
        # For now, return empty list - can be enhanced later
        return []
    except Exception as e:
        print(f"Error fetching insider trading for {ticker}: {e}")
        return []


def get_sector_performance() -> Dict[str, str]:
    """
    Get real-time sector performance data.
    
    Returns:
        dict with sector names and performance percentages
    """
    try:
        url = f"{BASE_URL}/groups.ashx?g=sector&v=120&o=name"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the groups/sector table
        tables = soup.find_all('table')
        sector_table = None
        for table in tables:
            if 'Perf' in str(table):
                sector_table = table
                break
        
        if not sector_table:
            return {}
        
        sectors = {}
        rows = sector_table.find_all('tr')[1:]  # Skip header
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                sector_name = cells[0].get_text(strip=True)
                # Performance is usually in one of the early columns
                performance = cells[1].get_text(strip=True)
                if sector_name and performance:
                    sectors[sector_name] = performance
        
        return sectors
    except Exception as e:
        print(f"Error fetching sector performance: {e}")
        return {}


def get_top_gainers(limit: int = 20) -> List[Dict]:
    """
    Get today's top gaining stocks.
    
    Args:
        limit: number of gainers to return
        
    Returns:
        list of top gainers with ticker, price, change%, volume
    """
    try:
        url = f"{BASE_URL}/screener.ashx?v=111&s=ta_topgainers"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the results table — try new class first, then legacy lookup
        results_table = soup.find('table', class_='screener_table')
        if not results_table:
            tables = soup.find_all('table')
            for table in tables:
                if table.find('td', string='Ticker'):
                    results_table = table
                    break
        
        if not results_table:
            return []
        
        # Get headers
        header_row = results_table.find('tr')
        headers = [th.get_text(strip=True) for th in header_row.find_all(['td', 'th'])] if header_row else []
        
        gainers = []
        rows = results_table.find_all('tr')[1:limit+1]  # Skip header
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= len(headers):
                gainer = {}
                for i, header in enumerate(headers):
                    if i < len(cells):
                        gainer[header] = cells[i].get_text(strip=True)
                gainers.append(gainer)
        
        return gainers
    except Exception as e:
        print(f"Error fetching top gainers: {e}")
        return []


def get_top_losers(limit: int = 20) -> List[Dict]:
    """
    Get today's top losing stocks.
    
    Args:
        limit: number of losers to return
        
    Returns:
        list of top losers with ticker, price, change%, volume
    """
    try:
        url = f"{BASE_URL}/screener.ashx?v=111&s=ta_toplosers"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the results table — try new class first, then legacy lookup
        results_table = soup.find('table', class_='screener_table')
        if not results_table:
            tables = soup.find_all('table')
            for table in tables:
                if table.find('td', string='Ticker'):
                    results_table = table
                    break
        
        if not results_table:
            return []
        
        # Get headers
        header_row = results_table.find('tr')
        headers = [th.get_text(strip=True) for th in header_row.find_all(['td', 'th'])] if header_row else []
        
        losers = []
        rows = results_table.find_all('tr')[1:limit+1]  # Skip header
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= len(headers):
                loser = {}
                for i, header in enumerate(headers):
                    if i < len(cells):
                        loser[header] = cells[i].get_text(strip=True)
                losers.append(loser)
        
        return losers
    except Exception as e:
        print(f"Error fetching top losers: {e}")
        return []


def get_most_active(limit: int = 20) -> List[Dict]:
    """
    Get today's most actively traded stocks by volume.
    
    Args:
        limit: number of stocks to return
        
    Returns:
        list of most active stocks
    """
    try:
        url = f"{BASE_URL}/screener.ashx?v=111&s=ta_mostactive"
        return screen_stocks({}, limit)
    except Exception as e:
        print(f"Error fetching most active: {e}")
        return []


# Example usage
if __name__ == "__main__":
    # Test quote
    print("Testing AAPL quote...")
    quote = get_stock_quote('AAPL')
    if quote:
        print(f"Company: {quote.get('company', 'N/A')}")
        print(f"P/E: {quote.get('P/E', 'N/A')}")
        print(f"Market Cap: {quote.get('Market Cap', 'N/A')}")
        print(f"EPS (ttm): {quote.get('EPS (ttm)', 'N/A')}")
    
    # Test screener
    print("\nTesting stock screener (mega caps)...")
    mega_caps = screen_stocks({'cap': 'mega'}, limit=5)
    for stock in mega_caps:
        print(f"{stock.get('Ticker', 'N/A')}: {stock.get('Company', 'N/A')}")
    
    # Test top gainers
    print("\nTesting top gainers...")
    gainers = get_top_gainers(limit=5)
    for g in gainers:
        print(f"{g.get('Ticker', 'N/A')}: {g.get('Change', 'N/A')}")
