"""Tests for git-blame pure functions."""

import os
import subprocess
import tempfile
from pathlib import Path


def _load_functions():
    source = (Path(__file__).parent.parent / "git-blame" / "git_blame.py").read_text()
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
_git_root = _ns["_git_root"]
_git_info_file = _ns["_git_info_file"]
_git_info_dir = _ns["_git_info_dir"]


def _git_available() -> bool:
    try:
        subprocess.run(["git", "--version"], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


def _init_git_repo_with_commit(tmpdir: str) -> str:
    """Inizializza un repo git con un commit iniziale."""
    subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmpdir,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test Author"],
        cwd=tmpdir,
        capture_output=True,
    )
    filepath = os.path.join(tmpdir, "file.py")
    with open(filepath, "w") as f:
        f.write("print('hello')\n")
    subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial commit"],
        cwd=tmpdir,
        capture_output=True,
    )
    return tmpdir


class TestGitRoot:
    def test_git_root_returns_path_inside_repo(self):
        if not _git_available():
            return
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_git_repo_with_commit(tmpdir)
            result = _git_root(tmpdir)
            assert result is not None
            assert isinstance(result, str)

    def test_git_root_returns_none_outside_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _git_root(tmpdir)
            assert result is None

    def test_git_root_from_file_path(self):
        if not _git_available():
            return
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_git_repo_with_commit(tmpdir)
            filepath = os.path.join(tmpdir, "file.py")
            result = _git_root(filepath)
            assert result is not None

    def test_git_root_nonexistent_path_returns_none(self):
        result = _git_root("/nonexistent/path/file.py")
        assert result is None

    def test_git_root_from_subdir(self):
        if not _git_available():
            return
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_git_repo_with_commit(tmpdir)
            subdir = os.path.join(tmpdir, "sub")
            os.makedirs(subdir)
            result = _git_root(subdir)
            assert result is not None


class TestGitInfoFile:
    def test_git_info_file_returns_tuple_of_three(self):
        if not _git_available():
            return
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_git_repo_with_commit(tmpdir)
            filepath = os.path.join(tmpdir, "file.py")
            result = _git_info_file(filepath, root=tmpdir)
            assert isinstance(result, tuple)
            assert len(result) == 3

    def test_git_info_file_returns_author_name(self):
        if not _git_available():
            return
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_git_repo_with_commit(tmpdir)
            filepath = os.path.join(tmpdir, "file.py")
            author, date, msg = _git_info_file(filepath, root=tmpdir)
            assert author == "Test Author"

    def test_git_info_file_returns_commit_message(self):
        if not _git_available():
            return
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_git_repo_with_commit(tmpdir)
            filepath = os.path.join(tmpdir, "file.py")
            _author, _date, msg = _git_info_file(filepath, root=tmpdir)
            assert "initial commit" in msg

    def test_git_info_file_untracked_file_returns_empty_tuple(self):
        if not _git_available():
            return
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_git_repo_with_commit(tmpdir)
            untracked = os.path.join(tmpdir, "untracked.py")
            with open(untracked, "w") as f:
                f.write("# new file\n")
            result = _git_info_file(untracked, root=tmpdir)
            assert result == ("", "", "")

    def test_git_info_file_nonexistent_file_returns_empty_tuple(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _git_info_file("/nonexistent/file.py", root=tmpdir)
            assert result == ("", "", "")

    def test_git_info_file_truncates_long_message(self):
        if not _git_available():
            return
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "t@t.com"],
                cwd=tmpdir,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "T"],
                cwd=tmpdir,
                capture_output=True,
            )
            filepath = os.path.join(tmpdir, "f.py")
            with open(filepath, "w") as f:
                f.write("x\n")
            subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
            long_msg = "a" * 100
            subprocess.run(
                ["git", "commit", "-m", long_msg],
                cwd=tmpdir,
                capture_output=True,
            )
            _author, _date, msg = _git_info_file(filepath, root=tmpdir)
            assert len(msg) <= 63  # 60 + "…"


class TestGitInfoDir:
    def test_git_info_dir_returns_tuple_of_three(self):
        if not _git_available():
            return
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_git_repo_with_commit(tmpdir)
            result = _git_info_dir(tmpdir, root=tmpdir)
            assert isinstance(result, tuple)
            assert len(result) == 3

    def test_git_info_dir_returns_author(self):
        if not _git_available():
            return
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_git_repo_with_commit(tmpdir)
            author, _date, _msg = _git_info_dir(tmpdir, root=tmpdir)
            assert author == "Test Author"

    def test_git_info_dir_returns_commit_message(self):
        if not _git_available():
            return
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_git_repo_with_commit(tmpdir)
            _author, _date, msg = _git_info_dir(tmpdir, root=tmpdir)
            assert "initial commit" in msg

    def test_git_info_dir_empty_repo_returns_empty_tuple(self):
        if not _git_available():
            return
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "t@t.com"],
                cwd=tmpdir,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "T"],
                cwd=tmpdir,
                capture_output=True,
            )
            result = _git_info_dir(tmpdir, root=tmpdir)
            assert result == ("", "", "")

    def test_git_info_dir_nonexistent_path_returns_empty_tuple(self):
        result = _git_info_dir("/nonexistent/dir", root="/nonexistent")
        assert result == ("", "", "")
