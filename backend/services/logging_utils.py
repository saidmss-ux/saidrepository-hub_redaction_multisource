import json
import logging
from datetime import UTC, datetime


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def log_event(event: str, **kwargs) -> None:
    payload = {"timestamp": datetime.now(UTC).isoformat(), "event": event, **kwargs}
    logging.getLogger("docuhub").info(json.dumps(payload, default=str))
