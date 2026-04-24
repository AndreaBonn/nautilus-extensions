"""Tests for pdf-splitter pure functions."""

import os

from conftest import ROOT, _load_module_functions

_ns = _load_module_functions(
    ROOT / "pdf-splitter" / "pdf_splitter.py",
    "pdf_splitter",
    [
        "parse_ranges",
        "every_n_chunks",
        "single_page_chunks",
        "chunk_filename",
        "bookmark_chunks",
        "fmt_size",
    ],
)
parse_ranges = _ns["parse_ranges"]
every_n_chunks = _ns["every_n_chunks"]
single_page_chunks = _ns["single_page_chunks"]
chunk_filename = _ns["chunk_filename"]
bookmark_chunks = _ns["bookmark_chunks"]
fmt_size = _ns["fmt_size"]


# --- parse_ranges ---


class TestParseRanges:
    def test_single_page(self):
        assert parse_ranges("3", total_pages=10) == [(2, 2)]

    def test_range(self):
        assert parse_ranges("1-3", total_pages=10) == [(0, 2)]

    def test_multiple_ranges(self):
        result = parse_ranges("1-3, 5, 7-9", total_pages=10)
        assert result == [(0, 2), (4, 4), (6, 8)]

    def test_semicolon_separator(self):
        result = parse_ranges("1-2; 4", total_pages=10)
        assert result == [(0, 1), (3, 3)]

    def test_page_out_of_range_returns_error(self):
        result = parse_ranges("15", total_pages=10)
        assert isinstance(result, str)
        assert "non esiste" in result

    def test_inverted_range_returns_error(self):
        result = parse_ranges("5-3", total_pages=10)
        assert isinstance(result, str)
        assert "non valido" in result

    def test_invalid_format_returns_error(self):
        result = parse_ranges("abc", total_pages=10)
        assert isinstance(result, str)
        assert "non riconosciuto" in result

    def test_empty_string_returns_error(self):
        result = parse_ranges("", total_pages=10)
        assert isinstance(result, str)

    def test_zero_page_returns_error(self):
        result = parse_ranges("0", total_pages=10)
        assert isinstance(result, str)


# --- every_n_chunks ---


class TestEveryNChunks:
    def test_even_split(self):
        assert every_n_chunks(total=10, n=5) == [(0, 4), (5, 9)]

    def test_uneven_split(self):
        result = every_n_chunks(total=7, n=3)
        assert result == [(0, 2), (3, 5), (6, 6)]

    def test_single_chunk(self):
        assert every_n_chunks(total=3, n=10) == [(0, 2)]

    def test_one_page_per_chunk(self):
        assert every_n_chunks(total=3, n=1) == [(0, 0), (1, 1), (2, 2)]


# --- single_page_chunks ---


class TestSinglePageChunks:
    def test_three_pages(self):
        assert single_page_chunks(3) == [(0, 0), (1, 1), (2, 2)]

    def test_one_page(self):
        assert single_page_chunks(1) == [(0, 0)]


# --- chunk_filename ---


class TestChunkFilename:
    def test_page_range(self):
        assert chunk_filename("doc", start=0, end=2) == "doc_pag1-3.pdf"

    def test_single_page(self):
        assert chunk_filename("doc", start=4, end=4) == "doc_pag5.pdf"

    def test_with_title(self):
        result = chunk_filename("doc", start=0, end=5, title="Chapter One")
        assert result == "doc_Chapter_One.pdf"

    def test_title_with_special_chars_sanitized(self):
        result = chunk_filename("doc", start=0, end=5, title="Ch@pt3r../../../etc")
        assert "../" not in result
        assert result.endswith(".pdf")

    def test_base_with_path_traversal_sanitized(self):
        result = chunk_filename("../../evil", start=0, end=0)
        assert "../" not in result

    def test_empty_title_falls_back_to_pages(self):
        result = chunk_filename("doc", start=0, end=2, title="!@#$%")
        assert "pag" in result


# --- fmt_size ---


class TestFmtSize:
    def test_bytes(self):
        assert fmt_size(500) == "500.0 B"

    def test_kilobytes(self):
        assert fmt_size(2048) == "2.0 KB"

    def test_megabytes(self):
        assert fmt_size(5 * 1024 * 1024) == "5.0 MB"

    def test_gigabytes(self):
        assert fmt_size(3 * 1024**3) == "3.0 GB"

    def test_zero(self):
        assert fmt_size(0) == "0.0 B"


