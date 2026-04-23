"""Tests for json-preview pure functions."""

import gzip
import json
import os
import tempfile
from pathlib import Path


def _load_functions():
    source = (Path(__file__).parent.parent / "json-preview" / "json_preview.py").read_text()
    namespace = {}
    exec("import os, json, gzip, collections, threading", namespace)
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
json_type = _ns["json_type"]
type_color = _ns["type_color"]
infer_schema = _ns["infer_schema"]
read_json_file = _ns["read_json_file"]
read_jsonl_file = _ns["read_jsonl_file"]
is_gzipped = _ns["is_gzipped"]


class TestFmtSize:
    def test_fmt_size_bytes_unit(self):
        assert fmt_size(512) == "512.0 B"

    def test_fmt_size_zero(self):
        assert fmt_size(0) == "0.0 B"

    def test_fmt_size_kilobytes(self):
        assert fmt_size(1024) == "1.0 KB"

    def test_fmt_size_megabytes(self):
        assert fmt_size(1024 * 1024) == "1.0 MB"

    def test_fmt_size_gigabytes(self):
        assert fmt_size(1024**3) == "1.0 GB"

    def test_fmt_size_terabytes(self):
        assert fmt_size(1024**4) == "1.0 TB"


class TestJsonType:
    def test_json_type_none_returns_null(self):
        assert json_type(None) == "null"

    def test_json_type_bool_true_returns_boolean(self):
        assert json_type(True) == "boolean"

    def test_json_type_bool_false_returns_boolean(self):
        assert json_type(False) == "boolean"

    def test_json_type_integer_returns_number(self):
        assert json_type(42) == "number"

    def test_json_type_float_returns_number(self):
        assert json_type(3.14) == "number"

    def test_json_type_string_returns_string(self):
        assert json_type("hello") == "string"

    def test_json_type_empty_string_returns_string(self):
        assert json_type("") == "string"

    def test_json_type_dict_returns_object(self):
        assert json_type({"a": 1}) == "object"

    def test_json_type_empty_dict_returns_object(self):
        assert json_type({}) == "object"

    def test_json_type_list_returns_array(self):
        assert json_type([1, 2]) == "array"

    def test_json_type_empty_list_returns_array(self):
        assert json_type([]) == "array"

    def test_json_type_bool_is_not_number(self):
        # bool è subclass di int — json_type deve riconoscerlo prima come boolean
        assert json_type(True) != "number"


class TestTypeColor:
    def test_type_color_string_returns_green(self):
        assert type_color("string") == "#22863a"

    def test_type_color_number_returns_blue(self):
        assert type_color("number") == "#0366d6"

    def test_type_color_boolean_returns_orange(self):
        assert type_color("boolean") == "#e36209"

    def test_type_color_null_returns_red(self):
        assert type_color("null") == "#b31d28"

    def test_type_color_object_returns_purple(self):
        assert type_color("object") == "#6f42c1"

    def test_type_color_unknown_returns_default(self):
        result = type_color("unknown_type")
        assert isinstance(result, str)
        assert result.startswith("#")


class TestInferSchema:
    def test_infer_schema_string_value(self):
        schema = infer_schema("hello")
        assert schema["type"] == "string"

    def test_infer_schema_integer_value(self):
        schema = infer_schema(42)
        assert schema["type"] == "number"

    def test_infer_schema_null_value(self):
        schema = infer_schema(None)
        assert schema["type"] == "null"

    def test_infer_schema_object_has_children(self):
        schema = infer_schema({"name": "Alice", "age": 30})
        assert schema["type"] == "object"
        assert "children" in schema
        assert "name" in schema["children"]
        assert "age" in schema["children"]

    def test_infer_schema_array_has_length_and_item_schema(self):
        schema = infer_schema([1, 2, 3])
        assert schema["type"] == "array"
        assert schema["length"] == 3
        assert "item_schema" in schema

    def test_infer_schema_empty_object_no_children(self):
        schema = infer_schema({})
        assert schema["type"] == "object"
        assert "children" not in schema

    def test_infer_schema_empty_array_no_item_schema(self):
        schema = infer_schema([])
        assert schema["type"] == "array"
        assert "item_schema" not in schema

    def test_infer_schema_respects_max_depth(self):
        nested = {"a": {"b": {"c": {"d": "deep"}}}}
        schema = infer_schema(nested, depth=0, max_depth=1)
        # Al depth=1 non dovrebbe scendere oltre
        assert schema["type"] == "object"
        assert "children" in schema
        # Il figlio "a" raggiunge max_depth, non ha children
        assert "children" not in schema["children"]["a"]

    def test_infer_schema_nested_children_types(self):
        schema = infer_schema({"name": "Bob", "score": 9.5, "active": True})
        assert schema["children"]["name"]["type"] == "string"
        assert schema["children"]["score"]["type"] == "number"
        assert schema["children"]["active"]["type"] == "boolean"


