"""Tests for pdf-merger pure functions.

Only pure/testable functions are covered (no GTK/Nautilus dependencies):
- fmt_size: human-readable file size formatter
- get_pdf_pages: PDF page counter (uses pypdf)
"""

import os
import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Load pure functions without GTK
# ---------------------------------------------------------------------------


def _load_merger_functions():
    """Load pure functions from pdf_merger.py, skipping gi imports."""
    source = (Path(__file__).parent.parent / "pdf-merger" / "pdf_merger.py").read_text()

    namespace = {"os": os, "re": re}
    for line in source.split("\n"):
        stripped = line.strip()
        if stripped.startswith(("import gi", "from gi.", "gi.require_version")):
            continue
        if stripped.startswith("class ") and ("Gtk." in stripped or "GObject." in stripped):
            break
        namespace.setdefault("__builtins__", __builtins__)

    safe_lines = []
    for line in source.split("\n"):
        stripped = line.strip()
        if stripped.startswith(("import gi", "from gi.", "gi.require_version")):
            continue
        if stripped.startswith("class ") and ("Gtk." in stripped or "GObject." in stripped):
            break
        safe_lines.append(line)

    exec("\n".join(safe_lines), namespace)
    return namespace


_ns = _load_merger_functions()
fmt_size = _ns["fmt_size"]
get_pdf_pages = _ns["get_pdf_pages"]
merge_pdf_files = _ns.get("merge_pdf_files")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_minimal_pdf(num_pages: int = 1) -> bytes:
    """Build a minimal valid PDF with the given number of blank pages.

    Uses hand-crafted PDF syntax so we avoid any circular dependency on pypdf
    for fixture creation while still producing a file pypdf can read.
    """
    objects: list[bytes] = []

    # Object 1: catalog
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

    # Kids refs: pages will be objects 3, 4, 5 …
    first_page_obj = 3
    kid_refs = " ".join(f"{first_page_obj + i} 0 R" for i in range(num_pages))
    objects.append(
        f"2 0 obj\n<< /Type /Pages /Kids [{kid_refs}] /Count {num_pages} >>\nendobj\n".encode()
    )

    for i in range(num_pages):
        obj_num = first_page_obj + i
        objects.append(
            f"{obj_num} 0 obj\n"
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\n"
            f"endobj\n".encode()
        )

    # Assemble
    body = b"%PDF-1.4\n"
    offsets: list[int] = []
    for obj in objects:
        offsets.append(len(body))
        body += obj

    xref_offset = len(body)
    xref = f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        xref += f"{off:010d} 00000 n \n".encode()

    trailer = (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"
    ).encode()

    return body + xref + trailer


@pytest.fixture()
def single_page_pdf(tmp_path: Path) -> Path:
    """Write a single-page PDF to a temp file and return its path."""
    path = tmp_path / "single.pdf"
    path.write_bytes(_make_minimal_pdf(num_pages=1))
    return path


@pytest.fixture()
def multi_page_pdf(tmp_path: Path) -> Path:
    """Write a 3-page PDF to a temp file and return its path."""
    path = tmp_path / "multi.pdf"
    path.write_bytes(_make_minimal_pdf(num_pages=3))
    return path


@pytest.fixture()
def corrupt_pdf(tmp_path: Path) -> Path:
    """Write a file with a PDF header but corrupt body."""
    path = tmp_path / "corrupt.pdf"
    path.write_bytes(b"%PDF-1.4\nthis is not valid pdf content at all\n%%EOF\n")
    return path


# ---------------------------------------------------------------------------
# fmt_size
# ---------------------------------------------------------------------------


class TestFmtSize:
    def test_zero_bytes_returns_zero_b(self):
        assert fmt_size(0) == "0.0 B"

    def test_below_1kb_returns_bytes(self):
        assert fmt_size(500) == "500.0 B"

    def test_exactly_1kb_returns_kilobytes(self):
        assert fmt_size(1024) == "1.0 KB"

    def test_2kb_returns_kilobytes(self):
        assert fmt_size(2048) == "2.0 KB"

    def test_exactly_1mb_returns_megabytes(self):
        assert fmt_size(1024 * 1024) == "1.0 MB"

    def test_5mb_returns_megabytes(self):
        assert fmt_size(5 * 1024 * 1024) == "5.0 MB"

    def test_exactly_1gb_returns_gigabytes(self):
        assert fmt_size(1024**3) == "1.0 GB"

    def test_3gb_returns_gigabytes(self):
        assert fmt_size(3 * 1024**3) == "3.0 GB"

    def test_large_terabyte_value_returns_tb(self):
        # 2 TB
        assert fmt_size(2 * 1024**4) == "2.0 TB"

    def test_1_byte(self):
        assert fmt_size(1) == "1.0 B"

    def test_1023_bytes_stays_in_bytes(self):
        assert fmt_size(1023) == "1023.0 B"

    def test_return_type_is_string(self):
        assert isinstance(fmt_size(100), str)

    def test_output_contains_unit_suffix(self):
        result = fmt_size(1024)
        assert any(unit in result for unit in ["B", "KB", "MB", "GB", "TB"])

    def test_fractional_kb_shows_one_decimal(self):
        # 1536 bytes = 1.5 KB
        assert fmt_size(1536) == "1.5 KB"

    def test_fractional_mb_shows_one_decimal(self):
        # 1.5 MB
        assert fmt_size(int(1.5 * 1024 * 1024)) == "1.5 MB"


