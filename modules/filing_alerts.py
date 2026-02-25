#!/usr/bin/env python3
"""
13D/13G Filing Alerts Module — Real-time SEC EDGAR RSS Notifications

Monitors SEC EDGAR RSS feeds for new activist filings and stake changes:
- Schedule 13D (hostile activist positions >5%)
- Schedule 13G (passive stakes >5%)
- SC 13D/SC 13G amendments

Data Sources:
- SEC EDGAR RSS Feeds (free, real-time)
  - https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=SC%2013D&company=&dateb=&owner=exclude&start=0&count=40&output=atom
  - https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=SC%2013G&company=&dateb=&owner=exclude&start=0&count=40&output=atom
  - https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=13D&company=&dateb=&owner=exclude&start=0&count=40&output=atom
  - https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=13G&company=&dateb=&owner=exclude&start=0&count=40&output=atom

Features:
- Real-time RSS polling for new filings
- Parse filer name, target company, filing date, accession number
- Detect amendments vs initial filings
- Extract URLs for full filing access
- Alert on activist campaigns and major stake changes

Author: QUANTCLAW DATA Build Agent
Phase: 68
"""

import feedparser
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import sys
import re
from urllib.parse import urlencode


# SEC EDGAR RSS Feed URLs
SEC_RSS_FEEDS = {
    "SC 13D": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=SC%2013D&company=&dateb=&owner=exclude&start=0&count=40&output=atom",
    "SC 13G": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=SC%2013G&company=&dateb=&owner=exclude&start=0&count=40&output=atom",
    "13D": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=13D&company=&dateb=&owner=exclude&start=0&count=40&output=atom",
    "13G": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=13G&company=&dateb=&owner=exclude&start=0&count=40&output=atom",
}


def parse_rss_feed(feed_url: str, filing_type: str) -> List[Dict]:
    """
    Parse SEC EDGAR RSS feed and extract filing details
    Returns list of filing dictionaries
    """
    try:
        # SEC requires User-Agent header - fetch with requests then parse
        headers = {'User-Agent': 'QuantClaw Research Tool contact@quantclaw.com'}
        response = requests.get(feed_url, headers=headers, timeout=10)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        
        filings = []
        for entry in feed.entries:
            try:
                # Extract filing metadata from entry
                title = entry.get('title', '')
                summary = entry.get('summary', '')
                link = entry.get('link', '')
                published = entry.get('published', '')
                
                # Parse title format: "COMPANY NAME - Filing Type - Date"
                # Example: "TESLA INC - SC 13D/A - 2026-02-24"
                parts = title.split(' - ')
                company_name = parts[0].strip() if len(parts) > 0 else 'Unknown'
                file_type = parts[1].strip() if len(parts) > 1 else filing_type
                file_date = parts[2].strip() if len(parts) > 2 else ''
                
                # Check if amendment
                is_amendment = '/A' in file_type or 'AMENDMENT' in title.upper()
                
                # Extract accession number from link
                # Link format: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001318605&type=SC%2013D&dateb=&owner=exclude&count=40
                accession_match = re.search(r'CIK=(\d+)', link)
                cik = accession_match.group(1) if accession_match else 'N/A'
                
                # Extract filer info from summary if available
                filer_match = re.search(r'Filed by:\s*([^<]+)', summary)
                filer = filer_match.group(1).strip() if filer_match else 'Unknown'
                
                filing = {
                    'company_name': company_name,
                    'filing_type': file_type,
                    'filing_date': file_date or published[:10],
                    'is_amendment': is_amendment,
                    'filer': filer,
                    'cik': cik,
                    'url': link,
                    'published_time': published,
                    'summary': summary[:200] if summary else ''
                }
                
                filings.append(filing)
                
            except Exception as e:
                print(f"⚠️  Error parsing entry: {e}", file=sys.stderr)
                continue
        
        return filings
        
    except Exception as e:
        print(f"❌ Error fetching RSS feed: {e}", file=sys.stderr)
        return []


def get_recent_filings(filing_types: List[str] = None, hours: int = 24) -> Dict:
    """
    Get recent 13D/13G filings from all RSS feeds
    
    Args:
        filing_types: List of filing types to monitor (default: all)
        hours: Lookback window in hours (default: 24)
    
    Returns:
        Dict with filing counts and details
    """
    if filing_types is None:
        filing_types = ["SC 13D", "SC 13G", "13D", "13G"]
    
    all_filings = []
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    for filing_type in filing_types:
        if filing_type not in SEC_RSS_FEEDS:
            print(f"⚠️  Unknown filing type: {filing_type}", file=sys.stderr)
            continue
        
        feed_url = SEC_RSS_FEEDS[filing_type]
        filings = parse_rss_feed(feed_url, filing_type)
        
        # Filter by time window
        for filing in filings:
            try:
                # Parse published time
                pub_time = datetime.strptime(filing['published_time'][:19], '%Y-%m-%dT%H:%M:%S')
                if pub_time >= cutoff_time:
                    filing['filing_category'] = filing_type
                    all_filings.append(filing)
            except:
                # If can't parse time, include it anyway
                filing['filing_category'] = filing_type
                all_filings.append(filing)
    
    # Sort by published time (most recent first)
    all_filings.sort(key=lambda x: x.get('published_time', ''), reverse=True)
    
    # Count filings by type
    type_counts = {}
    amendment_counts = {}
    for filing in all_filings:
        ft = filing['filing_category']
        type_counts[ft] = type_counts.get(ft, 0) + 1
        if filing['is_amendment']:
            amendment_counts[ft] = amendment_counts.get(ft, 0) + 1
    
    return {
        'total_filings': len(all_filings),
        'type_counts': type_counts,
        'amendment_counts': amendment_counts,
        'lookback_hours': hours,
        'filings': all_filings
    }


