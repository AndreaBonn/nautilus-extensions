"""Tests for parquet-preview pure functions."""

from pathlib import Path

import pytest


def _load_functions():
    source = (Path(__file__).parent.parent / "parquet-preview" / "parquet_preview.py").read_text()
    namespace = {}
    exec("import os, logging, threading", namespace)
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
read_parquet = _ns["read_parquet"]


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


# ── Fixtures ─────────────────────────────────────────────────────────────────

import importlib.util

HAS_PYARROW = importlib.util.find_spec("pyarrow") is not None

requires_pyarrow = pytest.mark.skipif(not HAS_PYARROW, reason="pyarrow not installed")


@pytest.fixture()
def simple_parquet(tmp_path):
    """Write a minimal Parquet file with int, float, and string columns."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = pa.table(
        {
            "id": pa.array([1, 2, 3], type=pa.int64()),
            "score": pa.array([1.1, 2.2, 3.3], type=pa.float64()),
            "label": pa.array(["a", "b", "c"], type=pa.string()),
        }
    )
    path = tmp_path / "simple.parquet"
    pq.write_table(table, str(path))
    return str(path)


@pytest.fixture()
def empty_parquet(tmp_path):
    """Write a Parquet file with schema but zero rows."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = pa.table({"id": pa.array([], type=pa.int64())})
    path = tmp_path / "empty.parquet"
    pq.write_table(table, str(path))
    return str(path)


@pytest.fixture()
def nullable_parquet(tmp_path):
    """Write a Parquet file that contains null values."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = pa.table(
        {
            "value": pa.array([1, None, 3], type=pa.int64()),
            "name": pa.array(["x", None, "z"], type=pa.string()),
        }
    )
    path = tmp_path / "nullable.parquet"
    pq.write_table(table, str(path))
    return str(path)


# ── Tests ─────────────────────────────────────────────────────────────────────


@requires_pyarrow
class TestReadParquet:
    def test_returns_dict(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)

        assert isinstance(result, dict)

    def test_no_error_key_on_valid_file(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)

        assert "error" not in result

    def test_num_rows_matches_table(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)

        assert result["num_rows"] == 3

    def test_num_columns_matches_table(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)

        assert result["num_columns"] == 3

    def test_num_row_groups_is_positive_integer(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)

        assert isinstance(result["num_row_groups"], int)
        assert result["num_row_groups"] >= 1

    def test_columns_list_has_correct_length(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)

        assert len(result["columns"]) == 3

    def test_columns_contain_required_keys(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)
        required = {"index", "name", "type", "nullable"}

        for col in result["columns"]:
            assert required.issubset(col.keys()), f"Missing keys in column: {col}"

    def test_column_names_match_schema(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)
        names = [c["name"] for c in result["columns"]]

        assert names == ["id", "score", "label"]

    def test_column_types_are_strings(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)

        for col in result["columns"]:
            assert isinstance(col["type"], str)

    def test_int_column_type_contains_int(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)
        id_col = next(c for c in result["columns"] if c["name"] == "id")

        assert "int" in id_col["type"].lower()

    def test_file_size_is_formatted_string(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)

        assert isinstance(result["file_size"], str)
        # Must contain a unit suffix
        assert any(unit in result["file_size"] for unit in ["B", "KB", "MB", "GB", "TB"])

    def test_df_preview_has_correct_row_count(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)

        assert len(result["df_preview"]) == 3

    def test_df_preview_has_correct_columns(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)
        columns = list(result["df_preview"].columns)

        assert columns == ["id", "score", "label"]

    def test_max_rows_limits_preview(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=1)

        assert len(result["df_preview"]) == 1

    def test_numeric_cols_contains_numeric_columns(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)

        assert "id" in result["numeric_cols"]
        assert "score" in result["numeric_cols"]

    def test_non_numeric_col_excluded_from_numeric_cols(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)

        assert "label" not in result["numeric_cols"]

    def test_null_counts_key_present(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)

        assert "null_counts" in result
        assert isinstance(result["null_counts"], dict)

    def test_null_counts_zero_for_clean_data(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)

        for col, count in result["null_counts"].items():
            assert count == 0, f"Unexpected nulls in column {col!r}"

    def test_null_counts_detects_nulls(self, nullable_parquet):
        result = read_parquet(nullable_parquet, max_rows=100)

        assert result["null_counts"]["value"] == 1
        assert result["null_counts"]["name"] == 1

    def test_empty_table_returns_zero_rows(self, empty_parquet):
        result = read_parquet(empty_parquet, max_rows=100)

        assert "error" not in result
        assert result["num_rows"] == 0
        assert len(result["df_preview"]) == 0

    def test_empty_table_schema_still_returned(self, empty_parquet):
        result = read_parquet(empty_parquet, max_rows=100)

        assert len(result["columns"]) == 1
        assert result["columns"][0]["name"] == "id"

    def test_nonexistent_file_returns_error_key(self, tmp_path):
        missing = str(tmp_path / "does_not_exist.parquet")

        result = read_parquet(missing, max_rows=100)

        assert "error" in result
        assert isinstance(result["error"], str)

    def test_nonexistent_file_does_not_raise(self, tmp_path):
        missing = str(tmp_path / "no_file.parquet")

        try:
            result = read_parquet(missing, max_rows=100)
        except Exception as exc:  # noqa: BLE001
            pytest.fail(f"read_parquet raised unexpectedly: {exc}")

        assert "error" in result

    def test_compressed_size_is_formatted_string(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)

        assert isinstance(result["compressed_size"], str)

    def test_uncompressed_size_is_formatted_string(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)

        assert isinstance(result["uncompressed_size"], str)

    def test_row_groups_is_list(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)

        assert isinstance(result["row_groups"], list)

    def test_row_groups_each_have_required_keys(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)
        required = {"index", "num_rows", "compressed", "uncompressed"}

        for rg in result["row_groups"]:
            assert required.issubset(rg.keys()), f"Missing keys in row group: {rg}"

    def test_custom_meta_is_dict(self, simple_parquet):
        result = read_parquet(simple_parquet, max_rows=100)

        assert isinstance(result["custom_meta"], dict)
