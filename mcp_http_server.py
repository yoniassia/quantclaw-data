#!/usr/bin/env python3
"""
QuantClaw Data — HTTP MCP Server
30 financial data tools over HTTP. Port 3056.
"""

import json
import sys
import os
import time
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

MODULES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules')
sys.path.insert(0, MODULES_PATH)

import sapi_postgres as sapi


def _yf_ticker(symbol):
    import yfinance as yf
    return yf.Ticker(symbol)


def tool_market_quote(params):
    symbol = params.get('symbol', params.get('ticker', 'AAPL'))
    t = _yf_ticker(symbol)
    info = t.info
    return {
        'ticker': symbol.upper(),
        'price': info.get('currentPrice') or info.get('regularMarketPrice'),
        'previous_close': info.get('previousClose'),
        'open': info.get('open') or info.get('regularMarketOpen'),
        'day_high': info.get('dayHigh'),
        'day_low': info.get('dayLow'),
        'volume': info.get('volume'),
        'market_cap': info.get('marketCap'),
        'pe_ratio': info.get('trailingPE'),
        'forward_pe': info.get('forwardPE'),
        'eps': info.get('trailingEps'),
        'beta': info.get('beta'),
        '52w_high': info.get('fiftyTwoWeekHigh'),
        '52w_low': info.get('fiftyTwoWeekLow'),
        'avg_volume': info.get('averageVolume'),
        'currency': info.get('currency', 'USD'),
        'exchange': info.get('exchange'),
        'timestamp': datetime.now().isoformat(),
    }


def tool_profile(params):
    symbol = params.get('symbol', params.get('ticker', 'AAPL'))
    t = _yf_ticker(symbol)
    info = t.info
    return {
        'ticker': symbol.upper(),
        'name': info.get('longName'),
        'sector': info.get('sector'),
        'industry': info.get('industry'),
        'employees': info.get('fullTimeEmployees'),
        'market_cap': info.get('marketCap'),
        'pe_ratio': info.get('trailingPE'),
        'forward_pe': info.get('forwardPE'),
        'price': info.get('currentPrice'),
        'beta': info.get('beta'),
        'dividend_yield': info.get('dividendYield'),
        'payout_ratio': info.get('payoutRatio'),
        'revenue': info.get('totalRevenue'),
        'gross_margins': info.get('grossMargins'),
        'operating_margins': info.get('operatingMargins'),
        'profit_margins': info.get('profitMargins'),
        'return_on_equity': info.get('returnOnEquity'),
        'debt_to_equity': info.get('debtToEquity'),
        'free_cash_flow': info.get('freeCashflow'),
        'website': info.get('website'),
        'description': info.get('longBusinessSummary', '')[:500],
        'timestamp': datetime.now().isoformat(),
    }


def tool_technicals(params):
    symbol = params.get('symbol', params.get('ticker', 'AAPL'))
    period = params.get('period', '3mo')
    import numpy as np
    t = _yf_ticker(symbol)
    hist = t.history(period=period)
    if hist.empty:
        return {'error': f'No data for {symbol}'}
    close = hist['Close']
    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    # MACD
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9).mean()
    # Bollinger Bands
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    bb_upper = sma20 + 2 * std20
    bb_lower = sma20 - 2 * std20
    # SMAs
    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()
    latest = close.iloc[-1]
    return {
        'ticker': symbol.upper(),
        'price': round(float(latest), 2),
        'rsi_14': round(float(rsi.iloc[-1]), 2) if not np.isnan(rsi.iloc[-1]) else None,
        'macd': round(float(macd_line.iloc[-1]), 4),
        'macd_signal': round(float(signal_line.iloc[-1]), 4),
        'macd_histogram': round(float(macd_line.iloc[-1] - signal_line.iloc[-1]), 4),
        'sma_20': round(float(sma20.iloc[-1]), 2) if not np.isnan(sma20.iloc[-1]) else None,
        'sma_50': round(float(sma50.iloc[-1]), 2) if len(close) >= 50 and not np.isnan(sma50.iloc[-1]) else None,
        'sma_200': round(float(sma200.iloc[-1]), 2) if len(close) >= 200 and not np.isnan(sma200.iloc[-1]) else None,
        'bb_upper': round(float(bb_upper.iloc[-1]), 2) if not np.isnan(bb_upper.iloc[-1]) else None,
        'bb_lower': round(float(bb_lower.iloc[-1]), 2) if not np.isnan(bb_lower.iloc[-1]) else None,
        'bb_middle': round(float(sma20.iloc[-1]), 2) if not np.isnan(sma20.iloc[-1]) else None,
        'above_sma50': bool(latest > sma50.iloc[-1]) if len(close) >= 50 else None,
        'above_sma200': bool(latest > sma200.iloc[-1]) if len(close) >= 200 else None,
        'timestamp': datetime.now().isoformat(),
    }


def tool_options(params):
    symbol = params.get('symbol', params.get('ticker', 'AAPL'))
    from options_flow import get_options_chain
    return get_options_chain(symbol)


def tool_dividends(params):
    symbol = params.get('symbol', params.get('ticker', 'AAPL'))
    t = _yf_ticker(symbol)
    info = t.info
    divs = t.dividends
    recent = divs.tail(8) if len(divs) > 0 else divs
    history = [{'date': str(d.date()), 'amount': round(float(v), 4)} for d, v in recent.items()]
    return {
        'ticker': symbol.upper(),
        'dividend_yield': info.get('dividendYield'),
        'dividend_rate': info.get('dividendRate'),
        'payout_ratio': info.get('payoutRatio'),
        'ex_dividend_date': str(info.get('exDividendDate', '')),
        'total_dividends_paid': len(divs),
        'recent_history': history,
        'timestamp': datetime.now().isoformat(),
    }


def tool_ratings(params):
    symbol = params.get('symbol', params.get('ticker', 'AAPL'))
    t = _yf_ticker(symbol)
    info = t.info
    recs = t.recommendations
    recent_recs = []
    if recs is not None and len(recs) > 0:
        for _, row in recs.tail(10).iterrows():
            recent_recs.append({k: str(v) for k, v in row.to_dict().items()})
    return {
        'ticker': symbol.upper(),
        'recommendation': info.get('recommendationKey'),
        'recommendation_mean': info.get('recommendationMean'),
        'target_high': info.get('targetHighPrice'),
        'target_low': info.get('targetLowPrice'),
        'target_mean': info.get('targetMeanPrice'),
        'target_median': info.get('targetMedianPrice'),
        'num_analysts': info.get('numberOfAnalystOpinions'),
        'recent_recommendations': recent_recs,
        'timestamp': datetime.now().isoformat(),
    }


