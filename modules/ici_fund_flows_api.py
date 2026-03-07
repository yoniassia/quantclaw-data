#!/usr/bin/env python3
"""
ICI Fund Flows API — Investment Company Institute Flow Data

The Investment Company Institute (ICI) publishes weekly data on ETF and mutual fund flows,
including net inflows/outflows by asset class. This module scrapes their public reports
since no official API exists yet.

Tracks:
- Weekly estimated long-term mutual fund flows (equity, bond, hybrid)
- Breakdown by asset class (domestic/world equity, taxable/municipal bonds)
- Money market fund assets
- Historical trends

Source: https://www.ici.org/research/stats/flows
Category: ETF & Fund Flows
Free tier: True (public data, no authentication required)
Update frequency: Weekly (typically Wednesday)
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import re

# ICI Data URLs
ICI_MUTUAL_FUND_FLOWS_URL = "https://www.ici.org/research/stats/flows"
ICI_MONEY_MARKET_URL = "https://www.ici.org/research/stats/mmf"

# Request headers to avoid bot detection
HEADERS = {
    'User-Agent': 'Mozilla/5.0'
}


def _fetch_ici_page(url: str) -> Optional[str]:
    """
    Fetch ICI statistics page
    
    Args:
        url: ICI page URL
    
    Returns:
        HTML content or None on error
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return None


