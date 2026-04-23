"""
pdf_merge.py — Nautilus extension for merging PDFs
===================================================
Select 2+ PDF files in Nautilus, right-click → "Unisci PDF".
Opens a window to reorder the files and choose the output name.

Installation:
    cp pdf_merge.py ~/.local/share/nautilus-python/extensions/
    nautilus -q && nautilus

Dependencies:
    sudo apt install python3-pypdf
"""

import logging
import os
import threading

import gi

gi.require_version("Nautilus", "4.0")
gi.require_version("Gtk", "4.0")
gi.require_version("GLib", "2.0")

from gi.repository import GLib, GObject, Gtk, Nautilus, Pango

CSS = b"""
.pdf-header {
    background-color: #f6f8fa;
    border-bottom: 1px solid #e1e4e8;
    padding: 10px 16px;
}
.pdf-title {
    font-size: 16px;
    font-weight: bold;
    color: #24292e;
}
.pdf-subtitle {
    font-size: 12px;
    color: #6a737d;
}
.pdf-row {
    padding: 4px 8px;
    border-bottom: 1px solid #f0f0f0;
}
.pdf-row-index {
    font-size: 13px;
    color: #6a737d;
    min-width: 24px;
}
.pdf-row-name {
    font-size: 13px;
    color: #24292e;
}
.pdf-row-size {
    font-size: 12px;
    color: #6a737d;
}
.success-bar {
    background-color: #dcffe4;
    border: 1px solid #34d058;
    border-radius: 6px;
    padding: 8px 14px;
    margin: 8px;
}
.error-bar {
    background-color: #ffeef0;
    border: 1px solid #f97583;
    border-radius: 6px;
    padding: 8px 14px;
    margin: 8px;
}
"""