def tool_earnings(params):
    symbol = params.get('symbol', params.get('ticker', 'AAPL'))
    t = _yf_ticker(symbol)
    info = t.info
    earnings = t.earnings_history
    history = []
    if earnings is not None and len(earnings) > 0:
        for _, row in earnings.tail(8).iterrows():
            history.append({k: str(v) for k, v in row.to_dict().items()})
    return {
        'ticker': symbol.upper(),
        'eps_trailing': info.get('trailingEps'),
        'eps_forward': info.get('forwardEps'),
        'pe_ratio': info.get('trailingPE'),
        'forward_pe': info.get('forwardPE'),
        'peg_ratio': info.get('pegRatio'),
        'earnings_growth': info.get('earningsGrowth'),
        'revenue_growth': info.get('revenueGrowth'),
        'history': history,
        'timestamp': datetime.now().isoformat(),
    }


def tool_news(params):
    symbol = params.get('symbol', params.get('ticker', 'AAPL'))
    t = _yf_ticker(symbol)
    news = t.news or []
    articles = []
    for n in news[:15]:
        articles.append({
            'title': n.get('title', ''),
            'publisher': n.get('publisher', ''),
            'link': n.get('link', ''),
            'published': n.get('providerPublishTime', ''),
            'type': n.get('type', ''),
        })
    return {
        'ticker': symbol.upper(),
        'total_articles': len(articles),
        'articles': articles,
        'timestamp': datetime.now().isoformat(),
    }


def tool_macro(params):
    """Real macro indicators from FRED + yfinance. Returns structured macro data."""
    indicator = params.get('indicator', params.get('ticker', 'snapshot'))
    if indicator == 'snapshot':
        return tool_macro_snapshot(params)
    try:
        from fred import get_series, get_latest_value
        series_map = {
            'gdp': 'GDP', 'cpi': 'CPIAUCSL', 'unemployment': 'UNRATE',
            'rates': 'DFF', 'fed_funds': 'DFF', 'treasury': 'DGS10',
            'pmi': 'UMCSENT', 'consumer_sentiment': 'UMCSENT',
            'industrial_production': 'INDPRO', 'housing': 'HOUST',
            'yield_10y': 'DGS10', 'yield_2y': 'DGS2', 'yield_3m': 'DGS3MO',
            'hy_oas': 'BAMLH0A0HYM2', 'ig_oas': 'BAMLC0A0CM',
        }
        sid = series_map.get(indicator.lower(), indicator.upper())
        data = get_series(sid, limit=30)
        latest = get_latest_value(sid)
        return {
            'indicator': indicator,
            'series_id': sid,
            'latest_value': latest,
            'data': data if isinstance(data, (list, dict)) else str(data),
            'timestamp': datetime.now().isoformat(),
        }
    except Exception as e:
        import yfinance as yf
        symbols = {
            'gdp': '^GSPC', 'rates': '^TNX', 'treasury': '^TNX',
            'vix': '^VIX', 'dxy': 'DX-Y.NYB', 'oil': 'CL=F', 'gold': 'GC=F',
        }
        sym = symbols.get(indicator.lower(), '^TNX')
        t = yf.Ticker(sym)
        info = t.info
        return {
            'indicator': indicator, 'symbol': sym,
            'value': info.get('regularMarketPrice'),
            'previous_close': info.get('previousClose'),
            'change': info.get('regularMarketChange'),
            'change_pct': info.get('regularMarketChangePercent'),
            'timestamp': datetime.now().isoformat(),
            '_fallback': True, '_error': str(e)[:200],
        }


def tool_crypto(params):
    symbol = params.get('symbol', params.get('ticker', 'BTC'))
    sym = symbol.upper()
    if not sym.endswith('-USD'):
        sym = f'{sym}-USD'
    t = _yf_ticker(sym)
    info = t.info
    return {
        'symbol': symbol.upper(),
        'price': info.get('regularMarketPrice'),
        'market_cap': info.get('marketCap'),
        'volume_24h': info.get('volume24Hr') or info.get('volume'),
        'circulating_supply': info.get('circulatingSupply'),
        'change_24h': info.get('regularMarketChangePercent'),
        '52w_high': info.get('fiftyTwoWeekHigh'),
        '52w_low': info.get('fiftyTwoWeekLow'),
        'timestamp': datetime.now().isoformat(),
    }


def tool_forex(params):
    pair = params.get('pair', params.get('ticker', 'EURUSD'))
    sym = pair.upper()
    if '=' not in sym:
        sym = f'{sym}=X'
    t = _yf_ticker(sym)
    info = t.info
    return {
        'pair': pair.upper(),
        'rate': info.get('regularMarketPrice'),
        'previous_close': info.get('previousClose'),
        'change': info.get('regularMarketChange'),
        'change_pct': info.get('regularMarketChangePercent'),
        'day_high': info.get('dayHigh'),
        'day_low': info.get('dayLow'),
        'timestamp': datetime.now().isoformat(),
    }


def tool_commodity(params):
    symbol = params.get('symbol', params.get('ticker', 'gold'))
    sym_map = {
        'gold': 'GC=F', 'silver': 'SI=F', 'oil': 'CL=F', 'wti': 'CL=F',
        'brent': 'BZ=F', 'natural_gas': 'NG=F', 'nat_gas': 'NG=F',
        'copper': 'HG=F', 'platinum': 'PL=F', 'palladium': 'PA=F',
        'wheat': 'ZW=F', 'corn': 'ZC=F', 'soybeans': 'ZS=F',
    }
    sym = sym_map.get(symbol.lower(), symbol if '=' in symbol else f'{symbol}=F')
    t = _yf_ticker(sym)
    info = t.info
    return {
        'commodity': symbol,
        'symbol': sym,
        'price': info.get('regularMarketPrice'),
        'previous_close': info.get('previousClose'),
        'change': info.get('regularMarketChange'),
        'change_pct': info.get('regularMarketChangePercent'),
        'timestamp': datetime.now().isoformat(),
    }


