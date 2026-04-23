"""Tests for csv-preview pure functions."""

import os
import tempfile
from pathlib import Path


def _load_functions():
    source = (Path(__file__).parent.parent / "csv-preview" / "csv_preview.py").read_text()
    namespace = {}
    exec("import os, csv, logging, threading", namespace)
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
detect_delimiter = _ns["detect_delimiter"]
read_csv_plain = _ns["read_csv_plain"]
read_csv_pandas = _ns.get("read_csv_pandas")
_fmt_size = _ns["_fmt_size"]

import pytest

requires_pandas = pytest.mark.skipif(read_csv_pandas is None, reason="pandas not available")


class TestFmtSize:
    def test_fmt_size_bytes_returns_b_unit(self):
        assert _fmt_size(500) == "500.0 B"

    def test_fmt_size_zero_returns_zero_b(self):
        assert _fmt_size(0) == "0.0 B"

    def test_fmt_size_exactly_1kb_returns_kb(self):
        assert _fmt_size(1024) == "1.0 KB"

    def test_fmt_size_exactly_1mb_returns_mb(self):
        assert _fmt_size(1024 * 1024) == "1.0 MB"

    def test_fmt_size_exactly_1gb_returns_gb(self):
        assert _fmt_size(1024**3) == "1.0 GB"

    def test_fmt_size_large_returns_tb(self):
        assert _fmt_size(1024**4) == "1.0 TB"

    def test_fmt_size_fractional_kb(self):
        assert _fmt_size(2048) == "2.0 KB"


