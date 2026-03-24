# 🔗 Merge PDF - Nautilus Extension

**Language:** [🇮🇹 Italiano](README_IT.md) | **🇬🇧 English**

---

Nautilus extension that allows merging multiple PDF files into one with a graphical interface.

## 🎯 Features

- **Multiple PDF selection**
- **Reorder via drag & drop** or ⬆⬇ buttons
- **Remove files** from the list
- **Page count preview** for each PDF
- **Total page count** of the resulting file
- **Choose output filename**
- **Automatic opening** of destination folder

## 🚀 Installation

```bash
sudo apt update
sudo apt install python3-nautilus python3-pypdf
mkdir -p ~/.local/share/nautilus-python/extensions
cp pdf_merger.py ~/.local/share/nautilus-python/extensions/
nautilus -q
```

## 📖 How to use

1. **Select 2 or more PDF files** (hold `Ctrl` while clicking)
2. **Right-click** on the selection
3. Select **"Merge [N] PDFs"**
4. Reorder, remove files, edit output name
5. Click **"🔗 Merge PDF"**

## 🗑️ Uninstallation

```bash
rm ~/.local/share/nautilus-python/extensions/pdf_merger.py
nautilus -q
```

---

**Back to [Main README](../README.md)**
