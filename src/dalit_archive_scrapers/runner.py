from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dalit_archive_scrapers.definitions import DEFINITIONS_BY_ID, DEFINITIONS_BY_URL, SOURCE_DEFINITIONS
from dalit_archive_scrapers.extractor import scrape_source, verify_result, write_result


ROOT_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT_DIR / "output"
LIST_FILE = ROOT_DIR / "list.txt"


def resolve_definition(url: str | None, source_id: str | None):
    if url:
        definition = DEFINITIONS_BY_URL.get(url)
        if definition is None:
            raise SystemExit(f"URL not configured: {url}")
        return definition
    if source_id:
        definition = DEFINITIONS_BY_ID.get(source_id)
        if definition is None:
            raise SystemExit(f"Source ID not configured: {source_id}")
        return definition
    raise SystemExit("Either --url or --source is required")


def run_one(url: str | None, source_id: str | None) -> int:
    definition = resolve_definition(url, source_id)
    result = scrape_source(definition, OUTPUT_DIR)
    write_result(OUTPUT_DIR, result)
    print(f"{definition.source_id}: records={len(result.records)} errors={len(result.errors)}")
    if result.verification_notes:
        for note in result.verification_notes:
            print(f"  verify: {note}")
    return 0 if not result.verification_notes else 1


def run_all() -> int:
    urls = [line.strip() for line in LIST_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    exit_code = 0
    for url in urls:
        print(f"Processing {url}")
        definition = DEFINITIONS_BY_URL.get(url)
        if definition is None:
            print(f"  skipped: no configured definition for {url}")
            exit_code = 1
            continue
        result = scrape_source(definition, OUTPUT_DIR)
        write_result(OUTPUT_DIR, result)
        print(f"  saved: {definition.source_id} records={len(result.records)} errors={len(result.errors)}")
        if result.verification_notes:
            exit_code = 1
            for note in result.verification_notes:
                print(f"  verify: {note}")
    return exit_code


def verify_one(url: str | None, source_id: str | None) -> int:
    definition = resolve_definition(url, source_id)
    result = scrape_source(definition, OUTPUT_DIR)
    notes = verify_result(definition, result.records, result.errors)
    if notes:
        for note in notes:
            print(note)
        return 1
    print(f"{definition.source_id}: verification passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dalit archive scrapers")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_all_parser = subparsers.add_parser("run-all")
    run_all_parser.set_defaults(handler=lambda args: run_all())

    for command in ("run-one", "verify-one"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--url")
        sub.add_argument("--source")
        sub.set_defaults(handler=lambda args, command=command: run_one(args.url, args.source) if command == "run-one" else verify_one(args.url, args.source))

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.handler(args))


if __name__ == "__main__":
    main()
