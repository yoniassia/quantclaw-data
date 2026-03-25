"""
eToro SAPI Instruments — Bronze/Silver/Gold pipeline for full instrument payloads.

Discovery via eToro Public API closing-prices; detail via SAPI per instrument.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import logging
import math
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import aiohttp

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from qcd_platform.pipeline import db
from qcd_platform.pipeline.base_module import BaseModule, DataPoint, QualityReport

logger = logging.getLogger("quantclaw.module.etoro-sapi-instruments")

# --- eToro standalone pipeline config (SAPI_BASE, public API URL, headers) ---
_ETORO_CFG_PATH = Path(os.getenv("ETORO_SAPI_CONFIG", "/home/quant/apps/etoro-sapi-pipeline/config.py"))
_spec = importlib.util.spec_from_file_location("etoro_sapi_cfg", _ETORO_CFG_PATH)
_etoro_cfg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_etoro_cfg)
SAPI_BASE: str = getattr(_etoro_cfg, "SAPI_BASE", "https://www.etoro.com/sapi/instrumentsinfo/instruments")
SAPI_HEADERS: Dict[str, str] = dict(getattr(_etoro_cfg, "SAPI_HEADERS", {}))
ETORO_PUBLIC_API: str = getattr(_etoro_cfg, "ETORO_PUBLIC_API", "https://public-api.etoro.com/api/v1")
SAPI_TIMEOUT = getattr(_etoro_cfg, "SAPI_TIMEOUT", 15)
SAPI_MAX_RETRIES = getattr(_etoro_cfg, "SAPI_MAX_RETRIES", 3)

CREDENTIAL_PATHS = [
    Path(os.getenv("ETORO_CREDENTIALS_PATH", "")) if os.getenv("ETORO_CREDENTIALS_PATH") else None,
    Path.home() / ".credentials" / "etoro-api.json",
    Path("/home/quant/.credentials/etoro-api.json"),
]
CREDENTIAL_PATHS = [p for p in CREDENTIAL_PATHS if p]

BRONZE_DIR = Path("/home/quant/apps/etoro-sapi-pipeline/data/bronze")


def _discover_from_bronze_cache() -> List[int]:
    """Read instrument IDs from existing bronze data files (pick dir with most files)."""
    if not BRONZE_DIR.exists():
        return []
    best_ids: List[int] = []
    for date_dir in BRONZE_DIR.iterdir():
        if not date_dir.is_dir():
            continue
        ids = []
        for f in date_dir.iterdir():
            if f.name.endswith(".json.gz"):
                num_part = f.name.replace(".json.gz", "")
                if num_part.isdigit():
                    ids.append(int(num_part))
        if len(ids) > len(best_ids):
            best_ids = ids
    return sorted(best_ids)


def _load_etoro_api_keys() -> Tuple[str, str]:
    api_key = os.getenv("ETORO_API_KEY", "") or os.getenv("ETORO_PUBLIC_KEY", "")
    user_key = os.getenv("ETORO_USER_KEY", "")
    for base in CREDENTIAL_PATHS:
        try:
            if not base or not base.is_file():
                continue
            data = json.loads(base.read_text(encoding="utf-8"))
            api_key = api_key or data.get("public-key") or data.get("x-api-key") or ""
            user_key = user_key or data.get("x-user-key") or data.get("user-key") or ""
        except (OSError, json.JSONDecodeError):
            continue
    return api_key, user_key


def _pick(d: Dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def _num(d: Dict[str, Any], *base_keys: str) -> Optional[float]:
    """Match silver/etl: prefer -TTM, then -Annual, then bare key."""
    for base in base_keys:
        for suffix in ("-TTM", "-Annual", ""):
            key = f"{base}{suffix}" if suffix else base
            if key not in d:
                continue
            val = d[key]
            if val is None or val == "":
                continue
            try:
                x = float(val)
                if math.isnan(x) or math.isinf(x):
                    continue
                return x
            except (TypeError, ValueError):
                continue
    return None


def _str(d: Dict[str, Any], *keys: str) -> Optional[str]:
    for k in keys:
        v = _pick(d, k)
        if v is None:
            continue
        s = str(v).strip()
        if s:
            return s
    return None


def _int(d: Dict[str, Any], *base_keys: str) -> Optional[int]:
    f = _num(d, *base_keys)
    if f is None:
        return None
    try:
        return int(round(f))
    except (TypeError, ValueError):
        return None


def _strip_nulls(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if v is None:
                continue
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                continue
            cv = _strip_nulls(v)
            if cv is None:
                continue
            if isinstance(cv, dict) and not cv:
                continue
            if isinstance(cv, list) and not cv:
                continue
            out[k] = cv
        return out
    if isinstance(obj, list):
        return [_strip_nulls(x) for x in obj if x is not None]
    return obj


def normalize_sapi_payload(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Map raw SAPI JSON to normalized field names (Silver payload)."""
    cp = raw.get("ClosingPrices") or raw.get("closingPrices") or {}
    if not isinstance(cp, dict):
        cp = {}

    iid = _pick(raw, "internalInstrumentId", "InternalInstrumentId")
    symbol = _str(raw, "internalSymbolFull", "InternalSymbolFull") or (str(int(iid)) if iid is not None else None)

    current = _num(raw, "currentRate", "CurrentRate")
    close_p = _num(raw, "internalClosingPrice", "InternalClosingPrice")
    day_high = _num(raw, "lastHigh", "LastHigh") or _num(cp, "DayHigh", "dayHigh")
    day_low = _num(raw, "lastLow", "LastLow") or _num(cp, "DayLow", "dayLow")
    volume = _num(raw, "lastVolume", "LastVolume") or _num(cp, "Volume", "volume")

    high_52w = _num(raw, "highPriceLast52Weeks", "52WeekHigh", "HighPriceLast52Weeks")
    low_52w = _num(raw, "lowPriceLast52Weeks", "52WeekLow", "LowPriceLast52Weeks")
    pct_hi = None
    pct_lo = None
    if current is not None and high_52w and high_52w > 0:
        pct_hi = (current / high_52w - 1.0) * 100.0
    if current is not None and low_52w and low_52w > 0:
        pct_lo = (current / low_52w - 1.0) * 100.0

    market_cap = _int(raw, "marketCapitalization", "marketCapInUSD", "MarketCapitalization")

    out: Dict[str, Any] = {
        "symbol": symbol,
        "name": _str(raw, "internalInstrumentDisplayName", "FullName", "fullName"),
        "exchange": _str(raw, "internalExchangeName", "ExchangeID", "internalExchangeId"),
        "sector": _str(raw, "sectorNameId", "Sector", "umbrellaSector"),
        "industry": _str(raw, "internalStockIndustryName", "industryNameId", "Industry", "industryName-TTM"),
        "asset_class": _str(raw, "internalAssetClassName", "InternalAssetClassName"),
        "current_price": current,
        "close_price": close_p,
        "day_high": day_high,
        "day_low": day_low,
        "volume": volume,
        "market_open": _pick(cp, "IsMarketOpen", "isMarketOpen"),
        "ma_5d": _num(raw, "movingAverage5DayAvg", "5DayMovingAverage", "MovingAverage5DayAvg"),
        "ma_10d": _num(raw, "movingAverage10DayAvg", "10DayMovingAverage"),
        "ma_50d": _num(raw, "movingAverage50DayAvg", "50DayMovingAverage"),
        "ma_200d": _num(raw, "movingAverage200DayAvg", "200DayMovingAverage"),
        "ma_10w": _num(raw, "10WeekMovingAverage", "movingAverage10WeekAvg"),
        "ma_30w": _num(raw, "30WeekMovingAverage", "movingAverage30WeekAvg"),
        "high_52w": high_52w,
        "low_52w": low_52w,
        "pct_from_52w_high": pct_hi,
        "pct_from_52w_low": pct_lo,
        "pe_ratio": _num(raw, "peRatio", "PeRatio"),
        "pb_ratio": _num(raw, "priceToBook", "priceToBookRatio", "PriceToBook"),
        "ps_ratio": _num(raw, "priceToSales", "priceToSalesRatio"),
        "price_to_cashflow": _num(raw, "priceToCashFlow", "priceToCashFlowPerShare"),
        "ev_ebitda": _num(raw, "enterpriseValuetoEBITDA", "enterpriseValueToEBITDA"),
        "peg_ratio": _num(raw, "pegRatio", "PegRatio"),
        "market_cap": market_cap,
        "gross_margin": _num(raw, "grossMargin", "grossIncomeMargin", "grossProfitMargin"),
        "operating_margin": _num(raw, "operatingMargin", "OperatingMargin"),
        "profit_margin": _num(raw, "netProfitMargin", "netMargin", "NetMargin"),
        "roe": _num(raw, "returnOnEquity", "returnOnCommonEquity", "ReturnOnEquity"),
        "roa": _num(raw, "returnOnAssets", "ReturnOnAssets"),
        "debt_to_equity": _num(raw, "debtToEquity", "totalDebtToEquityRatio", "debtEquityRatio"),
        "revenue_growth_1y": _num(raw, "1YearAnnualRevenueGrowthRate"),
        "revenue_growth_3y": _num(raw, "3YearAnnualRevenueGrowthRate"),
        "earnings_growth_1y": _num(raw, "1YearAnnualIncomeGrowthRate", "epsGrowth1Year"),
        "analyst_consensus": _pick(raw, "tipranksConsensus", "tipranks_consensus"),
        "analyst_count": _int(raw, "tipranksTotalAnalysts"),
        "target_price_mean": _num(raw, "tipranksTargetPrice"),
        "target_price_high": _num(raw, "tipranksHighPriceTarget"),
        "target_price_low": _num(raw, "tipranksLowPriceTarget"),
        "upside_pct": _num(raw, "tipranksTargetPriceUpside"),
        "trader_change_7d": _num(raw, "traders7DayChange", "traderChange7d"),
        "trader_change_14d": _num(raw, "traders14DayChange", "traderChange14d"),
        "trader_change_30d": _num(raw, "traders30DayChange", "traderChange30d"),
        "popularity": _int(raw, "popularityUniques"),
        "esg_total": _num(raw, "arabesqueESGTotal", "ArabesqueESGTotal"),
        "esg_environmental": _num(raw, "arabesqueESGEnvironment"),
        "esg_social": _num(raw, "arabesqueESGSocial"),
        "esg_governance": _num(raw, "arabesqueESGGovernance"),
        "beta_12m": _num(raw, "beta12Month", "beta12m"),
        "beta_24m": _num(raw, "beta24Month"),
        "beta_36m": _num(raw, "beta36Month"),
        "beta_60m": _num(raw, "beta60Month"),
        "etoro_instrument_id": int(iid) if iid is not None else None,
    }

    tr = raw.get("tipranks_consensus")
    if isinstance(tr, dict) and out.get("analyst_consensus") is None:
        out["analyst_consensus"] = _pick(tr, "consensus", "Consensus", "rating")

    return _strip_nulls(out)  # type: ignore[return-value]


