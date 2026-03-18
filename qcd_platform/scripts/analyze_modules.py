#!/usr/bin/env python3
"""
Module Analyzer — Parses all v1 modules, extracts metadata, classifies them.
Outputs a JSON manifest used by the bulk registrar and adapter generator.
"""
import ast
import json
import os
import re
import sys
from pathlib import Path

MODULES_DIR = Path(__file__).resolve().parent.parent.parent / "modules"

TAG_KEYWORDS = {
    "US Equities": [
        "stock", "equity", "s&p", "nasdaq", "nyse", "sector", "etf", "earnings",
        "dividend", "share", "insider", "institutional", "analyst", "valuation",
        "screening", "factor", "momentum", "alpha", "portfolio", "backtest",
        "short", "dark_pool", "options", "finviz", "stockanalysis", "morningstar",
        "iex", "polygon", "tiingo", "twelvedata", "twelve_data", "eodhd", "simfin",
        "zacks", "tipranks", "seeking_alpha", "sa_quant", "quality_factor",
        "quality_minus", "peer_", "relative_val", "comparable", "dcf_",
    ],
    "Fundamentals": [
        "fundamental", "balance_sheet", "income_statement", "cash_flow", "ratio",
        "financial_modeling_prep", "fmp_", "xbrl", "sec_edgar", "filing",
        "10-k", "10-q", "8-k", "annual_report", "quarterly", "revenue",
        "eps", "earnings_quality", "forensic", "accrual",
    ],
    "Earnings": [
        "earnings", "eps", "earnings_call", "earnings_transcript", "earnings_surprise",
        "earnings_whisper", "earnings_calendar", "earnings_estimate", "earnings_nlp",
        "live_earnings", "ai_earnings", "quantearnings",
    ],
    "Sentiment": [
        "sentiment", "fear_greed", "aaii", "put_call", "vix", "social_sentiment",
        "reddit", "wsb", "wallstreetbets", "stocktwits", "twitter", "news_sentiment",
        "lunarcrush", "stockgeist", "sentifi", "breaking_news", "wiki_pageview",
    ],
    "Corporate Actions": [
        "corporate_action", "merger", "acquisition", "spinoff", "ipo", "spac",
        "buyback", "share_buyback", "split", "stock_split", "secondary_offering",
        "proxy_fight", "activist", "tender_offer", "delisting", "index_reconstitution",
    ],
    "Macro": [
        "macro", "gdp", "inflation", "employment", "unemployment", "cpi", "ppi",
        "pmi", "ism", "consumer_confidence", "housing", "retail_sales", "industrial",
        "fred", "bls", "census", "recession", "yield_curve", "treasury", "fed_",
        "ecb", "boj", "boe", "bank_of_", "central_bank", "interest_rate", "swap_rate",
        "taylor_rule", "oecd", "imf_", "world_bank", "eurostat", "comtrade",
        "trade_balance", "current_account", "fiscal", "debt_sustain",
    ],
    "Crypto": [
        "crypto", "bitcoin", "ethereum", "defi", "nft", "stablecoin", "onchain",
        "on_chain", "coingecko", "glassnode", "dune", "flipside", "token_terminal",
        "whale", "liquidation", "perpetual", "mev", "l2", "bridge", "dex_",
        "staking", "token_unlock", "token_velocity",
    ],
    "FX": [
        "forex", "fx_", "currency", "exchange_rate", "fixer", "frankfurter",
        "openexchangerates", "exchangerate", "carry_trade", "ppp_fx", "em_currency",
        "alphavantage_fx", "live_forex",
    ],
    "Commodities": [
        "commodity", "crude_oil", "natural_gas", "gold", "silver", "copper",
        "lithium", "rare_earth", "agricultural", "wheat", "corn", "soybean",
        "lumber", "timber", "precious_metal", "energy", "eia_", "opec",
        "baker_hughes", "shale", "crack_spread", "crush_spread", "spark_spread",
        "contango", "backwardation", "lng_", "petroleum",
    ],
    "ESG": [
        "esg", "climate", "carbon", "sustainability", "biodiversity", "water_scarcity",
        "renewable", "green_bond", "eu_taxonomy", "climate_trace", "climatiq",
    ],
    "Alternative Data": [
        "satellite", "nighttime_light", "shipping", "container", "freight",
        "flight", "airport", "restaurant", "web_traffic", "app_download",
        "job_posting", "patent", "product_launch", "prediction_market",
        "weather_commodity", "drought",
    ],
    "Fixed Income": [
        "bond", "fixed_income", "yield", "credit", "spread", "muni_bond",
        "corporate_bond", "high_yield", "leveraged_loan", "convertible",
        "duration", "convexity", "cds_spread", "clo_", "abs_", "mortgage",
        "repo_rate", "floating_rate", "inflation_linked",
    ],
    "Risk": [
        "risk", "var", "drawdown", "volatility", "garch", "heston", "copula",
        "monte_carlo", "stress_test", "scenario", "tail_risk", "risk_parity",
        "risk_budget", "counterparty", "liquidity_score",
    ],
}

CADENCE_KEYWORDS = {
    "realtime": ["real-time", "realtime", "streaming", "websocket", "tick", "minute-by-minute"],
    "1min": ["1-minute", "1min", "per minute"],
    "5min": ["5-minute", "5min"],
    "15min": ["15-minute", "15min"],
    "1h": ["hourly", "every hour", "1h"],
    "daily": ["daily", "end of day", "eod", "close", "day"],
    "weekly": ["weekly", "every week", "week"],
    "monthly": ["monthly", "every month", "month"],
    "quarterly": ["quarterly", "every quarter", "quarter", "10-q"],
}

