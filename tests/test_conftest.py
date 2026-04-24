"""Tests for conftest helper functions."""

from __future__ import annotations

from unittest.mock import patch

from conftest import ROOT, _git_available, _load_module_functions


class TestGitAvailable:
    def test_returns_true_when_git_works(self):
        assert _git_available() is True

    def test_returns_false_when_subprocess_raises(self):
        with patch("conftest.subprocess.run", side_effect=OSError("not found")):
            assert _git_available() is False

    def test_returns_false_when_file_not_found(self):
        with patch("conftest.subprocess.run", side_effect=FileNotFoundError("git")):
            assert _git_available() is False


class TestLoadModuleFunctions:
    def test_loads_requested_functions(self):
        ns = _load_module_functions(
            ROOT / "git-graph" / "git_graph.py",
            "git_graph",
            ["hex_to_rgb"],
        )
        assert "hex_to_rgb" in ns
        assert callable(ns["hex_to_rgb"])

    def test_missing_function_excluded_from_result(self):
        ns = _load_module_functions(
            ROOT / "git-graph" / "git_graph.py",
            "git_graph",
            ["nonexistent_function"],
        )
        assert "nonexistent_function" not in ns

    def test_skips_gi_imports(self):
        ns = _load_module_functions(
            ROOT / "git-graph" / "git_graph.py",
            "git_graph",
            ["hex_to_rgb"],
        )
        assert "gi" not in ns

    def test_stops_at_gtk_class(self):
        ns = _load_module_functions(
            ROOT / "git-graph" / "git_graph.py",
            "git_graph",
            ["GitGraphWindow"],
        )
        assert "GitGraphWindow" not in ns
