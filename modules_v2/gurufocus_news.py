"""
GuruFocus News Module — Stock-specific news feed.

Source: gurufocus.com/data API (Enterprise)
Cadence: Hourly
Granularity: Symbol-level
Tags: News, US Equities, GuruFocus
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qcd_platform.pipeline.base_module import BaseModule, DataPoint
from modules_v2.gurufocus_client import get_news
from modules_v2.gurufocus_symbol_map import get_all_mappings

logger = logging.getLogger("quantclaw.gurufocus.news")

TOP_SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B",
    "JPM", "V", "UNH", "MA", "HD", "PG", "XOM", "JNJ", "AVGO", "LLY",
    "COST", "ABBV", "MRK", "KO", "PEP", "WMT", "BAC", "CRM", "AMD",
    "NFLX", "TMO", "ORCL",
]


class GurufocusNews(BaseModule):
    name = "gurufocus_news"
    display_name = "GuruFocus — Stock News"
    cadence = "hourly"
    granularity = "symbol"
    tags = ["News", "US Equities"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        mappings = get_all_mappings()
        target_symbols = symbols or TOP_SYMBOLS
        points = []
        errors = 0

        for sym in target_symbols:
            gf_sym = mappings.get(sym)
            if not gf_sym:
                gf_sym = f"NAS:{sym}"

            try:
                data = get_news(gf_sym)
                if not data:
                    continue

                articles = data if isinstance(data, list) else data.get("data", data.get("news", []))
                if not isinstance(articles, list):
                    continue

                for article in articles[:10]:
                    title = article.get("title", article.get("headline", ""))
                    pub_date = article.get("date", article.get("published_at", ""))

                    points.append(DataPoint(
                        ts=datetime.now(timezone.utc),
                        symbol=sym,
                        cadence="hourly",
                        tier="bronze",
                        payload={
                            "source": "gurufocus",
                            "gf_symbol": gf_sym,
                            "title": title,
                            "url": article.get("url", article.get("link", "")),
                            "published": pub_date,
                            "summary": (article.get("summary", article.get("description", "")))[:500],
                        },
                    ))
            except Exception as e:
                errors += 1
                logger.warning(f"News failed for {gf_sym}: {e}")

        logger.info(f"News fetched: {len(points)} articles from {len(target_symbols)} symbols, {errors} errors")
        return points


if __name__ == "__main__":
    mod = GurufocusNews()
    result = mod.run()
    print(json.dumps(result, indent=2, default=str))
