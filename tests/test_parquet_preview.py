"""Tests for parquet-preview pure functions."""

from pathlib import Path


def _load_functions():
    source = (Path(__file__).parent.parent / "parquet-preview" / "parquet_preview.py").read_text()
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
dtype_color = _ns["dtype_color"]
dtype_short = _ns["dtype_short"]


class TestFmtSize:
    def test_fmt_size_zero_bytes(self):
        assert fmt_size(0) == "0.0 B"

    def test_fmt_size_exact_kilobyte(self):
        assert fmt_size(1024) == "1.0 KB"

    def test_fmt_size_exact_megabyte(self):
        assert fmt_size(1024 * 1024) == "1.0 MB"

    def test_fmt_size_exact_gigabyte(self):
        assert fmt_size(1024**3) == "1.0 GB"

    def test_fmt_size_terabyte(self):
        assert fmt_size(1024**4) == "1.0 TB"

    def test_fmt_size_sub_kb_shows_b(self):
        result = fmt_size(512)
        assert "B" in result
        assert "K" not in result


class TestDtypeColor:
    def test_dtype_color_int64_returns_blue(self):
        assert dtype_color("int64") == "#0366d6"

    def test_dtype_color_float32_returns_purple(self):
        assert dtype_color("float32") == "#6f42c1"

    def test_dtype_color_double_returns_purple(self):
        assert dtype_color("double") == "#6f42c1"

    def test_dtype_color_timestamp_returns_orange(self):
        assert dtype_color("timestamp[us]") == "#e36209"

    def test_dtype_color_date32_returns_orange(self):
        assert dtype_color("date32") == "#e36209"

    def test_dtype_color_bool_returns_green(self):
        assert dtype_color("bool") == "#22863a"

    def test_dtype_color_string_returns_black(self):
        assert dtype_color("string") == "#24292e"

    def test_dtype_color_binary_returns_red(self):
        assert dtype_color("binary") == "#b31d28"

    def test_dtype_color_pure_list_returns_grey(self):
        # "list" senza altri tipi noti come substring → grigio
        assert dtype_color("list") == "#6a737d"

    def test_dtype_color_list_with_int_matches_int_first(self):
        # "list<item: int32>" contiene "int" come substring — matcha il colore blu
        # (comportamento attuale della funzione: prima corrispondenza vince)
        assert dtype_color("list<item: int32>") == "#0366d6"

    def test_dtype_color_unknown_returns_default(self):
        result = dtype_color("completely_unknown_type")
        assert result == "#24292e"

    def test_dtype_color_case_insensitive(self):
        # La funzione usa .lower() internamente
        assert dtype_color("INT64") == dtype_color("int64")


class TestDtypeShort:
    def test_dtype_short_timestamp_us_utc(self):
        result = dtype_short("timestamp[us, tz=UTC]")
        assert result == "timestamp"

    def test_dtype_short_timestamp_us(self):
        result = dtype_short("timestamp[us]")
        assert result == "timestamp"

    def test_dtype_short_timestamp_ns(self):
        result = dtype_short("timestamp[ns]")
        assert result == "timestamp"

    def test_dtype_short_large_string(self):
        result = dtype_short("large_string")
        assert result == "string"

    def test_dtype_short_large_binary(self):
        result = dtype_short("large_binary")
        assert result == "binary"

    def test_dtype_short_dictionary_categorical(self):
        result = dtype_short("dictionary<values=string, indices=int32, ordered=0>")
        assert result == "categorical"

    def test_dtype_short_simple_type_unchanged(self):
        assert dtype_short("int64") == "int64"
        assert dtype_short("float32") == "float32"
        assert dtype_short("bool") == "bool"

    def test_dtype_short_returns_string(self):
        result = dtype_short("int32")
        assert isinstance(result, str)
