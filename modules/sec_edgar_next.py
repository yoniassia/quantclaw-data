#!/usr/bin/env python3
"""sec_edgar_next — SEC EDGAR Next-Gen XBRL API. Source: https://data.sec.gov/api/xbrl/. Free, no auth. Rate limit: 10 req/sec."""
import requests
import os
import time
import json
from datetime import datetime

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)
HEADERS = {"User-Agent": "QuantClaw/1.0 quant@quantclaw.org", "Accept": "application/json"}
BASE = "https://data.sec.gov"

def _ticker_to_cik(ticker):
    """Resolve ticker to zero-padded CIK."""
    cache = os.path.join(CACHE_DIR, "sec_tickers.json")
    if os.path.exists(cache) and (time.time() - os.path.getmtime(cache)) < 86400 * 7:
        with open(cache) as f:
            mapping = json.load(f)
    else:
        resp = requests.get("https://www.sec.gov/files/company_tickers.json", headers=HEADERS, timeout=15)
        resp.raise_for_status()
        raw = resp.json()
        mapping = {v["ticker"].upper(): str(v["cik_str"]).zfill(10) for v in raw.values()}
        with open(cache, "w") as f:
            json.dump(mapping, f)
    cik = mapping.get(ticker.upper())
    if not cik:
        raise ValueError(f"Ticker {ticker} not found in SEC EDGAR")
    return cik

def get_company_financials(ticker, **kwargs):
    """Fetch all XBRL company facts (revenue, net income, assets, etc.)."""
    cik = _ticker_to_cik(ticker)
    cache_file = os.path.join(CACHE_DIR, f"sec_edgar_{ticker.upper()}.json")
    if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < 86400:
        with open(cache_file) as f:
            return json.load(f)
    try:
        url = f"{BASE}/api/xbrl/companyfacts/CIK{cik}.json"
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        result = {"ticker": ticker.upper(), "cik": cik, "entity": data.get("entityName", ""),
                  "facts": {}, "fetch_time": datetime.now().isoformat()}
        us_gaap = data.get("facts", {}).get("us-gaap", {})
        key_metrics = ["Revenues", "NetIncomeLoss", "Assets", "Liabilities",
                       "StockholdersEquity", "EarningsPerShareBasic", "EarningsPerShareDiluted",
                       "OperatingIncomeLoss", "GrossProfit", "CashAndCashEquivalentsAtCarryingValue"]
        for metric in key_metrics:
            if metric in us_gaap:
                units = us_gaap[metric].get("units", {})
                for unit_type, entries in units.items():
                    recent = sorted(entries, key=lambda x: x.get("end", ""), reverse=True)[:20]
                    result["facts"][metric] = [{"end": e.get("end"), "val": e.get("val"),
                                                 "form": e.get("form"), "fy": e.get("fy"),
                                                 "fp": e.get("fp")} for e in recent]
                    break
        with open(cache_file, "w") as f:
            json.dump(result, f, indent=2)
        return result
    except Exception as e:
        return {"error": str(e), "ticker": ticker}

def get_filing_history(ticker, form_type="10-K", **kwargs):
    """Fetch recent filing history for a ticker."""
    cik = _ticker_to_cik(ticker)
    try:
        url = f"{BASE}/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={form_type}&dateb=&owner=include&count=20&search_text=&action=getcompany&output=atom"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        import xml.etree.ElementTree as ET
        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        filings = []
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns)
            updated = entry.find("atom:updated", ns)
            link = entry.find("atom:link", ns)
            filings.append({"title": title.text if title is not None else "",
                            "date": updated.text if updated is not None else "",
                            "url": link.get("href", "") if link is not None else ""})
        return {"ticker": ticker.upper(), "form_type": form_type, "filings": filings,
                "fetch_time": datetime.now().isoformat()}
    except Exception as e:
        return {"error": str(e), "ticker": ticker}

def get_data(ticker="AAPL", **kwargs):
    """Default entry point — returns company financials."""
    return get_company_financials(ticker, **kwargs)

if __name__ == "__main__":
    import sys
    t = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = get_company_financials(t)
    if "error" not in result:
        print(f"Entity: {result['entity']}")
        print(f"Metrics available: {list(result['facts'].keys())}")
        for k, v in list(result['facts'].items())[:3]:
            print(f"  {k}: {v[0]['val']} ({v[0]['end']})")
    else:
        print(f"Error: {result['error']}")
