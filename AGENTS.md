# Repository Guidelines

## Project Structure & Module Organization

Core code lives in `src/dalit_archive_scrapers/`.
- `runner.py`: CLI entrypoints (`run-all`, `run-one`, `verify-one`)
- `definitions.py`: source registry and per-site scraping rules
- `extractor.py`: fetching, extraction, asset downloads, and output writing
- `models.py` / `utils.py`: shared data models and helpers

Tests live in `tests/`. Seed URLs are stored in `list.txt`. Generated scrape output is written to `output/<source_id>/` as `records.json`, `run_report.json`, and downloaded assets.

## Build, Test, and Development Commands

- `python3 -m venv .venv`: create the local virtual environment
- `.venv/bin/pip install -e '.[dev]'`: install the package and test dependencies
- `.venv/bin/pytest -q`: run the test suite
- `.venv/bin/dalit-scrapers run-all`: process every URL in `list.txt`
- `.venv/bin/dalit-scrapers run-one --url 'https://example.com'`: scrape one configured source
- `.venv/bin/dalit-scrapers verify-one --source epw_search_dalit`: rerun validation for one source

## Coding Style & Naming Conventions

Use Python 3.12 with 4-space indentation and type hints for public functions. Keep modules focused and small. Prefer snake_case for functions, variables, file names, and source IDs like `cvmc_home`. Put source-specific behavior in `definitions.py`; keep shared logic in `extractor.py` and `utils.py`. Avoid adding site-specific one-offs unless they are clearly isolated and reusable.

## Testing Guidelines

This repo uses `pytest`. Add tests under `tests/` with names like `test_<behavior>.py` and functions like `test_<case>()`. For scraper changes, add or update unit tests for helpers first, then verify live behavior with `run-one` or `verify-one`. Do not treat generated `output/` data as a test fixture unless the change explicitly depends on saved output shape.

## Commit & Pull Request Guidelines

Current history is minimal (`initial`), so keep commit messages short, imperative, and specific, for example `add cvmc source definitions` or `tighten asset filtering`. In pull requests, include:
- what sources or shared logic changed
- commands you ran (`pytest`, `run-one`, `verify-one`)
- any known site limitations, timeouts, or broken upstream links

## Security & Configuration Tips

Network fetches are part of normal development. Be careful with large PDFs and dynamic sites; prefer updating source rules before broad reruns. Do not hardcode secrets, cookies, or local-only paths into source definitions.
