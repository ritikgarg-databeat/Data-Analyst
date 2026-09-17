"""A thin wrapper around the official `kaggle` PyPI client (section 8 of the
Phase 5 spec: "Use the official Kaggle API. Do not scrape Kaggle pages.").

`kaggle` is imported lazily, inside methods — mirroring exactly how
`app/python_lab/docker_backend.py` lazily imports `docker` — so the core
test suite and the API process never require it to be installed (it's an
optional extra, see pyproject.toml's `kaggle` group) and importing this
module never touches the network or reads `~/.kaggle/kaggle.json`.

Authentication uses the classic KAGGLE_USERNAME/KAGGLE_KEY environment
variables (kaggle==1.6.x — see pyproject.toml's version pin comment),
sourced from `Settings`, never from a `kaggle.json` file on disk and never
exposed to the frontend."""

from __future__ import annotations

import os
import zipfile
from pathlib import Path
from typing import Any, Protocol

from app.core.errors import AppError


def _safe_extract(zf: zipfile.ZipFile, dest_dir: Path) -> None:
    """Guards against zip-slip: a malicious archive member whose name
    contains `../` segments (or an absolute path) that would otherwise let
    `extractall` write outside `dest_dir` — this is a real, network-fetched
    third-party archive (a Kaggle dataset file), never a trusted input."""
    resolved_dest = dest_dir.resolve()
    for member in zf.infolist():
        member_path = (dest_dir / member.filename).resolve()
        if resolved_dest != member_path and resolved_dest not in member_path.parents:
            raise AppError(f"Refusing to extract unsafe archive member path: '{member.filename}'.")
    zf.extractall(dest_dir)


class KaggleClientProtocol(Protocol):
    """The interface `KaggleService` depends on — implemented by both
    `KaggleClient` (real) and the fakes in tests/test_kaggle.py (mocked)."""

    def search(self, query: str, page: int = 1) -> list[dict[str, Any]]: ...
    def list_files(self, ref: str) -> list[dict[str, Any]]: ...
    def download_file(self, ref: str, file_name: str, dest_dir: Path) -> Path: ...


class KaggleClient:
    def __init__(self, username: str, key: str) -> None:
        self.username = username
        self.key = key
        self._api = None

    def _get_api(self):
        if self._api is not None:
            return self._api
        try:
            import kaggle  # noqa: F401 — import error caught below, unused otherwise
        except ImportError as exc:
            raise AppError(
                "The 'kaggle' package is not installed. Run: uv sync --project apps/api --extra kaggle"
            ) from exc

        # Set just for this process, never persisted or written to disk —
        # kaggle.api.authenticate() reads these two env vars directly.
        os.environ["KAGGLE_USERNAME"] = self.username
        os.environ["KAGGLE_KEY"] = self.key
        from kaggle.api.kaggle_api_extended import KaggleApi

        api = KaggleApi()
        try:
            api.authenticate()
        except Exception as exc:  # noqa: BLE001 — any auth failure maps to one clear message
            raise AppError(f"Kaggle authentication failed: {exc}") from exc
        self._api = api
        return api

    def search(self, query: str, page: int = 1) -> list[dict[str, Any]]:
        api = self._get_api()
        try:
            results = api.dataset_list(search=query, page=page)
        except Exception as exc:  # noqa: BLE001
            raise AppError(f"Kaggle search failed: {exc}") from exc
        return [_dataset_to_dict(d) for d in results]

    def list_files(self, ref: str) -> list[dict[str, Any]]:
        api = self._get_api()
        try:
            result = api.dataset_list_files(ref)
        except Exception as exc:  # noqa: BLE001
            raise AppError(f"Could not list files for Kaggle dataset '{ref}': {exc}") from exc
        return [_file_to_dict(f) for f in getattr(result, "files", [])]

    def download_file(self, ref: str, file_name: str, dest_dir: Path) -> Path:
        """Downloads exactly one file from the dataset (never the whole
        dataset) — section 10: "Do not automatically download massive
        datasets without explicit user action."."""
        api = self._get_api()
        dest_dir.mkdir(parents=True, exist_ok=True)
        try:
            api.dataset_download_file(ref, file_name, path=str(dest_dir), force=True, quiet=True)
        except Exception as exc:  # noqa: BLE001
            raise AppError(f"Could not download '{file_name}' from '{ref}': {exc}") from exc

        target = dest_dir / file_name
        zipped = dest_dir / f"{file_name}.zip"
        if zipped.exists() and not target.exists():
            with zipfile.ZipFile(zipped) as zf:
                _safe_extract(zf, dest_dir)
            zipped.unlink(missing_ok=True)
        if not target.exists():
            raise AppError(f"Kaggle download for '{file_name}' did not produce the expected file.")
        return target


def _dataset_to_dict(d: Any) -> dict[str, Any]:
    ref = str(getattr(d, "ref", ""))
    return {
        "ref": ref,
        "title": getattr(d, "title", None) or ref,
        "subtitle": getattr(d, "subtitle", None),
        "owner": getattr(d, "ownerName", None) or (ref.split("/")[0] if "/" in ref else None),
        "url": f"https://www.kaggle.com/datasets/{ref}" if ref else None,
        "size_bytes": getattr(d, "totalBytes", None),
        "last_updated": str(getattr(d, "lastUpdated", "") or "") or None,
        "download_count": getattr(d, "downloadCount", None),
        "vote_count": getattr(d, "voteCount", None),
        "usability_rating": getattr(d, "usabilityRating", None),
        "license_name": getattr(d, "licenseName", None),
        "tags": [str(getattr(t, "name", t)) for t in getattr(d, "tags", []) or []],
    }


def _file_to_dict(f: Any) -> dict[str, Any]:
    return {
        "name": getattr(f, "name", str(f)),
        "size_bytes": getattr(f, "totalBytes", None),
        "creation_date": str(getattr(f, "creationDate", "") or "") or None,
    }