# --- bookmark_chunks ---


class TestBookmarkChunks:
    @staticmethod
    def _fake_bookmark(title: str, page_idnum: int):
        class FakePage:
            pass

        class FakeBookmark:
            pass

        bm = FakeBookmark()
        bm.title = title
        bm.page = FakePage()
        bm.page.idnum = page_idnum
        return bm

    def test_empty_bookmarks_returns_empty(self):
        assert bookmark_chunks([], total_pages=10) == []

    def test_single_bookmark_covers_all_pages(self):
        bms = [self._fake_bookmark("Intro", 0)]
        result = bookmark_chunks(bms, total_pages=10)
        assert result == [(0, 9, "Intro")]

    def test_two_bookmarks_produce_correct_ranges(self):
        bms = [
            self._fake_bookmark("Ch1", 0),
            self._fake_bookmark("Ch2", 5),
        ]
        result = bookmark_chunks(bms, total_pages=10)
        assert result == [(0, 4, "Ch1"), (5, 9, "Ch2")]

    def test_last_bookmark_extends_to_end(self):
        bms = [
            self._fake_bookmark("A", 0),
            self._fake_bookmark("B", 7),
        ]
        result = bookmark_chunks(bms, total_pages=10)
        assert result[-1] == (7, 9, "B")

    def test_bookmarks_sorted_by_page(self):
        bms = [
            self._fake_bookmark("Second", 5),
            self._fake_bookmark("First", 0),
        ]
        result = bookmark_chunks(bms, total_pages=10)
        assert result[0][2] == "First"
        assert result[1][2] == "Second"

    def test_special_chars_in_title_sanitized(self):
        bms = [self._fake_bookmark("Ch/1: <evil>&more", 0)]
        result = bookmark_chunks(bms, total_pages=5)
        title = result[0][2]
        assert "/" not in title
        assert "<" not in title
        assert "&" not in title

    def test_title_truncated_at_50_chars(self):
        long_title = "A" * 100
        bms = [self._fake_bookmark(long_title, 0)]
        result = bookmark_chunks(bms, total_pages=5)
        assert len(result[0][2]) <= 50

    def test_nested_bookmarks_as_list(self):
        inner = [self._fake_bookmark("Nested", 3)]
        bms = [self._fake_bookmark("Top", 0), inner]
        result = bookmark_chunks(bms, total_pages=10)
        assert len(result) == 2
        assert result[1][2] == "Nested"

    def test_bookmark_without_page_attr_skipped(self):
        class NoPage:
            title = "Bad"

        bms = [NoPage(), self._fake_bookmark("Good", 0)]
        result = bookmark_chunks(bms, total_pages=5)
        assert len(result) == 1
        assert result[0][2] == "Good"


# ---------------------------------------------------------------------------
# Integration: split PDF file with pypdf (mirrors _do_split core logic)
# ---------------------------------------------------------------------------

import pypdf
import pytest

HAS_PYPDF = True


def _make_minimal_pdf(num_pages: int = 1) -> bytes:
    """Build a minimal valid PDF with blank pages (hand-crafted, no pypdf)."""
    objects = []
    obj_id = 1

    catalog_id = obj_id
    objects.append(f"{obj_id} 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")
    obj_id += 1

    pages_id = obj_id
    page_ids = list(range(obj_id + 1, obj_id + 1 + num_pages))
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects.append(
        f"{pages_id} 0 obj\n<< /Type /Pages /Kids [{kids}] /Count {num_pages} >>\nendobj"
    )
    obj_id += 1

    for _ in range(num_pages):
        objects.append(
            f"{obj_id} 0 obj\n"
            f"<< /Type /Page /Parent {pages_id} 0 R "
            f"/MediaBox [0 0 612 792] >>\nendobj"
        )
        obj_id += 1

    body = "\n".join(objects)
    xref_offset = len(f"%PDF-1.4\n{body}\n")
    xref = f"xref\n0 {obj_id}\n"
    xref += "0000000000 65535 f \n"
    offset = len("%PDF-1.4\n")
    for obj_str in objects:
        xref += f"{offset:010d} 00000 n \n"
        offset += len(obj_str) + 1

    trailer = (
        f"trailer\n<< /Size {obj_id} /Root {catalog_id} 0 R >>\nstartxref\n{xref_offset}\n%%EOF"
    )
    return f"%PDF-1.4\n{body}\n{xref}{trailer}".encode()


