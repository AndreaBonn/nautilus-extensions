"""
csv_preview.py — Nautilus extension for CSV preview
=====================================================
Adds a "Anteprima CSV" entry to the right-click menu on .csv files.
Shows the first N rows in a formatted table with basic statistics.

Installation:
    cp csv_preview.py ~/.local/share/nautilus-python/extensions/
    nautilus -q && nautilus

Optional dependencies (recommended):
    sudo apt install python3-pandas
"""

import csv
import os
import threading

import gi

gi.require_version("Nautilus", "4.0")
gi.require_version("Gtk", "4.0")
gi.require_version("GLib", "2.0")

from gi.repository import GLib, GObject, Gtk, Nautilus, Pango

# Pandas optional — if available, also shows statistics
PANDAS_AVAILABLE = False
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    pass


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

PREVIEW_ROWS = 100  # rows to show in the preview
MAX_COL_WIDTH = 300  # maximum column width in px
MIN_COL_WIDTH = 60  # minimum column width in px
WINDOW_W = 1100
WINDOW_H = 650


# --------------------------------------------------------------------------- #
# CSS
# --------------------------------------------------------------------------- #


CSS = b"""
.csv-header {
    background-color: #f6f8fa;
    font-weight: bold;
}
.csv-info-bar {
    background-color: #f6f8fa;
    border-bottom: 1px solid #e1e4e8;
    padding: 6px 12px;
}
.csv-stat-box {
    background-color: #ffffff;
    border: 1px solid #e1e4e8;
    border-radius: 6px;
    padding: 8px 14px;
    margin: 4px;
}
.csv-stat-title {
    font-size: 11px;
    color: #6a737d;
}
.csv-stat-value {
    font-size: 15px;
    font-weight: bold;
    color: #24292e;
}
.mono {
    font-family: monospace;
}
"""


# --------------------------------------------------------------------------- #
# CSV reading
# --------------------------------------------------------------------------- #


