"""
readme_preview.py — Nautilus extension for README preview
==========================================================
Adds a "Mostra README" entry to the right-click menu on the folder
background when a README file is present.

Installation:
    cp readme_preview.py ~/.local/share/nautilus-python/extensions/
    nautilus -q && nautilus
"""

import logging
import os
import subprocess
import threading
from urllib.parse import unquote

import gi

gi.require_version("Nautilus", "4.0")
gi.require_version("Gtk", "4.0")
gi.require_version("GLib", "2.0")

from gi.repository import GLib, GObject, Gtk, Nautilus, Pango

# Prova a caricare WebKit (per rendering Markdown)
WEBKIT_AVAILABLE = False
WEBKIT_VERSION = None
try:
    gi.require_version("WebKit", "6.0")
    from gi.repository import WebKit

    WEBKIT_AVAILABLE = True
    WEBKIT_VERSION = 6
except (ValueError, ImportError):
    try:
        gi.require_version("WebKit2", "4.1")
        from gi.repository import WebKit2 as WebKit

        WEBKIT_AVAILABLE = True
        WEBKIT_VERSION = 2
    except (ValueError, ImportError):
        pass

# Prova a caricare python3-markdown
MARKDOWN_AVAILABLE = False
try:
    import markdown

    MARKDOWN_AVAILABLE = True
except ImportError:
    pass


# --------------------------------------------------------------------------- #
# Costanti
# --------------------------------------------------------------------------- #

README_NAMES = [
    "README.md",
    "readme.md",
    "README.txt",
    "readme.txt",
    "README.rst",
    "readme.rst",
    "README",
    "readme",
]

WEBKIT_CSS = """
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 14px;
    line-height: 1.6;
    color: #24292e;
    background: #ffffff;
    padding: 20px 28px;
    margin: 0;
    max-width: 860px;
}
h1 { font-size: 1.6em; border-bottom: 1px solid #e1e4e8; padding-bottom: .3em; }
h2 { font-size: 1.3em; border-bottom: 1px solid #e1e4e8; padding-bottom: .3em; }
h3 { font-size: 1.1em; }
code {
    background: #f6f8fa; border-radius: 3px;
    padding: .2em .4em;
    font-family: 'SFMono-Regular', Consolas, monospace; font-size: 85%;
}
pre { background: #f6f8fa; border-radius: 6px; padding: 1em; overflow-x: auto; }
pre code { background: none; padding: 0; }
blockquote { border-left: 4px solid #dfe2e5; color: #6a737d; margin: 0; padding: 0 1em; }
a { color: #0366d6; }
img { max-width: 100%; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #dfe2e5; padding: 6px 13px; }
tr:nth-child(even) { background: #f6f8fa; }
"""


# --------------------------------------------------------------------------- #
# Utilità
# --------------------------------------------------------------------------- #


def find_readme(folder_path: str) -> str | None:
    for name in README_NAMES:
        path = os.path.join(folder_path, name)
        if os.path.isfile(path):
            return path
    return None


def uri_to_path(uri: str) -> str:
    if uri.startswith("file://"):
        return unquote(uri[7:])
    return uri


_UNSAFE_TAG_RE = None


def _get_unsafe_tag_re():
    import re

    global _UNSAFE_TAG_RE
    if _UNSAFE_TAG_RE is None:
        _UNSAFE_TAG_RE = re.compile(
            r"<\s*/?\s*(script|iframe|object|embed|form|input|textarea|button|link"
            r"|meta|base|applet|style)\b[^>]*>",
            re.IGNORECASE,
        )
    return _UNSAFE_TAG_RE


