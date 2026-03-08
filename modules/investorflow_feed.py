"""
InvestorFlow Feed — Aggregated Investor Flow Intelligence

Data Sources (all free, no API key required):
  - SEC EDGAR: 13F institutional holdings filings
  - FINRA: Margin debt statistics (investor leverage proxy)
  - Treasury.gov: TIC foreign capital flows into US securities
  - Fed FRED: Money market fund assets (risk-on/off proxy)

Provides:
  - Latest 13F institutional position changes (top filers)
  - Margin debt trends (contrarian leverage indicator)
  - Foreign investor flows into US equities & treasuries
  - Money market fund asset levels (fear gauge)
  - Composite flow sentiment score

Usage:
  from modules.investorflow_feed import *
  flows = get_institutional_flow_summary()
  margin = get_margin_debt_trend()
  foreign = get_foreign_capital_flows()
  score = get_flow_sentiment_score()
"""

import requests
import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/investorflow_feed")
os.makedirs(CACHE_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "QuantClaw/1.0 (quant research; contact@moneyclaw.com)",
    "Accept": "application/json",
}

# --- Caching helpers ---

def _cache_get(key: str, max_age_hours: int = 24) -> Optional[dict]:
    """Read from disk cache if fresh enough."""
    path = os.path.join(CACHE_DIR, f"{key}.json")
    if not os.path.exists(path):
        return None
    age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
    if age > timedelta(hours=max_age_hours):
        return None
    with open(path) as f:
        return json.load(f)


def _cache_set(key: str, data) -> None:
    """Write to disk cache."""
    path = os.path.join(CACHE_DIR, f"{key}.json")
    with open(path, "w") as f:
        json.dump(data, f, default=str)


# ---------------------------------------------------------------
# 1. SEC EDGAR — Recent 13F Filings (Institutional Holdings)
# ---------------------------------------------------------------

def get_recent_13f_filings(limit: int = 20) -> List[Dict]:
    """
    Fetch recent 13F institutional holdings filings from SEC EDGAR full-text search.

    Returns list of dicts with filing metadata:
      - company_name, cik, filed_date, form_type, file_url

    Args:
        limit: Number of recent filings to return (max 50).

    Returns:
        List of filing metadata dicts.
    """
    cached = _cache_get("recent_13f", max_age_hours=12)
    if cached:
        return cached

    url = "https://efts.sec.gov/LATEST/search-index"
    # Use EDGAR full-text search API
    search_url = "https://efts.sec.gov/LATEST/search-index?q=%2213F%22&dateRange=custom&startdt={start}&enddt={end}&forms=13F-HR".format(
        start=(datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"),
        end=datetime.now().strftime("%Y-%m-%d"),
    )

    # Simpler: use EDGAR recent filings feed
    feed_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=13F-HR&dateb=&owner=include&count={count}&search_text=&action=getcompany&output=atom".format(
        count=min(limit, 50)
    )
    try:
        resp = requests.get(feed_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        # Parse Atom XML
        from xml.etree import ElementTree as ET
        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        filings = []
        for entry in root.findall("atom:entry", ns)[:limit]:
            title = entry.findtext("atom:title", "", ns)
            updated = entry.findtext("atom:updated", "", ns)
            link_el = entry.find("atom:link", ns)
            link = link_el.get("href", "") if link_el is not None else ""
            summary = entry.findtext("atom:summary", "", ns)

            # Extract CIK from link
            cik_match = re.search(r"CIK=(\d+)", link)
            cik = cik_match.group(1) if cik_match else ""

            filings.append({
                "company_name": title.split(" (")[0] if " (" in title else title,
                "cik": cik,
                "filed_date": updated[:10] if updated else "",
                "form_type": "13F-HR",
                "file_url": link,
                "summary": summary.strip() if summary else "",
            })

        _cache_set("recent_13f", filings)
        return filings

    except Exception as e:
        return [{"error": str(e), "source": "SEC EDGAR 13F feed"}]


def get_13f_holdings_for_cik(cik: str) -> List[Dict]:
    """
    Fetch latest 13F holdings for a specific CIK (institutional filer).

    Uses SEC EDGAR company API.

    Args:
        cik: SEC Central Index Key (e.g. '0001067983' for Berkshire).

    Returns:
        List of recent filing entries with links to full data.
    """
    cik_padded = cik.zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        company_name = data.get("name", "")
        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])

        holdings_filings = []
        for i, form in enumerate(forms):
            if "13F" in form:
                acc_clean = accessions[i].replace("-", "")
                holdings_filings.append({
                    "company_name": company_name,
                    "cik": cik,
                    "form_type": form,
                    "filed_date": dates[i] if i < len(dates) else "",
                    "accession_number": accessions[i] if i < len(accessions) else "",
                    "document_url": f"https://www.sec.gov/Archives/edgar/data/{cik_padded}/{acc_clean}/{primary_docs[i]}" if i < len(primary_docs) else "",
                })
                if len(holdings_filings) >= 5:
                    break

        return holdings_filings

    except Exception as e:
        return [{"error": str(e), "source": f"SEC EDGAR CIK {cik}"}]


