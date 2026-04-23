"""
parquet_preview.py — Estensione Nautilus per anteprima file Parquet
====================================================================
Aggiunge una voce "Anteprima Parquet" nel menu tasto destro su file .parquet
Mostra schema, metadati, row groups e anteprima dati.

Installazione:
    cp parquet_preview.py ~/.local/share/nautilus-python/extensions/
    nautilus -q && nautilus

Dipendenze:
    sudo apt install python3-pandas
    pip install pyarrow --break-system-packages
"""

import os
import threading

import gi

gi.require_version("Nautilus", "4.0")
gi.require_version("Gtk", "4.0")
gi.require_version("GLib", "2.0")

from gi.repository import GLib, GObject, Gtk, Nautilus, Pango

try:
    import pandas as pd  # noqa: F401 — required by pyarrow .to_pandas()
    import pyarrow.parquet as pq

    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False


# --------------------------------------------------------------------------- #
# Costanti
# --------------------------------------------------------------------------- #

PREVIEW_ROWS = 100
MIN_COL_WIDTH = 80
MAX_COL_WIDTH = 300
WINDOW_W = 1100
WINDOW_H = 680

# Mappa colori per tipo di dato
DTYPE_COLORS = {
    "int": "#0366d6",  # blu — interi
    "float": "#6f42c1",  # viola — float
    "double": "#6f42c1",
    "timestamp": "#e36209",  # arancione — date
    "date": "#e36209",
    "bool": "#22863a",  # verde — booleani
    "string": "#24292e",  # nero — stringhe
    "binary": "#b31d28",  # rosso — binari
    "list": "#6a737d",  # grigio — complessi
    "struct": "#6a737d",
}