def detect_delimiter(path: str) -> str:
    """Automatically detects the CSV delimiter."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            sample = f.read(4096)
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        return ","


def read_csv_plain(path: str, max_rows: int) -> tuple[list, list, dict]:
    """
    Reads the CSV using stdlib.
    Returns (headers, rows, info) where info contains basic metadata.
    """
    delimiter = detect_delimiter(path)
    headers = []
    rows = []
    total_rows = 0

    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f, delimiter=delimiter)
            headers = next(reader, [])
            for row in reader:
                total_rows += 1
                if total_rows <= max_rows:
                    # Align the row to the header columns
                    while len(row) < len(headers):
                        row.append("")
                    rows.append(row[: len(headers)])
    except OSError as e:
        return [], [], {"error": str(e)}

    file_size = os.path.getsize(path)
    info = {
        "delimiter": repr(delimiter),
        "total_rows": total_rows,
        "total_cols": len(headers),
        "file_size": _fmt_size(file_size),
        "truncated": total_rows > max_rows,
    }
    return headers, rows, info


def read_csv_pandas(path: str, max_rows: int) -> tuple[list, list, dict, object]:
    """
    Reads with pandas — more robust and adds statistics.
    Also returns the dataframe for statistics.
    """
    try:
        delimiter = detect_delimiter(path)
        df_full = pd.read_csv(path, sep=delimiter, low_memory=False)
        total_rows = len(df_full)
        df = df_full.head(max_rows)

        headers = list(df.columns.astype(str))
        rows = df.astype(str).values.tolist()

        # Column types
        dtypes = {col: str(df_full[col].dtype) for col in df_full.columns}

        file_size = os.path.getsize(path)
        info = {
            "delimiter": repr(delimiter),
            "total_rows": total_rows,
            "total_cols": len(headers),
            "file_size": _fmt_size(file_size),
            "truncated": total_rows > max_rows,
            "null_counts": df_full.isnull().sum().to_dict(),
            "dtypes": dtypes,
            "numeric_cols": list(df_full.select_dtypes(include="number").columns),
        }
        return headers, rows, info, df_full
    except Exception as e:
        return [], [], {"error": str(e)}, None


def _fmt_size(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


# --------------------------------------------------------------------------- #
# Preview window
# --------------------------------------------------------------------------- #


class CsvPreviewWindow(Gtk.Window):
    def __init__(self, csv_path: str):
        filename = os.path.basename(csv_path)
        super().__init__(title=f"{filename} — CSV Preview")
        self.set_default_size(WINDOW_W, WINDOW_H)
        self._csv_path = csv_path
        self._df = None

        # Apply CSS
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self._build_ui()
        threading.Thread(target=self._load_data, daemon=True).start()

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        self._root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(self._root)

        # Initial loading spinner
        self._spinner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._spinner_box.set_valign(Gtk.Align.CENTER)
        self._spinner_box.set_halign(Gtk.Align.CENTER)
        self._spinner_box.set_vexpand(True)
        spinner = Gtk.Spinner()
        spinner.set_size_request(48, 48)
        spinner.start()
        lbl = Gtk.Label(label="Caricamento CSV...")
        lbl.add_css_class("dim-label")
        self._spinner_box.append(spinner)
        self._spinner_box.append(lbl)
        self._root.append(self._spinner_box)

    def _build_content(self, headers, rows, info, df=None):
        """Builds the full UI after data has been loaded."""

        # Remove the spinner
        self._root.remove(self._spinner_box)

        # --- Top info bar ---
        info_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        info_bar.add_css_class("csv-info-bar")
        info_bar.set_margin_start(4)
        info_bar.set_margin_end(8)

        self._add_stat(info_bar, "Righe", f"{info.get('total_rows', '?'):,}")
        self._add_stat(info_bar, "Colonne", str(info.get("total_cols", "?")))
        self._add_stat(info_bar, "Delimitatore", info.get("delimiter", "?"))
        self._add_stat(info_bar, "Dimensione", info.get("file_size", "?"))

        if info.get("truncated"):
            trunc_lbl = Gtk.Label(
                label=f"⚠ Mostrate prime {PREVIEW_ROWS} righe su {info['total_rows']:,}"
            )
            trunc_lbl.add_css_class("dim-label")
            trunc_lbl.set_hexpand(True)
            trunc_lbl.set_halign(Gtk.Align.END)
            info_bar.append(trunc_lbl)

        self._root.append(info_bar)
        self._root.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        if "error" in info:
            err = Gtk.Label(label=f"Errore: {info['error']}")
            err.set_margin_top(20)
            self._root.append(err)
            return

        # --- Notebook with tabs ---
        notebook = Gtk.Notebook()
        notebook.set_vexpand(True)
        self._root.append(notebook)

        # Tab 1: Data table
        table_widget = self._build_table(headers, rows, info)
        notebook.append_page(table_widget, Gtk.Label(label="📊 Dati"))

        # Tab 2: Statistics (only with pandas)
        if df is not None:
            stats_widget = self._build_stats(df, info)
            notebook.append_page(stats_widget, Gtk.Label(label="📈 Statistiche"))

        # Tab 3: Column info
        cols_widget = self._build_columns_info(headers, info)
        notebook.append_page(cols_widget, Gtk.Label(label="🗂 Colonne"))

        # --- Bottom bar ---
        bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bottom.set_margin_start(8)
        bottom.set_margin_end(8)
        bottom.set_margin_top(6)
        bottom.set_margin_bottom(6)

        path_lbl = Gtk.Label(label=self._csv_path)
        path_lbl.add_css_class("dim-label")
        path_lbl.set_ellipsize(Pango.EllipsizeMode.START)
        path_lbl.set_hexpand(True)
        path_lbl.set_halign(Gtk.Align.START)
        bottom.append(path_lbl)

        open_btn = Gtk.Button(label="Apri con editor")
        open_btn.connect("clicked", self._open_editor)
        bottom.append(open_btn)

        self._root.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        self._root.append(bottom)

    def _add_stat(self, box, title, value):
        stat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        stat_box.add_css_class("csv-stat-box")

        title_lbl = Gtk.Label(label=title)
        title_lbl.add_css_class("csv-stat-title")
        title_lbl.set_halign(Gtk.Align.START)

        value_lbl = Gtk.Label(label=str(value))
        value_lbl.add_css_class("csv-stat-value")
        value_lbl.set_halign(Gtk.Align.START)

        stat_box.append(title_lbl)
        stat_box.append(value_lbl)
        box.append(stat_box)

    # ------------------------------------------------------------------ #
    # Data tab
    # ------------------------------------------------------------------ #

    def _build_table(self, headers, rows, info) -> Gtk.Widget:
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)

        # Create ListStore with all columns as strings
        col_types = [str] * len(headers)
        store = Gtk.ListStore(*col_types)

        for row in rows:
            store.append(row)

        treeview = Gtk.TreeView(model=store)
        treeview.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
        treeview.add_css_class("mono")

        # Row index column
        idx_renderer = Gtk.CellRendererText()
        idx_renderer.set_property("foreground", "#6a737d")
        idx_col = Gtk.TreeViewColumn("#")
        idx_col.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        idx_col.set_fixed_width(50)

        # Add row number via a virtual column
        for i, header in enumerate(headers):
            renderer = Gtk.CellRendererText()
            renderer.set_property("ellipsize", Pango.EllipsizeMode.END)

            # Highlight numeric columns in blue
            info.get("dtypes", {})
            numeric_cols = info.get("numeric_cols", [])
            if header in numeric_cols:
                renderer.set_property("foreground", "#0366d6")
                renderer.set_property("xalign", 1.0)  # right-align numbers

            col = Gtk.TreeViewColumn(header, renderer, text=i)
            col.set_resizable(True)
            col.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
            col.set_fixed_width(max(MIN_COL_WIDTH, min(MAX_COL_WIDTH, len(header) * 12 + 20)))
            col.set_sort_column_id(i)

            # Bold header
            safe_header = GLib.markup_escape_text(header)
            label = Gtk.Label(label=header)
            label.set_markup(f"<b>{safe_header}</b>")
            if header in numeric_cols:
                label.set_markup(f"<b><span foreground='#0366d6'>{safe_header}</span></b>")
            col.set_widget(label)
            label.show()

            treeview.append_column(col)

        scrolled.set_child(treeview)
        return scrolled

    # ------------------------------------------------------------------ #
    # Statistics tab
    # ------------------------------------------------------------------ #

    def _build_stats(self, df, info) -> Gtk.Widget:
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        outer.set_margin_start(16)
        outer.set_margin_end(16)
        outer.set_margin_top(16)
        outer.set_margin_bottom(16)

        numeric_cols = info.get("numeric_cols", [])

        if not numeric_cols:
            lbl = Gtk.Label(label="Nessuna colonna numerica trovata.")
            lbl.add_css_class("dim-label")
            outer.append(lbl)
            scrolled.set_child(outer)
            return scrolled

        # Descriptive statistics with pandas
        try:
            desc = df[numeric_cols].describe()
        except Exception:
            scrolled.set_child(Gtk.Label(label="Errore nel calcolo delle statistiche."))
            return scrolled

        # Statistics table
        stats_headers = ["Statistica"] + numeric_cols
        stats_rows_data = []
        for stat in desc.index:
            row = [stat] + [f"{desc.loc[stat, col]:.4g}" for col in numeric_cols]
            stats_rows_data.append(row)

        col_types = [str] * len(stats_headers)
        store = Gtk.ListStore(*col_types)
        for row in stats_rows_data:
            store.append(row)

        treeview = Gtk.TreeView(model=store)
        treeview.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        treeview.add_css_class("mono")

        for i, h in enumerate(stats_headers):
            renderer = Gtk.CellRendererText()
            if i > 0:
                renderer.set_property("xalign", 1.0)
            col = Gtk.TreeViewColumn(h, renderer, text=i)
            col.set_resizable(True)
            col.set_min_width(MIN_COL_WIDTH)
            treeview.append_column(col)

        title = Gtk.Label()
        title.set_markup("<b>Statistiche descrittive (colonne numeriche)</b>")
        title.set_halign(Gtk.Align.START)
        outer.append(title)
        outer.append(treeview)

        # Null values
        null_counts = info.get("null_counts", {})
        nulls_with_data = {k: v for k, v in null_counts.items() if v > 0}
        if nulls_with_data:
            null_title = Gtk.Label()
            null_title.set_markup("<b>Valori nulli per colonna</b>")
            null_title.set_halign(Gtk.Align.START)
            null_title.set_margin_top(12)
            outer.append(null_title)

            for col, count in nulls_with_data.items():
                pct = count / info["total_rows"] * 100
                row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                col_lbl = Gtk.Label(label=col)
                col_lbl.set_width_chars(20)
                col_lbl.set_halign(Gtk.Align.START)
                val_lbl = Gtk.Label(label=f"{count:,} ({pct:.1f}%)")
                val_lbl.add_css_class("dim-label")
                row_box.append(col_lbl)
                row_box.append(val_lbl)
                outer.append(row_box)
        else:
            no_null = Gtk.Label(label="✓ Nessun valore nullo trovato")
            no_null.set_halign(Gtk.Align.START)
            no_null.set_margin_top(8)
            outer.append(no_null)

        scrolled.set_child(outer)
        return scrolled

    # ------------------------------------------------------------------ #
    # Columns tab
    # ------------------------------------------------------------------ #

    def _build_columns_info(self, headers, info) -> Gtk.Widget:
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        dtypes = info.get("dtypes", {})
        null_counts = info.get("null_counts", {})
        info.get("numeric_cols", [])
        total_rows = info.get("total_rows", 0)

        col_types_list = [str, str, str, str]
        store = Gtk.ListStore(*col_types_list)

        for i, h in enumerate(headers):
            dtype = dtypes.get(h, "unknown")
            nulls = null_counts.get(h, 0)
            null_str = f"{nulls:,} ({nulls / total_rows * 100:.1f}%)" if total_rows > 0 else "0"
            store.append([str(i + 1), h, dtype, null_str])

        treeview = Gtk.TreeView(model=store)
        treeview.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)

        col_defs = [("#", 40), ("Nome colonna", 200), ("Tipo", 120), ("Valori nulli", 140)]
        for i, (label, width) in enumerate(col_defs):
            renderer = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(label, renderer, text=i)
            col.set_resizable(True)
            col.set_min_width(width)
            treeview.append_column(col)

        scrolled.set_child(treeview)
        return scrolled

    # ------------------------------------------------------------------ #
    # Data loading
    # ------------------------------------------------------------------ #

    def _load_data(self):
        path = self._csv_path
        if PANDAS_AVAILABLE:
            headers, rows, info, df = read_csv_pandas(path, PREVIEW_ROWS)
        else:
            headers, rows, info = read_csv_plain(path, PREVIEW_ROWS)
            df = None

        GLib.idle_add(self._on_data_loaded, headers, rows, info, df)

    def _on_data_loaded(self, headers, rows, info, df):
        self._build_content(headers, rows, info, df)
        return False

    # ------------------------------------------------------------------ #
    # Handlers
    # ------------------------------------------------------------------ #

    def _open_editor(self, _btn):
        import subprocess

        subprocess.Popen(["xdg-open", self._csv_path])


# --------------------------------------------------------------------------- #
# Extension
# --------------------------------------------------------------------------- #


class CsvPreviewExtension(GObject.GObject, Nautilus.MenuProvider):
    def get_file_items(self, files):
        """Called when one or more files are selected."""
        # Show the menu item only when a single CSV is selected
        if len(files) != 1:
            return []

        f = files[0]
        if not self._is_csv(f):
            return []

        filename = f.get_name()
        item = Nautilus.MenuItem(
            name="CsvPreview::show",
            label="Anteprima CSV",
            tip=f"Mostra anteprima di {filename}",
        )
        item.connect("activate", self._on_activate, f.get_location().get_path())
        return [item]

    def get_background_items(self, folder):
        return []

    def _is_csv(self, nautilus_file) -> bool:
        name = nautilus_file.get_name().lower()
        return name.endswith(".csv") or name.endswith(".tsv")

    def _on_activate(self, _item, path):
        win = CsvPreviewWindow(path)
        win.present()
