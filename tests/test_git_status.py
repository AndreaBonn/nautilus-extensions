"""Tests for git-status pure functions."""

import os
import subprocess
import tempfile
from pathlib import Path


def _load_functions():
    source = (Path(__file__).parent.parent / "git-status" / "git_status.py").read_text()
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
is_git_repo = _ns["is_git_repo"]


def _git_available() -> bool:
    try:
        subprocess.run(["git", "--version"], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


def _init_git_repo(tmpdir: str) -> str:
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
    def test_run_git_version_returns_non_empty(self):
        if not _git_available():
            return
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_git(["--version"], cwd=tmpdir)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_run_git_invalid_args_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_git(["this-subcommand-does-not-exist"], cwd=tmpdir)
            assert result == ""

    def test_run_git_nonexistent_cwd_returns_empty(self):
        result = run_git(["status"], cwd="/nonexistent/path")
        assert result == ""

    def test_run_git_returns_string_type(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_git(["--version"], cwd=tmpdir)
            assert isinstance(result, str)

    def test_run_git_strips_output(self):
        # git --version non ha trailing newline dopo strip
        if not _git_available():
            return
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_git(["--version"], cwd=tmpdir)
            assert not result.endswith("\n")

    def test_run_git_in_repo_returns_toplevel(self):
        if not _git_available():
            return
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_git_repo(tmpdir)
            result = run_git(["rev-parse", "--show-toplevel"], cwd=tmpdir)
            assert result != ""


class TestIsGitRepo:
    def test_is_git_repo_returns_true_for_git_repo(self):
        if not _git_available():
            return
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_git_repo(tmpdir)
            assert is_git_repo(tmpdir) is True

    def test_is_git_repo_returns_false_for_plain_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            assert is_git_repo(tmpdir) is False

    def test_is_git_repo_returns_false_for_nonexistent_path(self):
        result = is_git_repo("/nonexistent/path")
        assert result is False

    def test_is_git_repo_returns_bool(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = is_git_repo(tmpdir)
            assert isinstance(result, bool)

    def test_is_git_repo_subdirectory_of_repo(self):
        if not _git_available():
            return
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_git_repo(tmpdir)
            subdir = os.path.join(tmpdir, "subdir")
            os.makedirs(subdir)
            # Anche una sottodirectory è dentro il repo
            assert is_git_repo(subdir) is True
