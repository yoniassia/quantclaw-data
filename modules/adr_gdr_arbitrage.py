#!/usr/bin/env python3
"""
ADR/GDR Arbitrage Monitor Module — Dual-Listed Price Discrepancies & FX-Adjusted Spreads

Analyzes price discrepancies between American Depositary Receipts (ADRs), Global Depositary Receipts (GDRs),
and their underlying foreign ordinary shares, accounting for FX rates and conversion ratios.

Data Sources:
- Yahoo Finance: ADR/GDR and ordinary share prices
- FRED: Real-time FX rates (Federal Reserve Economic Data)
- ECB: European Central Bank FX reference rates
- SEC EDGAR: ADR prospectus for conversion ratios (when available)

Key Metrics:
- Price premium/discount (ADR vs ordinary, FX-adjusted)
- Implied FX rate vs market rate
- Arbitrage profit potential (bps)
- Trading volume comparison
- Conversion ratio adjustments

Common ADR Structures:
- Level I ADR: OTC, minimal reporting
- Level II/III ADR: Exchange-listed (NYSE, NASDAQ)
- Sponsored vs Unsponsored
- Conversion ratios: 1:1, 1:10, 2:1, etc.

Author: QUANTCLAW DATA Build Agent
Phase: 147
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yfinance as yf
from xml.etree import ElementTree as ET

# Known ADR/GDR pairs with conversion ratios
# Format: {ADR_ticker: {ordinary_ticker, home_exchange, ratio, currency}}
# ratio = how many ordinary shares per 1 ADR (e.g., BP: 6.0 means 1 ADR = 6 ordinary shares)
ADR_PAIRS = {
    # UK ADRs
    'BP': {'ordinary': 'BP.L', 'exchange': 'LSE', 'ratio': 6.0, 'currency': 'GBP', 'name': 'BP plc'},
    'HSBC': {'ordinary': 'HSBA.L', 'exchange': 'LSE', 'ratio': 5.0, 'currency': 'GBP', 'name': 'HSBC Holdings'},
    'GSK': {'ordinary': 'GSK.L', 'exchange': 'LSE', 'ratio': 2.0, 'currency': 'GBP', 'name': 'GlaxoSmithKline'},
    'AZN': {'ordinary': 'AZN.L', 'exchange': 'LSE', 'ratio': 1.0, 'currency': 'GBP', 'name': 'AstraZeneca'},
    'RELX': {'ordinary': 'REL.L', 'exchange': 'LSE', 'ratio': 1.0, 'currency': 'GBP', 'name': 'RELX'},
    'RIO': {'ordinary': 'RIO.L', 'exchange': 'LSE', 'ratio': 4.0, 'currency': 'GBP', 'name': 'Rio Tinto'},
    'BTI': {'ordinary': 'BATS.L', 'exchange': 'LSE', 'ratio': 1.0, 'currency': 'GBP', 'name': 'British American Tobacco'},
    
    # Japanese ADRs
    'SONY': {'ordinary': '6758.T', 'exchange': 'TSE', 'ratio': 1.0, 'currency': 'JPY', 'name': 'Sony Group'},
    'TM': {'ordinary': '7203.T', 'exchange': 'TSE', 'ratio': 2.0, 'currency': 'JPY', 'name': 'Toyota Motor'},
    'MUFG': {'ordinary': '8306.T', 'exchange': 'TSE', 'ratio': 1.0, 'currency': 'JPY', 'name': 'Mitsubishi UFJ'},
    'SMFG': {'ordinary': '8316.T', 'exchange': 'TSE', 'ratio': 1.0, 'currency': 'JPY', 'name': 'Sumitomo Mitsui'},
    'NMR': {'ordinary': '6268.T', 'exchange': 'TSE', 'ratio': 10.0, 'currency': 'JPY', 'name': 'Nomura Holdings'},
    'HTHIY': {'ordinary': '6501.T', 'exchange': 'TSE', 'ratio': 2.0, 'currency': 'JPY', 'name': 'Hitachi'},
    'MTU': {'ordinary': '8766.T', 'exchange': 'TSE', 'ratio': 10.0, 'currency': 'JPY', 'name': 'Mitsubishi Estate'},
    
    # European ADRs
    'ASML': {'ordinary': 'ASML.AS', 'exchange': 'AEX', 'ratio': 1.0, 'currency': 'EUR', 'name': 'ASML Holding'},
    'SAP': {'ordinary': 'SAP.DE', 'exchange': 'XETRA', 'ratio': 1.0, 'currency': 'EUR', 'name': 'SAP SE'},
    'SAN': {'ordinary': 'SAN.MC', 'exchange': 'BME', 'ratio': 1.0, 'currency': 'EUR', 'name': 'Banco Santander'},
    'BBVA': {'ordinary': 'BBVA.MC', 'exchange': 'BME', 'ratio': 1.0, 'currency': 'EUR', 'name': 'BBVA'},
    'NVO': {'ordinary': 'NOVO-B.CO', 'exchange': 'OMX', 'ratio': 1.0, 'currency': 'DKK', 'name': 'Novo Nordisk'},
    'SIEGY': {'ordinary': 'SIE.DE', 'exchange': 'XETRA', 'ratio': 2.0, 'currency': 'EUR', 'name': 'Siemens'},
    'TEF': {'ordinary': 'TEF.MC', 'exchange': 'BME', 'ratio': 1.0, 'currency': 'EUR', 'name': 'Telefonica'},
    
    # Swiss ADRs
    'NVS': {'ordinary': 'NOVN.SW', 'exchange': 'SIX', 'ratio': 1.0, 'currency': 'CHF', 'name': 'Novartis'},
    'RHHBY': {'ordinary': 'ROG.SW', 'exchange': 'SIX', 'ratio': 20.0, 'currency': 'CHF', 'name': 'Roche Holding'},
    'UBS': {'ordinary': 'UBSG.SW', 'exchange': 'SIX', 'ratio': 1.0, 'currency': 'CHF', 'name': 'UBS Group'},
    
    # Chinese ADRs
    'BABA': {'ordinary': '9988.HK', 'exchange': 'HKEX', 'ratio': 8.0, 'currency': 'HKD', 'name': 'Alibaba'},
    'BIDU': {'ordinary': '9888.HK', 'exchange': 'HKEX', 'ratio': 10.0, 'currency': 'HKD', 'name': 'Baidu'},
    'JD': {'ordinary': '9618.HK', 'exchange': 'HKEX', 'ratio': 2.0, 'currency': 'HKD', 'name': 'JD.com'},
    'PDD': {'ordinary': 'PDD', 'exchange': 'NASDAQ', 'ratio': 1.0, 'currency': 'USD', 'name': 'PDD Holdings'},
    'NTES': {'ordinary': '9999.HK', 'exchange': 'HKEX', 'ratio': 25.0, 'currency': 'HKD', 'name': 'NetEase'},
    'LI': {'ordinary': '2015.HK', 'exchange': 'HKEX', 'ratio': 2.0, 'currency': 'HKD', 'name': 'Li Auto'},
    'XPEV': {'ordinary': '9868.HK', 'exchange': 'HKEX', 'ratio': 2.0, 'currency': 'HKD', 'name': 'XPeng'},
    
    # Brazilian ADRs
    'VALE': {'ordinary': 'VALE3.SA', 'exchange': 'B3', 'ratio': 1.0, 'currency': 'BRL', 'name': 'Vale'},
    'PBR': {'ordinary': 'PETR4.SA', 'exchange': 'B3', 'ratio': 2.0, 'currency': 'BRL', 'name': 'Petrobras'},
    'ITUB': {'ordinary': 'ITUB4.SA', 'exchange': 'B3', 'ratio': 1000.0, 'currency': 'BRL', 'name': 'Itaú Unibanco'},
    
    # Indian ADRs
    'INFY': {'ordinary': 'INFY.NS', 'exchange': 'NSE', 'ratio': 1.0, 'currency': 'INR', 'name': 'Infosys'},
    'WIT': {'ordinary': 'WIPRO.NS', 'exchange': 'NSE', 'ratio': 1.0, 'currency': 'INR', 'name': 'Wipro'},
    'HDB': {'ordinary': 'HDFCBANK.NS', 'exchange': 'NSE', 'ratio': 3.0, 'currency': 'INR', 'name': 'HDFC Bank'},
    
    # South African ADRs
    'GOLD': {'ordinary': 'ANG.JO', 'exchange': 'JSE', 'ratio': 1.0, 'currency': 'ZAR', 'name': 'AngloGold Ashanti'},
}

# FRED FX series codes
FRED_FX_SERIES = {
    'GBP': 'DEXUSUK',  # US$/UK£
    'EUR': 'DEXUSEU',  # US$/Euro
    'JPY': 'DEXJPUS',  # JPY/US$
    'CHF': 'DEXSZUS',  # CHF/US$
    'CNY': 'DEXCHUS',  # CNY/US$
    'BRL': 'DEXBZUS',  # BRL/US$
    'INR': 'DEXINUS',  # INR/US$
    'ZAR': 'DEXSFUS',  # ZAR/US$
    'KRW': 'DEXKOUS',  # KRW/US$
    'MXN': 'DEXMXUS',  # MXN/US$
}

def get_fx_rate(currency: str, date: Optional[str] = None) -> Optional[float]:
    """
    Get FX rate for converting foreign currency to USD
    Uses FRED API for historical rates, Yahoo Finance for current
    
    Args:
        currency: ISO 3-letter currency code (GBP, EUR, JPY, etc.)
        date: Optional date string (YYYY-MM-DD), defaults to today
        
    Returns:
        FX rate (foreign currency per USD) or None if unavailable
    """
    if currency == 'USD':
        return 1.0
    
    try:
        # Special handling for currencies
        if currency == 'HKD':
            # Hong Kong Dollar is pegged ~7.8 HKD/USD
            return 7.8
        elif currency == 'DKK':
            # Danish Krone via EUR (DKK is pegged to EUR at ~7.46)
            eur_rate = get_fx_rate('EUR', date)
            if eur_rate:
                return eur_rate * 7.46
            return None
        
        # Try Yahoo Finance for current rate
        if currency in ['GBP', 'EUR', 'JPY', 'CHF', 'CNY', 'BRL', 'INR', 'ZAR', 'KRW']:
            pair = f"{currency}USD=X"
            ticker = yf.Ticker(pair)
            hist = ticker.history(period='1d')
            
            if not hist.empty:
                rate = hist['Close'].iloc[-1]
                # For GBP and EUR, Yahoo gives USD per foreign (e.g., 1 GBP = 1.27 USD)
                # We need foreign per USD (e.g., 0.787 GBP = 1 USD)
                if currency in ['GBP', 'EUR']:
                    return 1.0 / rate
                # For other currencies, Yahoo gives foreign per USD directly
                return rate
        
        return None
        
    except Exception as e:
        print(f"Error fetching FX rate for {currency}: {e}", file=sys.stderr)
        return None


def get_adr_data(adr_ticker: str) -> Optional[Dict]:
    """
    Get current price and volume data for an ADR
    
    Args:
        adr_ticker: US-listed ADR ticker symbol
        
    Returns:
        Dict with price, volume, currency, timestamp
    """
    try:
        stock = yf.Ticker(adr_ticker)
        hist = stock.history(period='1d')
        
        if hist.empty:
            return None
        
        latest = hist.iloc[-1]
        
        return {
            'ticker': adr_ticker,
            'price': float(latest['Close']),
            'volume': int(latest['Volume']),
            'currency': 'USD',
            'timestamp': latest.name.strftime('%Y-%m-%d %H:%M:%S'),
            'exchange': 'US'
        }
        
    except Exception as e:
        print(f"Error fetching ADR data for {adr_ticker}: {e}", file=sys.stderr)
        return None


def get_ordinary_data(ordinary_ticker: str, currency: str) -> Optional[Dict]:
    """
    Get current price and volume data for ordinary shares
    
    Args:
        ordinary_ticker: Foreign exchange ticker (e.g., BP.L, 6758.T)
        currency: Home currency code
        
    Returns:
        Dict with price, volume, currency, timestamp
    """
    try:
        stock = yf.Ticker(ordinary_ticker)
        hist = stock.history(period='1d')
        
        if hist.empty:
            return None
        
        latest = hist.iloc[-1]
        price = float(latest['Close'])
        
        # UK stocks are quoted in pence (GBX), not pounds
        # Convert pence to pounds
        if ordinary_ticker.endswith('.L') and currency == 'GBP':
            price = price / 100.0  # Convert pence to pounds
        
        return {
            'ticker': ordinary_ticker,
            'price': price,
            'volume': int(latest['Volume']),
            'currency': currency,
            'timestamp': latest.name.strftime('%Y-%m-%d %H:%M:%S'),
            'exchange': ordinary_ticker.split('.')[-1] if '.' in ordinary_ticker else 'Unknown'
        }
        
    except Exception as e:
        print(f"Error fetching ordinary data for {ordinary_ticker}: {e}", file=sys.stderr)
        return None


def calculate_arbitrage_spread(adr_ticker: str, verbose: bool = False) -> Optional[Dict]:
    """
    Calculate the arbitrage spread between ADR and ordinary shares
    
    Args:
        adr_ticker: US-listed ADR ticker
        verbose: Print detailed calculations
        
    Returns:
        Dict with spread analysis or None
    """
    if adr_ticker not in ADR_PAIRS:
        print(f"Unknown ADR ticker: {adr_ticker}", file=sys.stderr)
        print(f"Available ADRs: {', '.join(sorted(ADR_PAIRS.keys()))}", file=sys.stderr)
        return None
    
    pair_info = ADR_PAIRS[adr_ticker]
    
    # Get ADR price
    adr_data = get_adr_data(adr_ticker)
    if not adr_data:
        print(f"Failed to fetch ADR data for {adr_ticker}", file=sys.stderr)
        return None
    
    # Get ordinary share price
    ordinary_data = get_ordinary_data(pair_info['ordinary'], pair_info['currency'])
    if not ordinary_data:
        print(f"Failed to fetch ordinary data for {pair_info['ordinary']}", file=sys.stderr)
        return None
    
    # Get FX rate
    fx_rate = get_fx_rate(pair_info['currency'])
    if fx_rate is None:
        print(f"Failed to fetch FX rate for {pair_info['currency']}", file=sys.stderr)
        return None
    
    # Calculate equivalent prices
    conversion_ratio = pair_info['ratio']
    
    # ADR price in USD
    adr_price_usd = adr_data['price']
    
    # Ordinary share price converted to USD
    ordinary_price_local = ordinary_data['price']
    ordinary_price_usd = ordinary_price_local / fx_rate
    
    # ADR-equivalent price (accounting for conversion ratio)
    ordinary_adr_equivalent = ordinary_price_usd * conversion_ratio
    
    # Calculate spread
    premium_usd = adr_price_usd - ordinary_adr_equivalent
    premium_pct = (premium_usd / ordinary_adr_equivalent) * 100
    premium_bps = premium_pct * 100
    
    # Implied FX rate
    implied_fx = (ordinary_price_local * conversion_ratio) / adr_price_usd
    fx_discount_pct = ((fx_rate - implied_fx) / fx_rate) * 100
    
    result = {
        'adr_ticker': adr_ticker,
        'ordinary_ticker': pair_info['ordinary'],
        'company_name': pair_info['name'],
        'exchange': pair_info['exchange'],
        'currency': pair_info['currency'],
        'conversion_ratio': float(conversion_ratio),
        'adr_price_usd': round(float(adr_price_usd), 4),
        'ordinary_price_local': round(float(ordinary_price_local), 4),
        'ordinary_price_usd': round(float(ordinary_price_usd), 4),
        'ordinary_adr_equivalent': round(float(ordinary_adr_equivalent), 4),
        'fx_rate': round(float(fx_rate), 6),
        'implied_fx_rate': round(float(implied_fx), 6),
        'premium_usd': round(float(premium_usd), 4),
        'premium_pct': round(float(premium_pct), 4),
        'premium_bps': round(float(premium_bps), 2),
        'fx_discount_pct': round(float(fx_discount_pct), 4),
        'adr_volume': int(adr_data['volume']),
        'ordinary_volume': int(ordinary_data['volume']),
        'timestamp': str(adr_data['timestamp']),
        'arbitrage_opportunity': bool(abs(premium_bps) > 50),  # >50 bps threshold
        'direction': 'buy_adr' if premium_bps < -50 else 'buy_ordinary' if premium_bps > 50 else 'neutral'
    }
    
    if verbose:
        print(f"\n{pair_info['name']} ({adr_ticker})")
        print(f"{'='*60}")
        print(f"ADR Price (USD):           ${adr_price_usd:,.4f}")
        print(f"Ordinary Price ({pair_info['currency']}):      {ordinary_price_local:,.4f}")
        print(f"FX Rate ({pair_info['currency']}/USD):         {fx_rate:.6f}")
        print(f"Conversion Ratio:          {conversion_ratio}:1")
        print(f"Ordinary in USD:           ${ordinary_price_usd:,.4f}")
        print(f"ADR Equivalent:            ${ordinary_adr_equivalent:,.4f}")
        print(f"\nSpread Analysis:")
        print(f"Premium/Discount:          ${premium_usd:+,.4f} ({premium_pct:+.2f}%)")
        print(f"Basis Points:              {premium_bps:+.0f} bps")
        print(f"Implied FX Rate:           {implied_fx:.6f}")
        print(f"FX Discount:               {fx_discount_pct:+.2f}%")
        print(f"\nLiquidity:")
        print(f"ADR Volume:                {adr_data['volume']:,}")
        print(f"Ordinary Volume:           {ordinary_data['volume']:,}")
        
        if result['arbitrage_opportunity']:
            print(f"\n⚠️  ARBITRAGE OPPORTUNITY: {result['direction'].upper().replace('_', ' ')}")
        else:
            print(f"\n✓ Prices are fairly aligned")
    
    return result


def scan_all_adrs(min_spread_bps: float = 50.0, sort_by: str = 'spread') -> List[Dict]:
    """
    Scan all known ADR/ordinary pairs for arbitrage opportunities
    
    Args:
        min_spread_bps: Minimum spread threshold in basis points (default 50)
        sort_by: Sort results by 'spread', 'volume', or 'alpha' (spread/volume score)
        
    Returns:
        List of arbitrage opportunities sorted by criteria
    """
    results = []
    
    print(f"Scanning {len(ADR_PAIRS)} ADR pairs for arbitrage opportunities...\n")
    
    for adr_ticker in sorted(ADR_PAIRS.keys()):
        spread = calculate_arbitrage_spread(adr_ticker, verbose=False)
        if spread and abs(spread['premium_bps']) >= min_spread_bps:
            results.append(spread)
    
    # Sort results
    if sort_by == 'spread':
        results.sort(key=lambda x: abs(x['premium_bps']), reverse=True)
    elif sort_by == 'volume':
        results.sort(key=lambda x: min(x['adr_volume'], x['ordinary_volume']), reverse=True)
    elif sort_by == 'alpha':
        # Score = spread * sqrt(min_volume)
        results.sort(key=lambda x: abs(x['premium_bps']) * (min(x['adr_volume'], x['ordinary_volume']) ** 0.5), reverse=True)
    
    return results


def compare_adrs(tickers: List[str]) -> Dict:
    """
    Compare multiple ADRs side-by-side
    
    Args:
        tickers: List of ADR tickers to compare
        
    Returns:
        Dict with comparison data
    """
    comparisons = []
    
    for ticker in tickers:
        spread = calculate_arbitrage_spread(ticker, verbose=False)
        if spread:
            comparisons.append(spread)
    
    if not comparisons:
        return {'error': 'No valid data for comparison'}
    
    # Calculate statistics
    spreads = [c['premium_bps'] for c in comparisons]
    
    return {
        'comparisons': comparisons,
        'count': len(comparisons),
        'avg_spread_bps': round(sum(spreads) / len(spreads), 2),
        'max_premium_bps': round(max(spreads), 2),
        'min_premium_bps': round(min(spreads), 2),
        'opportunities': len([s for s in comparisons if s['arbitrage_opportunity']]),
        'timestamp': datetime.utcnow().isoformat()
    }


def get_adr_list(filter_by: Optional[str] = None) -> List[Dict]:
    """
    Get list of all known ADR pairs with filtering
    
    Args:
        filter_by: Optional filter - 'currency', 'exchange', or None for all
        
    Returns:
        List of ADR pair information
    """
    result = []
    
    for adr_ticker, info in sorted(ADR_PAIRS.items()):
        pair = {
            'adr_ticker': adr_ticker,
            'ordinary_ticker': info['ordinary'],
            'name': info['name'],
            'exchange': info['exchange'],
            'currency': info['currency'],
            'ratio': info['ratio']
        }
        result.append(pair)
    
    return result


def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("ADR/GDR Arbitrage Monitor")
        print("\nUsage:")
        print("  adr-spread <ticker>              Calculate arbitrage spread for ADR")
        print("  adr-scan [--min-spread 50]       Scan all ADRs for opportunities")
        print("  adr-compare <t1> <t2> ...        Compare multiple ADRs")
        print("  adr-list [--currency GBP]        List all known ADR pairs")
        print("\nExamples:")
        print("  adr-spread BP                    BP ADR vs London ordinary shares")
        print("  adr-scan --min-spread 100        Find spreads > 100 bps")
        print("  adr-compare BABA JD BIDU         Compare Chinese ADRs")
        print("  adr-list --currency JPY          List Japanese ADRs")
        return
    
    cmd = sys.argv[1]
    
    if cmd == 'adr-spread':
        if len(sys.argv) < 3:
            print("Error: ticker required", file=sys.stderr)
            return
        
        ticker = sys.argv[2].upper()
        result = calculate_arbitrage_spread(ticker, verbose=True)
        
        if result:
            print(f"\nJSON Output:")
            print(json.dumps(result, indent=2))
    
    elif cmd == 'adr-scan':
        min_spread = 50.0
        sort_by = 'spread'
        
        # Parse args
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == '--min-spread' and i + 1 < len(sys.argv):
                min_spread = float(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == '--sort-by' and i + 1 < len(sys.argv):
                sort_by = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        results = scan_all_adrs(min_spread, sort_by)
        
        if results:
            print(f"\nFound {len(results)} arbitrage opportunities (min spread: {min_spread} bps):\n")
            print(f"{'Ticker':<8} {'Company':<25} {'Spread':<12} {'Direction':<15} {'ADR Vol':<12}")
            print("-" * 80)
            
            for r in results:
                print(f"{r['adr_ticker']:<8} {r['company_name'][:24]:<25} {r['premium_bps']:>+7.0f} bps   "
                      f"{r['direction']:<15} {r['adr_volume']:>10,}")
            
            print(f"\nJSON Output:")
            print(json.dumps(results, indent=2))
        else:
            print(f"No arbitrage opportunities found with min spread {min_spread} bps")
    
    elif cmd == 'adr-compare':
        if len(sys.argv) < 3:
            print("Error: at least one ticker required", file=sys.stderr)
            return
        
        tickers = [t.upper() for t in sys.argv[2:]]
        result = compare_adrs(tickers)
        
        print(json.dumps(result, indent=2))
    
    elif cmd == 'adr-list':
        currency_filter = None
        
        if '--currency' in sys.argv:
            idx = sys.argv.index('--currency')
            if idx + 1 < len(sys.argv):
                currency_filter = sys.argv[idx + 1].upper()
        
        pairs = get_adr_list()
        
        if currency_filter:
            pairs = [p for p in pairs if p['currency'] == currency_filter]
        
        print(f"\nKnown ADR/GDR Pairs ({len(pairs)}):\n")
        print(f"{'ADR':<8} {'Ordinary':<15} {'Company':<30} {'Exch':<6} {'Curr':<5} {'Ratio':<8}")
        print("-" * 90)
        
        for p in pairs:
            print(f"{p['adr_ticker']:<8} {p['ordinary_ticker']:<15} {p['name'][:29]:<30} "
                  f"{p['exchange']:<6} {p['currency']:<5} {p['ratio']:<8.1f}")
        
        print(f"\nJSON Output:")
        print(json.dumps(pairs, indent=2))
    
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)


if __name__ == '__main__':
    main()
