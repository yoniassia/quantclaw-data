#!/usr/bin/env python3
"""
Platinum Enriched Symbol Data — Fully enriched per-symbol records merging all Gold sources.

Aggregates: price + technicals, valuations, fundamentals, analyst targets,
earnings quality, earnings surprises, insider activity, institutional ownership,
news sentiment, estimate revisions, dividends, DCF intrinsic value.

Usage:
    from modules.platinum_enriched import get_platinum, get_platinum_summary

Author: QUANTCLAW DATA Build Agent
Phase: Platinum-1
"""

import sys
import os
import json
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

warnings.filterwarnings('ignore')

CACHE_DIR = Path(__file__).parent / "cache" / "platinum"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL_SECONDS = 3600  # 1 hour

DB_DSN = "dbname=quantclaw_data host=/var/run/postgresql user=quant"

# ---------------------------------------------------------------------------
# Universe — top 200 symbols across sectors
# ---------------------------------------------------------------------------
TOP_200 = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "UNH", "LLY",
    "JPM", "XOM", "V", "JNJ", "AVGO", "PG", "MA", "HD", "COST", "MRK",
    "ABBV", "CVX", "CRM", "NFLX", "AMD", "KO", "PEP", "ADBE", "WMT", "TMO",
    "LIN", "ACN", "CSCO", "MCD", "ABT", "DHR", "INTC", "ORCL", "VZ", "CMCSA",
    "TXN", "PM", "NEE", "RTX", "LOW", "UNP", "HON", "INTU", "ISRG", "QCOM",
    "BA", "AMGN", "GE", "SPGI", "CAT", "IBM", "PLD", "NOW", "BKNG", "AXP",
    "BLK", "AMAT", "SYK", "DE", "MDLZ", "GILD", "ADI", "TJX", "MMC", "LRCX",
    "VRTX", "ADP", "REGN", "SLB", "MU", "PANW", "SCHW", "PYPL", "CB", "ETN",
    "CI", "DUK", "SO", "BSX", "CME", "ZTS", "SNPS", "CL", "HUM", "EOG",
    "PNC", "FDX", "MCK", "ICE", "WM", "PSA", "SHW", "ITW", "NOC", "CDNS",
    "GD", "USB", "EMR", "CCI", "MMM", "APD", "ORLY", "FCX", "NSC", "GM",
    "FTNT", "PXD", "AJG", "MCO", "TGT", "PCAR", "DG", "ROP", "SRE", "AEP",
    "AFL", "OKE", "WELL", "FIS", "TFC", "SPG", "CARR", "D", "MPC", "PSX",
    "HCA", "NUE", "KMB", "CMI", "AIG", "MCHP", "MSCI", "HLT", "VLO", "STZ",
    "CTSH", "EW", "KLAC", "F", "GIS", "DXCM", "IQV", "WMB", "BK", "DVN",
    "YUM", "A", "RCL", "O", "EXC", "HAL", "DOW", "CTAS", "KDP", "AWK",
    "HSY", "ON", "AZO", "KEYS", "FAST", "LHX", "ED", "ROST", "WEC", "PPG",
    "GPN", "VRSK", "CDW", "EQR", "CHD", "LEN", "AME", "GEHC", "DLR", "PHM",
    "MTD", "TSCO", "HPQ", "XEL", "CPRT", "IT", "DD", "BRO", "ANSS", "NDAQ",
    "WST", "EFX", "WAB", "FANG", "TTD", "BR", "WTW", "ZBH", "FE", "TRGP",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_call(func, *args, **kwargs) -> Optional[Dict]:
    """Call a module function, return None on any error."""
    try:
        return func(*args, **kwargs)
    except Exception:
        return None


def _load_cache(ticker: str) -> Optional[Dict]:
    """Load cached Platinum record if fresh."""
    cache_file = CACHE_DIR / f"{ticker.upper()}.json"
    if not cache_file.exists():
        return None
    try:
        age = time.time() - cache_file.stat().st_mtime
        if age > CACHE_TTL_SECONDS:
            return None
        with open(cache_file) as f:
            return json.load(f)
    except Exception:
        return None


