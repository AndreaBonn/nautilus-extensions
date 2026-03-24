# ⎇ Git Blame - Nautilus Extension

**Language:** [🇮🇹 Italiano](README_IT.md) | **🇬🇧 English**

---

Nautilus extension that adds Git blame columns in the list view, showing the author, date, and message of the last commit for each file.

## 🎯 Features

- **"Git: Author" column** — who made the last commit on the file
- **"Git: Date" column** — when (e.g. "3 hours ago")
- **"Git: Message" column** — commit message (truncated to 55 characters)
- **Async loading** with background threads to avoid blocking Nautilus
- **Result caching** to avoid repeated git calls
- **Automatic detection** of whether the file is inside a git repository

## 🚀 Installation

### Step 1: Install nautilus-python

```bash
sudo apt update
sudo apt install python3-nautilus
```

### Step 2: Create the extensions folder

```bash
mkdir -p ~/.local/share/nautilus-python/extensions
```

### Step 3: Copy the extension file

```bash
cp git_blame.py ~/.local/share/nautilus-python/extensions/
```

### Step 4: Restart Nautilus

```bash
nautilus -q
```

**Note:** This extension requires no additional dependencies (only `git` installed on the system).

## 📖 How to use

1. Open Nautilus and navigate to a folder inside a Git repository
2. Switch to **List View** with `Ctrl+2`
3. **Right-click** on the column header
4. Check **"Git: Author"**, **"Git: Date"**, **"Git: Message"**

The columns will show the last commit information for each file.

## 🔍 Technical details

- **Nautilus version:** 43+ (GNOME 43+) with GTK 4
- **API:** `ColumnProvider` + `InfoProvider`
- **Threads:** Git information loading happens in separate threads to avoid blocking the interface
- **Cache:** Results are cached to avoid repeated calls to `git log`

## 🗑️ Uninstallation

```bash
rm ~/.local/share/nautilus-python/extensions/git_blame.py
nautilus -q
```

---

**Back to [Main README](../README.md)**
