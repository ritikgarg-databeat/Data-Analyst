"""Tests for Kaggle integration (sections 8-10, 57 of the Phase 5 spec).

Mocks the Kaggle API entirely via a fake `KaggleClientProtocol`
implementation injected through `KaggleService.client_factory` — never
imports the real `kaggle` package and never requires real credentials or
network access, so this suite runs the same in CI as anywhere else.
"""

from __future__ import annotations

import zipfile
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.errors import AppError
from app.dependencies.services import get_kaggle_service
from app.kaggle.client import _safe_extract
from app.main import app
from app.services.kaggle_service import KaggleService


class FakeKaggleClient:
    """A deterministic stand-in for app.kaggle.client.KaggleClient."""

    def __init__(self) -> None:
        self.search_calls: list[tuple[str, int]] = []
        self.download_calls: list[tuple[str, str]] = []

    def search(self, query: str, page: int = 1) -> list[dict]:
        self.search_calls.append((query, page))
        return [
            {
                "ref": "someuser/customer-churn",
                "title": "Customer Churn Dataset",
                "subtitle": "Telecom churn data",
                "owner": "someuser",
                "url": "https://www.kaggle.com/datasets/someuser/customer-churn",
                "size_bytes": 123_456,
                "last_updated": "2024-01-01",
                "download_count": 10_000,
                "vote_count": 250,
                "usability_rating": 0.88,
                "license_name": "CC0: Public Domain",
                "tags": ["business", "telecom"],
            }
        ]

    def list_files(self, ref: str) -> list[dict]:
        return [
            {"name": "churn.csv", "size_bytes": 5_000, "creation_date": "2024-01-01"},
            {"name": "readme.txt", "size_bytes": 200, "creation_date": "2024-01-01"},
        ]

    def download_file(self, ref: str, file_name: str, dest_dir: Path) -> Path:
        self.download_calls.append((ref, file_name))
        dest_dir.mkdir(parents=True, exist_ok=True)
        path = dest_dir / file_name
        path.write_text("customer_id,churned\n1,0\n2,1\n3,1\n", encoding="utf-8")
        return path


@pytest.fixture
def fake_kaggle_client() -> FakeKaggleClient:
    return FakeKaggleClient()


@pytest.fixture
def configured_kaggle(fake_kaggle_client: FakeKaggleClient) -> Generator[FakeKaggleClient, None, None]:
    """Overrides the Kaggle dependency so this test's requests see a
    "configured" service backed entirely by the fake client above."""
    from tests.conftest import TestingSessionLocal

    def _service() -> KaggleService:
        session = TestingSessionLocal()
        settings = Settings(kaggle_username="test-user", kaggle_key="test-key")
        return KaggleService(session, settings=settings, client_factory=lambda _u, _k: fake_kaggle_client)

    app.dependency_overrides[get_kaggle_service] = _service
    yield fake_kaggle_client
    del app.dependency_overrides[get_kaggle_service]


class TestConfigurationDetection:
    def test_unconfigured_by_default_with_clear_setup_instructions(self, client: TestClient) -> None:
        response = client.get("/api/v1/kaggle/status")
        assert response.status_code == 200
        body = response.json()
        assert body["configured"] is False
        assert body["setup_instructions"] is not None
        assert "KAGGLE_USERNAME" in body["setup_instructions"]

    def test_searching_while_unconfigured_returns_a_clear_error_not_a_crash(self, client: TestClient) -> None:
        response = client.get("/api/v1/kaggle/search", params={"q": "churn"})
        assert response.status_code == 400
        assert "not configured" in response.json()["error"]["message"]

    def test_rest_of_the_dataset_hub_works_normally_while_kaggle_is_unconfigured(
        self, client: TestClient
    ) -> None:
        # Section 9: "The rest of the Dataset Hub must still work normally."
        response = client.get("/api/v1/datasets")
        assert response.status_code == 200

    def test_reports_configured_once_credentials_and_a_client_are_available(
        self, client: TestClient, configured_kaggle: FakeKaggleClient
    ) -> None:
        response = client.get("/api/v1/kaggle/status")
        assert response.json() == {"configured": True, "reason": None, "setup_instructions": None}


