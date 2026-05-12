import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from paperbot.crawlers.openreview import OpenReviewCrawler


def test_iclr_fetch():
    crawler = OpenReviewCrawler(year=2025, conference="ICLR")
    papers = crawler.fetch_papers(limit=3)

    assert len(papers) > 0, f"Expected at least 1 paper, got {len(papers)}"
    assert len(papers) <= 3, f"Expected at most 3 papers, got {len(papers)}"

    for i, p in enumerate(papers):
        assert p.title, f"Paper {i} has no title"
        assert p.conference == "ICLR", f"Paper {i} conference mismatch: {p.conference}"
        assert p.year == 2025, f"Paper {i} year mismatch: {p.year}"
        print(f"  [{i+1}] {p.title[:80]}")
        print(f"      Authors: {p.authors[:3]}...")
        print(f"      PDF: {p.pdf_url}")
        print(f"      Decision: {p.decision}")
        print(f"      Withdrawn: {p.withdrawn}")
        print()

    print(f"ICLR 2025: {len(papers)} papers fetched successfully")


if __name__ == "__main__":
    test_iclr_fetch()