def get_company_filings(company_name: str, filing_types: List[str] = None) -> Dict:
    """
    Search for 13D/13G filings by company name
    
    Args:
        company_name: Company name to search (case-insensitive partial match)
        filing_types: List of filing types to search (default: all)
    
    Returns:
        Dict with matching filings
    """
    if filing_types is None:
        filing_types = ["SC 13D", "SC 13G", "13D", "13G"]
    
    # Get all recent filings (extended window for search)
    recent = get_recent_filings(filing_types, hours=168)  # 7 days
    
    # Filter by company name
    company_upper = company_name.upper()
    matches = [
        f for f in recent['filings']
        if company_upper in f['company_name'].upper()
    ]
    
    return {
        'search_term': company_name,
        'total_matches': len(matches),
        'filing_types': filing_types,
        'filings': matches
    }


def get_activist_filers(min_filings: int = 2) -> Dict:
    """
    Identify active filers with multiple recent filings
    
    Args:
        min_filings: Minimum number of filings to be considered "active"
    
    Returns:
        Dict with top activist filers and their targets
    """
    recent = get_recent_filings(filing_types=["SC 13D", "13D"], hours=720)  # 30 days
    
    # Group by filer
    filer_map = {}
    for filing in recent['filings']:
        filer = filing['filer']
        if filer not in filer_map:
            filer_map[filer] = []
        filer_map[filer].append(filing)
    
    # Filter by minimum filings
    active_filers = {
        filer: filings
        for filer, filings in filer_map.items()
        if len(filings) >= min_filings
    }
    
    # Sort by filing count
    sorted_filers = sorted(
        active_filers.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )
    
    top_filers = []
    for filer, filings in sorted_filers[:20]:  # Top 20
        targets = list(set([f['company_name'] for f in filings]))
        top_filers.append({
            'filer_name': filer,
            'filing_count': len(filings),
            'target_companies': targets,
            'recent_filings': filings[:5]  # Most recent 5
        })
    
    return {
        'total_active_filers': len(active_filers),
        'min_filings_threshold': min_filings,
        'lookback_days': 30,
        'top_filers': top_filers
    }


def watch_for_new_filings(interval_minutes: int = 15, max_iterations: int = 4):
    """
    Monitor RSS feeds for new filings in real-time
    
    Args:
        interval_minutes: Polling interval in minutes
        max_iterations: Maximum number of checks (for demo purposes)
    
    Note: In production, this would run continuously or be triggered by cron
    """
    import time
    
    print(f"🔍 Starting 13D/13G filing monitor...")
    print(f"   Polling every {interval_minutes} minutes")
    print(f"   Max iterations: {max_iterations}")
    print()
    
    seen_urls = set()
    
    for i in range(max_iterations):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking for new filings...")
        
        recent = get_recent_filings(hours=1)
        
        # Check for new filings
        new_filings = []
        for filing in recent['filings']:
            if filing['url'] not in seen_urls:
                new_filings.append(filing)
                seen_urls.add(filing['url'])
        
        if new_filings:
            print(f"🚨 Found {len(new_filings)} new filing(s):")
            for filing in new_filings:
                alert_type = "AMENDMENT" if filing['is_amendment'] else "NEW FILING"
                print(f"   [{alert_type}] {filing['filing_type']}")
                print(f"   Company: {filing['company_name']}")
                print(f"   Filed by: {filing['filer']}")
                print(f"   Date: {filing['filing_date']}")
                print(f"   URL: {filing['url']}")
                print()
        else:
            print("   No new filings detected.")
        
        if i < max_iterations - 1:
            print(f"   Waiting {interval_minutes} minutes until next check...")
            time.sleep(interval_minutes * 60)
        
        print()
    
    print("✅ Monitoring session complete.")
    print(f"   Total unique filings seen: {len(seen_urls)}")


