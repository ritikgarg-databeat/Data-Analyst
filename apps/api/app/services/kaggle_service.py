"""Search/inspect/import against Kaggle (sections 8-10 of the Phase 5
spec). `client_factory` is injectable so tests substitute a fake
`KaggleClientProtocol` implementation — see tests/test_kaggle.py — never
requiring real credentials or network access in CI (section 57)."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.dataset_hub import import_service
from app.dataset_hub.paths import raw_dir_for
from app.dataset_hub.security import assert_supported_extension
from app.kaggle.client import KaggleClient, KaggleClientProtocol
from app.schemas.dataset import Dataset as DatasetSchema
from app.schemas.kaggle import (
    KaggleDatasetSummary,
    KaggleFilesResponse,
    KaggleFileSummary,
    KaggleImportRequest,
    KaggleSearchResponse,
    KaggleStatusResponse,
)
from app.services.dataset_service import DatasetService

SETUP_INSTRUCTIONS = (
    "Kaggle integration is not configured.\n\n"
    "1. Create a free Kaggle account, then go to Settings -> API -> Create New Token.\n"
    "2. This downloads a kaggle.json file containing a username and key.\n"
    "3. Copy those two values into KAGGLE_USERNAME and KAGGLE_KEY in your .env file "
    "(see .env.example) — never commit this file.\n"
    "4. Restart the API. Kaggle search and import will then be available.\n\n"
    "Your credentials stay server-side — they are never sent to the browser."
)

_ClientFactory = Callable[[str, str], KaggleClientProtocol]


def _default_client_factory(username: str, key: str) -> KaggleClientProtocol:
    return KaggleClient(username, key)


class KaggleService:
    def __init__(
        self,
        db: Session,
        settings: Settings | None = None,
        client_factory: _ClientFactory | None = None,
        user_id: str | None = None,
    ) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self._client_factory = client_factory or _default_client_factory
        self.user_id = user_id

    def is_configured(self) -> bool:
        return self.settings.kaggle_configured

    def status(self) -> KaggleStatusResponse:
        if self.is_configured():
            return KaggleStatusResponse(configured=True)
        return KaggleStatusResponse(
            configured=False,
            reason="KAGGLE_USERNAME and/or KAGGLE_KEY are not set.",
            setup_instructions=SETUP_INSTRUCTIONS,
        )

    def _client(self) -> KaggleClientProtocol:
        if not self.is_configured():
            raise AppError("Kaggle integration is not configured.", details={"setup": SETUP_INSTRUCTIONS})
        return self._client_factory(self.settings.kaggle_username, self.settings.kaggle_key)  # type: ignore[arg-type]

    def search(self, query: str, page: int = 1) -> KaggleSearchResponse:
        results = self._client().search(query, page=page)
        return KaggleSearchResponse(
            query=query, page=page, results=[KaggleDatasetSummary(**r) for r in results]
        )

    def list_files(self, ref: str) -> KaggleFilesResponse:
        files = self._client().list_files(ref)
        return KaggleFilesResponse(ref=ref, files=[KaggleFileSummary(**f) for f in files])

    def start_import(
        self, ref: str, payload: KaggleImportRequest, background_tasks: BackgroundTasks
    ) -> DatasetSchema:
        if not payload.files:
            raise AppError("Select at least one file to import.")
        client = self._client()

        dataset_service = DatasetService(self.db, self.settings, self.user_id)
        dataset = dataset_service.create_kaggle_dataset_shell(
            payload.name,
            description=payload.description,
            business_domain=payload.business_domain,
            tags=payload.tags,
            kaggle_ref=ref,
        )

        dest_dir = raw_dir_for(dataset.slug, self.user_id)
        staged = []
        for file_name in payload.files:
            downloaded = client.download_file(ref, file_name, dest_dir)
            file_format = assert_supported_extension(downloaded.name)
            staged.append(
                import_service.StagedFile(
                    filename=downloaded.name, raw_path=downloaded, file_format=file_format
                )
            )

        background_tasks.add_task(import_service.process_dataset_import, self.db, dataset.id, staged)
        return dataset_service.to_schema(dataset)
