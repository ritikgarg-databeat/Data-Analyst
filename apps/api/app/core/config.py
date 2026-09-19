from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute, not relative: `env_file="./.env"` resolves against the process's
# CURRENT WORKING DIRECTORY, not this file's location — a distinction that
# has repeatedly hung/broken real commands (`uv run --project apps/api ...`
# invoked from the repo root, which every Makefile target and scripts/*.sh
# does, does NOT change the process's actual cwd to apps/api despite the
# `--project` flag "feeling" like it should). From repo root, `env_file`
# resolving to `<repo>/.env` (which doesn't exist — only `.env.example`
# does) silently falls back to `database_url`'s hard-coded Postgres default,
# which then hangs rather than failing fast connecting to a Postgres that
# isn't running. Anchoring to this file's own location makes `.env`
# resolution independent of cwd entirely, for every invocation pattern.
# Missing the file (e.g. inside a Docker image that never copies .env in) is
# harmless — pydantic-settings silently skips a nonexistent env_file and
# falls through to real process environment variables either way.
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    app_name: str = "Data Lab API"
    app_version: str = "0.1.0"
    environment: str = "development"  # development | test | production

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/data_analyst_lab"

    api_v1_prefix: str = "/api/v1"

    cors_origins: list[str] = ["http://localhost:3000"]

    # Local authentication/session configuration.
    auth_jwt_secret: str = "local-development-only-secret-change-before-production"
    auth_access_token_minutes: int = 15
    auth_refresh_token_days: int = 7
    auth_cookie_secure: bool = False
    auth_signup_enabled: bool = True
    auth_lockout_attempts: int = 5
    auth_lockout_minutes: int = 15
    auth_trusted_origin: str = "http://localhost:3000"
    auth_default_ai_quota: int = 25
    initial_admin_email: str = "admin@dataanalyst.com"
    initial_admin_password: str | None = None

    # Placeholders for future phases — no logic depends on these yet.
    kaggle_username: str | None = None
    kaggle_key: str | None = None

    log_level: str = "INFO"

    # --- SQL Lab (Phase 3) ---
    # Deliberately separate from `database_url` — the SQL Lab's Postgres
    # engine must never be able to reach the application's own metadata
    # tables. None (the default) means the Postgres engine is simply
    # reported unavailable; DuckDB has no such prerequisite.
    sql_lab_postgres_url: str | None = None
    sql_lab_query_timeout_seconds: float = 10.0
    sql_lab_row_limit: int = 1000
    sql_lab_preview_row_limit: int = 20

    @property
    def sql_lab_postgres_available(self) -> bool:
        return bool(self.sql_lab_postgres_url)

    # --- Python Lab (Phase 4) ---
    # Every one of these is a hard ceiling passed straight to the Docker
    # container (see app/python_lab/docker_backend.py) — none of them are
    # advisory. `python_lab_runtime_idle_ttl_seconds` is enforced by
    # PythonExecutionService.reap_idle_runtimes(), swept on API startup and
    # opportunistically on every runtime-list/create call (see
    # app/main.py) — this is a single-user local app, so a lightweight
    # sweep-on-access is enough; no separate scheduler process.
    # docker-py always talks to the Docker daemon on the HOST (whether the
    # api process is running there directly, or — via a mounted
    # /var/run/docker.sock, "Docker-out-of-Docker" — from inside the `api`
    # container itself). A volume-mount spec the daemon receives is always
    # resolved against the HOST filesystem, never the caller's own
    # container. Running directly on the host (no Docker), REPO_ROOT already
    # *is* a host path, so no override is needed there. Running via Docker
    # Compose, `api`'s own view of `data/sample` is a path *inside its own
    # image* — not the host — so docker-compose.yml bind-mounts
    # `./data/sample` into `api` too and sets this to the matching host-side
    # path string via `${PWD}`, purely so it can be handed back out to
    # sibling sandbox containers. See docs/architecture.md#python-lab-phase-4.
    python_lab_host_data_dir: str | None = None
    # Same host-path concern as python_lab_host_data_dir above, but for
    # data/datasets/ (Phase 5 user-imported datasets, mounted read-only at
    # /data/datasets inside the sandbox — see
    # app/python_lab/docker_backend.py's `extra_datasets_dir`).
    python_lab_host_datasets_dir: str | None = None
    python_lab_execution_timeout_seconds: float = 15.0
    python_lab_mem_limit: str = "512m"
    python_lab_nano_cpus: int = 1_000_000_000  # 1 CPU
    python_lab_pids_limit: int = 128
    python_lab_runtime_idle_ttl_seconds: int = 1800  # 30 minutes
    python_lab_max_concurrent_runtimes: int = 4

    # --- Dataset Hub (Phase 5) ---
    dataset_max_upload_mb: int = 500

    @property
    def dataset_max_upload_bytes(self) -> int:
        return self.dataset_max_upload_mb * 1024 * 1024

    # --- dbt Lab (Phase 7) ---
    # None (the defaults) means "use the repo's own data/sample/ecommerce and
    # data/warehouse/dev.duckdb" (see app/dbt_lab/paths.py) — overriding these
    # is only needed for tests, which point DBT_WAREHOUSE_PATH at a scratch
    # file so runs never touch the dev warehouse.
    dbt_data_dir: str | None = None
    dbt_warehouse_path: str | None = None
    dbt_command_timeout_seconds: float = 120.0

    @property
    def kaggle_configured(self) -> bool:
        return bool(self.kaggle_username) and bool(self.kaggle_key)

    # --- AI Layer (Phase 10) ---
    # Provider selection is env-driven and generic (section 2 of the spec) —
    # nothing in app/ai/ imports `openai` or `anthropic` at module load time,
    # and nothing hard-codes a provider name outside app/ai/providers/factory.py.
    # `ai_api_key` is the generic key used regardless of provider; a
    # provider-specific key (ai_openai_api_key/ai_anthropic_api_key) overrides
    # it for that provider only, so a user can hold keys for more than one
    # provider at once without the generic key being ambiguous.
    ai_provider: str = "local"  # "openai" | "anthropic" | "local"
    ai_model: str | None = None
    ai_api_key: str | None = None
    ai_openai_api_key: str | None = None
    ai_anthropic_api_key: str | None = None
    ai_openai_base_url: str = "https://api.openai.com/v1"
    ai_anthropic_base_url: str = "https://api.anthropic.com/v1"
    ai_request_timeout_seconds: float = 30.0
    ai_max_retries: int = 2
    # Hard ceilings applied by the Gateway regardless of what a request asks
    # for (section 42, "AI Cost Controls") — never advisory.
    ai_max_output_tokens: int = 1024
    ai_max_context_chars: int = 12_000
    ai_daily_request_limit: int = 200
    # Response caching (section 42) — identical (feature, mode, context hash,
    # message) requests within this TTL return the cached response instead of
    # calling the provider again; 0 disables caching.
    ai_response_cache_ttl_seconds: int = 300

    def _provider_api_key(self) -> str | None:
        if self.ai_provider == "openai":
            return self.ai_openai_api_key or self.ai_api_key
        if self.ai_provider == "anthropic":
            return self.ai_anthropic_api_key or self.ai_api_key
        return self.ai_api_key

    @property
    def ai_configured(self) -> bool:
        """LOCAL never needs a key (it's a deterministic, template-based
        fallback provider — see app/ai/providers/local_provider.py); every
        other provider needs a resolved API key before it can be used."""
        if self.ai_provider == "local":
            return True
        return bool(self._provider_api_key())

    @property
    def is_test(self) -> bool:
        return self.environment == "test"


@lru_cache
def get_settings() -> Settings:
    return Settings()
