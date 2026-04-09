from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from scrapling.fetchers import DynamicFetcher, Fetcher

from dalit_archive_scrapers.models import (
    DownloadedAsset,
    Record,
    ScrapeResult,
    SourceDefinition,
)
from dalit_archive_scrapers.utils import (
    any_pattern_matches,
    canonicalize_url,
    clean_text,
    extract_query_terms,
    guess_extension,
    sha256_bytes,
    shorten_text,
    slugify,
    utc_now,
)

EXCLUDED_IMAGE_PATTERNS = (
    r"logo",
    r"icon",
    r"avatar",
    r"sprite",
    r"banner",
    r"favicon",
    r"social",
    r"facebook",
    r"instagram",
    r"linkedin",
    r"twitter",
    r"whatsapp",
    r"newsletter",
    r"font_increase",
    r"share",
    r"layer1",
    r"untitled-design",
    r"googleusercontent",
    r"\.svg(?:$|\?)",
)
DOCUMENT_EXTENSIONS = (
    ".pdf",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".xls",
    ".xlsx",
)


def fetch_page(url: str, mode: str, *, timeout: int | float | None = None):
    if mode == "dynamic":
        return DynamicFetcher.fetch(url, headless=True, network_idle=True, timeout=int((timeout or 30) * 1000))
    return Fetcher.get(url, impersonate="chrome", stealthy_headers=True, timeout=timeout or 40)


def first_text(page, selectors: tuple[str, ...]) -> str:
    for selector in selectors:
        value = clean_text(page.css(selector).get())
        if value:
            return value
    return ""


def gather_texts(page, selectors: tuple[str, ...]) -> list[str]:
    texts: list[str] = []
    for selector in selectors:
        for value in page.css(selector).getall():
            cleaned = clean_text(value)
            if cleaned and cleaned not in texts:
                texts.append(cleaned)
    return texts


def find_main_node(page, selectors: tuple[str, ...]):
    best = None
    best_len = -1
    for selector in selectors or ("body",):
        nodes = page.css(selector)
        for node in nodes[:3]:
            text = clean_text(node.get_all_text(strip=True))
            if len(text) > best_len:
                best = node
                best_len = len(text)
    if best is not None:
        return best
    body_nodes = page.css("body")
    return body_nodes[0] if body_nodes else page


def collect_document_links(node, page_url: str) -> list[str]:
    links: list[str] = []
    urljoin = getattr(node, "urljoin", None)
    for anchor in node.css("a"):
        href = anchor.attrib.get("href")
        if not href:
            continue
        absolute = urljoin(href) if urljoin else href
        if absolute not in links:
            links.append(absolute)
    return links


def extract_meta(page, main_node):
    title = (
        first_text(page, ("meta[property='og:title']::attr(content)",))
        or first_text(page, ("h1::text",))
        or first_text(page, ("title::text",))
    )
    summary = (
        first_text(
            page,
            (
                "meta[name='description']::attr(content)",
                "meta[property='og:description']::attr(content)",
            ),
        )
        or shorten_text(clean_text(main_node.get_all_text(strip=True)), 400)
    )
    if summary.startswith("http://") or summary.startswith("https://"):
        summary = shorten_text(clean_text(main_node.get_all_text(strip=True)), 400)
    author = first_text(
        page,
        (
            "meta[name='author']::attr(content)",
            "meta[property='article:author']::attr(content)",
            "[rel='author']::text",
            ".author::text",
            ".byline::text",
        ),
    )
    published_at = first_text(
        page,
        (
            "meta[property='article:published_time']::attr(content)",
            "meta[name='publish-date']::attr(content)",
            "time::attr(datetime)",
            "time::text",
            ".date::text",
        ),
    )
    tags = gather_texts(
        page,
        (
            "meta[property='article:tag']::attr(content)",
            ".tags a::text",
            "[rel='tag']::text",
            ".category a::text",
        ),
    )
    return title, summary, author or None, published_at or None, tags


def is_asset_url(url: str) -> bool:
    lowered = url.lower()
    return lowered.endswith(DOCUMENT_EXTENSIONS) or "/pdf/" in lowered


def should_keep_asset(url: str, text: str, definition: SourceDefinition, *, kind: str) -> bool:
    blob = f"{text} {url}".strip()
    rule = definition.asset_rule
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if kind == "document" and parsed.fragment and not parsed.path.lower().endswith(DOCUMENT_EXTENSIONS):
        return False
    if any_pattern_matches(rule.exclude_url_patterns + EXCLUDED_IMAGE_PATTERNS, url):
        return False
    if kind == "document" and not rule.allow_documents:
        return False
    if kind == "image" and not rule.allow_images:
        return False
    if any_pattern_matches(rule.include_url_patterns, url):
        return True
    if kind == "document" and any_pattern_matches(rule.include_text_patterns, blob) and is_asset_url(url):
        return True
    if kind == "document":
        return is_asset_url(url)
    if kind == "image":
        return True
    return False


