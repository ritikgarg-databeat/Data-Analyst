from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


def resolve_repo_path(relative_path: str) -> Path:
    """Resolves a repo-root-relative path (as stored on SqlTable.file_path) to
    an absolute path, e.g. "data/sample/ecommerce/orders.csv"."""
    return REPO_ROOT / relative_path
