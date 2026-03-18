"""
Kafka producer for pipeline events.
Gracefully degrades if Kafka is unavailable.
"""
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("quantclaw.kafka")

_producer = None


def _get_producer():
    global _producer
    if _producer is not None:
        return _producer
    try:
        from kafka import KafkaProducer
        from ..config import KAFKA_CONFIG
        _producer = KafkaProducer(
            bootstrap_servers=KAFKA_CONFIG["bootstrap_servers"],
            client_id=KAFKA_CONFIG["client_id"],
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="all",
            retries=3,
            max_block_ms=5000,
        )
        logger.info("Kafka producer connected")
    except Exception as e:
        logger.warning(f"Kafka unavailable, events will be logged only: {e}")
        _producer = False  # sentinel to avoid retrying
    return _producer


def publish_event(topic: str, data: Dict[str, Any], key: str = None):
    """Publish an event to a Kafka topic. Falls back to logging if Kafka is down."""
    producer = _get_producer()
    if not producer:
        logger.debug(f"[kafka-fallback] {topic}: {json.dumps(data, default=str)[:200]}")
        return

    try:
        future = producer.send(topic, value=data, key=key)
        future.get(timeout=5)
    except Exception as e:
        logger.warning(f"Failed to publish to {topic}: {e}")


def flush():
    if _producer and _producer is not False:
        _producer.flush(timeout=10)


def close():
    global _producer
    if _producer and _producer is not False:
        _producer.close()
        _producer = None
