# Screenshot Guide

Capture screenshots for each extension to include in the README.
Use `gnome-screenshot` or `Shift+PrintScreen` to grab windows.

## Naming Convention

```
screenshots/csv-preview.png
screenshots/excel-preview.png
screenshots/json-preview.png
screenshots/parquet-preview.png
screenshots/pdf-merger.png
screenshots/pdf-splitter.png
screenshots/dockerfile-analyzer.png
screenshots/duplicate-finder.png
screenshots/readme-viewer.png
screenshots/git-blame.png
screenshots/git-diff.png
screenshots/git-graph.png
screenshots/git-status.png
```

## What to Capture

| Extension | Content to show |
|-----------|----------------|
| csv-preview | Data tab with a real CSV loaded (100 rows visible) |
| excel-preview | Multi-sheet file with sheet tabs visible |
| json-preview | Tree view expanded + schema tab |
| parquet-preview | Schema with colored types + metadata tab |
| pdf-merger | 3+ PDFs in the merge list with drag handles |
| pdf-splitter | Range mode with preview of output files |
| dockerfile-analyzer | Best practices tab with warnings |
| duplicate-finder | Results with grouped duplicates |
| readme-viewer | Rendered Markdown with code blocks |
| git-blame | Nautilus list view with Git columns visible |
| git-diff | Side-by-side diff with colored additions/deletions |
| git-graph | Commit graph with branch topology |
| git-status | Status panel with staged/modified/untracked files |

## Image Specs

- Format: PNG
- Max width: 900px (resize if larger)
- Crop to window only (no desktop background)
- Use a realistic file/repo, not empty or toy data

## Optional: Animated Demo

A single GIF showing the right-click → extension workflow:
```
screenshots/demo.gif
```

Use `peek` or `byzanz-record` to capture.