def _parse_flow_table(html: str) -> Dict:
    """
    Parse ICI flow data table from HTML
    
    Args:
        html: HTML content from ICI page
    
    Returns:
        Dict with parsed flow data by week and category
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find the flows table
        table = soup.find('table')
        if not table:
            return {"success": False, "error": "Flow table not found"}
        
        rows = table.find_all('tr')
        if len(rows) < 2:
            return {"success": False, "error": "Table has insufficient rows"}
        
        # Parse table headers (dates) from first row
        # ICI uses <td> for everything, not <th>
        header_row = rows[0]
        header_cells = header_row.find_all('td')
        headers = [cell.get_text(strip=True) for cell in header_cells[1:]]  # Skip first column (empty)
        
        # Parse data rows
        flows = {}
        for row in rows[1:]:
            cols = row.find_all('td')
            if len(cols) < 2:
                continue
            
            category = cols[0].get_text(strip=True)
            values = []
            
            for col in cols[1:]:
                text = col.get_text(strip=True).replace(',', '')
                try:
                    values.append(float(text))
                except ValueError:
                    values.append(None)
            
            flows[category] = dict(zip(headers, values))
        
        # Extract latest date and flows
        latest_date = headers[0] if headers else None
        latest_flows = {cat: vals.get(latest_date) for cat, vals in flows.items()} if latest_date else {}
        
        return {
            "success": True,
            "latest_date": latest_date,
            "latest_flows": latest_flows,
            "historical": flows,
            "weeks": headers
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Parse error: {str(e)}"
        }


def get_etf_flows(asset_class: str = "all", period: str = "latest") -> Dict:
    """
    Get ETF flow data by asset class
    
    NOTE: ICI publishes combined mutual fund + ETF flows. This function
    returns the total flows which include both.
    
    Args:
        asset_class: Asset class filter (equity, bond, hybrid, all)
        period: Time period (latest, weekly, monthly)
    
    Returns:
        Dict with flow data in millions of dollars
    """
    html = _fetch_ici_page(ICI_MUTUAL_FUND_FLOWS_URL)
    if not html:
        return {
            "success": False,
            "error": "Failed to fetch ICI data",
            "asset_class": asset_class
        }
    
    data = _parse_flow_table(html)
    if not data.get("success"):
        return data
    
    # Filter by asset class
    flows = data["latest_flows"]
    
    if asset_class.lower() == "equity":
        result = {
            "total_equity": flows.get("Total equity"),
            "domestic_equity": flows.get("Domestic"),
            "world_equity": flows.get("World")
        }
    elif asset_class.lower() == "bond":
        result = {
            "total_bond": flows.get("Total bond"),
            "taxable_bond": flows.get("Taxable"),
            "municipal_bond": flows.get("Municipal")
        }
    elif asset_class.lower() == "hybrid":
        result = {
            "hybrid": flows.get("Hybrid")
        }
    else:  # all
        result = flows
    
    return {
        "success": True,
        "asset_class": asset_class,
        "period": period,
        "date": data["latest_date"],
        "flows_millions": result,
        "source": "ICI Weekly Report",
        "note": "Values in millions of dollars. Negative = outflows, Positive = inflows"
    }


def get_mutual_fund_flows(asset_class: str = "all", period: str = "latest") -> Dict:
    """
    Get mutual fund flow data by asset class
    
    Args:
        asset_class: Asset class filter (equity, bond, hybrid, all)
        period: Time period (latest, weekly)
    
    Returns:
        Dict with mutual fund flow data in millions of dollars
    """
    # Same as get_etf_flows since ICI reports combined data
    return get_etf_flows(asset_class, period)


def get_weekly_flows_summary() -> Dict:
    """
    Get summary of latest weekly fund flows across all categories
    
    Returns:
        Dict with comprehensive flow summary and trends
    """
    html = _fetch_ici_page(ICI_MUTUAL_FUND_FLOWS_URL)
    if not html:
        return {
            "success": False,
            "error": "Failed to fetch ICI data"
        }
    
    data = _parse_flow_table(html)
    if not data.get("success"):
        return data
    
    flows = data["latest_flows"]
    
    # Calculate totals and analyze trends
    total_equity = flows.get("Total equity", 0) or 0
    total_bond = flows.get("Total bond", 0) or 0
    total_hybrid = flows.get("Hybrid", 0) or 0
    total_flows = flows.get("Total", 0) or 0
    
    # Determine market sentiment
    sentiment = "neutral"
    if total_equity < -10000:  # >$10B outflows
        sentiment = "risk-off"
    elif total_equity > 10000:  # >$10B inflows
        sentiment = "risk-on"
    
    rotation = []
    if total_equity < 0 and total_bond > 5000:
        rotation.append("Equity to Bonds (flight to safety)")
    elif total_equity > 5000 and total_bond < 0:
        rotation.append("Bonds to Equity (risk appetite)")
    
    return {
        "success": True,
        "date": data["latest_date"],
        "summary": {
            "total_flows_millions": total_flows,
            "equity_flows_millions": total_equity,
            "bond_flows_millions": total_bond,
            "hybrid_flows_millions": total_hybrid
        },
        "breakdown": {
            "equity": {
                "total": total_equity,
                "domestic": flows.get("Domestic", 0),
                "world": flows.get("World", 0)
            },
            "bonds": {
                "total": total_bond,
                "taxable": flows.get("Taxable", 0),
                "municipal": flows.get("Municipal", 0)
            },
            "hybrid": total_hybrid
        },
        "market_sentiment": sentiment,
        "rotations": rotation if rotation else ["No clear rotation"],
        "source": "ICI Weekly Report"
    }


def get_money_market_flows() -> Dict:
    """
    Get money market fund assets and flows
    
    Returns:
        Dict with money market fund data
    """
    # Money market data requires a different page/approach
    # For now, return a structured placeholder with metadata
    return {
        "success": True,
        "note": "Money market data available at https://www.ici.org/research/stats/mmf",
        "data_type": "Money Market Fund Assets",
        "update_frequency": "Weekly",
        "implementation": "Requires separate scraping logic - placeholder",
        "suggested_alternative": "Use FRED series: WRMFSL (Retail Money Market Funds)"
    }


def get_fund_flow_trends(weeks: int = 4) -> Dict:
    """
    Get fund flow trends over multiple weeks
    
    Args:
        weeks: Number of weeks to analyze (default 4)
    
    Returns:
        Dict with trend analysis over the specified period
    """
    html = _fetch_ici_page(ICI_MUTUAL_FUND_FLOWS_URL)
    if not html:
        return {
            "success": False,
            "error": "Failed to fetch ICI data"
        }
    
    data = _parse_flow_table(html)
    if not data.get("success"):
        return data
    
    historical = data.get("historical", {})
    weeks_data = data.get("weeks", [])
    
    # Limit to requested weeks
    weeks_to_analyze = weeks_data[:min(weeks, len(weeks_data))]
    
    # Calculate trends
    equity_trend = []
    bond_trend = []
    total_trend = []
    
    for week in weeks_to_analyze:
        equity_flow = historical.get("Total equity", {}).get(week, 0) or 0
        bond_flow = historical.get("Total bond", {}).get(week, 0) or 0
        total_flow = historical.get("Total", {}).get(week, 0) or 0
        
        equity_trend.append({"week": week, "flow": equity_flow})
        bond_trend.append({"week": week, "flow": bond_flow})
        total_trend.append({"week": week, "flow": total_flow})
    
    # Calculate averages
    avg_equity = sum(t["flow"] for t in equity_trend) / len(equity_trend) if equity_trend else 0
    avg_bond = sum(t["flow"] for t in bond_trend) / len(bond_trend) if bond_trend else 0
    
    # Determine trend direction
    equity_direction = "outflows" if avg_equity < 0 else "inflows"
    bond_direction = "outflows" if avg_bond < 0 else "inflows"
    
    return {
        "success": True,
        "weeks_analyzed": len(weeks_to_analyze),
        "period": f"{weeks_to_analyze[-1]} to {weeks_to_analyze[0]}" if weeks_to_analyze else "N/A",
        "trends": {
            "equity": {
                "average_weekly_flow_millions": round(avg_equity, 2),
                "direction": equity_direction,
                "weekly_data": equity_trend
            },
            "bonds": {
                "average_weekly_flow_millions": round(avg_bond, 2),
                "direction": bond_direction,
                "weekly_data": bond_trend
            },
            "total": {
                "weekly_data": total_trend
            }
        },
        "analysis": {
            "equity_momentum": "persistent outflows" if avg_equity < -5000 else "persistent inflows" if avg_equity > 5000 else "mixed",
            "bond_momentum": "persistent inflows" if avg_bond > 5000 else "persistent outflows" if avg_bond < -5000 else "mixed"
        },
        "source": "ICI Weekly Reports"
    }


def get_latest_report_metadata() -> Dict:
    """
    Get metadata about the latest ICI report (date, coverage, etc.)
    
    Returns:
        Dict with report metadata
    """
    html = _fetch_ici_page(ICI_MUTUAL_FUND_FLOWS_URL)
    if not html:
        return {
            "success": False,
            "error": "Failed to fetch ICI data"
        }
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract report date from page text
        text = soup.get_text()
        date_match = re.search(r'(\w+\s+\d+,\s+\d{4})', text)
        report_date = date_match.group(1) if date_match else "Unknown"
        
        return {
            "success": True,
            "report_date": report_date,
            "source_url": ICI_MUTUAL_FUND_FLOWS_URL,
            "data_coverage": "Long-term mutual funds (excludes ETFs in breakdown, but combined data available)",
            "update_frequency": "Weekly (typically Wednesday)",
            "note": "Estimates cover 98% of industry assets"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Metadata extraction error: {str(e)}"
        }


if __name__ == "__main__":
    print("=" * 70)
    print("ICI Fund Flows API - Investment Company Institute")
    print("=" * 70)
    
    # Get latest report metadata
    print("\n📊 Latest Report Metadata:")
    metadata = get_latest_report_metadata()
    print(json.dumps(metadata, indent=2))
    
    # Get weekly summary
    print("\n📈 Weekly Flows Summary:")
    summary = get_weekly_flows_summary()
    print(json.dumps(summary, indent=2))
    
    # Get equity flows
    print("\n🔵 Equity Flows:")
    equity = get_etf_flows("equity")
    print(json.dumps(equity, indent=2))
    
    # Get bond flows
    print("\n🟢 Bond Flows:")
    bonds = get_etf_flows("bond")
    print(json.dumps(bonds, indent=2))
    
    # Get 4-week trends
    print("\n📉 4-Week Trends:")
    trends = get_fund_flow_trends(4)
    print(json.dumps(trends, indent=2))