def tool_screener(params):
    try:
        from screener import run_screener
        return run_screener(**params)
    except Exception:
        # Fallback
        sector = params.get('sector', 'Technology')
        tickers = {
            'Technology': ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'META', 'TSLA', 'AMZN'],
            'Healthcare': ['JNJ', 'UNH', 'PFE', 'ABBV', 'MRK', 'LLY', 'TMO'],
            'Financial': ['JPM', 'BAC', 'GS', 'MS', 'WFC', 'BLK', 'C'],
        }.get(sector, ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'])
        limit = int(params.get('limit', 5))
        results = []
        for tk in tickers[:limit]:
            try:
                results.append(tool_market_quote({'symbol': tk}))
            except:
                pass
        return {'sector': sector, 'count': len(results), 'results': results}


def tool_sec(params):
    symbol = params.get('symbol', params.get('ticker', 'AAPL'))
    try:
        from institutional_ownership import get_cik
        cik = get_cik(symbol)
        import urllib.request
        url = f'https://efts.sec.gov/LATEST/search-index?q=%22{symbol}%22&dateRange=custom&startdt=2024-01-01&forms=10-K,10-Q,8-K'
        req = urllib.request.Request(url, headers={'User-Agent': 'QuantClaw/1.0'})
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return {'ticker': symbol.upper(), 'cik': cik, 'filings': data}
    except Exception as e:
        # Fallback: use SEC EDGAR directly
        import urllib.request
        url = f'https://efts.sec.gov/LATEST/search-index?q=%22{symbol}%22&forms=10-K,10-Q,8-K&dateRange=custom&startdt=2025-01-01'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'QuantClaw research@quantclaw.org'})
            data = json.loads(urllib.request.urlopen(req, timeout=10).read())
            return {'ticker': symbol.upper(), 'filings': data}
        except:
            return {'ticker': symbol.upper(), 'note': 'SEC EDGAR search unavailable', 'error': str(e)}


def tool_social(params):
    symbol = params.get('symbol', params.get('ticker', 'AAPL'))
    # Primary: SAPI social data (fast, real)
    try:
        social = sapi.fetch_instrument_social(symbol, limit=3)
        if social and len(social) > 0:
            latest = social[0]
            return {
                'ticker': symbol.upper(),
                'source': 'sapi',
                'buy_holding_pct': latest.get('buy_holding_pct'),
                'sell_holding_pct': latest.get('sell_holding_pct'),
                'popularity_rank': latest.get('popularity_uniques'),
                'popularity_7d': latest.get('popularity_7d'),
                'popularity_30d': latest.get('popularity_30d'),
                'traders_7d_change': latest.get('traders_7d_change'),
                'traders_30d_change': latest.get('traders_30d_change'),
                'institutional_pct': latest.get('institutional_pct'),
                'timestamp': datetime.now().isoformat(),
            }
    except Exception:
        pass
    # Fallback: social_sentiment_spikes module (slow, may timeout)
    try:
        from social_sentiment_spikes import get_ticker_momentum, detect_ticker_spike
        momentum = get_ticker_momentum(symbol)
        if momentum is not None:
            return momentum
        spike = detect_ticker_spike(symbol)
        return {'ticker': symbol.upper(), 'spike_data': spike if spike else 'No spike detected'}
    except Exception:
        return {'ticker': symbol.upper(), 'source': 'none', 'note': 'Social sentiment unavailable'}


def tool_short_interest(params):
    symbol = params.get('symbol', params.get('ticker', 'AAPL'))
    t = _yf_ticker(symbol)
    info = t.info
    return {
        'ticker': symbol.upper(),
        'short_ratio': info.get('shortRatio'),
        'short_percent_of_float': info.get('shortPercentOfFloat'),
        'shares_short': info.get('sharesShort'),
        'shares_short_prior': info.get('sharesShortPriorMonth'),
        'float_shares': info.get('floatShares'),
        'shares_outstanding': info.get('sharesOutstanding'),
        'timestamp': datetime.now().isoformat(),
    }


def tool_etf_holdings(params):
    symbol = params.get('symbol', params.get('ticker', 'SPY'))
    t = _yf_ticker(symbol)
    info = t.info
    try:
        holdings = t.institutional_holders
        top = []
        if holdings is not None:
            for _, row in holdings.head(15).iterrows():
                top.append({k: str(v) for k, v in row.to_dict().items()})
    except:
        top = []
    return {
        'ticker': symbol.upper(),
        'name': info.get('longName'),
        'total_assets': info.get('totalAssets'),
        'nav': info.get('navPrice'),
        'expense_ratio': info.get('annualReportExpenseRatio'),
        'top_holders': top,
        'timestamp': datetime.now().isoformat(),
    }


def tool_esg(params):
    symbol = params.get('symbol', params.get('ticker', 'AAPL'))
    t = _yf_ticker(symbol)
    try:
        esg = t.sustainability
        if esg is not None and not esg.empty:
            scores = {str(k): str(v) for k, v in esg.to_dict().items() if v is not None}
        else:
            scores = {}
    except:
        scores = {}
    info = t.info
    return {
        'ticker': symbol.upper(),
        'name': info.get('longName'),
        'esg_scores': scores,
        'timestamp': datetime.now().isoformat(),
    }


_13f_cache = {}
_13F_CACHE_TTL = 6 * 3600  # 6 hours — 13F data is quarterly

def tool_13f(params):
    symbol = params.get('symbol', params.get('ticker', 'AAPL')).upper()
    now = time.time()
    if symbol in _13f_cache and (now - _13f_cache[symbol]['ts']) < _13F_CACHE_TTL:
        return {**_13f_cache[symbol]['data'], 'cached': True}
    try:
        from institutional_ownership import get_top_institutional_holders
        result = get_top_institutional_holders(symbol)
        _13f_cache[symbol] = {'data': result, 'ts': now}
        return result
    except Exception:
        t = _yf_ticker(symbol)
        holders = []
        try:
            inst = t.institutional_holders
            if inst is not None:
                for _, row in inst.head(15).iterrows():
                    holders.append({k: str(v) for k, v in row.to_dict().items()})
        except:
            pass
        result = {'ticker': symbol, 'institutional_holders': holders, 'timestamp': datetime.now().isoformat()}
        if holders:
            _13f_cache[symbol] = {'data': result, 'ts': now}
        return result


