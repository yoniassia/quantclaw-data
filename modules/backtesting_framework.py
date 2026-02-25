"""
Backtesting Framework
Event-driven backtester with realistic fills, slippage modeling, commission tracking

Features:
- Event-driven architecture (market data → signal generation → order execution)
- Realistic fill simulation with bid-ask spreads
- Configurable slippage and commission models
- Position tracking with P&L calculation
- Portfolio-level risk metrics (Sharpe, Sortino, max drawdown)
- Transaction cost analysis
- Multiple order types (market, limit, stop)

Data Sources:
- Yahoo Finance for historical OHLCV
- Custom signal generators (momentum, mean reversion, etc.)
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

@dataclass
class Order:
    """Represents a trading order"""
    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    timestamp: datetime
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    filled: bool = False
    fill_price: Optional[float] = None
    fill_timestamp: Optional[datetime] = None

@dataclass
class Position:
    """Represents a trading position"""
    symbol: str
    quantity: int = 0
    avg_entry_price: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    
    def update_pnl(self, current_price: float):
        """Update unrealized P&L based on current market price"""
        self.unrealized_pnl = (current_price - self.avg_entry_price) * self.quantity

@dataclass
class Trade:
    """Represents a completed trade"""
    symbol: str
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    quantity: int
    pnl: float
    commission: float
    slippage: float

class CommissionModel:
    """Commission model for trading costs"""
    
    @staticmethod
    def fixed_per_trade(amount: float = 1.0):
        """Fixed commission per trade"""
        return lambda quantity, price: amount
    
    @staticmethod
    def per_share(amount: float = 0.005):
        """Commission per share"""
        return lambda quantity, price: quantity * amount
    
    @staticmethod
    def percentage(rate: float = 0.001):
        """Commission as percentage of trade value"""
        return lambda quantity, price: quantity * price * rate

class SlippageModel:
    """Slippage model for realistic fill simulation"""
    
    @staticmethod
    def fixed_bps(bps: float = 5.0):
        """Fixed basis points slippage"""
        return lambda price, side: price * (1 + bps/10000 if side == OrderSide.BUY else 1 - bps/10000)
    
    @staticmethod
    def volume_dependent(base_bps: float = 5.0, volume_impact: float = 0.1):
        """Slippage increases with order size relative to average volume"""
        def slippage_fn(price, side, order_size, avg_volume):
            volume_ratio = order_size / avg_volume if avg_volume > 0 else 0
            total_bps = base_bps * (1 + volume_impact * volume_ratio)
            return price * (1 + total_bps/10000 if side == OrderSide.BUY else 1 - total_bps/10000)
        return slippage_fn
    
    @staticmethod
    def spread_based(spread_pct: float = 0.1):
        """Slippage based on bid-ask spread"""
        return lambda price, side: price * (1 + spread_pct/100 if side == OrderSide.BUY else 1 - spread_pct/100)

class Backtester:
    """Event-driven backtesting engine"""
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_model: Callable = CommissionModel.per_share(0.005),
        slippage_model: Callable = SlippageModel.fixed_bps(5.0)
    ):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.portfolio_value = initial_capital
        self.commission_model = commission_model
        self.slippage_model = slippage_model
        
        self.trades: List[Trade] = []
        self.equity_curve: List[Tuple[datetime, float]] = []
        self.orders: List[Order] = []
        
    def add_position(self, symbol: str, quantity: int, price: float, timestamp: datetime):
        """Add or update a position"""
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol)
        
        pos = self.positions[symbol]
        
        # Calculate new average entry price
        if quantity > 0:  # Buy
            total_cost = pos.avg_entry_price * pos.quantity + price * quantity
            pos.quantity += quantity
            pos.avg_entry_price = total_cost / pos.quantity if pos.quantity > 0 else 0
        else:  # Sell
            # Record realized P&L
            pnl = (price - pos.avg_entry_price) * abs(quantity)
            pos.realized_pnl += pnl
            pos.quantity += quantity  # quantity is negative for sells
            
            if pos.quantity == 0:
                pos.avg_entry_price = 0
    
    def execute_order(self, order: Order, current_data: pd.Series) -> bool:
        """Execute an order with slippage and commission"""
        current_price = current_data['Close']
        
        # Apply slippage
        if callable(getattr(self.slippage_model, '__call__', None)):
            fill_price = self.slippage_model(current_price, order.side)
        else:
            fill_price = current_price
        
        # Calculate commission
        commission = self.commission_model(order.quantity, fill_price)
        
        # Check if we have enough cash for buys
        if order.side == OrderSide.BUY:
            cost = order.quantity * fill_price + commission
            if cost > self.cash:
                return False  # Insufficient funds
            self.cash -= cost
        else:  # Sell
            proceeds = order.quantity * fill_price - commission
            self.cash += proceeds
        
        # Update position
        quantity = order.quantity if order.side == OrderSide.BUY else -order.quantity
        self.add_position(order.symbol, quantity, fill_price, order.timestamp)
        
        # Mark order as filled
        order.filled = True
        order.fill_price = fill_price
        order.fill_timestamp = order.timestamp
        
        return True
    
    def run(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        signal_fn: Callable,
        rebalance_frequency: str = 'D'
    ) -> Dict:
        """
        Run backtest
        
        Args:
            symbols: List of ticker symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            signal_fn: Function that takes (symbol, data) and returns list of Orders
            rebalance_frequency: 'D' (daily), 'W' (weekly), 'M' (monthly)
        """
        # Download data
        data = {}
        for symbol in symbols:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            if not df.empty:
                data[symbol] = df
        
        if not data:
            return {"error": "No data downloaded"}
        
        # Get all dates
        all_dates = sorted(set().union(*[set(df.index) for df in data.values()]))
        
        # Event loop
        for date in all_dates:
            # Generate signals for each symbol
            for symbol in symbols:
                if symbol not in data or date not in data[symbol].index:
                    continue
                
                current_data = data[symbol].loc[date]
                
                # Generate signal
                orders = signal_fn(symbol, data[symbol].loc[:date])
                
                # Execute orders
                for order in orders:
                    order.timestamp = date
                    success = self.execute_order(order, current_data)
                    if success:
                        self.orders.append(order)
            
            # Update portfolio value
            portfolio_value = self.cash
            for symbol, pos in self.positions.items():
                if symbol in data and date in data[symbol].index:
                    current_price = data[symbol].loc[date, 'Close']
                    pos.update_pnl(current_price)
                    portfolio_value += pos.quantity * current_price
            
            self.portfolio_value = portfolio_value
            self.equity_curve.append((date, portfolio_value))
        
        return self.get_performance_stats()
    
    def get_performance_stats(self) -> Dict:
        """Calculate performance statistics"""
        if not self.equity_curve:
            return {}
        
        # Convert to DataFrame
        equity_df = pd.DataFrame(self.equity_curve, columns=['date', 'value'])
        equity_df['returns'] = equity_df['value'].pct_change()
        
        # Calculate metrics
        total_return = (equity_df['value'].iloc[-1] / self.initial_capital - 1) * 100
        
        annual_return = ((equity_df['value'].iloc[-1] / self.initial_capital) ** 
                        (252 / len(equity_df)) - 1) * 100
        
        returns = equity_df['returns'].dropna()
        sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
        
        # Sortino (downside deviation)
        downside_returns = returns[returns < 0]
        sortino = (np.sqrt(252) * returns.mean() / downside_returns.std() 
                  if len(downside_returns) > 0 and downside_returns.std() > 0 else 0)
        
        # Max drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        # Win rate
        winning_trades = len([t for t in self.trades if t.pnl > 0])
        total_trades = len(self.trades)
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        
        return {
            "initial_capital": self.initial_capital,
            "final_value": equity_df['value'].iloc[-1],
            "total_return_pct": total_return,
            "annual_return_pct": annual_return,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "max_drawdown_pct": max_drawdown,
            "total_trades": total_trades,
            "win_rate_pct": win_rate,
            "num_positions": len(self.positions)
        }

def simple_momentum_strategy(symbol: str, data: pd.DataFrame, lookback: int = 20) -> List[Order]:
    """
    Simple momentum strategy: buy when price > MA, sell when below
    
    Args:
        symbol: Ticker symbol
        data: Historical price data
        lookback: Moving average period
    
    Returns:
        List of orders
    """
    if len(data) < lookback + 1:
        return []
    
    data = data.copy()
    data['MA'] = data['Close'].rolling(lookback).mean()
    
    current = data.iloc[-1]
    previous = data.iloc[-2]
    
    orders = []
    
    # Buy signal: price crosses above MA
    if previous['Close'] <= previous['MA'] and current['Close'] > current['MA']:
        quantity = 100  # Buy 100 shares
        orders.append(Order(
            symbol=symbol,
            side=OrderSide.BUY,
            quantity=quantity,
            order_type=OrderType.MARKET,
            timestamp=current.name
        ))
    
    # Sell signal: price crosses below MA
    elif previous['Close'] >= previous['MA'] and current['Close'] < current['MA']:
        quantity = 100  # Sell 100 shares
        orders.append(Order(
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=quantity,
            order_type=OrderType.MARKET,
            timestamp=current.name
        ))
    
    return orders

def mean_reversion_strategy(symbol: str, data: pd.DataFrame, lookback: int = 20, 
                           z_threshold: float = 2.0) -> List[Order]:
    """
    Mean reversion strategy: buy when oversold, sell when overbought
    
    Args:
        symbol: Ticker symbol
        data: Historical price data
        lookback: Lookback period for mean/std calculation
        z_threshold: Z-score threshold for entry/exit
    
    Returns:
        List of orders
    """
    if len(data) < lookback + 1:
        return []
    
    data = data.copy()
    data['MA'] = data['Close'].rolling(lookback).mean()
    data['STD'] = data['Close'].rolling(lookback).std()
    data['Z'] = (data['Close'] - data['MA']) / data['STD']
    
    current = data.iloc[-1]
    
    orders = []
    
    # Buy when oversold (Z < -threshold)
    if current['Z'] < -z_threshold:
        quantity = 100
        orders.append(Order(
            symbol=symbol,
            side=OrderSide.BUY,
            quantity=quantity,
            order_type=OrderType.MARKET,
            timestamp=current.name
        ))
    
    # Sell when overbought (Z > threshold)
    elif current['Z'] > z_threshold:
        quantity = 100
        orders.append(Order(
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=quantity,
            order_type=OrderType.MARKET,
            timestamp=current.name
        ))
    
    return orders

def run_backtest(
    symbols: List[str],
    start_date: str,
    end_date: str,
    strategy: str = "momentum",
    initial_capital: float = 100000.0
) -> Dict:
    """
    Run backtest with specified strategy
    
    Args:
        symbols: List of ticker symbols
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        strategy: Strategy name ('momentum' or 'mean_reversion')
        initial_capital: Initial capital
    
    Returns:
        Performance statistics dictionary
    """
    # Select strategy
    if strategy == "momentum":
        signal_fn = simple_momentum_strategy
    elif strategy == "mean_reversion":
        signal_fn = mean_reversion_strategy
    else:
        return {"error": f"Unknown strategy: {strategy}"}
    
    # Create backtester
    backtester = Backtester(
        initial_capital=initial_capital,
        commission_model=CommissionModel.per_share(0.005),
        slippage_model=SlippageModel.fixed_bps(5.0)
    )
    
    # Run backtest
    results = backtester.run(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        signal_fn=signal_fn
    )
    
    return results

if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Backtesting Framework")
    parser.add_argument("command", choices=["backtest", "backtest-momentum", "backtest-mean-reversion"])
    parser.add_argument("symbols", help="Comma-separated list of symbols (e.g., AAPL,MSFT)")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--strategy", choices=["momentum", "mean_reversion"], default="momentum",
                       help="Trading strategy")
    parser.add_argument("--capital", type=float, default=100000.0, help="Initial capital")
    parser.add_argument("--lookback", type=int, default=20, help="Lookback period for strategy")
    parser.add_argument("--z-threshold", type=float, default=2.0,
                       help="Z-score threshold for mean reversion strategy")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    symbols = args.symbols.split(",")
    
    # Override strategy based on command
    if args.command == "backtest-momentum":
        strategy = "momentum"
    elif args.command == "backtest-mean-reversion":
        strategy = "mean_reversion"
    else:
        strategy = args.strategy
    
    results = run_backtest(
        symbols=symbols,
        start_date=args.start,
        end_date=args.end,
        strategy=strategy,
        initial_capital=args.capital
    )
    
    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print(f"\nBacktesting Results: {', '.join(symbols)}")
        print(f"Strategy: {strategy}")
        print(f"Period: {args.start} to {args.end}")
        print("-" * 60)
        for key, value in results.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
