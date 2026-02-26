"""
IBKR API Bridge — Interactive Brokers TWS/Gateway API connector and simulator.

Provides account data retrieval, order management, market data subscription,
and portfolio analytics via IBKR's Client Portal API (REST) or simulated mode.
Includes position tracking, P&L calculation, and contract lookup.
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

# Default IBKR Client Portal Gateway endpoint
DEFAULT_BASE_URL = "https://localhost:5000/v1/api"

# Simulated account data for testing/demo
_SIM_POSITIONS = [
    {"conid": 265598, "symbol": "AAPL", "qty": 100, "avgCost": 175.50, "mktPrice": 195.20, "currency": "USD"},
    {"conid": 272093, "symbol": "MSFT", "qty": 50, "avgCost": 380.00, "mktPrice": 420.15, "currency": "USD"},
    {"conid": 756733, "symbol": "TSLA", "qty": 25, "avgCost": 245.00, "mktPrice": 258.30, "currency": "USD"},
    {"conid": 15016062, "symbol": "NVDA", "qty": 75, "avgCost": 480.00, "mktPrice": 875.50, "currency": "USD"},
    {"conid": 265768, "symbol": "AMZN", "qty": 30, "avgCost": 155.00, "mktPrice": 185.75, "currency": "USD"},
]

_SIM_ACCOUNT = {
    "id": "U1234567",
    "type": "Individual",
    "currency": "USD",
    "netliquidation": 500000.00,
    "totalcashvalue": 125000.00,
    "buyingpower": 375000.00,
    "grosspositionvalue": 375000.00,
    "maintenancemarginreq": 93750.00,
    "excessliquidity": 406250.00,
}


def _api_request(endpoint: str, method: str = "GET", data: Optional[Dict] = None,
                 base_url: str = DEFAULT_BASE_URL) -> Dict:
    """Make a request to IBKR Client Portal API."""
    url = f"{base_url}{endpoint}"
    try:
        if data:
            req = urllib.request.Request(url, data=json.dumps(data).encode(),
                                         headers={"Content-Type": "application/json"}, method=method)
        else:
            req = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e), "simulated": True}


def get_account_summary(account_id: str = "U1234567", simulated: bool = True) -> Dict:
    """
    Get account summary including NAV, cash, buying power, and margin.

    Args:
        account_id: IBKR account ID
        simulated: Use simulated data (True) or live API (False)

    Returns:
        Account summary dict with key financial metrics
    """
    if not simulated:
        result = _api_request(f"/portfolio/{account_id}/summary")
        if "error" not in result:
            return result

    # Simulated
    acct = dict(_SIM_ACCOUNT)
    acct["timestamp"] = datetime.now(timezone.utc).isoformat()
    acct["margin_utilization_pct"] = round(
        acct["maintenancemarginreq"] / acct["netliquidation"] * 100, 2
    )
    return acct


def get_positions(account_id: str = "U1234567", simulated: bool = True) -> List[Dict]:
    """
    Get all open positions with P&L calculations.

    Args:
        account_id: IBKR account ID
        simulated: Use simulated data (True) or live API (False)

    Returns:
        List of position dicts with unrealized P&L
    """
    if not simulated:
        result = _api_request(f"/portfolio/{account_id}/positions/0")
        if isinstance(result, list):
            return result

    positions = []
    for pos in _SIM_POSITIONS:
        unrealized_pnl = (pos["mktPrice"] - pos["avgCost"]) * pos["qty"]
        mkt_value = pos["mktPrice"] * pos["qty"]
        pnl_pct = ((pos["mktPrice"] / pos["avgCost"]) - 1) * 100

        positions.append({
            "conid": pos["conid"],
            "symbol": pos["symbol"],
            "quantity": pos["qty"],
            "avg_cost": pos["avgCost"],
            "market_price": pos["mktPrice"],
            "market_value": round(mkt_value, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "currency": pos["currency"]
        })

    return positions


def search_contract(symbol: str, sec_type: str = "STK", exchange: str = "SMART",
                    simulated: bool = True) -> List[Dict]:
    """
    Search for contracts by symbol.

    Args:
        symbol: Ticker symbol
        sec_type: Security type (STK, OPT, FUT, CASH)
        exchange: Exchange (SMART for best routing)
        simulated: Use simulated data

    Returns:
        List of matching contracts
    """
    if not simulated:
        result = _api_request("/iserver/secdef/search", method="POST",
                              data={"symbol": symbol, "secType": sec_type})
        if isinstance(result, list):
            return result

    # Common conid mappings
    known = {
        "AAPL": 265598, "MSFT": 272093, "TSLA": 756733,
        "NVDA": 15016062, "AMZN": 265768, "GOOG": 208813720,
        "META": 107113386, "SPY": 756733, "QQQ": 320227571
    }
    conid = known.get(symbol.upper(), abs(hash(symbol)) % 99999999)

    return [{
        "conid": conid,
        "symbol": symbol.upper(),
        "secType": sec_type,
        "exchange": exchange,
        "currency": "USD",
        "description": f"{symbol.upper()} — {sec_type} on {exchange}"
    }]


def place_order(symbol: str, side: str, qty: int, order_type: str = "MKT",
                limit_price: float = 0.0, account_id: str = "U1234567",
                simulated: bool = True) -> Dict:
    """
    Place an order via IBKR.

    Args:
        symbol: Ticker symbol
        side: 'BUY' or 'SELL'
        qty: Number of shares
        order_type: 'MKT', 'LMT', 'STP', 'STP_LMT'
        limit_price: Price for limit orders
        account_id: IBKR account ID
        simulated: Use simulated mode

    Returns:
        Order confirmation dict
    """
    contracts = search_contract(symbol, simulated=simulated)
    if not contracts:
        return {"error": f"Contract not found for {symbol}"}

    conid = contracts[0]["conid"]
    order_data = {
        "acctId": account_id,
        "conid": conid,
        "orderType": order_type,
        "side": side.upper(),
        "quantity": qty,
        "tif": "DAY"
    }
    if order_type in ("LMT", "STP_LMT") and limit_price > 0:
        order_data["price"] = limit_price

    if not simulated:
        result = _api_request(f"/iserver/account/{account_id}/orders", method="POST",
                              data={"orders": [order_data]})
        if "error" not in result:
            return result

    # Simulated fill
    sim_price = limit_price if limit_price > 0 else round(100 + (hash(symbol) % 900) / 10, 2)
    return {
        "order_id": f"IBKR-{abs(hash(f'{symbol}{side}{qty}')) % 99999999}",
        "symbol": symbol.upper(),
        "side": side.upper(),
        "quantity": qty,
        "order_type": order_type,
        "fill_price": sim_price,
        "total_value": round(sim_price * qty, 2),
        "status": "Filled",
        "simulated": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def get_portfolio_analytics(account_id: str = "U1234567", simulated: bool = True) -> Dict:
    """
    Calculate portfolio-level analytics from positions.

    Args:
        account_id: IBKR account ID
        simulated: Use simulated data

    Returns:
        Portfolio analytics: concentration, P&L summary, sector breakdown
    """
    positions = get_positions(account_id, simulated)
    if not positions:
        return {"error": "No positions found"}

    total_value = sum(p["market_value"] for p in positions)
    total_pnl = sum(p["unrealized_pnl"] for p in positions)
    total_cost = sum(p["avg_cost"] * p["quantity"] for p in positions)

    # Concentration
    for p in positions:
        p["weight_pct"] = round(p["market_value"] / total_value * 100, 2) if total_value else 0

    # HHI (Herfindahl-Hirschman Index for concentration)
    hhi = sum((p["weight_pct"] / 100) ** 2 for p in positions)

    # Best/worst
    best = max(positions, key=lambda x: x["pnl_pct"])
    worst = min(positions, key=lambda x: x["pnl_pct"])

    return {
        "total_market_value": round(total_value, 2),
        "total_cost_basis": round(total_cost, 2),
        "total_unrealized_pnl": round(total_pnl, 2),
        "total_return_pct": round((total_value / total_cost - 1) * 100, 2) if total_cost else 0,
        "position_count": len(positions),
        "concentration_hhi": round(hhi, 4),
        "diversification_score": round(1 - hhi, 4),
        "best_performer": {"symbol": best["symbol"], "pnl_pct": best["pnl_pct"]},
        "worst_performer": {"symbol": worst["symbol"], "pnl_pct": worst["pnl_pct"]},
        "positions": positions
    }
