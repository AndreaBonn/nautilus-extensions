"""
git_status_nautilus.py — Pannello di stato Git per Nautilus
Apre una finestra flottante con aggiornamento automatico ogni 3 secondi.

Uso: click destro in una cartella git → "⎇ Stato Git…"

Installazione:
  cp git_status_nautilus.py ~/.local/share/nautilus-python/extensions/
  nautilus -q && nautilus &
"""

import os
import subprocess
import threading
import gi

gi.require_version("Nautilus", "4.0")
gi.require_version("Gtk", "4.0")

from gi.repository import Nautilus, GObject, Gtk, GLib, Pango
from urllib.parse import unquote, urlparse


def run_git(args, cwd):
    try:
        r = subprocess.run(["git"] + args, cwd=cwd,
                           capture_output=True, text=True, timeout=5)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def is_git_repo(path):
    return bool(run_git(["rev-parse", "--show-toplevel"], cwd=path))


# ─── Finestra di stato ─────────────────────────────────────────────────────────
class GitStatusWindow(Gtk.Window):
    REFRESH_MS = 3000

    def __init__(self, path):
        super().__init__()
        self._path = path
        self._timer_id = None

        repo_name = os.path.basename(
            run_git(["rev-parse", "--show-toplevel"], cwd=path) or path
        )
        self.set_default_size(360, 580)
        self.set_resizable(True)

        # Header bar
        hb = Gtk.HeaderBar()
        self._branch_label = Gtk.Label(label="…")
        self._branch_label.set_markup("<b>…</b>")
        hb.set_title_widget(self._branch_label)

        refresh_btn = Gtk.Button(label="↻")
        refresh_btn.set_tooltip_text("Aggiorna ora")
        refresh_btn.set_has_frame(False)
        refresh_btn.connect("clicked", lambda *_: self._refresh())
        hb.pack_end(refresh_btn)

        repo_lbl = Gtk.Label(label=repo_name)
        repo_lbl.add_css_class("dim-label")
        hb.pack_start(repo_lbl)

        self.set_titlebar(hb)

        # CSS
        css = Gtk.CssProvider()
        css.load_from_data(b"""
            .section-title {
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 0.8px;
                opacity: 0.45;
                padding: 12px 14px 3px;
            }
            .file-row label { padding: 2px 0; }
            .status-staged    { color: #98C379; }
            .status-modified  { color: #E5C07B; }
            .status-untracked { color: #61AFEF; }
            .status-deleted   { color: #E06C75; }
            .sign-label {
                font-family: monospace;
                font-size: 13px;
                min-width: 20px;
            }
            .filename {
                font-family: monospace;
                font-size: 11px;
            }
            .commit-row {
                padding: 6px 14px;
                border-bottom: 1px solid alpha(currentColor, 0.06);
            }
            .commit-hash {
                font-family: monospace;
                font-size: 10px;
                opacity: 0.4;
            }
            .commit-msg  { font-size: 12px; }
            .commit-meta { font-size: 10px; opacity: 0.45; }
            .clean-label { color: #98C379; padding: 8px 14px; font-size: 12px; }
            .sync-label  { font-size: 11px; opacity: 0.55; padding: 0 14px 6px; }
            .stash-label { font-size: 11px; opacity: 0.5; padding: 6px 14px; }
            .dim-label   { font-size: 11px; opacity: 0.45; }
        """)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Layout principale
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        self._content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        scroll.set_child(self._content)
        outer.append(scroll)

        # Status bar in fondo
        self._status_bar = Gtk.Label(label="")
        self._status_bar.add_css_class("dim-label")
        self._status_bar.set_margin_bottom(6)
        outer.append(self._status_bar)

        self.set_child(outer)

        # Prima caricamento + timer
        self._refresh()
        self._timer_id = GLib.timeout_add(self.REFRESH_MS, self._on_timer)
        self.connect("close-request", self._on_close)

    def _on_close(self, *_):
        if self._timer_id:
            GLib.source_remove(self._timer_id)
        return False

    def _on_timer(self):
        self._refresh()
        return True

    def _refresh(self):
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        path = self._path

        branch  = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=path)
        ahead   = run_git(["rev-list", "--count", "@{u}..HEAD"], cwd=path)
        behind  = run_git(["rev-list", "--count", "HEAD..@{u}"], cwd=path)
        status  = run_git(["status", "--porcelain"], cwd=path)
        log_raw = run_git(["log", "--pretty=format:%h|%an|%ar|%s", "-10"], cwd=path)
        stash_n = run_git(["stash", "list"], cwd=path)

        staged = []
        unstaged = []
        untracked = []

        for line in status.split("\n"):
            if len(line) < 4:
                continue
            x, y = line[0], line[1]
            name = line[3:]
            if x in "AMRDC" and x != " ":
                staged.append((x, name))
            if y in "MD":
                unstaged.append((y, name))
            if line[:2] == "??":
                untracked.append(name)

        commits = []
        for line in log_raw.split("\n"):
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append(parts)

        stash_count = len([l for l in stash_n.split("\n") if l.strip()]) if stash_n else 0

        GLib.idle_add(self._render, branch, ahead, behind,
                      staged, unstaged, untracked, commits, stash_count)

    def _clear(self):
        while True:
            child = self._content.get_first_child()
            if child is None:
                break
            self._content.remove(child)

    def _render(self, branch, ahead, behind,
                staged, unstaged, untracked, commits, stash_count):
        self._clear()

        # Aggiorna titolo branch
        sync = ""
        if ahead  and ahead  != "0": sync += f"  ↑{ahead}"
        if behind and behind != "0": sync += f"  ↓{behind}"
        self._branch_label.set_markup(f"<b>⎇  {branch}</b>{sync}")

        if sync:
            sync_lbl = Gtk.Label(label=sync.strip())
            sync_lbl.add_css_class("sync-label")
            sync_lbl.set_xalign(0)
            self._content.append(sync_lbl)

        # ── Staged ────────────────────────────────────────────────────────────
        if staged:
            self._section("STAGED", len(staged))
            for s, name in staged:
                self._file_row(s, name, "status-staged")

        # ── Modificati ────────────────────────────────────────────────────────
        if unstaged:
            self._section("MODIFICATI", len(unstaged))
            for s, name in unstaged:
                cls = "status-deleted" if s == "D" else "status-modified"
                self._file_row(s, name, cls)

        # ── Untracked ─────────────────────────────────────────────────────────
        if untracked:
            self._section("NUOVI / UNTRACKED", len(untracked))
            for name in untracked[:15]:
                self._file_row("?", name, "status-untracked")
            if len(untracked) > 15:
                more = Gtk.Label(label=f"  … e altri {len(untracked)-15} file")
                more.add_css_class("commit-meta")
                more.set_xalign(0)
                more.set_margin_start(14)
                self._content.append(more)

        # ── Working tree pulito ───────────────────────────────────────────────
        if not staged and not unstaged and not untracked:
            ok = Gtk.Label(label="✓  Working tree pulito")
            ok.add_css_class("clean-label")
            ok.set_xalign(0)
            self._content.append(ok)

        # ── Separatore ────────────────────────────────────────────────────────
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_margin_top(8)
        self._content.append(sep)

        # ── Ultimi commit ─────────────────────────────────────────────────────
        self._section("ULTIMI COMMIT", len(commits))
        for h, author, date, msg in commits:
            row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            row.add_css_class("commit-row")

            top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            hash_l = Gtk.Label(label=h)
            hash_l.add_css_class("commit-hash")
            hash_l.set_xalign(0)
            hash_l.set_hexpand(True)
            top.append(hash_l)
            date_l = Gtk.Label(label=date)
            date_l.add_css_class("commit-meta")
            top.append(date_l)

            msg_l = Gtk.Label(
                label=msg[:55] + ("…" if len(msg) > 55 else "")
            )
            msg_l.add_css_class("commit-msg")
            msg_l.set_xalign(0)
            msg_l.set_ellipsize(Pango.EllipsizeMode.END)

            auth_l = Gtk.Label(label=author)
            auth_l.add_css_class("commit-meta")
            auth_l.set_xalign(0)

            row.append(top)
            row.append(msg_l)
            row.append(auth_l)
            self._content.append(row)

        # ── Stash ─────────────────────────────────────────────────────────────
        if stash_count > 0:
            sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            sep2.set_margin_top(4)
            self._content.append(sep2)
            sl = Gtk.Label(
                label=f"📦  {stash_count} stash salvat{'o' if stash_count==1 else 'i'}"
            )
            sl.add_css_class("stash-label")
            sl.set_xalign(0)
            self._content.append(sl)

        # ── Status bar ────────────────────────────────────────────────────────
        total = len(staged) + len(unstaged) + len(untracked)
        self._status_bar.set_text(
            f"{total} modifiche  ·  {len(commits)} commit recenti"
            + (f"  ·  {stash_count} stash" if stash_count else "")
        )

    def _section(self, title, count):
        lbl = Gtk.Label(label=f"{title}  ({count})")
        lbl.add_css_class("section-title")
        lbl.set_xalign(0)
        self._content.append(lbl)

    def _file_row(self, sign, name, css_class):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        box.add_css_class("file-row")
        box.set_margin_start(14)
        box.set_margin_end(10)

        icons = {"A": "＋", "M": "●", "D": "✕", "R": "→", "C": "⊕", "?": "＋"}
        icon = Gtk.Label(label=icons.get(sign, sign))
        icon.add_css_class("sign-label")
        icon.add_css_class(css_class)
        box.append(icon)

        name_lbl = Gtk.Label(label=os.path.basename(name))
        name_lbl.add_css_class("filename")
        name_lbl.set_xalign(0)
        name_lbl.set_ellipsize(Pango.EllipsizeMode.START)
        name_lbl.set_hexpand(True)
        name_lbl.set_tooltip_text(name)
        box.append(name_lbl)

        self._content.append(box)


# ─── Estensione Nautilus ───────────────────────────────────────────────────────
class GitStatusExtension(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self):
        super().__init__()
        self._window = None

    def _git_root(self, path):
        return run_git(["rev-parse", "--show-toplevel"], cwd=path) or None

    def get_background_items(self, current_folder):
        if current_folder is None:
            return []
        path = unquote(urlparse(current_folder.get_uri()).path)
        if not self._git_root(path):
            return []
        return self._make_menu(path)

    def _make_menu(self, path):
        item = Nautilus.MenuItem(
            name="GitStatus::Open",
            label="⎇  Stato Git…",
            tip="Mostra branch, file modificati e ultimi commit"
        )
        item.connect("activate", lambda *_: self._open(path))
        return [item]

    def _open(self, path):
        # Riusa la finestra se già aperta, cambia solo il path
        if self._window and self._window.get_visible():
            self._window._path = path
            self._window._refresh()
            self._window.present()
        else:
            self._window = GitStatusWindow(path)
            self._window.present()
