"""Tests for readme-viewer pure functions."""

import os
import tempfile
from pathlib import Path


def _load_functions():
    source = (Path(__file__).parent.parent / "readme-viewer" / "readme_preview.py").read_text()
    namespace = {}
    exec("import os, logging, subprocess, threading", namespace)
    exec("from urllib.parse import unquote", namespace)
    lines = source.split("\n")
    safe_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("import gi", "from gi.", "gi.require_version")):
            continue
        # Salta i try/except per WebKit (richiedono gi)
        if "gi.require_version" in stripped:
            continue
        if stripped.startswith("class ") and ("Gtk." in stripped or "GObject." in stripped):
            break
        safe_lines.append(line)
    exec("\n".join(safe_lines), namespace)
    return namespace


_ns = _load_functions()
find_readme = _ns["find_readme"]
uri_to_path = _ns["uri_to_path"]
render_html = _ns["render_html"]
_sanitize_html = _ns["_sanitize_html"]


class TestFindReadme:
    def test_find_readme_finds_readme_md(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            readme = os.path.join(tmpdir, "README.md")
            with open(readme, "w") as f:
                f.write("# Hello")
            result = find_readme(tmpdir)
            assert result == readme

    def test_find_readme_finds_readme_txt(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            readme = os.path.join(tmpdir, "README.txt")
            with open(readme, "w") as f:
                f.write("Hello")
            result = find_readme(tmpdir)
            assert result == readme

    def test_find_readme_returns_none_when_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = find_readme(tmpdir)
            assert result is None

    def test_find_readme_prefers_readme_md_over_readme_txt(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            md = os.path.join(tmpdir, "README.md")
            txt = os.path.join(tmpdir, "README.txt")
            with open(md, "w") as f:
                f.write("# MD")
            with open(txt, "w") as f:
                f.write("TXT")
            result = find_readme(tmpdir)
            # README.md viene prima nella lista README_NAMES
            assert result == md

    def test_find_readme_lowercase_readme_md(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            readme = os.path.join(tmpdir, "readme.md")
            with open(readme, "w") as f:
                f.write("# lower")
            result = find_readme(tmpdir)
            assert result == readme

    def test_find_readme_nonexistent_directory_returns_none(self):
        result = find_readme("/nonexistent/directory")
        assert result is None


class TestUriToPath:
    def test_uri_to_path_file_uri_strips_prefix(self):
        result = uri_to_path("file:///home/user/docs")
        assert result == "/home/user/docs"

    def test_uri_to_path_encoded_spaces(self):
        result = uri_to_path("file:///home/user/my%20folder")
        assert result == "/home/user/my folder"

    def test_uri_to_path_non_file_uri_returned_as_is(self):
        result = uri_to_path("/absolute/path")
        assert result == "/absolute/path"

    def test_uri_to_path_encoded_special_chars(self):
        result = uri_to_path("file:///home/user/file%28copy%29.md")
        assert result == "/home/user/file(copy).md"

    def test_uri_to_path_empty_string(self):
        result = uri_to_path("")
        assert result == ""


class TestRenderHtml:
    def test_render_html_plain_text_file_wraps_in_pre(self):
        html = render_html("hello world", "notes.txt")
        assert "<pre" in html
        assert "hello world" in html

    def test_render_html_returns_valid_html_document(self):
        html = render_html("# Title", "README.md")
        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "</html>" in html

    def test_render_html_escapes_html_special_chars_in_plain(self):
        html = render_html("<script>alert(1)</script>", "notes.txt")
        # Both conditions must hold: raw tag absent AND escaped version present
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_render_html_includes_css_style(self):
        html = render_html("content", "README.md")
        assert "<style>" in html

    def test_render_html_empty_content(self):
        html = render_html("", "README.md")
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html

    def test_render_markdown_heading_produces_h1(self):
        html = render_html("# Title", "README.md")
        assert "<h1>" in html or "<h1" in html

    def test_render_markdown_bold_produces_strong(self):
        html = render_html("**bold text**", "README.md")
        assert "<strong>" in html or "<b>" in html

    def test_render_markdown_code_block(self):
        html = render_html("```python\nprint('hi')\n```", "README.md")
        assert "<code>" in html or "<pre>" in html

    def test_render_markdown_list(self):
        html = render_html("- item one\n- item two", "README.md")
        assert "<li>" in html

    def test_render_non_md_file_skips_markdown(self):
        html = render_html("# Not a heading", "notes.txt")
        assert "<h1>" not in html
        assert "# Not a heading" in html


class TestSanitizeHtml:
    def test_removes_script_tags(self):
        result = _sanitize_html('<p>Hello</p><script>alert("xss")</script>')
        assert "<script" not in result
        assert "<p>Hello</p>" in result

    def test_removes_iframe_tags(self):
        result = _sanitize_html('<iframe src="evil.com"></iframe>')
        assert "<iframe" not in result

    def test_removes_event_handlers_double_quotes(self):
        result = _sanitize_html('<img src="x.png" onerror="alert(1)">')
        assert "onerror" not in result
        assert "src" in result

    def test_removes_event_handlers_single_quotes(self):
        result = _sanitize_html("<div onclick='steal()'>click</div>")
        assert "onclick" not in result
        assert "click" in result

    def test_preserves_safe_tags(self):
        safe = "<h1>Title</h1><p>Text</p><a href='link'>link</a><code>code</code>"
        result = _sanitize_html(safe)
        assert result == safe

    def test_removes_object_embed_form(self):
        result = _sanitize_html('<object data="x"></object><embed src="y"><form action="z">')
        assert "<object" not in result
        assert "<embed" not in result
        assert "<form" not in result

    def test_case_insensitive(self):
        result = _sanitize_html("<SCRIPT>bad</SCRIPT><ScRiPt>bad</ScRiPt>")
        assert "script" not in result.lower()

    def test_removes_style_tag(self):
        result = _sanitize_html("<style>body { background: url('evil') }</style>")
        assert "<style" not in result

    def test_removes_javascript_href(self):
        result = _sanitize_html('<a href="javascript:alert(1)">click</a>')
        assert "javascript:" not in result

    def test_removes_javascript_href_case_insensitive(self):
        result = _sanitize_html('<a href="JavaScript:alert(1)">click</a>')
        assert "javascript:" not in result.lower()

    def test_removes_data_uri_in_src(self):
        result = _sanitize_html('<img src="data:text/html,<script>alert(1)</script>">')
        assert "data:" not in result.lower() or "&#blocked;" in result
