"""
pdf_split.py — Estensione Nautilus per dividere PDF
====================================================
Tasto destro su un PDF → "Dividi PDF"
Supporta 4 modalità:
  1. Intervalli personalizzati (es. 1-3, 4-6, 9)
  2. Ogni N pagine
  3. Una pagina per file
  4. Per segnalibri/capitoli

Installazione:
    cp pdf_split.py ~/.local/share/nautilus-python/extensions/
    nautilus -q && nautilus

Dipendenze:
    sudo apt install python3-pypdf
"""

import os
import re
import threading

import gi
gi.require_version('Nautilus', '4.0')
gi.require_version('Gtk', '4.0')
gi.require_version('GLib', '2.0')

from gi.repository import Nautilus, GObject, Gtk, GLib, Pango


CSS = b"""
.sp-header {
    background-color: #f6f8fa;
    border-bottom: 1px solid #e1e4e8;
    padding: 10px 16px;
}
.sp-title {
    font-size: 16px;
    font-weight: bold;
    color: #24292e;
}
.sp-subtitle {
    font-size: 12px;
    color: #6a737d;
}
.sp-section-title {
    font-size: 12px;
    font-weight: bold;
    color: #6a737d;
    margin-top: 4px;
}
.sp-preview-row {
    font-family: monospace;
    font-size: 12px;
    padding: 2px 4px;
}
.sp-hint {
    font-size: 11px;
    color: #6a737d;
    font-style: italic;
}
"""


