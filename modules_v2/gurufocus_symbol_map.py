"""
GuruFocus Symbol Mapper — resolves eToro symbols ↔ GuruFocus symbols.

GF format: EXCHANGE:TICKER (e.g. NAS:AAPL, NYSE:JPM, LSE:BATS)
Uses the symbol_universe table for eToro instrument data.
"""
import os
import sys
import logging
import re
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.db import execute_query

logger = logging.getLogger("quantclaw.gurufocus.symbolmap")

EXCHANGE_MAP = {
    "Nasdaq": "NAS",
    "NYSE": "NYSE",
    "FRA": "FRA",
    "Euronext Paris": "XPAR",
    "Euronext Brussels": "XBRU",
    "Euronext Amsterdam": "XAMS",
    "Euronext Lisbon": "XLIS",
    "Borsa Italiana": "MIL",
    "Bolsa De Madrid": "XMAD",
    "LSE": "LSE",
    "London Stock Exchange": "LSE",
    "LSE AIM": "LSE",
    "LSE_AIM": "LSE",
    "LSE AIM Auction": "LSE",
    "LSE Auction": "LSE",
    "Hong Kong Exchanges": "HKSE",
    "SIX": "XSWX",
    "OTC Markets Stock Exchange": "OTC",
    "Helsinki Stock Exchange": "OHEL",
    "Oslo Stock Exchange": "OSL",
    "Copenhagen Stock Exchange": "OCSE",
    "Stockholm  Stock Exchange": "OSTO",
    "Dubai Financial Market": "DFM",
    "Abu Dhabi": "ADX",
    "Sydney": "ASX",
    "Chicago Board Options Exchange": "CBOE",
}

# Reverse: GF exchange prefix → region for data lookups
GF_REGION_MAP = {
    "NAS": "U", "NYSE": "U", "OTC": "U", "CBOE": "U",
    "LSE": "B",
    "FRA": "E", "XPAR": "E", "XBRU": "E", "XAMS": "E",
    "XLIS": "E", "MIL": "E", "XMAD": "E", "XSWX": "E",
    "OHEL": "E", "OSL": "E", "OCSE": "E", "OSTO": "E",
    "HKSE": "A", "DFM": "A", "ADX": "A",
    "ASX": "O",
}

# Simple symbol suffix → exchange heuristic for symbols without exchange info
SUFFIX_TO_GF = {
    ".L": "LSE", ".AS": "XAMS", ".PA": "XPAR", ".BR": "XBRU",
    ".LS": "XLIS", ".MI": "MIL", ".MC": "XMAD", ".SW": "XSWX",
    ".HE": "OHEL", ".OL": "OSL", ".CO": "OCSE", ".ST": "OSTO",
    ".F": "FRA", ".DE": "FRA",
    ".HK": "HKSE", ".AX": "ASX",
    ".DH": "DFM", ".AD": "ADX", ".AE": "ADX",
    ".NV": "XAMS",
}

SKIP_SUFFIXES = {".RTH", ".US"}

_symbol_cache: Optional[Dict[str, str]] = None


def _load_symbol_universe() -> Dict[str, str]:
    """Load symbol_universe from DB. Returns {etoro_symbol: gf_symbol}."""
    rows = execute_query(
        """SELECT symbol, exchange, etoro_instrument_id, metadata
           FROM symbol_universe
           WHERE asset_class = 'stocks' AND is_active = true""",
        fetch=True,
    )
    mapping = {}
    for row in (rows or []):
        symbol = row["symbol"]
        gf_sym = etoro_symbol_to_gf(symbol, row.get("exchange"))
        if gf_sym:
            mapping[symbol] = gf_sym
    return mapping


def etoro_symbol_to_gf(symbol: str, exchange: Optional[str] = None) -> Optional[str]:
    """
    Convert an eToro-style symbol to GF format.
    Tries: exchange field → suffix heuristic → US default for clean tickers.
    """
    if exchange and exchange in EXCHANGE_MAP:
        gf_exch = EXCHANGE_MAP[exchange]
        ticker = symbol.split(".")[0] if "." in symbol else symbol
        if exchange == "Hong Kong Exchanges":
            ticker = ticker.zfill(5)
        return f"{gf_exch}:{ticker}"

    for skip in SKIP_SUFFIXES:
        if symbol.endswith(skip):
            return None

    for suffix, gf_exch in SUFFIX_TO_GF.items():
        if symbol.endswith(suffix):
            ticker = symbol[: -len(suffix)]
            if gf_exch == "HKSE":
                ticker = ticker.zfill(5)
            return f"{gf_exch}:{ticker}"

    if symbol == "BRK.B":
        return "NYSE:BRK.B"

    if re.match(r"^[A-Z]{1,5}$", symbol):
        return f"NAS:{symbol}"

    return None


def get_gf_symbol(etoro_symbol: str) -> Optional[str]:
    """Get cached GF symbol for an eToro symbol."""
    global _symbol_cache
    if _symbol_cache is None:
        _symbol_cache = _load_symbol_universe()
    return _symbol_cache.get(etoro_symbol)


def get_all_mappings() -> Dict[str, str]:
    """Return full {etoro_symbol: gf_symbol} mapping."""
    global _symbol_cache
    if _symbol_cache is None:
        _symbol_cache = _load_symbol_universe()
    return dict(_symbol_cache)


def get_tradeable_gf_symbols() -> List[str]:
    """Return list of GF symbols for all tradeable eToro stocks."""
    mappings = get_all_mappings()
    return list(mappings.values())


def invalidate_cache():
    global _symbol_cache
    _symbol_cache = None
