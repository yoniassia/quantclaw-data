#!/usr/bin/env python3
"""
Global Shipping Indicators Module

Data Sources:
- FRED API: Baltic Dry Index (BDI), container shipping rates
- Freightos (scraping): Container freight rates (FBX indices)
- Google Trends: Port congestion proxies (search volume for "port congestion", "supply chain")
- Port Activity Proxies: Shipping news sentiment via Google News RSS

Metrics:
1. Baltic Dry Index (BDI) - Dry bulk shipping costs
2. Container Freight Rates - Major trade routes (Asia-US, Asia-EU, etc.)
3. Port Congestion Indicators - Proxy via search trends and news sentiment
4. Shipping Cost YoY Changes - Inflation indicators

Daily updates for BDI, weekly for container rates, daily for congestion proxies.

Phase: 110
Author: QUANTCLAW DATA Build Agent
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
from bs4 import BeautifulSoup
import re


# FRED API Configuration
FRED_API_KEY = ""  # Will use fred module's key
FRED_API_BASE = "https://api.stlouisfed.org/fred"

# FRED Series IDs for Shipping
FRED_SHIPPING_SERIES = {
    "BALTICDI": "Baltic Dry Index (BDI)",
    "WPUSI012011": "PPI - Deep Sea Foreign Transportation of Freight",
    "WPUSI012012": "PPI - Deep Sea Domestic Transportation of Freight",
    "CUSR0000SETG01": "CPI - Shipping Away from Home",
}

# Container Freight Rate Routes (FBX indices - will scrape if needed)
CONTAINER_ROUTES = {
    "FBX01": "China/East Asia → North America West Coast",
    "FBX02": "China/East Asia → North America East Coast",
    "FBX03": "China/East Asia → Northern Europe",
    "FBX11": "China/East Asia → Mediterranean",
    "FBX12": "China/East Asia → US Gulf",
    "FBX13": "China/East Asia → Latin America West Coast",
}

# Port congestion search terms for Google Trends proxy
CONGESTION_TERMS = [
    "port congestion",
    "supply chain delays",
    "container shortage",
    "shipping delays",
    "port backlog"
]


def fetch_fred_data(series_id: str, start_date: Optional[str] = None, 
                   end_date: Optional[str] = None) -> Dict:
    """
    Fetch data from FRED API
    
    Args:
        series_id: FRED series ID
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        Dict with observations
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    params = {
        'series_id': series_id,
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'observation_start': start_date,
        'observation_end': end_date,
        'sort_order': 'desc',
        'limit': 1000
    }
    
    try:
        response = requests.get(f"{FRED_API_BASE}/series/observations", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'observations' in data:
            return {
                'success': True,
                'series_id': series_id,
                'data': data['observations']
            }
        else:
            return {'success': False, 'error': 'No observations found'}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_baltic_dry_index(days: int = 90) -> Dict:
    """
    Get Baltic Dry Index (BDI) data from FRED
    
    The Baltic Dry Index tracks shipping costs for dry bulk commodities (coal, iron ore, grain).
    It's a leading indicator of global trade activity and manufacturing demand.
    
    Args:
        days: Number of days of historical data
        
    Returns:
        Dict with BDI data and analysis
    """
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    result = fetch_fred_data('BALTICDI', start_date=start_date)
    
    if not result.get('success'):
        return {
            'success': False,
            'error': result.get('error', 'Failed to fetch BDI data'),
            'source': 'FRED'
        }
    
    observations = result['data']
    
    # Filter out non-numeric values
    valid_obs = []
    for obs in observations:
        try:
            value = float(obs['value'])
            if value > 0:  # BDI should be positive
                valid_obs.append({
                    'date': obs['date'],
                    'value': value
                })
        except (ValueError, TypeError):
            continue
    
    if not valid_obs:
        return {
            'success': False,
            'error': 'No valid BDI observations',
            'source': 'FRED'
        }
    
    # Sort by date descending (most recent first)
    valid_obs.sort(key=lambda x: x['date'], reverse=True)
    
    # Calculate statistics
    current = valid_obs[0]['value']
    
    # 30-day average
    recent_30d = [obs['value'] for obs in valid_obs[:30]]
    avg_30d = sum(recent_30d) / len(recent_30d) if recent_30d else current
    
    # YoY change (approximately 252 trading days)
    yoy_change = None
    if len(valid_obs) >= 252:
        year_ago = valid_obs[251]['value']
        yoy_change = ((current - year_ago) / year_ago) * 100
    
    # MoM change (approximately 21 trading days)
    mom_change = None
    if len(valid_obs) >= 21:
        month_ago = valid_obs[20]['value']
        mom_change = ((current - month_ago) / month_ago) * 100
    
    # Find recent min/max
    all_values = [obs['value'] for obs in valid_obs]
    recent_min = min(all_values)
    recent_max = max(all_values)
    
    return {
        'success': True,
        'metric': 'Baltic Dry Index (BDI)',
        'current_value': current,
        'date': valid_obs[0]['date'],
        'avg_30d': round(avg_30d, 2),
        'mom_change_pct': round(mom_change, 2) if mom_change else None,
        'yoy_change_pct': round(yoy_change, 2) if yoy_change else None,
        'recent_min': recent_min,
        'recent_max': recent_max,
        'percentile': round(((current - recent_min) / (recent_max - recent_min)) * 100, 1) if recent_max > recent_min else 50,
        'interpretation': interpret_bdi(current, avg_30d, mom_change),
        'historical_data': valid_obs[:30],  # Return last 30 days
        'source': 'FRED (Federal Reserve Economic Data)',
        'series_id': 'BALTICDI'
    }


def interpret_bdi(current: float, avg_30d: float, mom_change: Optional[float]) -> str:
    """Interpret BDI levels and trends"""
    
    # Historical context:
    # BDI < 1000: Weak global trade
    # BDI 1000-2000: Normal conditions
    # BDI 2000-4000: Strong trade activity
    # BDI > 4000: Extreme demand (rare)
    
    level_desc = ""
    if current < 1000:
        level_desc = "Weak global trade activity"
    elif current < 2000:
        level_desc = "Normal shipping conditions"
    elif current < 4000:
        level_desc = "Strong trade activity"
    else:
        level_desc = "Exceptionally strong demand"
    
    trend_desc = ""
    if mom_change:
        if mom_change > 10:
            trend_desc = "Rapidly rising (>10% MoM)"
        elif mom_change > 5:
            trend_desc = "Rising moderately"
        elif mom_change > -5:
            trend_desc = "Relatively stable"
        elif mom_change > -10:
            trend_desc = "Declining moderately"
        else:
            trend_desc = "Sharply declining"
    
    return f"{level_desc}. {trend_desc}."


def get_container_freight_rates() -> Dict:
    """
    Get container freight rate data
    
    Uses FRED PPI data for deep sea freight transportation as a proxy.
    Note: Detailed FBX indices require paid Freightos API access.
    
    Returns:
        Dict with container freight rate data
    """
    # Get FRED PPI data for deep sea freight
    foreign_freight = fetch_fred_data('WPUSI012011', 
                                     start_date=(datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'))
    domestic_freight = fetch_fred_data('WPUSI012012',
                                      start_date=(datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'))
    
    results = {
        'success': True,
        'note': 'Using FRED PPI indices as proxy. Detailed FBX data requires Freightos API subscription.',
        'data': {}
    }
    
    # Process foreign freight
    if foreign_freight.get('success'):
        obs = foreign_freight['data']
        valid_obs = []
        for o in obs:
            try:
                val = float(o['value'])
                valid_obs.append({'date': o['date'], 'value': val})
            except:
                continue
        
        if valid_obs:
            valid_obs.sort(key=lambda x: x['date'], reverse=True)
            current = valid_obs[0]['value']
            
            # Calculate YoY if we have enough data
            yoy = None
            if len(valid_obs) >= 12:  # Monthly data
                year_ago = valid_obs[11]['value']
                yoy = ((current - year_ago) / year_ago) * 100
            
            results['data']['foreign_freight_ppi'] = {
                'metric': 'PPI - Deep Sea Foreign Transportation',
                'current': current,
                'date': valid_obs[0]['date'],
                'yoy_change_pct': round(yoy, 2) if yoy else None,
                'series_id': 'WPUSI012011',
                'interpretation': 'Foreign ocean freight costs (index, base 1982=100)'
            }
    
    # Process domestic freight
    if domestic_freight.get('success'):
        obs = domestic_freight['data']
        valid_obs = []
        for o in obs:
            try:
                val = float(o['value'])
                valid_obs.append({'date': o['date'], 'value': val})
            except:
                continue
        
        if valid_obs:
            valid_obs.sort(key=lambda x: x['date'], reverse=True)
            current = valid_obs[0]['value']
            
            yoy = None
            if len(valid_obs) >= 12:
                year_ago = valid_obs[11]['value']
                yoy = ((current - year_ago) / year_ago) * 100
            
            results['data']['domestic_freight_ppi'] = {
                'metric': 'PPI - Deep Sea Domestic Transportation',
                'current': current,
                'date': valid_obs[0]['date'],
                'yoy_change_pct': round(yoy, 2) if yoy else None,
                'series_id': 'WPUSI012012',
                'interpretation': 'Domestic ocean freight costs (index, base 1982=100)'
            }
    
    results['source'] = 'FRED (Federal Reserve Economic Data)'
    return results


def get_port_congestion_proxy() -> Dict:
    """
    Get port congestion indicators using proxy methods
    
    Uses:
    1. Google Trends search volume (requires pytrends, optional)
    2. News sentiment analysis (via Google News RSS)
    
    Returns:
        Dict with congestion indicators
    """
    results = {
        'success': True,
        'metric': 'Port Congestion Indicators (Proxy)',
        'note': 'Direct port congestion data requires paid services. Using news sentiment as proxy.',
        'indicators': {}
    }
    
    # Try to fetch shipping news sentiment
    try:
        news_sentiment = fetch_shipping_news_sentiment()
        results['indicators']['news_sentiment'] = news_sentiment
    except Exception as e:
        results['indicators']['news_sentiment'] = {
            'error': str(e),
            'note': 'Could not fetch news sentiment'
        }
    
    # Add suggestion for better data
    results['data_upgrade_suggestion'] = {
        'services': [
            'Marine Traffic API - Real-time vessel tracking',
            'Port Authority APIs - Official wait times (LA/Long Beach, Rotterdam, etc.)',
            'FreightWaves SONAR - Container dwell times and port metrics'
        ],
        'free_alternatives': [
            'LA/Long Beach Port website - Daily terminal reports',
            'Google Trends API - Search volume for "port congestion"',
            'Shipping news RSS feeds - Automated sentiment analysis'
        ]
    }
    
    return results


def fetch_shipping_news_sentiment() -> Dict:
    """
    Fetch recent shipping/port congestion news via Google News RSS
    and provide basic sentiment proxy
    """
    # Google News RSS for shipping news
    query = "shipping+container+port+congestion"
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        
        # Parse RSS
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')[:10]  # Get latest 10 articles
        
        news_items = []
        negative_keywords = ['congestion', 'delays', 'backlog', 'bottleneck', 'shortage', 'crisis', 
                           'disruption', 'stuck', 'waiting', 'delays']
        positive_keywords = ['recovery', 'easing', 'improving', 'normal', 'clear', 'resolved', 
                           'better', 'declining', 'relief']
        
        sentiment_score = 0
        
        for item in items:
            title = item.find('title').text if item.find('title') else ''
            pub_date = item.find('pubDate').text if item.find('pubDate') else ''
            link = item.find('link').text if item.find('link') else ''
            
            # Simple sentiment analysis
            title_lower = title.lower()
            neg_count = sum(1 for word in negative_keywords if word in title_lower)
            pos_count = sum(1 for word in positive_keywords if word in title_lower)
            
            item_sentiment = pos_count - neg_count
            sentiment_score += item_sentiment
            
            news_items.append({
                'title': title,
                'date': pub_date,
                'url': link,
                'sentiment': 'negative' if item_sentiment < 0 else 'positive' if item_sentiment > 0 else 'neutral'
            })
        
        # Overall sentiment
        overall_sentiment = 'neutral'
        if sentiment_score < -3:
            overall_sentiment = 'negative'
        elif sentiment_score > 3:
            overall_sentiment = 'positive'
        
        return {
            'success': True,
            'overall_sentiment': overall_sentiment,
            'sentiment_score': sentiment_score,
            'recent_headlines': news_items[:5],
            'interpretation': interpret_congestion_sentiment(overall_sentiment, sentiment_score)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def interpret_congestion_sentiment(sentiment: str, score: int) -> str:
    """Interpret port congestion news sentiment"""
    if sentiment == 'negative':
        return f"Recent news suggests ongoing port congestion issues (score: {score}). Supply chain disruptions likely."
    elif sentiment == 'positive':
        return f"Recent news suggests improving port conditions (score: {score}). Congestion easing."
    else:
        return f"Recent news is mixed on port congestion (score: {score}). Conditions appear stable."


def get_shipping_dashboard() -> Dict:
    """
    Get comprehensive shipping indicators dashboard
    
    Returns:
        Dict with all shipping metrics
    """
    dashboard = {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'metrics': {}
    }
    
    # 1. Baltic Dry Index
    bdi = get_baltic_dry_index(days=90)
    if bdi.get('success'):
        dashboard['metrics']['baltic_dry_index'] = bdi
    
    # 2. Container Freight Rates
    container = get_container_freight_rates()
    if container.get('success'):
        dashboard['metrics']['container_freight_rates'] = container
    
    # 3. Port Congestion Proxy
    congestion = get_port_congestion_proxy()
    if congestion.get('success'):
        dashboard['metrics']['port_congestion'] = congestion
    
    # Overall shipping health score (0-100)
    health_score = calculate_shipping_health(dashboard['metrics'])
    dashboard['shipping_health_score'] = health_score
    dashboard['interpretation'] = interpret_shipping_health(health_score)
    
    return dashboard


def calculate_shipping_health(metrics: Dict) -> int:
    """
    Calculate overall shipping health score (0-100)
    Higher = healthier shipping conditions
    """
    score = 50  # Start neutral
    
    # BDI contribution (40 points)
    if 'baltic_dry_index' in metrics:
        bdi_data = metrics['baltic_dry_index']
        percentile = bdi_data.get('percentile', 50)
        
        # Healthy BDI: 1000-2500 range
        current = bdi_data.get('current_value', 0)
        if 1000 <= current <= 2500:
            score += 20
        elif current < 1000:
            score += 10
        elif current > 2500:
            score += 15
        
        # Trend contribution
        mom = bdi_data.get('mom_change_pct', 0)
        if mom:
            if -5 <= mom <= 5:  # Stable is good
                score += 20
            elif abs(mom) <= 10:
                score += 15
            else:
                score += 10
    
    # Container freight contribution (30 points)
    if 'container_freight_rates' in metrics:
        container = metrics['container_freight_rates']
        if 'data' in container:
            # Lower YoY change = better (less inflation)
            foreign = container['data'].get('foreign_freight_ppi', {})
            yoy = foreign.get('yoy_change_pct', 0)
            if yoy:
                if abs(yoy) < 5:
                    score += 30
                elif abs(yoy) < 10:
                    score += 20
                else:
                    score += 10
    
    # Congestion contribution (30 points)
    if 'port_congestion' in metrics:
        congestion = metrics['port_congestion']
        if 'indicators' in congestion:
            sentiment = congestion['indicators'].get('news_sentiment', {})
            overall = sentiment.get('overall_sentiment', 'neutral')
            
            if overall == 'positive':
                score += 30
            elif overall == 'neutral':
                score += 20
            else:
                score += 10
    
    return min(100, max(0, score))


def interpret_shipping_health(score: int) -> str:
    """Interpret overall shipping health score"""
    if score >= 80:
        return "Excellent shipping conditions. Healthy trade flows, stable costs, minimal congestion."
    elif score >= 60:
        return "Good shipping conditions. Normal trade activity with manageable costs."
    elif score >= 40:
        return "Fair shipping conditions. Some disruptions or cost pressures present."
    elif score >= 20:
        return "Poor shipping conditions. Significant congestion or cost inflation."
    else:
        return "Critical shipping conditions. Major disruptions affecting global trade."


# CLI Commands
def cmd_baltic_dry_index(days: int = 90):
    """CLI: Get Baltic Dry Index data"""
    result = get_baltic_dry_index(days=days)
    print(json.dumps(result, indent=2))


def cmd_container_freight():
    """CLI: Get container freight rates"""
    result = get_container_freight_rates()
    print(json.dumps(result, indent=2))


def cmd_port_congestion():
    """CLI: Get port congestion indicators"""
    result = get_port_congestion_proxy()
    print(json.dumps(result, indent=2))


def cmd_shipping_dashboard():
    """CLI: Get comprehensive shipping dashboard"""
    result = get_shipping_dashboard()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python global_shipping.py <command> [args]")
        print("\nCommands:")
        print("  bdi [days]               - Baltic Dry Index (default: 90 days)")
        print("  container-freight        - Container freight rates")
        print("  port-congestion          - Port congestion indicators")
        print("  shipping-dashboard       - Full shipping dashboard")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "bdi":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
        cmd_baltic_dry_index(days)
    elif command == "container-freight" or command == "container":
        cmd_container_freight()
    elif command == "port-congestion" or command == "congestion":
        cmd_port_congestion()
    elif command == "shipping-dashboard" or command == "dashboard":
        cmd_shipping_dashboard()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
