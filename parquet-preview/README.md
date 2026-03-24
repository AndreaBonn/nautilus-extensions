# 📦 Parquet Preview - Nautilus Extension

**Language:** [🇮🇹 Italiano](README_IT.md) | **🇬🇧 English**

---

Nautilus extension that adds advanced preview for Apache Parquet files directly from the context menu.

## 🎯 Features

- **Complete schema** with PyArrow data types
- **Detailed metadata** (row groups, compression, codec)
- **Data preview** with first 100 rows
- **Descriptive statistics** for numeric columns
- **Null value information**
- **Type-based column highlighting** with different colors
- **Row group details** with compressed/uncompressed sizes

## 🚀 Installation

```bash
sudo apt update
sudo apt install python3-nautilus python3-pandas
pip install pyarrow --break-system-packages
mkdir -p ~/.local/share/nautilus-python/extensions
cp parquet_preview.py ~/.local/share/nautilus-python/extensions/
nautilus -q
```

## 📖 How to use

1. Right-click on a `.parquet` file
2. Select **"Parquet Preview"**
3. Explore the tabs: Data, Schema, Statistics, Metadata

## 🗑️ Uninstallation

```bash
rm ~/.local/share/nautilus-python/extensions/parquet_preview.py
nautilus -q
```

---

**Back to [Main README](../README.md)**