def _save_cache(ticker: str, data: Dict):
    """Persist Platinum record to disk cache."""
    cache_file = CACHE_DIR / f"{ticker.upper()}.json"
    try:
        with open(cache_file, 'w') as f:
            json.dump(data, f, default=str)
    except Exception:
        pass


def _clean_nan(obj):
    """Recursively replace NaN/Inf with None for JSON safety."""
    if isinstance(obj, float):
        if obj != obj or obj == float('inf') or obj == float('-inf'):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _clean_nan(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean_nan(v) for v in obj]
    return obj


# ---------------------------------------------------------------------------
# Data collectors — each returns a dict section
# ---------------------------------------------------------------------------

def _get_yf_profile(ticker: str) -> Dict:
    """Core fundamentals + price from Yahoo Finance in a single call."""
    import yfinance as yf
    stock = yf.Ticker(ticker)
    info = stock.info or {}

    price = info.get('currentPrice') or info.get('regularMarketPrice') or 0
    prev = info.get('previousClose') or price
    change_pct = ((price - prev) / prev * 100) if prev else 0

    hist = stock.history(period='6mo')
    technicals = {}
    if not hist.empty:
        closes = hist['Close']
        technicals['sma_20'] = round(float(closes.tail(20).mean()), 2) if len(closes) >= 20 else None
        technicals['sma_50'] = round(float(closes.tail(50).mean()), 2) if len(closes) >= 50 else None
        technicals['sma_200'] = None
        technicals['price_vs_sma20'] = round((price / technicals['sma_20'] - 1) * 100, 2) if technicals['sma_20'] else None
        technicals['price_vs_sma50'] = round((price / technicals['sma_50'] - 1) * 100, 2) if technicals['sma_50'] else None

        # RSI-14
        delta = closes.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss
        rsi_series = 100 - (100 / (1 + rs))
        technicals['rsi_14'] = round(float(rsi_series.iloc[-1]), 2) if len(rsi_series) >= 14 else None

        technicals['high_52w'] = round(float(closes.max()), 2)
        technicals['low_52w'] = round(float(closes.min()), 2)
        if technicals['high_52w']:
            technicals['pct_from_52w_high'] = round((price / technicals['high_52w'] - 1) * 100, 2)

    return {
        "profile": {
            "name": info.get('shortName') or info.get('longName', ticker),
            "sector": info.get('sector', 'N/A'),
            "industry": info.get('industry', 'N/A'),
            "market_cap": info.get('marketCap'),
            "employees": info.get('fullTimeEmployees'),
            "country": info.get('country', 'N/A'),
            "exchange": info.get('exchange', 'N/A'),
        },
        "price": {
            "current": round(price, 2) if price else None,
            "previous_close": round(prev, 2) if prev else None,
            "change_pct": round(change_pct, 2),
            "day_high": info.get('dayHigh'),
            "day_low": info.get('dayLow'),
            "volume": info.get('volume'),
            "avg_volume": info.get('averageVolume'),
        },
        "technicals": technicals,
        "valuation": {
            "pe_trailing": info.get('trailingPE'),
            "pe_forward": info.get('forwardPE'),
            "peg_ratio": info.get('pegRatio'),
            "pb_ratio": info.get('priceToBook'),
            "ps_ratio": info.get('priceToSalesTrailing12Months'),
            "ev_ebitda": info.get('enterpriseToEbitda'),
            "ev_revenue": info.get('enterpriseToRevenue'),
            "price_to_fcf": None,
        },
        "fundamentals": {
            "revenue": info.get('totalRevenue'),
            "revenue_growth": info.get('revenueGrowth'),
            "gross_margin": info.get('grossMargins'),
            "operating_margin": info.get('operatingMargins'),
            "profit_margin": info.get('profitMargins'),
            "roe": info.get('returnOnEquity'),
            "roa": info.get('returnOnAssets'),
            "debt_to_equity": info.get('debtToEquity'),
            "current_ratio": info.get('currentRatio'),
            "free_cash_flow": info.get('freeCashflow'),
            "eps_trailing": info.get('trailingEps'),
            "eps_forward": info.get('forwardEps'),
            "beta": info.get('beta'),
        },
        "dividend": {
            "yield": info.get('dividendYield'),
            "rate": info.get('dividendRate'),
            "payout_ratio": info.get('payoutRatio'),
            "ex_date": str(info.get('exDividendDate', '')),
        },
    }


