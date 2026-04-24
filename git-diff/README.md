# Git Diff - Nautilus Extension

**Language:** [Italiano](README_IT.md) | **English**

---

Nautilus extension that adds a visual side-by-side diff view from the context menu for files in Git repositories.

## Features

- **Side-by-side diff** with aligned old/new lines
- **Unified diff** with a toggle to switch between the two views
- **Syntax coloring** — green for additions, red for removals
- **Line numbers** for both sides
- **Staged and working tree diff support** — shows unstaged changes first, then staged changes
- **Async loading** with a spinner during loading
- **Available on files and folders** from the context menu and from the background

## Installation

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
cp git_diff.py ~/.local/share/nautilus-python/extensions/
```

### Step 4: Restart Nautilus

```bash
nautilus -q
```

**Note:** This extension requires no additional dependencies (only `git` installed on the system).

## How to use

1. Open Nautilus and navigate to a Git repository
2. **Right-click** on a modified file
3. Select **"⎇ Mostra Diff Git"**
4. In the window:
   - Use the **"Side-by-side"** / **"Unified"** toggle to switch views
   - Scroll to navigate through the change hunks

You can also right-click on the **background** of a folder to view the diff for the folder itself.

## Technical details

- **Nautilus version:** 43+ (GNOME 43+) with GTK 4
- **API:** `MenuProvider`
- **Threads:** Diff loading happens in a separate thread to avoid blocking the interface
- **Diff parser:** Custom parsing of `git diff` output into hunks with support for added, removed, and context lines

## Uninstallation

```bash
rm ~/.local/share/nautilus-python/extensions/git_diff.py
nautilus -q
```

---

**Back to [Main README](../README.md)**
