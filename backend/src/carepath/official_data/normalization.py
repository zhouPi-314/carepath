"""Checksum, validation and status rules shared by every official source."""

from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta

from carepath.official_data.contracts import (
    SUPPORTED_SOURCE_CODES,
    DatasetSnapshot,
    ParsedDataset,
)

#: A snapshot older than this many days after its effective date is stale.
VALIDITY_DAYS = 365


def canonical_json(content: dict) -> str:
    return json.dumps(
        content,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_checksum(content: dict) -> str:
    return hashlib.sha256(canonical_json(content).encode("utf-8")).hexdigest()


def is_valid_checksum(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def validate_snapshot(
    snapshot: DatasetSnapshot,
    *,
    today: date | None = None,
) -> list[str]:
    """Return human-readable violations; an empty list means acceptable."""
    errors: list[str] = []
    today = today or date.today()

    if snapshot.source_code not in SUPPORTED_SOURCE_CODES:
        errors.append(f"不支持的来源代码: {snapshot.source_code}")
    if not snapshot.title.strip():
        errors.append("标题不能为空")
    if not snapshot.version.strip():
        errors.append("版本不能为空")
    if not snapshot.source_url.startswith("https://"):
        errors.append("来源链接必须使用 https 且指向公开合法来源")
    if not snapshot.reviewer.strip():
        errors.append("审核人不能为空")
    if not snapshot.parser_version.strip():
        errors.append("解析器版本不能为空")
    if not is_valid_checksum(snapshot.checksum):
        errors.append("校验值必须是 64 位小写十六进制 SHA-256")
    if snapshot.published_at and snapshot.effective_at:
        if snapshot.published_at > snapshot.effective_at:
            errors.append("发布日期不能晚于生效日期")
    if snapshot.effective_at and snapshot.effective_at > today + timedelta(days=366):
        errors.append("生效日期超出合理范围")
    return errors


def derive_status(
    parsed: ParsedDataset,
    *,
    today: date | None = None,
) -> str:
    """UNVERIFIED beats STALE: a data-quality problem is never hidden by age."""
    if parsed.unverified:
        return "UNVERIFIED"
    today = today or date.today()
    if parsed.effective_at is not None:
        expires = parsed.effective_at + timedelta(days=VALIDITY_DAYS)
        if today > expires:
            return "STALE"
    return "VERIFIED"
