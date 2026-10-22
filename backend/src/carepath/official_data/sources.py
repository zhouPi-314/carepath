"""Small, explicit parsers for the four first-batch official sources.

Each parser accepts a manually exported JSON snapshot. No parser performs
network access, bypasses access controls, or scrapes a live site.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from typing import Any

from carepath.official_data.contracts import (
    ParsedDataset,
    UnsupportedSourceError,
)


def _text(raw: Mapping[str, Any], key: str, *, default: str = "") -> str:
    value = raw.get(key, default)
    return str(value).strip() if value is not None else default


def _date(raw: Mapping[str, Any], key: str) -> date | None:
    value = raw.get(key)
    if not value:
        return None
    return date.fromisoformat(str(value))


def _records(raw: Mapping[str, Any]) -> list[Any]:
    records = raw.get("records")
    if isinstance(records, list):
        return records
    return []


class _BaseSource:
    source_code: str
    parser_version: str
    required_record_keys: tuple[str, ...] = ()
    disclaimer: str = ""

    def _parse(self, raw: Mapping[str, Any], content: dict[str, Any]) -> ParsedDataset:
        records = _records(raw)
        normalised: list[dict[str, Any]] = []
        unverified = False
        for record in records:
            if not isinstance(record, Mapping):
                unverified = True
                continue
            missing = [
                key
                for key in self.required_record_keys
                if not str(record.get(key, "")).strip()
            ]
            if missing:
                unverified = True
            normalised.append(
                {
                    key: record.get(key)
                    for key in self.required_record_keys
                }
            )
        if not normalised:
            unverified = True
        content["records"] = normalised
        content["recordCount"] = len(normalised)
        if self.disclaimer:
            content["disclaimer"] = self.disclaimer
        return ParsedDataset(
            source_code=self.source_code,
            title=_text(raw, "title"),
            version=_text(raw, "version"),
            source_url=_text(raw, "sourceUrl"),
            published_at=_date(raw, "publishedAt"),
            effective_at=_date(raw, "effectiveAt"),
            parser_version=self.parser_version,
            content=content,
            unverified=unverified,
        )


class NmpaSource(_BaseSource):
    source_code = "NMPA"
    parser_version = "nmpa-json-v1"
    required_record_keys = ("approvalNumber", "name", "manufacturer")
    disclaimer = "药品批准文号来自公开快照，仅用于演示匹配。"

    def parse(self, raw: Mapping[str, Any]) -> ParsedDataset:
        return self._parse(raw, {"dataset": "drug_approvals"})


class NhsaSource(_BaseSource):
    source_code = "NHSA"
    parser_version = "nhsa-json-v1"
    required_record_keys = ("drugName", "insuranceLabel")
    disclaimer = "医保标签仅为信息展示，不代表实际报销。"

    def parse(self, raw: Mapping[str, Any]) -> ParsedDataset:
        return self._parse(raw, {"dataset": "insurance_catalogue"})


class NhcSource(_BaseSource):
    source_code = "NHC"
    parser_version = "nhc-json-v1"
    required_record_keys = ("institutionName", "regionCode")
    disclaimer = "机构信息来自公开快照，认证状态需另行审核。"

    def parse(self, raw: Mapping[str, Any]) -> ParsedDataset:
        return self._parse(raw, {"dataset": "medical_institutions"})


class NbsSource(_BaseSource):
    source_code = "NBS"
    parser_version = "nbs-json-v1"
    required_record_keys = ("regionCode", "populationBaseline")
    disclaimer = "人口基线为公开统计快照，不代表实时数据。"

    def parse(self, raw: Mapping[str, Any]) -> ParsedDataset:
        return self._parse(raw, {"dataset": "regional_statistics"})


_SOURCES: dict[str, type[_BaseSource]] = {
    "NMPA": NmpaSource,
    "NHSA": NhsaSource,
    "NHC": NhcSource,
    "NBS": NbsSource,
}


def get_source(source_code: str) -> _BaseSource:
    key = (source_code or "").strip().upper()
    source_type = _SOURCES.get(key)
    if source_type is None:
        raise UnsupportedSourceError(source_code)
    return source_type()


def supported_sources() -> list[dict[str, str]]:
    return [
        {"sourceCode": code, "parserVersion": source_type().parser_version}
        for code, source_type in _SOURCES.items()
    ]
