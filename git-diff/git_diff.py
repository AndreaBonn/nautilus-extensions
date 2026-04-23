"""
git_diff_nautilus.py — Visual side-by-side diff from Nautilus context menu

Right-click on a modified file → "⎇ Mostra Diff Git"
Opens a window with a coloured side-by-side diff.

Installation:
  cp git_diff_nautilus.py ~/.local/share/nautilus-python/extensions/
  nautilus -q && nautilus &
"""

from __future__ import annotations

import logging
import os
import subprocess
import threading

import gi

gi.require_version("Nautilus", "4.0")
gi.require_version("Gtk", "4.0")

from urllib.parse import unquote, urlparse

from gi.repository import GLib, GObject, Gtk, Nautilus


def run_git(args: list[str], cwd: str) -> str:
    try:
        r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, timeout=10)
        return r.stdout if r.returncode == 0 else ""
    except Exception as e:
        logging.debug("run_git %s failed: %s", args[0] if args else "", e)
        return ""


def parse_diff(raw: str) -> list[dict]:
    """
    Parsa l'output di `git diff` in chunks.
    Ritorna lista di hunk: {'header': str, 'lines': [(type, lineno_old, lineno_new, text), ...]}
    type: 'add' | 'del' | 'ctx'
    """
    hunks = []
    current = None
    old_line = new_line = 0

    for line in raw.split("\n"):
        if line.startswith("@@"):
            # es. @@ -10,6 +10,8 @@
            import re

            m = re.search(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@(.*)", line)
            if m:
                old_line = int(m.group(1))
                new_line = int(m.group(2))
                header = line
                current = {"header": header, "lines": []}
                hunks.append(current)
        elif current is not None:
            if line.startswith("+") and not line.startswith("+++"):
                current["lines"].append(("add", None, new_line, line[1:]))
                new_line += 1
            elif line.startswith("-") and not line.startswith("---"):
                current["lines"].append(("del", old_line, None, line[1:]))
                old_line += 1
            elif not line.startswith(("---", "+++")):
                current["lines"].append(
                    ("ctx", old_line, new_line, line[1:] if line.startswith(" ") else line)
                )
                old_line += 1
                new_line += 1

    return hunks


# ─── Finestra di diff ──────────────────────────────────────────────────────────
class DiffWindow(Gtk.Window):
    def __init__(self, filepath, git_root):
        super().__init__()
        self.set_default_size(1100, 700)
        fname = os.path.basename(filepath)
        self.set_title(f"Git Diff — {fname}")

        # Header bar
        hb = Gtk.HeaderBar()
        hb.set_title_widget(Gtk.Label(label=f"⎇  {fname}"))

        # Toggle: unified / side-by-side
        self.split_toggle = Gtk.ToggleButton(label="Side-by-side")
        self.split_toggle.set_active(True)
        self.split_toggle.connect("toggled", self._on_toggle)
        hb.pack_end(self.split_toggle)

        self.set_titlebar(hb)

        # Spinner mentre carica
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        spinner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        spinner_box.set_halign(Gtk.Align.CENTER)
        spinner_box.set_valign(Gtk.Align.CENTER)
        spinner = Gtk.Spinner()
        spinner.start()
        spinner_box.append(spinner)
        self.stack.add_named(spinner_box, "loading")
        self.set_child(self.stack)

        self._filepath = filepath
        self._git_root = git_root
        self._hunks = []
        self._split = True

        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        rel = os.path.relpath(self._filepath, self._git_root)

        # Prova prima diff staged, poi working tree
        raw = run_git(["diff", "--", rel], cwd=self._git_root)
        staged = False
        if not raw.strip():
            raw = run_git(["diff", "--cached", "--", rel], cwd=self._git_root)
            staged = True

        if not raw.strip():
            # File non modificato o nuovo untracked: mostra il contenuto
            raw = run_git(["show", f"HEAD:{rel}"], cwd=self._git_root)
            GLib.idle_add(self._show_unmodified, raw)
            return

        hunks = parse_diff(raw)
        GLib.idle_add(self._build_diff_ui, hunks, staged)

    def _show_unmodified(self, content):
        lbl = Gtk.Label(label="Nessuna modifica rilevata per questo file.")
        lbl.set_margin_top(40)
        self.stack.add_named(lbl, "diff")
        self.stack.set_visible_child_name("diff")

    def _build_diff_ui(self, hunks, staged):
        self._hunks = hunks
        self._staged = staged
        self._render()

    def _on_toggle(self, btn):
        self._split = btn.get_active()
        btn.set_label("Side-by-side" if self._split else "Unificato")
        if self._hunks:
            self._render()

    def _render(self):
        # Rimuovi vecchio diff se esiste
        old = self.stack.get_child_by_name("diff")
        if old:
            self.stack.remove(old)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        if self._split:
            widget = self._build_split_view()
        else:
            widget = self._build_unified_view()

        scroll.set_child(widget)
        self.stack.add_named(scroll, "diff")
        self.stack.set_visible_child_name("diff")

    # ── Vista side-by-side ─────────────────────────────────────────────────────
    def _build_split_view(self):
        css = Gtk.CssProvider()
        css.load_from_data(b"""
            .diff-grid { background: transparent; }
            .hunk-header {
                font-family: monospace; font-size: 11px;
                background: alpha(#61AFEF, 0.12);
                color: alpha(currentColor, 0.6);
                padding: 3px 8px;
            }
            .line-add  { background: alpha(#98C379, 0.18); }
            .line-del  { background: alpha(#E06C75, 0.18); }
            .line-ctx  { background: transparent; }
            .line-empty{ background: alpha(currentColor, 0.04); }
            .line-num  {
                font-family: monospace; font-size: 11px;
                color: alpha(currentColor, 0.35);
                padding: 1px 8px; min-width: 36px;
                text-align: right; border-right: 1px solid alpha(currentColor,0.1);
            }
            .line-text {
                font-family: monospace; font-size: 12px;
                padding: 1px 8px; white-space: pre;
            }
            .sign-add { color: #98C379; font-weight: bold; padding: 0 4px; }
            .sign-del { color: #E06C75; font-weight: bold; padding: 0 4px; }
            .sign-ctx { color: transparent; padding: 0 4px; }
            .col-sep  { background: alpha(currentColor, 0.1); min-width: 1px; }
        """)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        outer.set_margin_top(4)

        for hunk in self._hunks:
            # Header hunk
            h_lbl = Gtk.Label(label=hunk["header"])
            h_lbl.add_css_class("hunk-header")
            h_lbl.set_xalign(0)
            outer.append(h_lbl)

            # Build two columns: old (ctx+del only) and new (ctx+add only)
            left_lines = []  # (lineno, type, text)
            right_lines = []

            # Associa righe: del/add appaiono affiancate, ctx su entrambi i lati
            raw_lines = hunk["lines"]
            i = 0
            while i < len(raw_lines):
                typ, lo, ln, txt = raw_lines[i]
                if typ == "ctx":
                    left_lines.append((lo, "ctx", txt))
                    right_lines.append((ln, "ctx", txt))
                    i += 1
                elif typ == "del":
                    # Prova a trovare una riga add corrispondente
                    j = i + 1
                    while j < len(raw_lines) and raw_lines[j][0] == "del":
                        j += 1
                    adds = []
                    k = j
                    while k < len(raw_lines) and raw_lines[k][0] == "add":
                        adds.append(raw_lines[k])
                        k += 1
                    # Raggruppa del e add affiancati
                    dels = raw_lines[i:j]
                    pairs = max(len(dels), len(adds))
                    for p in range(pairs):
                        dl = dels[p] if p < len(dels) else None
                        al = adds[p] if p < len(adds) else None
                        if dl:
                            left_lines.append((dl[1], "del", dl[3]))
                        else:
                            left_lines.append((None, "empty", ""))
                        if al:
                            right_lines.append((al[2], "add", al[3]))
                        else:
                            right_lines.append((None, "empty", ""))
                    i = k
                else:  # add solitario (senza del prima)
                    left_lines.append((None, "empty", ""))
                    right_lines.append((ln, "add", txt))
                    i += 1

            # Griglia: left_num | left_text | sep | right_num | right_text
            grid = Gtk.Grid()
            grid.add_css_class("diff-grid")
            grid.set_column_homogeneous(False)

            for row_i, (ll, rl) in enumerate(zip(left_lines, right_lines)):
                l_no, l_type, l_txt = ll
                r_no, r_type, r_txt = rl

                # Left num
                ln_lbl = Gtk.Label(label=str(l_no) if l_no else "")
                ln_lbl.add_css_class("line-num")
                ln_lbl.add_css_class(f"line-{l_type}")
                grid.attach(ln_lbl, 0, row_i, 1, 1)

                # Left sign
                signs = {"add": "+", "del": "−", "ctx": " ", "empty": ""}
                ls_lbl = Gtk.Label(label=signs.get(l_type, ""))
                ls_lbl.add_css_class(f"sign-{'del' if l_type == 'del' else 'ctx'}")
                ls_lbl.add_css_class(f"line-{l_type}")
                grid.attach(ls_lbl, 1, row_i, 1, 1)

                # Left text
                lt_lbl = Gtk.Label(label=l_txt[:120])
                lt_lbl.add_css_class("line-text")
                lt_lbl.add_css_class(f"line-{l_type}")
                lt_lbl.set_xalign(0)
                lt_lbl.set_hexpand(True)
                grid.attach(lt_lbl, 2, row_i, 1, 1)

                # Separatore centrale
                sep = Gtk.Box()
                sep.add_css_class("col-sep")
                sep.set_size_request(1, -1)
                grid.attach(sep, 3, row_i, 1, 1)

                # Right num
                rn_lbl = Gtk.Label(label=str(r_no) if r_no else "")
                rn_lbl.add_css_class("line-num")
                rn_lbl.add_css_class(f"line-{r_type}")
                grid.attach(rn_lbl, 4, row_i, 1, 1)

                # Right sign
                rs_lbl = Gtk.Label(label=signs.get(r_type, ""))
                rs_lbl.add_css_class(f"sign-{'add' if r_type == 'add' else 'ctx'}")
                rs_lbl.add_css_class(f"line-{r_type}")
                grid.attach(rs_lbl, 5, row_i, 1, 1)

                # Right text
                rt_lbl = Gtk.Label(label=r_txt[:120])
                rt_lbl.add_css_class("line-text")
                rt_lbl.add_css_class(f"line-{r_type}")
                rt_lbl.set_xalign(0)
                rt_lbl.set_hexpand(True)
                grid.attach(rt_lbl, 6, row_i, 1, 1)

            outer.append(grid)

            # Separatore tra hunk
            sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            sep.set_margin_top(2)
            sep.set_margin_bottom(2)
            outer.append(sep)

        return outer

    # ── Vista unificata ────────────────────────────────────────────────────────
    def _build_unified_view(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        outer.set_margin_top(4)

        for hunk in self._hunks:
            h_lbl = Gtk.Label(label=hunk["header"])
            h_lbl.add_css_class("hunk-header")
            h_lbl.set_xalign(0)
            outer.append(h_lbl)

            for typ, lo, _ln, txt in hunk["lines"]:
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
                box.add_css_class(f"line-{typ}")

                num_lbl = Gtk.Label(label=(str(lo) if lo else ""))
                num_lbl.add_css_class("line-num")
                box.append(num_lbl)

                sign_map = {"add": "+", "del": "−", "ctx": " "}
                sign = Gtk.Label(label=sign_map.get(typ, " "))
                sign.add_css_class(
                    f"sign-{'add' if typ == 'add' else 'del' if typ == 'del' else 'ctx'}"
                )
                box.append(sign)

                t_lbl = Gtk.Label(label=txt[:160])
                t_lbl.add_css_class("line-text")
                t_lbl.set_xalign(0)
                t_lbl.set_hexpand(True)
                box.append(t_lbl)

                outer.append(box)

        return outer


# ─── Estensione Nautilus ───────────────────────────────────────────────────────
class GitDiffExtension(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self):
        super().__init__()

    def _git_root(self, path):
        try:
            cwd = os.path.dirname(path) if os.path.isfile(path) else path
            r = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=3,
            )
            return r.stdout.strip() if r.returncode == 0 else None
        except Exception:
            return None

    def _menu_item(self, name):
        item = Nautilus.MenuItem(
            name=name,
            label="⎇  Mostra Diff Git",
            tip="Visualizza le modifiche side-by-side rispetto all'ultimo commit",
        )
        return item

    # Click destro su un file o cartella selezionati
    def get_file_items(self, files):
        if len(files) != 1:
            return []
        f = files[0]
        uri = f.get_uri()
        if not uri.startswith("file://"):
            return []
        path = unquote(urlparse(uri).path)
        root = self._git_root(path)
        if not root:
            return []
        item = self._menu_item("GitDiff::ShowDiff")
        item.connect("activate", lambda *_: self._open_diff(path, root))
        return [item]

    # Click destro sul fondo della cartella corrente
    def get_background_items(self, current_folder):
        if current_folder is None:
            return []
        uri = current_folder.get_uri()
        if not uri.startswith("file://"):
            return []
        path = unquote(urlparse(uri).path)
        root = self._git_root(path)
        if not root:
            return []
        item = self._menu_item("GitDiff::ShowDiffBg")
        item.connect("activate", lambda *_: self._open_diff(path, root))
        return [item]

    def _open_diff(self, path, root):
        win = DiffWindow(path, root)
        win.present()
