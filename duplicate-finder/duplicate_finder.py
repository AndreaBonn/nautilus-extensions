"""
duplicate-finder.py — Nautilus extension to find duplicate files
"""

import hashlib
import logging
import os
import subprocess
import threading
from collections import defaultdict

import gi

gi.require_version("Nautilus", "4.0")
gi.require_version("Gtk", "4.0")
gi.require_version("GLib", "2.0")

from gi.repository import GLib, GObject, Gtk, Nautilus, Pango

CSS = b"""
.dup-header {
    background-color: #f6f8fa;
    border-bottom: 1px solid #e1e4e8;
    padding: 10px 16px;
}
.dup-title {
    font-size: 16px;
    font-weight: bold;
    color: #24292e;
}
.dup-subtitle {
    font-size: 12px;
    color: #6a737d;
}
.dup-hint {
    font-size: 11px;
    color: #6a737d;
    font-style: italic;
}
"""


def human_size(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def hash_of_file(path: str, chunk_size: int = 65536) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
    except (OSError, PermissionError) as e:
        logging.warning("Skipped unreadable file: %s — %s", path, e)
        return ""
    return h.hexdigest()


MAX_SCAN_FILES = 100_000


def find_duplicates(root: str, progress_cb=None) -> dict:
    by_size = defaultdict(list)
    file_count = 0
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            file_count += 1
            if file_count > MAX_SCAN_FILES:
                logging.warning("Scan limit reached: %d files, stopping", MAX_SCAN_FILES)
                break
            fpath = os.path.join(dirpath, fname)
            try:
                size = os.path.getsize(fpath)
                if size > 0:
                    by_size[size].append(fpath)
            except OSError as e:
                logging.warning("File skipped during scan: %s", e)
        if file_count > MAX_SCAN_FILES:
            break

    candidates = [paths for paths in by_size.values() if len(paths) > 1]
    total = sum(len(g) for g in candidates)
    done = 0
    by_hash = defaultdict(list)

    for group in candidates:
        for fpath in group:
            digest = hash_of_file(fpath)
            if digest:
                by_hash[digest].append(fpath)
            done += 1
            if progress_cb and total > 0:
                progress_cb(done, total)

    return {h: paths for h, paths in by_hash.items() if len(paths) > 1}


# ---------------------------------------------------------------------------
# Finestra principale
# ---------------------------------------------------------------------------


class DupFinderWindow(Gtk.Window):
    def __init__(self, folder_path: str):
        super().__init__(title="Trova duplicati")
        self.set_default_size(780, 600)
        self._folder = folder_path
        self._duplicates = {}

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self._build_ui()
        self._start_scan()

    def _build_ui(self):
        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(root_box)

        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        header.add_css_class("dup-header")
        root_box.append(header)

        title_lbl = Gtk.Label(label="Trova duplicati")
        title_lbl.add_css_class("dup-title")
        title_lbl.set_halign(Gtk.Align.START)
        header.append(title_lbl)

        self._subtitle = Gtk.Label(label=f"Scansione di: {self._folder}")
        self._subtitle.add_css_class("dup-subtitle")
        self._subtitle.set_halign(Gtk.Align.START)
        self._subtitle.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        header.append(self._subtitle)

        self._progress = Gtk.ProgressBar()
        self._progress.set_show_text(True)
        self._progress.set_text("Analisi in corso…")
        self._progress.set_margin_start(12)
        self._progress.set_margin_end(12)
        self._progress.set_margin_top(8)
        self._progress.set_margin_bottom(4)
        root_box.append(self._progress)

        self._hint = Gtk.Label(
            label="☑ = verrà spostato nel cestino  |  "
            "Il primo file di ogni gruppo non è selezionato per default"
        )
        self._hint.add_css_class("dup-hint")
        self._hint.set_halign(Gtk.Align.START)
        self._hint.set_margin_start(12)
        self._hint.set_margin_top(4)
        self._hint.set_visible(False)
        root_box.append(self._hint)

        self._store = Gtk.ListStore(bool, str, str, str)
        tv = Gtk.TreeView(model=self._store)
        tv.set_rubber_banding(True)

        r_toggle = Gtk.CellRendererToggle()
        r_toggle.connect("toggled", self._on_toggle)
        col0 = Gtk.TreeViewColumn("Elimina", r_toggle, active=0)
        col0.set_fixed_width(72)
        col0.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        tv.append_column(col0)

        r1 = Gtk.CellRendererText()
        r1.set_property("font", "monospace 10")
        col1 = Gtk.TreeViewColumn("Group", r1, text=1)
        col1.set_fixed_width(100)
        col1.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        tv.append_column(col1)

        r2 = Gtk.CellRendererText()
        r2.set_property("ellipsize", Pango.EllipsizeMode.MIDDLE)
        col2 = Gtk.TreeViewColumn("Percorso", r2, text=2)
        col2.set_expand(True)
        col2.set_resizable(True)
        tv.append_column(col2)

        r3 = Gtk.CellRendererText()
        col3 = Gtk.TreeViewColumn("Dimensione", r3, text=3)
        col3.set_fixed_width(90)
        col3.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        tv.append_column(col3)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_margin_start(8)
        scroll.set_margin_end(8)
        scroll.set_margin_top(6)
        scroll.set_child(tv)
        root_box.append(scroll)

        self._status = Gtk.Label(label="")
        self._status.set_halign(Gtk.Align.START)
        self._status.set_margin_start(12)
        self._status.set_margin_top(4)
        self._status.set_visible(False)
        root_box.append(self._status)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_margin_start(12)
        btn_box.set_margin_end(12)
        btn_box.set_margin_top(8)
        btn_box.set_margin_bottom(12)
        btn_box.set_halign(Gtk.Align.END)
        root_box.append(btn_box)

        self._btn_auto = Gtk.Button(label="Seleziona duplicati automaticamente")
        self._btn_auto.connect("clicked", self._select_all_but_first)
        self._btn_auto.set_sensitive(False)
        btn_box.append(self._btn_auto)

        self._btn_trash = Gtk.Button(label="🗑  Sposta nel Cestino")
        self._btn_trash.add_css_class("destructive-action")
        self._btn_trash.connect("clicked", self._on_trash)
        self._btn_trash.set_sensitive(False)
        btn_box.append(self._btn_trash)

        btn_close = Gtk.Button(label="Chiudi")
        btn_close.connect("clicked", lambda *_: self.close())
        btn_box.append(btn_close)

    def _start_scan(self):
        self._progress.set_visible(True)
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        def on_progress(done, total):
            frac = done / total if total else 0
            GLib.idle_add(self._progress.set_fraction, frac)
            GLib.idle_add(self._progress.set_text, f"{done} / {total} file analizzati")

        duplicates = find_duplicates(self._folder, progress_cb=on_progress)
        GLib.idle_add(self._on_scan_done, duplicates)

    def _on_scan_done(self, duplicates: dict):
        self._duplicates = duplicates
        self._progress.set_visible(False)

        n_groups = len(duplicates)
        n_files = sum(len(v) for v in duplicates.values())
        wasted = 0
        for paths in duplicates.values():
            try:
                wasted += os.path.getsize(paths[0]) * (len(paths) - 1)
            except OSError as e:
                logging.debug("Cannot stat %s for wasted space: %s", paths[0], e)

        if n_groups == 0:
            self._subtitle.set_text(f"{self._folder}  •  Nessun duplicato trovato ✓")
        else:
            self._subtitle.set_text(
                f"{self._folder}  •  {n_groups} gruppi  •  "
                f"{n_files} file  •  Recuperabile: {human_size(wasted)}"
            )
            self._hint.set_visible(True)
            self._btn_auto.set_sensitive(True)
            self._btn_trash.set_sensitive(True)
            self._populate_store()

        return False

    def _populate_store(self):
        self._store.clear()
        for digest, paths in self._duplicates.items():
            short_hash = digest[:8]
            first = True
            for p in sorted(paths):
                try:
                    size = human_size(os.path.getsize(p))
                except OSError:
                    size = "?"
                self._store.append([not first, short_hash, p, size])
                first = False

    def _on_toggle(self, renderer, path_str):
        self._store[path_str][0] = not self._store[path_str][0]

    def _select_all_but_first(self, _btn):
        seen = set()
        for row in self._store:
            digest = row[1]
            if digest not in seen:
                seen.add(digest)
                row[0] = False
            else:
                row[0] = True

    def _on_trash(self, _btn):
        to_trash = [row[2] for row in self._store if row[0]]
        if not to_trash:
            self._show_status("Nessun file selezionato.", error=True)
            return

        dlg = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=f"Spostare {len(to_trash)} file nel cestino?",
        )
        preview = "\n".join(os.path.basename(p) for p in to_trash[:8])
        if len(to_trash) > 8:
            preview += f"\n… e altri {len(to_trash) - 8} file"
        dlg.set_property("secondary-text", preview)
        dlg.connect("response", self._on_confirm, to_trash)
        dlg.present()

    def _on_confirm(self, dlg, response_id, to_trash):
        dlg.destroy()
        if response_id != Gtk.ResponseType.OK:
            return

        errors = []
        trashed = set()
        root = os.path.realpath(self._folder)
        for path in to_trash:
            # Verify path is still under the scanned root directory
            if not os.path.realpath(path).startswith(root + os.sep):
                logging.warning("Skipping path outside scan root: %s", path)
                errors.append(
                    f"{os.path.basename(path)}: percorso fuori dalla cartella scansionata"
                )
                continue
            try:
                result = subprocess.run(
                    ["gio", "trash", path], capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    trashed.add(path)
                else:
                    logging.warning("gio trash failed for %s: %s", path, result.stderr.strip())
                    errors.append(f"{os.path.basename(path)}: impossibile spostare nel cestino")
            except subprocess.TimeoutExpired:
                logging.warning("gio trash timed out for %s", path)
                errors.append(f"{os.path.basename(path)}: timeout")
            except FileNotFoundError:
                logging.error("gio command not found — cannot trash files")
                errors.append(f"{os.path.basename(path)}: gio non trovato")
                break
            except OSError as e:
                logging.warning("gio trash failed for %s: %s", path, e)
                errors.append(f"{os.path.basename(path)}: {e}")

        to_remove = []
        it = self._store.get_iter_first()
        while it:
            if self._store.get_value(it, 2) in trashed:
                to_remove.append(it)
            it = self._store.iter_next(it)
        for it in reversed(to_remove):
            self._store.remove(it)

        msg = f"✓ {len(trashed)} file spostati nel cestino."
        if errors:
            msg += f"\n{len(errors)} errori:\n" + "\n".join(errors[:5])
        self._show_status(msg, error=bool(errors))

    def _show_status(self, msg: str, error: bool = False):
        color = "#d73a49" if error else "#22863a"
        self._status.set_markup(f"<span foreground='{color}'>{GLib.markup_escape_text(msg)}</span>")
        self._status.set_visible(True)


# ---------------------------------------------------------------------------
# Extension — uses is_directory() instead of get_file_type()
# and also checks via URI as fallback
# ---------------------------------------------------------------------------


class DuplicateFinderExtension(GObject.GObject, Nautilus.MenuProvider):
    def _path_from_file(self, f):
        """Extract local path robustly, with URI fallback."""
        # Direct method
        try:
            loc = f.get_location()
            if loc:
                p = loc.get_path()
                if p:
                    return p
        except Exception as e:
            logging.debug("get_location failed: %s", e)
        # fallback: parse dell'URI
        try:
            uri = f.get_uri()
            if uri and uri.startswith("file://"):
                from urllib.parse import unquote

                return unquote(uri[7:])
        except Exception as e:
            logging.debug("URI fallback failed: %s", e)
        return None

    def _is_local_dir(self, f):
        """Return True if the Nautilus file is a local directory (double check)."""
        # Check 1: Nautilus file type
        try:
            if f.get_file_type() == Nautilus.FileType.DIRECTORY:
                return True
        except Exception as e:
            logging.debug("get_file_type check failed: %s", e)
        # check 2: is_directory()
        try:
            if f.is_directory():
                return True
        except Exception as e:
            logging.debug("is_directory check failed: %s", e)
        # check 3: controlla sul filesystem
        path = self._path_from_file(f)
        if path and os.path.isdir(path):
            return True
        return False

    def get_file_items(self, files):
        """Right-click on a selected folder."""
        if len(files) != 1:
            return []
        f = files[0]
        if not self._is_local_dir(f):
            return []
        path = self._path_from_file(f)
        if not path:
            return []

        item = Nautilus.MenuItem(
            name="TrovaDuplicati::find",
            label="🔍 Trova duplicati",
            tip=f"Trova file identici in {f.get_name()}",
        )
        item.connect("activate", self._on_activate, path)
        return [item]

    def get_background_items(self, folder):
        """Right-click on the background of an open folder."""
        if folder is None:
            return []
        path = self._path_from_file(folder)
        if not path:
            return []

        item = Nautilus.MenuItem(
            name="TrovaDuplicati::find_bg",
            label="🔍 Trova duplicati in questa cartella",
            tip=f"Trova file identici in {path}",
        )
        item.connect("activate", self._on_activate, path)
        return [item]

    def _on_activate(self, _item, path):
        win = DupFinderWindow(path)
        win.present()
