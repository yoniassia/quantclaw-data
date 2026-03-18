#!/usr/bin/env python3
"""
Kafka consumer that triggers Platinum enrichment when Gold modules complete.

Listens on: quantclaw.pipeline.gold.*
Triggers: platinum_enriched.get_platinum() for each affected symbol.

Run: python3 -m qcd_platform.scripts.platinum_consumer
"""
import json
import logging
import os
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("quantclaw.platinum_consumer")

GOLD_TOPICS = [
    "quantclaw.pipeline.gold.us_equities",
    "quantclaw.pipeline.gold.fundamentals",
    "quantclaw.pipeline.gold.earnings",
    "quantclaw.pipeline.gold.sentiment",
    "quantclaw.pipeline.gold.corporate_actions",
    "quantclaw.pipeline.gold.macro",
]

DEBOUNCE_SECONDS = 300  # wait 5 min before refreshing same symbol


def run_consumer():
    from kafka import KafkaConsumer

    consumer = KafkaConsumer(
        *GOLD_TOPICS,
        bootstrap_servers="localhost:9092",
        group_id="platinum-enrichment",
        auto_offset_reset="latest",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        consumer_timeout_ms=10000,
        enable_auto_commit=True,
    )

    logger.info(f"Platinum consumer started, listening on {len(GOLD_TOPICS)} topics")

    last_refresh = defaultdict(float)

    from modules.platinum_enriched import get_platinum, TOP_200

    universe_set = set(t.upper() for t in TOP_200)

    try:
        while True:
            records = consumer.poll(timeout_ms=5000)
            symbols_to_refresh = set()

            for tp, messages in records.items():
                for msg in messages:
                    data = msg.value
                    module_name = data.get("module", "")
                    logger.info(f"Gold completion: {module_name} (count={data.get('count')})")

                    # Extract symbols from the module's latest data
                    try:
                        import psycopg2
                        conn = psycopg2.connect(
                            dbname="quantclaw_data",
                            host="/var/run/postgresql",
                            user="quant",
                        )
                        cur = conn.cursor()
                        cur.execute("""
                            SELECT DISTINCT dp.symbol FROM data_points dp
                            JOIN modules m ON dp.module_id = m.id
                            WHERE m.name = %s AND dp.tier = 'gold'
                              AND dp.symbol IS NOT NULL
                              AND dp.ts > NOW() - INTERVAL '2 hours'
                        """, (module_name,))
                        for row in cur.fetchall():
                            sym = row[0].upper()
                            if sym in universe_set:
                                symbols_to_refresh.add(sym)
                        cur.close()
                        conn.close()
                    except Exception as e:
                        logger.warning(f"Failed to get symbols for {module_name}: {e}")

            now = time.time()
            refreshed = 0
            for sym in symbols_to_refresh:
                if now - last_refresh[sym] < DEBOUNCE_SECONDS:
                    continue
                try:
                    logger.info(f"Refreshing platinum for {sym}")
                    get_platinum(sym, use_cache=False)
                    last_refresh[sym] = time.time()
                    refreshed += 1
                except Exception as e:
                    logger.error(f"Platinum refresh failed for {sym}: {e}")

            if refreshed:
                logger.info(f"Refreshed {refreshed} platinum records")

            if not records:
                time.sleep(2)

    except KeyboardInterrupt:
        logger.info("Shutting down platinum consumer")
    finally:
        consumer.close()


if __name__ == "__main__":
    run_consumer()
