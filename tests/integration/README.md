# Integration tests

Backend integration tests (API + real database, via SQLite for speed) live alongside the code they
test at `apps/api/tests/` — they use FastAPI's `TestClient` against a fully migrated, seeded schema,
so they already exercise the real request → router → service → repository → database path, not mocks.

This directory is reserved for *cross-service* integration tests that don't belong to a single app —
e.g. a future test that runs a migration, seeds the database, boots the API, and asserts the frontend
build can consume it end-to-end. None exist yet in Phase 1; see `tests/e2e/` for the current
end-to-end coverage.
