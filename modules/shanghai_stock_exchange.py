#!/usr/bin/env python3
"""
Shanghai Stock Exchange (SSE) Data Module

Phase 697: Shanghai Stock Exchange
Fetch SSE Composite index, margin trading data, Stock Connect northbound flows.

Data Sources:
- Yahoo Finance for SSE Composite (000001.SS)
- Eastmoney / free Chinese finance APIs for margin/northbound flows (simulated with Yahoo volume proxy)

CLI:
  python -m modules.shanghai_stock_exchange index
  python -m modules.shanghai_stock_exchange margin
  python -m modules.shanghai_stock_exchange northbound
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json

def get_sse_index(days: int = 30) -> dict:
    """
    Fetch SSE Composite Index (000001.SS) historical data.
    
    Args:
        days: Number of days of historical data
        
    Returns:
        dict with date, close, volume, change%
    """
    try:
        ticker = yf.Ticker("000001.SS")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty:
            return {
                "error": "No data available for SSE Composite",
                "symbol": "000001.SS",
                "period": f"{days}d"
            }
        
        # Calculate daily changes
        df['Change%'] = df['Close'].pct_change() * 100
        
        result = {
            "index": "SSE Composite",
            "symbol": "000001.SS",
            "period": f"{days}d",
            "latest": {
                "date": df.index[-1].strftime('%Y-%m-%d'),
                "close": round(df['Close'].iloc[-1], 2),
                "volume": int(df['Volume'].iloc[-1]),
                "change_pct": round(df['Change%'].iloc[-1], 2) if not pd.isna(df['Change%'].iloc[-1]) else 0.0
            },
            "summary": {
                "high_30d": round(df['High'].max(), 2),
                "low_30d": round(df['Low'].min(), 2),
                "avg_volume": int(df['Volume'].mean()),
                "volatility": round(df['Change%'].std(), 2)
            },
            "history": [
                {
                    "date": idx.strftime('%Y-%m-%d'),
                    "open": round(row['Open'], 2),
                    "high": round(row['High'], 2),
                    "low": round(row['Low'], 2),
                    "close": round(row['Close'], 2),
                    "volume": int(row['Volume']),
                    "change_pct": round(row['Change%'], 2) if not pd.isna(row['Change%']) else 0.0
                }
                for idx, row in df.iterrows()
            ][-10:]  # Last 10 days
        }
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to fetch SSE data: {str(e)}",
            "symbol": "000001.SS"
        }


def get_margin_trading() -> dict:
    """
    Simulate margin trading data for SSE.
    
    In production: scrape from Eastmoney, Shanghai Stock Exchange official site, or Wind Terminal.
    For now: use volume as proxy for margin activity.
    
    Returns:
        dict with margin buy/sell balance (simulated)
    """
    try:
        ticker = yf.Ticker("000001.SS")
        df = ticker.history(period="5d")
        
        if df.empty:
            return {"error": "No margin data available", "note": "Simulated from volume"}
        
        latest_volume = int(df['Volume'].iloc[-1])
        avg_volume = int(df['Volume'].mean())
        
        # Simulate margin balance (in reality would come from SSE official data)
        margin_balance_cny = latest_volume * 45.5  # Rough proxy: volume * avg price
        margin_buy_balance = margin_balance_cny * 0.55
        margin_sell_balance = margin_balance_cny * 0.45
        
        result = {
            "exchange": "Shanghai Stock Exchange",
            "date": df.index[-1].strftime('%Y-%m-%d'),
            "margin_balance_cny": round(margin_balance_cny / 1e8, 2),  # in 100M CNY
            "margin_buy_balance_cny": round(margin_buy_balance / 1e8, 2),
            "margin_sell_balance_cny": round(margin_sell_balance / 1e8, 2),
            "margin_to_volume_ratio": round((latest_volume / avg_volume) * 0.08, 4),  # Simulated
            "note": "Simulated data - production would use Eastmoney or SSE API"
        }
        
        return result
        
    except Exception as e:
        return {"error": f"Failed to fetch margin data: {str(e)}"}


def get_northbound_flow(days: int = 10) -> dict:
    """
    Simulate Stock Connect northbound flow (mainland → Hong Kong → A-shares).
    
    In production: scrape from Hong Kong Stock Exchange (HKEX) or Wind Terminal.
    For now: estimate from SSE volume trends.
    
    Args:
        days: Number of days to analyze
        
    Returns:
        dict with net northbound flow estimates
    """
    try:
        ticker = yf.Ticker("000001.SS")
        df = ticker.history(period=f"{days}d")
        
        if df.empty:
            return {"error": "No northbound flow data", "note": "Simulated from volume"}
        
        # Simulate northbound flow based on volume delta
        df['Volume_MA5'] = df['Volume'].rolling(5).mean()
        df['Flow_Proxy'] = (df['Volume'] - df['Volume_MA5']) / 1e6  # in millions
        
        latest = df.iloc[-1]
        net_flow_today = round(latest['Flow_Proxy'], 2) if not pd.isna(latest['Flow_Proxy']) else 0.0
        
        # Aggregate over period
        total_inflow = df[df['Flow_Proxy'] > 0]['Flow_Proxy'].sum() if 'Flow_Proxy' in df else 0
        total_outflow = abs(df[df['Flow_Proxy'] < 0]['Flow_Proxy'].sum()) if 'Flow_Proxy' in df else 0
        
        result = {
            "flow_type": "Stock Connect Northbound",
            "period": f"{days}d",
            "date": df.index[-1].strftime('%Y-%m-%d'),
            "net_flow_today_cny_millions": net_flow_today,
            "total_inflow_cny_millions": round(total_inflow, 2),
            "total_outflow_cny_millions": round(total_outflow, 2),
            "net_flow_period_cny_millions": round(total_inflow - total_outflow, 2),
            "avg_daily_flow_cny_millions": round((total_inflow - total_outflow) / days, 2),
            "note": "Simulated data - production would use HKEX or Wind API"
        }
        
        return result
        
    except Exception as e:
        return {"error": f"Failed to fetch northbound flow: {str(e)}"}


def cli():
    """CLI interface for Shanghai Stock Exchange module."""
    import sys
    
    if len(sys.argv) < 2:
        print(json.dumps({
            "usage": "python -m modules.shanghai_stock_exchange <command>",
            "commands": ["index", "margin", "northbound"]
        }, indent=2))
        return
    
    command = sys.argv[1].lower()
    # Strip sse- prefix if present
    if command.startswith('sse-'):
        command = command[4:]
    
    if command == "index":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        result = get_sse_index(days=days)
    elif command == "margin":
        result = get_margin_trading()
    elif command == "northbound":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        result = get_northbound_flow(days=days)
    else:
        result = {"error": f"Unknown command: {command}", "valid_commands": ["index", "margin", "northbound"]}
    
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    cli()
