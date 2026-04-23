"""
dockerfile_analyzer.py — Estensione Nautilus per analisi Dockerfile
====================================================================
Aggiunge "Analizza Dockerfile" nel menu tasto destro su file Dockerfile.
Mostra struttura, istruzioni raggruppate, best practice e suggerimenti.

Installazione:
    cp dockerfile_analyzer.py ~/.local/share/nautilus-python/extensions/
    nautilus -q && nautilus

Dipendenze: solo stdlib Python
"""

import os
import re
import threading
from urllib.parse import unquote, urlparse

import gi

gi.require_version("Nautilus", "4.0")
gi.require_version("Gtk", "4.0")
gi.require_version("GLib", "2.0")

from gi.repository import GLib, GObject, Gtk, Nautilus, Pango

# --------------------------------------------------------------------------- #
# Costanti
# --------------------------------------------------------------------------- #

WINDOW_W = 1000
WINDOW_H = 700

DOCKERFILE_NAMES = [
    "Dockerfile",
    "dockerfile",
    "Dockerfile.dev",
    "Dockerfile.prod",
    "Dockerfile.test",
    "Dockerfile.local",
    "Dockerfile.staging",
]

# Colori per istruzione
INSTRUCTION_COLORS = {
    "FROM": "#0366d6",  # blu
    "RUN": "#e36209",  # arancione
    "COPY": "#22863a",  # verde
    "ADD": "#22863a",
    "ENV": "#6f42c1",  # viola
    "ARG": "#6f42c1",
    "EXPOSE": "#d73a49",  # rosso
    "WORKDIR": "#0366d6",
    "CMD": "#e36209",
    "ENTRYPOINT": "#e36209",
    "LABEL": "#6a737d",  # grigio
    "USER": "#b31d28",
    "VOLUME": "#22863a",
    "HEALTHCHECK": "#d73a49",
    "ONBUILD": "#6a737d",
    "SHELL": "#6a737d",
    "STOPSIGNAL": "#6a737d",
}

CSS = b"""
.df-info-bar {
    background-color: #f6f8fa;
    border-bottom: 1px solid #e1e4e8;
    padding: 6px 12px;
}
.df-stat-box {
    background-color: #ffffff;
    border: 1px solid #e1e4e8;
    border-radius: 6px;
    padding: 8px 14px;
    margin: 4px;
}
.df-stat-title {
    font-size: 11px;
    color: #6a737d;
}
.df-stat-value {
    font-size: 15px;
    font-weight: bold;
    color: #24292e;
}
.warn-high {
    color: #d73a49;
    font-weight: bold;
}
.warn-medium {
    color: #e36209;
    font-weight: bold;
}
.warn-low {
    color: #6a737d;
}
.warn-ok {
    color: #22863a;
}
.mono {
    font-family: monospace;
    font-size: 13px;
}
.section-title {
    font-weight: bold;
    font-size: 13px;
    margin-top: 8px;
}
"""


# --------------------------------------------------------------------------- #
# Parser Dockerfile
# --------------------------------------------------------------------------- #


