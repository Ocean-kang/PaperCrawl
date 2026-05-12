import logging
from pathlib import Path
from datetime import datetime

from paperbot.config.settings import settings

logger = logging.getLogger(__name__)


def save_debug_snapshot(html: str, conference: str, context: str = "") -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{conference}_{context}_{ts}.html" if context else f"{conference}_{ts}.html"
    path = settings.DEBUG_DIR / conference.lower() / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    logger.debug(f"Debug snapshot saved: {path}")
    return path


def log_parse_failure(url: str, reason: str, selector: str = "") -> None:
    logger.error(f"Parse failure | url={url} | selector={selector} | reason={reason}")
