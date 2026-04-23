"""
Shared fixtures for nautilus-extensions tests.

Tests cover only pure functions (no GTK/Nautilus dependencies).
Functions are imported by adding extension directories to sys.path
to avoid issues with the gi.require_version imports at module level.
"""

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _git_available() -> bool:
    """Check if git is available on the system."""
    try:
        subprocess.run(["git", "--version"], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


requires_git = pytest.mark.skipif(not _git_available(), reason="git is not available")


def _load_module_functions(module_path: Path, module_name: str, functions: list[str]) -> dict:
    """
    Load specific functions from a module file, skipping gi imports.
    Returns a dict {function_name: callable}.
    """
    source = module_path.read_text()

    # Build a minimal namespace with standard library modules
    namespace = {}
    exec("import os, re, csv, hashlib, json, logging, threading, subprocess", namespace)
    exec("from collections import defaultdict", namespace)
    exec("from urllib.parse import unquote, urlparse", namespace)
    exec("from pathlib import Path", namespace)

    # Execute only the lines before the first class definition or gi import
    lines = source.split("\n")
    safe_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("import gi") or stripped.startswith("from gi."):
            continue
        if stripped.startswith("gi.require_version"):
            continue
        if stripped.startswith("from gi.repository"):
            continue
        if stripped.startswith("class ") and "(Gtk." in stripped:
            break
        if stripped.startswith("class ") and "(GObject." in stripped:
            break
        safe_lines.append(line)

    exec("\n".join(safe_lines), namespace)

    return {name: namespace[name] for name in functions if name in namespace}