def parse_dockerfile(path: str) -> dict:
    """
    Parsa un Dockerfile e ritorna un dict con tutte le informazioni estratte.
    """
    result = {
        "path": path,
        "error": None,
        "raw_lines": [],
        "instructions": [],  # lista di (line_num, instruction, args)
        "stages": [],  # multi-stage builds
        "from_images": [],
        "env_vars": {},
        "args": {},
        "exposed_ports": [],
        "volumes": [],
        "labels": {},
        "run_commands": [],
        "copy_adds": [],
        "users": [],
        "workdirs": [],
        "cmd": None,
        "entrypoint": None,
        "healthcheck": None,
        "num_layers": 0,
        "warnings": [],
    }

    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            raw = f.read()
        result["raw_lines"] = raw.splitlines()
    except OSError as e:
        result["error"] = str(e)
        return result

    # Parsa istruzione per istruzione (gestisce line continuation con \)
    lines = result["raw_lines"]
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Salta commenti e righe vuote
        if not line or line.startswith("#"):
            i += 1
            continue

        # Gestisce continuazione con backslash
        while line.endswith("\\") and i + 1 < len(lines):
            i += 1
            line = line[:-1] + " " + lines[i].strip()

        # Estrai istruzione e argomenti
        parts = line.split(None, 1)
        if not parts:
            i += 1
            continue

        instruction = parts[0].upper()
        args = parts[1].strip() if len(parts) > 1 else ""
        line_num = i + 1

        result["instructions"].append(
            {
                "line": line_num,
                "instruction": instruction,
                "args": args,
                "raw": line,
            }
        )

        # Estrai dati specifici per istruzione
        if instruction == "FROM":
            _parse_from(args, result)
        elif instruction == "ENV":
            _parse_env(args, result)
        elif instruction == "ARG":
            _parse_arg(args, result)
        elif instruction == "EXPOSE":
            ports = args.split()
            result["exposed_ports"].extend(ports)
        elif instruction == "VOLUME":
            vols = re.findall(r"[\w/\-\.]+", args)
            result["volumes"].extend(vols)
        elif instruction == "LABEL":
            _parse_label(args, result)
        elif instruction == "RUN":
            result["run_commands"].append({"line": line_num, "cmd": args})
        elif instruction in ("COPY", "ADD"):
            result["copy_adds"].append({"line": line_num, "instruction": instruction, "args": args})
        elif instruction == "USER":
            result["users"].append({"line": line_num, "user": args})
        elif instruction == "WORKDIR":
            result["workdirs"].append({"line": line_num, "path": args})
        elif instruction == "CMD":
            result["cmd"] = {"line": line_num, "args": args}
        elif instruction == "ENTRYPOINT":
            result["entrypoint"] = {"line": line_num, "args": args}
        elif instruction == "HEALTHCHECK":
            result["healthcheck"] = {"line": line_num, "args": args}

        i += 1

    # Conta layer (ogni FROM/RUN/COPY/ADD aggiunge un layer)
    result["num_layers"] = sum(
        1 for ins in result["instructions"] if ins["instruction"] in ("FROM", "RUN", "COPY", "ADD")
    )

    # Analisi best practice
    result["warnings"] = _analyze_best_practices(result)

    return result


def _parse_from(args: str, result: dict):
    # FROM image[:tag] [AS name]
    parts = args.split()
    image = parts[0] if parts else args
    alias = parts[2] if len(parts) >= 3 and parts[1].upper() == "AS" else None
    stage = {"image": image, "alias": alias, "index": len(result["from_images"])}
    result["from_images"].append(image)
    result["stages"].append(stage)


def _parse_env(args: str, result: dict):
    # ENV KEY=VALUE o ENV KEY VALUE
    if "=" in args:
        for pair in re.findall(r'(\w+)=(".*?"|\'.*?\'|\S+)', args):
            result["env_vars"][pair[0]] = pair[1].strip("\"'")
    else:
        parts = args.split(None, 1)
        if len(parts) == 2:
            result["env_vars"][parts[0]] = parts[1]


def _parse_arg(args: str, result: dict):
    if "=" in args:
        k, v = args.split("=", 1)
        result["args"][k.strip()] = v.strip()
    else:
        result["args"][args.strip()] = None


def _parse_label(args: str, result: dict):
    for pair in re.findall(r'(\S+)=(".*?"|\'.*?\'|\S+)', args):
        result["labels"][pair[0]] = pair[1].strip("\"'")