def fmt_size(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def get_pdf_pages(path: str) -> int:
    """Ritorna il numero di pagine di un PDF, o -1 in caso di errore."""
    try:
        import pypdf

        with open(path, "rb") as f:
            reader = pypdf.PdfReader(f, strict=False)
            return len(reader.pages)
    except ImportError as e:
        logging.error(
            "pypdf non installato — impossibile leggere le pagine PDF: %s. "
            "Installa con: sudo apt install python3-pypdf",
            e,
        )
        return -1
    except Exception as e:
        logging.warning("Impossibile leggere le pagine di %s: %s", path, e)
        return -1


# --------------------------------------------------------------------------- #
# Finestra
# --------------------------------------------------------------------------- #


class PdfMergeWindow(Gtk.Window):
    def __init__(self, paths: list[str]):
        super().__init__(title="Unisci PDF")
        self.set_default_size(620, 520)
        self._paths = list(paths)  # lista ordinabile
        self._merging = threading.Event()

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self._build_ui()

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(root)

        # --- Header ---
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        header.add_css_class("pdf-header")
        header.set_margin_start(4)

        title = Gtk.Label(label="Unisci PDF")
        title.add_css_class("pdf-title")
        title.set_halign(Gtk.Align.START)

        subtitle = Gtk.Label(
            label="Trascina per riordinare i file. L'output verrà salvato nella stessa cartella del primo file."
        )
        subtitle.add_css_class("pdf-subtitle")
        subtitle.set_halign(Gtk.Align.START)
        subtitle.set_wrap(True)
        subtitle.set_xalign(0)

        header.append(title)
        header.append(subtitle)
        root.append(header)
        root.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # --- Lista file riordinabile ---
        # Usiamo un ListStore con: indice (str), nome, percorso, dimensione, pagine
        self._store = Gtk.ListStore(str, str, str, str, str)
        self._refresh_store()

        self._treeview = Gtk.TreeView(model=self._store)
        self._treeview.set_reorderable(True)  # drag & drop per riordinare
        self._treeview.set_vexpand(True)
        self._treeview.set_headers_visible(True)
        self._treeview.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)

        # Colonna #
        r = Gtk.CellRendererText()
        r.set_property("foreground", "#6a737d")
        r.set_property("xalign", 1.0)
        c = Gtk.TreeViewColumn("#", r, text=0)
        c.set_min_width(36)
        c.set_max_width(40)
        self._treeview.append_column(c)

        # Colonna nome file
        r = Gtk.CellRendererText()
        r.set_property("ellipsize", Pango.EllipsizeMode.MIDDLE)
        c = Gtk.TreeViewColumn("File", r, text=1)
        c.set_resizable(True)
        c.set_expand(True)
        self._treeview.append_column(c)

        # Colonna pagine
        r = Gtk.CellRendererText()
        r.set_property("xalign", 1.0)
        r.set_property("foreground", "#6a737d")
        c = Gtk.TreeViewColumn("Pagine", r, text=4)
        c.set_min_width(60)
        self._treeview.append_column(c)

        # Colonna dimensione
        r = Gtk.CellRendererText()
        r.set_property("xalign", 1.0)
        r.set_property("foreground", "#6a737d")
        c = Gtk.TreeViewColumn("Dimensione", r, text=3)
        c.set_min_width(90)
        self._treeview.append_column(c)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self._treeview)
        scrolled.set_vexpand(True)
        root.append(scrolled)

        # --- Pulsanti su/giù + rimuovi ---
        btn_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        btn_bar.set_margin_start(8)
        btn_bar.set_margin_end(8)
        btn_bar.set_margin_top(6)
        btn_bar.set_margin_bottom(6)

        up_btn = Gtk.Button(label="⬆ Su")
        up_btn.set_tooltip_text("Sposta il file selezionato in su")
        up_btn.connect("clicked", self._move_up)
        btn_bar.append(up_btn)

        down_btn = Gtk.Button(label="⬇ Giù")
        down_btn.set_tooltip_text("Sposta il file selezionato in giù")
        down_btn.connect("clicked", self._move_down)
        btn_bar.append(down_btn)

        remove_btn = Gtk.Button(label="✕ Rimuovi")
        remove_btn.set_tooltip_text("Rimuovi il file selezionato dalla lista")
        remove_btn.connect("clicked", self._remove_selected)
        btn_bar.append(remove_btn)

        # Contatore pagine totali
        self._pages_label = Gtk.Label()
        self._pages_label.add_css_class("pdf-subtitle")
        self._pages_label.set_hexpand(True)
        self._pages_label.set_halign(Gtk.Align.END)
        btn_bar.append(self._pages_label)

        root.append(btn_bar)
        root.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # --- Nome file output ---
        name_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        name_bar.set_margin_start(12)
        name_bar.set_margin_end(12)
        name_bar.set_margin_top(10)
        name_bar.set_margin_bottom(10)

        name_lbl = Gtk.Label(label="Nome file output:")
        name_lbl.set_halign(Gtk.Align.START)
        name_bar.append(name_lbl)

        self._name_entry = Gtk.Entry()
        self._name_entry.set_hexpand(True)
        self._name_entry.set_placeholder_text("unione.pdf")
        self._name_entry.set_text(self._suggest_output_name())
        name_bar.append(self._name_entry)

        root.append(name_bar)

        # --- Barra di stato (nascosta finché non serve) ---
        self._status_bar = Gtk.Label()
        self._status_bar.set_visible(False)
        self._status_bar.set_wrap(True)
        self._status_bar.set_xalign(0)
        self._status_bar.set_margin_start(12)
        self._status_bar.set_margin_end(12)
        root.append(self._status_bar)

        # --- Progress bar ---
        self._progress = Gtk.ProgressBar()
        self._progress.set_visible(False)
        self._progress.set_margin_start(12)
        self._progress.set_margin_end(12)
        self._progress.set_margin_bottom(4)
        root.append(self._progress)

        root.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # --- Pulsanti azione ---
        action_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        action_bar.set_margin_start(12)
        action_bar.set_margin_end(12)
        action_bar.set_margin_top(8)
        action_bar.set_margin_bottom(8)
        action_bar.set_halign(Gtk.Align.END)

        cancel_btn = Gtk.Button(label="Annulla")
        cancel_btn.connect("clicked", lambda _: self.close())
        action_bar.append(cancel_btn)

        self._merge_btn = Gtk.Button(label="🔗 Unisci PDF")
        self._merge_btn.add_css_class("suggested-action")
        self._merge_btn.connect("clicked", self._on_merge)
        action_bar.append(self._merge_btn)

        root.append(action_bar)

        # Carica numero pagine in background
        threading.Thread(target=self._load_pages, daemon=True).start()

    # ------------------------------------------------------------------ #
    # Store e lista
    # ------------------------------------------------------------------ #

    def _refresh_store(self):
        self._store.clear()
        for i, path in enumerate(self._paths):
            name = os.path.basename(path)
            try:
                size = fmt_size(os.path.getsize(path))
            except OSError:
                size = "?"
            self._store.append([str(i + 1), name, path, size, "…"])

    def _sync_paths_from_store(self):
        """Aggiorna self._paths dall'ordine corrente dello store (dopo drag & drop)."""
        self._paths = []
        it = self._store.get_iter_first()
        while it:
            self._paths.append(self._store.get_value(it, 2))
            it = self._store.iter_next(it)
        # Aggiorna gli indici
        it = self._store.get_iter_first()
        i = 1
        while it:
            self._store.set_value(it, 0, str(i))
            it = self._store.iter_next(it)
            i += 1

    def _load_pages(self):
        """Carica il numero di pagine di ogni PDF in background."""
        totale = 0
        it_list = []
        it = self._store.get_iter_first()
        while it:
            it_list.append((self._store.get_string_from_iter(it), self._store.get_value(it, 2)))
            it = self._store.iter_next(it)

        for str_path_iter, path in it_list:
            pages = get_pdf_pages(path)
            pages_str = str(pages) if pages >= 0 else "?"
            if pages > 0:
                totale += pages
            GLib.idle_add(self._update_pages_cell, str_path_iter, pages_str, totale)

    def _update_pages_cell(self, str_iter, pages_str, totale):
        try:
            it = self._store.get_iter_from_string(str_iter)
            self._store.set_value(it, 4, pages_str)
            self._pages_label.set_text(f"Totale: {totale} pagine")
        except Exception as e:
            logging.debug("Page count update failed: %s", e)
        return False

    # ------------------------------------------------------------------ #
    # Pulsanti riordino
    # ------------------------------------------------------------------ #

    def _get_selected_iter(self):
        sel = self._treeview.get_selection()
        model, it = sel.get_selected()
        return it

    def _move_up(self, _btn):
        it = self._get_selected_iter()
        if not it:
            return
        prev = self._store.iter_previous(it)
        if prev:
            self._store.swap(it, prev)
            self._sync_paths_from_store()

    def _move_down(self, _btn):
        it = self._get_selected_iter()
        if not it:
            return
        next_it = self._store.iter_next(it)
        if next_it:
            self._store.swap(it, next_it)
            self._sync_paths_from_store()

    def _remove_selected(self, _btn):
        it = self._get_selected_iter()
        if not it:
            return
        self._store.remove(it)
        self._sync_paths_from_store()
        # Aggiorna nome suggerito
        self._name_entry.set_text(self._suggest_output_name())

    # ------------------------------------------------------------------ #
    # Nome output suggerito
    # ------------------------------------------------------------------ #

    def _suggest_output_name(self) -> str:
        if not self._paths:
            return "unione.pdf"
        # Prendi il nome del primo file senza estensione + "_unione"
        first = os.path.splitext(os.path.basename(self._paths[0]))[0]
        # Rimuovi numeri finali comuni (es. "documento_1" → "documento")
        import re

        base = re.sub(r"[\s_\-]+\d+$", "", first)
        return f"{base}_unione.pdf" if base else "unione.pdf"

    def _get_output_path(self) -> str:
        raw = self._name_entry.get_text().strip()
        if not raw:
            raw = "unione.pdf"
        # Strip directory components to prevent path traversal
        name = os.path.basename(raw)
        if not name or name.startswith("."):
            name = "unione.pdf"
        if not name.lower().endswith(".pdf"):
            name += ".pdf"
        folder = os.path.dirname(self._paths[0])
        return os.path.join(folder, name)

    # ------------------------------------------------------------------ #
    # PDF merge
    # ------------------------------------------------------------------ #

    def _on_merge(self, _btn):
        self._sync_paths_from_store()

        if len(self._paths) < 2:
            self._show_error("Seleziona almeno 2 file PDF.")
            return

        output_path = self._get_output_path()

        # Controlla che l'output non sovrascriva uno degli input
        if output_path in self._paths:
            self._show_error(
                "Il file di output non può avere lo stesso nome di uno dei file di input."
            )
            return

        self._merge_btn.set_sensitive(False)
        self._progress.set_visible(True)
        self._progress.pulse()
        self._status_bar.set_visible(False)

        # Avvia unione in thread separato
        threading.Thread(
            target=self._do_merge, args=(list(self._paths), output_path), daemon=True
        ).start()

        # Pulsa la progress bar finché non finisce
        GLib.timeout_add(100, self._pulse_progress)

    def _pulse_progress(self):
        if self._merging.is_set() or self._progress.get_visible():
            self._progress.pulse()
            return True
        return False

    def _do_merge(self, paths: list, output_path: str):
        self._merging.set()
        try:
            import pypdf

            writer = pypdf.PdfWriter()

            for path in paths:
                reader = pypdf.PdfReader(path, strict=False)
                for page in reader.pages:
                    writer.add_page(page)

            with open(output_path, "wb") as f:
                writer.write(f)

            # Conta pagine totali nel file output
            total_pages = sum(len(pypdf.PdfReader(p, strict=False).pages) for p in paths)

            GLib.idle_add(self._on_merge_done, output_path, total_pages, None)

        except Exception as e:
            GLib.idle_add(self._on_merge_done, output_path, 0, str(e))
        finally:
            self._merging.clear()

    def _on_merge_done(self, output_path: str, total_pages: int, error: str | None):
        self._progress.set_visible(False)
        self._merge_btn.set_sensitive(True)

        if error:
            self._show_error(f"Errore durante l'unione: {error}")
        else:
            filename = os.path.basename(output_path)
            size = fmt_size(os.path.getsize(output_path))
            self._show_success(
                f"✓ File creato: {filename}  ({total_pages} pagine, {size})\n"
                f"Salvato in: {os.path.dirname(output_path)}"
            )
            # Apri la cartella contenente il file
            import subprocess

            subprocess.Popen(["xdg-open", os.path.dirname(output_path)])

        return False

    # ------------------------------------------------------------------ #
    # Status bar
    # ------------------------------------------------------------------ #

    def _show_success(self, msg: str):
        safe = GLib.markup_escape_text(msg)
        self._status_bar.set_markup(f"<span foreground='#22863a'>{safe}</span>")
        self._status_bar.set_visible(True)

    def _show_error(self, msg: str):
        safe = GLib.markup_escape_text(msg)
        self._status_bar.set_markup(f"<span foreground='#d73a49'>{safe}</span>")
        self._status_bar.set_visible(True)


# --------------------------------------------------------------------------- #
# Extension
# --------------------------------------------------------------------------- #


class PdfMergeExtension(GObject.GObject, Nautilus.MenuProvider):
    def get_file_items(self, files):
        # Filtra solo i PDF
        pdf_files = [
            f
            for f in files
            if f.get_name().lower().endswith(".pdf") and f.get_location().get_path() is not None
        ]

        if len(pdf_files) < 2:
            return []

        paths = [f.get_location().get_path() for f in pdf_files]

        item = Nautilus.MenuItem(
            name="PdfMerge::merge",
            label=f"Unisci {len(pdf_files)} PDF",
            tip=f"Unisci {len(pdf_files)} file PDF in uno solo",
        )
        item.connect("activate", self._on_activate, paths)
        return [item]

    def get_background_items(self, folder):
        return []

    def _on_activate(self, _item, paths):
        # Ordina per nome come punto di partenza sensato
        paths_sorted = sorted(paths, key=lambda p: os.path.basename(p).lower())
        win = PdfMergeWindow(paths_sorted)
        win.present()
