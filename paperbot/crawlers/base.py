import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from paperbot.models.paper import Paper
from paperbot.config.settings import settings
from paperbot.utils.headers import random_headers

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    conference: str
    base_url: str
    source: str

    def __init__(self, year: int) -> None:
        self.year = year
        self.session = requests.Session()
        self.session.headers.update(random_headers())
        self._debug_dir = settings.DEBUG_DIR / self.conference.lower()
        self._debug_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def fetch_papers(self, limit: int | None = None) -> list[Paper]: ...

    def validate_paper(self, paper: Paper) -> bool:
        if not paper.title or not paper.title.strip():
            logger.warning("Paper validation failed: empty title")
            return False
        if not paper.authors:
            logger.warning(f"Paper validation failed: no authors for '{paper.title[:60]}'")
            return False
        return True

    def request_with_retry(self, url: str, **kwargs: Any) -> requests.Response:
        return self._do_request(url, **kwargs)

    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((requests.RequestException,)),
        reraise=True,
    )
    def _do_request(self, url: str, **kwargs: Any) -> requests.Response:
        kwargs.setdefault("timeout", settings.REQUEST_TIMEOUT)
        logger.debug(f"GET {url}")
        resp = self.session.get(url, **kwargs)
        resp.raise_for_status()
        return resp

    def save_debug_html(self, content: str, filename: str) -> Path:
        path = self._debug_dir / filename
        path.write_text(content, encoding="utf-8")
        logger.debug(f"Saved debug HTML: {path}")
        return path

    def _log_progress(self, stage: str, detail: str = "") -> None:
        logger.info(f"[{self.conference} {self.year}] {stage}" + (f" | {detail}" if detail else ""))
