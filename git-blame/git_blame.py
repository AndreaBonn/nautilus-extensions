"""
git_columns_nautilus.py — Colonne Git nella vista lista di Nautilus

Installazione:
  cp git_columns_nautilus.py ~/.local/share/nautilus-python/extensions/
  nautilus -q && nautilus &
"""

import os
import subprocess
import threading
from urllib.parse import unquote, urlparse

import gi

gi.require_version("Nautilus", "4.0")
from gi.repository import GLib, GObject, Nautilus

MAX_CACHE_SIZE = 2000
_cache = {}
_cache_lock = threading.Lock()


def _git_root(path):
    cwd = path if os.path.isdir(path) else os.path.dirname(path)
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd, capture_output=True, text=True, timeout=3
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def _git_info_file(filepath, root):
    """Info per un file: autore, data relativa, messaggio."""
    rel = os.path.relpath(filepath, root)
    try:
        r = subprocess.run(
            ["git", "log", "-1",
             "--pretty=format:%an||%ar||%s",
             "--follow", "--", rel],
            cwd=root, capture_output=True, text=True, timeout=5
        )
        out = r.stdout.strip()
        if not out:
            return ("", "", "")
        parts = out.split("||", 2)
        if len(parts) != 3:
            return ("", "", "")
        author, date, msg = parts
        return (author, date, msg[:60] + ("…" if len(msg) > 60 else ""))
    except Exception:
        return ("", "", "")


def _git_info_dir(dirpath, root):
    """
    Info per una cartella: trova l'ultimo commit che ha toccato
    qualsiasi file dentro quella cartella.
    """
    rel = os.path.relpath(dirpath, root)
    # Per la root stessa usa "."
    rel = "." if rel == "" else rel
    try:
        # Autore + data + messaggio dell'ultimo commit nella cartella
        r = subprocess.run(
            ["git", "log", "-1",
             "--pretty=format:%an||%ar||%s",
             "--", rel],
            cwd=root, capture_output=True, text=True, timeout=5
        )
        out = r.stdout.strip()
        if not out:
            # Fallback: info del repo (branch + ultimo commit globale)
            r2 = subprocess.run(
                ["git", "log", "-1", "--pretty=format:%an||%ar||%s"],
                cwd=root, capture_output=True, text=True, timeout=5
            )
            out = r2.stdout.strip()
        if not out:
            return ("", "", "")
        parts = out.split("||", 2)
        if len(parts) != 3:
            return ("", "", "")
        author, date, msg = parts
        return (author, date, msg[:60] + ("…" if len(msg) > 60 else ""))
    except Exception:
        return ("", "", "")


class GitColumnsExtension(GObject.GObject,
                          Nautilus.ColumnProvider,
                          Nautilus.InfoProvider):

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

        with _cache_lock:
            if filepath in _cache:
                a, d, m = _cache[filepath]
                file_obj.add_string_attribute("git_author",  a)
                file_obj.add_string_attribute("git_date",    d)
                file_obj.add_string_attribute("git_message", m)
                return

        file_obj.add_string_attribute("git_author",  "…")
        file_obj.add_string_attribute("git_date",    "…")
        file_obj.add_string_attribute("git_message", "…")

        def worker(fp, fobj):
            root = _git_root(fp)
            if not root:
                with _cache_lock:
                    _cache[fp] = ("", "", "")
                GLib.idle_add(_update, fobj, "", "", "")
                return

            if os.path.isdir(fp):
                result = _git_info_dir(fp, root)
            else:
                result = _git_info_file(fp, root)

            with _cache_lock:
                if len(_cache) >= MAX_CACHE_SIZE:
                    _cache.clear()
                _cache[fp] = result
            GLib.idle_add(_update, fobj, *result)

        threading.Thread(target=worker, args=(filepath, file_obj),
                         daemon=True).start()

    def _empty(self, file_obj):
        file_obj.add_string_attribute("git_author",  "")
        file_obj.add_string_attribute("git_date",    "")
        file_obj.add_string_attribute("git_message", "")


def _update(file_obj, author, date, msg):
    file_obj.add_string_attribute("git_author",  author)
    file_obj.add_string_attribute("git_date",    date)
    file_obj.add_string_attribute("git_message", msg)
    file_obj.invalidate_extension_info()
    return GLib.SOURCE_REMOVE