class TestReadJsonFile:
    def test_read_json_file_object_returns_data(self):
        data = {"key": "value", "num": 42}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            result = read_json_file(path)
            assert result["data"] == data
            assert result["root_type"] == "object"
            assert result["num_keys"] == 2
        finally:
            os.unlink(path)

    def test_read_json_file_array_has_num_items(self):
        data = [1, 2, 3]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            result = read_json_file(path)
            assert result["root_type"] == "array"
            assert result["num_items"] == 3
        finally:
            os.unlink(path)

    def test_read_json_file_invalid_json_returns_error(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{not valid json}")
            path = f.name
        try:
            result = read_json_file(path)
            assert "error" in result
        finally:
            os.unlink(path)

    def test_read_json_file_nonexistent_raises(self):
        # os.path.getsize è chiamato prima dell'apertura — propaga FileNotFoundError
        import pytest

        with pytest.raises((FileNotFoundError, OSError)):
            read_json_file("/nonexistent/file.json")

    def test_read_json_file_contains_schema(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"a": 1}, f)
            path = f.name
        try:
            result = read_json_file(path)
            assert "schema" in result
        finally:
            os.unlink(path)

    def test_read_json_file_contains_file_size(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"x": 1}, f)
            path = f.name
        try:
            result = read_json_file(path)
            assert "file_size" in result
            assert isinstance(result["file_size"], str)
        finally:
            os.unlink(path)


class TestReadJsonlFile:
    def test_read_jsonl_file_reads_all_lines(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"a": 1}\n{"a": 2}\n{"a": 3}\n')
            path = f.name
        try:
            result = read_jsonl_file(path)
            assert result["total_lines"] == 3
            assert len(result["preview_rows"]) == 3
        finally:
            os.unlink(path)

    def test_read_jsonl_file_skips_blank_lines(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"a": 1}\n\n{"a": 2}\n')
            path = f.name
        try:
            result = read_jsonl_file(path)
            assert result["total_lines"] == 2
        finally:
            os.unlink(path)

    def test_read_jsonl_file_counts_parse_errors(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"ok": 1}\nnot json\n{"ok": 2}\n')
            path = f.name
        try:
            result = read_jsonl_file(path)
            assert result["parse_errors"] == 1
        finally:
            os.unlink(path)

    def test_read_jsonl_file_nonexistent_raises(self):
        # os.path.getsize è chiamato prima dell'apertura — propaga FileNotFoundError
        import pytest

        with pytest.raises((FileNotFoundError, OSError)):
            read_jsonl_file("/nonexistent/file.jsonl")

    def test_read_jsonl_file_empty_file_returns_zero_lines(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            result = read_jsonl_file(path)
            assert result["total_lines"] == 0
        finally:
            os.unlink(path)


class TestIsGzipped:
    def test_is_gzipped_plain_file_returns_false(self):
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(b"plain text content")
            path = f.name
        try:
            assert is_gzipped(path) is False
        finally:
            os.unlink(path)

    def test_is_gzipped_gzip_file_returns_true(self):
        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as f:
            path = f.name
        try:
            with gzip.open(path, "wt") as gz:
                gz.write('{"a": 1}')
            assert is_gzipped(path) is True
        finally:
            os.unlink(path)

    def test_is_gzipped_nonexistent_returns_false(self):
        assert is_gzipped("/nonexistent/file.gz") is False

    def test_is_gzipped_empty_file_returns_false(self):
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            path = f.name
        try:
            assert is_gzipped(path) is False
        finally:
            os.unlink(path)