def _analyze_best_practices(data: dict) -> list:
    """
    Analizza il Dockerfile e ritorna una lista di warning con severità.
    Ogni warning: {'level': 'high'|'medium'|'low'|'ok', 'title': str, 'detail': str}
    """
    warnings = []

    def warn(level, title, detail=""):
        warnings.append({"level": level, "title": title, "detail": detail})

    data["instructions"]
    run_cmds = data["run_commands"]
    from_images = data["from_images"]

    # 1. Immagine base latest
    for img in from_images:
        if img.endswith(":latest") or (":" not in img and "@" not in img):
            warn(
                "high",
                f"Immagine senza tag specifico: {img}",
                "Usa un tag preciso (es. python:3.11-slim) per build riproducibili.",
            )

    # 2. Running as root
    if not data["users"]:
        warn(
            "high",
            "Container eseguito come root",
            "Aggiungi USER nonroot o crea un utente dedicato per sicurezza.",
        )

    # 3. apt-get senza --no-install-recommends
    for run in run_cmds:
        cmd = run["cmd"]
        if "apt-get install" in cmd and "--no-install-recommends" not in cmd:
            warn(
                "medium",
                f"apt-get install senza --no-install-recommends (riga {run['line']})",
                "Aggiunge pacchetti non necessari aumentando la dimensione dell'immagine.",
            )

    # 4. apt-get senza pulizia cache
    for run in run_cmds:
        cmd = run["cmd"]
        if "apt-get install" in cmd and "rm -rf /var/lib/apt/lists" not in cmd:
            warn(
                "medium",
                f"apt-get install senza pulizia cache (riga {run['line']})",
                'Aggiungi "&& rm -rf /var/lib/apt/lists/*" per ridurre la dimensione del layer.',
            )

    # 5. pip install senza --no-cache-dir
    for run in run_cmds:
        cmd = run["cmd"]
        if "pip install" in cmd and "--no-cache-dir" not in cmd:
            warn(
                "medium",
                f"pip install senza --no-cache-dir (riga {run['line']})",
                "Usa --no-cache-dir per evitare di salvare la cache pip nell'immagine.",
            )

    # 6. pip install senza versioni fissate
    for run in run_cmds:
        cmd = run["cmd"]
        if "pip install" in cmd and "requirements" not in cmd:
            pkgs = re.findall(r"pip install\s+([\w\-\s]+)", cmd)
            for pkg_str in pkgs:
                pkgs_list = pkg_str.strip().split()
                unversioned = [
                    p for p in pkgs_list if p and "==" not in p and not p.startswith("-")
                ]
                if unversioned:
                    warn(
                        "medium",
                        f"Dipendenze senza versione fissata (riga {run['line']}): {', '.join(unversioned[:3])}",
                        "Specifica le versioni (es. requests==2.31.0) per build riproducibili.",
                    )

    # 7. ADD invece di COPY
    for ca in data["copy_adds"]:
        if ca["instruction"] == "ADD" and not re.search(r"https?://", ca["args"]):
            warn(
                "low",
                f"ADD invece di COPY (riga {ca['line']})",
                "Usa COPY invece di ADD a meno che tu non debba estrarre archivi o scaricare URL.",
            )

    # 8. COPY . . (copia tutto il contesto)
    for ca in data["copy_adds"]:
        args = ca["args"].strip()
        if re.match(r"^\.[\s]+\.", args) or args in (". .", ". ./"):
            warn(
                "low",
                f"COPY . . copia l'intero contesto (riga {ca['line']})",
                "Considera un .dockerignore accurato o copia solo i file necessari.",
            )

    # 9. Nessun HEALTHCHECK
    if not data["healthcheck"]:
        warn(
            "low",
            "Nessun HEALTHCHECK definito",
            "Aggiungi un HEALTHCHECK per permettere a Docker/K8s di monitorare il container.",
        )

    # 10. Molti RUN separati
    if len(run_cmds) > 5:
        warn(
            "medium",
            f"{len(run_cmds)} istruzioni RUN separate",
            "Considera di unire i RUN con && per ridurre il numero di layer.",
        )

    # 11. Multi-stage build
    if len(data["stages"]) > 1:
        warn(
            "ok",
            f"Multi-stage build rilevato ({len(data['stages'])} stage)",
            "Ottimo! I multi-stage build riducono la dimensione dell'immagine finale.",
        )

    # 12. .dockerignore
    folder = os.path.dirname(data["path"])
    if not os.path.exists(os.path.join(folder, ".dockerignore")):
        warn(
            "low",
            "Nessun .dockerignore trovato",
            "Aggiungi un .dockerignore per escludere file non necessari dal contesto di build.",
        )

    # 13. Secrets in ENV
    secret_patterns = ["password", "secret", "token", "api_key", "private_key", "passwd"]
    for k in data["env_vars"]:
        if any(p in k.lower() for p in secret_patterns):
            warn(
                "high",
                f"Possibile secret in ENV: {k}",
                "Non mettere segreti nelle variabili ENV — finiscono nell'immagine e nella history.",
            )

    # 14. Nessun WORKDIR — uso di path relativi
    if not data["workdirs"]:
        warn(
            "low",
            "Nessun WORKDIR definito",
            "Definisci un WORKDIR esplicito invece di usare la root del container.",
        )

    # Ordina: high → medium → low → ok
    order = {"high": 0, "medium": 1, "low": 2, "ok": 3}
    warnings.sort(key=lambda w: order.get(w["level"], 99))

    return warnings


