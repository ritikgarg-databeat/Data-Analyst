from pydantic import BaseModel


class KaggleStatusResponse(BaseModel):
    configured: bool
    reason: str | None = None
    setup_instructions: str | None = None


class KaggleDatasetSummary(BaseModel):
    ref: str  # "<owner>/<dataset-slug>"
    title: str
    subtitle: str | None = None
    owner: str | None = None
    url: str | None = None
    size_bytes: int | None = None
    last_updated: str | None = None
    download_count: int | None = None
    vote_count: int | None = None
    usability_rating: float | None = None
    license_name: str | None = None
    tags: list[str] = []


class KaggleSearchResponse(BaseModel):
    query: str
    page: int
    results: list[KaggleDatasetSummary]


class KaggleFileSummary(BaseModel):
    name: str
    size_bytes: int | None = None
    creation_date: str | None = None


class KaggleFilesResponse(BaseModel):
    ref: str
    files: list[KaggleFileSummary]


class KaggleImportRequest(BaseModel):
    name: str
    files: list[str]
    description: str | None = None
    business_domain: str | None = None
    tags: list[str] = []
