"""
FIX Protocol Gateway — Simulated FIX 4.2/4.4 order routing and message handling.

Provides FIX message construction, parsing, order lifecycle simulation,
and execution report generation. Useful for backtesting order routing logic
and understanding FIX protocol mechanics without a live exchange connection.
"""

import time
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

# FIX tag definitions (subset)
FIX_TAGS = {
    8: "BeginString", 9: "BodyLength", 35: "MsgType", 49: "SenderCompID",
    56: "TargetCompID", 34: "MsgSeqNum", 52: "SendingTime", 11: "ClOrdID",
    21: "HandlInst", 55: "Symbol", 54: "Side", 38: "OrderQty", 40: "OrdType",
    44: "Price", 59: "TimeInForce", 60: "TransactTime", 150: "ExecType",
    39: "OrdStatus", 14: "CumQty", 151: "LeavesQty", 6: "AvgPx",
    17: "ExecID", 37: "OrderID", 31: "LastPx", 32: "LastQty", 10: "CheckSum"
}

MSG_TYPES = {
    "0": "Heartbeat", "A": "Logon", "5": "Logout", "D": "NewOrderSingle",
    "F": "OrderCancelRequest", "G": "OrderCancelReplaceRequest",
    "8": "ExecutionReport", "9": "OrderCancelReject", "3": "Reject"
}

SIDE = {"1": "Buy", "2": "Sell", "5": "SellShort"}
ORD_TYPE = {"1": "Market", "2": "Limit", "3": "Stop", "4": "StopLimit"}
TIF = {"0": "Day", "1": "GTC", "3": "IOC", "4": "FOK", "6": "GTD"}
ORD_STATUS = {"0": "New", "1": "PartiallyFilled", "2": "Filled", "4": "Canceled", "8": "Rejected"}

# Simulated order book
_orders: Dict[str, Dict] = {}
_seq_num = 0


def _next_seq() -> int:
    global _seq_num
    _seq_num += 1
    return _seq_num


def _checksum(msg: str) -> str:
    """Calculate FIX checksum (sum of ASCII values mod 256)."""
    return str(sum(ord(c) for c in msg) % 256).zfill(3)


def build_fix_message(msg_type: str, fields: Dict[int, str],
                      sender: str = "QUANTCLAW", target: str = "EXCHANGE") -> str:
    """
    Build a FIX protocol message string.

    Args:
        msg_type: FIX message type (e.g., 'D' for NewOrderSingle)
        fields: Dict of tag number -> value
        sender: SenderCompID
        target: TargetCompID

    Returns:
        Complete FIX message string with SOH delimiters shown as '|'
    """
    now = datetime.now(timezone.utc).strftime("%Y%m%d-%H:%M:%S.%f")[:-3]
    seq = _next_seq()

    # Body (everything between BeginString/BodyLength and CheckSum)
    body_fields = {
        35: msg_type, 49: sender, 56: target,
        34: str(seq), 52: now
    }
    body_fields.update(fields)

    body = "|".join(f"{tag}={val}" for tag, val in sorted(body_fields.items()))
    body_len = len(body.replace("|", "\x01"))  # SOH = 1 byte

    header = f"8=FIX.4.4|9={body_len}"
    msg_no_checksum = f"{header}|{body}|"
    checksum = _checksum(msg_no_checksum.replace("|", "\x01"))

    return f"{msg_no_checksum}10={checksum}|"


