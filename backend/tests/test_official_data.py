from __future__ import annotations

import json
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from carepath.official_data.contracts import (
    DatasetSnapshot,
    DuplicateSnapshotError,
    SnapshotValidationError,
    UnsupportedSourceError,
)
from carepath.official_data.normalization import (
    compute_checksum,
    derive_status,
    validate_snapshot,
)
from carepath.official_data.service import import_snapshot
from carepath.official_data.sources import get_source, supported_sources

FIXTURES = Path(__file__).parent / "fixtures" / "official"
PARSER_CASES = [
    ("NMPA", "nmpa", "drug_approvals"),
    ("NHSA", "nhsa", "insurance_catalogue"),
    ("NHC", "nhc", "medical_institutions"),
    ("NBS", "nbs", "regional_statistics"),
]


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def snapshot_from(parsed, *, reviewer: str = "测试审核员") -> DatasetSnapshot:
    return DatasetSnapshot(
        source_code=parsed.source_code,
        title=parsed.title,
        version=parsed.version,
        source_url=parsed.source_url,
        published_at=parsed.published_at,
        effective_at=parsed.effective_at,
        checksum=compute_checksum(parsed.content),
        parser_version=parsed.parser_version,
        reviewer=reviewer,
        content=parsed.content,
        status=derive_status(parsed),
    )


class FakeRepository:
    def __init__(self) -> None:
        self.snapshots: list[DatasetSnapshot] = []

    async def exists_by_checksum(self, checksum: str) -> bool:
        return any(item.checksum == checksum for item in self.snapshots)

    async def add(self, snapshot: DatasetSnapshot) -> str:
        self.snapshots.append(snapshot)
        return f"dataset-{len(self.snapshots)}"


@pytest.mark.parametrize(("source_code", "fixture", "dataset_key"), PARSER_CASES)
def test_each_source_normalises_its_fixture(
    source_code: str,
    fixture: str,
    dataset_key: str,
) -> None:
    source = get_source(source_code)
    parsed = source.parse(load_fixture(fixture))

    assert parsed.source_code == source_code
    assert parsed.parser_version == source.parser_version
    assert parsed.content["dataset"] == dataset_key
    assert parsed.content["recordCount"] == 2
    assert parsed.unverified is False
    assert len(compute_checksum(parsed.content)) == 64


def test_supported_sources_expose_parser_versions() -> None:
    codes = {item["sourceCode"] for item in supported_sources()}
    assert codes == {"NMPA", "NHSA", "NHC", "NBS"}


def test_unknown_source_is_rejected() -> None:
    with pytest.raises(UnsupportedSourceError):
        get_source("WHO")


def test_checksum_is_stable_and_content_sensitive() -> None:
    first = compute_checksum({"records": [{"name": "A"}]})
    second = compute_checksum({"records": [{"name": "A"}]})
    changed = compute_checksum({"records": [{"name": "B"}]})

    assert first == second
    assert first != changed


def test_validation_rejects_missing_reviewer_and_insecure_url() -> None:
    parsed = get_source("NMPA").parse(load_fixture("nmpa"))
    snapshot = snapshot_from(parsed)
    assert validate_snapshot(snapshot) == []

    blank_reviewer = validate_snapshot(replace(snapshot, reviewer="  "))
    assert "审核人不能为空" in blank_reviewer

    insecure = validate_snapshot(replace(snapshot, source_url="http://example.test/"))
    assert any("https" in error for error in insecure)


def test_validation_rejects_published_after_effective() -> None:
    parsed = get_source("NHSA").parse(load_fixture("nhsa"))
    snapshot = replace(
        snapshot_from(parsed),
        published_at=date(2026, 11, 1),
        effective_at=date(2026, 10, 1),
    )
    errors = validate_snapshot(snapshot)
    assert "发布日期不能晚于生效日期" in errors


def test_status_becomes_stale_after_validity_window() -> None:
    parsed = get_source("NHC").parse(load_fixture("nhc"))

    assert derive_status(parsed, today=date(2026, 10, 2)) == "VERIFIED"
    assert derive_status(parsed, today=date(2027, 10, 2)) == "STALE"


