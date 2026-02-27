#!/usr/bin/env python3
"""
PAPER TRADING ENGINE — Real-time P&L tracking with live prices
Track positions, execute paper trades, analyze performance metrics
"""

import sqlite3
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
import threading
import yfinance as yf
import requests
import numpy as np

# Database path
DB_PATH = Path(__file__).parent.parent / 'data' / 'paper_trading.db'
DB_PATH.parent.mkdir(exist_ok=True)

# Thread lock for concurrent access
db_lock = threading.Lock()

# Fee structure
STOCK_COMMISSION = 0.0  # $0 like Robinhood
CRYPTO_COMMISSION = 0.001  # 0.1%
MARKET_ORDER_SLIPPAGE = 0.0005  # 0.05%


def get_db():
    """Get thread-safe database connection"""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database schema"""
    with db_lock:
        conn = get_db()
        cursor = conn.cursor()
        
        # Portfolios table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                initial_cash REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Positions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                quantity REAL NOT NULL,
                avg_cost REAL NOT NULL,
                opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
                UNIQUE(portfolio_id, ticker)
            )
        ''')
        
        # Orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                side TEXT NOT NULL,
                type TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                filled_at TIMESTAMP,
                filled_price REAL,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id)
            )
        ''')
        
        # Trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                fees REAL NOT NULL,
                pnl REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id)
            )
        ''')
        
        # Daily snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                date DATE NOT NULL,
                equity REAL NOT NULL,
                cash REAL NOT NULL,
                unrealized_pnl REAL NOT NULL,
                realized_pnl REAL NOT NULL,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
                UNIQUE(portfolio_id, date)
            )
        ''')
        
        conn.commit()
        conn.close()


def is_crypto(ticker):
    """Check if ticker is a cryptocurrency"""
    crypto_suffixes = ['-USD', '-USDT', '-BUSD']
    crypto_tickers = ['BTC-USD', 'ETH-USD', 'USDT-USD', 'BNB-USD', 'ADA-USD', 'DOGE-USD', 'XRP-USD', 'SOL-USD']
    return any(ticker.endswith(suffix) for suffix in crypto_suffixes) or ticker.upper() in crypto_tickers


def get_live_price(ticker):
    """Get live price from yfinance (stocks) or CoinGecko (crypto)"""
    try:
        if is_crypto(ticker):
            # Try CoinGecko for crypto
            coin_id = ticker.replace('-USD', '').replace('-USDT', '').lower()
            coin_map = {'btc': 'bitcoin', 'eth': 'ethereum', 'usdt': 'tether', 'bnb': 'binancecoin', 
                       'ada': 'cardano', 'doge': 'dogecoin', 'xrp': 'ripple', 'sol': 'solana'}
            coin_id = coin_map.get(coin_id, coin_id)
            
            url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd'
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if coin_id in data:
                    return data[coin_id]['usd']
        
        # Fallback to yfinance
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Try different price fields
        price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
        if price:
            return float(price)
            
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}", file=sys.stderr)
    
    return None


def create_portfolio(name, initial_cash=100000):
    """Create a new portfolio"""
    init_db()
    with db_lock:
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO portfolios (name, initial_cash) VALUES (?, ?)', 
                         (name, initial_cash))
            conn.commit()
            portfolio_id = cursor.lastrowid
            conn.close()
            
            return {
                'success': True,
                'portfolio_id': portfolio_id,
                'name': name,
                'initial_cash': initial_cash,
                'message': f'Portfolio "{name}" created with ${initial_cash:,.2f}'
            }
        except sqlite3.IntegrityError:
            return {'success': False, 'error': f'Portfolio "{name}" already exists'}


def get_or_create_default_portfolio():
    """Get or create the default portfolio"""
    init_db()
    
    # First check without lock
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM portfolios WHERE name = ?', ('default',))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row[0]
    
    # Create default portfolio (this will use its own lock)
    result = create_portfolio('default', 100000)
    if result.get('success'):
        return result['portfolio_id']
    
    # If creation failed because it was just created by another thread,
    # try getting it again
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM portfolios WHERE name = ?', ('default',))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row[0]
    
    raise Exception("Could not create or get default portfolio")


def get_portfolio_id(name):
    """Get portfolio ID by name"""
    init_db()
    with db_lock:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM portfolios WHERE name = ?', (name,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return row[0]
        return None


def get_cash_balance(portfolio_id):
    """Calculate current cash balance"""
    with db_lock:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get initial cash
        cursor.execute('SELECT initial_cash FROM portfolios WHERE id = ?', (portfolio_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return 0
        
        cash = row[0]
        
        # Subtract all trade costs (buy side)
        cursor.execute('''
            SELECT SUM((price * quantity) + fees) FROM trades 
            WHERE portfolio_id = ? AND side = 'buy'
        ''', (portfolio_id,))
        row = cursor.fetchone()
        if row[0]:
            cash -= row[0]
        
        # Add all trade proceeds (sell side)
        cursor.execute('''
            SELECT SUM((price * quantity) - fees) FROM trades 
            WHERE portfolio_id = ? AND side = 'sell'
        ''', (portfolio_id,))
        row = cursor.fetchone()
        if row[0]:
            cash += row[0]
        
        conn.close()
        return cash


def execute_trade(portfolio_id, ticker, side, quantity, order_type='market', limit_price=None):
    """Execute a paper trade"""
    init_db()
    
    # Get current price
    current_price = get_live_price(ticker)
    if not current_price:
        return {'success': False, 'error': f'Could not fetch price for {ticker}'}
    
    # Calculate execution price
    if order_type == 'market':
        # Apply slippage
        slippage = current_price * MARKET_ORDER_SLIPPAGE
        exec_price = current_price + slippage if side == 'buy' else current_price - slippage
    elif order_type == 'limit':
        if not limit_price:
            return {'success': False, 'error': 'Limit price required for limit orders'}
        
        # Check if limit order can be filled
        if side == 'buy' and limit_price < current_price:
            return {'success': False, 'error': f'Buy limit ${limit_price:.2f} below market ${current_price:.2f}'}
        if side == 'sell' and limit_price > current_price:
            return {'success': False, 'error': f'Sell limit ${limit_price:.2f} above market ${current_price:.2f}'}
        
        exec_price = limit_price
    else:
        return {'success': False, 'error': f'Unknown order type: {order_type}'}
    
    # Calculate fees
    fee_rate = CRYPTO_COMMISSION if is_crypto(ticker) else STOCK_COMMISSION
    fees = exec_price * quantity * fee_rate
    
    # Check if we have enough cash for buys
    if side == 'buy':
        cash = get_cash_balance(portfolio_id)
        cost = (exec_price * quantity) + fees
        if cost > cash:
            return {'success': False, 'error': f'Insufficient funds: ${cash:.2f} available, ${cost:.2f} needed'}
    
    # Check if we have enough shares for sells
    if side == 'sell':
        with db_lock:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT quantity FROM positions WHERE portfolio_id = ? AND ticker = ?', 
                         (portfolio_id, ticker))
            row = cursor.fetchone()
            conn.close()
            
            if not row or row[0] < quantity:
                held = row[0] if row else 0
                return {'success': False, 'error': f'Insufficient shares: {held} held, {quantity} needed'}
    
    # Calculate P&L for sells
    pnl = None
    if side == 'sell':
        with db_lock:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT avg_cost FROM positions WHERE portfolio_id = ? AND ticker = ?', 
                         (portfolio_id, ticker))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                avg_cost = row[0]
                pnl = (exec_price - avg_cost) * quantity - fees
    
    # Record the trade
    with db_lock:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO trades (portfolio_id, ticker, side, quantity, price, fees, pnl)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (portfolio_id, ticker, side, quantity, exec_price, fees, pnl))
        
        # Update position
        if side == 'buy':
            # Check if position exists
            cursor.execute('SELECT quantity, avg_cost FROM positions WHERE portfolio_id = ? AND ticker = ?',
                         (portfolio_id, ticker))
            row = cursor.fetchone()
            
            if row:
                # Update existing position
                old_qty, old_cost = row
                new_qty = old_qty + quantity
                new_cost = ((old_qty * old_cost) + (quantity * exec_price)) / new_qty
                cursor.execute('''
                    UPDATE positions SET quantity = ?, avg_cost = ?
                    WHERE portfolio_id = ? AND ticker = ?
                ''', (new_qty, new_cost, portfolio_id, ticker))
            else:
                # Create new position
                cursor.execute('''
                    INSERT INTO positions (portfolio_id, ticker, quantity, avg_cost)
                    VALUES (?, ?, ?, ?)
                ''', (portfolio_id, ticker, quantity, exec_price))
        
        elif side == 'sell':
            # Reduce position
            cursor.execute('SELECT quantity FROM positions WHERE portfolio_id = ? AND ticker = ?',
                         (portfolio_id, ticker))
            row = cursor.fetchone()
            
            if row:
                new_qty = row[0] - quantity
                if new_qty <= 0.0001:  # Close to zero
                    cursor.execute('DELETE FROM positions WHERE portfolio_id = ? AND ticker = ?',
                                 (portfolio_id, ticker))
                else:
                    cursor.execute('UPDATE positions SET quantity = ? WHERE portfolio_id = ? AND ticker = ?',
                                 (new_qty, portfolio_id, ticker))
        
        conn.commit()
        trade_id = cursor.lastrowid
        conn.close()
    
    return {
        'success': True,
        'trade_id': trade_id,
        'ticker': ticker,
        'side': side,
        'quantity': quantity,
        'price': exec_price,
        'fees': fees,
        'pnl': pnl,
        'message': f'{side.upper()} {quantity} {ticker} @ ${exec_price:.2f} (fees: ${fees:.2f})'
    }


def get_positions(portfolio_id, with_live_prices=True):
    """Get all positions with live prices and P&L"""
    init_db()
    
    with db_lock:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ticker, quantity, avg_cost, opened_at FROM positions
            WHERE portfolio_id = ?
        ''', (portfolio_id,))
        rows = cursor.fetchall()
        conn.close()
    
    positions = []
    total_value = 0
    total_cost = 0
    
    for row in rows:
        ticker, quantity, avg_cost, opened_at = row
        cost_basis = quantity * avg_cost
        
        if with_live_prices:
            current_price = get_live_price(ticker)
            if current_price:
                market_value = quantity * current_price
                unrealized_pnl = market_value - cost_basis
                unrealized_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
            else:
                current_price = avg_cost
                market_value = cost_basis
                unrealized_pnl = 0
                unrealized_pct = 0
        else:
            current_price = avg_cost
            market_value = cost_basis
            unrealized_pnl = 0
            unrealized_pct = 0
        
        total_value += market_value
        total_cost += cost_basis
        
        positions.append({
            'ticker': ticker,
            'quantity': quantity,
            'avg_cost': avg_cost,
            'current_price': current_price,
            'cost_basis': cost_basis,
            'market_value': market_value,
            'unrealized_pnl': unrealized_pnl,
            'unrealized_pct': unrealized_pct,
            'opened_at': opened_at
        })
    
    cash = get_cash_balance(portfolio_id)
    total_equity = total_value + cash
    
    return {
        'positions': positions,
        'cash': cash,
        'total_value': total_value,
        'total_equity': total_equity,
        'total_unrealized_pnl': total_value - total_cost
    }


def get_pnl_summary(portfolio_id):
    """Get comprehensive P&L summary"""
    init_db()
    
    # Get portfolio info
    with db_lock:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT name, initial_cash, created_at FROM portfolios WHERE id = ?', (portfolio_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return {'error': 'Portfolio not found'}
        
        name, initial_cash, created_at = row
        
        # Get realized P&L
        cursor.execute('''
            SELECT SUM(pnl) FROM trades WHERE portfolio_id = ? AND side = 'sell'
        ''', (portfolio_id,))
        row = cursor.fetchone()
        realized_pnl = row[0] or 0
        
        # Get trade stats
        cursor.execute('''
            SELECT COUNT(*), SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END),
                   AVG(CASE WHEN pnl > 0 THEN pnl END),
                   AVG(CASE WHEN pnl < 0 THEN pnl END)
            FROM trades WHERE portfolio_id = ? AND side = 'sell' AND pnl IS NOT NULL
        ''', (portfolio_id,))
        row = cursor.fetchone()
        
        total_trades, winning_trades, avg_win, avg_loss = row
        total_trades = total_trades or 0
        winning_trades = winning_trades or 0
        avg_win = avg_win or 0
        avg_loss = avg_loss or 0
        
        conn.close()
    
    # Get current positions
    pos_data = get_positions(portfolio_id, with_live_prices=True)
    unrealized_pnl = pos_data['total_unrealized_pnl']
    total_equity = pos_data['total_equity']
    
    # Calculate metrics
    total_return = ((total_equity - initial_cash) / initial_cash * 100) if initial_cash > 0 else 0
    
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    # Calculate Sharpe ratio (simplified - would need daily returns for accurate calculation)
    sharpe_ratio = 0
    if total_trades > 5:
        # Get daily snapshots
        with db_lock:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT equity FROM daily_snapshots 
                WHERE portfolio_id = ? ORDER BY date
            ''', (portfolio_id,))
            rows = cursor.fetchall()
            conn.close()
            
            if len(rows) > 1:
                equities = [row[0] for row in rows]
                returns = np.diff(equities) / equities[:-1]
                if len(returns) > 0:
                    sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if np.std(returns) > 0 else 0
    
    # Calculate max drawdown
    max_drawdown = 0
    if total_trades > 0:
        with db_lock:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT equity FROM daily_snapshots 
                WHERE portfolio_id = ? ORDER BY date
            ''', (portfolio_id,))
            rows = cursor.fetchall()
            conn.close()
            
            if len(rows) > 1:
                equities = [row[0] for row in rows]
                peak = equities[0]
                for equity in equities:
                    if equity > peak:
                        peak = equity
                    drawdown = (peak - equity) / peak * 100 if peak > 0 else 0
                    max_drawdown = max(max_drawdown, drawdown)
    
    # Profit factor
    gross_wins = winning_trades * avg_win if avg_win > 0 else 0
    gross_losses = abs((total_trades - winning_trades) * avg_loss) if avg_loss < 0 else 0.01
    profit_factor = gross_wins / gross_losses if gross_losses > 0 else 0
    
    # Exposure
    exposure_pct = (pos_data['total_value'] / total_equity * 100) if total_equity > 0 else 0
    
    # Largest position
    largest_position_pct = 0
    if pos_data['positions']:
        largest_value = max(p['market_value'] for p in pos_data['positions'])
        largest_position_pct = (largest_value / total_equity * 100) if total_equity > 0 else 0
    
    return {
        'portfolio_name': name,
        'initial_cash': initial_cash,
        'current_equity': total_equity,
        'cash': pos_data['cash'],
        'total_return_pct': total_return,
        'realized_pnl': realized_pnl,
        'unrealized_pnl': unrealized_pnl,
        'total_pnl': realized_pnl + unrealized_pnl,
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'win_rate_pct': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown_pct': max_drawdown,
        'current_exposure_pct': exposure_pct,
        'largest_position_pct': largest_position_pct,
        'created_at': created_at
    }


def get_trade_history(portfolio_id, days=30):
    """Get trade history"""
    init_db()
    
    cutoff = datetime.now() - timedelta(days=days)
    
    with db_lock:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ticker, side, quantity, price, fees, pnl, timestamp
            FROM trades WHERE portfolio_id = ? AND timestamp >= ?
            ORDER BY timestamp DESC
        ''', (portfolio_id, cutoff))
        rows = cursor.fetchall()
        conn.close()
    
    trades = []
    for row in rows:
        ticker, side, quantity, price, fees, pnl, timestamp = row
        trades.append({
            'ticker': ticker,
            'side': side,
            'quantity': quantity,
            'price': price,
            'fees': fees,
            'pnl': pnl,
            'timestamp': timestamp
        })
    
    return {'trades': trades, 'count': len(trades)}


def take_snapshot(portfolio_id):
    """Take a daily snapshot of portfolio value"""
    init_db()
    
    pos_data = get_positions(portfolio_id, with_live_prices=True)
    
    # Get realized P&L
    with db_lock:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COALESCE(SUM(pnl), 0) FROM trades 
            WHERE portfolio_id = ? AND side = 'sell'
        ''', (portfolio_id,))
        row = cursor.fetchone()
        realized_pnl = row[0]
        
        # Insert or update snapshot
        today = datetime.now().date()
        cursor.execute('''
            INSERT OR REPLACE INTO daily_snapshots 
            (portfolio_id, date, equity, cash, unrealized_pnl, realized_pnl)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (portfolio_id, today, pos_data['total_equity'], pos_data['cash'], 
              pos_data['total_unrealized_pnl'], realized_pnl))
        
        conn.commit()
        conn.close()
    
    return {
        'success': True,
        'date': str(today),
        'equity': pos_data['total_equity'],
        'message': f'Snapshot taken: ${pos_data["total_equity"]:,.2f}'
    }


def get_equity_curve(portfolio_id):
    """Get equity curve for ASCII chart"""
    init_db()
    
    with db_lock:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT date, equity FROM daily_snapshots
            WHERE portfolio_id = ? ORDER BY date
        ''', (portfolio_id,))
        rows = cursor.fetchall()
        conn.close()
    
    if not rows:
        return {'error': 'No snapshots found. Run: python cli.py paper-snapshot'}
    
    points = [{'date': row[0], 'equity': row[1]} for row in rows]
    
    # Generate ASCII chart
    width = 60
    height = 15
    
    values = [p['equity'] for p in points]
    min_val = min(values)
    max_val = max(values)
    
    chart_lines = []
    for i in range(height):
        line = []
        threshold = max_val - (max_val - min_val) * i / height
        for val in values:
            line.append('█' if val >= threshold else ' ')
        chart_lines.append(''.join(line))
    
    chart = '\n'.join(chart_lines)
    
    return {
        'points': points,
        'ascii_chart': chart,
        'min': min_val,
        'max': max_val
    }


# CLI handlers
def handle_create(args):
    """CLI: Create portfolio"""
    if len(args) < 1:
        return {'error': 'Usage: paper-create <name> [--cash 100000]'}
    
    name = args[0]
    cash = 100000
    
    if '--cash' in args:
        idx = args.index('--cash')
        if idx + 1 < len(args):
            cash = float(args[idx + 1])
    
    return create_portfolio(name, cash)


def handle_buy(args):
    """CLI: Buy"""
    if len(args) < 2:
        return {'error': 'Usage: paper-buy <ticker> <qty> [--limit price] [--portfolio default]'}
    
    ticker = args[0].upper()
    quantity = float(args[1])
    
    portfolio_name = 'default'
    limit_price = None
    order_type = 'market'
    
    if '--portfolio' in args:
        idx = args.index('--portfolio')
        if idx + 1 < len(args):
            portfolio_name = args[idx + 1]
    
    if '--limit' in args:
        idx = args.index('--limit')
        if idx + 1 < len(args):
            limit_price = float(args[idx + 1])
            order_type = 'limit'
    
    portfolio_id = get_portfolio_id(portfolio_name)
    if not portfolio_id:
        portfolio_id = get_or_create_default_portfolio()
    
    return execute_trade(portfolio_id, ticker, 'buy', quantity, order_type, limit_price)


def handle_sell(args):
    """CLI: Sell"""
    if len(args) < 2:
        return {'error': 'Usage: paper-sell <ticker> <qty> [--limit price] [--portfolio default]'}
    
    ticker = args[0].upper()
    quantity = float(args[1])
    
    portfolio_name = 'default'
    limit_price = None
    order_type = 'market'
    
    if '--portfolio' in args:
        idx = args.index('--portfolio')
        if idx + 1 < len(args):
            portfolio_name = args[idx + 1]
    
    if '--limit' in args:
        idx = args.index('--limit')
        if idx + 1 < len(args):
            limit_price = float(args[idx + 1])
            order_type = 'limit'
    
    portfolio_id = get_portfolio_id(portfolio_name)
    if not portfolio_id:
        return {'error': 'Portfolio not found'}
    
    return execute_trade(portfolio_id, ticker, 'sell', quantity, order_type, limit_price)


def handle_positions(args):
    """CLI: Show positions"""
    portfolio_name = 'default'
    
    if '--portfolio' in args:
        idx = args.index('--portfolio')
        if idx + 1 < len(args):
            portfolio_name = args[idx + 1]
    
    portfolio_id = get_portfolio_id(portfolio_name)
    if not portfolio_id:
        portfolio_id = get_or_create_default_portfolio()
    
    return get_positions(portfolio_id, with_live_prices=True)


def handle_pnl(args):
    """CLI: Show P&L"""
    portfolio_name = 'default'
    
    if '--portfolio' in args:
        idx = args.index('--portfolio')
        if idx + 1 < len(args):
            portfolio_name = args[idx + 1]
    
    portfolio_id = get_portfolio_id(portfolio_name)
    if not portfolio_id:
        portfolio_id = get_or_create_default_portfolio()
    
    return get_pnl_summary(portfolio_id)


def handle_trades(args):
    """CLI: Show trade history"""
    portfolio_name = 'default'
    days = 30
    
    if '--portfolio' in args:
        idx = args.index('--portfolio')
        if idx + 1 < len(args):
            portfolio_name = args[idx + 1]
    
    if '--days' in args:
        idx = args.index('--days')
        if idx + 1 < len(args):
            days = int(args[idx + 1])
    
    portfolio_id = get_portfolio_id(portfolio_name)
    if not portfolio_id:
        return {'error': 'Portfolio not found'}
    
    return get_trade_history(portfolio_id, days)


def handle_snapshot(args):
    """CLI: Take snapshot"""
    portfolio_name = 'default'
    
    if '--portfolio' in args:
        idx = args.index('--portfolio')
        if idx + 1 < len(args):
            portfolio_name = args[idx + 1]
    
    portfolio_id = get_portfolio_id(portfolio_name)
    if not portfolio_id:
        portfolio_id = get_or_create_default_portfolio()
    
    return take_snapshot(portfolio_id)


def handle_chart(args):
    """CLI: Show equity curve"""
    portfolio_name = 'default'
    
    if '--portfolio' in args:
        idx = args.index('--portfolio')
        if idx + 1 < len(args):
            portfolio_name = args[idx + 1]
    
    portfolio_id = get_portfolio_id(portfolio_name)
    if not portfolio_id:
        return {'error': 'Portfolio not found'}
    
    return get_equity_curve(portfolio_id)


def handle_risk(args):
    """CLI: Show risk metrics (same as P&L)"""
    return handle_pnl(args)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'No command specified'}))
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    handlers = {
        'paper-create': handle_create,
        'paper-buy': handle_buy,
        'paper-sell': handle_sell,
        'paper-positions': handle_positions,
        'paper-pnl': handle_pnl,
        'paper-trades': handle_trades,
        'paper-snapshot': handle_snapshot,
        'paper-chart': handle_chart,
        'paper-risk': handle_risk
    }
    
    handler = handlers.get(command)
    if not handler:
        print(json.dumps({'error': f'Unknown command: {command}'}))
        sys.exit(1)
    
    try:
        result = handler(args)
        print(json.dumps(result, indent=2, default=str))
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)
