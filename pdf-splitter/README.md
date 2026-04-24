# Split PDF - Nautilus Extension

**Language:** [Italiano](README_IT.md) | **English**

---

Nautilus extension that allows splitting a PDF file into multiple files with 4 different modes.

## Features

- **4 split modes:**
  1. Custom ranges (e.g., 1-3, 5-7, 9)
  2. Every N pages
  3. One page per file
  4. By bookmarks/chapters
- **Preview of files** to be created
- **Choose output folder**
- **Progress bar** during splitting

## Installation

```bash
sudo apt update
sudo apt install python3-nautilus python3-pypdf
mkdir -p ~/.local/share/nautilus-python/extensions
cp pdf_splitter.py ~/.local/share/nautilus-python/extensions/
nautilus -q
```

## How to use

1. **Right-click** on a PDF file
2. Select **"Split PDF"**
3. Choose a mode and configure
4. Choose output folder
5. Click **"Split PDF"**

## Uninstallation

```bash
rm ~/.local/share/nautilus-python/extensions/pdf_splitter.py
nautilus -q
```

---

**Back to [Main README](../README.md)**