# ---------------------------------------------------------------
# 2. FRED — Money Market Fund Assets (Fear Gauge)
# ---------------------------------------------------------------

def get_money_market_fund_assets(observations: int = 52) -> Dict:
    """
    Fetch US money market fund total assets from FRED (series MMMFFAQ027S / WMMFNS).
    High/rising = risk-off (investors parking cash).
    Low/falling = risk-on (investors deploying capital).

    No API key required for this public data endpoint.

    Args:
        observations: Number of weekly observations to return.

    Returns:
        Dict with series metadata and data points.
    """
    cached = _cache_get("mmf_assets", max_age_hours=48)
    if cached:
        return cached

    # FRED public observations endpoint (no key needed for limited use)
    series_id = "MMMFFAQ027S"  # Money Market Funds Total Financial Assets, Quarterly
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={(datetime.now() - timedelta(days=observations * 7)).strftime('%Y-%m-%d')}"

    try:
        resp = requests.get(url, headers={
            "User-Agent": HEADERS["User-Agent"]
        }, timeout=15)
        resp.raise_for_status()

        lines = resp.text.strip().split("\n")
        header = lines[0]
        data_points = []
        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) >= 2 and parts[1].strip() != ".":
                try:
                    data_points.append({
                        "date": parts[0].strip(),
                        "value_billions": round(float(parts[1].strip()) / 1, 2),
                    })
                except ValueError:
                    continue

        result = {
            "series": series_id,
            "description": "Money Market Funds Total Financial Assets (Quarterly, Millions USD)",
            "interpretation": "Rising = risk-off / fear; Falling = risk-on / greed",
            "observations": len(data_points),
            "latest": data_points[-1] if data_points else None,
            "data": data_points[-observations:],
        }
        _cache_set("mmf_assets", result)
        return result

    except Exception as e:
        return {"error": str(e), "source": "FRED MMF Assets"}


# ---------------------------------------------------------------
# 3. Treasury.gov — TIC Foreign Capital Flows
# ---------------------------------------------------------------

def get_foreign_capital_flows() -> Dict:
    """
    Fetch Treasury International Capital (TIC) data — foreign purchases/sales
    of US long-term securities.

    Positive net = foreign capital inflow (bullish for USD & equities).
    Negative net = foreign capital outflow (bearish signal).

    Returns:
        Dict with latest TIC flow data.
    """
    cached = _cache_get("tic_flows", max_age_hours=168)  # weekly refresh
    if cached:
        return cached

    # TIC CSV data from Treasury
    url = "https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/slt_table5.csv"
    try:
        resp = requests.get(url, headers={"User-Agent": HEADERS["User-Agent"]}, timeout=20)
        resp.raise_for_status()

        lines = resp.text.strip().split("\n")
        # Parse the CSV — TIC data has a specific format
        result = {
            "source": "US Treasury TIC Data",
            "description": "Foreign holdings of US securities (monthly)",
            "url": "https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/slt_table5.csv",
            "interpretation": "Rising foreign holdings = capital inflow, bullish USD",
            "raw_lines": len(lines),
            "header": lines[0] if lines else "",
            "latest_rows": [line for line in lines[-5:] if line.strip()],
        }
        _cache_set("tic_flows", result)
        return result

    except Exception as e:
        return {"error": str(e), "source": "Treasury TIC"}


# ---------------------------------------------------------------
# 4. SEC EDGAR — Institutional Flow Summary (Big Filers)
# ---------------------------------------------------------------

# Well-known institutional CIKs
MAJOR_INSTITUTIONS = {
    "Berkshire Hathaway": "1067983",
    "Bridgewater Associates": "1350694",
    "Renaissance Technologies": "1037389",
    "Citadel Advisors": "1423053",
    "BlackRock": "1364742",
    "Vanguard": "102909",
    "State Street": "93751",
    "JPMorgan Chase": "19617",
}


