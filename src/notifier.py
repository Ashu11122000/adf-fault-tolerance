
import json
from pathlib import Path
from datetime import datetime, timezone


BASE_DIR = Path(__file__).resolve().parent.parent

ALERT_FILE = BASE_DIR / "logs" / "alerts.log"


def send_alert(level, message, details=None):
    """
    Simulate a pipeline alert notification.

    Alerts are printed to the console and
    stored in a persistent JSON Lines log.
    """

    ALERT_FILE.parent.mkdir(parents=True, exist_ok=True)

    alert = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "message": message,
        "details": details or {}
    }

    # Display notification in terminal
    print(f"\n[{level} ALERT] {message}")

    # Save notification history
    with ALERT_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(alert) + "\n")

    return alert


def notify_success(details=None):
    return send_alert(
        "INFO",
        "Pipeline executed successfully.",
        details
    )


def notify_partial_failure(details=None):
    return send_alert(
        "WARNING",
        "Pipeline completed with skipped records.",
        details
    )


def notify_failure(details=None):
    return send_alert(
        "ERROR",
        "Pipeline execution failed.",
        details
    )