def _get_analyst_targets(ticker: str) -> Optional[Dict]:
    """Analyst consensus targets from Gold module."""
    from modules.analyst_target_price import get_consensus_targets
    raw = _safe_call(get_consensus_targets, ticker)
    if not raw:
        return None
    consensus = raw.get('consensus', {})
    return {
        "mean_target": consensus.get('mean_target'),
        "median_target": consensus.get('median_target'),
        "high_target": consensus.get('high_target'),
        "low_target": consensus.get('low_target'),
        "upside_pct": consensus.get('mean_upside_pct'),
        "num_analysts": consensus.get('num_analysts'),
        "assessment": raw.get('assessment'),
    }


def _get_earnings_quality(ticker: str) -> Optional[Dict]:
    """Earnings quality metrics from Gold module."""
    from modules.earnings_quality import analyze_earnings_quality
    raw = _safe_call(analyze_earnings_quality, ticker)
    if not raw:
        return None
    accruals = raw.get('accruals_ratio', {})
    beneish = raw.get('beneish_m_score', {})
    altman = raw.get('altman_z_score', {})
    summary = raw.get('summary', {})
    return {
        "accruals_ratio": accruals.get('value'),
        "accruals_flag": accruals.get('flag'),
        "beneish_m_score": beneish.get('m_score'),
        "beneish_flag": beneish.get('flag'),
        "altman_z_score": altman.get('z_score'),
        "altman_flag": altman.get('flag'),
        "overall_risk": summary.get('overall_risk'),
        "earnings_quality": summary.get('earnings_quality'),
        "manipulation_risk": summary.get('manipulation_risk'),
    }


def _get_earnings_surprises(ticker: str) -> Optional[Dict]:
    """Earnings surprise history from Gold module."""
    from modules.earnings_surprise_history import get_earnings_history
    raw = _safe_call(get_earnings_history, ticker)
    if not raw:
        return None
    surprises = raw.get('surprises', [])
    return {
        "beat_rate": raw.get('beat_rate'),
        "avg_surprise_pct": raw.get('avg_surprise_pct'),
        "total_quarters": raw.get('total_quarters'),
        "beats": raw.get('beats'),
        "misses": raw.get('misses'),
        "avg_drift_1d": raw.get('avg_drift_1d'),
        "avg_drift_5d": raw.get('avg_drift_5d'),
        "last_quarter": surprises[0] if surprises else None,
    }


def _get_estimate_revisions(ticker: str) -> Optional[Dict]:
    """Estimate revision momentum from Gold module."""
    from modules.estimate_revision_tracker import get_estimate_momentum_summary
    raw = _safe_call(get_estimate_momentum_summary, ticker)
    if not raw:
        return None
    velocity = raw.get('revision_velocity') or {}
    ar = raw.get('analyst_recommendations') or {}
    vel_val = velocity.get('avg_monthly_velocity') if isinstance(velocity, dict) else velocity
    trend_val = velocity.get('trend') if isinstance(velocity, dict) else None
    return {
        "momentum_score": raw.get('composite_momentum_score'),
        "signal": raw.get('signal'),
        "revision_velocity": vel_val,
        "trend": trend_val,
        "total_analysts": ar.get('total_analysts') if ar else None,
        "consensus": ar.get('consensus') if ar else None,
        "target_price": ar.get('target_price') if ar else None,
        "upside_pct": ar.get('upside_pct') if ar else None,
    }


def _get_institutional(ticker: str) -> Optional[Dict]:
    """Top institutional holders from Gold module."""
    from modules.institutional_ownership import get_top_institutional_holders
    raw = _safe_call(get_top_institutional_holders, ticker)
    if not raw:
        return None
    return {
        "institutional_pct": raw.get('institutional_ownership_pct'),
        "top_holders": raw.get('top_holders', [])[:5],
        "total_institutions": raw.get('total_institutions'),
    }