def fmt_size(size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


# --------------------------------------------------------------------------- #
# Parsing intervalli
# --------------------------------------------------------------------------- #

def parse_ranges(text: str, total_pages: int) -> list[tuple[int, int]] | str:
    """
    Parsa una stringa di intervalli come "1-3, 5, 7-9" e ritorna
    una lista di tuple (start, end) in base 0.
    Ritorna una stringa di errore se il formato non è valido.
    """
    ranges = []
    parts = re.split(r'[,;\s]+', text.strip())
    for part in parts:
        part = part.strip()
        if not part:
            continue
        m = re.match(r'^(\d+)-(\d+)$', part)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if a < 1 or b < 1:
                return f"Numeri pagina devono essere ≥ 1 (trovato: {part})"
            if a > b:
                return f"Intervallo non valido: {part} (inizio > fine)"
            if b > total_pages:
                return f"Pagina {b} non esiste (il PDF ha {total_pages} pagine)"
            ranges.append((a - 1, b - 1))
        elif re.match(r'^\d+$', part):
            n = int(part)
            if n < 1 or n > total_pages:
                return f"Pagina {n} non esiste (il PDF ha {total_pages} pagine)"
            ranges.append((n - 1, n - 1))
        else:
            return f"Formato non riconosciuto: '{part}' (usa es. 1-3, 5, 7-9)"
    if not ranges:
        return "Inserisci almeno un intervallo"
    return ranges


def ranges_to_chunks(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    return ranges


def every_n_chunks(total: int, n: int) -> list[tuple[int, int]]:
    chunks = []
    for start in range(0, total, n):
        end = min(start + n - 1, total - 1)
        chunks.append((start, end))
    return chunks


def single_page_chunks(total: int) -> list[tuple[int, int]]:
    return [(i, i) for i in range(total)]


def bookmark_chunks(bookmarks, total_pages: int) -> list[tuple[int, int, str]]:
    """
    Ritorna lista di (start, end, titolo) dai segnalibri.
    Ogni segnalibro va fino all'inizio del successivo.
    """
    entries = []

    def collect(items, depth=0):
        for item in items:
            if hasattr(item, 'title') and hasattr(item, 'page'):
                try:
                    page_num = item.page.idnum if hasattr(item.page, 'idnum') else 0
                    entries.append((page_num, item.title))
                except Exception:
                    pass
            if isinstance(item, list):
                collect(item, depth + 1)

    collect(bookmarks)

    if not entries:
        return []

    entries.sort(key=lambda x: x[0])

    chunks = []
    for i, (page_idx, title) in enumerate(entries):
        start = page_idx
        end = entries[i + 1][0] - 1 if i + 1 < len(entries) else total_pages - 1
        if start <= end:
            safe_title = re.sub(r'[^\w\s\-]', '', title).strip()[:50]
            chunks.append((start, end, safe_title))

    return chunks


# --------------------------------------------------------------------------- #
# Nomi file output
# --------------------------------------------------------------------------- #

def chunk_filename(base: str, start: int, end: int, title: str = None) -> str:
    """Genera il nome file per un chunk: base_pag1-3.pdf o base_TitoloCapitolo.pdf"""
    if title:
        safe = re.sub(r'\s+', '_', title)
        return f"{base}_{safe}.pdf"
    if start == end:
        return f"{base}_pag{start + 1}.pdf"
    return f"{base}_pag{start + 1}-{end + 1}.pdf"


# --------------------------------------------------------------------------- #
# Finestra principale
# --------------------------------------------------------------------------- #

class PdfSplitWindow(Gtk.Window):

    def __init__(self, path: str):
        super().__init__(title="Dividi PDF")
        self.set_default_size(680, 580)
        self._path = path
        self._total_pages = 0
        self._bookmarks = []
        self._splitting = False

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self._build_ui()
        threading.Thread(target=self._load_pdf_info, daemon=True).start()

    # ------------------------------------------------------------------ #
    # Caricamento info PDF
    # ------------------------------------------------------------------ #

    def _load_pdf_info(self):
        try:
            import pypdf
            reader = pypdf.PdfReader(self._path, strict=False)
            total = len(reader.pages)
            bookmarks = []
            try:
                bookmarks = list(reader.outline)
            except Exception:
                pass
            GLib.idle_add(self._on_pdf_loaded, total, bookmarks, None)
        except Exception as e:
            GLib.idle_add(self._on_pdf_loaded, 0, [], str(e))

    def _on_pdf_loaded(self, total, bookmarks, error):
        if error:
            self._subtitle.set_text(f"Errore: {error}")
            return False

        self._total_pages = total
        self._bookmarks = bookmarks
        filename = os.path.basename(self._path)
        size = fmt_size(os.path.getsize(self._path))
        self._subtitle.set_text(
            f"{filename}  •  {total} pagine  •  {size}"
        )
        self._split_btn.set_sensitive(True)

        # Abilita tab segnalibri solo se esistono
        has_bookmarks = len(bookmarks) > 0
        self._notebook.get_nth_page(3).set_sensitive(has_bookmarks)
        if not has_bookmarks:
            self._notebook.get_tab_label(
                self._notebook.get_nth_page(3)
            ).set_tooltip_text("Nessun segnalibro trovato in questo PDF")

        self._update_preview()
        return False

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(root)

        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        header.add_css_class('sp-header')
        header.set_margin_start(4)

        title = Gtk.Label(label="Dividi PDF")
        title.add_css_class('sp-title')
        title.set_halign(Gtk.Align.START)

        self._subtitle = Gtk.Label(label="Caricamento…")
        self._subtitle.add_css_class('sp-subtitle')
        self._subtitle.set_halign(Gtk.Align.START)

        header.append(title)
        header.append(self._subtitle)
        root.append(header)
        root.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Notebook con le 4 modalità
        self._notebook = Gtk.Notebook()
        self._notebook.set_margin_start(12)
        self._notebook.set_margin_end(12)
        self._notebook.set_margin_top(10)
        self._notebook.connect('switch-page', lambda *_: GLib.idle_add(self._update_preview))

        self._notebook.append_page(self._tab_ranges(),    Gtk.Label(label="📐 Intervalli"))
        self._notebook.append_page(self._tab_every_n(),   Gtk.Label(label="🔢 Ogni N pagine"))
        self._notebook.append_page(self._tab_single(),    Gtk.Label(label="📄 Una per file"))
        self._notebook.append_page(self._tab_bookmarks(), Gtk.Label(label="🔖 Segnalibri"))

        root.append(self._notebook)

        # Cartella output
        out_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        out_box.set_margin_start(12)
        out_box.set_margin_end(12)
        out_box.set_margin_top(10)

        out_lbl = Gtk.Label(label="Cartella output:")
        out_lbl.set_halign(Gtk.Align.START)
        out_box.append(out_lbl)

        self._out_entry = Gtk.Entry()
        self._out_entry.set_hexpand(True)
        self._out_entry.set_text(os.path.dirname(self._path))
        out_box.append(self._out_entry)

        browse_btn = Gtk.Button(label="…")
        browse_btn.set_tooltip_text("Scegli cartella")
        browse_btn.connect('clicked', self._browse_folder)
        out_box.append(browse_btn)

        root.append(out_box)

        # Anteprima file che verranno creati
        preview_lbl = Gtk.Label()
        preview_lbl.set_markup("<b>Anteprima file che verranno creati:</b>")
        preview_lbl.set_halign(Gtk.Align.START)
        preview_lbl.set_margin_start(12)
        preview_lbl.set_margin_top(10)
        preview_lbl.set_margin_bottom(4)
        root.append(preview_lbl)

        self._preview_store = Gtk.ListStore(str, str)
        preview_tv = Gtk.TreeView(model=self._preview_store)
        preview_tv.set_headers_visible(False)
        preview_tv.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        preview_tv.add_css_class('sp-preview-row')

        r = Gtk.CellRendererText()
        r.set_property('family', 'monospace')
        r.set_property('foreground', '#24292e')
        c = Gtk.TreeViewColumn("File", r, text=0)
        c.set_expand(True)
        preview_tv.append_column(c)

        r = Gtk.CellRendererText()
        r.set_property('foreground', '#6a737d')
        r.set_property('xalign', 1.0)
        c = Gtk.TreeViewColumn("Pagine", r, text=1)
        c.set_min_width(80)
        preview_tv.append_column(c)

        preview_scroll = Gtk.ScrolledWindow()
        preview_scroll.set_child(preview_tv)
        preview_scroll.set_size_request(-1, 130)
        preview_scroll.set_margin_start(12)
        preview_scroll.set_margin_end(12)
        root.append(preview_scroll)

        # Progress + status
        self._progress = Gtk.ProgressBar()
        self._progress.set_visible(False)
        self._progress.set_margin_start(12)
        self._progress.set_margin_end(12)
        self._progress.set_margin_top(6)
        root.append(self._progress)

        self._status = Gtk.Label()
        self._status.set_visible(False)
        self._status.set_wrap(True)
        self._status.set_xalign(0)
        self._status.set_margin_start(12)
        self._status.set_margin_end(12)
        self._status.set_margin_top(4)
        root.append(self._status)

        root.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Pulsanti azione
        action_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        action_bar.set_margin_start(12)
        action_bar.set_margin_end(12)
        action_bar.set_margin_top(8)
        action_bar.set_margin_bottom(8)
        action_bar.set_halign(Gtk.Align.END)

        cancel_btn = Gtk.Button(label="Annulla")
        cancel_btn.connect('clicked', lambda _: self.close())
        action_bar.append(cancel_btn)

        self._split_btn = Gtk.Button(label="✂ Dividi PDF")
        self._split_btn.add_css_class('suggested-action')
        self._split_btn.set_sensitive(False)
        self._split_btn.connect('clicked', self._on_split)
        action_bar.append(self._split_btn)

        root.append(action_bar)

    # ------------------------------------------------------------------ #
    # Tab modalità
    # ------------------------------------------------------------------ #

    def _tab_ranges(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_start(8)
        box.set_margin_end(8)
        box.set_margin_top(12)
        box.set_margin_bottom(8)

        lbl = Gtk.Label()
        lbl.set_markup("Inserisci gli intervalli separati da virgola.\n"
                        "<span size='small' foreground='#6a737d'>Esempi: <tt>1-3, 5, 7-9</tt> oppure <tt>1-5, 6-10, 11-15</tt></span>")
        lbl.set_halign(Gtk.Align.START)
        lbl.set_wrap(True)
        lbl.set_xalign(0)
        box.append(lbl)

        self._ranges_entry = Gtk.Entry()
        self._ranges_entry.set_placeholder_text("es. 1-3, 4-6, 7-9")
        self._ranges_entry.connect('changed', lambda _: self._update_preview())
        box.append(self._ranges_entry)

        self._ranges_error = Gtk.Label()
        self._ranges_error.add_css_class('sp-hint')
        self._ranges_error.set_halign(Gtk.Align.START)
        self._ranges_error.set_visible(False)
        box.append(self._ranges_error)

        return box

    def _tab_every_n(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_start(8)
        box.set_margin_end(8)
        box.set_margin_top(12)
        box.set_margin_bottom(8)

        lbl = Gtk.Label(label="Dividi il PDF ogni N pagine:")
        lbl.set_halign(Gtk.Align.START)
        box.append(lbl)

        spin_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        adj = Gtk.Adjustment(value=1, lower=1, upper=9999, step_increment=1)
        self._n_spin = Gtk.SpinButton(adjustment=adj, climb_rate=1, digits=0)
        self._n_spin.set_value(1)
        self._n_spin.connect('value-changed', lambda _: self._update_preview())
        spin_box.append(self._n_spin)

        spin_lbl = Gtk.Label(label="pagine per file")
        spin_lbl.add_css_class('sp-hint')
        spin_box.append(spin_lbl)
        box.append(spin_box)

        self._n_hint = Gtk.Label()
        self._n_hint.add_css_class('sp-hint')
        self._n_hint.set_halign(Gtk.Align.START)
        box.append(self._n_hint)

        return box

    def _tab_single(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_start(8)
        box.set_margin_end(8)
        box.set_margin_top(12)
        box.set_margin_bottom(8)

        lbl = Gtk.Label(label="Ogni pagina diventa un file PDF separato.")
        lbl.set_halign(Gtk.Align.START)
        box.append(lbl)

        self._single_hint = Gtk.Label()
        self._single_hint.add_css_class('sp-hint')
        self._single_hint.set_halign(Gtk.Align.START)
        box.append(self._single_hint)

        return box

    def _tab_bookmarks(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_start(8)
        box.set_margin_end(8)
        box.set_margin_top(12)
        box.set_margin_bottom(8)

        lbl = Gtk.Label(
            label="Dividi il PDF in base ai segnalibri (capitoli).\n"
                  "Ogni segnalibro di primo livello diventa un file separato."
        )
        lbl.set_halign(Gtk.Align.START)
        lbl.set_wrap(True)
        lbl.set_xalign(0)
        box.append(lbl)

        self._bm_hint = Gtk.Label()
        self._bm_hint.add_css_class('sp-hint')
        self._bm_hint.set_halign(Gtk.Align.START)
        box.append(self._bm_hint)

        return box

    # ------------------------------------------------------------------ #
    # Anteprima
    # ------------------------------------------------------------------ #

    def _get_current_chunks(self):
        """Ritorna i chunk per la modalità corrente, o None in caso di errore."""
        if self._total_pages == 0:
            return None

        page = self._notebook.get_current_page()
        base = os.path.splitext(os.path.basename(self._path))[0]

        if page == 0:   # Intervalli
            text = self._ranges_entry.get_text().strip()
            if not text:
                return []
            result = parse_ranges(text, self._total_pages)
            if isinstance(result, str):
                self._ranges_error.set_text(f"⚠ {result}")
                self._ranges_error.set_visible(True)
                return None
            self._ranges_error.set_visible(False)
            return [(s, e, None) for s, e in result]

        elif page == 1:  # Ogni N
            n = int(self._n_spin.get_value())
            chunks = every_n_chunks(self._total_pages, n)
            num = len(chunks)
            self._n_hint.set_text(
                f"Verranno creati {num} file da {n} pagine "
                f"({'+ 1 file parziale' if self._total_pages % n != 0 else 'esatte'})"
            )
            return [(s, e, None) for s, e in chunks]

        elif page == 2:  # Una per file
            chunks = single_page_chunks(self._total_pages)
            self._single_hint.set_text(
                f"Verranno creati {self._total_pages} file (uno per pagina)"
            )
            return [(s, e, None) for s, e in chunks]

        elif page == 3:  # Segnalibri
            chunks = bookmark_chunks(self._bookmarks, self._total_pages)
            if not chunks:
                self._bm_hint.set_text("Nessun segnalibro trovato.")
                return []
            self._bm_hint.set_text(
                f"Trovati {len(chunks)} segnalibri → {len(chunks)} file"
            )
            return chunks

        return []

    def _update_preview(self):
        self._preview_store.clear()
        chunks = self._get_current_chunks()
        if chunks is None:
            return

        base = os.path.splitext(os.path.basename(self._path))[0]
        MAX_PREVIEW = 50

        for i, chunk in enumerate(chunks[:MAX_PREVIEW]):
            start, end = chunk[0], chunk[1]
            title = chunk[2] if len(chunk) > 2 else None
            name = chunk_filename(base, start, end, title)
            pages_str = f"pag. {start+1}" if start == end else f"pag. {start+1}–{end+1}"
            self._preview_store.append([name, pages_str])

        if len(chunks) > MAX_PREVIEW:
            self._preview_store.append([
                f"… e altri {len(chunks) - MAX_PREVIEW} file", ""
            ])

    # ------------------------------------------------------------------ #
    # Cartella output
    # ------------------------------------------------------------------ #

    def _browse_folder(self, _btn):
        dialog = Gtk.FileDialog()
        dialog.set_title("Scegli cartella di output")
        dialog.select_folder(self, None, self._on_folder_chosen)

    def _on_folder_chosen(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                self._out_entry.set_text(folder.get_path())
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Split
    # ------------------------------------------------------------------ #

    def _on_split(self, _btn):
        chunks = self._get_current_chunks()
        if not chunks:
            self._show_status("Nessun file da creare. Controlla le impostazioni.", error=True)
            return

        out_folder = self._out_entry.get_text().strip()
        if not os.path.isdir(out_folder):
            self._show_status(f"Cartella non valida: {out_folder}", error=True)
            return

        self._split_btn.set_sensitive(False)
        self._progress.set_visible(True)
        self._progress.set_fraction(0)
        self._status.set_visible(False)

        threading.Thread(
            target=self._do_split,
            args=(chunks, out_folder),
            daemon=True
        ).start()

    def _do_split(self, chunks, out_folder):
        try:
            import pypdf
            reader = pypdf.PdfReader(self._path, strict=False)
            base = os.path.splitext(os.path.basename(self._path))[0]
            total = len(chunks)
            created = []

            for i, chunk in enumerate(chunks):
                start, end = chunk[0], chunk[1]
                title = chunk[2] if len(chunk) > 2 else None

                writer = pypdf.PdfWriter()
                for page_idx in range(start, end + 1):
                    writer.add_page(reader.pages[page_idx])

                filename = chunk_filename(base, start, end, title)
                out_path = os.path.join(out_folder, filename)

                # Evita sovrascrittura
                if os.path.exists(out_path):
                    name_part, ext = os.path.splitext(filename)
                    out_path = os.path.join(out_folder, f"{name_part}_nuovo{ext}")

                with open(out_path, 'wb') as f:
                    writer.write(f)

                created.append(out_path)
                progress = (i + 1) / total
                GLib.idle_add(self._progress.set_fraction, progress)

            GLib.idle_add(self._on_split_done, created, out_folder, None)

        except Exception as e:
            GLib.idle_add(self._on_split_done, [], out_folder, str(e))

    def _on_split_done(self, created, out_folder, error):
        self._progress.set_visible(False)
        self._split_btn.set_sensitive(True)

        if error:
            self._show_status(f"Errore: {error}", error=True)
        else:
            import subprocess
            self._show_status(
                f"✓ Creati {len(created)} file in: {out_folder}",
                error=False
            )
            subprocess.Popen(['xdg-open', out_folder])

        return False

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _show_status(self, msg: str, error: bool = False):
        color = '#d73a49' if error else '#22863a'
        self._status.set_markup(f"<span foreground='{color}'>{msg}</span>")
        self._status.set_visible(True)


# --------------------------------------------------------------------------- #
# Estensione
# --------------------------------------------------------------------------- #

class PdfSplitExtension(GObject.GObject, Nautilus.MenuProvider):

    def get_file_items(self, files):
        if len(files) != 1:
            return []
        f = files[0]
        if not f.get_name().lower().endswith('.pdf'):
            return []
        if f.get_location().get_path() is None:
            return []

        item = Nautilus.MenuItem(
            name='PdfSplit::split',
            label='Dividi PDF',
            tip=f"Dividi {f.get_name()} in più file",
        )
        item.connect('activate', self._on_activate, f.get_location().get_path())
        return [item]

    def get_background_items(self, folder):
        return []

    def _on_activate(self, _item, path):
        win = PdfSplitWindow(path)
        win.present()
