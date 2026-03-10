#!/usr/bin/env python3
"""
ETFGI Global ETF Data — Global ETF/ETP Industry Research

Data Source: ETFGI (https://etfgi.com) + ICI (Investment Company Institute)
Update: Monthly (ETFGI reports), Weekly (ICI flows)
Free: Yes (RSS feed, web scraping, ICI public data)
No paid API keys required.

Provides:
- Global ETF industry reports catalog from ETFGI RSS
- Report metadata (title, date, region, type, description)
- Key industry stats extracted from report descriptions
- ETF/ETP counts, AUM figures, provider/exchange counts
- ICI weekly ETF flow data (domestic + global)
- Historical ETF industry growth trends

Usage:
    from modules.etfgi_global_etf_data import *

    # Get latest ETFGI reports
    reports = get_etfgi_reports(limit=10)

    # Get global ETF industry snapshot from report descriptions
    snapshot = get_global_etf_snapshot()

    # Get ICI weekly ETF flows
    flows = get_ici_etf_flows()

    # Search reports by region or type
    results = search_reports(query="Europe")
"""

import requests
import json
import re
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from html import unescape

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/etfgi")
os.makedirs(CACHE_DIR, exist_ok=True)

ETFGI_RSS_URL = "https://etfgi.com/rss.xml"
ETFGI_RESEARCH_URL = "https://etfgi.com/research"
ICI_ETF_FLOWS_URL = "https://www.ici.org/statistics/etf"
ICI_COMBINED_FLOWS_URL = "https://www.ici.org/statistics/combined"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _read_cache(name: str, max_age_hours: int = 24) -> Optional[dict]:
    """Read from local cache if fresh enough."""
    path = os.path.join(CACHE_DIR, f"{name}.json")
    if os.path.exists(path):
        age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
        if age < timedelta(hours=max_age_hours):
            with open(path) as f:
                return json.load(f)
    return None


