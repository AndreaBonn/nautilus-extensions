# 🔍 Find Duplicates - Nautilus Extension

**Language:** [🇮🇹 Italiano](README_IT.md) | **🇬🇧 English**

---

Nautilus extension that finds duplicate files in a folder using SHA-256 hash.

## 🎯 Features

- **Recursive scan** of all subfolders
- **SHA-256 hash** to identify identical files
- **Grouping** by content
- **Smart selection** (keeps the first file)
- **Move to trash** with one click
- **Progress bar** during scan

## 🚀 Installation

```bash
sudo apt update
sudo apt install python3-nautilus
mkdir -p ~/.local/share/nautilus-python/extensions
cp duplicate-finder.py ~/.local/share/nautilus-python/extensions/
nautilus -q
```

**Note:** This extension requires no additional dependencies.

## 📖 How to use

1. **Right-click** on a folder
2. Select **"🔍 Find duplicates"**
3. Wait for the scan
4. Select files to delete
5. Click **"🗑 Move to Trash"**

## 🗑️ Uninstallation

```bash
rm ~/.local/share/nautilus-python/extensions/duplicate-finder.py
nautilus -q
```

---

**Back to [Main README](../README.md)**
