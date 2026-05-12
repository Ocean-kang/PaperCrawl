import logging
from urllib.parse import urljoin

from lxml import html

from paperbot.crawlers.base import BaseCrawler
from paperbot.models.paper import Paper
from paperbot.utils.rate_limit import RateLimiter
from paperbot.utils.html_debug import save_debug_snapshot, log_parse_failure

logger = logging.getLogger(__name__)

CVF_CONFERENCES = {
    "CVPR": "CVPR",
    "ICCV": "ICCV",
}


class CVFCrawler(BaseCrawler):
    conference = "CVPR"
    base_url = "https://openaccess.thecvf.com"
    source = "cvf"

    def __init__(self, year: int, conference: str = "CVPR") -> None:
        self.conference = conference
        self.year = year
        super().__init__(year)
        self._rate_limiter = RateLimiter(2.0)

    def _listing_url(self) -> str:
        return f"{self.base_url}/{self.conference}{self.year}?day=all"

    def _paper_detail_url(self, relative_path: str) -> str:
        return urljoin(f"{self.base_url}/", relative_path)

    def _parse_listing_page(self, html_content: str) -> list[dict[str, str]]:
        tree = html.fromstring(html_content)
        entries: list[dict[str, str]] = []

        # CVF uses <dt> for paper titles/links and <dd> for metadata
        for dt in tree.cssselect("dt"):
            link = dt.cssselect("a")
            if not link:
                continue
            title = link[0].text_content().strip()
            href = link[0].get("href", "")
            if not href:
                continue
            entries.append({"title": title, "url": href})
        return entries

    def _parse_detail_page(self, html_content: str, entry: dict[str, str]) -> Paper | None:
        try:
            tree = html.fromstring(html_content)

            # Authors — div with id="authors", format: "Name1, Name2; Proceedings..."
            author_el = tree.cssselect("#authors")
            authors: list[str] = []
            if author_el:
                author_text = author_el[0].text_content().strip()
                # Split on semicolon to separate author list from proceedings info
                author_part = author_text.split(";")[0].strip()
                authors = [a.strip() for a in author_part.split(",") if a.strip()]
            else:
                for i_el in tree.cssselect("i"):
                    text = i_el.text_content().strip()
                    if text and "," in text:
                        author_part = text.split(";")[0].strip()
                        authors = [a.strip() for a in author_part.split(",") if a.strip()]
                        break

            # Abstract
            abstract = ""
            abstract_el = tree.cssselect("#abstract")
            if abstract_el:
                abstract = abstract_el[0].text_content().strip()

            # PDF URL
            pdf_url = None
            pdf_link = tree.cssselect('a[href$=".pdf"]')
            if pdf_link:
                pdf_url = urljoin(f"{self.base_url}/", pdf_link[0].get("href", ""))

            detail_url = self._paper_detail_url(entry["url"])

            return Paper(
                title=entry["title"],
                authors=authors,
                abstract=abstract,
                pdf_url=pdf_url,
                detail_url=detail_url,
                conference=self.conference,
                year=self.year,
                source=self.source,
            )
        except Exception:
            logger.debug("Failed to parse CVF detail page", exc_info=True)
            return None

    def fetch_papers(self, limit: int | None = None) -> list[Paper]:
        listing_url = self._listing_url()
        self._log_progress("Fetching listing page", f"url={listing_url}")

        resp = self.request_with_retry(listing_url)
        entries = self._parse_listing_page(resp.text)

        if not entries:
            self.save_debug_html(resp.text, "listing_empty.html")
            self._log_progress("No entries found on listing page — saved debug HTML")
            return []

        actual_limit = min(limit, len(entries)) if limit else len(entries)
        entries = entries[:actual_limit]

        self._log_progress(f"Found {len(entries)} entries on listing page, fetching details")

        papers: list[Paper] = []
        for i, entry in enumerate(entries):
            detail_url = self._paper_detail_url(entry["url"])
            try:
                self._rate_limiter.wait()
                d_resp = self.request_with_retry(detail_url)
                paper = self._parse_detail_page(d_resp.text, entry)
                if paper and self.validate_paper(paper):
                    papers.append(paper)
                else:
                    self._log_progress("Skipped paper (validation or parse failure)", f"url={detail_url}")
                    log_parse_failure(detail_url, "parse or validation failed")
            except Exception as e:
                self._log_progress("Skipped paper (request failure)", f"url={detail_url}")
                log_parse_failure(detail_url, str(e))

            if i % 10 == 0 and i > 0:
                self._log_progress(f"Progress: {i}/{len(entries)} details fetched")

        self._log_progress("Fetched papers", f"count={len(papers)}")
        return papers