# --------------------------------------------------------------------------- #
# Finestra
# --------------------------------------------------------------------------- #


class DockerfileWindow(Gtk.Window):
    def __init__(self, path: str):
        filename = os.path.basename(path)
        super().__init__(title=f"{filename} — Dockerfile Analyzer")
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
        lbl = Gtk.Label(label="Analisi Dockerfile...")
        lbl.add_css_class("dim-label")
        box.append(spinner)
        box.append(lbl)
        self._spinner_box = box
        self._root.append(box)

    def _load(self):
        data = parse_dockerfile(self._path)
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
    # Contenuto
    # ------------------------------------------------------------------ #

    def _build_content(self, data: dict):

        # Conta warning per severità
        highs = sum(1 for w in data["warnings"] if w["level"] == "high")
        mediums = sum(1 for w in data["warnings"] if w["level"] == "medium")
        lows = sum(1 for w in data["warnings"] if w["level"] == "low")
        sum(1 for w in data["warnings"] if w["level"] == "ok")

        # --- Info bar ---
        info_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        info_bar.add_css_class("df-info-bar")
        info_bar.set_margin_start(4)
        info_bar.set_margin_end(8)

        self._stat(info_bar, "Stage", str(len(data["stages"])))
        self._stat(info_bar, "Layer", str(data["num_layers"]))
        self._stat(info_bar, "RUN", str(len(data["run_commands"])))
        self._stat(
            info_bar, "Porte", str(len(data["exposed_ports"])) if data["exposed_ports"] else "—"
        )
        self._stat(info_bar, "ENV", str(len(data["env_vars"])))
        self._stat(info_bar, "🔴 Critici", str(highs))
        self._stat(info_bar, "🟠 Medi", str(mediums))
        self._stat(info_bar, "🔵 Info", str(lows))

        self._root.append(info_bar)
        self._root.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # --- Notebook ---
        notebook = Gtk.Notebook()
        notebook.set_vexpand(True)
        self._root.append(notebook)

        notebook.append_page(self._tab_overview(data), Gtk.Label(label="🐳 Overview"))
        notebook.append_page(
            self._tab_warnings(data), Gtk.Label(label=f"⚠ Best Practice ({len(data['warnings'])})")
        )
        notebook.append_page(self._tab_instructions(data), Gtk.Label(label="📋 Istruzioni"))
        notebook.append_page(self._tab_source(data), Gtk.Label(label="📄 Sorgente"))

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

    def _stat(self, box, title, value):
        sb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        sb.add_css_class("df-stat-box")
        t = Gtk.Label(label=title)
        t.add_css_class("df-stat-title")
        t.set_halign(Gtk.Align.START)
        v = Gtk.Label(label=str(value))
        v.add_css_class("df-stat-value")
        v.set_halign(Gtk.Align.START)
        sb.append(t)
        sb.append(v)
        box.append(sb)

    # ------------------------------------------------------------------ #
    # Tab Overview
    # ------------------------------------------------------------------ #

    def _tab_overview(self, data: dict) -> Gtk.Widget:
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        outer.set_margin_start(16)
        outer.set_margin_end(16)
        outer.set_margin_top(12)
        outer.set_margin_bottom(12)

        # --- Stage / immagini base ---
        self._section(outer, "Immagini base / Stage")
        for i, stage in enumerate(data["stages"]):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            idx_lbl = Gtk.Label(label=f"Stage {i}")
            idx_lbl.set_width_chars(8)
            idx_lbl.set_halign(Gtk.Align.START)
            idx_lbl.add_css_class("dim-label")

            img_lbl = Gtk.Label(label=stage["image"])
            img_lbl.set_halign(Gtk.Align.START)
            img_lbl.add_css_class("mono")
            safe_img = GLib.markup_escape_text(stage["image"])
            img_lbl.set_markup(
                f"<span foreground='{INSTRUCTION_COLORS['FROM']}'><b>{safe_img}</b></span>"
            )

            row.append(idx_lbl)
            row.append(img_lbl)
            if stage["alias"]:
                alias_lbl = Gtk.Label(label=f"  AS {stage['alias']}")
                alias_lbl.add_css_class("dim-label")
                row.append(alias_lbl)
            outer.append(row)

        # --- Porte ---
        if data["exposed_ports"]:
            self._section(outer, "Porte esposte")
            ports_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            for port in data["exposed_ports"]:
                chip = Gtk.Label(label=port)
                safe_port = GLib.markup_escape_text(port)
                chip.set_markup(
                    f"<span foreground='{INSTRUCTION_COLORS['EXPOSE']}'><b>{safe_port}</b></span>"
                )
                chip.add_css_class("mono")
                ports_box.append(chip)
            outer.append(ports_box)

        # --- ENV ---
        if data["env_vars"]:
            self._section(outer, "Variabili d'ambiente (ENV)")
            store = Gtk.ListStore(str, str)
            for k, v in data["env_vars"].items():
                store.append([k, v])
            tv = self._simple_treeview(store, ["Chiave", "Valore"], [180, 300])
            outer.append(tv)

        # --- ARG ---
        if data["args"]:
            self._section(outer, "Argomenti di build (ARG)")
            store = Gtk.ListStore(str, str)
            for k, v in data["args"].items():
                store.append([k, v or "(nessun default)"])
            tv = self._simple_treeview(store, ["Argomento", "Default"], [180, 200])
            outer.append(tv)

        # --- WORKDIR ---
        if data["workdirs"]:
            self._section(outer, "Directory di lavoro")
            for wd in data["workdirs"]:
                lbl = Gtk.Label(label=wd["path"])
                lbl.add_css_class("mono")
                lbl.set_halign(Gtk.Align.START)
                outer.append(lbl)

        # --- USER ---
        if data["users"]:
            self._section(outer, "Utente")
            for u in data["users"]:
                lbl = Gtk.Label(label=u["user"])
                lbl.add_css_class("mono")
                lbl.set_halign(Gtk.Align.START)
                outer.append(lbl)

        # --- CMD / ENTRYPOINT ---
        if data["cmd"] or data["entrypoint"]:
            self._section(outer, "Comando di avvio")
            if data["entrypoint"]:
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                row.append(self._tag_label("ENTRYPOINT"))
                lbl = Gtk.Label(label=data["entrypoint"]["args"])
                lbl.add_css_class("mono")
                lbl.set_halign(Gtk.Align.START)
                row.append(lbl)
                outer.append(row)
            if data["cmd"]:
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                row.append(self._tag_label("CMD"))
                lbl = Gtk.Label(label=data["cmd"]["args"])
                lbl.add_css_class("mono")
                lbl.set_halign(Gtk.Align.START)
                row.append(lbl)
                outer.append(row)

        # --- HEALTHCHECK ---
        if data["healthcheck"]:
            self._section(outer, "Healthcheck")
            lbl = Gtk.Label(label=data["healthcheck"]["args"])
            lbl.add_css_class("mono")
            lbl.set_halign(Gtk.Align.START)
            outer.append(lbl)

        # --- LABELS ---
        if data["labels"]:
            self._section(outer, "Label")
            store = Gtk.ListStore(str, str)
            for k, v in data["labels"].items():
                store.append([k, v])
            tv = self._simple_treeview(store, ["Chiave", "Valore"], [200, 300])
            outer.append(tv)

        # --- VOLUMES ---
        if data["volumes"]:
            self._section(outer, "Volumi")
            for v in data["volumes"]:
                lbl = Gtk.Label(label=v)
                lbl.add_css_class("mono")
                lbl.set_halign(Gtk.Align.START)
                outer.append(lbl)

        scrolled.set_child(outer)
        return scrolled

    # ------------------------------------------------------------------ #
    # Tab Best Practice
    # ------------------------------------------------------------------ #

    def _tab_warnings(self, data: dict) -> Gtk.Widget:
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        outer.set_margin_start(16)
        outer.set_margin_end(16)
        outer.set_margin_top(12)
        outer.set_margin_bottom(12)

        if not data["warnings"]:
            lbl = Gtk.Label(label="✓ Nessun problema rilevato!")
            lbl.add_css_class("warn-ok")
            outer.append(lbl)
            scrolled.set_child(outer)
            return scrolled

        level_icons = {"high": "🔴", "medium": "🟠", "low": "🔵", "ok": "✅"}
        level_css = {
            "high": "warn-high",
            "medium": "warn-medium",
            "low": "warn-low",
            "ok": "warn-ok",
        }

        for w in data["warnings"]:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            card.set_margin_bottom(8)

            # Titolo
            title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            icon = Gtk.Label(label=level_icons.get(w["level"], "•"))
            title_lbl = Gtk.Label(label=w["title"])
            title_lbl.add_css_class(level_css.get(w["level"], ""))
            title_lbl.set_halign(Gtk.Align.START)
            title_box.append(icon)
            title_box.append(title_lbl)
            card.append(title_box)

            # Dettaglio
            if w.get("detail"):
                detail_lbl = Gtk.Label(label=w["detail"])
                detail_lbl.add_css_class("dim-label")
                detail_lbl.set_halign(Gtk.Align.START)
                detail_lbl.set_margin_start(24)
                detail_lbl.set_wrap(True)
                detail_lbl.set_xalign(0)
                card.append(detail_lbl)

            outer.append(card)
            outer.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        scrolled.set_child(outer)
        return scrolled

    # ------------------------------------------------------------------ #
    # Tab Istruzioni
    # ------------------------------------------------------------------ #

    def _tab_instructions(self, data: dict) -> Gtk.Widget:
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        store = Gtk.ListStore(str, str, str)
        for ins in data["instructions"]:
            store.append(
                [
                    str(ins["line"]),
                    ins["instruction"],
                    ins["args"],
                ]
            )

        tv = Gtk.TreeView(model=store)
        tv.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        tv.add_css_class("mono")

        # Colonna riga
        r = Gtk.CellRendererText()
        r.set_property("foreground", "#6a737d")
        r.set_property("xalign", 1.0)
        c = Gtk.TreeViewColumn("Riga", r, text=0)
        c.set_min_width(50)
        tv.append_column(c)

        # Colonna istruzione con colore
        r = Gtk.CellRendererText()
        r.set_property("weight", Pango.Weight.BOLD)
        c = Gtk.TreeViewColumn("Istruzione")
        c.pack_start(r, True)
        c.set_min_width(120)

        def set_instr_color(col, cell, model, iter_, _):
            instr = model.get_value(iter_, 1)
            cell.set_property("text", instr)
            cell.set_property("foreground", INSTRUCTION_COLORS.get(instr, "#24292e"))

        c.set_cell_data_func(r, set_instr_color, None)
        tv.append_column(c)

        # Colonna argomenti
        r = Gtk.CellRendererText()
        r.set_property("ellipsize", Pango.EllipsizeMode.END)
        c = Gtk.TreeViewColumn("Argomenti", r, text=2)
        c.set_resizable(True)
        c.set_expand(True)
        tv.append_column(c)

        scrolled.set_child(tv)
        return scrolled

    # ------------------------------------------------------------------ #
    # Tab Sorgente
    # ------------------------------------------------------------------ #

    def _tab_source(self, data: dict) -> Gtk.Widget:
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        tv = Gtk.TextView()
        tv.set_editable(False)
        tv.set_monospace(True)
        tv.set_margin_start(12)
        tv.set_margin_end(12)
        tv.set_margin_top(8)

        buf = tv.get_buffer()
        source = "\n".join(data["raw_lines"])
        buf.set_text(source)

        # Evidenzia istruzioni con tag colore
        for ins in data["instructions"]:
            line_idx = ins["line"] - 1
            instr = ins["instruction"]
            color = INSTRUCTION_COLORS.get(instr)
            if not color:
                continue

            start = buf.get_iter_at_line(line_idx)
            end = buf.get_iter_at_line(line_idx)
            end.forward_chars(len(instr))

            tag = buf.create_tag(None, foreground=color, weight=Pango.Weight.BOLD)
            buf.apply_tag(tag, start, end)

        scrolled.set_child(tv)
        return scrolled

    # ------------------------------------------------------------------ #
    # Helpers UI
    # ------------------------------------------------------------------ #

    def _section(self, box, title: str):
        lbl = Gtk.Label()
        safe_title = GLib.markup_escape_text(title)
        lbl.set_markup(f"<b>{safe_title}</b>")
        lbl.set_halign(Gtk.Align.START)
        lbl.set_margin_top(8)
        box.append(lbl)

    def _tag_label(self, text: str) -> Gtk.Label:
        lbl = Gtk.Label()
        color = INSTRUCTION_COLORS.get(text, "#24292e")
        safe_text = GLib.markup_escape_text(text)
        lbl.set_markup(f"<span foreground='{color}'><b>{safe_text}</b></span>")
        lbl.add_css_class("mono")
        lbl.set_width_chars(12)
        lbl.set_halign(Gtk.Align.START)
        return lbl

    def _simple_treeview(self, store, headers, widths) -> Gtk.TreeView:
        tv = Gtk.TreeView(model=store)
        tv.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        tv.add_css_class("mono")
        for i, (h, w) in enumerate(zip(headers, widths)):
            r = Gtk.CellRendererText()
            r.set_property("ellipsize", Pango.EllipsizeMode.END)
            c = Gtk.TreeViewColumn(h, r, text=i)
            c.set_resizable(True)
            c.set_min_width(w)
            tv.append_column(c)
        return tv


