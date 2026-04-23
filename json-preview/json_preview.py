"""
json_preview.py — Nautilus extension for JSON and JSONL preview
================================================================
Adds "Anteprima JSON" to the right-click menu on .json and .jsonl files.
Shows tree structure, inferred schema, data preview, and statistics.

Installation:
    cp json_preview.py ~/.local/share/nautilus-python/extensions/
    nautilus -q && nautilus

Dependencies: Python stdlib only
Optional: sudo apt install python3-pandas  (statistics on JSONL)
"""

import collections
import gzip
import json
import logging
import os
import threading

import gi

gi.require_version("Nautilus", "4.0")
gi.require_version("Gtk", "4.0")
gi.require_version("GLib", "2.0")

from gi.repository import GLib, GObject, Gtk, Nautilus, Pango

PANDAS_AVAILABLE = False
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    pass


# --------------------------------------------------------------------------- #
# Costanti
# --------------------------------------------------------------------------- #

PREVIEW_ROWS = 100
MAX_READ_BYTES = 50 * 1024 * 1024  # 50MB
MAX_TREE_DEPTH = 8  # profondità massima albero
WINDOW_W = 1100
WINDOW_H = 700
MIN_COL_WIDTH = 80
MAX_COL_WIDTH = 350

# Colori per tipo JSON
TYPE_COLORS = {
    "string": "#22863a",  # verde
    "number": "#0366d6",  # blu
    "boolean": "#e36209",  # arancione
    "null": "#b31d28",  # rosso
    "object": "#6f42c1",  # viola
    "array": "#6f42c1",  # viola
}

CSS = b"""
.js-info-bar {
    background-color: #f6f8fa;
    border-bottom: 1px solid #e1e4e8;
    padding: 6px 12px;
}
.js-stat-box {
    background-color: #ffffff;
    border: 1px solid #e1e4e8;
    border-radius: 6px;
    padding: 8px 14px;
    margin: 4px;
}
.js-stat-title { font-size: 11px; color: #6a737d; }
.js-stat-value { font-size: 15px; font-weight: bold; color: #24292e; }
.mono { font-family: monospace; font-size: 13px; }
.type-string  { color: #22863a; }
.type-number  { color: #0366d6; }
.type-boolean { color: #e36209; }
.type-null    { color: #b31d28; }
.type-object  { color: #6f42c1; }
"""


# --------------------------------------------------------------------------- #
# Utilità
# --------------------------------------------------------------------------- #