def _get_insider_activity(ticker: str) -> Optional[Dict]:
    """Insider trading signals from Gold module."""
    from modules.insider_trade_alert import fetch_recent_insider_filings, insider_sentiment_score
    filings = _safe_call(fetch_recent_insider_filings, ticker)
    if not filings or not filings.get('filings'):
        return {"signal": "no_data", "transactions": []}
    score = _safe_call(insider_sentiment_score, ticker, filings.get('filings', []))
    return {
        "signal": score.get('signal') if score else 'unknown',
        "buy_sell_ratio": score.get('buy_sell_ratio') if score else None,
        "net_value": score.get('net_value') if score else None,
        "recent_count": len(filings.get('filings', [])),
    }


def _get_dcf(ticker: str) -> Optional[Dict]:
    """DCF intrinsic value from Gold module."""
    from modules.dcf_valuation import perform_dcf_valuation
    raw = _safe_call(perform_dcf_valuation, ticker)
    if not raw or raw.get('error'):
        return None
    val = raw.get('valuation', raw)
    return {
        "intrinsic_value": val.get('intrinsic_value_per_share') or val.get('fair_value'),
        "current_price": val.get('current_price'),
        "upside_pct": val.get('upside_pct') or val.get('margin_of_safety_pct'),
        "wacc": val.get('wacc'),
        "terminal_growth": val.get('terminal_growth_rate'),
        "assessment": val.get('assessment'),
    }


def _get_news_sentiment(ticker: str) -> Optional[Dict]:
    """Sentiment-weighted news score."""
    from modules.sentiment_weighted_news import compute_weighted_sentiment
    raw = _safe_call(compute_weighted_sentiment, ticker)
    if not raw:
        return None
    return {
        "composite_score": raw.get('composite_score'),
        "signal": raw.get('signal'),
        "article_count": raw.get('article_count'),
        "positive_pct": raw.get('positive_pct'),
        "negative_pct": raw.get('negative_pct'),
    }


def _get_gf_data(ticker: str) -> Optional[Dict]:
    """GuruFocus rankings + valuations from PostgreSQL."""
    import psycopg2
    conn = None
    try:
        conn = psycopg2.connect(dbname='quantclaw_data', host='/var/run/postgresql', user='quant')
        cur = conn.cursor()

        result = {}

        cur.execute("""
            SELECT gf_score, financial_strength, profitability_rank, growth_rank,
                   gf_value_rank, momentum_rank, predictability_rank, payload
            FROM gf_rankings WHERE symbol = %s ORDER BY fetched_at DESC LIMIT 1
        """, (ticker.upper(),))
        row = cur.fetchone()
        if row:
            result['rankings'] = {
                'gf_score': float(row[0]) if row[0] else None,
                'financial_strength': float(row[1]) if row[1] else None,
                'profitability_rank': float(row[2]) if row[2] else None,
                'growth_rank': float(row[3]) if row[3] else None,
                'value_rank': float(row[4]) if row[4] else None,
                'momentum_rank': float(row[5]) if row[5] else None,
                'predictability_rank': float(row[6]) if row[6] else None,
            }
            if row[7]:
                payload = row[7] if isinstance(row[7], dict) else json.loads(row[7])
                result['rankings']['piotroski_f'] = payload.get('piotroski_f_score')
                result['rankings']['altman_z'] = payload.get('altman_z_score')

        cur.execute("""
            SELECT gf_value, dcf_value, graham_number, peter_lynch_value,
                   current_price, price_to_gf_value, payload
            FROM gf_valuations WHERE symbol = %s ORDER BY fetched_at DESC LIMIT 1
        """, (ticker.upper(),))
        row = cur.fetchone()
        if row:
            result['valuations'] = {
                'gf_value': float(row[0]) if row[0] else None,
                'dcf_value': float(row[1]) if row[1] else None,
                'graham_number': float(row[2]) if row[2] else None,
                'peter_lynch_value': float(row[3]) if row[3] else None,
                'gf_current_price': float(row[4]) if row[4] else None,
                'price_to_gf_value': float(row[5]) if row[5] else None,
            }

        cur.execute("""
            SELECT payload FROM gf_fundamentals
            WHERE symbol = %s ORDER BY fetched_at DESC LIMIT 1
        """, (ticker.upper(),))
        row = cur.fetchone()
        if row and row[0]:
            payload = row[0] if isinstance(row[0], dict) else json.loads(row[0])
            result['gf_fundamentals'] = {
                'roe': payload.get('roe'),
                'roic': payload.get('roic'),
                'revenue_growth_3y': payload.get('revenue_growth_3y'),
                'eps_growth_3y': payload.get('eps_growth_3y'),
                'debt_to_equity': payload.get('debt_to_equity'),
                'interest_coverage': payload.get('interest_coverage'),
                'fcf_yield': payload.get('fcf_yield'),
                'dividend_yield': payload.get('dividend_yield'),
            }

        cur.close()
        return result if result else None
    except Exception:
        return None
    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# DB Persistence — write enriched records to platinum_records hypertable
