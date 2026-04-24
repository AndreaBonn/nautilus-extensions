# Git Graph - Nautilus Extension

**Language:** [Italiano](README_IT.md) | **English**

---

Nautilus extension that displays the Git commit graph with branches, merges, and a colored legend in an interactive graphical window.

## Features

- **Visual commit graph** drawn with Cairo on GTK 4 DrawingArea
- **Branch color palette** — each branch has a distinct color from the palette
- **HEAD marker** with a golden ring on the current commit
- **Branch badges** with colored background next to commits with refs
- **Interactive legend** at the top with all branches
- **Bezier curves** for connections between commits on different branches
- **Up to 60 commits** displayed with hash, author, date, and message
- **Status bar** with commit and branch count
- **Async loading** with a spinner during loading

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
cp git_graph.py ~/.local/share/nautilus-python/extensions/
```

### Step 4: Restart Nautilus

```bash
nautilus -q
```

**Note:** This extension requires no additional dependencies (only `git` installed on the system).

## How to use

1. Open Nautilus and navigate to a folder inside a Git repository
2. **Right-click** on the folder background
3. Select **"⎇ Mostra Git Graph…"**
4. In the window you will see:
   - **Legend** at the top with branches and their respective colors
   - **Graph** with commit nodes connected by lines/curves
   - **Colored badges** for branches associated with commits
   - **Hash + message** for each commit
   - **Author and date** aligned to the right
   - **Status bar** with the total count of commits and branches

You can also right-click on a **folder** to open the graph for the contained repository.

## Configuration

You can customize the extension by editing the constants in the `git_graph.py` file:

```python
BRANCH_COLORS = [...]    # Branch color palette
HEAD_COLOR = "#FFD700"    # HEAD marker color
MERGE_COLOR = "#FF6B9D"   # Color for merge commits
max_commits = 60           # Maximum number of commits displayed
```

In the `GitGraphWidget` class:
```python
ROW_H = 52     # Height of each commit row
COL_W = 22     # Column width for parallel branches
NODE_R = 7     # Commit node radius
LEFT_PAD = 16  # Left padding
```

## Technical details

- **Nautilus version:** 43+ (GNOME 43+) with GTK 4
- **API:** `MenuProvider`
- **Rendering:** Cairo drawing on `Gtk.DrawingArea` with `set_draw_func`
- **Threads:** Git data loading happens in a separate thread to avoid blocking the interface
- **Layout:** Column assignment heuristic based on active branches to avoid overlaps

## Uninstallation

```bash
rm ~/.local/share/nautilus-python/extensions/git_graph.py
nautilus -q
```

---

**Back to [Main README](../README.md)**