def _sanitize_html(html_str: str) -> str:
    import re

    sanitized = _get_unsafe_tag_re().sub("", html_str)
    sanitized = re.sub(r"\bon\w+\s*=\s*[\"'][^\"']*[\"']", "", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\bon\w+\s*=\s*\S+", "", sanitized, flags=re.IGNORECASE)
    return sanitized


def render_html(content: str, filename: str) -> str:
    import html as html_mod

    if MARKDOWN_AVAILABLE and filename.lower().endswith(".md"):
        body = markdown.markdown(
            content, extensions=["fenced_code", "tables", "nl2br", "sane_lists"]
        )
        body = _sanitize_html(body)
    else:
        escaped = html_mod.escape(content)
        body = f"<pre style='white-space:pre-wrap;word-break:break-word'>{escaped}</pre>"
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>{WEBKIT_CSS}</style></head><body>{body}</body></html>"


# --------------------------------------------------------------------------- #
# Finestra README
# --------------------------------------------------------------------------- #


class ReadmeWindow(Gtk.Window):
    def __init__(self, readme_path: str):
        filename = os.path.basename(readme_path)
        super().__init__(title=f"{filename} — README Preview")
        self.set_default_size(800, 600)
        self._readme_path = readme_path

        # Layout principale
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(box)

        # Barra superiore
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header.set_margin_start(12)
        header.set_margin_end(8)
        header.set_margin_top(6)
        header.set_margin_bottom(6)

        lbl = Gtk.Label(label=readme_path)
        lbl.set_halign(Gtk.Align.START)
        lbl.set_hexpand(True)
        lbl.set_ellipsize(Pango.EllipsizeMode.END)
        lbl.add_css_class("dim-label")
        header.append(lbl)

        open_btn = Gtk.Button(label="Apri nell'editor")
        open_btn.connect("clicked", lambda _: subprocess.Popen(["xdg-open", readme_path]))
        header.append(open_btn)

        box.append(header)
        box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Contenuto
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)

        if WEBKIT_AVAILABLE:
            # WebKit 6.0 richiede un NetworkSession esplicito
            if WEBKIT_VERSION == 6:
                network_session = WebKit.NetworkSession.new_ephemeral()
                self._webview = WebKit.WebView(network_session=network_session)
            else:
                self._webview = WebKit.WebView()
            self._webview.set_vexpand(True)
            # Disable JavaScript — README rendering does not need it,
            # and this prevents execution of inline <script> tags in Markdown.
            settings = self._webview.get_settings()
            settings.set_enable_javascript(False)
            self._webview.set_settings(settings)
            self._webview.connect("decide-policy", self._block_navigation)
            scrolled.set_child(self._webview)
        else:
            self._textview = Gtk.TextView()
            self._textview.set_editable(False)
            self._textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
            self._textview.set_monospace(True)
            self._textview.set_margin_start(16)
            self._textview.set_margin_end(16)
            self._textview.set_margin_top(12)
            scrolled.set_child(self._textview)

        box.append(scrolled)

        # Carica in thread separato
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        try:
            with open(self._readme_path, encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError as e:
            content = f"Errore nella lettura del file:\n{e}"

        filename = os.path.basename(self._readme_path)
        html = render_html(content, filename)
        GLib.idle_add(self._show, content, html)

    def _show(self, content, html):
        if WEBKIT_AVAILABLE:
            self._webview.load_html(html, "about:blank")
        else:
            self._textview.get_buffer().set_text(content)
        return False

    def _block_navigation(self, webview, decision, decision_type):
        """Block external link navigation inside the WebView."""
        try:
            if WEBKIT_VERSION == 6:
                NAV = WebKit.PolicyDecisionType.NAVIGATION_ACTION
            else:
                NAV = WebKit.WebKitPolicyDecisionType.NAVIGATION_ACTION
        except AttributeError:
            return False

        if decision_type == NAV:
            try:
                uri = decision.get_navigation_action().get_request().get_uri()
                if uri and not uri.startswith("file://") and uri != "about:blank":
                    decision.ignore()
                    return True
            except Exception as e:
                # Fail-safe: block navigation if we cannot determine the URI
                logging.warning("Navigation policy check failed, blocking for safety: %s", e)
                decision.ignore()
                return True
        return False


# --------------------------------------------------------------------------- #
# Extension
# --------------------------------------------------------------------------- #


class ReadmeExtension(GObject.GObject, Nautilus.MenuProvider):
    def get_background_items(self, folder):
        """Called on right-click on the folder background."""
        if folder is None:
            return []

        folder_path = uri_to_path(folder.get_uri())
        readme_path = find_readme(folder_path)
        if readme_path is None:
            return []

        filename = os.path.basename(readme_path)
        item = Nautilus.MenuItem(
            name="ReadmePreview::show",
            label=f"Mostra {filename}",
            tip=f"Apri una anteprima di {readme_path}",
        )
        item.connect("activate", self._on_activate, readme_path)
        return [item]

    def get_file_items(self, files):
        return []

    def _on_activate(self, _menu_item, readme_path):
        win = ReadmeWindow(readme_path)
        win.present()
