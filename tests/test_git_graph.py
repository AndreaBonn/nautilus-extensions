"""Tests for git-graph pure functions."""

import pytest


def _load_functions():
    import math
    from pathlib import Path
    source = (Path(__file__).parent.parent / "git-graph" / "git_graph.py").read_text()

    namespace = {"math": math}
    lines = source.split('\n')
    safe_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(('import gi', 'from gi.', 'gi.require_version')):
            continue
        if stripped.startswith('class ') and ('Gtk.' in stripped or 'GObject.' in stripped):
            break
        safe_lines.append(line)
    exec('\n'.join(safe_lines), namespace)
    return namespace


_ns = _load_functions()
hex_to_rgb = _ns['hex_to_rgb']


class TestHexToRgb:

    def test_white(self):
        r, g, b = hex_to_rgb("#FFFFFF")
        assert r == pytest.approx(1.0)
        assert g == pytest.approx(1.0)
        assert b == pytest.approx(1.0)

    def test_black(self):
        r, g, b = hex_to_rgb("#000000")
        assert r == pytest.approx(0.0)
        assert g == pytest.approx(0.0)
        assert b == pytest.approx(0.0)

    def test_red(self):
        r, g, b = hex_to_rgb("#FF0000")
        assert r == pytest.approx(1.0)
        assert g == pytest.approx(0.0)
        assert b == pytest.approx(0.0)

    def test_without_hash(self):
        r, g, b = hex_to_rgb("00FF00")
        assert r == pytest.approx(0.0)
        assert g == pytest.approx(1.0)
        assert b == pytest.approx(0.0)

    def test_returns_normalized_values(self):
        r, g, b = hex_to_rgb("#808080")
        assert 0.49 < r < 0.51
        assert 0.49 < g < 0.51
        assert 0.49 < b < 0.51