def fmt_size(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def json_type(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return "unknown"


def type_color(t: str) -> str:
    return TYPE_COLORS.get(t, "#24292e")


def infer_schema(value, depth=0, max_depth=4) -> dict:
    """
    Inferisce lo schema ricorsivo di un valore JSON.
    Ritorna un dict con 'type', 'children' (per oggetti), 'item_type' (per array).
    """
    t = json_type(value)
    schema = {"type": t}

    if depth >= max_depth:
        return schema

    if t == "object" and value:
        schema["children"] = {}
        for k, v in value.items():
            schema["children"][k] = infer_schema(v, depth + 1, max_depth)

    elif t == "array" and value:
        schema["length"] = len(value)
        # Campiona il primo elemento per il tipo degli item
        schema["item_schema"] = infer_schema(value[0], depth + 1, max_depth)

    return schema


def merge_schemas(schemas: list) -> dict:
    """
    Unisce più schema (da più oggetti JSONL) in uno schema comune.
    Segna i campi non presenti in tutti gli oggetti come opzionali.
    """
    if not schemas:
        return {}

    merged = {}
    total = len(schemas)

    # Raccoglie tutti i campi
    all_keys = set()
    for s in schemas:
        if s.get("type") == "object" and "children" in s:
            all_keys.update(s["children"].keys())

    for key in all_keys:
        present = [
            s
            for s in schemas
            if s.get("type") == "object" and "children" in s and key in s["children"]
        ]
        count = len(present)

        # Tipo più frequente per questo campo
        type_counts = collections.Counter(p["children"][key]["type"] for p in present)
        dominant_type = type_counts.most_common(1)[0][0]

        merged[key] = {
            "type": dominant_type,
            "count": count,
            "total": total,
            "optional": count < total,
            "children": {},
        }

    return {"type": "object", "children": merged, "total": total}


# --------------------------------------------------------------------------- #
# File reading
# --------------------------------------------------------------------------- #


def read_json_file(path: str, compressed: bool = False) -> dict:
    """Legge un file JSON standard, con supporto gzip trasparente."""
    result = {"format": "json", "path": path}
    file_size = os.path.getsize(path)
    result["file_size"] = fmt_size(file_size)
    result["truncated"] = not compressed and file_size > MAX_READ_BYTES

    try:
        opener = (
            gzip.open(path, "rt", encoding="utf-8", errors="replace")
            if compressed
            else open(path, encoding="utf-8", errors="replace")
        )
        with opener as f:
            raw = f.read(MAX_READ_BYTES)

        data = json.loads(raw)
    except json.JSONDecodeError as e:
        result["error"] = f"JSON non valido: {e}"
        return result
    except OSError as e:
        result["error"] = str(e)
        return result

    result["data"] = data
    result["root_type"] = json_type(data)
    result["schema"] = infer_schema(data, max_depth=MAX_TREE_DEPTH)

    if isinstance(data, list):
        result["num_items"] = len(data)
        result["preview_rows"] = data[:PREVIEW_ROWS]
        # Schema unificato dai primi N oggetti
        obj_samples = [x for x in data[:50] if isinstance(x, dict)]
        if obj_samples:
            schemas = [infer_schema(o, max_depth=3) for o in obj_samples]
            result["merged_schema"] = merge_schemas(schemas)
    elif isinstance(data, dict):
        result["num_keys"] = len(data)

    return result


def read_jsonl_file(path: str, compressed: bool = False) -> dict:
    """Legge un file JSONL (una riga = un oggetto JSON), con supporto gzip trasparente."""
    result = {"format": "jsonl", "path": path}
    file_size = os.path.getsize(path)
    result["file_size"] = fmt_size(file_size)

    rows = []
    total_lines = 0
    errors = 0
    schemas = []

    try:
        bytes_read = 0
        opener = (
            gzip.open(path, "rt", encoding="utf-8", errors="replace")
            if compressed
            else open(path, encoding="utf-8", errors="replace")
        )
        with opener as f:
            for line in f:
                bytes_read += len(line.encode("utf-8"))
                line = line.strip()
                if not line:
                    continue
                total_lines += 1
                try:
                    obj = json.loads(line)
                    if total_lines <= PREVIEW_ROWS:
                        rows.append(obj)
                    if total_lines <= 200:
                        schemas.append(infer_schema(obj, max_depth=3))
                except json.JSONDecodeError:
                    errors += 1
                if bytes_read >= MAX_READ_BYTES:
                    result["truncated"] = True
                    break
    except OSError as e:
        result["error"] = str(e)
        return result

    result["total_lines"] = total_lines
    result["parse_errors"] = errors
    result["preview_rows"] = rows
    result["truncated"] = result.get("truncated", False)

    if schemas:
        result["merged_schema"] = merge_schemas(schemas)
        result["schema"] = result["merged_schema"]

    # Statistiche con pandas se disponibile
    if PANDAS_AVAILABLE and rows:
        try:
            df = pd.DataFrame(rows)
            result["df"] = df
            result["numeric_cols"] = list(df.select_dtypes(include="number").columns)
            result["null_counts"] = df.isnull().sum().to_dict()
            if result["numeric_cols"]:
                result["describe"] = df[result["numeric_cols"]].describe()
        except Exception as e:
            logging.debug("DataFrame analysis failed: %s", e)

    return result


def is_gzipped(path: str) -> bool:
    """Controlla la magic number per rilevare file gzip."""
    try:
        with open(path, "rb") as f:
            return f.read(2) == b"\x1f\x8b"
    except OSError:
        return False


def load_json(path: str) -> dict:
    name = os.path.basename(path).lower()
    compressed = is_gzipped(path)

    # Rimuovi .gz per determinare il formato sottostante
    base_name = name[:-3] if name.endswith(".gz") else name

    if base_name.endswith(".jsonl") or base_name.endswith(".ndjson"):
        result = read_jsonl_file(path, compressed=compressed)
    else:
        result = read_json_file(path, compressed=compressed)

    if compressed:
        result["file_size"] = fmt_size(os.path.getsize(path)) + " (gzip)"
    return result


# --------------------------------------------------------------------------- #
# Finestra
# --------------------------------------------------------------------------- #


class JsonPreviewWindow(Gtk.Window):
    def __init__(self, path: str):
        filename = os.path.basename(path)
        super().__init__(title=f"{filename} — JSON Preview")
        self.set_default_size(WINDOW_W, WINDOW_H)
        self._path = path

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self._build_skeleton()
        threading.Thread(target=self._load, daemon=True).start()

    def _build_skeleton(self):
        self._root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(self._root)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        box.set_vexpand(True)
        spinner = Gtk.Spinner()
        spinner.set_size_request(48, 48)
        spinner.start()
        lbl = Gtk.Label(label="Lettura file JSON...")
        lbl.add_css_class("dim-label")
        box.append(spinner)
        box.append(lbl)
        self._spinner_box = box
        self._root.append(box)

    def _load(self):
        data = load_json(self._path)
        GLib.idle_add(self._on_loaded, data)

    def _on_loaded(self, data):
        self._root.remove(self._spinner_box)
        if data.get("error"):
            lbl = Gtk.Label(label=f"Errore: {data['error']}")
            lbl.set_margin_top(40)
            self._root.append(lbl)
            return False
        self._build_content(data)
        return False

    # ------------------------------------------------------------------ #
    # Layout principale
    # ------------------------------------------------------------------ #

    def _build_content(self, data: dict):
        fmt = data["format"]

        # --- Info bar ---
        info_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        info_bar.add_css_class("js-info-bar")
        info_bar.set_margin_start(4)
        info_bar.set_margin_end(8)

        self._stat(info_bar, "Formato", "JSONL" if fmt == "jsonl" else "JSON")
        self._stat(info_bar, "Dimensione", data.get("file_size", "?"))

        if fmt == "jsonl":
            self._stat(info_bar, "Righe totali", f"{data.get('total_lines', 0):,}")
            if data.get("parse_errors", 0) > 0:
                self._stat(info_bar, "⚠ Errori parse", str(data["parse_errors"]))
        else:
            root_type = data.get("root_type", "?")
            self._stat(info_bar, "Tipo radice", root_type)
            if root_type == "array":
                self._stat(info_bar, "Elementi", f"{data.get('num_items', 0):,}")
            elif root_type == "object":
                self._stat(info_bar, "Chiavi", str(data.get("num_keys", 0)))

        if data.get("truncated"):
            t = Gtk.Label(label="⚠ File troncato a 50MB")
            t.add_css_class("dim-label")
            t.set_hexpand(True)
            t.set_halign(Gtk.Align.END)
            info_bar.append(t)

        self._root.append(info_bar)
        self._root.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # --- Notebook ---
        notebook = Gtk.Notebook()
        notebook.set_vexpand(True)
        self._root.append(notebook)

        # Tab Struttura — sempre presente
        notebook.append_page(self._tab_tree(data), Gtk.Label(label="🌳 Struttura"))

        # Tab Schema — per JSONL o JSON con array di oggetti
        merged = data.get("merged_schema") or data.get("schema")
        if merged and merged.get("type") == "object" and merged.get("children"):
            notebook.append_page(self._tab_schema(merged), Gtk.Label(label="🗂 Schema"))

        # Tab Dati — per JSONL o JSON array
        preview = data.get("preview_rows")
        if preview:
            notebook.append_page(
                self._tab_data(preview, data),
                Gtk.Label(label=f"📊 Dati (prime {min(len(preview), PREVIEW_ROWS)} righe)"),
            )

        # Tab Statistiche — solo con pandas e colonne numeriche
        if data.get("describe") is not None:
            notebook.append_page(self._tab_stats(data), Gtk.Label(label="📈 Statistiche"))

        # Tab Raw — sorgente formattato
        notebook.append_page(self._tab_raw(data), Gtk.Label(label="{ } Raw"))

        # --- Bottom bar ---
        bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bottom.set_margin_start(8)
        bottom.set_margin_end(8)
        bottom.set_margin_top(6)
        bottom.set_margin_bottom(6)

        path_lbl = Gtk.Label(label=self._path)
        path_lbl.add_css_class("dim-label")
        path_lbl.set_ellipsize(Pango.EllipsizeMode.START)
        path_lbl.set_hexpand(True)
        path_lbl.set_halign(Gtk.Align.START)
        bottom.append(path_lbl)

        import subprocess

        open_btn = Gtk.Button(label="Apri nell'editor")
        open_btn.connect("clicked", lambda _: subprocess.Popen(["xdg-open", self._path]))
        bottom.append(open_btn)

        self._root.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        self._root.append(bottom)

    # ------------------------------------------------------------------ #
    # Tab Struttura ad albero
    # ------------------------------------------------------------------ #

    def _tab_tree(self, data: dict) -> Gtk.Widget:
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        # TreeStore: chiave, tipo, valore/preview, colore tipo
        store = Gtk.TreeStore(str, str, str, str)

        raw = data.get("data")
        if raw is not None:
            self._fill_tree(store, None, raw, depth=0)
        elif data.get("preview_rows"):
            # JSONL: mostra i primi oggetti come nodi radice
            for i, row in enumerate(data["preview_rows"][:20]):
                it = store.append(None, [f"[{i}]", "object", "{…}", type_color("object")])
                self._fill_tree(store, it, row, depth=1)

        tv = Gtk.TreeView(model=store)
        tv.set_headers_visible(True)
        tv.add_css_class("mono")

        # Colonna chiave
        r = Gtk.CellRendererText()
        r.set_property("weight", Pango.Weight.BOLD)
        c = Gtk.TreeViewColumn("Chiave / Indice", r, text=0)
        c.set_resizable(True)
        c.set_min_width(200)
        tv.append_column(c)

        # Colonna tipo con colore
        r = Gtk.CellRendererText()
        c = Gtk.TreeViewColumn("Tipo")
        c.pack_start(r, True)
        c.set_min_width(90)

        def set_type(col, cell, model, it, _):
            t = model.get_value(it, 1)
            cell.set_property("text", t)
            cell.set_property("foreground", type_color(t))

        c.set_cell_data_func(r, set_type, None)
        tv.append_column(c)

        # Colonna valore
        r = Gtk.CellRendererText()
        r.set_property("ellipsize", Pango.EllipsizeMode.END)
        c = Gtk.TreeViewColumn("Valore", r, text=2)
        c.set_resizable(True)
        c.set_expand(True)
        tv.append_column(c)

        # Espandi primo livello
        tv.expand_to_path(Gtk.TreePath.new_first())

        scrolled.set_child(tv)
        return scrolled

    def _fill_tree(self, store, parent, value, depth: int):
        if depth > MAX_TREE_DEPTH:
            store.append(parent, ["…", "", "(profondità massima)", "#6a737d"])
            return

        t = json_type(value)

        if t == "object":
            for k, v in value.items():
                child_type = json_type(v)
                preview = self._value_preview(v)
                it = store.append(parent, [str(k), child_type, preview, type_color(child_type)])
                if child_type in ("object", "array"):
                    self._fill_tree(store, it, v, depth + 1)

        elif t == "array":
            for i, v in enumerate(value[:50]):
                child_type = json_type(v)
                preview = self._value_preview(v)
                it = store.append(parent, [f"[{i}]", child_type, preview, type_color(child_type)])
                if child_type in ("object", "array"):
                    self._fill_tree(store, it, v, depth + 1)
            if len(value) > 50:
                store.append(parent, [f"… altri {len(value) - 50}", "", "", "#6a737d"])

        else:
            store.append(parent, ["(valore)", t, self._value_preview(value), type_color(t)])

    def _value_preview(self, value) -> str:
        t = json_type(value)
        if t == "null":
            return "null"
        if t == "boolean":
            return str(value).lower()
        if t == "number":
            return str(value)
        if t == "string":
            s = str(value)
            return s[:80] + "…" if len(s) > 80 else s
        if t == "object":
            return f"{{ {len(value)} chiavi }}"
        if t == "array":
            return f"[ {len(value)} elementi ]"
        return str(value)

    # ------------------------------------------------------------------ #
    # Tab Schema
    # ------------------------------------------------------------------ #

    def _tab_schema(self, schema: dict) -> Gtk.Widget:
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        children = schema.get("children", {})
        total = schema.get("total", 0)

        store = Gtk.ListStore(str, str, str, str)
        for field, info in children.items():
            t = info.get("type", "?")
            count = info.get("count", total)
            if total > 0:
                pct = count / total * 100
                presence = f"{count:,}/{total:,} ({pct:.0f}%)"
            else:
                presence = "—"
            optional = "⚠ opzionale" if info.get("optional") else "✓ sempre presente"
            store.append([field, t, presence, optional])

        tv = Gtk.TreeView(model=store)
        tv.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        tv.add_css_class("mono")

        # Campo
        r = Gtk.CellRendererText()
        r.set_property("weight", Pango.Weight.BOLD)
        c = Gtk.TreeViewColumn("Campo", r, text=0)
        c.set_resizable(True)
        c.set_min_width(180)
        tv.append_column(c)

        # Tipo con colore
        r = Gtk.CellRendererText()
        c = Gtk.TreeViewColumn("Tipo")
        c.pack_start(r, True)
        c.set_min_width(100)

        def set_type(col, cell, model, it, _):
            t = model.get_value(it, 1)
            cell.set_property("text", t)
            cell.set_property("foreground", type_color(t))

        c.set_cell_data_func(r, set_type, None)
        tv.append_column(c)

        # Presenza (solo per JSONL)
        if total > 1:
            r = Gtk.CellRendererText()
            c = Gtk.TreeViewColumn("Presenza", r, text=2)
            c.set_min_width(160)
            tv.append_column(c)

            r = Gtk.CellRendererText()
            c = Gtk.TreeViewColumn("", r, text=3)
            c.set_min_width(160)

            def set_optional(col, cell, model, it, _):
                val = model.get_value(it, 3)
                cell.set_property("text", val)
                cell.set_property("foreground", "#22863a" if "✓" in val else "#e36209")

            c.set_cell_data_func(r, set_optional, None)
            tv.append_column(c)

        scrolled.set_child(tv)
        return scrolled

    # ------------------------------------------------------------------ #
    # Tab Dati (tabella per array/JSONL)
    # ------------------------------------------------------------------ #

    def _tab_data(self, rows: list, data: dict) -> Gtk.Widget:
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        if not rows:
            scrolled.set_child(Gtk.Label(label="Nessun dato da mostrare."))
            return scrolled

        # Determina le colonne dai primi oggetti
        if isinstance(rows[0], dict):
            headers = list(
                dict.fromkeys(k for row in rows[:20] if isinstance(row, dict) for k in row.keys())
            )
        else:
            # Array di valori scalari
            headers = ["valore"]
            rows = [{"valore": r} for r in rows]

        numeric_cols = data.get("numeric_cols", [])
        col_types_list = [str] * len(headers)
        store = Gtk.ListStore(*col_types_list)

        for row in rows:
            if isinstance(row, dict):
                vals = [str(row.get(h, "")) for h in headers]
            else:
                vals = [str(row)]
            store.append(vals)

        tv = Gtk.TreeView(model=store)
        tv.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
        tv.add_css_class("mono")

        for i, h in enumerate(headers):
            r = Gtk.CellRendererText()
            r.set_property("ellipsize", Pango.EllipsizeMode.END)
            if h in numeric_cols:
                r.set_property("xalign", 1.0)
                r.set_property("foreground", type_color("number"))

            c = Gtk.TreeViewColumn()
            c.pack_start(r, True)
            c.add_attribute(r, "text", i)
            c.set_resizable(True)
            c.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
            c.set_fixed_width(max(MIN_COL_WIDTH, min(MAX_COL_WIDTH, len(h) * 11 + 24)))
            c.set_sort_column_id(i)

            lbl = Gtk.Label(label=h)
            lbl.set_markup(f"<b>{GLib.markup_escape_text(h)}</b>")
            lbl.show()
            c.set_widget(lbl)
            tv.append_column(c)

        scrolled.set_child(tv)
        return scrolled

    # ------------------------------------------------------------------ #
    # Tab Statistiche
    # ------------------------------------------------------------------ #

    def _tab_stats(self, data: dict) -> Gtk.Widget:
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        outer.set_margin_start(16)
        outer.set_margin_end(16)
        outer.set_margin_top(12)
        outer.set_margin_bottom(12)

        desc = data["describe"]
        numeric_cols = data["numeric_cols"]

        title = Gtk.Label()
        title.set_markup("<b>Statistiche descrittive (colonne numeriche)</b>")
        title.set_halign(Gtk.Align.START)
        outer.append(title)

        col_types_list = [str] * (len(numeric_cols) + 1)
        store = Gtk.ListStore(*col_types_list)
        for stat in desc.index:
            row = [stat] + [f"{desc.loc[stat, col]:.4g}" for col in numeric_cols]
            store.append(row)

        tv = Gtk.TreeView(model=store)
        tv.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        tv.add_css_class("mono")

        r = Gtk.CellRendererText()
        r.set_property("weight", Pango.Weight.BOLD)
        c = Gtk.TreeViewColumn("Statistica", r, text=0)
        c.set_min_width(100)
        tv.append_column(c)

        for i, col in enumerate(numeric_cols):
            r = Gtk.CellRendererText()
            r.set_property("xalign", 1.0)
            r.set_property("foreground", type_color("number"))
            c = Gtk.TreeViewColumn(col, r, text=i + 1)
            c.set_resizable(True)
            c.set_min_width(MIN_COL_WIDTH)
            tv.append_column(c)

        outer.append(tv)

        # Valori nulli
        null_counts = data.get("null_counts", {})
        nulls = {k: v for k, v in null_counts.items() if v > 0}
        null_title = Gtk.Label()
        null_title.set_markup("<b>Valori nulli</b>")
        null_title.set_halign(Gtk.Align.START)
        null_title.set_margin_top(12)
        outer.append(null_title)

        if nulls:
            total = data.get("total_lines", len(data.get("preview_rows", [])))
            for col, count in nulls.items():
                pct = count / total * 100 if total else 0
                row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                col_lbl = Gtk.Label(label=col)
                col_lbl.set_width_chars(24)
                col_lbl.set_halign(Gtk.Align.START)
                val_lbl = Gtk.Label(label=f"{count:,} ({pct:.1f}%)")
                val_lbl.add_css_class("dim-label")
                row_box.append(col_lbl)
                row_box.append(val_lbl)
                outer.append(row_box)
        else:
            ok = Gtk.Label(label="✓ Nessun valore nullo")
            ok.set_halign(Gtk.Align.START)
            outer.append(ok)

        scrolled.set_child(outer)
        return scrolled

    # ------------------------------------------------------------------ #
    # Tab Raw
    # ------------------------------------------------------------------ #

    def _tab_raw(self, data: dict) -> Gtk.Widget:
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        tv = Gtk.TextView()
        tv.set_editable(False)
        tv.set_monospace(True)
        tv.set_margin_start(12)
        tv.set_margin_top(8)

        buf = tv.get_buffer()

        if data["format"] == "jsonl":
            # Mostra le prime righe formattate
            lines = []
            for row in (data.get("preview_rows") or [])[:20]:
                lines.append(json.dumps(row, indent=2, ensure_ascii=False))
                lines.append("")
            buf.set_text("\n".join(lines))
        else:
            raw = data.get("data")
            if raw is not None:
                try:
                    formatted = json.dumps(raw, indent=2, ensure_ascii=False)
                    # Limita a 200KB per non bloccare GTK
                    if len(formatted) > 200_000:
                        formatted = formatted[:200_000] + "\n\n… (troncato per la visualizzazione)"
                    buf.set_text(formatted)
                except Exception as e:
                    buf.set_text(f"Errore nella formattazione: {e}")

        scrolled.set_child(tv)
        return scrolled

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _stat(self, box, title, value):
        sb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        sb.add_css_class("js-stat-box")
        t = Gtk.Label(label=title)
        t.add_css_class("js-stat-title")
        t.set_halign(Gtk.Align.START)
        v = Gtk.Label(label=str(value))
        v.add_css_class("js-stat-value")
        v.set_halign(Gtk.Align.START)
        sb.append(t)
        sb.append(v)
        box.append(sb)


# --------------------------------------------------------------------------- #
# Extension
# --------------------------------------------------------------------------- #


class JsonPreviewExtension(GObject.GObject, Nautilus.MenuProvider):
    def get_file_items(self, files):
        if len(files) != 1:
            return []
        f = files[0]
        name = f.get_name().lower()
        # Supporta anche versioni .gz (es. data.json.gz, events.jsonl.gz)
        base = name[:-3] if name.endswith(".gz") else name
        is_json = base.endswith(".json")
        is_jsonl = base.endswith(".jsonl") or base.endswith(".ndjson")
        if not (is_json or is_jsonl):
            return []

        fmt = "JSONL" if is_jsonl else "JSON"
        if name.endswith(".gz"):
            fmt += ".gz"
        item = Nautilus.MenuItem(
            name="JsonPreview::show",
            label=f"Anteprima {fmt}",
            tip=f"Mostra struttura e dati di {f.get_name()}",
        )
        item.connect("activate", self._on_activate, f.get_location().get_path())
        return [item]

    def get_background_items(self, folder):
        return []

    def _on_activate(self, _item, path):
        win = JsonPreviewWindow(path)
        win.present()
