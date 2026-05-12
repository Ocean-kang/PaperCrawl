import logging
from typing import Any
from urllib.parse import urljoin, urlparse

from lxml import html

from paperbot.crawlers.base import BaseCrawler
from paperbot.models.paper import Paper
from paperbot.utils.rate_limit import RateLimiter
from paperbot.utils.html_debug import log_parse_failure

logger = logging.getLogger(__name__)

# PMLR volume numbers for ICML proceedings
# Map year -> volume number
ICML_VOLUMES: dict[int, int] = {
    2025: 235,
    2024: 235,
    2023: 202,
    2022: 162,
    2021: 139,
    2020: 119,
    2019: 97,
}


class PMLRCrawler(BaseCrawler):
    conference = "ICML"
    base_url = "https://proceedings.mlr.press"
    source = "pmlr"

    def __init__(self, year: int, conference: str = "ICML") -> None:
        self.conference = conference
        self.year = year
        super().__init__(year)
        self._rate_limiter = RateLimiter(2.0)

    def _volume_url(self) -> str:
        volume = ICML_VOLUMES.get(self.year, 235)
        return f"{self.base_url}/v{volume}/"

    def _parse_paper_entry(self, entry_div: Any, volume_url: str) -> Paper | None:
        try:
            # Title — in <p class="title">
            title_el = entry_div.cssselect("p.title")
            if not title_el:
                return None
            title = title_el[0].text_content().strip()

            # Authors — in <p class="authors"> or <span class="authors">
            authors: list[str] = []
            authors_el = entry_div.cssselect(".authors")
            if authors_el:
                authors_text = authors_el[0].text_content().strip()
                authors = [a.strip() for a in authors_text.split(",") if a.strip()]

            # Links — look for <a> tags
            links = entry_div.cssselect("a")
            pdf_url = None
            detail_url = None
            for link in links:
                href = link.get("href", "")
                text = link.text_content().strip().lower()
                full_url = urljoin(volume_url, href)
                if href.endswith(".pdf"):
                    pdf_url = full_url
                elif text in ("abs", "abstract", "details") or "/v" in href:
                    detail_url = full_url

            # Abstract — sometimes inline in an "abstract" div
            abstract = ""
            abstract_el = entry_div.cssselect(".abstract")
            if abstract_el:
                abstract = abstract_el[0].text_content().strip()

            return Paper(
                title=title,
                authors=authors,
                abstract=abstract,
                pdf_url=pdf_url,
                detail_url=detail_url or volume_url,
                conference=self.conference,
                year=self.year,
                source=self.source,
            )
        except Exception:
            logger.debug("Failed to parse PMLR paper entry", exc_info=True)
            return None

    def fetch_papers(self, limit: int | None = None) -> list[Paper]:
        volume_url = self._volume_url()
        self._log_progress("Fetching proceedings", f"url={volume_url}")

        resp = self.request_with_retry(volume_url)
        tree = html.fromstring(resp.text)

        # PMLR lists papers in <div class="paper"> containers
        paper_divs = tree.cssselect("div.paper")

        if not paper_divs:
            # Try alternative: the listing may use a different structure
            # Some volumes use <div class="entry-content"> with paragraphs
            paper_divs = tree.cssselect("div.post-content div")
            if not paper_divs:
                self.save_debug_html(resp.text, "pmlr_listing.html")
                self._log_progress("No paper divs found — saved debug HTML")
                return []

        actual_limit = min(limit, len(paper_divs)) if limit else len(paper_divs)
        self._log_progress(f"Found {len(paper_divs)} paper entries, parsing up to {actual_limit}")

        papers: list[Paper] = []
        for i, div in enumerate(paper_divs[:actual_limit]):
            paper = self._parse_paper_entry(div, volume_url)
            if paper and self.validate_paper(paper):
                papers.append(paper)
            elif paper:
                self._log_progress("Skipped paper (validation failed)", f"title={paper.title[:50]}")
                log_parse_failure(volume_url, "validation failed", "div.paper")

        self._log_progress("Fetched papers", f"count={len(papers)}")
        return papers
