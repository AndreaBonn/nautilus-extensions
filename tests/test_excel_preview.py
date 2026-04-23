"""Tests for excel-preview pure functions."""

from pathlib import Path


def _load_functions():
    source = (Path(__file__).parent.parent / "excel-preview" / "excel_preview.py").read_text()
    namespace = {}
    exec("import os, threading", namespace)
    lines = source.split("\n")
    safe_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("import gi", "from gi.", "gi.require_version")):
            continue
        if stripped.startswith("class ") and ("Gtk." in stripped or "GObject." in stripped):
            break
        safe_lines.append(line)
    exec("\n".join(safe_lines), namespace)
    return namespace


_ns = _load_functions()
fmt_size = _ns["fmt_size"]


class TestFmtSize:
    def test_fmt_size_bytes_returns_b_unit(self):
        assert fmt_size(0) == "0.0 B"

    def test_fmt_size_999_bytes(self):
        assert fmt_size(999) == "999.0 B"

    def test_fmt_size_exactly_1kb(self):
        assert fmt_size(1024) == "1.0 KB"

    def test_fmt_size_exactly_1mb(self):
        assert fmt_size(1024 * 1024) == "1.0 MB"

    def test_fmt_size_exactly_1gb(self):
        assert fmt_size(1024**3) == "1.0 GB"

    def test_fmt_size_large_terabytes(self):
        assert fmt_size(1024**4) == "1.0 TB"

    def test_fmt_size_2kb(self):
        assert fmt_size(2048) == "2.0 KB"

    def test_fmt_size_1_5mb(self):
        result = fmt_size(int(1.5 * 1024 * 1024))
        assert "MB" in result
        assert "1.5" in result
