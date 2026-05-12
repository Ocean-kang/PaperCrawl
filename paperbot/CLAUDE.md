# PaperBot — Claude Code Agent Guide

## Architecture Principles

1. **API-first**: Prefer official APIs over HTML scraping. OpenReview conferences (ICLR, NeurIPS) MUST use `api2.openreview.net`.
2. **Schema-first**: All crawlers return `list[Paper]`. Pydantic `Paper` model is the universal contract.
3. **Adapter pattern**: One crawler class per data source. New conference = new entry in `registry.py`, no existing code changes needed.
4. **Strong typing**: mypy-compatible typing everywhere. No `Any` in public signatures. No raw dicts.
5. **Structured logging**: `logging` + `RichHandler`. Never `print()`.

## Crawler Development Standards

- Inherit from `BaseCrawler` — never write standalone fetch functions.
- Use `self.request_with_retry()` for all HTTP calls — it handles retries, timeouts, User-Agent rotation.
- Use `self.validate_paper(paper)` before appending to results.
- Use `self.save_debug_html()` when parsing fails — saves HTML for offline debugging.
- Use `self._rate_limiter.wait()` before each request to respect rate limits.
- Use `log_parse_failure()` from `utils/html_debug.py` when selectors don't match.

## Adding a New Conference

1. Determine data source (API > proceedings page > HTML > browser).
2. Create `crawlers/<source>.py` extending `BaseCrawler`.
3. Add mapping to `_CRAWLER_MAP` in `crawlers/registry.py`.
4. Write a test in `tests/test_<conference>.py`.
5. Run the test, fix failures, iterate.

## Logging Standards

- Log levels: INFO for progress milestones, WARNING for skips, ERROR for failures.
- Format: `[CONFERENCE YEAR] message | key=value`.
- Use `self._log_progress(stage, detail)` for progress milestones.
- Never log full HTML bodies — use `save_debug_html()` instead.

## Retry Standards

- All HTTP via `self.request_with_retry()` — backed by `tenacity`.
- Retryable: Timeout, ConnectionError, HTTP 429/502/503/504.
- Exponential backoff: 2s → 30s max, 3 attempts.

## Parser Standards

- Use `lxml` cssselect (not BeautifulSoup, not regex).
- If a selector fails: save debug HTML, log failure, skip paper, continue.
- Never retry the same URL with different selectors in a loop — save and move on.
- Handle missing fields gracefully: `None` for optional, empty list for arrays.

## Debugging Workflow

When a parser fails:
1. `self.save_debug_html(html, "descriptive_name.html")` → saves to `debug/<conference>/`.
2. `log_parse_failure(url, reason, selector)` → structured error log.
3. Open the saved HTML in a browser, inspect the actual DOM structure.
4. Update selectors based on real DOM, not assumptions.
5. Re-run the test.

## Token Optimization

- Keep log output concise: one line per progress checkpoint.
- Don't dump HTML, JSON payloads, or stack traces in logs.
- Don't explain what code does — the code speaks for itself.
- Write minimal, focused commit messages.

## Forbidden Practices

- No `print()` — use `logging`.
- No `BeautifulSoup` — use `lxml`.
- No `selenium`/`playwright` — use APIs or raw HTTP.
- No hardcoded selectors without fallback debug saving.
- No giant `main.py` — logic lives in modules.
- No `try/except Exception` without logging the failure.
- No raw dict returns — always `Paper` model.

## Running

```bash
# Install
pip install -r requirements.txt

# Crawl
python main.py --conference CVPR --year 2025 --limit 50
python main.py --conference ICLR --year 2025 --limit 20
python main.py --conference ICML --year 2025 --limit 10

# Tests
python tests/test_cvpr.py
python tests/test_iclr.py
python tests/test_icml.py
python tests/test_csv.py
```
