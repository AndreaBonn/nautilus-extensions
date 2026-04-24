<div align="center">

[![CI](https://github.com/AndreaBonn/nautilus-extensions/actions/workflows/ci.yml/badge.svg)](https://github.com/AndreaBonn/nautilus-extensions/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/AndreaBonn/nautilus-extensions/main/badges/test-badge.json)](https://github.com/AndreaBonn/nautilus-extensions/actions/workflows/ci.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Security Policy](https://img.shields.io/badge/security-policy-blueviolet.svg)](SECURITY.md)

</div>

# 🐚 Nautilus Extensions - Complete Guide

**Language:** [🇮🇹 Italiano](README_IT.md) | **🇬🇧 English**

---

Collection of extensions for Nautilus (Ubuntu/GNOME file manager) that add advanced preview and file management features directly from the context menu.

<!-- Screenshots — uncomment when images are available
<p align="center">
  <img src="assets/screenshots/csv-preview.png" width="280" alt="CSV Preview">
  <img src="assets/screenshots/git-graph.png" width="280" alt="Git Graph">
  <img src="assets/screenshots/pdf-splitter.png" width="280" alt="PDF Splitter">
</p>
-->

## 📋 Table of Contents

- [What are Nautilus extensions](#what-are-nautilus-extensions)
- [Available extensions](#available-extensions)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [Uninstallation](#uninstallation)

---

## 🎯 What are Nautilus extensions

Nautilus extensions are Python scripts that add new entries to the menu that appears when you right-click on a file or folder. These extensions allow you to:

- View advanced previews of data files (CSV, Excel, JSON, Parquet)
- Merge or split PDF files
- Analyze Dockerfiles
- Find duplicate files
- View README files directly from Nautilus
- Integrate Git directly into Nautilus (blame, diff, status, graph)

---

## 📦 Available extensions

### 1. 📊 **CSV Preview** (`csv-preview`)
View CSV files with:
- Formatted table of the first 100 rows
- Descriptive statistics (with pandas)
- Automatic delimiter detection
- Information on numeric columns and null values

**Supported formats:** `.csv`, `.tsv`

📖 **[Read the complete guide →](csv-preview/README.md)**

### 2. 📗 **Excel Preview** (`excel-preview`)
View Excel/LibreOffice files with:
- All document sheets
- Tabular data with column types
- Descriptive statistics for numeric columns
- Document metadata (author, creation date)

**Supported formats:** `.xlsx`, `.xlsm`, `.xltx`, `.xltm`, `.ods`

📖 **[Read the complete guide →](excel-preview/README.md)**

### 3. 🗂️ **JSON Preview** (`json-preview`)
View JSON and JSONL files with:
- Navigable tree structure
- Automatically inferred schema
- Data preview for arrays/JSONL
- Statistics for JSONL files
- Gzip compressed file support

**Supported formats:** `.json`, `.jsonl`, `.ndjson`, `.json.gz`, `.jsonl.gz`

📖 **[Read the complete guide →](json-preview/README.md)**

### 4. 📦 **Parquet Preview** (`parquet-preview`)
View Parquet files with:
- Complete schema with data types
- Metadata and row groups
- Data preview
- Descriptive statistics
- Compression information

**Supported formats:** `.parquet`

📖 **[Read the complete guide →](parquet-preview/README.md)**

### 5. 🔗 **Merge PDF** (`pdf-merger`)
Merge multiple PDF files into one:
- Multiple PDF selection
- Reorder via drag & drop
- Page count preview
- Choose output filename

**Usage:** Select 2 or more PDFs → right-click → "Merge PDF"

📖 **[Read the complete guide →](pdf-merger/README.md)**

### 6. ✂️ **Split PDF** (`pdf-splitter`)
Split a PDF into multiple files with 4 modes:
- **Custom ranges** (e.g., 1-3, 5-7, 9)
- **Every N pages** (e.g., every 5 pages)
- **One page per file**
- **By bookmarks/chapters**

**Usage:** Right-click on PDF → "Split PDF"

📖 **[Read the complete guide →](pdf-splitter/README.md)**

### 7. 🐳 **Analyze Dockerfile** (`dockerfile-analyzer`)
Analyze Dockerfiles with:
- Structure and instructions
- Multi-stage builds
- Environment variables and arguments
- **Best practices and security suggestions**
- Common issue detection

**Usage:** Right-click on Dockerfile → "Analyze Dockerfile"

📖 **[Read the complete guide →](dockerfile-analyzer/README.md)**

### 8. 🔍 **Find Duplicates** (`duplicate-finder`)
Find duplicate files in a folder:
- Recursive scan with SHA-256 hash
- Grouping by identical content
- Smart selection (keeps the first)
- Move to trash with one click

**Usage:** Right-click on folder → "🔍 Find duplicates"

📖 **[Read the complete guide →](duplicate-finder/README.md)**

### 9. 📖 **View README** (`readme-viewer`)
Show the current folder's README:
- Markdown rendering (if available)
- Support for README.md, README.txt, README.rst
- Quick open in editor

**Usage:** Right-click on folder background → "Show README.md"

📖 **[Read the complete guide →](readme-viewer/README.md)**

### 10. ⎇ **Git Blame** (`git-blame`)
Adds Git columns to Nautilus list view:
- Last commit author for each file
- Relative commit date (e.g., "3 hours ago")
- Commit message (truncated to 55 characters)
- Result caching and async loading

**Usage:** List View (`Ctrl+2`) → right-click column headers → enable Git columns

📖 **[Read the complete guide →](git-blame/README.md)**

### 11. ⎇ **Git Diff** (`git-diff`)
Visual diff viewer for modified files:
- Side-by-side view with aligned lines
- Unified view with toggle
- Green/red coloring for additions/removals
- Support for staged and working tree diffs

**Usage:** Right-click on modified file → "⎇ Mostra Diff Git"

📖 **[Read the complete guide →](git-diff/README.md)**

### 12. ⎇ **Git Graph** (`git-graph`)
Visualize the Git commit graph:
- Visual graph with nodes and Bézier curves
- Color palette for distinct branches
- Branch badges and golden HEAD marker
- Interactive legend and status bar

**Usage:** Right-click on background → "⎇ Mostra Git Graph…"

📖 **[Read the complete guide →](git-graph/README.md)**

### 13. ⎇ **Git Status** (`git-status`)
Git status panel with automatic refresh:
- Current branch with ahead/behind indicator
- Staged, modified and untracked files with colored icons
- Last 10 commits with hash, author and date
- Stash count and 3-second auto-refresh

**Usage:** Right-click on background → "⎇ Stato Git…"

📖 **[Read the complete guide →](git-status/README.md)**

---

## 🚀 Installation

### Prerequisites

Before installing the extensions, make sure you have:

1. **Ubuntu/GNOME** (or another distribution with Nautilus)
2. **Python 3** (already installed on Ubuntu)
3. **nautilus-python** (the bridge between Nautilus and Python)

### Step 1: Install nautilus-python

Open the terminal (press `Ctrl+Alt+T`) and type:

```bash
sudo apt update
sudo apt install python3-nautilus
```

### Step 2: Create the extensions folder

If it doesn't already exist, create the folder where Nautilus looks for extensions:

```bash
mkdir -p ~/.local/share/nautilus-python/extensions
```

### Step 3: Install Python dependencies

Some extensions require additional Python libraries. Install the ones you need:

#### For ALL extensions (recommended):
```bash
sudo apt install python3-pandas python3-openpyxl python3-pypdf python3-markdown
pip install pyarrow --break-system-packages
```

#### Or only for specific extensions:

**CSV Preview:**
```bash
sudo apt install python3-pandas
```

**Excel Preview:**
```bash
sudo apt install python3-pandas python3-openpyxl
```

**JSON Preview:**
```bash
sudo apt install python3-pandas  # optional, for JSONL statistics
```

**Parquet Preview:**
```bash
sudo apt install python3-pandas
pip install pyarrow --break-system-packages
```

**PDF Merger/Splitter:**
```bash
sudo apt install python3-pypdf
```

**README Viewer:**
```bash
sudo apt install python3-markdown gir1.2-webkit2-4.1  # optional, for Markdown rendering
```

**Dockerfile Analyzer and Duplicate Finder:**
No additional dependencies (use only standard libraries)

**Git Blame, Git Diff, Git Graph and Git Status:**
No additional dependencies (only require `git` installed on the system)

### Step 4: Copy the extensions

Copy the `.py` files of the extensions you want to use to the created folder:

```bash
# Example: install all extensions
cp csv-preview/csv_preview.py ~/.local/share/nautilus-python/extensions/
cp excel-preview/excel_preview.py ~/.local/share/nautilus-python/extensions/
cp json-preview/json_preview.py ~/.local/share/nautilus-python/extensions/
cp parquet-preview/parquet_preview.py ~/.local/share/nautilus-python/extensions/
cp pdf-merger/pdf_merger.py ~/.local/share/nautilus-python/extensions/
cp pdf-splitter/pdf_splitter.py ~/.local/share/nautilus-python/extensions/
cp dockerfile-analyzer/dockerfile_analyzer.py ~/.local/share/nautilus-python/extensions/
cp duplicate-finder/duplicate-finder.py ~/.local/share/nautilus-python/extensions/
cp readme-viewer/readme_preview.py ~/.local/share/nautilus-python/extensions/
cp git-blame/git_blame.py ~/.local/share/nautilus-python/extensions/
cp git-diff/git_diff.py ~/.local/share/nautilus-python/extensions/
cp git-graph/git_graph.py ~/.local/share/nautilus-python/extensions/
cp git-status/git_status.py ~/.local/share/nautilus-python/extensions/
```

**Or install only the ones you need**, for example only CSV and PDF:
```bash
cp csv-preview/csv_preview.py ~/.local/share/nautilus-python/extensions/
cp pdf-merger/pdf_merger.py ~/.local/share/nautilus-python/extensions/
```

### Step 5: Restart Nautilus

To activate the extensions, restart Nautilus:

```bash
nautilus -q
```

Then reopen Nautilus normally (click the "Files" icon in the dock or press `Super+E`).

---

## ⚙️ Configuration

### Verify installation

To verify that the extensions have been loaded correctly:

1. Open Nautilus
2. Go to a folder with CSV, PDF, JSON files, etc.
3. Right-click on a supported file
4. You should see the new entries in the menu (e.g., "CSV Preview", "Split PDF")

### Troubleshoot loading issues

If the extensions don't appear:

1. **Check Nautilus logs:**
   ```bash
   nautilus -q
   nautilus 2>&1 | grep -i python
   ```

2. **Verify that nautilus-python is installed:**
   ```bash
   dpkg -l | grep nautilus-python
   ```

3. **Check file permissions:**
   ```bash
   ls -la ~/.local/share/nautilus-python/extensions/
   ```
   Files must be readable (permissions `644` or `755`)

4. **Make files executable (if necessary):**
   ```bash
   chmod +x ~/.local/share/nautilus-python/extensions/*.py
   ```

---

## 📖 Usage

### Preview data files (CSV, Excel, JSON, Parquet)

1. Navigate to the file you want to view
2. **Right-click** on the file
3. Select **"Preview [file type]"** (e.g., "CSV Preview")
4. A window will open with:
   - "Data" tab: table with data
   - "Schema/Columns" tab: column information
   - "Statistics" tab: descriptive statistics (if available)
   - "Metadata" tab: file information

### Merge PDFs

1. **Select 2 or more PDF files** (hold `Ctrl` while clicking)
2. **Right-click** on the selection
3. Select **"Merge [N] PDFs"**
4. In the window that opens:
   - Reorder files by dragging or using ⬆⬇ buttons
   - Remove unwanted files with ✕ button
   - Edit the output filename
   - Click **"🔗 Merge PDF"**
5. The merged file will be saved in the same folder as the first PDF

### Split PDF

1. **Right-click** on a PDF file
2. Select **"Split PDF"**
3. Choose one of 4 modes:
   - **Ranges**: enter "1-3, 5, 7-9" to create 3 files
   - **Every N pages**: split every 5 pages
   - **One per file**: each page becomes a PDF
   - **Bookmarks**: one file per chapter
4. Choose the output folder
5. Click **"✂ Split PDF"**

### Analyze Dockerfile

1. **Right-click** on a Dockerfile
2. Select **"Analyze Dockerfile"**
3. Explore the tabs:
   - **Overview**: base images, ports, variables
   - **Best Practices**: security and optimization suggestions
   - **Instructions**: complete instruction list
   - **Source**: code with syntax highlighting

### Find duplicates

1. **Right-click** on a folder
2. Select **"🔍 Find duplicates"**
3. Wait for the scan (may take time for large folders)
4. In the results window:
   - Files are grouped by identical content
   - The first file in each group is NOT selected (will be kept)
   - You can modify the selection manually
   - Click **"Select duplicates automatically"** to select all except the first
   - Click **"🗑 Move to Trash"** to delete selected duplicates

### View README

1. Open a folder containing a README file
2. **Right-click on the background** (not on a file)
3. Select **"Show README.md"** (or README.txt, etc.)
4. The README will be displayed with Markdown rendering (if available)

---

## 🔧 Troubleshooting

### Extensions don't appear in the menu

**Cause:** nautilus-python is not installed or Nautilus hasn't been restarted

**Solution:**
```bash
sudo apt install python3-nautilus
nautilus -q
```

### Error "ModuleNotFoundError: No module named 'pandas'"

**Cause:** Missing pandas library

**Solution:**
```bash
sudo apt install python3-pandas
```

### Error "ModuleNotFoundError: No module named 'pypdf'"

**Cause:** Missing pypdf library for PDF handling

**Solution:**
```bash
sudo apt install python3-pypdf
```

### Error "ModuleNotFoundError: No module named 'pyarrow'"

**Cause:** Missing pyarrow for Parquet files

**Solution:**
```bash
pip install pyarrow --break-system-packages
```

### CSV/Excel preview is slow

**Cause:** Very large file

**Solution:** Extensions load only the first 100 rows for speed. For huge files, consider using dedicated tools like LibreOffice Calc or DBeaver.

### Markdown rendering doesn't work

**Cause:** Missing WebKit or python3-markdown

**Solution:**
```bash
sudo apt install python3-markdown gir1.2-webkit2-4.1
```

### Nautilus freezes or crashes

**Cause:** Buggy extension or corrupted file

**Solution:**
1. Temporarily remove all extensions:
   ```bash
   mv ~/.local/share/nautilus-python/extensions ~/.local/share/nautilus-python/extensions.backup
   nautilus -q
   ```
2. Reinstall extensions one at a time to identify the problematic one

---

## 🗑️ Uninstallation

### Remove a single extension

```bash
rm ~/.local/share/nautilus-python/extensions/[extension_name].py
nautilus -q
```

Example to remove CSV preview:
```bash
rm ~/.local/share/nautilus-python/extensions/csv_preview.py
nautilus -q
```

### Remove all extensions

```bash
rm ~/.local/share/nautilus-python/extensions/*.py
nautilus -q
```

### Uninstall nautilus-python (removes ALL Python extensions)

```bash
sudo apt remove python3-nautilus
nautilus -q
```

---

## 💡 Tips

### Performance

- Preview extensions load only part of files (first 100 rows) for speed
- For very large files (>100MB), opening may take a few seconds
- Duplicate search can be slow on folders with thousands of files

### Security

- The Dockerfile analyzer highlights common security issues
- Never put passwords or secrets in ENV variables in Dockerfiles
- Always use specific tags for Docker images (not `:latest`)

### Customization

You can modify the `.py` files to customize:
- Number of rows displayed (change `PREVIEW_ROWS`)
- Window sizes (change `WINDOW_W` and `WINDOW_H`)
- Colors and CSS styles (modify the `CSS` variable)

---

## 📝 Technical notes

- **Nautilus version:** These extensions are designed for Nautilus 43+ (GNOME 43+) with GTK 4
- **Python:** Requires Python 3.9 or higher
- **Threads:** Heavy operations (file reading, hash calculation) are executed in separate threads to avoid blocking the interface
- **Single-file architecture:** Each extension is a self-contained `.py` file — this is a [Nautilus constraint](https://wiki.gnome.org/Projects/NautilusPython), not a design choice. Nautilus loads extensions by scanning a single directory for `.py` files, so each extension must bundle its UI, parsing logic, and entry point in one module. Some utility functions (e.g. `fmt_size`) are intentionally duplicated across extensions for this reason.

---

## 🤝 Contributions

Found a bug or want to add a feature? Feel free to:
- Open an issue
- Submit a pull request
- Suggest improvements

---

## 📄 License

These extensions are provided "as is" without warranties. Use at your own risk.

---

## ❓ Frequently Asked Questions (FAQ)

**Q: Can I use these extensions on other Linux distributions?**  
A: Yes, they work on any distribution with Nautilus and nautilus-python (Fedora, Debian, Arch, etc.)

**Q: Do they work with other file managers?**  
A: No, they are specific to Nautilus. For other file managers (Dolphin, Thunar, etc.) you need different extensions.

**Q: Can I modify the code?**  
A: Absolutely yes! The files are readable and modifiable Python scripts.

**Q: Do extensions slow down Nautilus?**  
A: No, they are loaded only when needed and heavy operations are in separate threads.

**Q: Where are merged/split files saved?**  
A: In the same folder as the original file, or in the folder you choose in the dialog window.

---

**Happy working with Nautilus! 🚀**