# ---------------------------------------------------------------------------

def _persist_to_db(ticker: str, data: Dict):
    """Write a Platinum record to the platinum_records table."""
    import psycopg2
    conn = None
    try:
        conn = psycopg2.connect(DB_DSN)
        cur = conn.cursor()

        profile = data.get('profile', {})
        price = data.get('price', {})
        tech = data.get('technicals', {})
        val = data.get('valuation', {})
        fund = data.get('fundamentals', {})
        at = data.get('analyst_targets', {}) or {}
        eq = data.get('earnings_quality', {}) or {}
        es = data.get('earnings_surprises', {}) or {}
        sent = data.get('news_sentiment', {}) or {}
        ins = data.get('insider_activity', {}) or {}
        gf = data.get('gurufocus', {}) or {}
        gf_r = gf.get('rankings', {}) if gf else {}
        gf_v = gf.get('valuations', {}) if gf else {}
        dcf = data.get('dcf_valuation', {}) or {}
        comp = data.get('composite', {})
        meta = data.get('_meta', {})

        cur.execute("""
            INSERT INTO platinum_records (
                symbol, generated_at, composite_score, rating,
                price, change_pct, rsi_14, sma_20, sma_50, volume,
                pe_trailing, pe_forward, pb_ratio, ps_ratio, ev_ebitda,
                market_cap, revenue, revenue_growth, profit_margin, roe,
                debt_to_equity, free_cash_flow,
                analyst_target_mean, analyst_target_median, analyst_upside_pct, analyst_count,
                beat_rate, avg_surprise_pct, earnings_quality, altman_z_score,
                sentiment_score, sentiment_signal,
                insider_signal, insider_buy_sell_ratio,
                gf_score, gf_value, gf_financial_strength, gf_profitability, gf_growth,
                dcf_intrinsic_value, dcf_upside_pct,
                company_name, sector, industry,
                payload, sections_populated, elapsed_seconds
            ) VALUES (
                %s, NOW(), %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s
            )
        """, (
            ticker,
            comp.get('composite_score'),
            comp.get('rating'),
            price.get('current'),
            price.get('change_pct'),
            tech.get('rsi_14'),
            tech.get('sma_20'),
            tech.get('sma_50'),
            price.get('volume'),
            val.get('pe_trailing'),
            val.get('pe_forward'),
            val.get('pb_ratio'),
            val.get('ps_ratio'),
            val.get('ev_ebitda'),
            profile.get('market_cap'),
            fund.get('revenue'),
            fund.get('revenue_growth'),
            fund.get('profit_margin'),
            fund.get('roe'),
            fund.get('debt_to_equity'),
            fund.get('free_cash_flow'),
            at.get('mean_target'),
            at.get('median_target'),
            at.get('upside_pct'),
            at.get('num_analysts'),
            es.get('beat_rate'),
            es.get('avg_surprise_pct'),
            eq.get('earnings_quality'),
            eq.get('altman_z_score'),
            sent.get('composite_score'),
            sent.get('signal'),
            ins.get('signal'),
            ins.get('buy_sell_ratio'),
            gf_r.get('gf_score'),
            gf_v.get('gf_value'),
            gf_r.get('financial_strength'),
            gf_r.get('profitability_rank'),
            gf_r.get('growth_rank'),
            dcf.get('intrinsic_value'),
            dcf.get('upside_pct'),
            profile.get('name'),
            profile.get('sector'),
            profile.get('industry'),
            json.dumps(data, default=str),
            meta.get('sections_populated', 0),
            meta.get('elapsed_seconds'),
        ))
        conn.commit()
        cur.close()
    except Exception as e:
        import logging
        logging.getLogger("quantclaw.platinum").warning(f"DB persist failed for {ticker}: {e}")
    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# Composite scoring
