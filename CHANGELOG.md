# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
