# 🗂️ JSON Preview - Nautilus Extension

**Language:** [🇮🇹 Italiano](README_IT.md) | **🇬🇧 English**

---

Nautilus extension that adds advanced preview for JSON and JSONL files directly from the context menu.

## 🎯 Features

- **Navigable tree structure** to explore complex JSON
- **Automatically inferred schema** with data types
- **JSONL support** (JSON Lines) with statistics
- **Data preview** for arrays and JSONL files
- **Descriptive statistics** for numeric columns (with pandas)
- **Compressed file support** (.json.gz, .jsonl.gz)
- **Raw visualization** with formatting

## 🚀 Installation

```bash
sudo apt update
sudo apt install python3-nautilus
sudo apt install python3-pandas  # optional, for JSONL statistics
mkdir -p ~/.local/share/nautilus-python/extensions
cp json_preview.py ~/.local/share/nautilus-python/extensions/
nautilus -q
```

## 📖 How to use

1. Right-click on a JSON or JSONL file
2. Select **"JSON Preview"** or **"JSONL Preview"**
3. Explore the tabs: Structure, Schema, Data, Statistics, Raw

## 📋 Supported formats

- `.json`, `.jsonl`, `.ndjson`, `.json.gz`, `.jsonl.gz`

## 🗑️ Uninstallation

```bash
rm ~/.local/share/nautilus-python/extensions/json_preview.py
nautilus -q
```

---

**Back to [Main README](../README.md)**
