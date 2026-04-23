"""Tests for dockerfile-analyzer pure functions."""

import os
import tempfile
from pathlib import Path


def _load_functions():
    source = (
        Path(__file__).parent.parent / "dockerfile-analyzer" / "dockerfile_analyzer.py"
    ).read_text()
    namespace = {}
    exec("import os, re, threading", namespace)
    exec("from urllib.parse import unquote, urlparse", namespace)
    lines = source.split("\n")
    safe_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("import gi", "from gi.", "gi.require_version")):
            continue
        if stripped.startswith("class ") and ("Gtk." in stripped or "GObject." in stripped):
            break
        safe_lines.append(line)
    exec("\n".join(safe_lines), namespace)
    return namespace


_ns = _load_functions()
parse_dockerfile = _ns["parse_dockerfile"]
_parse_from = _ns["_parse_from"]
_parse_env = _ns["_parse_env"]
_parse_arg = _ns["_parse_arg"]
_parse_label = _ns["_parse_label"]
_analyze_best_practices = _ns["_analyze_best_practices"]


def _make_dockerfile(content: str) -> str:
    """Crea un Dockerfile temporaneo e ritorna il path."""
    with tempfile.NamedTemporaryFile(mode="w", prefix="Dockerfile", suffix="", delete=False) as f:
        f.write(content)
        return f.name