def tool_13f_changes(params):
    symbol = params.get('symbol', params.get('ticker', 'AAPL'))
    try:
        from institutional_ownership import get_top_institutional_holders
        data = get_top_institutional_holders(symbol)
        return {'ticker': symbol.upper(), 'data': data, 'note': 'QoQ changes from SEC 13F'}
    except Exception as e:
        return {'ticker': symbol.upper(), 'error': str(e)}


def tool_smart_money(params):
    """Redirects to SAPI-backed smart money (real institutional/social data)."""
    return tool_smart_money_sapi(params)


def tool_top_funds(params):
    try:
        from institutional_ownership import get_top_institutional_holders
        tickers = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN']
        results = {}
        for tk in tickers:
            try:
                results[tk] = get_top_institutional_holders(tk)
            except:
                pass
        return {'top_held_stocks': results, 'timestamp': datetime.now().isoformat()}
    except Exception as e:
        return {'error': str(e)}


def tool_gex(params):
    symbol = params.get('symbol', params.get('ticker', 'SPY'))
    try:
        from options_flow import get_options_chain, compute_put_call_ratios
        chain = get_options_chain(symbol)
        if isinstance(chain, dict) and ('error' in chain or 'Unauthorized' in str(chain)):
            return {
                'ticker': symbol.upper(),
                'status': 'degraded',
                'error': 'Options chain auth failed (Yahoo 401). GEX unavailable.',
                'put_call_ratios': [],
            }
        ratios = compute_put_call_ratios(symbol)
        return {'ticker': symbol.upper(), 'options_chain': chain, 'put_call_ratios': ratios}
    except Exception as e:
        return {'ticker': symbol.upper(), 'status': 'degraded', 'error': str(e)[:200]}


def tool_pin_risk(params):
    symbol = params.get('symbol', params.get('ticker', 'AAPL'))
    try:
        from options_flow import get_options_chain
        chain = get_options_chain(symbol)
        return {'ticker': symbol.upper(), 'data': chain, 'analysis': 'pin_risk'}
    except Exception as e:
        return {'ticker': symbol.upper(), 'error': str(e)}


def tool_hedging_flow(params):
    symbol = params.get('symbol', params.get('ticker', 'QQQ'))
    try:
        from options_flow import scan_unusual_activity
        unusual = scan_unusual_activity(symbol)
        return {'ticker': symbol.upper(), 'unusual_activity': unusual}
    except Exception as e:
        return {'ticker': symbol.upper(), 'error': str(e)}


def tool_alpha_picker(params):
    symbol = params.get('symbol', params.get('ticker', 'AAPL'))
    try:
        from alpha_picker import AlphaPickerV3
        ap = AlphaPickerV3()
        score = ap.score_stock(symbol)
        return score
    except Exception as e:
        return {'ticker': symbol.upper(), 'error': str(e)}


def tool_fama_french(params):
    symbol = params.get('symbol', params.get('ticker', 'AAPL'))
    try:
        from factor_model_engine import get_factor_scores
        return get_factor_scores(symbol)
    except Exception as e:
        return {'ticker': symbol.upper(), 'error': str(e)}


def tool_factor_attribution(params):
    symbol = params.get('symbol', params.get('ticker', 'AAPL'))
    try:
        from factor_model_engine import get_factor_scores
        scores = get_factor_scores(symbol)
        return {'ticker': symbol.upper(), 'factor_scores': scores}
    except Exception as e:
        return {'ticker': symbol.upper(), 'error': str(e)}


def tool_factor_returns(params):
    tickers = params.get('tickers', 'AAPL,MSFT,GOOGL,NVDA,AMZN')
    if isinstance(tickers, str):
        tickers = [t.strip() for t in tickers.split(',')]
    try:
        from factor_model_engine import compare_factors
        df = compare_factors(tickers)
        return {'tickers': tickers, 'factors': df.to_dict('records') if hasattr(df, 'to_dict') else str(df)}
    except Exception as e:
        return {'error': str(e)}


def tool_monte_carlo(params):
    symbol = params.get('symbol', params.get('ticker', 'SPY'))
    sims = int(params.get('simulations', 1000))
    try:
        from monte_carlo import cmd_monte_carlo
        import argparse
        args = argparse.Namespace(ticker=symbol, simulations=sims, days=252, percentile=5)
        return cmd_monte_carlo(args)
    except Exception as e:
        # Fallback: simple Monte Carlo
        import numpy as np
        t = _yf_ticker(symbol)
        hist = t.history(period='1y')
        if hist.empty:
            return {'ticker': symbol.upper(), 'error': 'No historical data'}
        returns = hist['Close'].pct_change().dropna()
        mu = float(returns.mean())
        sigma = float(returns.std())
        last_price = float(hist['Close'].iloc[-1])
        final_prices = []
        for _ in range(sims):
            price = last_price
            for _ in range(252):
                price *= (1 + np.random.normal(mu, sigma))
            final_prices.append(price)
        final_prices = sorted(final_prices)
        return {
            'ticker': symbol.upper(),
            'current_price': round(last_price, 2),
            'simulations': sims,
            'days': 252,
            'median': round(float(np.median(final_prices)), 2),
            'mean': round(float(np.mean(final_prices)), 2),
            'p5': round(float(np.percentile(final_prices, 5)), 2),
            'p25': round(float(np.percentile(final_prices, 25)), 2),
            'p75': round(float(np.percentile(final_prices, 75)), 2),
            'p95': round(float(np.percentile(final_prices, 95)), 2),
            'max': round(float(max(final_prices)), 2),
            'min': round(float(min(final_prices)), 2),
        }


def tool_sapi_quote(params):
    """eToro SAPI instrument data — 10K+ symbols with price, fundamentals, analyst, social, ESG."""
    symbol = params.get('symbol', params.get('ticker', ''))
    if not symbol:
        return {'error': 'symbol required'}
    inst = sapi.fetch_instruments(symbol)
    if not inst:
        return {'error': f'Symbol {symbol} not found in SAPI database (10,409 instruments)'}
    prices = sapi.fetch_instrument_prices(symbol, limit=1)
    fundies = sapi.fetch_instrument_fundamentals(symbol, limit=1)
    analysts = sapi.fetch_instrument_analysts(symbol, limit=1)
    social_data = sapi.fetch_instrument_social(symbol, limit=1)
    esg_data = sapi.fetch_instrument_esg(symbol, limit=1)
    betas = sapi.fetch_instrument_betas(symbol, limit=1)
    result = {'instrument': inst}
    if prices:
        result['latest_price'] = prices[0]
    if fundies:
        result['fundamentals'] = fundies[0]
    if analysts:
        result['analysts'] = analysts[0]
    if social_data:
        result['social'] = social_data[0]
    if esg_data:
        result['esg'] = esg_data[0]
    if betas:
        result['betas'] = betas[0]
    result['source'] = 'etoro_sapi_postgres'
    result['timestamp'] = datetime.now().isoformat()
    return result


