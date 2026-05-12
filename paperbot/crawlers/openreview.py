import logging
from typing import Any

from paperbot.crawlers.base import BaseCrawler
from paperbot.models.paper import Paper
from paperbot.utils.rate_limit import RateLimiter
from paperbot.utils.html_debug import log_parse_failure

logger = logging.getLogger(__name__)

_INVITATIONS: dict[str, dict[int, str]] = {
    "ICLR": {
        2025: "ICLR.cc/2025/Conference/-/Submission",
        2024: "ICLR.cc/2024/Conference/-/Submission",
        2023: "ICLR.cc/2023/Conference/-/Submission",
    },
    "NeurIPS": {
        2025: "NeurIPS.cc/2025/Conference/-/Submission",
        2024: "NeurIPS.cc/2024/Conference/-/Submission",
    },
}


class OpenReviewCrawler(BaseCrawler):
    conference = "ICLR"
    base_url = "https://api2.openreview.net"
    source = "openreview"

    def __init__(self, year: int, conference: str = "ICLR") -> None:
        self.conference = conference
        self.year = year
        self.source = "openreview"
        super().__init__(year)
        self._rate_limiter = RateLimiter(1.5)

    def _get_invitation(self) -> str:
        conf_invites = _INVITATIONS.get(self.conference, {})
        invite = conf_invites.get(self.year)
        if invite:
            return invite
        return f"{self.conference}.cc/{self.year}/Conference/-/Submission"

    @staticmethod
    def _parse_venue(venue: str) -> tuple[str | None, bool]:
        if not venue:
            return None, False
        withdrawn = "withdrawn" in venue.lower()
        decision = None
        if "Oral" in venue:
            decision = "Oral"
        elif "Spotlight" in venue:
            decision = "Spotlight"
        elif "Poster" in venue:
            decision = "Poster"
        return decision, withdrawn

    def _parse_note(self, note: dict[str, Any]) -> Paper | None:
        try:
            content = note.get("content", {})
            title = (content.get("title", {}) or {}).get("value", "").strip()
            if not title:
                return None

            authors_raw = (content.get("authors", {}) or {}).get("value", [])
            authors = authors_raw if isinstance(authors_raw, list) else [authors_raw]

            abstract = (content.get("abstract", {}) or {}).get("value", "")
            keywords_raw = (content.get("keywords", {}) or {}).get("value", [])
            keywords = keywords_raw if isinstance(keywords_raw, list) else []

            # PDF — content.pdf.value is a relative path like /pdf/abc123...pdf
            pdf_path = (content.get("pdf", {}) or {}).get("value", "")
            pdf_url = f"https://openreview.net{pdf_path}" if pdf_path else None

            note_id = note.get("id", "")
            detail_url = f"https://openreview.net/forum?id={note_id}" if note_id else None

            venue = (content.get("venue", {}) or {}).get("value", "")
            decision, withdrawn = self._parse_venue(venue)

            return Paper(
                title=title,
                authors=authors,
                abstract=abstract,
                pdf_url=pdf_url,
                detail_url=detail_url,
                conference=self.conference,
                year=self.year,
                source=self.source,
                keywords=keywords,
                decision=decision,
                withdrawn=withdrawn,
            )
        except Exception:
            logger.debug("Failed to parse OpenReview note", exc_info=True)
            return None

    def fetch_papers(self, limit: int | None = None) -> list[Paper]:
        invitation = self._get_invitation()
        self._log_progress("Fetching papers", f"invitation={invitation}")

        papers: list[Paper] = []
        offset = 0
        batch_size = 200

        while True:
            if limit and len(papers) >= limit:
                break

            fetch_count = min(batch_size, limit - len(papers)) if limit else batch_size

            params: dict[str, Any] = {
                "invitation": invitation,
                "limit": fetch_count,
                "offset": offset,
            }

            self._rate_limiter.wait()
            resp = self.request_with_retry(f"{self.base_url}/notes", params=params)
            data = resp.json()

            notes = data.get("notes", [])

            if not notes:
                break

            for note in notes:
                paper = self._parse_note(note)
                if paper and self.validate_paper(paper):
                    papers.append(paper)
                    if limit and len(papers) >= limit:
                        break

            offset += len(notes)
            if len(notes) < fetch_count:
                break

        self._log_progress("Fetched papers", f"count={len(papers)}")
        return papers
