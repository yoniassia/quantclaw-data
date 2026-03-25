#!/usr/bin/env python3
"""
V3 Alpha Picker — Live Signal Generator
Runs on 1st and 15th of each month
Outputs: new picks, pyramid signals, exit signals
"""

import json, os, sys, sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent / 'modules'))

DB_PATH = Path(__file__).parent / 'data' / 'live_portfolio.db'
SA_PICKS_PATH = Path(__file__).parent / 'data' / 'stock_picks.csv'
SIGNALS_DIR = Path(__file__).parent / 'data' / 'signals'
SIGNALS_DIR.mkdir(exist_ok=True)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        entry_date TEXT NOT NULL,
        entry_price REAL NOT NULL,
        shares REAL NOT NULL,
        cost REAL NOT NULL,
        avg_entry REAL NOT NULL,
        pyramid_level INTEGER DEFAULT 0,
        status TEXT DEFAULT 'open',
        exit_date TEXT,
        exit_price REAL,
        exit_reason TEXT,
        pnl REAL,
        sector TEXT,
        v3_score REAL
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        type TEXT NOT NULL,
        ticker TEXT NOT NULL,
        action TEXT NOT NULL,
        price REAL,
        amount REAL,
        reason TEXT,
        executed INTEGER DEFAULT 0
    )''')
    conn.commit()
    return conn


def get_sa_portfolio():
    """Get tickers already in SA Quant portfolio"""
    import csv
    tickers = set()
    with open(SA_PICKS_PATH) as f:
        for row in csv.DictReader(f):
            tickers.add(row['Symbol'])
    return tickers


def get_open_positions(conn):
    """Get all open positions"""
    cursor = conn.execute(
        'SELECT id, ticker, entry_date, entry_price, shares, cost, avg_entry, pyramid_level, sector, v3_score '
        'FROM positions WHERE status = "open"'
    )
    positions = []
    for row in cursor:
        positions.append({
            'id': row[0], 'ticker': row[1], 'entry_date': row[2],
            'entry_price': row[3], 'shares': row[4], 'cost': row[5],
            'avg_entry': row[6], 'pyramid_level': row[7],
            'sector': row[8], 'v3_score': row[9]
        })
    return positions


def get_current_price(ticker):
    """Get current price via yfinance"""
    import yfinance as yf
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period='5d')
        if len(hist) > 0:
            return float(hist['Close'].iloc[-1])
    except:
        pass
    return None


def run_signal():
    today = datetime.now().strftime('%Y-%m-%d')
    conn = init_db()
    
    print(f"{'='*60}")
    print(f"V3 ALPHA PICKER — LIVE SIGNAL")
    print(f"Date: {today}")
    print(f"{'='*60}")
    
    # Load V3 scorer
    from alpha_picker import AlphaPickerV3
    picker = AlphaPickerV3()
    
    sa_portfolio = get_sa_portfolio()
    open_positions = get_open_positions(conn)
    held_tickers = set(p['ticker'] for p in open_positions)
    
    signals = []
    
    # ===== STEP 1: CHECK EXITS =====
    print("\n📤 CHECKING EXITS...")
    for pos in open_positions:
        ticker = pos['ticker']
        current_price = get_current_price(ticker)
        if current_price is None:
            print(f"  ⚠️ {ticker}: Could not get price, skipping")
            continue
        
        avg_entry = pos['avg_entry']
        change_pct = (current_price - avg_entry) / avg_entry
        entry_date = datetime.strptime(pos['entry_date'], '%Y-%m-%d')
        hold_days = (datetime.now() - entry_date).days
        
        exit_reason = None
        
        # Stop loss: -15%
        if change_pct <= -0.15:
            exit_reason = f"STOP LOSS (-15%) | Down {change_pct*100:.1f}%"
        
        # Take profit: +150%
        elif change_pct >= 1.50:
            exit_reason = f"TAKE PROFIT (+150%) | Up {change_pct*100:.1f}%"
        
        # Time exit: 6 months
        elif hold_days >= 180:
            exit_reason = f"TIME EXIT (6mo) | Held {hold_days} days | {change_pct*100:+.1f}%"
        
        # Score exit: V3 score below 15
        else:
            try:
                result = picker.score_stock(ticker)
                current_score = result.get('score', 0) if isinstance(result, dict) else 0
                if current_score < 15:
                    exit_reason = f"SCORE EXIT (V3={current_score} < 15) | {change_pct*100:+.1f}%"
            except:
                pass
        
        if exit_reason:
            pnl = pos['shares'] * (current_price - avg_entry)
            signals.append({
                'type': 'EXIT',
                'ticker': ticker,
                'action': 'SELL',
                'price': current_price,
                'shares': pos['shares'],
                'cost': pos['cost'],
                'pnl': pnl,
                'reason': exit_reason
            })
            print(f"  🔴 {ticker}: {exit_reason} → SELL {pos['shares']:.0f} shares @ ${current_price:.2f} | P&L: ${pnl:+,.0f}")
        else:
            print(f"  ✅ {ticker}: Hold | {change_pct*100:+.1f}% | {hold_days}d | Pyr:{pos['pyramid_level']}")
    
    # ===== STEP 2: CHECK PYRAMIDS =====
    print("\n📈 CHECKING PYRAMIDS...")
    pyramid_thresholds = [(0.10, 5000, 1), (0.20, 5000, 2), (0.35, 5000, 3)]
    
    # Filter out positions we're exiting
    exit_tickers = set(s['ticker'] for s in signals if s['type'] == 'EXIT')
    
    for pos in open_positions:
        ticker = pos['ticker']
        if ticker in exit_tickers:
            continue
        
        current_price = get_current_price(ticker)
        if current_price is None:
            continue
        
        avg_entry = pos['avg_entry']
        change_pct = (current_price - avg_entry) / avg_entry
        current_level = pos['pyramid_level']
        
        for threshold, amount, level in pyramid_thresholds:
            if current_level < level and change_pct >= threshold:
                add_shares = amount / current_price
                new_total_cost = pos['cost'] + amount
                new_total_shares = pos['shares'] + add_shares
                new_avg_entry = new_total_cost / new_total_shares
                
                signals.append({
                    'type': 'PYRAMID',
                    'ticker': ticker,
                    'action': 'BUY',
                    'price': current_price,
                    'amount': amount,
                    'shares_to_add': add_shares,
                    'level': level,
                    'reason': f"PYRAMID L{level} (up {change_pct*100:.1f}% ≥ {threshold*100:.0f}%) | New avg: ${new_avg_entry:.2f}"
                })
                print(f"  🟢 {ticker}: Pyramid L{level} | Up {change_pct*100:.1f}% | ADD ${amount:,} ({add_shares:.1f} shares @ ${current_price:.2f})")
                break  # Only one pyramid level per rebalance
    
    # ===== STEP 3: NEW PICK =====
    print("\n🎯 SCORING UNIVERSE FOR NEW PICK...")
    results = picker.get_top_picks(n=50)
    
    new_pick = None
    for r in results:
        ticker = r.get('ticker', '')
        if ticker in sa_portfolio:
            continue
        if ticker in held_tickers:
            continue
        if ticker in exit_tickers:
            continue
        
        # Sector check: max 3 per sector
        sector = r.get('sector', 'Unknown')
        sector_count = sum(1 for p in open_positions 
                          if p['sector'] == sector and p['ticker'] not in exit_tickers)
        if sector_count >= 3:
            continue
        
        current_price = get_current_price(ticker)
        if current_price is None:
            continue
        
        new_pick = {
            'type': 'ENTRY',
            'ticker': ticker,
            'action': 'BUY',
            'price': current_price,
            'amount': 5000,
            'shares': 5000 / current_price,
            'score': r.get('score', 0),
            'sector': sector,
            'reason': f"V3 Top Pick | Score: {r.get('score', 0)} | {sector} | MCap: ${r.get('mcap_b', 0):.1f}B"
        }
        signals.append(new_pick)
        print(f"  🎯 NEW PICK: {ticker} | Score: {r.get('score', 0)} | {sector} | ${current_price:.2f} | Buy {5000/current_price:.1f} shares")
        break
    
    if not new_pick:
        print("  ⚠️ No new pick found (all filtered out)")
    
    # ===== GENERATE SIGNAL REPORT =====
    print(f"\n{'='*60}")
    print("📋 SIGNAL SUMMARY")
    print(f"{'='*60}")
    
    report_lines = []
    report_lines.append(f"*📈 V3 Alpha Picker — Signal Report*")
    report_lines.append(f"*{today}*")
    report_lines.append("")
    
    exits = [s for s in signals if s['type'] == 'EXIT']
    pyramids = [s for s in signals if s['type'] == 'PYRAMID']
    entries = [s for s in signals if s['type'] == 'ENTRY']
    
    if exits:
        report_lines.append("*🔴 EXITS:*")
        for s in exits:
            report_lines.append(f"• SELL *{s['ticker']}* — {s['shares']:.0f} shares @ ${s['price']:.2f}")
            report_lines.append(f"  {s['reason']} | P&L: ${s['pnl']:+,.0f}")
        report_lines.append("")
    
    if pyramids:
        report_lines.append("*🟢 PYRAMIDS:*")
        for s in pyramids:
            report_lines.append(f"• BUY *{s['ticker']}* — ${s['amount']:,.0f} ({s['shares_to_add']:.1f} shares @ ${s['price']:.2f})")
            report_lines.append(f"  {s['reason']}")
        report_lines.append("")
    
    if entries:
        report_lines.append("*🎯 NEW ENTRY:*")
        for s in entries:
            report_lines.append(f"• BUY *{s['ticker']}* — ${s['amount']:,.0f} ({s['shares']:.1f} shares @ ${s['price']:.2f})")
            report_lines.append(f"  {s['reason']}")
        report_lines.append("")
    
    if not signals:
        report_lines.append("No signals today — all positions holding steady ✅")
    
    # Portfolio summary
    report_lines.append("*📊 Portfolio:*")
    active = [p for p in open_positions if p['ticker'] not in exit_tickers]
    total_cost = sum(p['cost'] for p in active)
    report_lines.append(f"• Open positions: {len(active)} (+{len(entries)} new, -{len(exits)} exits)")
    report_lines.append(f"• Capital deployed: ${total_cost:,.0f}")
    
    report = "\n".join(report_lines)
    print(report)
    
    # Save signal to file
    signal_file = SIGNALS_DIR / f"signal_{today}.json"
    with open(signal_file, 'w') as f:
        json.dump({
            'date': today,
            'signals': signals,
            'portfolio': [p for p in open_positions],
            'report': report
        }, f, indent=2, default=str)
    
    print(f"\n✅ Signal saved to {signal_file}")
    
    # Save signals to DB
    for s in signals:
        conn.execute(
            'INSERT INTO signals (date, type, ticker, action, price, amount, reason) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (today, s['type'], s['ticker'], s['action'], s.get('price'), s.get('amount', s.get('cost', 0)), s.get('reason'))
        )
    conn.commit()
    conn.close()
    
    # Output report for WhatsApp
    print("\n---WHATSAPP_REPORT_START---")
    print(report)
    print("---WHATSAPP_REPORT_END---")
    
    return signals


if __name__ == '__main__':
    run_signal()