def collect_assets(page, main_node, definition: SourceDefinition) -> tuple[list[str], list[str]]:
    document_links: list[str] = []
    image_links: list[str] = []
    max_documents = definition.asset_rule.max_documents
    max_images = definition.asset_rule.max_images or 4
    for anchor in main_node.css("a"):
        href = anchor.attrib.get("href")
        if not href:
            continue
        absolute = page.urljoin(href)
        text = clean_text(" ".join(anchor.css("::text").getall()))
        if should_keep_asset(absolute, text, definition, kind="document"):
            if absolute not in document_links:
                document_links.append(absolute)
                if max_documents is not None and len(document_links) >= max_documents:
                    break
    if definition.asset_rule.include_og_image:
        for selector in (
            "meta[property='og:image']::attr(content)",
            "meta[name='twitter:image']::attr(content)",
        ):
            image_url = clean_text(page.css(selector).get())
            if image_url:
                absolute = page.urljoin(image_url)
                if should_keep_asset(absolute, "", definition, kind="image") and absolute not in image_links:
                    image_links.append(absolute)
    for selector in ("img::attr(src)", "source::attr(srcset)"):
        for candidate in main_node.css(selector).getall():
            absolute = page.urljoin(candidate.split(" ", 1)[0])
            if should_keep_asset(absolute, "", definition, kind="image") and absolute not in image_links:
                image_links.append(absolute)
            if len(image_links) >= max_images:
                break
        if len(image_links) >= max_images:
            break
    return document_links, image_links


def choose_candidate_links(page, definition: SourceDefinition) -> list[str]:
    rule = definition.candidate_rule
    if rule is None:
        return []
    query_terms = extract_query_terms(definition.url, definition.query_hint_keys)
    candidates: list[str] = []
    seen: set[str] = set()
    origin = urlparse(page.url).netloc
    for anchor in page.css("a"):
        href = anchor.attrib.get("href")
        if not href:
            continue
        absolute = page.urljoin(href)
        parsed = urlparse(absolute)
        text = clean_text(" ".join(anchor.css("::text").getall()))
        blob = f"{text} {absolute}"
        if parsed.scheme not in {"http", "https"}:
            continue
        if parsed.netloc != origin:
            continue
        if canonicalize_url(absolute) == canonicalize_url(definition.url):
            continue
        if "#" in absolute and absolute.split("#", 1)[0] == definition.url.rstrip("/"):
            continue
        if is_asset_url(absolute):
            continue
        if len(text) < rule.min_text_length and not any_pattern_matches(rule.include_url_patterns, absolute):
            continue
        if any_pattern_matches(rule.exclude_url_patterns, absolute):
            continue
        if any_pattern_matches(rule.exclude_text_patterns, text):
            continue
        score = 0
        if any_pattern_matches(rule.include_url_patterns, absolute):
            score += 5
        if any_pattern_matches(rule.include_text_patterns, blob):
            score += 3
        if query_terms and any(term in blob.lower() for term in query_terms):
            score += 2
        if score <= 0:
            continue
        canonical = canonicalize_url(absolute)
        if canonical not in seen:
            candidates.append(absolute)
            seen.add(canonical)
        if rule.max_candidates and len(candidates) >= rule.max_candidates:
            break
    return candidates


def download_asset(url: str, destination_dir: Path, fetch_mode: str) -> DownloadedAsset:
    response = fetch_page(url, fetch_mode, timeout=180)
    if getattr(response, "status", 200) >= 400:
        raise RuntimeError(f"Asset request failed with status {response.status}: {url}")
    payload = bytes(response.body)
    content_type = response.headers.get("content-type") if hasattr(response, "headers") else None
    extension = guess_extension(url, content_type)
    filename = slugify(Path(urlparse(url).path).stem or "asset")
    target = destination_dir / f"{filename}{extension}"
    target.write_bytes(payload)
    return DownloadedAsset(
        source_url=url,
        saved_path=str(target),
        content_type=content_type,
        sha256=sha256_bytes(payload),
        size_bytes=len(payload),
    )


def build_record(
    definition: SourceDefinition,
    *,
    page,
    listing_url: str,
    page_type: str,
    assets_dir: Path,
) -> Record:
    main_node = find_main_node(page, definition.content_selectors)
    title, summary, author, published_at, tags = extract_meta(page, main_node)
    body_text = clean_text(main_node.get_all_text(strip=True))
    document_links, image_links = collect_assets(page, main_node, definition)
    downloaded_assets: list[DownloadedAsset] = []
    verification_notes: list[str] = []
    record_slug = slugify(title or page.url)
    record_asset_dir = assets_dir / record_slug
    record_asset_dir.mkdir(parents=True, exist_ok=True)
    for url in document_links + image_links:
        try:
            downloaded_assets.append(download_asset(url, record_asset_dir, definition.detail_fetch_mode))
        except Exception as exc:  # pragma: no cover - network failures are saved as notes
            verification_notes.append(f"Asset download failed: {url} ({exc})")
    if not title:
        verification_notes.append("Missing title")
    if len(body_text) < 80 and not document_links:
        verification_notes.append("Short body text")
    return Record(
        record_id=record_slug,
        source_id=definition.source_id,
        source_url=definition.url,
        listing_url=listing_url,
        page_type=page_type,
        title=title,
        summary=summary,
        body_text=body_text,
        author=author,
        published_at=published_at,
        tags=tags,
        record_url=str(page.url),
        document_links=document_links,
        image_links=image_links,
        downloaded_assets=downloaded_assets,
        scraped_at=utc_now(),
        verification_notes=verification_notes,
    )


