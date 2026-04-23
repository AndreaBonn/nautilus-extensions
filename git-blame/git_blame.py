"""
git_columns_nautilus.py — Git columns in Nautilus list view

Installation:
  cp git_columns_nautilus.py ~/.local/share/nautilus-python/extensions/
  nautilus -q && nautilus &
"""

from __future__ import annotations

import logging
import os
import subprocess
import threading
from urllib.parse import unquote, urlparse

import gi

gi.require_version("Nautilus", "4.0")
from gi.repository import GLib, GObject, Nautilus

MAX_CACHE_SIZE = 2000
_cache: dict[tuple[str, float], tuple[str, str, str]] = {}
_cache_lock = threading.Lock()


def _git_root(path: str) -> str | None:
    cwd = path if os.path.isdir(path) else os.path.dirname(path)
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=3,
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except FileNotFoundError:
        logging.warning("git executable not found")
        return None
    except subprocess.TimeoutExpired:
        logging.warning("git rev-parse timed out for %s", cwd)
        return None
    except OSError as e:
        logging.warning("_git_root failed for %s: %s", cwd, e)
        return None


def _git_info_file(filepath: str, root: str) -> tuple[str, str, str]:
    """Return (author, relative_date, message) for a single file."""
    rel = os.path.relpath(filepath, root)
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%an||%ar||%s", "--follow", "--", rel],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        out = r.stdout.strip()
        if not out:
            return ("", "", "")
        parts = out.split("||", 2)
        if len(parts) != 3:
            return ("", "", "")
        author, date, msg = parts
        return (author, date, msg[:60] + ("…" if len(msg) > 60 else ""))
    except FileNotFoundError:
        logging.warning("git executable not found")
        return ("", "", "")
    except subprocess.TimeoutExpired:
        logging.warning("git log timed out for %s", filepath)
        return ("", "", "")
    except OSError as e:
        logging.warning("_git_info_file failed for %s: %s", filepath, e)
        return ("", "", "")


def _git_info_dir(dirpath: str, root: str) -> tuple[str, str, str]:
    """
    Return (author, relative_date, message) for a directory,
    based on the last commit that touched any file inside it.
    """
    rel = os.path.relpath(dirpath, root)
    # Use "." for the root itself
    rel = "." if rel == "" else rel
    try:
        # Author + date + message of the last commit in the directory
        r = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%an||%ar||%s", "--", rel],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        out = r.stdout.strip()
        if not out:
            # Fallback: repo info (branch + latest global commit)
            r2 = subprocess.run(
                ["git", "log", "-1", "--pretty=format:%an||%ar||%s"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=5,
            )
            out = r2.stdout.strip()
        if not out:
            return ("", "", "")
        parts = out.split("||", 2)
        if len(parts) != 3:
            return ("", "", "")
        author, date, msg = parts
        return (author, date, msg[:60] + ("…" if len(msg) > 60 else ""))
    except FileNotFoundError:
        logging.warning("git executable not found")
        return ("", "", "")
    except subprocess.TimeoutExpired:
        logging.warning("git log timed out for %s", dirpath)
        return ("", "", "")
    except OSError as e:
        logging.warning("_git_info_dir failed for %s: %s", dirpath, e)
        return ("", "", "")


class GitColumnsExtension(GObject.GObject, Nautilus.ColumnProvider, Nautilus.InfoProvider):
    def __init__(self):
        super().__init__()

    def get_columns(self):
        return (
            Nautilus.Column(
                name="GitColumns::author",
                attribute="git_author",
                label="Git: Autore",
                description="Autore dell'ultimo commit",
            ),
            Nautilus.Column(
                name="GitColumns::date",
                attribute="git_date",
                label="Git: Data",
                description="Data dell'ultimo commit",
            ),
            Nautilus.Column(
                name="GitColumns::message",
                attribute="git_message",
                label="Git: Messaggio",
                description="Messaggio dell'ultimo commit",
            ),
        )

    def update_file_info(self, file_obj):
        if file_obj.get_uri_scheme() != "file":
            self._empty(file_obj)
            return

        filepath = unquote(urlparse(file_obj.get_uri()).path)

        try:
            mtime = os.path.getmtime(filepath)
        except OSError:
            mtime = 0

        cache_key = (filepath, mtime)

        with _cache_lock:
            if cache_key in _cache:
                a, d, m = _cache[cache_key]
                file_obj.add_string_attribute("git_author", a)
                file_obj.add_string_attribute("git_date", d)
                file_obj.add_string_attribute("git_message", m)
                return

        file_obj.add_string_attribute("git_author", "…")
        file_obj.add_string_attribute("git_date", "…")
        file_obj.add_string_attribute("git_message", "…")

        def worker(fp, fobj, ck):
            root = _git_root(fp)
            if not root:
                with _cache_lock:
                    _cache[ck] = ("", "", "")
                GLib.idle_add(_update, fobj, "", "", "")
                return

            if os.path.isdir(fp):
                result = _git_info_dir(fp, root)
            else:
                result = _git_info_file(fp, root)

            with _cache_lock:
                if len(_cache) >= MAX_CACHE_SIZE:
                    _cache.clear()
                _cache[ck] = result
            GLib.idle_add(_update, fobj, *result)

        threading.Thread(target=worker, args=(filepath, file_obj, cache_key), daemon=True).start()

    def _empty(self, file_obj):
        file_obj.add_string_attribute("git_author", "")
        file_obj.add_string_attribute("git_date", "")
        file_obj.add_string_attribute("git_message", "")


def _update(file_obj, author, date, msg):
    file_obj.add_string_attribute("git_author", author)
    file_obj.add_string_attribute("git_date", date)
    file_obj.add_string_attribute("git_message", msg)
    file_obj.invalidate_extension_info()
    return GLib.SOURCE_REMOVE
