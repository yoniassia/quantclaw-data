"""
Alert notifier — sends critical pipeline alerts to WhatsApp.
Called by the orchestrator when modules fail 3x consecutively.
"""
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone

sys.path.insert(0, '/home/quant/apps/quantclaw-data')
from qcd_platform.pipeline import db

logger = logging.getLogger("quantclaw.alerts")

MARKETDATACLAW_JID = "120363423165669711@g.us"
WACLI = "/home/linuxbrew/.linuxbrew/bin/wacli"


def send_whatsapp(message: str, to: str = MARKETDATACLAW_JID) -> bool:
    try:
        result = subprocess.run(
            [WACLI, "send", "text", "--to", to, "--message", message],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            logger.info(f"WhatsApp alert sent to {to}")
            return True
        logger.error(f"wacli failed: {result.stderr}")
        return False
    except Exception as e:
        logger.error(f"WhatsApp send error: {e}")
        return False


def check_and_notify():
    """Check for unresolved critical alerts and send notifications."""
    alerts = db.execute_query(
        """SELECT a.id, a.module_id, a.severity, a.category, a.message,
                  a.created_at, m.name AS module_name
           FROM alerts a
           JOIN modules m ON m.id = a.module_id
           WHERE a.resolved = false
             AND a.severity = 'critical'
             AND NOT ('whatsapp' = ANY(a.notified_channels))
           ORDER BY a.created_at DESC
           LIMIT 10""",
        fetch=True,
    )

    if not alerts:
        return 0

    lines = [f"*PIPELINE ALERT* ({len(alerts)} critical)\n"]
    for a in alerts:
        lines.append(f"- *{a['module_name']}*: {a['message'][:100]}")

    lines.append(f"\nTime: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("Dashboard: signalcentre.quantclaw.org/pipeline")

    msg = "\n".join(lines)

    if send_whatsapp(msg):
        alert_ids = [a["id"] for a in alerts]
        for aid in alert_ids:
            db.execute_query(
                "UPDATE alerts SET notified_channels = array_append(notified_channels, 'whatsapp') WHERE id = %s",
                (aid,),
            )
        return len(alerts)

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = check_and_notify()
    if count:
        print(f"Sent {count} alert(s) to WhatsApp")
    else:
        print("No pending critical alerts")
