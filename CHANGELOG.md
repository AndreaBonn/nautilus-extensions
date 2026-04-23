# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.1.0] - 2026-04-23

### Security
- README Viewer: fail-safe navigation blocking — block on error instead of allow
- README Viewer: disable JavaScript in WebView to prevent inline script execution
- Git Status: escape sync counter in GTK markup to prevent injection
- Dockerfile Analyzer: escape title/text in `_section()` and `_tag_label()`
- CI: pin GitHub Actions to commit SHAs (supply chain protection)
- CI: add bandit and pip-audit to security job

### Fixed
- Parquet Preview: handle empty tables in `read_parquet()` (StopIteration)
- Excel Preview: protect `os.path.getsize` from OSError on missing files
- Replace silent `except Exception: pass` with diagnostic logging (7 files)
- Fix README documentation: MD5 → SHA-256 (matches actual code)

### Changed
- Rename `TrovaDuplicatiExtension` → `DuplicateFinderExtension` for naming consistency
- Add type hints to all git extension modules
- Translate all docstrings and comments to English
- Rewrite CONTRIBUTING.md with real development workflow (uv, make check)
- Add single-file architecture note to README (explains Nautilus constraint)

### Added
- 116 new tests (241 → 357): pdf_merger, excel read_excel, parquet read_parquet, git_graph get_git_log
- `[build-system]` in pyproject.toml (enables `pip install` from GitHub)
- CI: reproducible builds with `uv.lock` + `--frozen`
- CI: concurrency groups and timeout limits
- Screenshot directory structure with capture guide

## [1.0.0] - 2026-04-23

### Added
- CSV Preview — tabular preview with delimiter auto-detection and optional pandas statistics
- Excel Preview — .xlsx/.xls preview with sheet navigation and column statistics
- JSON Preview — structured tree view with syntax highlighting and search
- Parquet Preview — schema, metadata, row groups and data preview for Apache Parquet files
- PDF Merger — combine multiple PDF files with drag-and-drop reordering
- PDF Splitter — split PDFs by page ranges, bookmarks or fixed intervals
- Dockerfile Analyzer — Dockerfile linting with best-practice suggestions
- Duplicate Finder — find duplicate files by content hash (SHA-256)
- README Viewer — render Markdown README files with WebKit
- Git Blame columns — author, date and commit message in Nautilus list view
- Git Diff — visual side-by-side diff viewer for tracked files
- Git Graph — commit history visualization with branch topology
- Git Status — repository status overview with staging and file navigation

### Security
- All subprocess calls use list-form arguments (no `shell=True`)
- Optional dependencies handled gracefully with `try/except ImportError`
- Path traversal protection on PDF output filenames
- GTK markup strings escaped with `GLib.markup_escape_text()`
