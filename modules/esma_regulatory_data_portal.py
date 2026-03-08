#!/usr/bin/env python3
"""
ESMA Regulatory Data Portal — QuantClaw Data Module
Access European Securities and Markets Authority public registers via Solr API.

Covers:
  - FIRDS (Financial Instruments Reference Data System) — 255M+ instruments
  - Investment Firms Register (MiFID II authorized entities)

Source: https://registers.esma.europa.eu
Category: Government & Regulatory
Free tier: Yes — public Solr endpoints, no API key needed
Update frequency: Daily
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional


BASE_URL = "https://registers.esma.europa.eu/solr"
FIRDS_CORE = "esma_registers_firds"
UPREG_CORE = "esma_registers_upreg"
TIMEOUT = 30


def _solr_query(core: str, params: dict) -> dict:
    """Execute a Solr query against an ESMA register core."""
    url = f"{BASE_URL}/{core}/select"
    params.setdefault("wt", "json")
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        return {"error": "Request timed out", "core": core}
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "core": core}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response", "core": core}


# ─── FIRDS: Financial Instruments ───────────────────────────────────────


def search_instruments(query: str, rows: int = 10) -> List[Dict]:
    """
    Search ESMA FIRDS for financial instruments by free-text query.

    Args:
        query: Search term (ISIN, instrument name, etc.)
        rows: Number of results (max 100)

    Returns:
        List of instrument dicts with ISIN, name, MIC, status, etc.
    """
    rows = min(rows, 100)
    data = _solr_query(FIRDS_CORE, {
        "q": query,
        "rows": str(rows),
        "fl": "isin,gnr_full_name,gnr_short_name,gnr_cfi_code,mic,rca_mic,status,status_label,"
              "gnr_notional_curr_code,lei,mrkt_trdng_start_date,mrkt_trdng_trmination_date,"
              "drv_expiry_date,drv_option_type,drv_underlng_isin,publication_date",
    })
    if "error" in data:
        return [data]
    docs = data.get("response", {}).get("docs", [])
    return [_clean_instrument(d) for d in docs]


def lookup_isin(isin: str, rows: int = 5) -> List[Dict]:
    """
    Look up a specific ISIN in the FIRDS register.

    Args:
        isin: ISIN code (e.g. 'US0378331005' for Apple)
        rows: Max listings to return (same ISIN can trade on multiple venues)

    Returns:
        List of instrument records for that ISIN.
    """
    rows = min(rows, 100)
    data = _solr_query(FIRDS_CORE, {
        "q": f"isin:{isin}",
        "rows": str(rows),
        "sort": "publication_date desc",
        "fl": "isin,gnr_full_name,gnr_short_name,gnr_cfi_code,mic,rca_mic,status,status_label,"
              "gnr_notional_curr_code,lei,mrkt_trdng_start_date,mrkt_trdng_trmination_date,"
              "drv_expiry_date,drv_option_type,drv_underlng_isin,publication_date",
    })
    if "error" in data:
        return [data]
    return [_clean_instrument(d) for d in data.get("response", {}).get("docs", [])]


def get_instruments_by_mic(mic: str, rows: int = 20) -> List[Dict]:
    """
    Get instruments traded on a specific venue (MIC code).

    Args:
        mic: Market Identifier Code (e.g. 'XPAR' for Euronext Paris)
        rows: Number of results (max 100)

    Returns:
        List of instruments on that venue.
    """
    rows = min(rows, 100)
    data = _solr_query(FIRDS_CORE, {
        "q": f"mic:{mic} AND status:ACTV",
        "rows": str(rows),
        "sort": "publication_date desc",
        "fl": "isin,gnr_full_name,gnr_short_name,gnr_cfi_code,mic,status_label,"
              "gnr_notional_curr_code,lei,publication_date",
    })
    if "error" in data:
        return [data]
    return [_clean_instrument(d) for d in data.get("response", {}).get("docs", [])]


def get_derivatives_for_underlying(underlying_isin: str, option_type: Optional[str] = None,
                                     rows: int = 20) -> List[Dict]:
    """
    Find derivatives referencing a given underlying ISIN.

    Args:
        underlying_isin: ISIN of the underlying instrument
        option_type: Filter by 'CALL' or 'PUT' (optional)
        rows: Number of results (max 100)

    Returns:
        List of derivative instruments.
    """
    rows = min(rows, 100)
    q = f"drv_underlng_isin:{underlying_isin}"
    if option_type and option_type.upper() in ("CALL", "PUT"):
        q += f" AND drv_option_type:{option_type.upper()}"
    data = _solr_query(FIRDS_CORE, {
        "q": q,
        "rows": str(rows),
        "sort": "drv_expiry_date desc",
        "fl": "isin,gnr_full_name,gnr_short_name,gnr_cfi_code,mic,status_label,"
              "drv_option_type,drv_sp_prc_value_amount,drv_sp_prc_value_curr_code,"
              "drv_expiry_date,drv_delivery_type,drv_option_exercise_style,"
              "drv_underlng_isin,gnr_notional_curr_code,publication_date",
    })
    if "error" in data:
        return [data]
    return [_clean_instrument(d) for d in data.get("response", {}).get("docs", [])]


def count_instruments(query: str = "*:*") -> Dict:
    """
    Count instruments matching a query in FIRDS.

    Args:
        query: Solr query string (default: all instruments)

    Returns:
        Dict with total count and query used.
    """
    data = _solr_query(FIRDS_CORE, {"q": query, "rows": "0"})
    if "error" in data:
        return data
    total = data.get("response", {}).get("numFound", 0)
    return {
        "query": query,
        "total_instruments": total,
        "source": "ESMA FIRDS",
        "timestamp": datetime.utcnow().isoformat()
    }


def get_recently_published(days: int = 7, rows: int = 20) -> List[Dict]:
    """
    Get instruments published in the last N days.

    Args:
        days: Lookback period in days (default 7)
        rows: Number of results (max 100)

    Returns:
        List of recently published instruments.
    """
    rows = min(rows, 100)
    from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00Z")
    now = datetime.utcnow().strftime("%Y-%m-%dT23:59:59Z")
    data = _solr_query(FIRDS_CORE, {
        "q": f"publication_date:[{from_date} TO {now}]",
        "rows": str(rows),
        "sort": "publication_date desc",
        "fl": "isin,gnr_full_name,gnr_short_name,gnr_cfi_code,mic,status,status_label,"
              "gnr_notional_curr_code,publication_date",
    })
    if "error" in data:
        return [data]
    return [_clean_instrument(d) for d in data.get("response", {}).get("docs", [])]


def get_instrument_stats() -> Dict:
    """
    Get aggregate statistics from FIRDS: total instruments and breakdown by status.

    Returns:
        Dict with total count and status facet counts.
    """
    data = _solr_query(FIRDS_CORE, {
        "q": "*:*",
        "rows": "0",
        "facet": "true",
        "facet.field": "status_label",
        "facet.mincount": "1",
    })
    if "error" in data:
        return data
    total = data.get("response", {}).get("numFound", 0)
    facets_raw = data.get("facet_counts", {}).get("facet_fields", {}).get("status_label", [])
    # Solr facets come as [name, count, name, count, ...]
    status_counts = {}
    for i in range(0, len(facets_raw) - 1, 2):
        status_counts[facets_raw[i]] = facets_raw[i + 1]
    return {
        "total_instruments": total,
        "by_status": status_counts,
        "source": "ESMA FIRDS",
        "timestamp": datetime.utcnow().isoformat()
    }


# ─── Investment Firms Register ──────────────────────────────────────────


def search_investment_firms(name: str, rows: int = 10) -> List[Dict]:
    """
    Search ESMA register for MiFID II authorized investment firms.

    Args:
        name: Firm name to search for
        rows: Number of results (max 100)

    Returns:
        List of firm dicts with name, LEI, country, status, etc.
    """
    rows = min(rows, 100)
    data = _solr_query(UPREG_CORE, {
        "q": f"ae_entityName:*{name}* AND type_s:parent",
        "rows": str(rows),
        "fl": "ae_entityName,ae_commercialName,ae_lei,ae_homeMemberState,ae_hostMemberState,"
              "ae_competentAuthority,ae_status,ae_entityTypeLabel,ae_headOfficeAddress,"
              "ae_authorisationNotificationDateStr,ae_website,ae_legalform",
    })
    if "error" in data:
        return [data]
    return [_clean_firm(d) for d in data.get("response", {}).get("docs", [])]


def get_firms_by_country(country: str, status: str = "Active", rows: int = 20) -> List[Dict]:
    """
    List investment firms registered in a specific EU member state.

    Args:
        country: Country name (e.g. 'GERMANY', 'FRANCE', 'NETHERLANDS')
        status: Filter by status — 'Active' or 'Withdrawn' (default: Active)
        rows: Number of results (max 100)

    Returns:
        List of firms in that country.
    """
    rows = min(rows, 100)
    data = _solr_query(UPREG_CORE, {
        "q": f'ae_homeMemberState:"{country.upper()}" AND ae_status:"{status}" AND type_s:parent',
        "rows": str(rows),
        "sort": "ae_entityName asc",
        "fl": "ae_entityName,ae_lei,ae_homeMemberState,ae_competentAuthority,"
              "ae_status,ae_entityTypeLabel,ae_headOfficeAddress,ae_authorisationNotificationDateStr",
    })
    if "error" in data:
        return [data]
    return [_clean_firm(d) for d in data.get("response", {}).get("docs", [])]


def lookup_firm_by_lei(lei: str) -> List[Dict]:
    """
    Look up an investment firm by its LEI (Legal Entity Identifier).

    Args:
        lei: 20-character LEI code

    Returns:
        List of matching firm records.
    """
    data = _solr_query(UPREG_CORE, {
        "q": f"ae_lei:{lei} AND type_s:parent",
        "rows": "5",
        "fl": "ae_entityName,ae_commercialName,ae_lei,ae_homeMemberState,"
              "ae_competentAuthority,ae_status,ae_entityTypeLabel,ae_headOfficeAddress,"
              "ae_authorisationNotificationDateStr,ae_website",
    })
    if "error" in data:
        return [data]
    return [_clean_firm(d) for d in data.get("response", {}).get("docs", [])]


def count_firms_by_country() -> Dict:
    """
    Get a faceted count of investment firms by EU member state.

    Returns:
        Dict with country → count mapping.
    """
    data = _solr_query(UPREG_CORE, {
        "q": "type_s:parent AND ae_status:Active",
        "rows": "0",
        "facet": "true",
        "facet.field": "ae_homeMemberState",
        "facet.mincount": "1",
        "facet.limit": "50",
        "facet.sort": "count",
    })
    if "error" in data:
        return data
    total = data.get("response", {}).get("numFound", 0)
    facets_raw = data.get("facet_counts", {}).get("facet_fields", {}).get("ae_homeMemberState", [])
    country_counts = {}
    for i in range(0, len(facets_raw) - 1, 2):
        country_counts[facets_raw[i]] = facets_raw[i + 1]
    return {
        "total_active_firms": total,
        "by_country": country_counts,
        "source": "ESMA Investment Firms Register",
        "timestamp": datetime.utcnow().isoformat()
    }


# ─── Helpers ────────────────────────────────────────────────────────────


def _clean_instrument(doc: dict) -> dict:
    """Normalize a FIRDS Solr document to a clean dict."""
    return {
        "isin": doc.get("isin"),
        "full_name": doc.get("gnr_full_name"),
        "short_name": doc.get("gnr_short_name"),
        "cfi_code": doc.get("gnr_cfi_code"),
        "currency": doc.get("gnr_notional_curr_code"),
        "mic": doc.get("mic"),
        "rca_mic": doc.get("rca_mic"),
        "lei": doc.get("lei"),
        "status": doc.get("status_label") or doc.get("status"),
        "trading_start": doc.get("mrkt_trdng_start_date"),
        "trading_end": doc.get("mrkt_trdng_trmination_date"),
        "option_type": doc.get("drv_option_type"),
        "strike_price": doc.get("drv_sp_prc_value_amount"),
        "strike_currency": doc.get("drv_sp_prc_value_curr_code"),
        "expiry_date": doc.get("drv_expiry_date"),
        "exercise_style": doc.get("drv_option_exercise_style"),
        "delivery_type": doc.get("drv_delivery_type"),
        "underlying_isin": doc.get("drv_underlng_isin"),
        "publication_date": doc.get("publication_date"),
    }


def _clean_firm(doc: dict) -> dict:
    """Normalize an investment firms register document."""
    return {
        "name": doc.get("ae_entityName"),
        "commercial_name": doc.get("ae_commercialName"),
        "lei": doc.get("ae_lei"),
        "country": doc.get("ae_homeMemberState"),
        "host_country": doc.get("ae_hostMemberState"),
        "competent_authority": doc.get("ae_competentAuthority"),
        "status": doc.get("ae_status"),
        "entity_type": doc.get("ae_entityTypeLabel"),
        "address": doc.get("ae_headOfficeAddress"),
        "authorised_date": doc.get("ae_authorisationNotificationDateStr"),
        "website": doc.get("ae_website"),
        "legal_form": doc.get("ae_legalform"),
    }


# ─── Convenience / Aliases ──────────────────────────────────────────────

def fetch_data(query: str = "*:*", rows: int = 10) -> List[Dict]:
    """Alias for search_instruments — satisfies stub interface."""
    return search_instruments(query, rows)


def get_latest(rows: int = 10) -> List[Dict]:
    """Get most recently published instruments — satisfies stub interface."""
    return get_recently_published(days=3, rows=rows)


if __name__ == "__main__":
    print(json.dumps({
        "module": "esma_regulatory_data_portal",
        "status": "active",
        "functions": 13,
        "source": "https://registers.esma.europa.eu"
    }, indent=2))
