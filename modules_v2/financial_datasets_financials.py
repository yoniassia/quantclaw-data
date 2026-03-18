"""
Financial Datasets API — Income Statements & Financial Metrics

Source: financialdatasets.ai
Cadence: Quarterly
Granularity: Symbol-level
Tags: US Equities, Fundamentals, Earnings
"""
import os
import requests
from datetime import datetime, timezone
from typing import List

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint
from qcd_platform.pipeline.db import execute_query

API_KEY = os.getenv("FINANCIAL_DATASETS_API_KEY", "f4cd5217-2afe-4d8e-9031-1328633c8532")
BASE_URL = "https://api.financialdatasets.ai"


class FinancialDatasetsFinancials(BaseModule):
    name = "financial_datasets_financials"
    display_name = "Financial Datasets — Income Statements"
    cadence = "quarterly"
    granularity = "symbol"
    tags = ["US Equities", "Fundamentals", "Earnings"]

    def _get_symbols(self) -> List[str]:
        rows = execute_query(
            """SELECT symbol FROM symbol_universe
               WHERE asset_class = 'stocks' AND is_active = true
               AND symbol NOT LIKE '%.%'
               ORDER BY symbol LIMIT 200""",
            fetch=True,
        )
        return [r["symbol"] for r in (rows or [])]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        if symbols is None:
            symbols = self._get_symbols()[:50]

        headers = {"X-API-KEY": API_KEY}
        points = []

        for symbol in symbols:
            try:
                url = f"{BASE_URL}/financials/income-statements?ticker={symbol}&period=quarterly&limit=4"
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code != 200:
                    continue

                data = resp.json()
                statements = data.get("income_statements", [])
                for stmt in statements:
                    report_date = stmt.get("report_period") or stmt.get("date")
                    if not report_date:
                        continue

                    try:
                        ts = datetime.fromisoformat(report_date).replace(tzinfo=timezone.utc)
                    except (ValueError, TypeError):
                        ts = datetime.now(timezone.utc)

                    points.append(DataPoint(
                        ts=ts,
                        symbol=symbol,
                        cadence="quarterly",
                        payload={
                            "revenue": stmt.get("revenue"),
                            "gross_profit": stmt.get("gross_profit"),
                            "operating_income": stmt.get("operating_income"),
                            "net_income": stmt.get("net_income"),
                            "eps": stmt.get("earnings_per_share") or stmt.get("eps_diluted"),
                            "eps_diluted": stmt.get("eps_diluted"),
                            "ebitda": stmt.get("ebitda"),
                            "operating_expense": stmt.get("operating_expense"),
                            "period": stmt.get("period"),
                            "fiscal_year": stmt.get("fiscal_year"),
                            "report_period": report_date,
                            "source": "financial_datasets",
                        },
                    ))
            except requests.RequestException as e:
                self.logger.warning(f"Failed for {symbol}: {e}")
                continue

        return points

    def validate(self, clean_points: List[DataPoint]):
        report = super().validate(clean_points)
        if clean_points:
            with_revenue = sum(1 for p in clean_points if p.payload.get("revenue"))
            report.completeness = (with_revenue / len(clean_points) * 100)
            with_eps = sum(1 for p in clean_points if p.payload.get("eps") is not None)
            report.accuracy = (with_eps / len(clean_points) * 100)
        report.compute_overall()
        return report
