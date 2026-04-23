"""Tests for git-diff pure functions."""

import os
import subprocess
import tempfile
from pathlib import Path

from conftest import requires_git


def _load_functions():
    source = (Path(__file__).parent.parent / "git-diff" / "git_diff.py").read_text()
    namespace = {}
    exec("import os, subprocess, threading", namespace)
    exec("from urllib.parse import unquote, urlparse", namespace)
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
run_git = _ns["run_git"]
parse_diff = _ns["parse_diff"]


def _init_git_repo(tmpdir: str) -> str:
    """Inizializza un repo git minimale nel tmpdir."""
    subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmpdir,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmpdir,
        capture_output=True,
    )
    return tmpdir


class TestRunGit:
    @requires_git
    def test_run_git_valid_command_returns_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_git_repo(tmpdir)
            result = run_git(["rev-parse", "--show-toplevel"], cwd=tmpdir)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_run_git_invalid_command_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_git(["this-command-does-not-exist"], cwd=tmpdir)
            assert result == ""

    def test_run_git_nonexistent_cwd_returns_empty(self):
        result = run_git(["status"], cwd="/nonexistent/path")
        assert result == ""

    def test_run_git_returns_string(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_git(["--version"], cwd=tmpdir)
            assert isinstance(result, str)

    def test_run_git_outside_repo_returns_empty_for_log(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_git(["log", "--oneline"], cwd=tmpdir)
            assert result == ""


class TestParseDiff:
    def test_parse_diff_empty_returns_empty_list(self):
        assert parse_diff("") == []

    def test_parse_diff_single_hunk_returns_one_hunk(self):
        raw = "@@ -1,3 +1,4 @@\n context\n+added line\n context2\n"
        hunks = parse_diff(raw)
        assert len(hunks) == 1

    def test_parse_diff_hunk_has_header(self):
        raw = "@@ -1,3 +1,4 @@ function_name\n context\n+added\n"
        hunks = parse_diff(raw)
        assert "@@ -1,3 +1,4 @@" in hunks[0]["header"]

    def test_parse_diff_added_line_has_add_type(self):
        raw = "@@ -1,1 +1,2 @@\n context\n+added line\n"
        hunks = parse_diff(raw)
        types = [line[0] for line in hunks[0]["lines"]]
        assert "add" in types

    def test_parse_diff_removed_line_has_del_type(self):
        raw = "@@ -1,2 +1,1 @@\n context\n-removed line\n"
        hunks = parse_diff(raw)
        types = [line[0] for line in hunks[0]["lines"]]
        assert "del" in types

    def test_parse_diff_context_line_has_ctx_type(self):
        raw = "@@ -1,1 +1,1 @@\n context line\n"
        hunks = parse_diff(raw)
        types = [line[0] for line in hunks[0]["lines"]]
        assert "ctx" in types

    def test_parse_diff_multiple_hunks(self):
        raw = (
            "@@ -1,2 +1,2 @@ func1\n ctx\n-old\n+new\n"
            "@@ -10,2 +10,2 @@ func2\n ctx2\n-old2\n+new2\n"
        )
        hunks = parse_diff(raw)
        assert len(hunks) == 2

    def test_parse_diff_line_numbers_tracked(self):
        raw = "@@ -5,3 +5,4 @@\n context\n+added\n context2\n"
        hunks = parse_diff(raw)
        lines = hunks[0]["lines"]
        # Ogni riga ha (type, old_lineno, new_lineno, text)
        assert len(lines[0]) == 4

    def test_parse_diff_added_line_no_old_lineno(self):
        raw = "@@ -1,1 +1,2 @@\n ctx\n+new line\n"
        hunks = parse_diff(raw)
        add_lines = [ln for ln in hunks[0]["lines"] if ln[0] == "add"]
        assert add_lines[0][1] is None  # old_line = None per add

    def test_parse_diff_removed_line_no_new_lineno(self):
        raw = "@@ -1,2 +1,1 @@\n ctx\n-old line\n"
        hunks = parse_diff(raw)
        del_lines = [ln for ln in hunks[0]["lines"] if ln[0] == "del"]
        assert del_lines[0][2] is None  # new_line = None per del

    def test_parse_diff_skips_file_header_lines(self):
        raw = "--- a/file.py\n+++ b/file.py\n@@ -1,1 +1,2 @@\n ctx\n+new\n"
        hunks = parse_diff(raw)
        assert len(hunks) == 1
        # Le righe --- e +++ non devono essere nel content
        all_texts = [ln[3] for ln in hunks[0]["lines"]]
        assert not any("--- a/" in t or "+++ b/" in t for t in all_texts)

    @requires_git
    def test_parse_diff_real_git_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_git_repo(tmpdir)
            filepath = os.path.join(tmpdir, "test.py")
            with open(filepath, "w") as f:
                f.write("line1\nline2\n")
            subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "init"],
                cwd=tmpdir,
                capture_output=True,
            )
            with open(filepath, "w") as f:
                f.write("line1\nline2 modified\nline3\n")
            raw = subprocess.run(
                ["git", "diff", "--", "test.py"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            ).stdout
            hunks = parse_diff(raw)
            assert len(hunks) >= 1