class TestParseDockerfile:
    def test_parse_dockerfile_extracts_from_image(self):
        path = _make_dockerfile("FROM python:3.11-slim\n")
        try:
            result = parse_dockerfile(path)
            assert result["from_images"] == ["python:3.11-slim"]
            assert len(result["stages"]) == 1
        finally:
            os.unlink(path)

    def test_parse_dockerfile_multistage_builds(self):
        content = "FROM node:18 AS builder\nFROM nginx:alpine\n"
        path = _make_dockerfile(content)
        try:
            result = parse_dockerfile(path)
            assert len(result["stages"]) == 2
            assert result["stages"][0]["alias"] == "builder"
            assert result["stages"][1]["alias"] is None
        finally:
            os.unlink(path)

    def test_parse_dockerfile_extracts_env_vars(self):
        path = _make_dockerfile("FROM alpine\nENV APP_PORT=8080\n")
        try:
            result = parse_dockerfile(path)
            assert "APP_PORT" in result["env_vars"]
            assert result["env_vars"]["APP_PORT"] == "8080"
        finally:
            os.unlink(path)

    def test_parse_dockerfile_extracts_exposed_ports(self):
        path = _make_dockerfile("FROM alpine\nEXPOSE 8080 443\n")
        try:
            result = parse_dockerfile(path)
            assert "8080" in result["exposed_ports"]
            assert "443" in result["exposed_ports"]
        finally:
            os.unlink(path)

    def test_parse_dockerfile_extracts_run_commands(self):
        path = _make_dockerfile("FROM alpine\nRUN apk add curl\n")
        try:
            result = parse_dockerfile(path)
            assert len(result["run_commands"]) == 1
            assert "apk add curl" in result["run_commands"][0]["cmd"]
        finally:
            os.unlink(path)

    def test_parse_dockerfile_extracts_workdir(self):
        path = _make_dockerfile("FROM alpine\nWORKDIR /app\n")
        try:
            result = parse_dockerfile(path)
            assert len(result["workdirs"]) == 1
            assert result["workdirs"][0]["path"] == "/app"
        finally:
            os.unlink(path)

    def test_parse_dockerfile_extracts_user(self):
        path = _make_dockerfile("FROM alpine\nUSER appuser\n")
        try:
            result = parse_dockerfile(path)
            assert len(result["users"]) == 1
            assert result["users"][0]["user"] == "appuser"
        finally:
            os.unlink(path)

    def test_parse_dockerfile_extracts_cmd(self):
        path = _make_dockerfile('FROM alpine\nCMD ["python", "app.py"]\n')
        try:
            result = parse_dockerfile(path)
            assert result["cmd"] is not None
            assert "python" in result["cmd"]["args"]
        finally:
            os.unlink(path)

    def test_parse_dockerfile_skips_comments(self):
        path = _make_dockerfile("# This is a comment\nFROM alpine\n")
        try:
            result = parse_dockerfile(path)
            assert len(result["instructions"]) == 1
        finally:
            os.unlink(path)

    def test_parse_dockerfile_handles_line_continuation(self):
        content = "FROM alpine\nRUN apt-get update \\\n    && apt-get install -y curl\n"
        path = _make_dockerfile(content)
        try:
            result = parse_dockerfile(path)
            assert len(result["run_commands"]) == 1
            assert "curl" in result["run_commands"][0]["cmd"]
        finally:
            os.unlink(path)

    def test_parse_dockerfile_nonexistent_file_returns_error(self):
        result = parse_dockerfile("/nonexistent/Dockerfile")
        assert result["error"] is not None

    def test_parse_dockerfile_empty_file_returns_no_instructions(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            path = f.name
        try:
            result = parse_dockerfile(path)
            assert result["instructions"] == []
            assert result["error"] is None
        finally:
            os.unlink(path)

    def test_parse_dockerfile_counts_layers(self):
        content = "FROM alpine\nRUN echo 1\nCOPY . .\nRUN echo 2\n"
        path = _make_dockerfile(content)
        try:
            result = parse_dockerfile(path)
            # FROM + RUN + COPY + RUN = 4 layer
            assert result["num_layers"] == 4
        finally:
            os.unlink(path)


class TestParseFrom:
    def test_parse_from_simple_image(self):
        result = {"from_images": [], "stages": []}
        _parse_from("python:3.11", result)
        assert result["from_images"] == ["python:3.11"]
        assert result["stages"][0]["alias"] is None

    def test_parse_from_with_alias(self):
        result = {"from_images": [], "stages": []}
        _parse_from("node:18 AS builder", result)
        assert result["stages"][0]["alias"] == "builder"
        assert result["stages"][0]["image"] == "node:18"

    def test_parse_from_without_tag(self):
        result = {"from_images": [], "stages": []}
        _parse_from("ubuntu", result)
        assert result["from_images"] == ["ubuntu"]


class TestParseEnv:
    def test_parse_env_key_equals_value(self):
        result = {"env_vars": {}}
        _parse_env("PORT=8080", result)
        assert result["env_vars"]["PORT"] == "8080"

    def test_parse_env_key_space_value(self):
        result = {"env_vars": {}}
        _parse_env("PORT 8080", result)
        assert result["env_vars"]["PORT"] == "8080"

    def test_parse_env_quoted_value_strips_quotes(self):
        result = {"env_vars": {}}
        _parse_env('APP_NAME="myapp"', result)
        assert result["env_vars"]["APP_NAME"] == "myapp"

    def test_parse_env_multiple_pairs(self):
        result = {"env_vars": {}}
        _parse_env("KEY1=val1 KEY2=val2", result)
        assert "KEY1" in result["env_vars"]
        assert "KEY2" in result["env_vars"]


class TestParseArg:
    def test_parse_arg_with_default(self):
        result = {"args": {}}
        _parse_arg("VERSION=1.0", result)
        assert result["args"]["VERSION"] == "1.0"

    def test_parse_arg_without_default(self):
        result = {"args": {}}
        _parse_arg("BUILD_DATE", result)
        assert result["args"]["BUILD_DATE"] is None

    def test_parse_arg_strips_whitespace(self):
        result = {"args": {}}
        _parse_arg("  MY_ARG  ", result)
        assert "MY_ARG" in result["args"]


class TestParseLabel:
    def test_parse_label_key_value(self):
        result = {"labels": {}}
        _parse_label('maintainer="Alice"', result)
        assert result["labels"]["maintainer"] == "Alice"

    def test_parse_label_multiple(self):
        result = {"labels": {}}
        _parse_label('version="1.0" env="prod"', result)
        assert "version" in result["labels"]
        assert "env" in result["labels"]


class TestAnalyzeBestPractices:
    def _base_data(self, **overrides) -> dict:
        base = {
            "path": "/nonexistent/Dockerfile",
            "instructions": [],
            "run_commands": [],
            "from_images": ["python:3.11-slim"],
            "users": [{"line": 5, "user": "appuser"}],
            "copy_adds": [],
            "healthcheck": {"line": 10, "args": "CMD curl -f http://localhost/"},
            "env_vars": {},
            "workdirs": [{"line": 3, "path": "/app"}],
            "stages": [{"image": "python:3.11-slim", "alias": None, "index": 0}],
        }
        base.update(overrides)
        return base

    def test_no_user_generates_high_warning(self):
        data = self._base_data(users=[])
        warnings = _analyze_best_practices(data)
        levels = [w["level"] for w in warnings]
        assert "high" in levels

    def test_latest_tag_generates_high_warning(self):
        data = self._base_data(from_images=["ubuntu:latest"])
        warnings = _analyze_best_practices(data)
        high_titles = [w["title"] for w in warnings if w["level"] == "high"]
        assert any("latest" in t or "ubuntu" in t for t in high_titles)

    def test_untagged_image_generates_high_warning(self):
        data = self._base_data(from_images=["ubuntu"])
        warnings = _analyze_best_practices(data)
        assert any(w["level"] == "high" for w in warnings)

    def test_apt_without_no_install_recommends_generates_medium_warning(self):
        data = self._base_data(run_commands=[{"line": 3, "cmd": "apt-get install -y curl"}])
        warnings = _analyze_best_practices(data)
        assert any(w["level"] == "medium" for w in warnings)

    def test_apt_without_cache_cleanup_generates_medium_warning(self):
        data = self._base_data(
            run_commands=[{"line": 3, "cmd": "apt-get install -y --no-install-recommends curl"}]
        )
        warnings = _analyze_best_practices(data)
        medium_titles = [w["title"] for w in warnings if w["level"] == "medium"]
        assert any("cache" in t.lower() or "pulizia" in t.lower() for t in medium_titles)

    def test_pip_without_no_cache_dir_generates_medium_warning(self):
        data = self._base_data(run_commands=[{"line": 3, "cmd": "pip install requests"}])
        warnings = _analyze_best_practices(data)
        assert any(w["level"] == "medium" for w in warnings)

    def test_add_instead_of_copy_generates_low_warning(self):
        data = self._base_data(
            copy_adds=[{"line": 4, "instruction": "ADD", "args": "app.tar.bz2 /app"}]
        )
        warnings = _analyze_best_practices(data)
        assert any(w["level"] == "low" for w in warnings)

    def test_multistage_build_generates_ok_message(self):
        data = self._base_data(
            stages=[
                {"image": "node:18", "alias": "builder", "index": 0},
                {"image": "nginx:alpine", "alias": None, "index": 1},
            ]
        )
        warnings = _analyze_best_practices(data)
        assert any(w["level"] == "ok" for w in warnings)

    def test_secret_in_env_generates_high_warning(self):
        data = self._base_data(env_vars={"DB_PASSWORD": "secret123"})
        warnings = _analyze_best_practices(data)
        assert any(w["level"] == "high" for w in warnings)

    def test_many_run_commands_generates_medium_warning(self):
        runs = [{"line": i, "cmd": f"echo {i}"} for i in range(7)]
        data = self._base_data(run_commands=runs)
        warnings = _analyze_best_practices(data)
        assert any("RUN" in w["title"] for w in warnings if w["level"] == "medium")

    def test_warnings_sorted_high_before_low(self):
        data = self._base_data(users=[], from_images=["ubuntu"])
        warnings = _analyze_best_practices(data)
        levels = [w["level"] for w in warnings]
        order = {"high": 0, "medium": 1, "low": 2, "ok": 3}
        # Verifica che sia ordinato
        numeric = [order.get(lvl, 99) for lvl in levels]
        assert numeric == sorted(numeric)

    def test_pip_install_without_pinned_version_generates_medium(self):
        data = self._base_data(run_commands=[{"line": 3, "cmd": "pip install requests flask"}])
        warnings = _analyze_best_practices(data)
        medium = [w for w in warnings if w["level"] == "medium"]
        assert any(
            "versione" in w["title"].lower() or "dipendenz" in w["title"].lower() for w in medium
        )

    def test_pip_install_with_pinned_version_no_version_warning(self):
        data = self._base_data(
            run_commands=[
                {"line": 3, "cmd": "pip install --no-cache-dir requests==2.31.0 flask==3.0.0"}
            ]
        )
        warnings = _analyze_best_practices(data)
        assert not any(
            "versione" in w["title"].lower() or "dipendenz" in w["title"].lower() for w in warnings
        )

    def test_copy_dot_dot_generates_low_warning(self):
        data = self._base_data(copy_adds=[{"line": 5, "instruction": "COPY", "args": ". ."}])
        warnings = _analyze_best_practices(data)
        low = [w for w in warnings if w["level"] == "low"]
        assert any("COPY" in w["title"] and "contesto" in w["title"] for w in low)

    def test_copy_specific_path_no_context_warning(self):
        data = self._base_data(
            copy_adds=[{"line": 5, "instruction": "COPY", "args": "requirements.txt /app/"}]
        )
        warnings = _analyze_best_practices(data)
        assert not any("contesto" in w["title"] for w in warnings)