def test_unverified_record_is_flagged() -> None:
    raw = load_fixture("nmpa")
    raw["records"] = [{"approvalNumber": "国药准字H20260001", "name": "缺厂商"}]
    parsed = get_source("NMPA").parse(raw)

    assert parsed.unverified is True
    assert derive_status(parsed) == "UNVERIFIED"


@pytest.mark.asyncio
async def test_service_persists_once_and_rejects_duplicate() -> None:
    repository = FakeRepository()
    source = get_source("NBS")
    raw = load_fixture("nbs")

    stored = await import_snapshot(source, raw, repository, reviewer="审核员")

    assert stored.id == "dataset-1"
    assert stored.status == "VERIFIED"
    assert len(repository.snapshots) == 1

    with pytest.raises(DuplicateSnapshotError):
        await import_snapshot(source, raw, repository, reviewer="审核员")


@pytest.mark.asyncio
async def test_service_rejects_invalid_snapshot() -> None:
    repository = FakeRepository()
    with pytest.raises(SnapshotValidationError):
        await import_snapshot(
            get_source("NMPA"),
            load_fixture("nmpa"),
            repository,
            reviewer="   ",
        )
    assert repository.snapshots == []


@pytest.mark.asyncio
async def test_service_marks_unverified_snapshot() -> None:
    repository = FakeRepository()
    raw = load_fixture("nhc")
    raw["records"] = [{"institutionName": "缺少地区码"}]

    stored = await import_snapshot(
        get_source("NHC"),
        raw,
        repository,
        reviewer="审核员",
    )

    assert stored.status == "UNVERIFIED"


async def _login(client, username: str) -> dict:
    from carepath.seed import DEMO_PASSWORDS

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": DEMO_PASSWORDS[username]},
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.asyncio
async def test_admin_imports_source_snapshot_and_duplicate_is_409(client) -> None:
    admin = await _login(client, "admin")
    headers = {"Authorization": f"Bearer {admin['accessToken']}"}
    body = {"payload": load_fixture("nmpa")}

    created = await client.post(
        "/api/v1/admin/official-datasets/sources/NMPA/import",
        headers=headers,
        json=body,
    )
    assert created.status_code == 201, created.text
    dataset = created.json()
    assert dataset["sourceCode"] == "NMPA"
    assert dataset["parserVersion"] == "nmpa-json-v1"
    assert dataset["status"] == "VERIFIED"
    assert len(dataset["checksum"]) == 64

    duplicate = await client.post(
        "/api/v1/admin/official-datasets/sources/NMPA/import",
        headers=headers,
        json=body,
    )
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_sources_listing_and_role_guard(client) -> None:
    admin = await _login(client, "admin")
    headers = {"Authorization": f"Bearer {admin['accessToken']}"}
    listing = await client.get("/api/v1/admin/official-datasets/sources", headers=headers)
    assert listing.status_code == 200
    assert {item["sourceCode"] for item in listing.json()} == {"NMPA", "NHSA", "NHC", "NBS"}

    patient = await _login(client, "patient")
    patient_headers = {"Authorization": f"Bearer {patient['accessToken']}"}
    denied = await client.get(
        "/api/v1/admin/official-datasets/sources",
        headers=patient_headers,
    )
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_invalid_snapshot_returns_422(client) -> None:
    admin = await _login(client, "admin")
    headers = {"Authorization": f"Bearer {admin['accessToken']}"}
    payload = load_fixture("nhsa")
    payload["sourceUrl"] = "http://insecure.example"

    response = await client.post(
        "/api/v1/admin/official-datasets/sources/NHSA/import",
        headers=headers,
        json={"payload": payload},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "INVALID_SNAPSHOT"


@pytest.mark.asyncio
async def test_unknown_source_returns_404(client) -> None:
    admin = await _login(client, "admin")
    response = await client.post(
        "/api/v1/admin/official-datasets/sources/WHO/import",
        headers={"Authorization": f"Bearer {admin['accessToken']}"},
        json={"payload": {}},
    )
    assert response.status_code == 404
