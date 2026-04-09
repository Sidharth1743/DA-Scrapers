from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


FetchMode = Literal["static", "dynamic"]
SourceMode = Literal["listing_follow", "single_page"]


@dataclass(frozen=True)
class AssetRule:
    include_url_patterns: tuple[str, ...] = ()
    include_text_patterns: tuple[str, ...] = ()
    exclude_url_patterns: tuple[str, ...] = ()
    allow_images: bool = True
    allow_documents: bool = True
    include_og_image: bool = True
    max_documents: int | None = None
    max_images: int | None = None


@dataclass(frozen=True)
class CandidateRule:
    include_url_patterns: tuple[str, ...] = ()
    include_text_patterns: tuple[str, ...] = ()
    exclude_url_patterns: tuple[str, ...] = ()
    exclude_text_patterns: tuple[str, ...] = ()
    min_text_length: int = 12
    max_candidates: int | None = None


@dataclass(frozen=True)
class SourceDefinition:
    source_id: str
    url: str
    mode: SourceMode
    seed_fetch_mode: FetchMode = "static"
    detail_fetch_mode: FetchMode = "static"
    content_selectors: tuple[str, ...] = ()
    candidate_rule: CandidateRule | None = None
    asset_rule: AssetRule = field(default_factory=AssetRule)
    min_records: int = 1
    query_hint_keys: tuple[str, ...] = ("q", "query", "s", "epw_input")


@dataclass
class DownloadedAsset:
    source_url: str
    saved_path: str
    content_type: str | None
    sha256: str
    size_bytes: int


@dataclass
class Record:
    record_id: str
    source_id: str
    source_url: str
    listing_url: str
    page_type: str
    title: str
    summary: str
    body_text: str
    author: str | None
    published_at: str | None
    tags: list[str]
    record_url: str
    document_links: list[str]
    image_links: list[str]
    downloaded_assets: list[DownloadedAsset]
    scraped_at: str
    verification_notes: list[str]


@dataclass
class ScrapeResult:
    source_id: str
    source_url: str
    records: list[Record]
    errors: list[str]
    verification_notes: list[str]
    fetch_log: list[str]
