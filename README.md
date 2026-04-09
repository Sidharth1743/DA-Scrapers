# Dalit Archive Scrapers

This repository contains `scrapling`-based scrapers for the source URLs listed in `list.txt`. Each configured source is processed sequentially, saved under `output/<source_id>/`, and validated with a small verification pass.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

## Project Layout

- `src/dalit_archive_scrapers/runner.py`: CLI commands
- `src/dalit_archive_scrapers/definitions.py`: per-source rules and source registry
- `src/dalit_archive_scrapers/extractor.py`: fetch, parse, download, and write logic
- `tests/`: unit tests
- `list.txt`: seed URLs processed by `run-all`
- `output/`: generated JSON reports and downloaded assets

## Commands

Run tests:

```bash
.venv/bin/pytest -q
```

Run every configured source:

```bash
.venv/bin/dalit-scrapers run-all
```

Run one source by URL or source ID:

```bash
.venv/bin/dalit-scrapers run-one --url 'https://www.cvmc.in/'
.venv/bin/dalit-scrapers run-one --source cvmc_home
```

Verify one saved source:

```bash
.venv/bin/dalit-scrapers verify-one --source epw_search_dalit
```

## Output Format

Each source writes:

- `output/<source_id>/records.json`: normalized records
- `output/<source_id>/run_report.json`: scrape summary, fetch log, and verification notes
- `output/<source_id>/assets/`: downloaded PDFs, images, or spreadsheets

## Adding or Updating Sources

1. Add the URL to `list.txt`.
2. Register a `SourceDefinition` in `definitions.py`.
3. Prefer shared extraction logic over source-specific hacks.
4. Run `pytest`, then `run-one` and `verify-one` for the new source.

See `AGENTS.md` for repository-wide contributor guidance.