def scrape_source(definition: SourceDefinition, output_root: Path) -> ScrapeResult:
    records: list[Record] = []
    errors: list[str] = []
    fetch_log: list[str] = []
    source_dir = output_root / definition.source_id
    assets_dir = source_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    try:
        seed_page = fetch_page(definition.url, definition.seed_fetch_mode)
        fetch_log.append(f"{definition.seed_fetch_mode}:{definition.url}")
    except Exception as exc:
        return ScrapeResult(
            source_id=definition.source_id,
            source_url=definition.url,
            records=[],
            errors=[str(exc)],
            verification_notes=["Seed fetch failed"],
            fetch_log=fetch_log,
        )

    if definition.mode == "single_page":
        records.append(
            build_record(
                definition,
                page=seed_page,
                listing_url=definition.url,
                page_type="document",
                assets_dir=assets_dir,
            )
        )
    else:
        candidates = choose_candidate_links(seed_page, definition)
        if not candidates:
            records.append(
                build_record(
                    definition,
                    page=seed_page,
                    listing_url=definition.url,
                    page_type="listing",
                    assets_dir=assets_dir,
                )
            )
        else:
            for candidate in candidates:
                try:
                    page = fetch_page(candidate, definition.detail_fetch_mode)
                    fetch_log.append(f"{definition.detail_fetch_mode}:{candidate}")
                    records.append(
                        build_record(
                            definition,
                            page=page,
                            listing_url=definition.url,
                            page_type="article",
                            assets_dir=assets_dir,
                        )
                    )
                except Exception as exc:
                    errors.append(f"{candidate}: {exc}")

    verification_notes = verify_result(definition, records, errors)
    return ScrapeResult(
        source_id=definition.source_id,
        source_url=definition.url,
        records=records,
        errors=errors,
        verification_notes=verification_notes,
        fetch_log=fetch_log,
    )


def verify_result(definition: SourceDefinition, records: list[Record], errors: list[str]) -> list[str]:
    notes: list[str] = []
    if len(records) < definition.min_records:
        notes.append(f"Expected at least {definition.min_records} record(s), got {len(records)}")
    query_terms = extract_query_terms(definition.url, definition.query_hint_keys)
    matched_query = False
    for record in records:
        if not record.title:
            notes.append(f"{record.record_url}: missing title")
        if not record.body_text and not record.document_links:
            notes.append(f"{record.record_url}: missing body text and documents")
        if query_terms:
            blob = f"{record.title} {record.summary} {record.body_text[:500]}".lower()
            if any(term in blob for term in query_terms):
                matched_query = True
        for asset in record.downloaded_assets:
            if asset.saved_path and not Path(asset.saved_path).exists():
                notes.append(f"Missing downloaded file for {asset.source_url}")
    if query_terms and definition.mode == "listing_follow" and records and not matched_query:
        notes.append(f"No scraped record appears relevant to query terms: {', '.join(query_terms)}")
    if errors:
        notes.append(f"{len(errors)} request(s) failed")
    return notes


def serialize_result(result: ScrapeResult) -> dict:
    def asset_to_dict(asset: DownloadedAsset) -> dict:
        return {
            "source_url": asset.source_url,
            "saved_path": asset.saved_path,
            "content_type": asset.content_type,
            "sha256": asset.sha256,
            "size_bytes": asset.size_bytes,
        }

    def record_to_dict(record: Record) -> dict:
        return {
            "record_id": record.record_id,
            "source_id": record.source_id,
            "source_url": record.source_url,
            "listing_url": record.listing_url,
            "page_type": record.page_type,
            "title": record.title,
            "summary": record.summary,
            "body_text": record.body_text,
            "author": record.author,
            "published_at": record.published_at,
            "tags": record.tags,
            "record_url": record.record_url,
            "document_links": record.document_links,
            "image_links": record.image_links,
            "downloaded_assets": [asset_to_dict(asset) for asset in record.downloaded_assets],
            "scraped_at": record.scraped_at,
            "verification_notes": record.verification_notes,
        }

    return {
        "source_id": result.source_id,
        "source_url": result.source_url,
        "records": [record_to_dict(record) for record in result.records],
        "errors": result.errors,
        "verification_notes": result.verification_notes,
        "fetch_log": result.fetch_log,
    }


def write_result(output_root: Path, result: ScrapeResult) -> None:
    source_dir = output_root / result.source_id
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "records.json").write_text(
        json.dumps(serialize_result(result)["records"], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (source_dir / "run_report.json").write_text(
        json.dumps(
            {
                "source_id": result.source_id,
                "source_url": result.source_url,
                "record_count": len(result.records),
                "errors": result.errors,
                "verification_notes": result.verification_notes,
                "fetch_log": result.fetch_log,
                "written_at": utc_now(),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
