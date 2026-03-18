"""
Redis cache layer for hot data access.
Gracefully degrades if Redis is unavailable.
"""
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("quantclaw.redis")

_client = None


def _get_redis():
    global _client
    if _client is not None:
        return _client
    try:
        import redis
        from ..config import REDIS_CONFIG
        _client = redis.Redis(**REDIS_CONFIG)
        _client.ping()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning(f"Redis unavailable: {e}")
        _client = False
    return _client


def cache_latest(module_name: str, symbol: str, payload: Dict[str, Any], ttl: int = 86400):
    """Cache the latest data point for a module/symbol pair. TTL defaults to 24h."""
    r = _get_redis()
    if not r:
        return
    try:
        key = f"qcd:latest:{module_name}:{symbol}"
        r.setex(key, ttl, json.dumps(payload, default=str))
    except Exception as e:
        logger.warning(f"Redis cache write failed: {e}")


def get_latest(module_name: str, symbol: str) -> Optional[Dict]:
    r = _get_redis()
    if not r:
        return None
    try:
        key = f"qcd:latest:{module_name}:{symbol}"
        val = r.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None


def set_module_health(module_name: str, status: str, details: Dict = None):
    r = _get_redis()
    if not r:
        return
    try:
        key = f"qcd:health:{module_name}"
        data = {"status": status, **(details or {})}
        r.setex(key, 3600, json.dumps(data, default=str))
    except Exception as e:
        logger.warning(f"Redis health write failed: {e}")


def publish_update(channel: str, message: Dict):
    """Publish real-time update via Redis pub/sub."""
    r = _get_redis()
    if not r:
        return
    try:
        r.publish(channel, json.dumps(message, default=str))
    except Exception:
        pass