# ---------------------------------------------------------------------------

def _compute_composite_score(data: Dict) -> Dict:
    """Compute a weighted composite score from all enrichment sections."""
    scores = {}
    weights = {}

    # Valuation (lower PE/PB = better, but cap extremes)
    val = data.get('valuation', {})
    pe = val.get('pe_forward') or val.get('pe_trailing')
    if pe and 0 < pe < 100:
        scores['valuation'] = max(0, min(100, 100 - pe))
        weights['valuation'] = 0.15

    # Analyst targets
    at = data.get('analyst_targets', {})
    upside = at.get('upside_pct')
    if upside is not None:
        scores['analyst'] = max(0, min(100, 50 + upside))
        weights['analyst'] = 0.15

    # Earnings quality
    eq = data.get('earnings_quality') or {}
    z = eq.get('altman_z_score')
    if z is not None:
        scores['earnings_quality'] = max(0, min(100, z * 25))
        weights['earnings_quality'] = 0.10

    # Earnings momentum (beat rate, comes as 0-100 pct)
    es = data.get('earnings_surprises') or {}
    br = es.get('beat_rate')
    if br is not None:
        scores['earnings_momentum'] = max(0, min(100, br))
        weights['earnings_momentum'] = 0.10

    # Technicals (RSI-based — 30-70 is neutral, below/above biased)
    tech = data.get('technicals', {})
    rsi = tech.get('rsi_14')
    if rsi is not None:
        scores['technicals'] = max(0, min(100, 100 - abs(rsi - 50) * 2))
        weights['technicals'] = 0.10

    # Fundamentals (profit margin as proxy)
    fund = data.get('fundamentals', {})
    pm = fund.get('profit_margin')
    if pm is not None:
        scores['fundamentals'] = max(0, min(100, pm * 200 + 50))
        weights['fundamentals'] = 0.15

    # DCF upside
    dcf = data.get('dcf_valuation', {})
    dcf_up = dcf.get('upside_pct') if dcf else None
    if dcf_up is not None:
        scores['dcf'] = max(0, min(100, 50 + dcf_up / 2))
        weights['dcf'] = 0.10

    # Sentiment
    sent = data.get('news_sentiment', {})
    comp = sent.get('composite_score') if sent else None
    if comp is not None:
        scores['sentiment'] = max(0, min(100, 50 + comp * 50))
        weights['sentiment'] = 0.10

    # Insider
    ins = data.get('insider_activity', {})
    ins_sig = ins.get('signal') if ins else None
    if ins_sig == 'bullish':
        scores['insider'] = 75
        weights['insider'] = 0.05
    elif ins_sig == 'bearish':
        scores['insider'] = 25
        weights['insider'] = 0.05

    # GuruFocus GF Score (0-100 scale, already normalized)
    gf = data.get('gurufocus', {})
    gf_rankings = gf.get('rankings', {}) if gf else {}
    gf_score = gf_rankings.get('gf_score')
    if gf_score is not None:
        scores['gf_score'] = max(0, min(100, gf_score))
        weights['gf_score'] = 0.15

    total_weight = sum(weights.values()) or 1
    composite = sum(scores.get(k, 0) * weights.get(k, 0) for k in weights) / total_weight

    # Rating tier based on composite
    if composite >= 80:
        rating = "Strong Buy"
    elif composite >= 65:
        rating = "Buy"
    elif composite >= 50:
        rating = "Hold"
    elif composite >= 35:
        rating = "Sell"
    else:
        rating = "Strong Sell"

    return {
        "composite_score": round(composite, 1),
        "rating": rating,
        "component_scores": {k: round(v, 1) for k, v in scores.items()},
        "weights_used": weights,
        "coverage": len(scores),
        "max_coverage": 10,
    }


