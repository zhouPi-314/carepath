"""Stable contracts for official public-data snapshots.

This module is deliberately free of FastAPI, SQLAlchemy and network code: the
domain only describes what a source produces, what a repository must persist,
and which failures callers must handle.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any, Protocol

SUPPORTED_SOURCE_CODES = ("NMPA", "NHSA", "NHC", "NBS")


@dataclass(frozen=True)
class ParsedDataset:
    """A source-specific document normalised into the shared shape."""

    source_code: str
    title: str
    version: str
    source_url: str
    published_at: date | None
    effective_at: date | None
    parser_version: str
    content: dict[str, Any]
    unverified: bool = False


@dataclass(frozen=True)
class DatasetSnapshot:
    """A parsed dataset plus the custody metadata required by the spec."""

    source_code: str
    title: str
    version: str
    source_url: str
    published_at: date | None
    effective_at: date | None
    checksum: str
    parser_version: str
    reviewer: str
    content: dict[str, Any]
    status: str = "VERIFIED"
    id: str | None = None


class OfficialCatalogSource(Protocol):
    """Parses one official source's manual snapshot export."""

    source_code: str
    parser_version: str

    def parse(self, raw: Mapping[str, Any]) -> ParsedDataset: ...


class OfficialDatasetRepository(Protocol):
    """Persistence port; the SQLAlchemy adapter is one implementation."""

    async def exists_by_checksum(self, checksum: str) -> bool: ...

    async def add(self, snapshot: DatasetSnapshot) -> str: ...


class OfficialDataError(Exception):
    """Base class for official-data import failures."""


class SnapshotValidationError(OfficialDataError):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors) or "invalid snapshot")


class DuplicateSnapshotError(OfficialDataError):
    def __init__(self, checksum: str) -> None:
        self.checksum = checksum
        super().__init__("相同校验值的数据快照已导入")


class UnsupportedSourceError(OfficialDataError):
    def __init__(self, source_code: str) -> None:
        self.source_code = source_code
        super().__init__(f"不支持的官方数据来源: {source_code}")
