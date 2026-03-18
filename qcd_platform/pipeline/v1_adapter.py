"""
V1 Adapter — Wraps legacy function-based modules as BaseModule subclasses.

Instead of rewriting 993 modules from scratch, this adapter:
1. Dynamically imports the v1 module
2. Calls its main function (get_data, fetch_*, get_*)
3. Converts the return value (dict/DataFrame/list) into DataPoint objects
4. Feeds them through the standard Bronze→Silver→Gold pipeline
"""
import importlib.util
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd

from .base_module import BaseModule, DataPoint

logger = logging.getLogger("quantclaw.v1_adapter")

V1_MODULES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "modules"
)


class V1ModuleAdapter(BaseModule):
    """Generic adapter that wraps any v1 module as a v2 BaseModule."""

    def __init__(self, module_name: str, main_callable: str = None,
                 cadence: str = "daily", granularity: str = "symbol",
                 tags: List[str] = None, call_args: Dict = None):
        self.name = module_name
        self.display_name = module_name.replace("_", " ").title()
        self.cadence = cadence
        self.granularity = granularity
        self.tags = tags or ["US Equities"]
        self._main_callable_name = main_callable
        self._call_args = call_args or {}
        self._v1_module = None
        self._v1_callable = None
        super().__init__()

    def _load_v1_module(self):
        if self._v1_module is not None:
            return

        module_path = os.path.join(V1_MODULES_DIR, f"{self.name}.py")
        if not os.path.exists(module_path):
            raise FileNotFoundError(f"V1 module not found: {module_path}")

        spec = importlib.util.spec_from_file_location(
            f"v1_modules.{self.name}", module_path
        )
        mod = importlib.util.module_from_spec(spec)

        old_argv = sys.argv
        old_exit = sys.exit
        sys.argv = [module_path]
        sys.exit = lambda *a, **kw: None
        try:
            spec.loader.exec_module(mod)
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv
            sys.exit = old_exit

        self._v1_module = mod

        if self._main_callable_name:
            self._v1_callable = getattr(mod, self._main_callable_name, None)
        if self._v1_callable is None:
            for fn_name in ["get_data", "fetch_data", "fetch", "get_current_sentiment",
                            "get_latest", "main"]:
                fn = getattr(mod, fn_name, None)
                if callable(fn):
                    self._v1_callable = fn
                    self._main_callable_name = fn_name
                    break

        if self._v1_callable is None:
            for attr_name in dir(mod):
                if attr_name.startswith("_"):
                    continue
                attr = getattr(mod, attr_name)
                if callable(attr) and not isinstance(attr, type):
                    self._v1_callable = attr
                    self._main_callable_name = attr_name
                    break

        if self._v1_callable is None:
            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if isinstance(attr, type) and attr_name != "BaseModule":
                    instance = attr()
                    for method_name in ["get_data", "fetch", "run", "get"]:
                        method = getattr(instance, method_name, None)
                        if callable(method):
                            self._v1_callable = method
                            self._main_callable_name = f"{attr_name}.{method_name}"
                            break
                    if self._v1_callable:
                        break

    def _convert_to_datapoints(self, raw_data: Any, symbols: List[str] = None) -> List[DataPoint]:
        """Convert v1 output (dict/DataFrame/list/str) into DataPoint objects."""
        points = []
        now = datetime.now(timezone.utc)

        if raw_data is None:
            return points

        if isinstance(raw_data, pd.DataFrame):
            return self._convert_dataframe(raw_data, now)

        if isinstance(raw_data, dict):
            if "error" in raw_data:
                logger.warning(f"[{self.name}] V1 returned error: {raw_data['error']}")
                return points
            return self._convert_dict(raw_data, now)

        if isinstance(raw_data, list):
            return self._convert_list(raw_data, now)

        if isinstance(raw_data, (str, int, float)):
            points.append(DataPoint(
                ts=now, symbol=None, cadence=self.cadence,
                payload={"value": raw_data, "source": self.name},
            ))
            return points

        logger.warning(f"[{self.name}] Unhandled return type: {type(raw_data)}")
        return points

    def _convert_dataframe(self, df: pd.DataFrame, now: datetime) -> List[DataPoint]:
        points = []
        if df.empty:
            return points

        has_symbol = any(col in df.columns for col in ["symbol", "ticker", "Symbol", "Ticker"])
        symbol_col = next((c for c in ["symbol", "ticker", "Symbol", "Ticker"] if c in df.columns), None)

        has_date = any(col in df.columns for col in ["date", "Date", "timestamp", "ts"])
        date_col = next((c for c in ["date", "Date", "timestamp", "ts"] if c in df.columns), None)

        if df.index.name and df.index.name.lower() in ("date", "timestamp", "ts"):
            df = df.reset_index()
            date_col = df.columns[0]

        for _, row in df.head(500).iterrows():
            row_dict = {}
            for k, v in row.items():
                if pd.isna(v):
                    continue
                if hasattr(v, "item"):
                    v = v.item()
                row_dict[str(k)] = v

            symbol = row_dict.pop(symbol_col, None) if symbol_col else None
            ts = now
            if date_col and date_col in row_dict:
                try:
                    ts = pd.Timestamp(row_dict.pop(date_col)).to_pydatetime()
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                except Exception:
                    pass

            if isinstance(symbol, (list, dict)):
                symbol = None
            if symbol is not None:
                symbol = str(symbol)

            points.append(DataPoint(
                ts=ts, symbol=symbol, cadence=self.cadence,
                payload=row_dict,
            ))

        return points

    def _convert_dict(self, data: dict, now: datetime) -> List[DataPoint]:
        points = []

        if "data" in data and isinstance(data["data"], list):
            return self._convert_list(data["data"], now)

        is_nested_symbols = all(
            isinstance(v, dict) for v in data.values()
        ) and len(data) > 1

        if is_nested_symbols:
            for symbol, payload in data.items():
                if not isinstance(payload, dict):
                    continue
                ts = now
                for date_key in ("date", "timestamp", "ts"):
                    if date_key in payload:
                        try:
                            ts = pd.Timestamp(payload.pop(date_key)).to_pydatetime()
                            if ts.tzinfo is None:
                                ts = ts.replace(tzinfo=timezone.utc)
                        except Exception:
                            pass
                points.append(DataPoint(
                    ts=ts, symbol=str(symbol), cadence=self.cadence,
                    payload=payload,
                ))
        else:
            symbol = data.pop("symbol", data.pop("ticker", None))
            ts = now
            for date_key in ("date", "timestamp", "ts"):
                if date_key in data:
                    try:
                        ts = pd.Timestamp(data.pop(date_key)).to_pydatetime()
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                    except Exception:
                        pass
            if symbol is not None:
                symbol = str(symbol)
            points.append(DataPoint(
                ts=ts, symbol=symbol, cadence=self.cadence,
                payload=data,
            ))

        return points

    def _convert_list(self, data: list, now: datetime) -> List[DataPoint]:
        points = []
        for item in data[:500]:
            if isinstance(item, dict):
                symbol = item.pop("symbol", item.pop("ticker", None))
                ts = now
                for date_key in ("date", "timestamp", "ts", "period"):
                    if date_key in item:
                        try:
                            ts = pd.Timestamp(item.pop(date_key)).to_pydatetime()
                            if ts.tzinfo is None:
                                ts = ts.replace(tzinfo=timezone.utc)
                        except Exception:
                            pass
                if symbol is not None:
                    symbol = str(symbol)
                points.append(DataPoint(
                    ts=ts, symbol=symbol, cadence=self.cadence,
                    payload=item,
                ))
            elif isinstance(item, (int, float, str)):
                points.append(DataPoint(
                    ts=now, cadence=self.cadence,
                    payload={"value": item, "source": self.name},
                ))
        return points

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        self._load_v1_module()

        if self._v1_callable is None:
            raise RuntimeError(f"No callable found in v1 module: {self.name}")

        call_args = dict(self._call_args)

        import inspect
        try:
            sig = inspect.signature(self._v1_callable)
        except (ValueError, TypeError):
            sig = None

        if sig:
            required_params = [
                p for p in sig.parameters.values()
                if p.default is inspect.Parameter.empty
                and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
            ]
            for param in required_params:
                pname = param.name.lower()
                if pname in call_args:
                    continue
                if pname in ("self",):
                    continue
                if pname in ("ticker", "symbol"):
                    if symbols:
                        call_args[param.name] = symbols[0]
                    else:
                        call_args[param.name] = "AAPL"
                elif pname in ("tickers", "symbols"):
                    if symbols:
                        call_args[param.name] = symbols[:10]
                    else:
                        call_args[param.name] = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
                elif pname in ("model",):
                    call_args[param.name] = "default"
                elif pname in ("period", "timeframe"):
                    call_args[param.name] = "1y"
                elif pname in ("series_id",):
                    call_args[param.name] = "GDP"
                elif pname in ("series_ids",):
                    call_args[param.name] = ["CPIAUCSL", "UNRATE", "GDP"]
                elif pname in ("series",):
                    call_args[param.name] = "CPIAUCSL"
                elif pname in ("cik",):
                    call_args[param.name] = "0000320193"  # Apple
                elif pname in ("start_year",):
                    call_args[param.name] = "2024"
                elif pname in ("end_year",):
                    call_args[param.name] = "2026"
                elif pname in ("db", "database"):
                    call_args[param.name] = "main"
                elif pname in ("codes", "indicators"):
                    call_args[param.name] = ["GDP", "CPI"]
                elif pname in ("country", "country_code"):
                    call_args[param.name] = "US"
                elif pname in ("asset", "token", "coin"):
                    call_args[param.name] = "bitcoin"
                elif pname in ("exchange",):
                    call_args[param.name] = "NYSE"
                elif pname in ("freq", "frequency"):
                    call_args[param.name] = "quarterly"
                elif pname in ("api_key", "key", "token"):
                    pass  # skip auth params
                elif pname in ("date", "start_date"):
                    call_args[param.name] = "2025-01-01"
                elif pname in ("end_date",):
                    call_args[param.name] = "2026-03-18"
                elif pname in ("etf", "fund"):
                    call_args[param.name] = "SPY"
                elif pname in ("sector",):
                    call_args[param.name] = "Technology"
                elif pname in ("chain", "network"):
                    call_args[param.name] = "ethereum"
                elif pname in ("address", "wallet"):
                    call_args[param.name] = "0x0000000000000000000000000000000000000000"
                elif pname in ("url",):
                    pass  # skip URL params

            if symbols and self.granularity == "symbol":
                for param_name in ("ticker", "symbol", "tickers", "symbols"):
                    if param_name in sig.parameters and param_name not in call_args:
                        if param_name in ("ticker", "symbol"):
                            call_args[param_name] = symbols[0]
                        else:
                            call_args[param_name] = symbols[:10]

        old_exit = sys.exit
        sys.exit = lambda *a, **kw: None
        try:
            raw_data = self._v1_callable(**call_args)
        except (TypeError, SystemExit) as te:
            try:
                raw_data = self._v1_callable()
            except SystemExit:
                raw_data = None
            except Exception:
                raise RuntimeError(f"V1 callable {self._main_callable_name} failed: {te}")
        except Exception as e:
            raise RuntimeError(f"V1 callable {self._main_callable_name} failed: {e}")
        finally:
            sys.exit = old_exit

        return self._convert_to_datapoints(raw_data, symbols)


def create_adapter_from_manifest(entry: dict) -> V1ModuleAdapter:
    """Create a V1ModuleAdapter from a manifest entry."""
    return V1ModuleAdapter(
        module_name=entry["name"],
        main_callable=entry.get("main_callable"),
        cadence=entry.get("cadence", "daily"),
        granularity=entry.get("granularity", "symbol"),
        tags=entry.get("tags", ["US Equities"]),
    )