class TestSearch:
    def test_search_returns_results_from_the_client(
        self, client: TestClient, configured_kaggle: FakeKaggleClient
    ) -> None:
        response = client.get("/api/v1/kaggle/search", params={"q": "customer churn"})
        assert response.status_code == 200
        body = response.json()
        assert body["query"] == "customer churn"
        assert len(body["results"]) == 1
        result = body["results"][0]
        assert result["ref"] == "someuser/customer-churn"
        assert result["title"] == "Customer Churn Dataset"
        assert configured_kaggle.search_calls == [("customer churn", 1)]

    def test_search_forwards_the_page_parameter(
        self, client: TestClient, configured_kaggle: FakeKaggleClient
    ) -> None:
        client.get("/api/v1/kaggle/search", params={"q": "churn", "page": 2})
        assert configured_kaggle.search_calls == [("churn", 2)]


class TestFileListing:
    def test_lists_available_files_for_a_dataset(
        self, client: TestClient, configured_kaggle: FakeKaggleClient
    ) -> None:
        response = client.get("/api/v1/kaggle/datasets/someuser/customer-churn/files")
        assert response.status_code == 200
        body = response.json()
        assert body["ref"] == "someuser/customer-churn"
        names = {f["name"] for f in body["files"]}
        assert names == {"churn.csv", "readme.txt"}


class TestImport:
    def test_importing_selected_files_downloads_only_those_files_and_registers_the_dataset(
        self, client: TestClient, configured_kaggle: FakeKaggleClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        response = client.post(
            "/api/v1/kaggle/datasets/someuser/customer-churn/import",
            json={"name": "Churn Import", "files": ["churn.csv"], "business_domain": "Customer Analytics"},
        )
        assert response.status_code == 201
        created = response.json()
        dataset_dirs_cleanup.append(created["slug"])
        assert created["source_type"] == "KAGGLE"
        assert created["kaggle_ref"] == "someuser/customer-churn"

        # Only the explicitly selected file was downloaded — never the whole dataset unprompted.
        assert configured_kaggle.download_calls == [("someuser/customer-churn", "churn.csv")]

        # Background import runs synchronously under TestClient (see test_dataset_import.py) —
        # a follow-up GET reflects the finished state.
        settled = client.get(f"/api/v1/datasets/{created['slug']}").json()
        assert settled["status"] == "READY"
        assert settled["row_count"] == 3

    def test_importing_with_no_files_selected_is_rejected(
        self, client: TestClient, configured_kaggle: FakeKaggleClient
    ) -> None:
        response = client.post(
            "/api/v1/kaggle/datasets/someuser/customer-churn/import",
            json={"name": "Empty Import", "files": []},
        )
        assert response.status_code == 400

    def test_importing_while_unconfigured_is_rejected_with_a_clear_error(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/kaggle/datasets/someuser/customer-churn/import",
            json={"name": "Should Fail", "files": ["churn.csv"]},
        )
        assert response.status_code == 400
        assert "not configured" in response.json()["error"]["message"]


class TestZipSlipProtection:
    """Regression tests — `KaggleClient.download_file` used to call
    `zipfile.ZipFile.extractall` directly on a Kaggle-provided (i.e.
    network-fetched, third-party) archive, so a malicious member name
    containing `../` segments could write outside the intended destination
    directory. `_safe_extract` validates every member's resolved path stays
    under `dest_dir` before extracting anything."""

    def test_a_traversal_member_path_is_rejected_and_nothing_is_extracted(self, tmp_path: Path) -> None:
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        malicious_zip = tmp_path / "evil.zip"
        with zipfile.ZipFile(malicious_zip, "w") as zf:
            zf.writestr("../../escaped.txt", "pwned")

        with zipfile.ZipFile(malicious_zip) as zf, pytest.raises(AppError):
            _safe_extract(zf, dest_dir)

        assert not (tmp_path / "escaped.txt").exists()

    def test_a_normal_archive_still_extracts_correctly(self, tmp_path: Path) -> None:
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        good_zip = tmp_path / "good.zip"
        with zipfile.ZipFile(good_zip, "w") as zf:
            zf.writestr("data.csv", "a,b\n1,2\n")

        with zipfile.ZipFile(good_zip) as zf:
            _safe_extract(zf, dest_dir)

        assert (dest_dir / "data.csv").read_text() == "a,b\n1,2\n"