def tool_sapi_prices(params):
    """Historical SAPI price snapshots for a symbol."""
    symbol = params.get('symbol', params.get('ticker', ''))
    limit = int(params.get('limit', 30))
    if not symbol:
        return {'error': 'symbol required'}
    prices = sapi.fetch_instrument_prices(symbol, limit=limit)
    if not prices:
        return {'error': f'No price data for {symbol}'}
    return {'symbol': symbol, 'count': len(prices), 'prices': prices, 'source': 'etoro_sapi_postgres'}


def tool_sapi_fundamentals(params):
    """SAPI fundamentals history for a symbol (PE, margins, ROE, debt, etc.)."""
    symbol = params.get('symbol', params.get('ticker', ''))
    limit = int(params.get('limit', 12))
    if not symbol:
        return {'error': 'symbol required'}
    data = sapi.fetch_instrument_fundamentals(symbol, limit=limit)
    if not data:
        return {'error': f'No fundamentals for {symbol}'}
    return {'symbol': symbol, 'count': len(data), 'fundamentals': data, 'source': 'etoro_sapi_postgres'}


def tool_sapi_analysts(params):
    """SAPI analyst consensus, target prices, and ratings."""
    symbol = params.get('symbol', params.get('ticker', ''))
    limit = int(params.get('limit', 12))
    if not symbol:
        return {'error': 'symbol required'}
    data = sapi.fetch_instrument_analysts(symbol, limit=limit)
    if not data:
        return {'error': f'No analyst data for {symbol}'}
    return {'symbol': symbol, 'count': len(data), 'analysts': data, 'source': 'etoro_sapi_postgres'}


def tool_sapi_social(params):
    """SAPI social/trader sentiment (popularity, trader changes)."""
    symbol = params.get('symbol', params.get('ticker', ''))
    limit = int(params.get('limit', 30))
    if not symbol:
        return {'error': 'symbol required'}
    data = sapi.fetch_instrument_social(symbol, limit=limit)
    if not data:
        return {'error': f'No social data for {symbol}'}
    return {'symbol': symbol, 'count': len(data), 'social': data, 'source': 'etoro_sapi_postgres'}


def tool_sapi_search(params):
    """Search/list SAPI instruments by name, symbol, sector, or asset class."""
    query = params.get('query', params.get('q', ''))
    sector = params.get('sector', '')
    asset_class = params.get('asset_class', '')
    limit = min(int(params.get('limit', 50)), 500)

    with sapi._connect() as conn:
        with conn.cursor() as cur:
            conditions = []
            bind_params = []
            if query:
                conditions.append("(UPPER(symbol) LIKE UPPER(%s) OR UPPER(display_name) LIKE UPPER(%s))")
                bind_params.extend([f'%{query}%', f'%{query}%'])
            if sector:
                conditions.append("UPPER(umbrella_sector) LIKE UPPER(%s)")
                bind_params.append(f'%{sector}%')
            if asset_class:
                conditions.append("UPPER(asset_class) LIKE UPPER(%s)")
                bind_params.append(f'%{asset_class}%')

            where = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
            cur.execute(
                f"SELECT instrument_id, symbol, display_name, exchange, umbrella_sector, asset_class, market_cap_class, is_tradable FROM instruments {where} ORDER BY symbol LIMIT %s",
                (*bind_params, limit),
            )
            rows = [sapi._serialize_row(dict(r)) for r in cur.fetchall()]
            cur.execute(f"SELECT COUNT(*) as total FROM instruments {where}", tuple(bind_params))
            total = cur.fetchone()['total']
    return {'count': len(rows), 'total_matching': total, 'instruments': rows, 'source': 'etoro_sapi_postgres'}


def _fred_latest(series_id, api_key=None):
    """Fetch latest value from FRED series. Returns (value, date) or (None, None)."""
    import urllib.request
    key = api_key or os.environ.get('FRED_API_KEY', '67587f0c539b9b4c15b36c14f543f5f4')
    url = f'https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={key}&file_type=json&sort_order=desc&limit=60'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'QuantClaw/2.0'})
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        for obs in data.get('observations', []):
            if obs.get('value', '.') != '.':
                return float(obs['value']), obs['date']
    except Exception:
        pass
    return None, None


def _fred_series(series_id, limit=60, api_key=None):
    """Fetch recent observations from FRED. Returns list of (value, date)."""
    import urllib.request
    key = api_key or os.environ.get('FRED_API_KEY', '67587f0c539b9b4c15b36c14f543f5f4')
    url = f'https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={key}&file_type=json&sort_order=desc&limit={limit}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'QuantClaw/2.0'})
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        out = []
        for obs in data.get('observations', []):
            if obs.get('value', '.') != '.':
                out.append((float(obs['value']), obs['date']))
        return out
    except Exception:
        return []