@pytest.mark.skipif(not HAS_PYPDF, reason="pypdf not installed")
class TestSplitPdfIntegration:
    """Integration tests that actually split PDF files using pypdf."""

    def _do_split(self, input_path: str, chunks: list, out_folder: str) -> list[str]:
        """Replicate _do_split core logic without GTK."""
        reader = pypdf.PdfReader(input_path, strict=False)
        base = os.path.splitext(os.path.basename(input_path))[0]
        created = []

        for chunk in chunks:
            start, end = chunk[0], chunk[1]
            title = chunk[2] if len(chunk) > 2 else None

            writer = pypdf.PdfWriter()
            for page_idx in range(start, end + 1):
                writer.add_page(reader.pages[page_idx])

            filename = chunk_filename(base, start, end, title)
            out_path = os.path.join(out_folder, filename)

            from pathlib import Path

            if not Path(out_path).resolve().is_relative_to(Path(out_folder).resolve()):
                raise ValueError(f"Path non valido: {filename}")

            with open(out_path, "wb") as f:
                writer.write(f)

            created.append(out_path)

        return created

    def test_split_single_page_creates_one_file(self, tmp_path):
        pdf = tmp_path / "doc.pdf"
        pdf.write_bytes(_make_minimal_pdf(num_pages=3))
        out = tmp_path / "output"
        out.mkdir()

        created = self._do_split(str(pdf), [(0, 0)], str(out))
        assert len(created) == 1
        assert os.path.exists(created[0])
        reader = pypdf.PdfReader(created[0])
        assert len(reader.pages) == 1

    def test_split_all_pages_individually(self, tmp_path):
        pdf = tmp_path / "doc.pdf"
        pdf.write_bytes(_make_minimal_pdf(num_pages=3))
        out = tmp_path / "output"
        out.mkdir()

        chunks = [(0, 0), (1, 1), (2, 2)]
        created = self._do_split(str(pdf), chunks, str(out))
        assert len(created) == 3
        for f in created:
            reader = pypdf.PdfReader(f)
            assert len(reader.pages) == 1

    def test_split_range_preserves_page_count(self, tmp_path):
        pdf = tmp_path / "doc.pdf"
        pdf.write_bytes(_make_minimal_pdf(num_pages=5))
        out = tmp_path / "output"
        out.mkdir()

        created = self._do_split(str(pdf), [(1, 3)], str(out))
        assert len(created) == 1
        reader = pypdf.PdfReader(created[0])
        assert len(reader.pages) == 3

    def test_split_with_title_in_filename(self, tmp_path):
        pdf = tmp_path / "doc.pdf"
        pdf.write_bytes(_make_minimal_pdf(num_pages=3))
        out = tmp_path / "output"
        out.mkdir()

        created = self._do_split(str(pdf), [(0, 1, "Intro")], str(out))
        assert "Intro" in os.path.basename(created[0])

    def test_split_output_is_valid_pdf(self, tmp_path):
        pdf = tmp_path / "doc.pdf"
        pdf.write_bytes(_make_minimal_pdf(num_pages=2))
        out = tmp_path / "output"
        out.mkdir()

        created = self._do_split(str(pdf), [(0, 1)], str(out))
        content = open(created[0], "rb").read()
        assert content[:5] == b"%PDF-"

    def test_path_traversal_in_title_is_sanitized(self, tmp_path):
        pdf = tmp_path / "doc.pdf"
        pdf.write_bytes(_make_minimal_pdf(num_pages=2))
        out = tmp_path / "output"
        out.mkdir()

        # chunk_filename sanitizes titles, so path traversal characters are stripped
        created = self._do_split(str(pdf), [(0, 0, "../../evil")], str(out))
        from pathlib import Path

        for f in created:
            assert Path(f).resolve().is_relative_to(Path(out).resolve())

    def test_path_traversal_bypass_raises_valueerror(self, tmp_path):
        from unittest.mock import patch

        pdf = tmp_path / "doc.pdf"
        pdf.write_bytes(_make_minimal_pdf(num_pages=2))
        out = tmp_path / "output"
        out.mkdir()

        with (
            patch(f"{__name__}.chunk_filename", return_value="../../escaped.pdf"),
            pytest.raises(ValueError, match="Path non valido"),
        ):
            self._do_split(str(pdf), [(0, 0)], str(out))