# ---------------------------------------------------------------------------
# Main Platinum builder
# ---------------------------------------------------------------------------

def get_platinum(ticker: str, use_cache: bool = True, include_slow: bool = True) -> Dict:
    """
    Build a fully enriched Platinum record for a single symbol.

    Args:
        ticker: Stock ticker symbol
        use_cache: Use disk cache if fresh (default: True)
        include_slow: Include slow modules like DCF, 13F (default: True)

    Returns:
        Complete enriched record with all sections.
    """
    ticker = ticker.upper().strip()

    if use_cache:
        cached = _load_cache(ticker)
        if cached:
            cached['_from_cache'] = True
            return cached

    start = time.time()
    result = {
        "ticker": ticker,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "tier": "platinum",
        "version": "1.0",
    }

    # Phase 1: Yahoo Finance core (fast, single API call)
    yf_data = _safe_call(_get_yf_profile, ticker) or {}
    result.update(yf_data)

    # Phase 2: Gold module enrichment (parallelized)
    tasks = {
        'analyst_targets': (_get_analyst_targets, ticker),
        'earnings_quality': (_get_earnings_quality, ticker),
        'earnings_surprises': (_get_earnings_surprises, ticker),
        'estimate_revisions': (_get_estimate_revisions, ticker),
        'news_sentiment': (_get_news_sentiment, ticker),
        'gurufocus': (_get_gf_data, ticker),
    }

    if include_slow:
        tasks['institutional'] = (_get_institutional, ticker)
        tasks['insider_activity'] = (_get_insider_activity, ticker)
        tasks['dcf_valuation'] = (_get_dcf, ticker)

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {}
        for key, (func, arg) in tasks.items():
            futures[executor.submit(func, arg)] = key

        for future in as_completed(futures):
            key = futures[future]
            try:
                data = future.result(timeout=45)
                if data:
                    result[key] = data
            except Exception:
                result[key] = None

    # Phase 3: Composite score
    result['composite'] = _compute_composite_score(result)

    elapsed = round(time.time() - start, 2)
    result['_meta'] = {
        'elapsed_seconds': elapsed,
        'sections_populated': sum(1 for k in [
            'profile', 'price', 'technicals', 'valuation', 'fundamentals',
            'dividend', 'analyst_targets', 'earnings_quality', 'earnings_surprises',
            'estimate_revisions', 'institutional', 'insider_activity', 'dcf_valuation',
            'news_sentiment', 'gurufocus', 'composite'
        ] if result.get(k)),
        'total_sections': 16,
    }

    result = _clean_nan(result)

    if use_cache:
        _save_cache(ticker, result)

    _persist_to_db(ticker, result)

    try:
        from qcd_platform.pipeline.kafka_producer import publish_event
        publish_event("quantclaw.pipeline.platinum", {
            "ticker": ticker,
            "composite_score": result.get('composite', {}).get('composite_score'),
            "rating": result.get('composite', {}).get('rating'),
            "sections": result.get('_meta', {}).get('sections_populated'),
            "ts": datetime.utcnow().isoformat() + "Z",
        })
    except Exception:
        pass

    return result


def get_platinum_summary(ticker: str) -> Dict:
    """Lightweight Platinum — skip slow modules (DCF, 13F, insider)."""
    return get_platinum(ticker, include_slow=False)


def get_platinum_batch(tickers: List[str], max_workers: int = 4) -> Dict:
    """
    Build Platinum records for multiple symbols concurrently.
    Returns {ticker: platinum_record, ...}.
    """
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(get_platinum, t): t for t in tickers}
        for future in as_completed(futures):
            t = futures[future]
            try:
                results[t] = future.result(timeout=120)
            except Exception as e:
                results[t] = {"ticker": t, "error": str(e)}
    return results


def get_universe() -> List[str]:
    """Return the default Platinum universe (top 200 US equities)."""
    return TOP_200.copy()


