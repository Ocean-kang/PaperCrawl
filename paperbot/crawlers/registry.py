import logging
from typing import Type

from paperbot.crawlers.base import BaseCrawler
from paperbot.crawlers.cvf import CVFCrawler
from paperbot.crawlers.openreview import OpenReviewCrawler
from paperbot.crawlers.pmlr import PMLRCrawler

logger = logging.getLogger(__name__)

_CRAWLER_MAP: dict[str, Type[BaseCrawler]] = {
    "CVPR": CVFCrawler,
    "ICCV": CVFCrawler,
    "ICLR": OpenReviewCrawler,
    "ICML": PMLRCrawler,
    "NeurIPS": OpenReviewCrawler,
}


def get_crawler(conference: str, year: int) -> BaseCrawler:
    conference_upper = conference.upper()
    crawler_cls = _CRAWLER_MAP.get(conference_upper)
    if crawler_cls is None:
        supported = ", ".join(sorted(_CRAWLER_MAP.keys()))
        raise ValueError(f"Unsupported conference '{conference}'. Supported: {supported}")

    return crawler_cls(year=year, conference=conference_upper)


def list_supported() -> list[str]:
    return sorted(_CRAWLER_MAP.keys())
