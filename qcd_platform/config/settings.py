"""
QuantClaw Data Platform — Configuration
"""
import os

DB_CONFIG = {
    "host": os.getenv("QCD_DB_HOST", "localhost"),
    "port": int(os.getenv("QCD_DB_PORT", "5432")),
    "database": os.getenv("QCD_DB_NAME", "quantclaw_data"),
    "user": os.getenv("QCD_DB_USER", "quantclaw_user"),
    "password": os.getenv("QCD_DB_PASS", "quantclaw_2026_prod"),
}

KAFKA_CONFIG = {
    "bootstrap_servers": os.getenv("QCD_KAFKA_SERVERS", "localhost:9092"),
    "client_id": "quantclaw-pipeline",
}

REDIS_CONFIG = {
    "host": os.getenv("QCD_REDIS_HOST", "localhost"),
    "port": int(os.getenv("QCD_REDIS_PORT", "6379")),
    "db": int(os.getenv("QCD_REDIS_DB", "2")),
    "decode_responses": True,
}

PIPELINE_CONFIG = {
    "max_retries": 3,
    "retry_delay_seconds": 60,
    "quality_threshold_gold": 80,
    "quality_threshold_silver": 50,
    "batch_size": 1000,
    "alert_whatsapp_group": "MarketDataClaw",
}

TIER_THRESHOLDS = {
    "bronze": 0,
    "silver": 50,
    "gold": 80,
    "platinum": 95,
}