CSS = b"""
.pq-info-bar {
    background-color: #f6f8fa;
    border-bottom: 1px solid #e1e4e8;
    padding: 6px 12px;
}
.pq-stat-box {
    background-color: #ffffff;
    border: 1px solid #e1e4e8;
    border-radius: 6px;
    padding: 8px 14px;
    margin: 4px;
}
.pq-stat-title {
    font-size: 11px;
    color: #6a737d;
}
.pq-stat-value {
    font-size: 15px;
    font-weight: bold;
    color: #24292e;
}
.pq-section-title {
    font-weight: bold;
    font-size: 13px;
    margin-top: 8px;
    margin-bottom: 4px;
}
.mono {
    font-family: monospace;
    font-size: 13px;
}
.tag-int     { color: #0366d6; }
.tag-float   { color: #6f42c1; }
.tag-ts      { color: #e36209; }
.tag-bool    { color: #22863a; }
.tag-string  { color: #24292e; }
.tag-binary  { color: #b31d28; }
.tag-other   { color: #6a737d; }
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


def dtype_color(dtype_str: str) -> str:
    s = str(dtype_str).lower()
    for key, color in DTYPE_COLORS.items():
        if key in s:
            return color
    return "#24292e"


def dtype_short(dtype) -> str:
    """Versione corta leggibile del tipo pyarrow."""
    s = str(dtype)
    # Accorcia tipi lunghi
    replacements = [
        ("timestamp[us, tz=UTC]", "timestamp"),
        ("timestamp[us]", "timestamp"),
        ("timestamp[ns]", "timestamp"),
        ("large_string", "string"),
        ("large_binary", "binary"),
        ("dictionary<values=string, indices=int32, ordered=0>", "categorical"),
    ]
    for long, short in replacements:
        s = s.replace(long, short)
    return s


# --------------------------------------------------------------------------- #
# Lettura Parquet
# --------------------------------------------------------------------------- #


def read_parquet(path: str, max_rows: int) -> dict:
    """
    Legge il file Parquet e ritorna un dict con tutti i dati necessari.
    """
    result = {}
    try:
        pf = pq.ParquetFile(path)
        meta = pf.metadata
        schema = pf.schema_arrow

        # Metadati generali
        result["num_rows"] = meta.num_rows
        result["num_columns"] = meta.num_columns
        result["num_row_groups"] = meta.num_row_groups
        result["format_version"] = meta.format_version
        result["created_by"] = meta.created_by or "sconosciuto"
        result["file_size"] = fmt_size(os.path.getsize(path))

        # Calcola dimensione decompressa stimata
        total_compressed = 0
        total_uncompressed = 0
        codecs = set()
        rg_info = []

        for rg_idx in range(meta.num_row_groups):
            rg = meta.row_group(rg_idx)
            rg_compressed = 0
            rg_uncompressed = 0
            for col_idx in range(rg.num_columns):
                col_chunk = rg.column(col_idx)
                rg_compressed += col_chunk.total_compressed_size
                rg_uncompressed += col_chunk.total_uncompressed_size
                codecs.add(col_chunk.compression)
            total_compressed += rg_compressed
            total_uncompressed += rg_uncompressed
            rg_info.append(
                {
                    "index": rg_idx,
                    "num_rows": rg.num_rows,
                    "compressed": fmt_size(rg_compressed),
                    "uncompressed": fmt_size(rg_uncompressed),
                }
            )

        result["compressed_size"] = fmt_size(total_compressed)
        result["uncompressed_size"] = fmt_size(total_uncompressed)
        result["codecs"] = ", ".join(sorted(codecs)) or "nessuno"
        result["row_groups"] = rg_info

        # Schema colonne
        columns = []
        for i, field in enumerate(schema):
            columns.append(
                {
                    "index": i,
                    "name": field.name,
                    "type": dtype_short(field.type),
                    "nullable": field.nullable,
                }
            )
        result["columns"] = columns

        # Metadati custom (es. pandas metadata)
        custom_meta = {}
        if meta.metadata:
            for k, v in meta.metadata.items():
                key = k.decode("utf-8") if isinstance(k, bytes) else str(k)
                if key == "pandas":
                    custom_meta["pandas"] = "(presente)"
                else:
                    val = v.decode("utf-8") if isinstance(v, bytes) else str(v)
                    if len(val) < 200:
                        custom_meta[key] = val
        result["custom_meta"] = custom_meta

        # Leggi solo le prime N righe senza caricare l'intero file in RAM
        first_batch = next(pf.iter_batches(batch_size=max_rows), None)
        if first_batch is not None:
            df = first_batch.to_pandas()
        else:
            # Tabella vuota: costruisci un DataFrame vuoto con lo schema corretto
            df = schema.empty_table().to_pandas()
        result["total_rows_read"] = len(df)
        result["df_preview"] = df
        result["df_full"] = df

        # Statistiche descrittive (solo sulle righe caricate)
        numeric_cols = list(df.select_dtypes(include="number").columns)
        result["numeric_cols"] = numeric_cols
        if numeric_cols:
            result["describe"] = df[numeric_cols].describe()

        # Valori nulli
        result["null_counts"] = df.isnull().sum().to_dict()

    except Exception as e:
        result["error"] = str(e)

    return result


# --------------------------------------------------------------------------- #
# Finestra preview
# --------------------------------------------------------------------------- #


class ParquetPreviewWindow(Gtk.Window):
    def __init__(self, parquet_path: str):
        filename = os.path.basename(parquet_path)
        super().__init__(title=f"{filename} — Parquet Preview")
        self.set_default_size(WINDOW_W, WINDOW_H)
        self._path = parquet_path

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self._build_skeleton()
        threading.Thread(target=self._load, daemon=True).start()

    # ------------------------------------------------------------------ #
    # Scheletro con spinner
    # ------------------------------------------------------------------ #

    def _build_skeleton(self):
        self._root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(self._root)

        self._spinner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._spinner_box.set_valign(Gtk.Align.CENTER)
        self._spinner_box.set_halign(Gtk.Align.CENTER)
        self._spinner_box.set_vexpand(True)
        spinner = Gtk.Spinner()
        spinner.set_size_request(48, 48)
        spinner.start()
        lbl = Gtk.Label(label="Lettura file Parquet...")
        lbl.add_css_class("dim-label")
        self._spinner_box.append(spinner)
        self._spinner_box.append(lbl)
        self._root.append(self._spinner_box)

    # ------------------------------------------------------------------ #
    # Caricamento in thread
    # ------------------------------------------------------------------ #

    def _load(self):
        data = read_parquet(self._path, PREVIEW_ROWS)
        GLib.idle_add(self._on_loaded, data)

    def _on_loaded(self, data):
        self._root.remove(self._spinner_box)
        if "error" in data:
            err_lbl = Gtk.Label(label=f"Errore nella lettura:\n{data['error']}")
            err_lbl.set_margin_top(40)
            self._root.append(err_lbl)
            return False

        self._build_content(data)
        return False

    # ------------------------------------------------------------------ #
    # Contenuto principale
    # ------------------------------------------------------------------ #

    def _build_content(self, data: dict):

        # --- Info bar superiore ---
        info_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        info_bar.add_css_class("pq-info-bar")
        info_bar.set_margin_start(4)
        info_bar.set_margin_end(8)

        self._stat(info_bar, "Righe", f"{data['num_rows']:,}")
        self._stat(info_bar, "Colonne", str(data["num_columns"]))
        self._stat(info_bar, "Row Groups", str(data["num_row_groups"]))
        self._stat(info_bar, "Compresso", data["compressed_size"])
        self._stat(info_bar, "Originale", data["uncompressed_size"])
        self._stat(info_bar, "Codec", data["codecs"])
        self._stat(info_bar, "File", data["file_size"])

        self._root.append(info_bar)
        self._root.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # --- Notebook ---
        notebook = Gtk.Notebook()
        notebook.set_vexpand(True)
        self._root.append(notebook)

        notebook.append_page(self._tab_data(data), Gtk.Label(label="📊 Dati"))
        notebook.append_page(self._tab_schema(data), Gtk.Label(label="🗂 Schema"))
        if data.get("numeric_cols"):
            notebook.append_page(self._tab_stats(data), Gtk.Label(label="📈 Statistiche"))
        notebook.append_page(self._tab_metadata(data), Gtk.Label(label="ℹ Metadati"))

        # --- Barra inferiore ---
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

        self._root.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        self._root.append(bottom)

    def _stat(self, box, title, value):
        sb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        sb.add_css_class("pq-stat-box")
        t = Gtk.Label(label=title)
        t.add_css_class("pq-stat-title")
        t.set_halign(Gtk.Align.START)
        v = Gtk.Label(label=str(value))
        v.add_css_class("pq-stat-value")
        v.set_halign(Gtk.Align.START)
        sb.append(t)
        sb.append(v)
        box.append(sb)

    # ------------------------------------------------------------------ #
    # Tab Dati
    # ------------------------------------------------------------------ #

    def _tab_data(self, data: dict) -> Gtk.Widget:
        df = data["df_preview"]
        headers = list(df.columns)
        rows = df.astype(str).values.tolist()
        numeric_cols = data.get("numeric_cols", [])

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        col_types = [str] * len(headers)
        store = Gtk.ListStore(*col_types)
        for row in rows:
            store.append(row)

        tv = Gtk.TreeView(model=store)
        tv.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
        tv.add_css_class("mono")

        for i, h in enumerate(headers):
            renderer = Gtk.CellRendererText()
            renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
            color = dtype_color(data["columns"][i]["type"] if i < len(data["columns"]) else "")
            renderer.set_property("foreground", color)
            if h in numeric_cols:
                renderer.set_property("xalign", 1.0)

            col = Gtk.TreeViewColumn()
            col.pack_start(renderer, True)
            col.add_attribute(renderer, "text", i)
            col.set_resizable(True)
            col.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
            col.set_fixed_width(max(MIN_COL_WIDTH, min(MAX_COL_WIDTH, len(h) * 11 + 24)))
            col.set_sort_column_id(i)

            # Header con tipo
            col_type = data["columns"][i]["type"] if i < len(data["columns"]) else ""
            header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            name_lbl = Gtk.Label()
            safe_h = GLib.markup_escape_text(str(h))
            name_lbl.set_markup(f"<b>{safe_h}</b>")
            type_lbl = Gtk.Label()
            safe_type = GLib.markup_escape_text(col_type)
            type_lbl.set_markup(
                f"<span foreground='{dtype_color(col_type)}' size='small'>{safe_type}</span>"
            )
            header_box.append(name_lbl)
            header_box.append(type_lbl)
            header_box.show()
            col.set_widget(header_box)

            tv.append_column(col)

        if data.get("total_rows_read", 0) > PREVIEW_ROWS:
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            box.append(tv)
            warn = Gtk.Label(label=f"⚠ Mostrate prime {PREVIEW_ROWS} righe su {data['num_rows']:,}")
            warn.add_css_class("dim-label")
            warn.set_margin_top(4)
            warn.set_margin_bottom(4)
            scrolled.set_child(box)
        else:
            scrolled.set_child(tv)

        return scrolled

    # ------------------------------------------------------------------ #
    # Tab Schema
    # ------------------------------------------------------------------ #

    def _tab_schema(self, data: dict) -> Gtk.Widget:
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        store = Gtk.ListStore(str, str, str, str)
        for col in data["columns"]:
            nullable = "✓" if col["nullable"] else "✗"
            store.append(
                [
                    str(col["index"] + 1),
                    col["name"],
                    col["type"],
                    nullable,
                ]
            )

        tv = Gtk.TreeView(model=store)
        tv.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)

        # Colonna indice
        r = Gtk.CellRendererText()
        r.set_property("foreground", "#6a737d")
        c = Gtk.TreeViewColumn("#", r, text=0)
        c.set_min_width(40)
        tv.append_column(c)

        # Colonna nome
        r = Gtk.CellRendererText()
        r.set_property("weight", Pango.Weight.BOLD)
        c = Gtk.TreeViewColumn("Nome", r, text=1)
        c.set_resizable(True)
        c.set_min_width(180)
        tv.append_column(c)

        # Colonna tipo con colore
        r = Gtk.CellRendererText()
        c = Gtk.TreeViewColumn("Tipo")
        c.pack_start(r, True)
        c.set_resizable(True)
        c.set_min_width(150)

        def set_type_color(col, cell, model, iter_, data):
            type_str = model.get_value(iter_, 2)
            cell.set_property("text", type_str)
            cell.set_property("foreground", dtype_color(type_str))

        c.set_cell_data_func(r, set_type_color, None)
        tv.append_column(c)

        # Colonna nullable
        r = Gtk.CellRendererText()
        r.set_property("xalign", 0.5)
        c = Gtk.TreeViewColumn("Nullable", r, text=3)
        c.set_min_width(80)
        tv.append_column(c)

        # Row groups
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        outer.append(tv)

        if data.get("row_groups"):
            sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            sep.set_margin_top(16)
            outer.append(sep)

            rg_title = Gtk.Label()
            rg_title.set_markup("<b>Row Groups</b>")
            rg_title.set_halign(Gtk.Align.START)
            rg_title.set_margin_start(12)
            rg_title.set_margin_top(8)
            rg_title.set_margin_bottom(4)
            outer.append(rg_title)

            rg_store = Gtk.ListStore(str, str, str, str)
            for rg in data["row_groups"]:
                rg_store.append(
                    [
                        str(rg["index"]),
                        f"{rg['num_rows']:,}",
                        rg["compressed"],
                        rg["uncompressed"],
                    ]
                )

            rg_tv = Gtk.TreeView(model=rg_store)
            rg_tv.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
            for i, label in enumerate(["#", "Righe", "Compresso", "Originale"]):
                r = Gtk.CellRendererText()
                c = Gtk.TreeViewColumn(label, r, text=i)
                c.set_min_width(100)
                rg_tv.append_column(c)
            outer.append(rg_tv)

        scrolled.set_child(outer)
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

        col_types = [str] * (len(numeric_cols) + 1)
        store = Gtk.ListStore(*col_types)
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
            r.set_property("foreground", dtype_color("float"))
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
            for col, count in nulls.items():
                pct = count / data["num_rows"] * 100
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
    # Tab Metadati
    # ------------------------------------------------------------------ #

    def _tab_metadata(self, data: dict) -> Gtk.Widget:
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        outer.set_margin_start(16)
        outer.set_margin_end(16)
        outer.set_margin_top(12)
        outer.set_margin_bottom(12)

        def add_row(key, value):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            k = Gtk.Label(label=key)
            k.set_width_chars(22)
            k.set_halign(Gtk.Align.START)
            k.set_markup(f"<b>{GLib.markup_escape_text(key)}</b>")
            v = Gtk.Label(label=str(value))
            v.set_halign(Gtk.Align.START)
            v.set_selectable(True)
            row.append(k)
            row.append(v)
            outer.append(row)

        add_row("Versione formato", data.get("format_version", "?"))
        add_row("Creato da", data.get("created_by", "?"))
        add_row("Dimensione file", data.get("file_size", "?"))
        add_row("Dimensione compressa", data.get("compressed_size", "?"))
        add_row("Dimensione originale", data.get("uncompressed_size", "?"))
        add_row("Codec compressione", data.get("codecs", "?"))
        add_row("Row groups", str(data.get("num_row_groups", "?")))
        add_row("Righe totali", f"{data.get('num_rows', 0):,}")
        add_row("Colonne totali", str(data.get("num_columns", "?")))

        custom = data.get("custom_meta", {})
        if custom:
            sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            sep.set_margin_top(8)
            sep.set_margin_bottom(8)
            outer.append(sep)
            title = Gtk.Label()
            title.set_markup("<b>Metadati custom</b>")
            title.set_halign(Gtk.Align.START)
            outer.append(title)
            for k, v in custom.items():
                add_row(k, v)

        scrolled.set_child(outer)
        return scrolled


# --------------------------------------------------------------------------- #
# Estensione
# --------------------------------------------------------------------------- #


class ParquetPreviewExtension(GObject.GObject, Nautilus.MenuProvider):
    def get_file_items(self, files):
        if not HAS_PYARROW:
            return []

        if len(files) != 1:
            return []

        f = files[0]
        if not f.get_name().lower().endswith(".parquet"):
            return []

        item = Nautilus.MenuItem(
            name="ParquetPreview::show",
            label="Anteprima Parquet",
            tip=f"Mostra schema e dati di {f.get_name()}",
        )
        item.connect("activate", self._on_activate, f.get_location().get_path())
        return [item]

    def get_background_items(self, folder):
        return []

    def _on_activate(self, _item, path):
        win = ParquetPreviewWindow(path)
        win.present()
