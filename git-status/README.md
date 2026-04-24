# Git Status - Nautilus Extension

**Language:** [Italiano](README_IT.md) | **English**

---

Nautilus extension that adds a Git status panel with automatic refresh from the context menu.

## Features

- **Current branch** with ahead/behind indicator relative to the remote
- **Staged files** ready for commit
- **Modified files** in the working tree
- **Untracked files** new and not tracked
- **Last 10 commits** with hash, author, date, and message
- **Stash count** saved stashes
- **Automatic refresh** every 3 seconds
- **Refresh button** manual refresh in the title bar
- **Colored icons** by change type (added, modified, deleted)

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
cp git_status.py ~/.local/share/nautilus-python/extensions/
```

### Step 4: Restart Nautilus

```bash
nautilus -q
```

**Note:** This extension requires no additional dependencies (only `git` installed on the system).

## How to use

1. Open Nautilus and navigate to a folder inside a Git repository
2. **Right-click** on the folder background
3. Select **"⎇ Stato Git…"**
4. In the window you will see:
   - **Header:** branch name with ↑↓ indicators for commits ahead/behind
   - **Staged:** files ready for commit (green)
   - **Modified:** files with unstaged changes (yellow)
   - **New/Untracked:** untracked files (blue)
   - **Last commits:** history of the last 10 commits
   - **Stash:** number of saved stashes

The window refreshes automatically every 3 seconds. You can also click **↻** for an immediate refresh.

## Technical details

- **Nautilus version:** 43+ (GNOME 43+) with GTK 4
- **API:** `MenuProvider`
- **Threads:** Git data updates happen in separate threads to avoid blocking the interface
- **Auto-refresh:** Timer using `GLib.timeout_add()` every 3000ms
- **Window reuse:** If the window is already open, it is reused by updating the path

## Uninstallation

```bash
rm ~/.local/share/nautilus-python/extensions/git_status.py
nautilus -q
```

---

**Back to [Main README](../README.md)**