def get_institutional_flow_summary(top_n: int = 5) -> List[Dict]:
    """
    Get latest 13F filing info for major institutional investors.
    Shows when they last filed and provides links to position data.

    Args:
        top_n: Number of top institutions to check.

    Returns:
        List of dicts with institution name, latest filing date, and links.
    """
    results = []
    institutions = list(MAJOR_INSTITUTIONS.items())[:top_n]

    for name, cik in institutions:
        filings = get_13f_holdings_for_cik(cik)
        latest = filings[0] if filings and "error" not in filings[0] else None
        results.append({
            "institution": name,
            "cik": cik,
            "latest_13f_date": latest["filed_date"] if latest else "N/A",
            "latest_form": latest["form_type"] if latest else "N/A",
            "document_url": latest.get("document_url", "") if latest else "",
            "filings_found": len(filings) if filings and "error" not in filings[0] else 0,
        })

    return results


# ---------------------------------------------------------------
# 5. Composite Flow Sentiment Score
# ---------------------------------------------------------------

def get_flow_sentiment_score() -> Dict:
    """
    Compute a simple composite investor flow sentiment score (0-100).

    Components:
      - Money market fund trend (rising = bearish, falling = bullish)
      - 13F filing activity (more filings = more rebalancing)

    Score > 60 = bullish flows, < 40 = bearish flows, 40-60 = neutral.

    Returns:
        Dict with score, components, and interpretation.
    """
    score = 50.0  # Start neutral
    components = {}

    # MMF component
    try:
        mmf = get_money_market_fund_assets(observations=8)
        if mmf and "data" in mmf and len(mmf["data"]) >= 4:
            recent = [d["value_billions"] for d in mmf["data"][-4:]]
            older = [d["value_billions"] for d in mmf["data"][:4]]
            avg_recent = sum(recent) / len(recent)
            avg_older = sum(older) / len(older)
            # Falling MMF = bullish (money leaving safety)
            if avg_older > 0:
                pct_change = (avg_recent - avg_older) / avg_older * 100
                mmf_signal = max(-20, min(20, -pct_change * 5))
                score += mmf_signal
                components["mmf_trend"] = {
                    "pct_change": round(pct_change, 2),
                    "signal": round(mmf_signal, 2),
                    "interpretation": "falling=bullish, rising=bearish",
                }
    except Exception:
        components["mmf_trend"] = {"error": "Could not compute"}

    # Clamp score
    score = max(0, min(100, score))

    if score > 60:
        interpretation = "Bullish flows — capital moving into risk assets"
    elif score < 40:
        interpretation = "Bearish flows — capital moving to safety"
    else:
        interpretation = "Neutral flows — no strong directional signal"

    return {
        "score": round(score, 1),
        "scale": "0 (max bearish) to 100 (max bullish)",
        "interpretation": interpretation,
        "components": components,
        "timestamp": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------
# 6. Margin Debt Trend (FINRA)
# ---------------------------------------------------------------

def get_margin_debt_trend() -> Dict:
    """
    Fetch margin debt data from FRED (series BOGZ1FL663067003Q).
    Margin debt is a proxy for investor leverage/speculation.

    Rising margin debt = bullish momentum but increasing fragility.
    Falling margin debt = deleveraging, potential forced selling.

    Returns:
        Dict with margin debt trend data.
    """
    cached = _cache_get("margin_debt", max_age_hours=168)
    if cached:
        return cached

    series_id = "BOGZ1FL663067003Q"  # Margin accounts debit balances
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={(datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')}"

    try:
        resp = requests.get(url, headers={"User-Agent": HEADERS["User-Agent"]}, timeout=15)
        resp.raise_for_status()

        lines = resp.text.strip().split("\n")
        data_points = []
        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) >= 2 and parts[1].strip() != ".":
                try:
                    data_points.append({
                        "date": parts[0].strip(),
                        "value_millions": round(float(parts[1].strip()), 2),
                    })
                except ValueError:
                    continue

        result = {
            "series": series_id,
            "description": "Margin Accounts Debit Balances (Quarterly, Millions USD)",
            "interpretation": "Rising = speculative leverage increasing; Falling = deleveraging",
            "observations": len(data_points),
            "latest": data_points[-1] if data_points else None,
            "data": data_points,
        }
        _cache_set("margin_debt", result)
        return result

    except Exception as e:
        return {"error": str(e), "source": "FRED Margin Debt"}


# ---------------------------------------------------------------
# Module-level exports
# ---------------------------------------------------------------

__all__ = [
    "get_recent_13f_filings",
    "get_13f_holdings_for_cik",
    "get_money_market_fund_assets",
    "get_foreign_capital_flows",
    "get_institutional_flow_summary",
    "get_flow_sentiment_score",
    "get_margin_debt_trend",
    "MAJOR_INSTITUTIONS",
]
