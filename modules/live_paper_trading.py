#!/usr/bin/env python3
"""
LIVE PAPER TRADING SYSTEM — SA Quant Replica Alpha Picker Strategy
Auto-rebalances on 1st and 15th of each month
15% position size, pyramid on winners, $100K starting capital
"""

import sys
import sqlite3
import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import yfinance as yf

# Import alpha picker and paper trading
from alpha_picker import AlphaPickerV3
from paper_trading import (
    init_db, get_db, db_lock, get_live_price,
    get_or_create_default_portfolio, get_cash_balance
)

# Constants
PORTFOLIO_NAME = 'sa_quant_live'
INITIAL_CASH = 100000
POSITION_SIZE = 0.15  # 15% per position
PYRAMID_THRESHOLD_1 = 0.15  # 15% gain → add 50%
PYRAMID_THRESHOLD_2 = 0.30  # 30% gain → add another 50%
STOP_LOSS_PCT = -0.15  # -15% → sell
MIN_SCORE = 35  # Minimum score to qualify as Buy+ (top tier)

DB_PATH = Path(__file__).parent.parent / 'data' / 'paper_trading.db'


class LivePaperTrader:
    """Live paper trading engine for Alpha Picker strategy"""
    
    def __init__(self):
        init_db()
        self.picker = AlphaPickerV3(initial_cash=INITIAL_CASH)
        self.portfolio_id = self._get_or_create_portfolio()
        
    def _get_or_create_portfolio(self) -> int:
        """Get or create the SA Quant Live portfolio"""
        with db_lock:
            conn = get_db()
            cursor = conn.cursor()
            
            # Check if exists
            cursor.execute('SELECT id FROM portfolios WHERE name = ?', (PORTFOLIO_NAME,))
            row = cursor.fetchone()
            
            if row:
                portfolio_id = row[0]
            else:
                # Create it
                cursor.execute(
                    'INSERT INTO portfolios (name, initial_cash) VALUES (?, ?)',
                    (PORTFOLIO_NAME, INITIAL_CASH)
                )
                conn.commit()
                portfolio_id = cursor.lastrowid
                
            conn.close()
            return portfolio_id
    
    def get_current_positions(self) -> List[Dict]:
        """Get current portfolio positions with live P&L"""
        with db_lock:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ticker, quantity, avg_cost, opened_at 
                FROM positions 
                WHERE portfolio_id = ? AND quantity > 0
            ''', (self.portfolio_id,))
            
            positions = []
            for row in cursor.fetchall():
                ticker = row[0]
                quantity = row[1]
                avg_cost = row[2]
                opened_at = row[3]
                
                # Get live price
                current_price = get_live_price(ticker)
                if current_price is None:
                    current_price = avg_cost
                
                cost_basis = quantity * avg_cost
                market_value = quantity * current_price
                unrealized_pnl = market_value - cost_basis
                pnl_pct = (current_price / avg_cost - 1) * 100
                
                positions.append({
                    'ticker': ticker,
                    'quantity': quantity,
                    'avg_cost': avg_cost,
                    'current_price': current_price,
                    'cost_basis': cost_basis,
                    'market_value': market_value,
                    'unrealized_pnl': unrealized_pnl,
                    'pnl_pct': pnl_pct,
                    'opened_at': opened_at
                })
            
            conn.close()
            return positions
    
    def execute_trade(self, ticker: str, side: str, quantity: float, price: float, 
                     reason: str = '') -> Dict:
        """Execute a paper trade and log it"""
        with db_lock:
            conn = get_db()
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            
            if side == 'buy':
                # Add or update position
                cursor.execute('''
                    SELECT quantity, avg_cost FROM positions 
                    WHERE portfolio_id = ? AND ticker = ?
                ''', (self.portfolio_id, ticker))
                row = cursor.fetchone()
                
                if row:
                    # Existing position - calculate new average cost
                    old_qty = row[0]
                    old_cost = row[1]
                    new_qty = old_qty + quantity
                    new_avg_cost = (old_qty * old_cost + quantity * price) / new_qty
                    
                    cursor.execute('''
                        UPDATE positions 
                        SET quantity = ?, avg_cost = ? 
                        WHERE portfolio_id = ? AND ticker = ?
                    ''', (new_qty, new_avg_cost, self.portfolio_id, ticker))
                else:
                    # New position
                    cursor.execute('''
                        INSERT INTO positions (portfolio_id, ticker, quantity, avg_cost, opened_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (self.portfolio_id, ticker, quantity, price, timestamp))
                
                # Log trade
                cursor.execute('''
                    INSERT INTO trades (portfolio_id, ticker, side, quantity, price, fees, timestamp)
                    VALUES (?, ?, 'buy', ?, ?, 0, ?)
                ''', (self.portfolio_id, ticker, quantity, price, timestamp))
                
            elif side == 'sell':
                # Get current position
                cursor.execute('''
                    SELECT quantity, avg_cost FROM positions 
                    WHERE portfolio_id = ? AND ticker = ?
                ''', (self.portfolio_id, ticker))
                row = cursor.fetchone()
                
                if not row:
                    conn.close()
                    return {'success': False, 'error': f'No position in {ticker}'}
                
                current_qty = row[0]
                avg_cost = row[1]
                
                if quantity > current_qty:
                    quantity = current_qty
                
                # Calculate P&L
                pnl = quantity * (price - avg_cost)
                
                # Update or remove position
                new_qty = current_qty - quantity
                if new_qty <= 0:
                    cursor.execute('''
                        DELETE FROM positions 
                        WHERE portfolio_id = ? AND ticker = ?
                    ''', (self.portfolio_id, ticker))
                else:
                    cursor.execute('''
                        UPDATE positions 
                        SET quantity = ? 
                        WHERE portfolio_id = ? AND ticker = ?
                    ''', (new_qty, self.portfolio_id, ticker))
                
                # Log trade with P&L
                cursor.execute('''
                    INSERT INTO trades (portfolio_id, ticker, side, quantity, price, fees, pnl, timestamp)
                    VALUES (?, ?, 'sell', ?, ?, 0, ?, ?)
                ''', (self.portfolio_id, ticker, quantity, price, pnl, timestamp))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'ticker': ticker,
                'side': side,
                'quantity': quantity,
                'price': price,
                'reason': reason
            }
    
    def check_stop_loss_and_pyramid(self) -> List[Dict]:
        """Check all positions for stop-loss triggers and pyramid opportunities"""
        positions = self.get_current_positions()
        actions = []
        
        for pos in positions:
            ticker = pos['ticker']
            pnl_pct = pos['pnl_pct'] / 100
            
            # Check stop loss
            if pnl_pct <= STOP_LOSS_PCT:
                actions.append({
                    'action': 'stop_loss',
                    'ticker': ticker,
                    'quantity': pos['quantity'],
                    'price': pos['current_price'],
                    'reason': f'Stop loss triggered at {pnl_pct*100:.1f}%'
                })
            
            # Check pyramid opportunities
            elif pnl_pct >= PYRAMID_THRESHOLD_2:
                # Already up 30%+ → add another 50% (3rd tranche)
                pyramid_size = pos['cost_basis'] * 0.5 / pos['current_price']
                actions.append({
                    'action': 'pyramid_3',
                    'ticker': ticker,
                    'quantity': pyramid_size,
                    'price': pos['current_price'],
                    'reason': f'Pyramid Tier 3 at +{pnl_pct*100:.1f}%'
                })
            
            elif pnl_pct >= PYRAMID_THRESHOLD_1:
                # Up 15%+ → add 50% (2nd tranche)
                pyramid_size = pos['cost_basis'] * 0.5 / pos['current_price']
                actions.append({
                    'action': 'pyramid_2',
                    'ticker': ticker,
                    'quantity': pyramid_size,
                    'price': pos['current_price'],
                    'reason': f'Pyramid Tier 2 at +{pnl_pct*100:.1f}%'
                })
        
        return actions
    
    def rebalance(self, dry_run: bool = False) -> Dict:
        """Execute bi-weekly rebalance: score stocks, compare with portfolio, execute trades"""
        
        print(f"\n{'='*70}")
        print(f"LIVE PAPER TRADING REBALANCE — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*70}\n")
        
        # Step 1: Get top picks from Alpha Picker
        print("📊 Scoring stocks with Alpha Picker...")
        top_picks = self.picker.get_top_picks(n=20, use_prefilter=True, verbose=False)
        
        # Filter for Buy+ rated stocks (score >= MIN_SCORE)
        buy_plus = [p for p in top_picks if p['score'] >= MIN_SCORE]
        
        print(f"✅ Found {len(buy_plus)} Buy+ rated stocks (score ≥ {MIN_SCORE})\n")
        
        # Step 2: Get current portfolio state
        positions = self.get_current_positions()
        current_tickers = {p['ticker'] for p in positions}
        cash = get_cash_balance(self.portfolio_id)
        
        # Calculate total portfolio value
        portfolio_value = cash + sum(p['market_value'] for p in positions)
        
        print(f"💰 Portfolio Value: ${portfolio_value:,.2f}")
        print(f"💵 Cash Available: ${cash:,.2f}")
        print(f"📊 Current Positions: {len(positions)}\n")
        
        # Step 3: Check stop-loss and pyramid opportunities
        print("🔍 Checking stop-loss and pyramid opportunities...")
        actions = self.check_stop_loss_and_pyramid()
        
        trades_executed = []
        
        # Execute stop-losses first
        for action in actions:
            if action['action'] == 'stop_loss':
                print(f"🛑 STOP LOSS: Selling {action['ticker']} - {action['reason']}")
                if not dry_run:
                    result = self.execute_trade(
                        action['ticker'], 'sell', 
                        action['quantity'], action['price'],
                        action['reason']
                    )
                    trades_executed.append(result)
        
        # Re-get positions after stop-losses
        positions = self.get_current_positions()
        current_tickers = {p['ticker'] for p in positions}
        cash = get_cash_balance(self.portfolio_id)
        
        # Step 4: Determine entry/exit trades
        target_tickers = {p['ticker'] for p in buy_plus[:10]}  # Top 10 Buy+
        
        # Tickers to exit (no longer in top Buy+)
        to_exit = current_tickers - target_tickers
        
        # Tickers to enter (new in top Buy+)
        to_enter = target_tickers - current_tickers
        
        print(f"\n📤 Positions to EXIT: {len(to_exit)}")
        for ticker in to_exit:
            pos = next(p for p in positions if p['ticker'] == ticker)
            print(f"   • {ticker}: {pos['pnl_pct']:.1f}% P&L")
        
        print(f"\n📥 New Positions to ENTER: {len(to_enter)}")
        for ticker in to_enter:
            pick = next(p for p in buy_plus if p['ticker'] == ticker)
            print(f"   • {ticker}: Score {pick['score']:.1f}")
        
        # Step 5: Execute exit trades
        for ticker in to_exit:
            pos = next(p for p in positions if p['ticker'] == ticker)
            print(f"\n💸 SELL: {ticker} @ ${pos['current_price']:.2f} (P&L: {pos['pnl_pct']:.1f}%)")
            if not dry_run:
                result = self.execute_trade(
                    ticker, 'sell',
                    pos['quantity'], pos['current_price'],
                    'Rebalance exit - no longer top pick'
                )
                trades_executed.append(result)
                cash += pos['market_value']
        
        # Step 6: Execute entry trades
        position_size_usd = portfolio_value * POSITION_SIZE
        
        for ticker in to_enter:
            current_price = get_live_price(ticker)
            if current_price is None:
                print(f"\n⚠️  Could not get price for {ticker}, skipping")
                continue
            
            quantity = position_size_usd / current_price
            cost = quantity * current_price
            
            if cash < cost:
                print(f"\n⚠️  Insufficient cash for {ticker} (need ${cost:,.0f}, have ${cash:,.0f}), skipping")
                continue
            
            print(f"\n💰 BUY: {ticker} @ ${current_price:.2f} (${cost:,.2f})")
            if not dry_run:
                result = self.execute_trade(
                    ticker, 'buy',
                    quantity, current_price,
                    f'Rebalance entry - Buy+ score {next(p for p in buy_plus if p["ticker"] == ticker)["score"]:.1f}'
                )
                trades_executed.append(result)
                cash -= cost
        
        # Step 7: Execute pyramid trades
        for action in actions:
            if action['action'].startswith('pyramid'):
                if cash < action['quantity'] * action['price'] * 0.5:
                    print(f"\n⚠️  Insufficient cash for pyramid on {action['ticker']}, skipping")
                    continue
                
                print(f"\n📈 PYRAMID: {action['ticker']} - {action['reason']}")
                if not dry_run:
                    result = self.execute_trade(
                        action['ticker'], 'buy',
                        action['quantity'], action['price'],
                        action['reason']
                    )
                    trades_executed.append(result)
                    cash -= action['quantity'] * action['price']
        
        # Step 8: Generate summary
        final_positions = self.get_current_positions() if not dry_run else positions
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'dry_run': dry_run,
            'portfolio_value': portfolio_value,
            'cash': cash,
            'num_positions': len(final_positions),
            'trades_executed': len(trades_executed),
            'top_picks': buy_plus[:10],
            'positions': final_positions,
            'trades': trades_executed
        }
        
        print(f"\n{'='*70}")
        print(f"✅ Rebalance complete - {len(trades_executed)} trades executed")
        print(f"{'='*70}\n")
        
        return summary
    
    def get_portfolio_status(self) -> Dict:
        """Get current portfolio status with metrics"""
        positions = self.get_current_positions()
        cash = get_cash_balance(self.portfolio_id)
        
        total_market_value = sum(p['market_value'] for p in positions)
        total_unrealized_pnl = sum(p['unrealized_pnl'] for p in positions)
        portfolio_value = cash + total_market_value
        
        # Calculate realized P&L from trades
        with db_lock:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COALESCE(SUM(pnl), 0) FROM trades 
                WHERE portfolio_id = ? AND side = 'sell'
            ''', (self.portfolio_id,))
            realized_pnl = cursor.fetchone()[0]
            
            # Get trade history stats
            cursor.execute('''
                SELECT COUNT(*), 
                       SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END),
                       AVG(pnl)
                FROM trades 
                WHERE portfolio_id = ? AND side = 'sell' AND pnl IS NOT NULL
            ''', (self.portfolio_id,))
            row = cursor.fetchone()
            total_trades = row[0] or 0
            winning_trades = row[1] or 0
            avg_pnl = row[2] or 0
            
            conn.close()
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        total_return = ((portfolio_value / INITIAL_CASH) - 1) * 100
        drawdown = ((portfolio_value - INITIAL_CASH) / INITIAL_CASH * 100) if portfolio_value < INITIAL_CASH else 0
        
        return {
            'portfolio_value': portfolio_value,
            'cash': cash,
            'total_market_value': total_market_value,
            'unrealized_pnl': total_unrealized_pnl,
            'realized_pnl': realized_pnl,
            'total_return_pct': total_return,
            'num_positions': len(positions),
            'positions': positions,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'avg_pnl_per_trade': avg_pnl,
            'drawdown_pct': drawdown
        }
    
    def get_trade_history(self, limit: int = 50) -> List[Dict]:
        """Get recent trade history"""
        with db_lock:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ticker, side, quantity, price, pnl, timestamp
                FROM trades 
                WHERE portfolio_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (self.portfolio_id, limit))
            
            trades = []
            for row in cursor.fetchall():
                trades.append({
                    'ticker': row[0],
                    'side': row[1],
                    'quantity': row[2],
                    'price': row[3],
                    'pnl': row[4],
                    'timestamp': row[5]
                })
            
            conn.close()
            return trades


def format_whatsapp_report(summary: Dict) -> str:
    """Format summary as WhatsApp-friendly text (no markdown tables)"""
    lines = []
    lines.append("📈 *PAPER TRADING REBALANCE COMPLETE*")
    lines.append("")
    lines.append(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC")
    lines.append("")
    lines.append("💼 *PORTFOLIO*")
    lines.append(f"• Value: ${summary['portfolio_value']:,.2f}")
    lines.append(f"• Cash: ${summary['cash']:,.2f}")
    lines.append(f"• Positions: {summary['num_positions']}")
    lines.append(f"• Trades: {summary['trades_executed']}")
    lines.append("")
    
    if summary['positions']:
        lines.append("📊 *CURRENT POSITIONS*")
        for pos in sorted(summary['positions'], key=lambda x: x['pnl_pct'], reverse=True):
            emoji = "🟢" if pos['pnl_pct'] > 0 else "🔴"
            lines.append(
                f"{emoji} *{pos['ticker']}* "
                f"${pos['market_value']:,.0f} "
                f"({pos['pnl_pct']:+.1f}%)"
            )
        lines.append("")
    
    if summary['trades']:
        lines.append("📝 *TRADES EXECUTED*")
        for trade in summary['trades']:
            side_emoji = "💰" if trade['side'] == 'buy' else "💸"
            lines.append(
                f"{side_emoji} {trade['side'].upper()} {trade['ticker']} "
                f"@ ${trade['price']:.2f}"
            )
            if trade['reason']:
                lines.append(f"  └─ {trade['reason']}")
        lines.append("")
    
    lines.append("✅ Rebalance complete")
    
    return "\n".join(lines)


def format_status_report(status: Dict) -> str:
    """Format portfolio status as WhatsApp-friendly text"""
    lines = []
    lines.append("📊 *PORTFOLIO STATUS*")
    lines.append("")
    lines.append("💼 *OVERVIEW*")
    lines.append(f"• Total Value: ${status['portfolio_value']:,.2f}")
    lines.append(f"• Cash: ${status['cash']:,.2f}")
    lines.append(f"• Invested: ${status['total_market_value']:,.2f}")
    lines.append(f"• Total Return: {status['total_return_pct']:+.2f}%")
    lines.append("")
    lines.append("📈 *P&L*")
    lines.append(f"• Unrealized: ${status['unrealized_pnl']:,.2f}")
    lines.append(f"• Realized: ${status['realized_pnl']:,.2f}")
    if status['drawdown_pct'] < 0:
        lines.append(f"• Drawdown: {status['drawdown_pct']:.2f}%")
    lines.append("")
    lines.append("🎯 *PERFORMANCE*")
    lines.append(f"• Win Rate: {status['win_rate']:.1f}%")
    lines.append(f"• Total Trades: {status['total_trades']}")
    lines.append(f"• Avg P&L/Trade: ${status['avg_pnl_per_trade']:,.2f}")
    lines.append("")
    
    if status['positions']:
        lines.append(f"📊 *POSITIONS ({len(status['positions'])})*")
        for pos in sorted(status['positions'], key=lambda x: x['market_value'], reverse=True):
            emoji = "🟢" if pos['pnl_pct'] > 0 else "🔴"
            lines.append(
                f"{emoji} *{pos['ticker']}* "
                f"${pos['market_value']:,.0f} "
                f"({pos['pnl_pct']:+.1f}%)"
            )
    
    return "\n".join(lines)


if __name__ == '__main__':
    import argparse
    
    # Handle both "paper-run" and "run" formats (CLI passes "paper-" prefix)
    import sys as _sys
    if len(_sys.argv) > 1 and _sys.argv[1].startswith('paper-'):
        _sys.argv[1] = _sys.argv[1].replace('paper-', '')
    
    parser = argparse.ArgumentParser(description='Live Paper Trading for SA Quant Replica')
    parser.add_argument('command', choices=['run', 'status', 'history'], 
                       help='Command to execute')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Simulate without executing trades')
    parser.add_argument('--limit', type=int, default=50, 
                       help='Number of trades to show in history')
    
    args = parser.parse_args()
    
    trader = LivePaperTrader()
    
    if args.command == 'run':
        summary = trader.rebalance(dry_run=args.dry_run)
        print("\n" + format_whatsapp_report(summary))
        
    elif args.command == 'status':
        status = trader.get_portfolio_status()
        print("\n" + format_status_report(status))
        
    elif args.command == 'history':
        trades = trader.get_trade_history(limit=args.limit)
        print("\n📝 *TRADE HISTORY*\n")
        for trade in trades:
            side_emoji = "💰" if trade['side'] == 'buy' else "💸"
            pnl_str = f" (P&L: ${trade['pnl']:,.2f})" if trade['pnl'] else ""
            print(
                f"{side_emoji} {trade['side'].upper()} {trade['ticker']} "
                f"@ ${trade['price']:.2f}{pnl_str} "
                f"[{trade['timestamp'][:10]}]"
            )