def search_platinum(query: str) -> List[str]:
    """Search cached Platinum records by ticker prefix or sector."""
    query = query.upper().strip()
    matches = []
    for f in CACHE_DIR.glob("*.json"):
        ticker = f.stem
        if ticker.startswith(query):
            matches.append(ticker)
            continue
        try:
            with open(f) as fh:
                data = json.load(fh)
            sector = (data.get('profile', {}).get('sector', '') or '').upper()
            industry = (data.get('profile', {}).get('industry', '') or '').upper()
            if query in sector or query in industry:
                matches.append(ticker)
        except Exception:
            pass
    return sorted(matches)


def get_platinum_dashboard(
    sort_by: str = 'composite_score',
    min_score: float = 0,
    sector: Optional[str] = None,
    limit: int = 50,
) -> Dict:
    """
    Screen the universe by composite score, sector, or any sortable field.
    Uses cached Platinum records for speed.
    """
    records = []
    for f in CACHE_DIR.glob("*.json"):
        try:
            with open(f) as fh:
                data = json.load(fh)
            comp = data.get('composite', {})
            score = comp.get('composite_score', 0)
            if score < min_score:
                continue
            profile = data.get('profile', {})
            if sector and sector.lower() not in (profile.get('sector', '') or '').lower():
                continue

            gf = data.get('gurufocus', {})
            gf_rankings = gf.get('rankings', {}) if gf else {}

            records.append({
                'ticker': data.get('ticker'),
                'name': profile.get('name'),
                'sector': profile.get('sector'),
                'market_cap': profile.get('market_cap'),
                'price': (data.get('price') or {}).get('current'),
                'change_pct': (data.get('price') or {}).get('change_pct'),
                'composite_score': score,
                'rating': comp.get('rating'),
                'gf_score': gf_rankings.get('gf_score'),
                'pe_forward': (data.get('valuation') or {}).get('pe_forward'),
                'rsi_14': (data.get('technicals') or {}).get('rsi_14'),
                'profit_margin': (data.get('fundamentals') or {}).get('profit_margin'),
                'analyst_upside': (data.get('analyst_targets') or {}).get('upside_pct'),
                'beat_rate': (data.get('earnings_surprises') or {}).get('beat_rate'),
                'generated_at': data.get('generated_at'),
            })
        except Exception:
            continue

    valid_sorts = {
        'composite_score', 'gf_score', 'market_cap', 'price',
        'change_pct', 'pe_forward', 'rsi_14', 'analyst_upside', 'beat_rate',
    }
    if sort_by not in valid_sorts:
        sort_by = 'composite_score'

    records.sort(key=lambda x: x.get(sort_by) or 0, reverse=True)
    records = records[:limit]

    return {
        'count': len(records),
        'sort_by': sort_by,
        'min_score': min_score,
        'sector': sector,
        'data': records,
    }


def refresh_universe(max_workers: int = 3) -> Dict:
    """Pre-cache the entire universe. Returns stats."""
    start = time.time()
    success = 0
    failed = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(get_platinum, t, use_cache=False): t for t in TOP_200}
        for future in as_completed(futures):
            t = futures[future]
            try:
                result = future.result(timeout=180)
                if result and not result.get('error'):
                    success += 1
                else:
                    failed.append(t)
            except Exception:
                failed.append(t)

    return {
        'total': len(TOP_200),
        'success': success,
        'failed': len(failed),
        'failed_tickers': failed,
        'elapsed_seconds': round(time.time() - start, 1),
    }


def main():
    ticker = sys.argv[1] if len(sys.argv) > 1 else 'AAPL'
    action = sys.argv[2] if len(sys.argv) > 2 else 'full'

    if action == 'summary':
        data = get_platinum_summary(ticker)
    elif action == 'batch':
        tickers = ticker.split(',')
        data = get_platinum_batch(tickers)
    elif action == 'universe':
        data = {"universe": get_universe(), "count": len(TOP_200)}
    elif action == 'search':
        data = {"matches": search_platinum(ticker)}
    elif action == 'dashboard':
        data = get_platinum_dashboard(sort_by=ticker if ticker != 'AAPL' else 'composite_score')
    elif action == 'refresh':
        data = refresh_universe()
    else:
        data = get_platinum(ticker)

    print(json.dumps(data, default=str, indent=2))


if __name__ == '__main__':
    main()
