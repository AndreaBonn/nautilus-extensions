# 📖 View README - Nautilus Extension

**Language:** [🇮🇹 Italiano](README.md) | **🇬🇧 English**

---

Nautilus extension that shows the current folder's README file with Markdown rendering.

## 🎯 Features

- **Automatic detection** of README.md, README.txt, README.rst
- **Markdown rendering** (if WebKit is available)
- **Quick open** in editor
- **Multiple format support**

## 🚀 Installation

```bash
sudo apt update
sudo apt install python3-nautilus
sudo apt install python3-markdown gir1.2-webkit2-4.1  # optional, for Markdown rendering
mkdir -p ~/.local/share/nautilus-python/extensions
cp readme_preview.py ~/.local/share/nautilus-python/extensions/
nautilus -q
```

## 📖 How to use

1. Open a folder with a README
2. **Right-click on the background** (not on a file)
3. Select **"Show README.md"**
4. The README will be displayed

## 🗑️ Uninstallation

```bash
rm ~/.local/share/nautilus-python/extensions/readme_preview.py
nautilus -q
```

---

**Back to [Main README](../README_EN.md)**
