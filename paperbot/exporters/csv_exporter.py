import logging
from pathlib import Path

import pandas as pd

from paperbot.models.paper import Paper
from paperbot.config.settings import settings

logger = logging.getLogger(__name__)

_COLUMNS = [
    "title",
    "authors",
    "abstract",
    "pdf_url",
    "detail_url",
    "conference",
    "year",
    "source",
    "keywords",
    "decision",
    "withdrawn",
]


def export_csv(papers: list[Paper], filepath: str | Path | None = None) -> Path:
    if filepath is None:
        if not papers:
            raise ValueError("No papers to export and no filepath specified")
        p = papers[0]
        filename = f"{p.conference}{p.year}.csv"
        filepath = settings.OUTPUT_DIR / filename
    else:
        filepath = Path(filepath)

    filepath.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for paper in papers:
        row = {}
        for col in _COLUMNS:
            val = getattr(paper, col, None)
            if isinstance(val, list):
                val = "; ".join(str(v) for v in val)
            row[col] = val
        rows.append(row)

    df = pd.DataFrame(rows, columns=_COLUMNS)
    df.to_csv(filepath, index=False, encoding="utf-8")

    logger.info(f"Exported {len(papers)} papers to {filepath}")
    return filepath