GRANULARITY_KEYWORDS = {
    "symbol": ["ticker", "symbol", "stock", "equity", "company", "per-stock", "per-symbol"],
    "market": ["market-wide", "index", "aggregate", "composite", "breadth", "sector"],
    "macro": ["macro", "economy", "gdp", "inflation", "employment", "country", "global"],
}


def extract_module_info(filepath: Path) -> dict:
    """Parse a Python file and extract metadata."""
    name = filepath.stem
    info = {
        "name": name,
        "file": str(filepath.relative_to(MODULES_DIR.parent)),
        "docstring": "",
        "imports": [],
        "functions": [],
        "classes": [],
        "api_urls": [],
        "api_keys_env": [],
        "has_get_data": False,
        "has_fetch": False,
        "main_callable": None,
        "tags": [],
        "cadence": "daily",
        "granularity": "symbol",
        "source": "",
        "parse_error": None,
    }

    try:
        source = filepath.read_text(errors="replace")
    except Exception as e:
        info["parse_error"] = f"read error: {e}"
        return info

    # Extract URLs
    url_pattern = re.compile(r'https?://[^\s\'"\\)]+')
    info["api_urls"] = list(set(url_pattern.findall(source)))[:10]

    # Extract env var references for API keys
    env_pattern = re.compile(r'os\.(?:environ|getenv)\s*[\[(]\s*["\']([^"\']+)')
    info["api_keys_env"] = list(set(env_pattern.findall(source)))

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        info["parse_error"] = f"syntax error: {e}"
        # Still try regex extraction
        info["tags"] = classify_tags(name, source[:2000])
        info["cadence"] = classify_cadence(source[:2000])
        info["granularity"] = classify_granularity(name, source[:2000])
        return info

    # Module docstring
    if (isinstance(tree.body, list) and tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)):
        info["docstring"] = tree.body[0].value.value[:500]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                info["imports"].append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            info["imports"].append(node.module.split(".")[0])
        elif isinstance(node, ast.FunctionDef):
            info["functions"].append(node.name)
            if node.name == "get_data":
                info["has_get_data"] = True
                info["main_callable"] = "get_data"
            elif node.name.startswith("fetch") and not info["main_callable"]:
                info["has_fetch"] = True
                info["main_callable"] = node.name
            elif node.name.startswith("get_") and not info["main_callable"]:
                info["main_callable"] = node.name
        elif isinstance(node, ast.ClassDef):
            info["classes"].append(node.name)

    if not info["main_callable"] and info["functions"]:
        for fn in info["functions"]:
            if fn.startswith("get_") or fn.startswith("fetch_"):
                info["main_callable"] = fn
                break
        if not info["main_callable"]:
            pub_funcs = [f for f in info["functions"] if not f.startswith("_")]
            if pub_funcs:
                info["main_callable"] = pub_funcs[0]

    info["imports"] = list(set(info["imports"]))
    doc_and_name = (info["docstring"] + " " + name).lower()
    info["tags"] = classify_tags(name, doc_and_name)
    info["cadence"] = classify_cadence(doc_and_name)
    info["granularity"] = classify_granularity(name, doc_and_name)

    return info


def classify_tags(name: str, text: str) -> list:
    text_lower = text.lower()
    name_lower = name.lower()
    tags = []
    for tag, keywords in TAG_KEYWORDS.items():
        for kw in keywords:
            if kw in name_lower or kw in text_lower:
                tags.append(tag)
                break
    if not tags:
        tags = ["US Equities"]
    return tags


def classify_cadence(text: str) -> str:
    text_lower = text.lower()
    for cadence, keywords in CADENCE_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return cadence
    return "daily"


def classify_granularity(name: str, text: str) -> str:
    text_lower = text.lower()
    name_lower = name.lower()
    for gran, keywords in GRANULARITY_KEYWORDS.items():
        for kw in keywords:
            if kw in name_lower or kw in text_lower:
                return gran
    return "symbol"


def main():
    modules = []
    py_files = sorted(MODULES_DIR.glob("*.py"))

    for f in py_files:
        if f.name.startswith("__"):
            continue
        info = extract_module_info(f)
        modules.append(info)

    output_path = MODULES_DIR.parent / "qcd_platform" / "module_manifest.json"
    with open(output_path, "w") as fp:
        json.dump(modules, fp, indent=2, default=str)

    # Stats
    total = len(modules)
    with_callable = sum(1 for m in modules if m["main_callable"])
    with_classes = sum(1 for m in modules if m["classes"])
    parse_errors = sum(1 for m in modules if m["parse_error"])
    by_cadence = {}
    by_tag = {}
    for m in modules:
        by_cadence[m["cadence"]] = by_cadence.get(m["cadence"], 0) + 1
        for t in m["tags"]:
            by_tag[t] = by_tag.get(t, 0) + 1

    print(f"\n=== Module Analysis Complete ===")
    print(f"Total modules: {total}")
    print(f"With callable function: {with_callable}")
    print(f"With classes: {with_classes}")
    print(f"Parse errors: {parse_errors}")
    print(f"\nBy cadence:")
    for k, v in sorted(by_cadence.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    print(f"\nBy tag:")
    for k, v in sorted(by_tag.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    print(f"\nManifest written to: {output_path}")


if __name__ == "__main__":
    main()