def tool_macro_snapshot(params):
    """
    Comprehensive macro snapshot for regime detection.
    Returns VIX, yield curve, credit spreads, CPI, DXY, PMI proxies, earnings revisions.
    All real data from FRED + yfinance. No mock data.
    """
    import yfinance as yf
    from concurrent.futures import ThreadPoolExecutor, as_completed

    result = {'timestamp': datetime.now().isoformat(), 'sources': {}}

    def fetch_fred(sid):
        return sid, _fred_series(sid, limit=60)

    def fetch_yf(sym):
        try:
            t = yf.Ticker(sym)
            info = t.info
            return sym, info
        except Exception:
            return sym, {}

    fred_ids = ['DGS2', 'DGS10', 'DGS3MO', 'BAMLH0A0HYM2', 'BAMLC0A0CM',
                'CPIAUCSL', 'UMCSENT', 'INDPRO', 'UNRATE', 'T10Y2Y']
    yf_symbols = ['^VIX', '^VIX3M', 'DX-Y.NYB']

    fred_data = {}
    yf_data = {}

    with ThreadPoolExecutor(max_workers=8) as pool:
        fred_futures = {pool.submit(fetch_fred, sid): sid for sid in fred_ids}
        yf_futures = {pool.submit(fetch_yf, sym): sym for sym in yf_symbols}
        for f in as_completed(list(fred_futures) + list(yf_futures)):
            try:
                key, val = f.result()
                if key in fred_ids:
                    fred_data[key] = val
                else:
                    yf_data[key] = val
            except Exception:
                pass

    def latest(series):
        return series[0][0] if series else None

    def older(series, idx):
        return series[idx][0] if len(series) > idx else None

    # VIX
    vix_info = yf_data.get('^VIX', {})
    vix3m_info = yf_data.get('^VIX3M', {})
    vix_level = vix_info.get('regularMarketPrice') or vix_info.get('currentPrice')
    vix3m_level = vix3m_info.get('regularMarketPrice') or vix3m_info.get('currentPrice')
    vix_prev = vix_info.get('regularMarketPreviousClose')
    term_slope = 0
    if vix_level and vix3m_level and vix_level > 0:
        term_slope = round((vix3m_level - vix_level) / vix_level, 4)

    result['vix'] = {
        'level': vix_level,
        'previous_close': vix_prev,
        'change_1d': round(vix_level - vix_prev, 2) if vix_level and vix_prev else None,
        'vix3m': vix3m_level,
        'term_slope': term_slope,
    }
    result['sources']['vix'] = 'yfinance_realtime'

    # Yield Curve
    y2 = latest(fred_data.get('DGS2', []))
    y10 = latest(fred_data.get('DGS10', []))
    y3m = latest(fred_data.get('DGS3MO', []))
    t10y2y = latest(fred_data.get('T10Y2Y', []))
    spread_2s10s = round(y10 - y2, 2) if y10 is not None and y2 is not None else t10y2y
    spread_3m10y = round(y10 - y3m, 2) if y10 is not None and y3m is not None else None
    result['yield_curve'] = {
        'dgs2': y2, 'dgs10': y10, 'dgs3mo': y3m,
        'spread_2s10s': spread_2s10s,
        'spread_3m10y': spread_3m10y,
        'inverted': (spread_2s10s is not None and spread_2s10s < 0) or
                    (spread_3m10y is not None and spread_3m10y < 0),
    }
    result['sources']['yield_curve'] = 'fred_daily'

    # Credit Spreads
    hy_series = fred_data.get('BAMLH0A0HYM2', [])
    ig_series = fred_data.get('BAMLC0A0CM', [])
    hy_oas = latest(hy_series)
    ig_oas = latest(ig_series)
    hy_older = older(hy_series, min(21, len(hy_series) - 1)) if hy_series else None
    result['credit_spreads'] = {
        'hy_oas': hy_oas, 'ig_oas': ig_oas,
        'hy_oas_21d_ago': hy_older,
        'widening': hy_oas > hy_older + 0.25 if hy_oas is not None and hy_older is not None else False,
    }
    result['sources']['credit_spreads'] = 'fred_daily'

    # CPI
    cpi_series = fred_data.get('CPIAUCSL', [])
    cpi_yoy = None
    cpi_trend = 'stable'
    if len(cpi_series) >= 13:
        cpi_latest = cpi_series[0][0]
        cpi_yago = cpi_series[12][0]
        cpi_yoy = round((cpi_latest / cpi_yago - 1) * 100, 2)
        if len(cpi_series) >= 16:
            prev_yoy = (cpi_series[3][0] / cpi_series[15][0] - 1) * 100
            if cpi_yoy > prev_yoy + 0.15:
                cpi_trend = 'rising'
            elif cpi_yoy < prev_yoy - 0.15:
                cpi_trend = 'falling'
    result['cpi'] = {'yoy': cpi_yoy, 'trend': cpi_trend, 'latest_index': latest(cpi_series)}
    result['sources']['cpi'] = 'fred_monthly'

    # DXY
    dxy_info = yf_data.get('DX-Y.NYB', {})
    dxy_level = dxy_info.get('regularMarketPrice') or dxy_info.get('currentPrice')
    dxy_prev = dxy_info.get('regularMarketPreviousClose')
    result['dxy'] = {'level': dxy_level, 'previous_close': dxy_prev}
    result['sources']['dxy'] = 'yfinance_realtime'

    # PMI Proxies (UMCSENT = Michigan Consumer Sentiment, INDPRO = Industrial Production)
    umcsent_series = fred_data.get('UMCSENT', [])
    indpro_series = fred_data.get('INDPRO', [])
    umcsent = latest(umcsent_series)
    indpro = latest(indpro_series)
    indpro_prev = older(indpro_series, 1)
    indpro_mom = None
    if indpro is not None and indpro_prev is not None and indpro_prev > 0:
        indpro_mom = round((indpro / indpro_prev - 1) * 100, 2)

    # Synthetic PMI: combine consumer sentiment (rescaled) + industrial production MoM
    # UMCSENT: historical range ~50-115, mean ~85. Map to PMI-like scale:
    #   50 → 38 (deep contraction), 85 → 50 (neutral), 110 → 60 (strong expansion)
    # INDPRO MoM: +0.5% → strong expansion boost, -0.5% → contraction signal
    synthetic_pmi = 50.0
    if umcsent is not None:
        synthetic_pmi = max(35, min(65, 38 + (umcsent - 50) * 0.4))
    if indpro_mom is not None:
        synthetic_pmi += indpro_mom * 5.0
        synthetic_pmi = max(30, min(70, synthetic_pmi))

    result['pmi_proxy'] = {
        'synthetic_composite': round(synthetic_pmi, 1),
        'consumer_sentiment': umcsent,
        'consumer_sentiment_date': umcsent_series[0][1] if umcsent_series else None,
        'industrial_production': indpro,
        'industrial_production_mom': indpro_mom,
        'note': 'PMI proxy from UMCSENT + INDPRO (ISM PMI is proprietary, not available from FRED)',
    }
    result['sources']['pmi_proxy'] = 'fred_monthly'

    # Unemployment
    unemp = latest(fred_data.get('UNRATE', []))
    result['unemployment'] = {'rate': unemp}
    result['sources']['unemployment'] = 'fred_monthly'

    # Earnings Revision Aggregate (from SAPI if available)
    try:
        result['earnings_revisions'] = _compute_earnings_revisions_aggregate()
        result['sources']['earnings_revisions'] = 'sapi_postgres'
    except Exception as e:
        result['earnings_revisions'] = {
            'ratio': None, 'trend': 'unknown',
            'error': str(e)[:200],
        }
        result['sources']['earnings_revisions'] = 'unavailable'

    return result


