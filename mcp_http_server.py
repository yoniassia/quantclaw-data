#!/usr/bin/env python3
"""
QuantClaw Data — HTTP MCP Server
30 financial data tools over HTTP. Port 3056.
"""

import json
import sys
import os
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

MODULES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules')
sys.path.insert(0, MODULES_PATH)


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
    indicator = params.get('indicator', params.get('ticker', 'gdp'))
    try:
        from fred import get_fred_series
        data = get_fred_series(indicator)
        return {'indicator': indicator, 'data': data}
    except Exception:
        # Fallback: treasury yields
        import yfinance as yf
        symbols = {
            'gdp': '^GSPC', 'rates': '^TNX', 'treasury': '^TNX',
            'vix': '^VIX', 'dxy': 'DX-Y.NYB', 'oil': 'CL=F', 'gold': 'GC=F',
        }
        sym = symbols.get(indicator.lower(), '^TNX')
        t = yf.Ticker(sym)
        info = t.info
        return {
            'indicator': indicator,
            'symbol': sym,
            'value': info.get('regularMarketPrice'),
            'previous_close': info.get('previousClose'),
            'change': info.get('regularMarketChange'),
            'change_pct': info.get('regularMarketChangePercent'),
            'timestamp': datetime.now().isoformat(),
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
    try:
        from social_sentiment_spikes import get_ticker_momentum, detect_ticker_spike
        momentum = get_ticker_momentum(symbol)
        if momentum is None:
            # Try detect spike instead
            spike = detect_ticker_spike(symbol)
            return {'ticker': symbol.upper(), 'spike_data': spike if spike else 'No spike detected'}
        return momentum
    except Exception as e:
        # Fallback: basic Yahoo sentiment from news
        t = _yf_ticker(symbol)
        news = t.news or []
        return {
            'ticker': symbol.upper(),
            'news_count': len(news),
            'latest_headlines': [n.get('title', '') for n in news[:5]],
            'note': 'Basic news sentiment (social module unavailable)',
        }


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


def tool_13f(params):
    symbol = params.get('symbol', params.get('ticker', 'AAPL'))
    try:
        from institutional_ownership import get_top_institutional_holders
        return get_top_institutional_holders(symbol)
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
        return {
            'ticker': symbol.upper(),
            'institutional_holders': holders,
            'timestamp': datetime.now().isoformat(),
        }


def tool_13f_changes(params):
    symbol = params.get('symbol', params.get('ticker', 'AAPL'))
    try:
        from institutional_ownership import get_top_institutional_holders
        data = get_top_institutional_holders(symbol)
        return {'ticker': symbol.upper(), 'data': data, 'note': 'QoQ changes from SEC 13F'}
    except Exception as e:
        return {'ticker': symbol.upper(), 'error': str(e)}


def tool_smart_money(params):
    symbol = params.get('symbol', params.get('ticker', 'AAPL'))
    try:
        from smart_money_tracker import track_smart_money
        return track_smart_money(symbol)
    except Exception as e:
        return {'ticker': symbol.upper(), 'error': str(e)}


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
        ratios = compute_put_call_ratios(symbol)
        return {'ticker': symbol.upper(), 'options_chain': chain, 'put_call_ratios': ratios}
    except Exception as e:
        return {'ticker': symbol.upper(), 'error': str(e)}


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
    'macro': {'fn': tool_macro, 'desc': 'Macro indicators (GDP, rates, VIX, DXY)'},
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
    'smart_money': {'fn': tool_smart_money, 'desc': 'Smart money flow tracking'},
    'top_funds': {'fn': tool_top_funds, 'desc': 'Top hedge fund holdings'},
    'gex': {'fn': tool_gex, 'desc': 'Gamma exposure (GEX)'},
    'pin_risk': {'fn': tool_pin_risk, 'desc': 'Options pinning risk'},
    'hedging_flow': {'fn': tool_hedging_flow, 'desc': 'Hedging flow analysis'},
    'alpha_picker': {'fn': tool_alpha_picker, 'desc': 'AI stock scoring algorithm'},
    'fama_french': {'fn': tool_fama_french, 'desc': 'Factor model analysis'},
    'factor_attribution': {'fn': tool_factor_attribution, 'desc': 'Factor return attribution'},
    'factor_returns': {'fn': tool_factor_returns, 'desc': 'Factor return data'},
    'monte_carlo': {'fn': tool_monte_carlo, 'desc': 'Monte Carlo price simulation'},
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
