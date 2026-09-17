"""Untrusted-input guards for dataset import (section 58 of the Phase 5
spec) — every uploaded filename, table name, and Kaggle-supplied path
string passes through here before it ever touches the filesystem or SQL."""

from __future__ import annotations

import re

from app.core.errors import AppError

ALLOWED_EXTENSIONS = {"csv", "parquet", "json", "xlsx"}

# Conservative allowlist: letters, digits, underscore, hyphen, dot — enough
# for any real-world dataset filename — including the spaces/parentheses
# common in real-world exports like "Sales Report (2024).xlsx" — while still
# excluding every path separator, shell metacharacter, and every character
# Windows itself forbids in a filename (\/:*?"<>|).
_SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._()\[\]-]{0,150}$")
_SAFE_TABLE_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")

_WINDOWS_RESERVED = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}  # fmt: skip


class UnsafeFilenameError(AppError):
    code = "unsafe_filename"


def sanitize_filename(raw_name: str) -> str:
    """Strips any directory component and validates what's left — rejects
    path traversal (`../`), absolute paths, null bytes, hidden/dotfiles,
    and Windows-reserved device names, never trusts the client-supplied
    filename verbatim."""
    if not raw_name or "\x00" in raw_name:
        raise UnsafeFilenameError("The uploaded file has an invalid name.")

    # Strip any path the client tried to smuggle in (both separator styles —
    # a request can arrive from any OS regardless of what this server runs on).
    name = raw_name.replace("\\", "/").rsplit("/", 1)[-1].strip()

    if name in ("", ".", "..") or name.startswith("."):
        raise UnsafeFilenameError(f"Unsafe file name: '{raw_name}'.")
    if not _SAFE_FILENAME_RE.match(name):
        raise UnsafeFilenameError(
            f"File name '{raw_name}' contains unsupported characters. "
            "Use letters, numbers, dots, hyphens, and underscores only."
        )
    stem = name.rsplit(".", 1)[0].lower()
    if stem in _WINDOWS_RESERVED:
        raise UnsafeFilenameError(f"'{raw_name}' is a reserved device name and cannot be used.")
    return name


def extension_of(filename: str) -> str:
    if "." not in filename:
        raise UnsafeFilenameError(f"File '{filename}' has no extension.")
    return filename.rsplit(".", 1)[-1].lower()


def assert_supported_extension(filename: str) -> str:
    ext = extension_of(filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise AppError(
            f"Unsupported file format '.{ext}'. Supported formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}.",
            details={"filename": filename, "extension": ext},
        )
    return ext


def table_name_from_filename(filename: str) -> str:
    """Derives a safe SQL/DuckDB identifier from a filename stem — used as
    both the DatasetTable/SqlTable table_name and the on-disk Parquet
    filename, so it must be safe in both contexts."""
    stem = filename.rsplit(".", 1)[0].lower()
    slug = re.sub(r"[^a-z0-9]+", "_", stem).strip("_") or "table"
    if not slug[0].isalpha():
        slug = f"t_{slug}"
    slug = slug[:64]
    if not _SAFE_TABLE_NAME_RE.match(slug):
        raise UnsafeFilenameError(f"Could not derive a safe table name from '{filename}'.")
    return slug


def slugify(raw: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", raw.strip().lower()).strip("-")
    return slug or "dataset"