def main():
    """CLI interface for 13D/13G filing alerts"""
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  filing-alerts-recent [--hours HOURS] [--type TYPE]")
        print("  filing-alerts-search COMPANY [--type TYPE]")
        print("  filing-alerts-activists [--min-filings N]")
        print("  filing-alerts-watch [--interval MINUTES] [--iterations N]")
        print()
        print("Examples:")
        print("  filing-alerts-recent                       # Last 24 hours, all types")
        print("  filing-alerts-recent --hours 48            # Last 48 hours")
        print("  filing-alerts-recent --type 'SC 13D'       # Only hostile activist filings")
        print("  filing-alerts-search TESLA                 # All Tesla 13D/13G filings")
        print("  filing-alerts-activists --min-filings 3    # Active filers with 3+ filings")
        print("  filing-alerts-watch --interval 15          # Monitor for new filings every 15 min")
        return
    
    command = sys.argv[1]
    
    if command == 'filing-alerts-recent':
        # Parse optional arguments
        hours = 24
        filing_type = None
        
        for i, arg in enumerate(sys.argv[2:]):
            if arg == '--hours' and i + 3 < len(sys.argv):
                hours = int(sys.argv[i + 3])
            elif arg == '--type' and i + 3 < len(sys.argv):
                filing_type = sys.argv[i + 3]
        
        filing_types = [filing_type] if filing_type else None
        result = get_recent_filings(filing_types, hours)
        
        print(f"📊 Recent 13D/13G Filings (Last {hours} hours)")
        print(f"Total Filings: {result['total_filings']}")
        print()
        
        print("By Type:")
        for ft, count in result['type_counts'].items():
            amendments = result['amendment_counts'].get(ft, 0)
            print(f"  {ft}: {count} ({amendments} amendments)")
        print()
        
        print("Recent Filings:")
        for filing in result['filings'][:20]:  # Show top 20
            alert_icon = "📝" if filing['is_amendment'] else "🚨"
            print(f"{alert_icon} {filing['filing_type']}")
            print(f"   Company: {filing['company_name']}")
            print(f"   Filed by: {filing['filer']}")
            print(f"   Date: {filing['filing_date']}")
            print(f"   CIK: {filing['cik']}")
            print(f"   URL: {filing['url']}")
            print()
    
    elif command == 'filing-alerts-search':
        if len(sys.argv) < 3:
            print("❌ Error: Company name required")
            print("Usage: filing-alerts-search COMPANY [--type TYPE]")
            return
        
        company_name = sys.argv[2]
        
        # Parse optional filing type
        filing_type = None
        for i, arg in enumerate(sys.argv[3:]):
            if arg == '--type' and i + 4 < len(sys.argv):
                filing_type = sys.argv[i + 4]
        
        filing_types = [filing_type] if filing_type else None
        result = get_company_filings(company_name, filing_types)
        
        print(f"🔍 13D/13G Filings for '{company_name}'")
        print(f"Total Matches: {result['total_matches']}")
        print()
        
        if result['total_matches'] == 0:
            print("No recent filings found in the last 7 days.")
            print("Try a broader search term or check the SEC EDGAR website directly.")
        else:
            for filing in result['filings']:
                alert_icon = "📝" if filing['is_amendment'] else "🚨"
                print(f"{alert_icon} {filing['filing_type']}")
                print(f"   Company: {filing['company_name']}")
                print(f"   Filed by: {filing['filer']}")
                print(f"   Date: {filing['filing_date']}")
                print(f"   CIK: {filing['cik']}")
                print(f"   URL: {filing['url']}")
                print()
    
    elif command == 'filing-alerts-activists':
        # Parse optional min_filings
        min_filings = 2
        for i, arg in enumerate(sys.argv[2:]):
            if arg == '--min-filings' and i + 3 < len(sys.argv):
                min_filings = int(sys.argv[i + 3])
        
        result = get_activist_filers(min_filings)
        
        print(f"🎯 Active 13D Filers (Last 30 Days)")
        print(f"Total Active Filers: {result['total_active_filers']}")
        print(f"Minimum Filings: {min_filings}")
        print()
        
        print("Top Activist Filers:")
        for filer_info in result['top_filers']:
            print(f"📌 {filer_info['filer_name']}")
            print(f"   Filings: {filer_info['filing_count']}")
            print(f"   Targets: {', '.join(filer_info['target_companies'][:5])}")
            if len(filer_info['target_companies']) > 5:
                print(f"            +{len(filer_info['target_companies']) - 5} more...")
            print()
    
    elif command == 'filing-alerts-watch':
        # Parse optional arguments
        interval = 15
        iterations = 4
        
        for i, arg in enumerate(sys.argv[2:]):
            if arg == '--interval' and i + 3 < len(sys.argv):
                interval = int(sys.argv[i + 3])
            elif arg == '--iterations' and i + 3 < len(sys.argv):
                iterations = int(sys.argv[i + 3])
        
        watch_for_new_filings(interval, iterations)
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Run module without arguments for usage help.")


if __name__ == '__main__':
    main()