# ---------------------------------------------------------------------------
# get_pdf_pages
# ---------------------------------------------------------------------------


class TestGetPdfPages:
    def test_single_page_pdf_returns_1(self, single_page_pdf: Path):
        result = get_pdf_pages(str(single_page_pdf))
        assert result == 1

    def test_multi_page_pdf_returns_correct_count(self, multi_page_pdf: Path):
        result = get_pdf_pages(str(multi_page_pdf))
        assert result == 3

    def test_nonexistent_path_returns_minus_one(self, tmp_path: Path):
        result = get_pdf_pages(str(tmp_path / "does_not_exist.pdf"))
        assert result == -1

    def test_corrupt_pdf_returns_minus_one(self, corrupt_pdf: Path):
        result = get_pdf_pages(str(corrupt_pdf))
        assert result == -1

    def test_empty_file_returns_minus_one(self, tmp_path: Path):
        empty = tmp_path / "empty.pdf"
        empty.write_bytes(b"")
        result = get_pdf_pages(str(empty))
        assert result == -1

    def test_plain_text_file_returns_minus_one(self, tmp_path: Path):
        txt = tmp_path / "not_a_pdf.txt"
        txt.write_text("hello world")
        result = get_pdf_pages(str(txt))
        assert result == -1

    def test_return_type_is_int(self, single_page_pdf: Path):
        result = get_pdf_pages(str(single_page_pdf))
        assert isinstance(result, int)

    def test_valid_pdf_returns_non_negative(self, multi_page_pdf: Path):
        result = get_pdf_pages(str(multi_page_pdf))
        assert result >= 0

    def test_error_sentinel_is_exactly_minus_one(self, tmp_path: Path):
        result = get_pdf_pages(str(tmp_path / "missing.pdf"))
        assert result == -1

    def test_5_page_pdf_returns_5(self, tmp_path: Path):
        path = tmp_path / "five.pdf"
        path.write_bytes(_make_minimal_pdf(num_pages=5))
        result = get_pdf_pages(str(path))
        assert result == 5


# ---------------------------------------------------------------------------
# Regex pattern used in _suggest_output_name (extracted for pure testing)
# ---------------------------------------------------------------------------
# The method strips trailing number suffixes like "_1", "-2", " 3" from
# a filename stem before appending "_unione". We test the pattern directly.

_TRAILING_NUM_PATTERN = re.compile(r"[\s_\-]+\d+$")


class TestSuggestOutputNamePattern:
    """Tests for the trailing-number-strip regex used in _suggest_output_name."""

    def test_strips_underscore_number_suffix(self):
        base = _TRAILING_NUM_PATTERN.sub("", "documento_1")
        assert base == "documento"

    def test_strips_dash_number_suffix(self):
        base = _TRAILING_NUM_PATTERN.sub("", "report-2024")
        assert base == "report"

    def test_strips_space_number_suffix(self):
        base = _TRAILING_NUM_PATTERN.sub("", "file 3")
        assert base == "file"

    def test_strips_multi_digit_number(self):
        base = _TRAILING_NUM_PATTERN.sub("", "scan_123")
        assert base == "scan"

    def test_no_trailing_number_unchanged(self):
        base = _TRAILING_NUM_PATTERN.sub("", "documento")
        assert base == "documento"

    def test_name_that_is_only_number_stripped_to_empty(self):
        base = _TRAILING_NUM_PATTERN.sub("", "_1")
        assert base == ""

    def test_number_in_middle_not_stripped(self):
        base = _TRAILING_NUM_PATTERN.sub("", "doc2023final")
        assert base == "doc2023final"

    def test_multiple_trailing_delimiters_stripped(self):
        # e.g. "file__5" → "file"
        base = _TRAILING_NUM_PATTERN.sub("", "file__5")
        assert base == "file"


