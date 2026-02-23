# 🐳 Analyze Dockerfile - Nautilus Extension

**Language:** [🇮🇹 Italiano](README.md) | **🇬🇧 English**

---

Nautilus extension that analyzes Dockerfiles and provides best practice and security suggestions.

## 🎯 Features

- **Dockerfile structure analysis**
- **Multi-stage build detection**
- **Best practices and security** with 14+ checks
- **Issue highlighting** by severity (critical, medium, info)
- **Instruction visualization** with syntax highlighting
- **Metadata** (ENV, ARG, EXPOSE, VOLUME, etc.)

## 🚀 Installation

```bash
sudo apt update
sudo apt install python3-nautilus
mkdir -p ~/.local/share/nautilus-python/extensions
cp dockerfile_analyzer.py ~/.local/share/nautilus-python/extensions/
nautilus -q
```

**Note:** This extension requires no additional dependencies.

## 📖 How to use

1. **Right-click** on a Dockerfile
2. Select **"Analyze Dockerfile"**
3. Explore the 4 tabs:
   - **🐳 Overview**: images, ports, variables
   - **⚠ Best Practices**: security suggestions
   - **📋 Instructions**: complete list
   - **📄 Source**: code with colors

## 🗑️ Uninstallation

```bash
rm ~/.local/share/nautilus-python/extensions/dockerfile_analyzer.py
nautilus -q
```

---

**Back to [Main README](../README_EN.md)**
