"""
GuruFocus Insider Trading Module — Daily insider trades (buys/sells) with enrichment.

Source: gurufocus.com/data API (Enterprise)
Cadence: Daily
Granularity: Market-level (fetches by date, not symbol)
Tags: Insider, US Equities, GuruFocus
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone, timedelta, date
from typing import List, Optional, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint
from qcd_platform.pipeline.db import execute_query
from modules_v2.gurufocus_client import get_insider_data

logger = logging.getLogger("quantclaw.gurufocus.insider")


def _safe_float(val) -> Optional[float]:
    if val is None or val == "" or val == "N/A":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


class GurufocusInsider(BaseModule):
    name = "gurufocus_insider_trading"
    display_name = "GuruFocus — Insider Trading"
    cadence = "daily"
    granularity = "market"
    tags = ["Insider", "US Equities"]

    LOOKBACK_DAYS = 3

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        points = []
        errors = 0
        today = date.today()

        for days_back in range(self.LOOKBACK_DAYS):
            target_date = today - timedelta(days=days_back)
            date_str = target_date.strftime("%Y-%m-%d")

            try:
                data = get_insider_data(date_str)
                if not data:
                    continue

                trades = data if isinstance(data, list) else data.get("data", data.get("trades", []))
                if not isinstance(trades, list):
                    continue

                for trade in trades:
                    sym = trade.get("symbol", trade.get("ticker", ""))
                    if not sym:
                        continue

                    etoro_sym = sym.split(":")[-1] if ":" in sym else sym

                    trade_date_str = trade.get("date", trade.get("trade_date", date_str))
                    try:
                        td = datetime.strptime(str(trade_date_str)[:10], "%Y-%m-%d").date()
                    except ValueError:
                        td = target_date

                    self._store_trade(etoro_sym, sym, trade, td)

                    points.append(DataPoint(
                        ts=datetime.combine(td, datetime.min.time(), tzinfo=timezone.utc),
                        symbol=etoro_sym,
                        cadence="daily",
                        tier="bronze",
                        payload={
                            "source": "gurufocus",
                            "gf_symbol": sym,
                            "insider_name": trade.get("insider_name", trade.get("name", "")),
                            "insider_title": trade.get("insider_title", trade.get("title", "")),
                            "trade_type": trade.get("type", trade.get("transaction_type", "")),
                            "shares": _safe_float(trade.get("shares", trade.get("amount"))),
                            "price": _safe_float(trade.get("price", trade.get("avg_price"))),
                            "total_value": _safe_float(trade.get("value", trade.get("total_value"))),
                            "trade_date": str(td),
                        },
                    ))

            except Exception as e:
                errors += 1
                logger.warning(f"Insider data failed for {date_str}: {e}")

        logger.info(f"Insider trades fetched: {len(points)} trades, {errors} errors")
        return points

    def _store_trade(self, etoro_sym: str, gf_sym: str, trade: Dict, trade_date):
        filing_date_str = trade.get("filing_date")
        filing_date = None
        if filing_date_str:
            try:
                filing_date = datetime.strptime(str(filing_date_str)[:10], "%Y-%m-%d").date()
            except ValueError:
                pass

        execute_query(
            """INSERT INTO gf_insider_trades (symbol, gf_symbol, insider_name, insider_title,
                trade_type, shares, price, total_value, trade_date, filing_date, payload)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                etoro_sym, gf_sym,
                trade.get("insider_name", trade.get("name", "")),
                trade.get("insider_title", trade.get("title", "")),
                trade.get("type", trade.get("transaction_type", "")),
                _safe_float(trade.get("shares", trade.get("amount"))),
                _safe_float(trade.get("price", trade.get("avg_price"))),
                _safe_float(trade.get("value", trade.get("total_value"))),
                trade_date, filing_date,
                json.dumps(trade, default=str)[:5000],
            ),
        )


if __name__ == "__main__":
    mod = GurufocusInsider()
    result = mod.run()
    print(json.dumps(result, indent=2, default=str))
