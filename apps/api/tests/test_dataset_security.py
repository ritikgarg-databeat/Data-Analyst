"""Untrusted-input guard tests (app/dataset_hub/security.py) — section 58
of the Phase 5 spec: path traversal, unsafe filenames, unauthorized file
access via crafted names, oversized/malformed inputs."""

from __future__ import annotations

import pytest

from app.dataset_hub.security import (
    UnsafeFilenameError,
    assert_supported_extension,
    sanitize_filename,
    slugify,
    table_name_from_filename,
)


class TestSanitizeFilename:
    @pytest.mark.parametrize(
        "raw",
        [
            "",
            ".",
            "..",
            ".hidden.csv",
            "file\x00name.csv",
            "con.csv",
            "NUL.csv",
            "com1.csv",
            "file<>|?.csv",
            "file:name.csv",
            'file"name.csv',
        ],
    )
    def test_rejects_unsafe_names(self, raw: str) -> None:
        with pytest.raises(UnsafeFilenameError):
            sanitize_filename(raw)

    @pytest.mark.parametrize(
        "raw",
        [
            "../../etc/passwd.csv",
            "../../../secrets.csv",
            "..\\..\\windows\\system32\\config.csv",
            "/etc/passwd.csv",
            "C:\\Windows\\System32\\drivers\\etc\\hosts.csv",
            "some/dir/orders.csv",
            "some\\dir\\orders.csv",
        ],
    )
    def test_path_traversal_is_neutralized_to_a_bare_filename(self, raw: str) -> None:
        # Directory components (however an attacker tries to smuggle them
        # in) are always stripped down to a bare basename — the file is
        # then written under a server-controlled directory (data/raw/<slug>/),
        # so no traversal is actually reachable regardless of what survives.
        result = sanitize_filename(raw)
        assert "/" not in result
        assert "\\" not in result
        assert ".." not in result

    @pytest.mark.parametrize(
        "name", ["orders.csv", "customer_data-2024.parquet", "Sales Report.xlsx", "Sales Report (2024).csv"]
    )
    def test_accepts_normal_filenames(self, name: str) -> None:
        assert sanitize_filename(name)


class TestExtensionAllowlist:
    @pytest.mark.parametrize("ext", ["csv", "parquet", "json", "xlsx"])
    def test_accepts_supported_extensions(self, ext: str) -> None:
        assert assert_supported_extension(f"data.{ext}") == ext

    @pytest.mark.parametrize("filename", ["data.exe", "data.sh", "data.py", "data.php", "data"])
    def test_rejects_unsupported_or_missing_extensions(self, filename: str) -> None:
        from app.core.errors import AppError

        with pytest.raises((AppError, UnsafeFilenameError)):
            assert_supported_extension(filename)


class TestTableNameFromFilename:
    def test_produces_a_safe_sql_identifier(self) -> None:
        assert table_name_from_filename("Orders 2024!.csv") == "orders_2024"

    def test_never_starts_with_a_digit(self) -> None:
        name = table_name_from_filename("2024_orders.csv")
        assert name[0].isalpha()

    def test_is_deterministic(self) -> None:
        assert table_name_from_filename("orders.csv") == table_name_from_filename("orders.csv")


class TestSlugify:
    def test_produces_a_url_safe_slug(self) -> None:
        assert slugify("My Cool Dataset!!") == "my-cool-dataset"

    def test_empty_input_falls_back_to_a_default(self) -> None:
        assert slugify("   ") == "dataset"
