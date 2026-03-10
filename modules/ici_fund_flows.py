#!/usr/bin/env python3
"""
ICI Fund Flows — Weekly & Monthly Mutual Fund Flow Data

Data Source: Investment Company Institute (ICI)
URL: https://www.ici.org/research/stats/flows
Update: Weekly (Wednesday report for prior week)
History: 2+ years of monthly, recent weekly estimates
Free: Yes (public XLS download, no API key required)

Provides:
- Weekly estimated net new cash flows (equity, bond, hybrid)
- Monthly actual net new cash flows
- Breakdown: domestic/world equity, taxable/municipal bonds
- Sub-categories: large/mid/small cap, investment grade, high yield, etc.

Usage as Indicator:
- Persistent equity outflows → risk-off sentiment
- Bond inflows during equity outflows → flight to safety
- Magnitude of flows relative to AUM signals conviction
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import json
import os
import re
import io

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/ici_fund_flows")
os.makedirs(CACHE_DIR, exist_ok=True)

ICI_FLOWS_PAGE = "https://www.ici.org/research/stats/flows"

# Column mapping for the XLS (0-indexed, skipping NaN spacer columns)
# The XLS uses pairs: value in even cols, NaN spacers in odd cols
COLUMN_MAP = {
    0: "date",
    1: "total_long_term",
    3: "total_equity",
    5: "domestic_equity",
    7: "domestic_large_cap",
    9: "domestic_mid_cap",
    11: "domestic_small_cap",
    13: "domestic_multi_cap",
    15: "domestic_other",
    17: "world_equity",
    19: "world_developed",
    21: "world_emerging",
    23: "hybrid",
    25: "total_bond",
    27: "taxable_bond",
    29: "investment_grade",
    31: "high_yield",
    33: "government_bond",
    35: "multisector",
    37: "global_bond",
    39: "municipal_bond",
}


def _get_xls_url() -> str:
    """
    Determine the current year's XLS URL.
    ICI uses pattern: https://www.ici.org/flows_data_YYYY.xls
    with redirects from prior years.
    """
    year = datetime.now().year
    return f"https://www.ici.org/flows_data_{year}.xls"


def _download_xls(force_refresh: bool = False) -> str:
    """
    Download the ICI flows XLS file, with caching (refresh weekly).
    Returns path to local file.
    """
    cache_file = os.path.join(CACHE_DIR, "ici_flows.xls")

    if not force_refresh and os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(days=3):
            return cache_file

    url = _get_xls_url()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
    response.raise_for_status()

    with open(cache_file, "wb") as f:
        f.write(response.content)

    return cache_file


def _parse_xls(file_path: str) -> Dict[str, pd.DataFrame]:
    """
    Parse the ICI XLS into monthly and weekly DataFrames.
    The file has a multi-row header and two data sections:
    - Monthly Net New Cash Flow (rows after 'Monthly Net New Cash Flow')
    - Estimated Weekly Net New Cash Flow (rows after 'Estimated Weekly...')
    """
    df_raw = pd.read_excel(file_path, sheet_name=0, header=None)

    monthly_start = None
    weekly_start = None
    data_end = None

    for i, row in df_raw.iterrows():
        val = str(row[0]).strip() if pd.notna(row[0]) else ""
        if "Monthly Net New Cash Flow" in val:
            monthly_start = i + 1
        elif "Estimated Weekly" in val:
            weekly_start = i + 1
        elif val.startswith("Note:"):
            data_end = i

    result = {}

    for label, start in [("monthly", monthly_start), ("weekly", weekly_start)]:
        if start is None:
            continue

        end = weekly_start - 2 if label == "monthly" and weekly_start else data_end
        if end is None:
            end = len(df_raw)

        section = df_raw.iloc[start:end].copy()
        # Drop rows where date is NaN
        section = section[section[0].notna()].copy()

        # Rename columns using our map
        rename = {}
        for col_idx, col_name in COLUMN_MAP.items():
            if col_idx < section.shape[1]:
                rename[col_idx] = col_name
        section = section.rename(columns=rename)

        # Keep only mapped columns
        keep = [c for c in COLUMN_MAP.values() if c in section.columns]
        section = section[keep].copy()

        # Parse dates
        section["date"] = pd.to_datetime(section["date"], format="mixed", errors="coerce")
        section = section.dropna(subset=["date"])

        # Convert numeric columns
        for col in keep:
            if col != "date":
                section[col] = pd.to_numeric(section[col], errors="coerce")

        section = section.sort_values("date", ascending=False).reset_index(drop=True)
        result[label] = section

    return result


def get_weekly_flows(weeks: int = 5, force_refresh: bool = False) -> List[Dict]:
    """
    Get estimated weekly mutual fund flow data.

    Args:
        weeks: Number of recent weeks to return (default 5)
        force_refresh: Force re-download of XLS data

    Returns:
        List of dicts with weekly flow data (millions USD), most recent first.
        Each dict contains: date, total_long_term, total_equity, domestic_equity,
        world_equity, hybrid, total_bond, taxable_bond, municipal_bond, etc.
    """
    try:
        xls_path = _download_xls(force_refresh=force_refresh)
        data = _parse_xls(xls_path)

        if "weekly" not in data or data["weekly"].empty:
            return [{"error": "No weekly data available in ICI XLS"}]

        df = data["weekly"].head(weeks)
        records = df.to_dict(orient="records")

        # Convert dates to strings for JSON serialization
        for r in records:
            if "date" in r and pd.notna(r["date"]):
                r["date"] = r["date"].strftime("%Y-%m-%d")

        return records

    except Exception as e:
        return [{"error": f"Failed to fetch weekly flows: {str(e)}"}]


def get_monthly_flows(months: int = 12, force_refresh: bool = False) -> List[Dict]:
    """
    Get monthly mutual fund net new cash flow data.

    Args:
        months: Number of recent months to return (default 12)
        force_refresh: Force re-download of XLS data

    Returns:
        List of dicts with monthly flow data (millions USD), most recent first.
    """
    try:
        xls_path = _download_xls(force_refresh=force_refresh)
        data = _parse_xls(xls_path)

        if "monthly" not in data or data["monthly"].empty:
            return [{"error": "No monthly data available in ICI XLS"}]

        df = data["monthly"].head(months)
        records = df.to_dict(orient="records")

        for r in records:
            if "date" in r and pd.notna(r["date"]):
                r["date"] = r["date"].strftime("%Y-%m-%d")

        return records

    except Exception as e:
        return [{"error": f"Failed to fetch monthly flows: {str(e)}"}]


def get_latest_flows(force_refresh: bool = False) -> Dict:
    """
    Get the most recent weekly flow estimate with context.

    Returns:
        Dict with latest weekly flows plus prior week for comparison,
        and a summary of flow direction (risk-on/risk-off signal).
    """
    try:
        weekly = get_weekly_flows(weeks=2, force_refresh=force_refresh)
        if not weekly or "error" in weekly[0]:
            return weekly[0] if weekly else {"error": "No data"}

        latest = weekly[0]
        prior = weekly[1] if len(weekly) > 1 else None

        # Determine sentiment signal
        equity_flow = latest.get("total_equity", 0) or 0
        bond_flow = latest.get("total_bond", 0) or 0

        if equity_flow < -10000 and bond_flow > 5000:
            signal = "strong_risk_off"
        elif equity_flow < 0 and bond_flow > 0:
            signal = "risk_off"
        elif equity_flow > 0 and bond_flow < 0:
            signal = "risk_on"
        elif equity_flow > 10000:
            signal = "strong_risk_on"
        else:
            signal = "neutral"

        result = {
            "latest": latest,
            "prior_week": prior,
            "signal": signal,
            "interpretation": {
                "equity_direction": "outflows" if equity_flow < 0 else "inflows",
                "equity_magnitude_millions": equity_flow,
                "bond_direction": "inflows" if bond_flow > 0 else "outflows",
                "bond_magnitude_millions": bond_flow,
            },
            "source": "Investment Company Institute (ICI)",
            "url": ICI_FLOWS_PAGE,
        }

        return result

    except Exception as e:
        return {"error": f"Failed to get latest flows: {str(e)}"}


def get_flow_trend(weeks: int = 10, category: str = "total_equity",
                   force_refresh: bool = False) -> Dict:
    """
    Analyze flow trend for a specific category over recent weeks.

    Args:
        weeks: Number of weeks to analyze
        category: Column name (total_equity, total_bond, domestic_equity, etc.)
        force_refresh: Force re-download

    Returns:
        Dict with trend analysis: values, average, direction, consecutive weeks.
    """
    try:
        data = get_weekly_flows(weeks=weeks, force_refresh=force_refresh)
        if not data or "error" in data[0]:
            return data[0] if data else {"error": "No data"}

        values = [d.get(category) for d in data if d.get(category) is not None]

        if not values:
            return {"error": f"No data for category '{category}'",
                    "valid_categories": list(COLUMN_MAP.values())}

        avg = sum(values) / len(values)

        # Count consecutive weeks of same direction
        consecutive = 1
        if len(values) >= 2:
            direction = "outflows" if values[0] < 0 else "inflows"
            for v in values[1:]:
                if (direction == "outflows" and v < 0) or \
                   (direction == "inflows" and v >= 0):
                    consecutive += 1
                else:
                    break
        else:
            direction = "outflows" if values[0] < 0 else "inflows"

        return {
            "category": category,
            "weeks_analyzed": len(values),
            "latest_value_millions": values[0],
            "average_millions": round(avg, 1),
            "direction": direction,
            "consecutive_weeks": consecutive,
            "values": [{"date": data[i]["date"], "value": v}
                       for i, v in enumerate(values)],
            "source": "ICI",
        }

    except Exception as e:
        return {"error": f"Failed to analyze trend: {str(e)}"}


def scrape_latest_headline() -> Dict:
    """
    Scrape the latest ICI flows headline from the website.
    Useful as a quick check without downloading the full XLS.

    Returns:
        Dict with headline text, date, and key figures extracted.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(ICI_FLOWS_PAGE, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)

        # Extract key figures from the page text
        result = {
            "source": ICI_FLOWS_PAGE,
            "fetched_at": datetime.now().isoformat(),
        }

        # Find total flow figure
        total_match = re.search(
            r"Total estimated (?:outflows|inflows) from long-term mutual funds.*?"
            r"were \$?([\d,.]+)\s*(billion|million)",
            text, re.IGNORECASE
        )
        if total_match:
            amount = float(total_match.group(1).replace(",", ""))
            unit = total_match.group(2).lower()
            if "outflows" in total_match.group(0).lower():
                amount = -amount
            result["total_flow"] = amount
            result["unit"] = unit

        # Find date
        date_match = re.search(
            r"week ended \w+,\s*(\w+ \d+)", text, re.IGNORECASE
        )
        if date_match:
            result["week_ended"] = date_match.group(1)

        # Find AUM percentage
        pct_match = re.search(
            r"represent[s]?\s+([\d.]+)\s*percent", text, re.IGNORECASE
        )
        if pct_match:
            result["pct_of_assets"] = float(pct_match.group(1))

        return result

    except Exception as e:
        return {"error": f"Failed to scrape headline: {str(e)}"}


if __name__ == "__main__":
    print("=== ICI Fund Flows Module ===")
    print("\n--- Latest Headline ---")
    headline = scrape_latest_headline()
    print(json.dumps(headline, indent=2))

    print("\n--- Latest Flows ---")
    latest = get_latest_flows()
    print(json.dumps(latest, indent=2, default=str))