# ---------------------------------------------------------------------------
# merge_pdf_files
# ---------------------------------------------------------------------------


@pytest.mark.skipif(merge_pdf_files is None, reason="merge_pdf_files not loadable")
class TestMergePdfFiles:
    def test_merge_two_single_page_pdfs(self, tmp_path: Path):
        pdf_a = tmp_path / "a.pdf"
        pdf_b = tmp_path / "b.pdf"
        pdf_a.write_bytes(_make_minimal_pdf(num_pages=1))
        pdf_b.write_bytes(_make_minimal_pdf(num_pages=1))
        output = tmp_path / "merged.pdf"
        total = merge_pdf_files([str(pdf_a), str(pdf_b)], str(output))
        assert total == 2
        assert output.exists()

    def test_merge_preserves_total_page_count(self, tmp_path: Path):
        pdf_a = tmp_path / "a.pdf"
        pdf_b = tmp_path / "b.pdf"
        pdf_a.write_bytes(_make_minimal_pdf(num_pages=2))
        pdf_b.write_bytes(_make_minimal_pdf(num_pages=3))
        output = tmp_path / "merged.pdf"
        total = merge_pdf_files([str(pdf_a), str(pdf_b)], str(output))
        assert total == 5

    def test_merged_output_is_valid_pdf(self, tmp_path: Path):
        pdf_a = tmp_path / "a.pdf"
        pdf_b = tmp_path / "b.pdf"
        pdf_a.write_bytes(_make_minimal_pdf(num_pages=1))
        pdf_b.write_bytes(_make_minimal_pdf(num_pages=2))
        output = tmp_path / "merged.pdf"
        merge_pdf_files([str(pdf_a), str(pdf_b)], str(output))
        assert get_pdf_pages(str(output)) == 3

    def test_merge_single_file_returns_same_page_count(self, tmp_path: Path):
        pdf = tmp_path / "single.pdf"
        pdf.write_bytes(_make_minimal_pdf(num_pages=4))
        output = tmp_path / "merged.pdf"
        total = merge_pdf_files([str(pdf)], str(output))
        assert total == 4

    def test_merge_nonexistent_file_raises(self, tmp_path: Path):
        output = tmp_path / "merged.pdf"
        with pytest.raises(FileNotFoundError):
            merge_pdf_files([str(tmp_path / "missing.pdf")], str(output))

    def test_merge_corrupt_pdf_raises(self, tmp_path: Path):
        corrupt = tmp_path / "bad.pdf"
        corrupt.write_bytes(b"%PDF-1.4\ncorrupt content\n%%EOF\n")
        output = tmp_path / "merged.pdf"
        from pypdf.errors import PdfReadError

        with pytest.raises(PdfReadError):
            merge_pdf_files([str(corrupt)], str(output))


# ---------------------------------------------------------------------------
# Output path sanitization logic (mirrors _get_output_path behavior)
# ---------------------------------------------------------------------------


def _sanitize_output_name(raw: str) -> str:
    """Replicate _get_output_path sanitization logic for testing."""
    if not raw:
        raw = "unione.pdf"
    name = os.path.basename(raw)
    if not name or name.startswith("."):
        name = "unione.pdf"
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name


class TestOutputPathSanitization:
    """Tests for the path traversal prevention in output filename."""

    def test_path_traversal_stripped(self):
        assert _sanitize_output_name("../../evil.pdf") == "evil.pdf"

    def test_deep_path_traversal_stripped(self):
        assert _sanitize_output_name("../../../etc/passwd") == "passwd.pdf"

    def test_absolute_path_stripped(self):
        assert _sanitize_output_name("/etc/shadow") == "shadow.pdf"

    def test_dotfile_rejected(self):
        assert _sanitize_output_name(".hidden") == "unione.pdf"

    def test_empty_string_defaults(self):
        assert _sanitize_output_name("") == "unione.pdf"

    def test_normal_name_preserved(self):
        assert _sanitize_output_name("my_document.pdf") == "my_document.pdf"

    def test_pdf_extension_added_if_missing(self):
        assert _sanitize_output_name("report") == "report.pdf"

    def test_pdf_extension_case_insensitive(self):
        assert _sanitize_output_name("file.PDF") == "file.PDF"

    def test_whitespace_only_gets_extension(self):
        # basename("   ") = "   ", which gets .pdf appended
        # In real code, get_text().strip() handles this before calling the logic
        result = _sanitize_output_name("   ")
        assert result.endswith(".pdf")