def parse_fix_message(msg: str) -> Dict:
    """
    Parse a FIX message string into a structured dict.

    Args:
        msg: FIX message with '|' as delimiter

    Returns:
        Dict with parsed fields, human-readable names, and validation
    """
    fields = {}
    raw_fields = {}

    for pair in msg.strip("|").split("|"):
        if "=" in pair:
            tag_str, val = pair.split("=", 1)
            try:
                tag = int(tag_str)
                raw_fields[tag] = val
                name = FIX_TAGS.get(tag, f"Tag{tag}")
                fields[name] = val
            except ValueError:
                continue

    # Decode known enums
    decoded = dict(fields)
    if "MsgType" in decoded:
        decoded["MsgType_Name"] = MSG_TYPES.get(decoded["MsgType"], "Unknown")
    if "Side" in decoded:
        decoded["Side_Name"] = SIDE.get(decoded["Side"], "Unknown")
    if "OrdType" in decoded:
        decoded["OrdType_Name"] = ORD_TYPE.get(decoded["OrdType"], "Unknown")
    if "TimeInForce" in decoded:
        decoded["TimeInForce_Name"] = TIF.get(decoded["TimeInForce"], "Unknown")
    if "OrdStatus" in decoded:
        decoded["OrdStatus_Name"] = ORD_STATUS.get(decoded["OrdStatus"], "Unknown")

    return {"parsed": decoded, "raw_tags": raw_fields, "field_count": len(raw_fields)}


def simulate_new_order(symbol: str, side: str, qty: int, ord_type: str = "2",
                       price: float = 0.0, tif: str = "0") -> Dict:
    """
    Simulate sending a NewOrderSingle and receiving ExecutionReports.

    Args:
        symbol: Instrument symbol (e.g., 'AAPL')
        side: '1' (Buy) or '2' (Sell)
        qty: Order quantity
        ord_type: '1' (Market) or '2' (Limit)
        price: Limit price (required for limit orders)
        tif: TimeInForce ('0'=Day, '1'=GTC, '3'=IOC)

    Returns:
        Dict with order details, FIX messages sent/received, order state
    """
    cl_ord_id = f"QC-{uuid.uuid4().hex[:8].upper()}"
    order_id = f"EX-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc).strftime("%Y%m%d-%H:%M:%S.%f")[:-3]

    # Build NewOrderSingle
    nos_fields = {
        11: cl_ord_id, 21: "1", 55: symbol, 54: side,
        38: str(qty), 40: ord_type, 59: tif, 60: now
    }
    if ord_type == "2" and price > 0:
        nos_fields[44] = f"{price:.2f}"

    nos_msg = build_fix_message("D", nos_fields)

    # Simulate: market orders fill immediately, limit orders get ack then fill
    sim_price = price if price > 0 else round(100 + (hash(symbol) % 900) / 10, 2)

    # Execution Report: New (ack)
    ack_fields = {
        11: cl_ord_id, 37: order_id, 17: f"EXEC-{uuid.uuid4().hex[:6].upper()}",
        55: symbol, 54: side, 150: "0", 39: "0",
        38: str(qty), 14: "0", 151: str(qty), 6: "0", 60: now
    }
    ack_msg = build_fix_message("8", ack_fields)

    # Execution Report: Filled
    fill_fields = {
        11: cl_ord_id, 37: order_id, 17: f"EXEC-{uuid.uuid4().hex[:6].upper()}",
        55: symbol, 54: side, 150: "F", 39: "2",
        38: str(qty), 14: str(qty), 151: "0",
        31: f"{sim_price:.2f}", 32: str(qty), 6: f"{sim_price:.2f}", 60: now
    }
    fill_msg = build_fix_message("8", fill_fields)

    order = {
        "cl_ord_id": cl_ord_id, "order_id": order_id, "symbol": symbol,
        "side": SIDE.get(side, side), "qty": qty, "ord_type": ORD_TYPE.get(ord_type, ord_type),
        "price": price, "fill_price": sim_price, "status": "Filled",
        "tif": TIF.get(tif, tif)
    }
    _orders[cl_ord_id] = order

    return {
        "order": order,
        "messages": {
            "new_order_single": nos_msg,
            "execution_report_ack": ack_msg,
            "execution_report_fill": fill_msg
        },
        "message_count": 3
    }


def get_order_status(cl_ord_id: str) -> Dict:
    """
    Get the current status of a simulated order.

    Args:
        cl_ord_id: Client order ID

    Returns:
        Order state dict or error
    """
    if cl_ord_id in _orders:
        return _orders[cl_ord_id]
    return {"error": f"Order {cl_ord_id} not found"}


def list_all_orders() -> List[Dict]:
    """List all simulated orders in the gateway."""
    return list(_orders.values())
