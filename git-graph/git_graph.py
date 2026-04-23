"""
git_graph_nautilus.py — Nautilus extension to visualise the Git graph
Installation:
  mkdir -p ~/.local/share/nautilus-python/extensions/
  cp git_graph_nautilus.py ~/.local/share/nautilus-python/extensions/
  nautilus -q && nautilus &

Dependencies:
  sudo apt install python3-nautilus python3-gi gir1.2-gtk-3.0
  pip3 install gitpython  --break-system-packages
"""

from __future__ import annotations

import logging
import os
import subprocess
import threading

import gi

gi.require_version("Nautilus", "4.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

from urllib.parse import unquote, urlparse

from gi.repository import GLib, GObject, Gtk, Nautilus

# ─── Palette colori per i branch ──────────────────────────────────────────────
BRANCH_COLORS = [
    "#61AFEF",  # azzurro
    "#E5C07B",  # giallo
    "#98C379",  # verde
    "#E06C75",  # rosso
    "#C678DD",  # viola
    "#56B6C2",  # ciano
    "#FF9F5B",  # arancio
    "#F8F8F2",  # bianco
]

HEAD_COLOR = "#FFD700"  # oro per HEAD
MERGE_COLOR = "#FF6B9D"  # rosa per merge commits


def run_git(args: list[str], cwd: str) -> str:
    """Esegue un comando git e restituisce l'output."""
    try:
        result = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception as e:
        logging.debug("run_git %s failed: %s", args[0] if args else "", e)
        return ""


def get_git_log(path: str, max_commits: int = 60) -> tuple[list[dict] | None, dict | None]:
    """
    Recupera la storia git con grafo.
    Formato: hash|branch_refs|autore|data|messaggio
    """
    fmt = "%H|%D|%an|%ar|%s"
    raw = run_git(
        ["log", "--all", "--decorate", f"--pretty=format:{fmt}", f"-{max_commits}"], cwd=path
    )
    if not raw:
        return None, None

    # Ottieni il grafo ASCII per determinare le relazioni
    run_git(["log", "--all", "--graph", "--pretty=format:%H", f"-{max_commits}"], cwd=path)

    commits = []
    for line in raw.split("\n"):
        if not line.strip():
            continue
        parts = line.split("|", 4)
        if len(parts) < 5:
            continue
        h, refs, author, date, msg = parts
        branches = []
        is_head = False
        for ref in refs.split(","):
            ref = ref.strip()
            if ref == "HEAD" or ref.startswith("HEAD ->"):
                is_head = True
                if "->" in ref:
                    branches.append(ref.split("->")[1].strip())
            elif ref.startswith("origin/"):
                pass  # skip remote refs for display
            elif ref:
                branches.append(ref)
        commits.append(
            {
                "hash": h[:8],
                "full_hash": h,
                "refs": refs,
                "branches": branches,
                "author": author,
                "date": date,
                "message": msg[:60] + ("…" if len(msg) > 60 else ""),
                "is_head": is_head,
            }
        )

    # Assegna un colore a ogni branch unico
    branch_color_map = {}
    color_idx = 0
    for c in commits:
        for b in c["branches"]:
            if b not in branch_color_map:
                branch_color_map[b] = BRANCH_COLORS[color_idx % len(BRANCH_COLORS)]
                color_idx += 1

    return commits, branch_color_map


def hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


# ─── Widget di disegno del grafo ──────────────────────────────────────────────
class GitGraphWidget(Gtk.DrawingArea):
    ROW_H = 52
    COL_W = 22
    NODE_R = 7
    LEFT_PAD = 16

    def __init__(self, commits, branch_color_map, repo_name):
        super().__init__()
        self.commits = commits
        self.branch_color_map = branch_color_map
        self.repo_name = repo_name
        self._layout_columns()
        h = max(400, len(commits) * self.ROW_H + 20)
        self.set_content_height(h)
        self.set_draw_func(self._draw)

    def _layout_columns(self):
        """Assegna a ogni commit una colonna (semplice euristica)."""
        free_cols = []
        self.commit_cols = []

        active_branches = {}  # branch -> colonna

        for _i, c in enumerate(self.commits):
            branch = c["branches"][0] if c["branches"] else None

            if branch and branch in active_branches:
                col = active_branches[branch]
            else:
                if free_cols:
                    col = free_cols.pop(0)
                else:
                    col = len(active_branches)
                if branch:
                    active_branches[branch] = col

            self.commit_cols.append(col)

    def _node_pos(self, row, col):
        x = self.LEFT_PAD + col * self.COL_W + self.NODE_R + 4
        y = row * self.ROW_H + self.ROW_H // 2
        return x, y

    def _get_node_color(self, commit):
        if commit["is_head"]:
            return hex_to_rgb(HEAD_COLOR)
        for b in commit["branches"]:
            if b in self.branch_color_map:
                return hex_to_rgb(self.branch_color_map[b])
        return hex_to_rgb("#6C7086")

    def _draw(self, area, cr, width, height):
        # Sfondo scuro
        cr.set_source_rgb(0.11, 0.12, 0.16)
        cr.paint()

        # Titolo repo
        cr.set_source_rgb(0.85, 0.87, 0.91)
        cr.select_font_face("Monospace", 0, 1)
        cr.set_font_size(11)
        cr.move_to(self.LEFT_PAD, 14)
        cr.show_text(f"⎇  {self.repo_name}")

        n = len(self.commits)
        row_h = self.ROW_H

        # Disegna le linee di connessione tra commit
        for i in range(n - 1):
            x1, y1 = self._node_pos(i, self.commit_cols[i])
            x2, y2 = self._node_pos(i + 1, self.commit_cols[i + 1])
            c = self._get_node_color(self.commits[i])
            cr.set_source_rgba(c[0], c[1], c[2], 0.5)
            cr.set_line_width(2)
            cr.move_to(x1, y1)
            if self.commit_cols[i] != self.commit_cols[i + 1]:
                # curva bezier per branch divergenti
                mid_y = (y1 + y2) / 2
                cr.curve_to(x1, mid_y, x2, mid_y, x2, y2)
            else:
                cr.line_to(x2, y2)
            cr.stroke()

        # Disegna i nodi e le etichette
        for i, commit in enumerate(self.commits):
            col = self.commit_cols[i]
            nx, ny = self._node_pos(i, col)
            c = self._get_node_color(commit)

            # Riga hover alternata
            if i % 2 == 0:
                cr.set_source_rgba(1, 1, 1, 0.02)
                cr.rectangle(0, i * row_h, width, row_h)
                cr.fill()

            # Nodo (cerchio)
            cr.set_source_rgb(*c)
            cr.arc(nx, ny, self.NODE_R, 0, 6.2832)
            cr.fill()

            # Bordo nodo
            cr.set_source_rgba(1, 1, 1, 0.3)
            cr.set_line_width(1)
            cr.arc(nx, ny, self.NODE_R, 0, 6.2832)
            cr.stroke()

            # HEAD marker
            if commit["is_head"]:
                cr.set_source_rgb(*hex_to_rgb(HEAD_COLOR))
                cr.arc(nx, ny, self.NODE_R + 3, 0, 6.2832)
                cr.set_line_width(1.5)
                cr.stroke()

            text_x = nx + self.NODE_R + 8

            # Badge branch
            badge_x = text_x
            for b in commit["branches"]:
                bc = hex_to_rgb(self.branch_color_map.get(b, "#6C7086"))
                label = b if len(b) <= 18 else b[:16] + "…"
                # sfondo badge
                cr.set_source_rgba(bc[0], bc[1], bc[2], 0.25)
                badge_w = len(label) * 6.5 + 8
                cr.rectangle(badge_x - 2, ny - 9, badge_w, 17)
                cr.fill()
                # bordo badge
                cr.set_source_rgba(bc[0], bc[1], bc[2], 0.8)
                cr.set_line_width(1)
                cr.rectangle(badge_x - 2, ny - 9, badge_w, 17)
                cr.stroke()
                # testo badge
                cr.set_source_rgb(*bc)
                cr.select_font_face("Monospace", 0, 0)
                cr.set_font_size(9)
                cr.move_to(badge_x + 2, ny + 4)
                cr.show_text(label)
                badge_x += badge_w + 6

            # Hash + messaggio
            msg_x = max(badge_x, text_x + 4)
            cr.set_source_rgb(0.55, 0.57, 0.65)
            cr.select_font_face("Monospace", 0, 0)
            cr.set_font_size(9)
            cr.move_to(msg_x, ny - 2)
            cr.show_text(commit["hash"])

            cr.set_source_rgb(0.78, 0.80, 0.86)
            cr.set_font_size(10)
            cr.move_to(msg_x + 56, ny - 2)
            available = int((width - msg_x - 220) / 6.5)
            msg = commit["message"][:available] if available > 0 else ""
            cr.show_text(msg)

            # Author + date (right side)
            cr.set_source_rgb(0.50, 0.52, 0.60)
            cr.set_font_size(9)
            info = f"{commit['author']}  {commit['date']}"
            xbearing, ybearing, tw, th, dx, dy = cr.text_extents(info)
            cr.move_to(width - tw - 12, ny + 4)
            cr.show_text(info)

            # Linea separatore sottile
            cr.set_source_rgba(1, 1, 1, 0.04)
            cr.set_line_width(0.5)
            cr.move_to(0, (i + 1) * row_h)
            cr.line_to(width, (i + 1) * row_h)
            cr.stroke()


# ─── Finestra principale ───────────────────────────────────────────────────────
class GitGraphWindow(Gtk.Window):
    def __init__(self, path):
        super().__init__()
        self.set_title("Git Graph")
        self.set_default_size(900, 620)

        repo_name = os.path.basename(path)

        # Header bar
        header = Gtk.HeaderBar()
        header.set_title_widget(Gtk.Label(label=f"⎇ Git Graph — {repo_name}"))
        self.set_titlebar(header)

        # Loading spinner
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        spinner = Gtk.Spinner()
        spinner.start()
        box.append(spinner)
        self.set_child(box)

        # Carica dati in background
        threading.Thread(
            target=self._load, args=(path, repo_name, box, spinner), daemon=True
        ).start()

    def _load(self, path, repo_name, box, spinner):
        commits, branch_color_map = get_git_log(path)
        GLib.idle_add(self._build_ui, commits, branch_color_map, repo_name, box, spinner)

    def _build_ui(self, commits, branch_color_map, repo_name, box, spinner):
        spinner.stop()
        # Rimuovi spinner
        box.remove(spinner)

        if not commits:
            label = Gtk.Label(label="Nessun repository Git trovato in questa cartella.")
            label.set_margin_top(40)
            box.append(label)
            return

        # Legenda branch
        legend_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        legend_box.set_margin_start(12)
        legend_box.set_margin_top(8)
        legend_box.set_margin_bottom(4)

        for branch, color in branch_color_map.items():
            dot = Gtk.Label(label="●")
            dot.add_css_class("branch-dot")
            r, g, b = hex_to_rgb(color)
            dot_css = Gtk.CssProvider()
            dot_css.load_from_data(f"label {{ color: {color}; font-size: 14px; }}".encode())
            Gtk.StyleContext.add_provider_for_display(
                dot.get_display(), dot_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            lbl = Gtk.Label(label=branch)
            lbl_css = Gtk.CssProvider()
            lbl_css.load_from_data(b"label { font-size: 11px; color: #CDD6F4; }")
            Gtk.StyleContext.add_provider_for_display(
                lbl.get_display(), lbl_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            legend_box.append(dot)
            legend_box.append(lbl)

        box.append(legend_box)

        # ScrolledWindow con il grafo
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)

        graph = GitGraphWidget(commits, branch_color_map, repo_name)
        graph.set_hexpand(True)
        scroll.set_child(graph)
        box.append(scroll)

        # Stat bar
        stat = Gtk.Label(label=f"{len(commits)} commit  ·  {len(branch_color_map)} branch")
        stat.set_margin_bottom(6)
        css = Gtk.CssProvider()
        css.load_from_data(b"label { font-size: 10px; color: #6C7086; }")
        Gtk.StyleContext.add_provider_for_display(
            stat.get_display(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        box.append(stat)


# ─── Estensione Nautilus ───────────────────────────────────────────────────────
class GitGraphExtension(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self):
        super().__init__()

    def _get_git_root(self, path):
        root = run_git(["rev-parse", "--show-toplevel"], cwd=path)
        return root if root else None

    def get_background_items(self, current_folder):
        if current_folder is None:
            return []
        path = unquote(urlparse(current_folder.get_uri()).path)
        if not self._get_git_root(path):
            return []
        return self._make_menu(path)

    def get_file_items(self, files):
        if len(files) != 1:
            return []
        f = files[0]
        if f.get_file_type() != Nautilus.FileType.DIRECTORY:
            return []
        path = unquote(urlparse(f.get_uri()).path)
        if not self._get_git_root(path):
            return []
        return self._make_menu(path)

    def _make_menu(self, path):
        item = Nautilus.MenuItem(
            name="GitGraph::ShowGraph",
            label="⎇  Mostra Git Graph…",
            tip="Visualizza la storia dei commit e dei branch Git",
        )
        item.connect("activate", lambda *_: self._open_window(path))
        return [item]

    def _open_window(self, path):
        win = GitGraphWindow(path)
        win.present()
