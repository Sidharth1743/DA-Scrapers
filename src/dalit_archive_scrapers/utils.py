from __future__ import annotations

import hashlib
import mimetypes
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse, urlunparse


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def slugify(value: str, default: str = "item") -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return normalized or default


def shorten_text(value: str, limit: int = 320) -> str:
    value = clean_text(value)
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "..."


def any_pattern_matches(patterns: tuple[str, ...], value: str) -> bool:
    return any(re.search(pattern, value, flags=re.IGNORECASE) for pattern in patterns)


def extract_query_terms(url: str, keys: tuple[str, ...]) -> list[str]:
    query = parse_qs(urlparse(url).query)
    terms: list[str] = []
    for key in keys:
        for raw in query.get(key, []):
            terms.extend(part.lower() for part in re.findall(r"[A-Za-z0-9]{3,}", raw))
    deduped: list[str] = []
    for term in terms:
        if term not in deduped:
            deduped.append(term)
    return deduped


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            parsed.params,
            parsed.query,
            "",
        )
    )


def guess_extension(url: str, content_type: str | None) -> str:
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix:
        return suffix
    if not content_type:
        return ""
    extension = mimetypes.guess_extension(content_type.split(";", 1)[0].strip())
    return extension or ""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def utc_now() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat()