class _AsyncRateLimiter:
    """Serializes request starts to respect max N requests per second."""

    def __init__(self, per_second: float):
        self._interval = 1.0 / per_second
        self._lock = asyncio.Lock()
        self._next = 0.0

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = max(0.0, self._next - now)
            if wait:
                await asyncio.sleep(wait)
            self._next = time.monotonic() + self._interval


class EtoroSapiInstrumentsModule(BaseModule):
    name = "etoro-sapi-instruments"
    display_name = "eToro SAPI Instruments"
    cadence = "4h"
    granularity = "symbol"
    tags = ["US Equities", "Fundamentals", "Multi-Asset"]

    def register(self) -> int:
        self.module_id = db.register_module(
            name=self.name,
            display_name=self.display_name or self.name,
            source_file="modules_v2/etoro_sapi_instruments.py",
            cadence=self.cadence,
            granularity=self.granularity,
            tags=self.tags,
        )
        return self.module_id

    async def _discover_ids(self, session: aiohttp.ClientSession) -> List[int]:
        api_key, user_key = _load_etoro_api_keys()
        url = f"{ETORO_PUBLIC_API}/market-data/closing-prices"
        headers = {
            "x-api-key": api_key,
            "x-user-key": user_key,
            "x-request-id": str(uuid.uuid4()),
        }
        try:
            async with session.get(
                url, headers=headers, timeout=aiohttp.ClientTimeout(total=45)
            ) as resp:
                if resp.status != 200:
                    self.logger.warning("Closing-prices discovery HTTP %s", resp.status)
                    return []
                data = await resp.json()
                if not isinstance(data, list):
                    return []
                ids = sorted(
                    {
                        int(x)
                        for x in (
                            (item.get("InstrumentId") or item.get("instrumentId"))
                            for item in data
                        )
                        if x is not None
                    }
                )
                self.logger.info("Discovered %s instrument IDs from public API", len(ids))
                return ids
        except Exception as e:
            self.logger.warning("Instrument discovery failed: %s", e)
            return []

    async def _discover_ids_standalone(self) -> List[int]:
        async with aiohttp.ClientSession() as session:
            return await self._discover_ids(session)

    async def _fetch_one(
        self,
        session: aiohttp.ClientSession,
        instrument_id: int,
        sem: asyncio.Semaphore,
        limiter: _AsyncRateLimiter,
    ) -> Optional[Dict[str, Any]]:
        url = f"{SAPI_BASE}/{instrument_id}"
        async with sem:
            await limiter.acquire()
            for attempt in range(SAPI_MAX_RETRIES):
                try:
                    async with session.get(
                        url,
                        headers=SAPI_HEADERS,
                        timeout=aiohttp.ClientTimeout(total=SAPI_TIMEOUT),
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json(content_type=None)
                            if data and isinstance(data, dict) and len(data) > 10:
                                return data
                            return None
                        if resp.status == 429:
                            await asyncio.sleep(2 ** (attempt + 2))
                        elif resp.status in (400, 404):
                            return None
                except asyncio.TimeoutError:
                    self.logger.debug("Timeout instrument %s attempt %s", instrument_id, attempt + 1)
                except Exception as e:
                    self.logger.debug("Fetch %s: %s", instrument_id, e)
                await asyncio.sleep(1.0)
        return None

    async def _fetch_all_async(self, instrument_ids: Sequence[int]) -> List[Tuple[int, Dict[str, Any]]]:
        sem = asyncio.Semaphore(10)
        limiter = _AsyncRateLimiter(50.0)

        async with aiohttp.ClientSession() as session:
            tasks = [self._fetch_one(session, iid, sem, limiter) for iid in instrument_ids]
            results_raw = await asyncio.gather(*tasks)

        out: List[Tuple[int, Dict[str, Any]]] = []
        for iid, data in zip(instrument_ids, results_raw):
            if data:
                out.append((iid, data))
        return out

    def _resolve_instrument_ids(self, symbols: Optional[List[str]]) -> List[int]:
        if symbols:
            ids: List[int] = []
            for s in symbols:
                s = str(s).strip()
                if s.isdigit():
                    ids.append(int(s))
            if ids:
                return ids
            self.logger.warning("No numeric instrument IDs in symbols=%s; falling back to discovery", symbols)

        try:
            discovered = asyncio.run(self._discover_ids_standalone())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                discovered = loop.run_until_complete(self._discover_ids_standalone())
            finally:
                loop.close()
                asyncio.set_event_loop(None)

        if discovered:
            return discovered

        bronze_ids = _discover_from_bronze_cache()
        if bronze_ids:
            self.logger.info("Discovered %s instrument IDs from bronze cache", len(bronze_ids))
            return bronze_ids

        self.logger.warning("No discovery source available — fetching top ~5000 IDs by range")
        return list(range(1001, 6000))

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        ids = self._resolve_instrument_ids(symbols)
        if not ids:
            return []

        try:
            rows = asyncio.run(self._fetch_all_async(ids))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                rows = loop.run_until_complete(self._fetch_all_async(ids))
            finally:
                loop.close()
                asyncio.set_event_loop(None)

        ts = datetime.now(timezone.utc)
        points: List[DataPoint] = []
        for iid, raw in rows:
            sym = _str(raw, "internalSymbolFull", "InternalSymbolFull") or str(iid)
            points.append(
                DataPoint(
                    ts=ts,
                    symbol=sym[:50] if sym else str(iid),
                    cadence=self.cadence,
                    tier="bronze",
                    payload=raw,
                )
            )
        return points

    def clean(self, raw_points: List[DataPoint]) -> List[DataPoint]:
        cleaned = super().clean(raw_points)
        for p in cleaned:
            if not isinstance(p.payload, dict):
                continue
            norm = normalize_sapi_payload(p.payload)
            norm["sapi_raw_keys"] = len(p.payload)
            p.payload = norm
        return [p for p in cleaned if p.payload.get("symbol")]

    def validate(self, clean_points: List[DataPoint]) -> QualityReport:
        report = super().validate(clean_points)
        if not clean_points:
            report.compute_overall()
            return report

        key_fields = ("symbol", "current_price", "close_price", "name")
        complete = 0
        for p in clean_points:
            pl = p.payload or {}
            if sum(1 for k in key_fields if pl.get(k) is not None) >= 3:
                complete += 1
        report.completeness = complete / len(clean_points) * 100.0

        today = datetime.now(timezone.utc).date()
        timely = 0
        for p in clean_points:
            pl = p.payload or {}
            if p.ts.date() == today:
                timely += 1
            elif pl.get("current_price") is not None and pl.get("close_price") is not None:
                timely += 1
        report.timeliness = timely / len(clean_points) * 100.0

        sane = 0
        for p in clean_points:
            px = (p.payload or {}).get("current_price")
            if isinstance(px, (int, float)) and 1e-6 < float(px) < 1e7:
                sane += 1
        report.accuracy = sane / len(clean_points) * 100.0

        if report.completeness < 70:
            report.issues.append(f"Low field completeness: {report.completeness:.1f}%")
        if report.timeliness < 50:
            report.issues.append(f"Timeliness weak: {report.timeliness:.1f}%")
        if report.accuracy < 80:
            report.issues.append(f"Price bounds check: {report.accuracy:.1f}%")

        report.compute_overall()
        return report
