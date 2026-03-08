#!/usr/bin/env python3
"""
SEC EDGAR Inline XBRL API — structured financial data extraction from XBRL filings.
Source: https://www.sec.gov/edgar/sec-api-documentation
Endpoints:
  - https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json
  - https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/{taxonomy}/{tag}.json
  - https://data.sec.gov/api/xbrl/frames/{taxonomy}/{tag}/{unit}/{period}.json
Category: Earnings & Fundamentals
Free tier: True
Update frequency: real-time
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional
from requests.exceptions import RequestException

USER_AGENT = "QuantClaw/1.0 (quant@moneyclaw.com)"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
COMPANYCONCEPT_URL = "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/{taxonomy}/{tag}.json"
FRAMES_URL = "https://data.sec.gov/api/xbrl/frames/{taxonomy}/{tag}/{unit}/{period}.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

_cik_cache: Dict[str, str] = {}


def _rate_limit():
    """SEC EDGAR rate limit: 10 req/sec max."""
    time.sleep(0.12)


def _get(url: str, timeout: int = 15) -> Any:
    """Make a GET request with proper User-Agent header."""
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    resp.raise_for_status()
    _rate_limit()
    return resp.json()


def get_cik(ticker: str) -> Optional[str]:
    """
    Resolve ticker symbol to 10-digit CIK string.

    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL')

    Returns:
        10-digit zero-padded CIK string, or None if not found.
    """
    ticker_upper = ticker.upper()
    if ticker_upper in _cik_cache:
        return _cik_cache[ticker_upper]
    try:
        data = _get(TICKERS_URL)
        for entry in data.values():
            if isinstance(entry, dict) and entry.get("ticker") == ticker_upper:
                cik = str(entry["cik_str"]).zfill(10)
                _cik_cache[ticker_upper] = cik
                return cik
        return None
    except RequestException as e:
        raise ValueError(f"Failed to resolve CIK for '{ticker}': {e}")


def _resolve_cik(ticker_or_cik: str) -> str:
    """Resolve a ticker or CIK string to a 10-digit CIK."""
    if ticker_or_cik.isdigit():
        return ticker_or_cik.zfill(10)
    cik = get_cik(ticker_or_cik)
    if not cik:
        raise ValueError(f"Ticker '{ticker_or_cik}' not found in SEC database")
    return cik


def get_company_facts(ticker_or_cik: str) -> Dict[str, Any]:
    """
    Fetch all XBRL facts for a company (revenue, assets, EPS, etc.).

    Args:
        ticker_or_cik: Ticker symbol ('AAPL') or CIK number ('320193')

    Returns:
        Dict with keys: cik, entityName, facts (with us-gaap/dei/ifrs-full taxonomies).
    """
    cik = _resolve_cik(ticker_or_cik)
    url = COMPANYFACTS_URL.format(cik=cik)
    try:
        return _get(url)
    except RequestException as e:
        raise ValueError(f"Failed to fetch company facts for CIK {cik}: {e}")


def get_company_concept(ticker_or_cik: str, tag: str, taxonomy: str = "us-gaap") -> Dict[str, Any]:
    """
    Fetch all filings for a single XBRL concept (e.g. Revenue, Assets).

    Args:
        ticker_or_cik: Ticker symbol or CIK number
        tag: XBRL tag name (e.g. 'Revenues', 'Assets', 'NetIncomeLoss')
        taxonomy: XBRL taxonomy ('us-gaap', 'dei', 'ifrs-full')

    Returns:
        Dict with entityName, tag, taxonomy, units (USD/shares/etc) each containing
        list of filing observations with val, end, fy, fp, form, filed, accn.
    """
    cik = _resolve_cik(ticker_or_cik)
    url = COMPANYCONCEPT_URL.format(cik=cik, taxonomy=taxonomy, tag=tag)
    try:
        return _get(url)
    except RequestException as e:
        raise ValueError(f"Failed to fetch concept '{tag}' for CIK {cik}: {e}")


def get_revenue_history(ticker_or_cik: str) -> List[Dict[str, Any]]:
    """
    Get quarterly/annual revenue history for a company.

    Args:
        ticker_or_cik: Ticker symbol or CIK

    Returns:
        List of dicts with keys: end, val, fy, fp, form, filed.
        Sorted by end date descending.
    """
    tags_to_try = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                   "SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax"]
    for tag in tags_to_try:
        try:
            data = get_company_concept(ticker_or_cik, tag)
            units = data.get("units", {})
            usd_data = units.get("USD", [])
            if usd_data:
                # Filter to 10-K and 10-Q forms for clean data
                filtered = [d for d in usd_data if d.get("form") in ("10-K", "10-Q")]
                if not filtered:
                    filtered = usd_data
                filtered.sort(key=lambda x: x.get("end", ""), reverse=True)
                return filtered[:40]
        except ValueError:
            continue
    return []


def get_net_income_history(ticker_or_cik: str) -> List[Dict[str, Any]]:
    """
    Get quarterly/annual net income history.

    Args:
        ticker_or_cik: Ticker symbol or CIK

    Returns:
        List of dicts with val, end, fy, fp, form, filed. Sorted by end date desc.
    """
    tags_to_try = ["NetIncomeLoss", "ProfitLoss", "NetIncomeLossAvailableToCommonStockholdersBasic"]
    for tag in tags_to_try:
        try:
            data = get_company_concept(ticker_or_cik, tag)
            usd_data = data.get("units", {}).get("USD", [])
            if usd_data:
                filtered = [d for d in usd_data if d.get("form") in ("10-K", "10-Q")]
                if not filtered:
                    filtered = usd_data
                filtered.sort(key=lambda x: x.get("end", ""), reverse=True)
                return filtered[:40]
        except ValueError:
            continue
    return []


def get_eps_history(ticker_or_cik: str) -> List[Dict[str, Any]]:
    """
    Get earnings per share history (basic diluted).

    Args:
        ticker_or_cik: Ticker symbol or CIK

    Returns:
        List of EPS observations with val, end, fy, fp, form, filed.
    """
    tags_to_try = ["EarningsPerShareDiluted", "EarningsPerShareBasic"]
    for tag in tags_to_try:
        try:
            data = get_company_concept(ticker_or_cik, tag)
            usd_data = data.get("units", {}).get("USD/shares", [])
            if usd_data:
                filtered = [d for d in usd_data if d.get("form") in ("10-K", "10-Q")]
                if not filtered:
                    filtered = usd_data
                filtered.sort(key=lambda x: x.get("end", ""), reverse=True)
                return filtered[:40]
        except ValueError:
            continue
    return []


def get_total_assets(ticker_or_cik: str) -> List[Dict[str, Any]]:
    """
    Get total assets history.

    Args:
        ticker_or_cik: Ticker symbol or CIK

    Returns:
        List of asset observations sorted by end date desc.
    """
    try:
        data = get_company_concept(ticker_or_cik, "Assets")
        usd_data = data.get("units", {}).get("USD", [])
        filtered = [d for d in usd_data if d.get("form") in ("10-K", "10-Q")]
        if not filtered:
            filtered = usd_data
        filtered.sort(key=lambda x: x.get("end", ""), reverse=True)
        return filtered[:40]
    except ValueError:
        return []


def get_shares_outstanding(ticker_or_cik: str) -> List[Dict[str, Any]]:
    """
    Get shares outstanding history.

    Args:
        ticker_or_cik: Ticker symbol or CIK

    Returns:
        List of share count observations.
    """
    tags_to_try = ["CommonStockSharesOutstanding", "EntityCommonStockSharesOutstanding"]
    taxonomies = ["us-gaap", "dei"]
    for tag, tax in zip(tags_to_try, taxonomies):
        try:
            data = get_company_concept(ticker_or_cik, tag, taxonomy=tax)
            shares_data = data.get("units", {}).get("shares", [])
            if shares_data:
                shares_data.sort(key=lambda x: x.get("end", ""), reverse=True)
                return shares_data[:40]
        except ValueError:
            continue
    return []


def get_xbrl_frame(tag: str, period: str, taxonomy: str = "us-gaap",
                    unit: str = "USD") -> Dict[str, Any]:
    """
    Fetch an XBRL frame — cross-company data for a single concept/period.
    Useful for screening (e.g. all companies' revenue in Q1 2025).

    Args:
        tag: XBRL tag (e.g. 'Revenues', 'Assets', 'NetIncomeLoss')
        period: Period string like 'CY2024Q4I' (instant) or 'CY2024Q4' (duration)
        taxonomy: 'us-gaap', 'dei', 'ifrs-full'
        unit: 'USD', 'shares', 'pure', 'USD/shares'

    Returns:
        Dict with taxonomy, tag, ccp, uom, data (list of company observations).
    """
    url = FRAMES_URL.format(taxonomy=taxonomy, tag=tag, unit=unit, period=period)
    try:
        return _get(url)
    except RequestException as e:
        raise ValueError(f"Failed to fetch XBRL frame {taxonomy}/{tag}/{unit}/{period}: {e}")


def get_available_concepts(ticker_or_cik: str, taxonomy: str = "us-gaap",
                           limit: int = 50) -> List[str]:
    """
    List available XBRL concept tags for a company.

    Args:
        ticker_or_cik: Ticker or CIK
        taxonomy: 'us-gaap', 'dei', 'ifrs-full'
        limit: Max number of concept names to return

    Returns:
        List of XBRL tag names available for this company.
    """
    facts = get_company_facts(ticker_or_cik)
    tax_facts = facts.get("facts", {}).get(taxonomy, {})
    return list(tax_facts.keys())[:limit]


def get_financial_summary(ticker_or_cik: str) -> Dict[str, Any]:
    """
    Build a financial summary with latest revenue, net income, EPS, assets, shares.

    Args:
        ticker_or_cik: Ticker or CIK

    Returns:
        Dict with entityName, cik, latest values for key financial metrics.
    """
    cik = _resolve_cik(ticker_or_cik)
    try:
        facts_raw = get_company_facts(ticker_or_cik)
        entity_name = facts_raw.get("entityName", "Unknown")
    except ValueError:
        entity_name = "Unknown"

    summary = {"entityName": entity_name, "cik": cik, "metrics": {}}

    rev = get_revenue_history(ticker_or_cik)
    if rev:
        latest = rev[0]
        summary["metrics"]["revenue"] = {
            "value": latest.get("val"), "period_end": latest.get("end"),
            "form": latest.get("form"), "fiscal_year": latest.get("fy")
        }

    ni = get_net_income_history(ticker_or_cik)
    if ni:
        latest = ni[0]
        summary["metrics"]["net_income"] = {
            "value": latest.get("val"), "period_end": latest.get("end"),
            "form": latest.get("form"), "fiscal_year": latest.get("fy")
        }

    eps = get_eps_history(ticker_or_cik)
    if eps:
        latest = eps[0]
        summary["metrics"]["eps_diluted"] = {
            "value": latest.get("val"), "period_end": latest.get("end"),
            "form": latest.get("form"), "fiscal_year": latest.get("fy")
        }

    assets = get_total_assets(ticker_or_cik)
    if assets:
        latest = assets[0]
        summary["metrics"]["total_assets"] = {
            "value": latest.get("val"), "period_end": latest.get("end"),
            "form": latest.get("form"), "fiscal_year": latest.get("fy")
        }

    shares = get_shares_outstanding(ticker_or_cik)
    if shares:
        latest = shares[0]
        summary["metrics"]["shares_outstanding"] = {
            "value": latest.get("val"), "period_end": latest.get("end"),
            "form": latest.get("form")
        }

    return summary


def get_company_info(ticker_or_cik: str) -> Dict[str, Any]:
    """
    Get company metadata from submissions endpoint.

    Args:
        ticker_or_cik: Ticker or CIK

    Returns:
        Dict with name, cik, tickers, exchanges, sic, sicDescription,
        category, fiscalYearEnd, stateOfIncorporation, website.
    """
    cik = _resolve_cik(ticker_or_cik)
    url = SUBMISSIONS_URL.format(cik=cik)
    try:
        data = _get(url)
        return {
            "name": data.get("name"),
            "cik": data.get("cik"),
            "tickers": data.get("tickers", []),
            "exchanges": data.get("exchanges", []),
            "sic": data.get("sic"),
            "sicDescription": data.get("sicDescription"),
            "category": data.get("category"),
            "fiscalYearEnd": data.get("fiscalYearEnd"),
            "stateOfIncorporation": data.get("stateOfIncorporation"),
            "website": data.get("website"),
            "entityType": data.get("entityType"),
        }
    except RequestException as e:
        raise ValueError(f"Failed to fetch company info for CIK {cik}: {e}")


if __name__ == "__main__":
    print(json.dumps({"module": "sec_edgar_inline_xbrl_api", "status": "ready",
                       "source": "https://www.sec.gov/edgar/sec-api-documentation"}, indent=2))