# --------------------------------------------------------------------------- #
# Estensione
# --------------------------------------------------------------------------- #


class DockerfileExtension(GObject.GObject, Nautilus.MenuProvider):
    def get_file_items(self, files):
        if len(files) != 1:
            return []
        f = files[0]
        if not self._is_dockerfile(f.get_name()):
            return []
        item = Nautilus.MenuItem(
            name="DockerfileAnalyzer::show",
            label="Analizza Dockerfile",
            tip=f"Analizza {f.get_name()}",
        )
        item.connect("activate", self._on_activate, f.get_location().get_path())
        return [item]

    def get_background_items(self, folder):
        """Mostra la voce anche sul menu della cartella se contiene un Dockerfile."""
        if folder is None:
            return []

        folder_path = unquote(urlparse(folder.get_uri()).path)
        for name in DOCKERFILE_NAMES:
            path = os.path.join(folder_path, name)
            if os.path.isfile(path):
                item = Nautilus.MenuItem(
                    name="DockerfileAnalyzer::folder",
                    label=f"Analizza {name}",
                    tip="Analizza il Dockerfile in questa cartella",
                )
                item.connect("activate", self._on_activate, path)
                return [item]
        return []

    def _is_dockerfile(self, name: str) -> bool:
        return name in DOCKERFILE_NAMES or name.lower().startswith("dockerfile")

    def _on_activate(self, _item, path):
        win = DockerfileWindow(path)
        win.present()