def _write_cache(name: str, data) -> None:
    """Write data to local cache."""
    path = os.path.join(CACHE_DIR, f"{name}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def _strip_html(text: str) -> str:
    """Remove HTML tags and clean whitespace."""
    text = unescape(text)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_field(html: str, field_name: str) -> str:
    """Extract a Drupal field value from rendered HTML."""
    m = re.search(
        rf'field--name-{field_name}.*?field--item["\s>]*?>(.*?)</div>',
        html, re.DOTALL
    )
    if m:
        return re.sub(r'<[^>]+>', '', m.group(1)).strip()
    return ""


def _extract_stats_from_text(text: str) -> Dict:
    """
    Extract key ETF industry statistics from text.
    Parses numbers like ETF count, AUM, providers, exchanges.
    """
    stats = {}

    # ETF count: "had X,XXX ETFs"
    m = re.search(r"had\s+([\d,]+)\s+ETFs(?!\s*/)", text)
    if m:
        stats["etf_count"] = int(m.group(1).replace(",", ""))

    # ETF/ETP count: "had X,XXX ETFs/ETPs"
    m = re.search(r"had\s+([\d,]+)\s+ETFs?/ETPs?", text)
    if m:
        stats["etf_etp_count"] = int(m.group(1).replace(",", ""))

    # Listings: "with X,XXX listings"
    m = re.search(r"([\d,]+)\s+listings", text)
    if m:
        stats["listings"] = int(m.group(1).replace(",", ""))

    # AUM: "assets of US$X,XXX Bn" or "US$X.X Tn"
    m = re.search(r"assets?\s+of\s+US?\$?([\d,.]+)\s*(Bn|Tn|billion|trillion)", text, re.I)
    if m:
        val = float(m.group(1).replace(",", ""))
        unit = m.group(2).lower()
        if unit in ("tn", "trillion"):
            val *= 1000
        stats["aum_billion_usd"] = val

    # Providers: "from X providers"
    m = re.search(r"from\s+(\d+)\s+providers?", text)
    if m:
        stats["providers"] = int(m.group(1))

    # Exchanges: "on X exchanges"
    m = re.search(r"on\s+(\d+)\s+exchanges?", text)
    if m:
        stats["exchanges"] = int(m.group(1))

    # Net inflows
    m = re.search(r"net\s+(?:in|out)flows?\s+of\s+US?\$?([\d,.]+)\s*(Bn|Mn|billion|million)", text, re.I)
    if m:
        val = float(m.group(1).replace(",", ""))
        unit = m.group(2).lower()
        if unit in ("mn", "million"):
            val /= 1000
        stats["net_flows_billion_usd"] = val

    # Period reference: "end of Month YYYY"
    m = re.search(r"end\s+of\s+(\w+\s+\d{4})", text)
    if m:
        stats["period"] = m.group(1)

    return stats


def get_etfgi_reports(limit: int = 20, use_cache: bool = True) -> List[Dict]:
    """
    Fetch ETFGI report catalog from their RSS feed.

    Uses regex-based parsing since the RSS feed contains Drupal theme
    debug comments that break standard XML parsers.

    Args:
        limit: Maximum number of reports to return.
        use_cache: Whether to use cached data (default 24h TTL).

    Returns:
        List of dicts with report metadata:
        - title: Report title
        - link: URL to report page
        - pub_date: Publication date (ISO format)
        - report_type: Type (e.g., "ETF/ETP Industry Insights")
        - region: Geographic scope (e.g., "Global", "Europe")
        - frequency: Update frequency (e.g., "Monthly")
        - description: Cleaned text description
        - stats: Extracted numeric stats (AUM, ETF count, etc.)
    """
    if use_cache:
        cached = _read_cache("etfgi_reports", max_age_hours=24)
        if cached:
            return cached[:limit]

    try:
        resp = requests.get(ETFGI_RSS_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ConnectionError(f"Failed to fetch ETFGI RSS feed: {e}")

    content = resp.text
    # Extract items via regex (XML parser fails due to Drupal comments before <?xml>)
    raw_items = re.findall(r"<item>(.*?)</item>", content, re.DOTALL)

    reports = []
    for raw_item in raw_items:
        # Remove XML comments from item
        item_clean = re.sub(r"<!--.*?-->", "", raw_item, flags=re.DOTALL)

        # Title
        m = re.search(r"<title>(.*?)</title>", item_clean, re.DOTALL)
        title = _strip_html(m.group(1)) if m else ""

        # Link
        m = re.search(r"<link>(.*?)</link>", item_clean, re.DOTALL)
        link = m.group(1).strip() if m else ""

        # Description — HTML-encoded Drupal fields
        m = re.search(r"<description>(.*?)</description>", item_clean, re.DOTALL)
        raw_desc = unescape(m.group(1)) if m else ""

        # Extract structured fields from rendered HTML
        report_type = _extract_field(raw_desc, "field-report-type")
        region = _extract_field(raw_desc, "field-reg")
        frequency = _extract_field(raw_desc, "field-frequency")
        description = _extract_field(raw_desc, "field-description")

        # Publication date
        pub_date = ""
        m = re.search(r'datetime="(\d{4}-\d{2}-\d{2})', raw_desc)
        if m:
            pub_date = m.group(1)

        # Infer region from title if not found in fields
        if not region:
            for r in ["Global", "Europe", "US", "Asia Pacific", "Latin America",
                       "Middle East", "Africa", "Canada", "Japan", "China", "India"]:
                if r.lower() in title.lower():
                    region = r
                    break

        # Extract stats from description text
        stats = _extract_stats_from_text(description)

        reports.append({
            "title": title,
            "link": link,
            "pub_date": pub_date,
            "report_type": report_type,
            "region": region,
            "frequency": frequency,
            "description": description[:500],
            "stats": stats,
        })

    _write_cache("etfgi_reports", reports)
    return reports[:limit]


def get_research_catalog(page: int = 0, limit: int = 10, use_cache: bool = True) -> List[Dict]:
    """
    Scrape ETFGI research catalog page for recent report listings.

    This is the primary source for recent/current data since the RSS feed
    only contains a few items. The research page has 2500+ reports.

    Args:
        page: Page number (0-indexed, 10 results per page).
        limit: Max results to return from this page.
        use_cache: Whether to use cached data (default 6h TTL).

    Returns:
        List of dicts with:
        - title: Report title
        - link: Full URL to report page
        - report_id: Numeric report ID
        - month: Publication month (e.g., "March 2026")
        - region: Inferred from title
    """
    cache_key = f"research_catalog_page_{page}"
    if use_cache:
        cached = _read_cache(cache_key, max_age_hours=6)
        if cached:
            return cached[:limit]

    url = f"{ETFGI_RESEARCH_URL}?page={page}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ConnectionError(f"Failed to fetch ETFGI research page: {e}")

    html = resp.text

    # Extract report links
    links = re.findall(r'href="(/research/report/(\d+)/([^"]+))"[^>]*>([^<]+)', html)

    results = []
    for path, report_id, slug, title in links[:limit]:
        title = title.strip()
        full_url = f"https://etfgi.com{path}"

        # Infer region from title
        region = ""
        for r in ["Global", "Europe", "European", "US", "United States",
                   "Asia Pacific", "Asia", "Latin America", "Middle East",
                   "Africa", "Canada", "Japan", "China", "India", "Australia"]:
            if r.lower() in title.lower():
                region = r.replace("European", "Europe")
                break

        results.append({
            "title": title,
            "link": full_url,
            "report_id": int(report_id),
            "slug": slug,
            "region": region,
        })

    _write_cache(cache_key, results)
    return results[:limit]


def get_report_description(report_url: str) -> Dict:
    """
    Fetch the description from an individual ETFGI report page.

    Args:
        report_url: Full URL to an ETFGI report page.

    Returns:
        Dict with:
        - title: Report title
        - description: Report description text
        - stats: Extracted numeric stats if any
        - url: The report URL
    """
    try:
        resp = requests.get(report_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"url": report_url, "error": f"Failed to fetch: {e}"}

    html = resp.text

    # Extract title
    title = ""
    m = re.search(r'<title>([^<]+)</title>', html)
    if m:
        title = _strip_html(m.group(1)).split("|")[0].strip()

    # Extract description field
    description = ""
    m = re.search(r'field--name-field-description.*?field--item[^>]*>(.*?)</div>', html, re.DOTALL)
    if m:
        description = _strip_html(m.group(1))

    stats = _extract_stats_from_text(description)

    return {
        "title": title,
        "description": description,
        "stats": stats,
        "url": report_url,
    }


def search_reports(query: str, limit: int = 10) -> List[Dict]:
    """
    Search ETFGI reports by keyword.

    Args:
        query: Search term (matched against title, region, type, description).
        limit: Max results to return.

    Returns:
        Filtered list of matching report dicts.
    """
    reports = get_etfgi_reports(limit=200)
    query_lower = query.lower()

    matches = []
    for r in reports:
        searchable = f"{r['title']} {r['region']} {r['report_type']} {r['description']}".lower()
        if query_lower in searchable:
            matches.append(r)
            if len(matches) >= limit:
                break

    return matches


def get_global_etf_snapshot() -> Dict:
    """
    Get the latest global ETF industry snapshot from ETFGI report descriptions.

    Returns a dict with the most recent stats found across reports:
    - etf_count: Number of ETFs globally
    - etf_etp_count: Number of ETFs+ETPs globally
    - aum_billion_usd: Total AUM in billions USD
    - providers: Number of ETF providers
    - exchanges: Number of exchanges listing ETFs
    - listings: Total number of listings
    - period: The reporting period
    - source: "ETFGI"
    """
    reports = get_etfgi_reports(limit=50)

    # Find the most recent report with stats (prefer Global scope)
    for r in reports:
        if r["stats"] and ("Global" in r.get("region", "") or "global" in r.get("title", "").lower()):
            return {
                "source": "ETFGI",
                "report_title": r["title"],
                "report_date": r["pub_date"],
                "report_url": r["link"],
                **r["stats"],
            }

    # Fallback: any report with stats
    for r in reports:
        if r["stats"]:
            return {
                "source": "ETFGI",
                "report_title": r["title"],
                "report_date": r["pub_date"],
                "report_url": r["link"],
                **r["stats"],
            }

    return {"source": "ETFGI", "error": "No stats found in recent reports"}


def get_report_regions() -> List[str]:
    """
    Get all available report regions/geographies.

    Returns:
        Sorted list of unique region names found in ETFGI reports.
    """
    reports = get_etfgi_reports(limit=200)
    regions = set()
    for r in reports:
        if r.get("region"):
            regions.add(r["region"])
    return sorted(regions)


def get_report_types() -> List[str]:
    """
    Get all available report types.

    Returns:
        Sorted list of unique report type names.
    """
    reports = get_etfgi_reports(limit=200)
    types = set()
    for r in reports:
        if r.get("report_type"):
            types.add(r["report_type"])
    return sorted(types)


def get_ici_etf_flows() -> Dict:
    """
    Fetch ETF flow data from ICI (Investment Company Institute).

    ICI publishes weekly/monthly ETF and mutual fund flow statistics.
    This scrapes their public statistics page for the latest available data.

    Returns:
        Dict with:
        - source: "ICI"
        - url: Data page URL
        - download_links: Available data file URLs
        - flows: Extracted flow data points
        - page_available: Whether the ICI page responded
        - last_updated: Timestamp of fetch
    """
    cache = _read_cache("ici_flows", max_age_hours=168)  # 7 day cache
    if cache:
        return cache

    try:
        resp = requests.get(ICI_ETF_FLOWS_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        text = resp.text
    except requests.RequestException as e:
        return {
            "source": "ICI",
            "url": ICI_ETF_FLOWS_URL,
            "error": f"Failed to fetch ICI data: {e}",
            "last_updated": datetime.now().isoformat(),
        }

    # Extract data links
    download_links = re.findall(
        r'href="([^"]*(?:\.xls|\.xlsx|\.csv)[^"]*)"', text, re.I
    )

    # Extract flow numbers from page text
    clean_text = _strip_html(text)
    flows = []
    flow_matches = re.findall(
        r'(?:ETF|exchange-traded fund)s?\s+(?:had|saw|recorded|received)\s+'
        r'(?:net\s+)?(?:in|out)flows?\s+of\s+\$?([\d,.]+)\s*(billion|million|Bn|Mn)',
        clean_text, re.I
    )
    for val_str, unit in flow_matches:
        val = float(val_str.replace(",", ""))
        if unit.lower() in ("million", "mn"):
            val /= 1000
        flows.append({"flow_billion_usd": val})

    result = {
        "source": "ICI",
        "url": ICI_ETF_FLOWS_URL,
        "download_links": download_links[:5],
        "flows": flows,
        "page_available": resp.status_code == 200,
        "last_updated": datetime.now().isoformat(),
    }

    _write_cache("ici_flows", result)
    return result


def get_etf_industry_timeline() -> List[Dict]:
    """
    Build a timeline of global ETF industry growth from ETFGI report descriptions.

    Extracts AUM, ETF counts, and other stats from all available report
    descriptions to show industry evolution over time.

    Returns:
        List of dicts sorted by date (newest first), each with:
        - period: e.g., "December 2023"
        - date: ISO date string
        - stats: extracted numeric stats
        - report_title: source report title
    """
    reports = get_etfgi_reports(limit=200)

    timeline = []
    seen_periods = set()

    for r in reports:
        if not r["stats"]:
            continue

        period = r["stats"].get("period", r.get("pub_date", ""))
        if not period or period in seen_periods:
            continue
        seen_periods.add(period)

        timeline.append({
            "period": period,
            "date": r.get("pub_date", ""),
            "stats": r["stats"],
            "report_title": r["title"],
        })

    timeline.sort(key=lambda x: x.get("date", ""), reverse=True)
    return timeline


def fetch_data() -> Dict:
    """
    Main entry point — fetch comprehensive global ETF data.

    Returns:
        Dict with snapshot, recent reports, and ICI flow data.
    """
    return {
        "snapshot": get_global_etf_snapshot(),
        "recent_reports": get_etfgi_reports(limit=5),
        "ici_flows": get_ici_etf_flows(),
        "fetched_at": datetime.now().isoformat(),
    }


def get_latest() -> Dict:
    """
    Get latest data point — alias for fetch_data().

    Returns:
        Dict with the latest global ETF industry data.
    """
    return fetch_data()


if __name__ == "__main__":
    print(json.dumps({
        "module": "etfgi_global_etf_data",
        "status": "active",
        "source": "https://etfgi.com/research",
        "functions": [
            "get_etfgi_reports", "get_research_catalog", "get_report_description",
            "search_reports", "get_global_etf_snapshot",
            "get_report_regions", "get_report_types", "get_ici_etf_flows",
            "get_etf_industry_timeline", "fetch_data", "get_latest"
        ]
    }, indent=2))
