"""Tests for duplicate-finder pure functions."""

import hashlib
import os
import tempfile


def _load_functions():
    import re
    from collections import defaultdict
    from pathlib import Path

    source = (Path(__file__).parent.parent / "duplicate-finder" / "duplicate_finder.py").read_text()

    namespace = {"os": os, "re": re, "hashlib": hashlib, "defaultdict": defaultdict}
    exec("from collections import defaultdict", namespace)
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
human_size = _ns["human_size"]
hash_of_file = _ns["hash_of_file"]
find_duplicates = _ns["find_duplicates"]


class TestHumanSize:
    def test_bytes(self):
        assert human_size(100) == "100.0 B"

    def test_kilobytes(self):
        assert human_size(1024) == "1.0 KB"

    def test_megabytes(self):
        assert human_size(1024 * 1024) == "1.0 MB"

    def test_zero(self):
        assert human_size(0) == "0.0 B"


class TestHashOfFile:
    def test_known_content(self):
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            f.write(b"hello world")
            path = f.name
        try:
            result = hash_of_file(path)
            expected = hashlib.sha256(b"hello world").hexdigest()
            assert result == expected
        finally:
            os.unlink(path)

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            path = f.name
        try:
            result = hash_of_file(path)
            expected = hashlib.sha256(b"").hexdigest()
            assert result == expected
        finally:
            os.unlink(path)

    def test_nonexistent_file_returns_empty(self):
        assert hash_of_file("/nonexistent/file/path.txt") == ""

    def test_uses_sha256_not_md5(self):
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            f.write(b"test")
            path = f.name
        try:
            result = hash_of_file(path)
            md5_result = hashlib.md5(b"test").hexdigest()
            sha256_result = hashlib.sha256(b"test").hexdigest()
            assert result == sha256_result
            assert result != md5_result
        finally:
            os.unlink(path)


class TestFindDuplicates:
    def test_finds_duplicate_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            content = b"duplicate content"
            for name in ["file1.txt", "file2.txt"]:
                with open(os.path.join(tmpdir, name), "wb") as f:
                    f.write(content)
            # Add a unique file
            with open(os.path.join(tmpdir, "unique.txt"), "wb") as f:
                f.write(b"unique content")

            dups = find_duplicates(tmpdir)
            # Should have exactly one group of duplicates
            assert len(dups) == 1
            # That group should have 2 files
            group = list(dups.values())[0]
            assert len(group) == 2

    def test_no_duplicates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i, name in enumerate(["a.txt", "b.txt", "c.txt"]):
                with open(os.path.join(tmpdir, name), "wb") as f:
                    f.write(f"content {i}".encode())

            dups = find_duplicates(tmpdir)
            assert len(dups) == 0

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dups = find_duplicates(tmpdir)
            assert len(dups) == 0