def _compute_earnings_revisions_aggregate():
    """
    Compute aggregate earnings revision ratio from SAPI analyst data.
    Uses latest vs 30-day-ago consensus targets across top 50 S&P500 names.
    """
    universe = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B',
                'UNH', 'JNJ', 'JPM', 'V', 'PG', 'XOM', 'MA', 'HD', 'CVX', 'MRK',
                'ABBV', 'LLY', 'PEP', 'KO', 'COST', 'AVGO', 'WMT', 'TMO', 'MCD',
                'CSCO', 'ACN', 'ABT', 'CRM', 'DHR', 'NEE', 'CMCSA', 'VZ', 'NKE',
                'TXN', 'PM', 'BMY', 'UPS']
    upgrades = 0
    downgrades = 0
    unchanged = 0
    total = 0
    try:
        for sym in universe[:30]:
            rows = sapi.fetch_instrument_analysts(sym, limit=35)
            if rows and len(rows) >= 2:
                latest = rows[0]
                # Compare against ~30 days ago snapshot
                prev = rows[-1] if len(rows) > 25 else rows[min(len(rows)-1, 7)]
                latest_target = latest.get('target_price')
                prev_target = prev.get('target_price')
                if latest_target and prev_target:
                    latest_val = float(latest_target)
                    prev_val = float(prev_target)
                    if prev_val > 0:
                        change = (latest_val - prev_val) / prev_val
                        total += 1
                        if change > 0.01:
                            upgrades += 1
                        elif change < -0.01:
                            downgrades += 1
                        else:
                            unchanged += 1
    except Exception:
        pass

    if total == 0:
        return {'ratio': None, 'trend': 'unknown', 'sample_size': 0}

    ratio = round(upgrades / max(downgrades, 1), 2)
    if upgrades > downgrades * 1.3:
        trend = 'improving'
    elif downgrades > upgrades * 1.3:
        trend = 'deteriorating'
    else:
        trend = 'stable'

    return {
        'ratio': ratio,
        'trend': trend,
        'upgrades': upgrades,
        'downgrades': downgrades,
        'unchanged': unchanged,
        'sample_size': total,
    }


def tool_estimate_revision_aggregate(params):
    """Aggregate earnings revision ratio across S&P500 universe from SAPI."""
    try:
        result = _compute_earnings_revisions_aggregate()
        result['timestamp'] = datetime.now().isoformat()
        result['source'] = 'sapi_postgres'
        return result
    except Exception as e:
        return {'error': str(e), 'timestamp': datetime.now().isoformat()}


def tool_smart_money_sapi(params):
    """Smart money tracking using SAPI institutional/social data (real data, no mocks)."""
    symbol = params.get('symbol', params.get('ticker', 'AAPL'))
    result = {'ticker': symbol.upper(), 'timestamp': datetime.now().isoformat(), 'source': 'sapi_postgres'}

    try:
        social = sapi.fetch_instrument_social(symbol, limit=5)
        if social:
            latest = social[0]
            result['social_sentiment'] = {
                'popularity_rank': latest.get('popularity_uniques'),
                'popularity_7d': latest.get('popularity_7d'),
                'popularity_30d': latest.get('popularity_30d'),
                'buy_holding_pct': latest.get('buy_holding_pct'),
                'sell_holding_pct': latest.get('sell_holding_pct'),
                'traders_7d_change': latest.get('traders_7d_change'),
                'traders_30d_change': latest.get('traders_30d_change'),
                'institutional_pct': latest.get('institutional_pct'),
                'holding_pct': latest.get('holding_pct'),
            }

        analysts = sapi.fetch_instrument_analysts(symbol, limit=3)
        if analysts:
            latest = analysts[0]
            result['analyst_consensus'] = {
                'consensus': latest.get('consensus'),
                'target_price': latest.get('target_price'),
                'target_upside_pct': latest.get('target_upside_pct'),
                'total_analysts': latest.get('total_analysts'),
                'buy_count': latest.get('buy_count'),
                'hold_count': latest.get('hold_count'),
                'sell_count': latest.get('sell_count'),
                'target_high': latest.get('target_high'),
                'target_low': latest.get('target_low'),
                'estimated_eps': latest.get('estimated_eps'),
                'next_earnings_date': str(latest.get('next_earnings_date', '')),
            }

        fundies = sapi.fetch_instrument_fundamentals(symbol, limit=2)
        if fundies:
            latest = fundies[0]
            result['fundamentals'] = {
                'pe_ratio': latest.get('pe_ratio') or latest.get('trailing_pe'),
                'forward_pe': latest.get('forward_pe'),
                'profit_margin': latest.get('profit_margin'),
                'roe': latest.get('return_on_equity') or latest.get('roe'),
                'debt_equity': latest.get('debt_to_equity') or latest.get('debt_equity'),
                'institutional_pct': latest.get('institutional_pct'),
            }
    except Exception as e:
        result['error'] = str(e)[:300]

    return result