class TestDetectDelimiter:
    def test_detect_delimiter_comma(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("a,b,c\n1,2,3\n")
            path = f.name
        try:
            assert detect_delimiter(path) == ","
        finally:
            os.unlink(path)

    def test_detect_delimiter_semicolon(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("a;b;c\n1;2;3\n")
            path = f.name
        try:
            assert detect_delimiter(path) == ";"
        finally:
            os.unlink(path)

    def test_detect_delimiter_tab(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("a\tb\tc\n1\t2\t3\n")
            path = f.name
        try:
            assert detect_delimiter(path) == "\t"
        finally:
            os.unlink(path)

    def test_detect_delimiter_pipe(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("a|b|c\n1|2|3\n")
            path = f.name
        try:
            assert detect_delimiter(path) == "|"
        finally:
            os.unlink(path)

    def test_detect_delimiter_unrecognised_falls_back_to_comma(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("no delimiters here\njust plain text\n")
            path = f.name
        try:
            result = detect_delimiter(path)
            assert isinstance(result, str)
            assert len(result) == 1
        finally:
            os.unlink(path)

    def test_detect_delimiter_nonexistent_file_raises(self):
        # detect_delimiter non gestisce FileNotFoundError — propaga l'eccezione
        import pytest

        with pytest.raises((FileNotFoundError, OSError)):
            detect_delimiter("/nonexistent/file.csv")


class TestReadCsvPlain:
    def test_read_csv_plain_returns_headers_and_rows(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("name,age,city\nAlice,30,Rome\nBob,25,Milan\n")
            path = f.name
        try:
            headers, rows, info = read_csv_plain(path, max_rows=100)
            assert headers == ["name", "age", "city"]
            assert len(rows) == 2
            assert rows[0] == ["Alice", "30", "Rome"]
        finally:
            os.unlink(path)

    def test_read_csv_plain_truncates_at_max_rows(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("col\n")
            for i in range(10):
                f.write(f"{i}\n")
            path = f.name
        try:
            headers, rows, info = read_csv_plain(path, max_rows=3)
            assert len(rows) == 3
            assert info["truncated"] is True
            assert info["total_rows"] == 10
        finally:
            os.unlink(path)

    def test_read_csv_plain_no_truncation_flag_when_within_limit(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("col\n1\n2\n")
            path = f.name
        try:
            _headers, _rows, info = read_csv_plain(path, max_rows=100)
            assert info["truncated"] is False
        finally:
            os.unlink(path)

    def test_read_csv_plain_info_contains_file_size(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("a,b\n1,2\n")
            path = f.name
        try:
            _headers, _rows, info = read_csv_plain(path, max_rows=100)
            assert "file_size" in info
            assert isinstance(info["file_size"], str)
        finally:
            os.unlink(path)

    def test_read_csv_plain_nonexistent_file_raises(self):
        # detect_delimiter viene chiamata prima dell'open — propaga FileNotFoundError
        import pytest

        with pytest.raises((FileNotFoundError, OSError)):
            read_csv_plain("/nonexistent/path.csv", max_rows=100)

    def test_read_csv_plain_empty_file_returns_empty(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            path = f.name
        try:
            headers, rows, info = read_csv_plain(path, max_rows=100)
            assert headers == []
            assert rows == []
        finally:
            os.unlink(path)

    def test_read_csv_plain_pads_short_rows(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("a,b,c\n1,2\n")
            path = f.name
        try:
            _headers, rows, _info = read_csv_plain(path, max_rows=100)
            assert rows[0] == ["1", "2", ""]
        finally:
            os.unlink(path)

    def test_read_csv_plain_info_contains_delimiter(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("a,b\n1,2\n")
            path = f.name
        try:
            _headers, _rows, info = read_csv_plain(path, max_rows=100)
            assert "delimiter" in info
        finally:
            os.unlink(path)


@requires_pandas
class TestReadCsvPandas:
    def test_returns_four_tuple(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("a,b,c\n1,2,3\n4,5,6\n")
            path = f.name
        try:
            result = read_csv_pandas(path, max_rows=100)
            assert len(result) == 4
        finally:
            os.unlink(path)

    def test_headers_match_columns(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("name,age,city\nAlice,30,Rome\n")
            path = f.name
        try:
            headers, _rows, _info, _df = read_csv_pandas(path, max_rows=100)
            assert headers == ["name", "age", "city"]
        finally:
            os.unlink(path)

    def test_rows_contain_values(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("x,y\n10,20\n30,40\n")
            path = f.name
        try:
            _headers, rows, _info, _df = read_csv_pandas(path, max_rows=100)
            assert len(rows) == 2
            assert rows[0] == ["10", "20"]
            assert rows[1] == ["30", "40"]
        finally:
            os.unlink(path)

    def test_truncates_at_max_rows(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("v\n" + "\n".join(str(i) for i in range(50)) + "\n")
            path = f.name
        try:
            _headers, rows, info, _df = read_csv_pandas(path, max_rows=10)
            assert len(rows) == 10
            assert info["truncated"] is True
            assert info["total_rows"] == 50
        finally:
            os.unlink(path)

    def test_info_contains_statistics_fields(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("a,b\n1,2\n3,\n")
            path = f.name
        try:
            _headers, _rows, info, _df = read_csv_pandas(path, max_rows=100)
            assert "null_counts" in info
            assert "dtypes" in info
            assert "numeric_cols" in info
        finally:
            os.unlink(path)

    def test_null_counts_detects_missing_values(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("a,b\n1,\n,2\n")
            path = f.name
        try:
            _headers, _rows, info, _df = read_csv_pandas(path, max_rows=100)
            assert info["null_counts"]["a"] == 1
            assert info["null_counts"]["b"] == 1
        finally:
            os.unlink(path)

    def test_nonexistent_file_returns_error(self):
        headers, rows, info, df = read_csv_pandas("/nonexistent/path.csv", max_rows=100)
        assert headers == []
        assert rows == []
        assert "error" in info
        assert df is None

    def test_returns_dataframe_as_fourth_element(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("x\n1\n2\n")
            path = f.name
        try:
            _headers, _rows, _info, df = read_csv_pandas(path, max_rows=100)
            assert df is not None
            assert len(df) == 2
        finally:
            os.unlink(path)
