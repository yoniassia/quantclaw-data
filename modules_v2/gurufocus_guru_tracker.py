"""
GuruFocus Guru Tracker — Track institutional investor (guru) portfolios and trades.

Source: gurufocus.com/data API (Enterprise)
Cadence: Weekly (13F filings are quarterly, but check weekly for updates)
Granularity: Guru-level → symbol-level holdings
Tags: Insider, Fundamentals, GuruFocus
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint
from qcd_platform.pipeline.db import execute_query
from modules_v2.gurufocus_client import get_guru_list, get_guru_data

logger = logging.getLogger("quantclaw.gurufocus.guru_tracker")


def _safe_float(val) -> Optional[float]:
    if val is None or val == "" or val == "N/A":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


class GurufocusGuruTracker(BaseModule):
    name = "gurufocus_guru_tracker"
    display_name = "GuruFocus — Guru Portfolio Tracker"
    cadence = "weekly"
    granularity = "global"
    tags = ["Insider", "Fundamentals"]

    TOP_GURUS_PAGES = 5  # 500 gurus

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        points = []
        errors = 0
        guru_count = 0

        for page in range(1, self.TOP_GURUS_PAGES + 1):
            try:
                guru_list = get_guru_list(page=page, per_page=100)
                gurus = guru_list if isinstance(guru_list, list) else guru_list.get("data", guru_list.get("gurus", []))
                if not gurus:
                    break

                for guru in gurus:
                    guru_id = str(guru.get("id", guru.get("guru_id", "")))
                    name = guru.get("name", guru.get("guru_name", "Unknown"))
                    if not guru_id:
                        continue

                    try:
                        detail = get_guru_data(guru_id)
                        if not detail:
                            continue

                        self._store_guru(guru_id, name, guru, detail)

                        holdings = detail.get("holdings", detail.get("portfolio", []))
                        if isinstance(holdings, dict):
                            holdings = holdings.get("data", [])

                        for holding in (holdings or [])[:50]:
                            sym = holding.get("symbol", holding.get("ticker", ""))
                            if not sym:
                                continue

                            self._store_holding(guru_id, sym, holding)

                            points.append(DataPoint(
                                ts=datetime.now(timezone.utc),
                                symbol=sym.split(":")[-1] if ":" in sym else sym,
                                cadence="weekly",
                                tier="bronze",
                                payload={
                                    "source": "gurufocus",
                                    "guru_id": guru_id,
                                    "guru_name": name,
                                    "gf_symbol": sym,
                                    "shares": _safe_float(holding.get("shares", holding.get("current_shares"))),
                                    "portfolio_weight": _safe_float(holding.get("weight", holding.get("portfolio_perc"))),
                                    "change_type": holding.get("change", holding.get("change_type")),
                                    "change_pct": _safe_float(holding.get("change_pct")),
                                },
                            ))

                        guru_count += 1
                    except Exception as e:
                        errors += 1
                        logger.warning(f"Guru detail failed for {guru_id}: {e}")

            except Exception as e:
                errors += 1
                logger.warning(f"Guru list page {page} failed: {e}")

        logger.info(f"Guru tracker: {guru_count} gurus, {len(points)} holdings, {errors} errors")
        return points

    def _store_guru(self, guru_id: str, name: str, basic: Dict, detail: Dict):
        firm = basic.get("firm", detail.get("firm", ""))
        num_holdings = detail.get("num_holdings", len(detail.get("holdings", [])))
        portfolio_value = _safe_float(detail.get("portfolio_value", detail.get("equity")))
        portfolio_date_str = detail.get("portfolio_date", detail.get("date"))
        portfolio_date = None
        if portfolio_date_str:
            try:
                portfolio_date = datetime.strptime(str(portfolio_date_str)[:10], "%Y-%m-%d").date()
            except ValueError:
                pass

        execute_query(
            """INSERT INTO gf_gurus (guru_id, name, firm, portfolio_date, num_holdings, portfolio_value, payload)
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (guru_id) DO UPDATE SET
                name = EXCLUDED.name, firm = EXCLUDED.firm,
                portfolio_date = EXCLUDED.portfolio_date,
                num_holdings = EXCLUDED.num_holdings,
                portfolio_value = EXCLUDED.portfolio_value,
                payload = EXCLUDED.payload,
                fetched_at = NOW()""",
            (guru_id, name, firm, portfolio_date, num_holdings, portfolio_value,
             json.dumps({**basic, **detail}, default=str)[:10000]),
        )

    def _store_holding(self, guru_id: str, gf_sym: str, holding: Dict):
        etoro_sym = gf_sym.split(":")[-1] if ":" in gf_sym else gf_sym
        portfolio_date_str = holding.get("date", holding.get("portfolio_date"))
        portfolio_date = None
        if portfolio_date_str:
            try:
                portfolio_date = datetime.strptime(str(portfolio_date_str)[:10], "%Y-%m-%d").date()
            except ValueError:
                pass

        execute_query(
            """INSERT INTO gf_guru_holdings (guru_id, symbol, gf_symbol, portfolio_date,
                shares, portfolio_weight, change_type, change_pct,
                current_price, market_value, payload)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (guru_id, symbol, portfolio_date) DO UPDATE SET
                shares = EXCLUDED.shares, portfolio_weight = EXCLUDED.portfolio_weight,
                payload = EXCLUDED.payload, fetched_at = NOW()""",
            (
                guru_id, etoro_sym, gf_sym, portfolio_date,
                _safe_float(holding.get("shares", holding.get("current_shares"))),
                _safe_float(holding.get("weight", holding.get("portfolio_perc"))),
                holding.get("change", holding.get("change_type")),
                _safe_float(holding.get("change_pct")),
                _safe_float(holding.get("price", holding.get("current_price"))),
                _safe_float(holding.get("value", holding.get("market_value"))),
                json.dumps(holding, default=str)[:5000],
            ),
        )


if __name__ == "__main__":
    mod = GurufocusGuruTracker()
    result = mod.run()
    print(json.dumps(result, indent=2, default=str))