# Tool registry
TOOLS = {
    'market_quote': {'fn': tool_market_quote, 'desc': 'Real-time stock quote (price, volume, market cap, ratios)'},
    'profile': {'fn': tool_profile, 'desc': 'Company profile and fundamentals'},
    'technicals': {'fn': tool_technicals, 'desc': 'Technical indicators (RSI, MACD, Bollinger Bands, SMA)'},
    'options': {'fn': tool_options, 'desc': 'Options chain data'},
    'dividends': {'fn': tool_dividends, 'desc': 'Dividend history and yield'},
    'ratings': {'fn': tool_ratings, 'desc': 'Analyst ratings and price targets'},
    'earnings': {'fn': tool_earnings, 'desc': 'Earnings data and history'},
    'news': {'fn': tool_news, 'desc': 'Latest news articles'},
    'macro': {'fn': tool_macro, 'desc': 'Macro indicators from FRED (GDP, CPI, yields, spreads, PMI proxy)'},
    'macro_snapshot': {'fn': tool_macro_snapshot, 'desc': 'Comprehensive macro snapshot for regime detection (VIX, yields, spreads, CPI, PMI proxy, DXY, earnings revisions)'},
    'estimate_revision_aggregate': {'fn': tool_estimate_revision_aggregate, 'desc': 'Aggregate earnings revision ratio across S&P500 universe'},
    'smart_money_sapi': {'fn': tool_smart_money_sapi, 'desc': 'Smart money tracking via eToro SAPI (real institutional + social data)'},
    'crypto': {'fn': tool_crypto, 'desc': 'Cryptocurrency prices'},
    'forex': {'fn': tool_forex, 'desc': 'Foreign exchange rates'},
    'commodity': {'fn': tool_commodity, 'desc': 'Commodity prices (gold, oil, etc.)'},
    'screener': {'fn': tool_screener, 'desc': 'Stock screener by sector'},
    'sec': {'fn': tool_sec, 'desc': 'SEC EDGAR filings'},
    'social': {'fn': tool_social, 'desc': 'Social media sentiment'},
    'short_interest': {'fn': tool_short_interest, 'desc': 'Short interest data'},
    'etf_holdings': {'fn': tool_etf_holdings, 'desc': 'ETF holdings and top holders'},
    'esg': {'fn': tool_esg, 'desc': 'ESG scores'},
    '13f': {'fn': tool_13f, 'desc': 'Institutional 13F holdings'},
    '13f_changes': {'fn': tool_13f_changes, 'desc': '13F quarter-over-quarter changes'},
    'smart_money': {'fn': tool_smart_money, 'desc': 'Smart money flow tracking (via SAPI institutional + social data)'},
    'top_funds': {'fn': tool_top_funds, 'desc': 'Top hedge fund holdings'},
    'gex': {'fn': tool_gex, 'desc': 'Gamma exposure (GEX)'},
    'pin_risk': {'fn': tool_pin_risk, 'desc': 'Options pinning risk'},
    'hedging_flow': {'fn': tool_hedging_flow, 'desc': 'Hedging flow analysis'},
    'alpha_picker': {'fn': tool_alpha_picker, 'desc': 'AI stock scoring algorithm'},
    'fama_french': {'fn': tool_fama_french, 'desc': 'Factor model analysis'},
    'factor_attribution': {'fn': tool_factor_attribution, 'desc': 'Factor return attribution'},
    'factor_returns': {'fn': tool_factor_returns, 'desc': 'Factor return data'},
    'monte_carlo': {'fn': tool_monte_carlo, 'desc': 'Monte Carlo price simulation'},
    'sapi_quote': {'fn': tool_sapi_quote, 'desc': 'eToro SAPI full instrument data (price, fundamentals, analysts, social, ESG, betas) — 10K+ symbols'},
    'sapi_prices': {'fn': tool_sapi_prices, 'desc': 'SAPI price history snapshots'},
    'sapi_fundamentals': {'fn': tool_sapi_fundamentals, 'desc': 'SAPI fundamentals history (PE, margins, ROE, debt)'},
    'sapi_analysts': {'fn': tool_sapi_analysts, 'desc': 'SAPI analyst consensus and target prices'},
    'sapi_social': {'fn': tool_sapi_social, 'desc': 'SAPI trader sentiment and popularity'},
    'sapi_search': {'fn': tool_sapi_search, 'desc': 'Search/list eToro SAPI instruments (10,409 symbols)'},
}


def call_tool(name, params):
    if name not in TOOLS:
        # Try with underscores/hyphens swapped
        alt = name.replace('-', '_')
        if alt not in TOOLS:
            return {'error': f'Unknown tool: {name}', 'available': sorted(TOOLS.keys())}
        name = alt
    try:
        result = TOOLS[name]['fn'](params)
        return {'tool': name, 'result': result}
    except Exception as e:
        return {'tool': name, 'error': str(e), 'traceback': traceback.format_exc()[-500:]}


def list_tools():
    return {
        'tools': {k: v['desc'] for k, v in TOOLS.items()},
        'count': len(TOOLS),
    }


class MCPHTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send_json(self, data, status=200):
        try:
            body = json.dumps(data, indent=2, default=str).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            self.wfile.write(body)
        except BrokenPipeError:
            pass  # Client disconnected, don't crash

    def do_OPTIONS(self):
        self._send_json({})

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        params = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(parsed.query).items()}

        if path in ('', '/', '/health'):
            self._send_json({'status': 'ok', 'service': 'quantclaw-data-mcp', 'tools': len(TOOLS), 'version': '2.0.0',
                'endpoints': ['GET /health', 'GET /tools', 'GET /tool/<name>?params', 'POST /mcp/call', 'POST /mcp/batch', 'POST /rpc']})
            return
        if path in ('/tools', '/list-tools', '/mcp/tools'):
            self._send_json(list_tools())
            return
        if path.startswith('/tool/'):
            tool_name = path[6:]
            self._send_json(call_tool(tool_name, params))
            return
        self._send_json({'error': 'Not found'}, 404)

    def do_POST(self):
        cl = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(cl)
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_json({'error': 'Invalid JSON'}, 400)
            return
        path = urlparse(self.path).path.rstrip('/')

        if path == '/rpc':
            method = data.get('method', '')
            params = data.get('params', {})
            if method == 'list_tools':
                result = list_tools()
            elif method == 'call_tool':
                tool = params.get('tool') or params.get('name', '')
                args = params.get('args') or params.get('arguments', {})
                result = call_tool(tool, args)
            else:
                result = {'error': f'Unknown method: {method}'}
            self._send_json({'jsonrpc': '2.0', 'result': result, 'id': data.get('id')})
            return
        if path == '/mcp/call':
            tool = data.get('tool') or data.get('name', '')
            args = data.get('arguments') or data.get('params') or data.get('args', {})
            self._send_json(call_tool(tool, args))
            return
        if path == '/mcp/batch':
            if not isinstance(data, list):
                self._send_json({'error': 'Expected array'}, 400)
                return
            self._send_json([call_tool(c.get('tool', c.get('name', '')), c.get('arguments', c.get('params', {}))) for c in data])
            return
        self._send_json({'error': 'Not found'}, 404)


def main():
    port = int(os.environ.get('MCP_HTTP_PORT', 3056))
    httpd = HTTPServer(('0.0.0.0', port), MCPHTTPHandler)
    print(f"🚀 QuantClaw MCP HTTP v2 on http://0.0.0.0:{port} — {len(TOOLS)} tools", file=sys.stderr)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


if __name__ == '__main__':
    main()
