import argparse
import logging
import logging.config
import sys
from pathlib import Path

import yaml

# Ensure project root is on path for direct invocation
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from paperbot.crawlers.registry import get_crawler, list_supported
from paperbot.exporters.csv_exporter import export_csv


def setup_logging() -> None:
    log_config_path = Path(__file__).resolve().parent / "config" / "logging.yaml"
    if log_config_path.exists():
        with open(log_config_path) as f:
            config = yaml.safe_load(f)
        logging.config.dictConfig(config)
    else:
        from rich.logging import RichHandler
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            handlers=[RichHandler(rich_tracebacks=True, show_time=True, show_path=False)],
        )


def main() -> None:
    setup_logging()
    logger = logging.getLogger("paperbot")

    parser = argparse.ArgumentParser(
        description="PaperBot — Academic Paper Crawler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Supported conferences: {', '.join(list_supported())}",
    )
    parser.add_argument("--conference", "-c", required=True, help="Conference acronym (e.g., CVPR, ICLR, ICML)")
    parser.add_argument("--year", "-y", type=int, required=True, help="Conference year (e.g., 2025)")
    parser.add_argument("--limit", "-l", type=int, default=None, help="Max papers to fetch")
    parser.add_argument("--output", "-o", default=None, help="Output CSV path (default: output/<CONFERENCE><YEAR>.csv)")

    args = parser.parse_args()

    try:
        crawler = get_crawler(args.conference, args.year)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    logger.info(f"Starting crawl: {crawler.conference} {crawler.year}")
    papers = crawler.fetch_papers(limit=args.limit)

    if not papers:
        logger.warning("No papers fetched. Check the conference/year combination or network connectivity.")
        sys.exit(0)

    output_path = export_csv(papers, filepath=args.output)
    logger.info(f"Done. {len(papers)} papers exported -> {output_path}")


if __name__ == "__main__":
    main()
