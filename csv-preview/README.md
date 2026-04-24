# CSV Preview - Nautilus Extension

**Language:** [Italiano](README_IT.md) | **English**

---

Nautilus extension that adds advanced preview for CSV and TSV files directly from the context menu.

## Features

- **Formatted table** with the first 100 rows of the file
- **Automatic delimiter detection** (comma, semicolon, tab)
- **Descriptive statistics** for numeric columns (mean, median, min, max, etc.)
- **Numeric column highlighting** with blue color
- **Null value information** for each column
- **Column sorting** by clicking on the header
- **Large file support** with optimized loading

## What you'll see

When you open a CSV file preview, you'll see a window with 3 tabs:

1. **Data**: Table with data, resizable and sortable columns
2. **Statistics**: Descriptive statistics for numeric columns (only with pandas)
3. **Columns**: Information about each column (name, type, null values)

In the top bar you'll find:
- Total number of rows and columns
- Detected delimiter
- File size
- Warning if file was truncated (shows only first 100 rows)

## Installation

### Step 1: Install nautilus-python

```bash
sudo apt update
sudo apt install python3-nautilus
```

### Step 2: Install dependencies (optional but recommended)

To get descriptive statistics:
```bash
sudo apt install python3-pandas
```

**Note:** The extension works without pandas, but won't show statistics.

### Step 3: Create the extensions folder

```bash
mkdir -p ~/.local/share/nautilus-python/extensions
```

### Step 4: Copy the extension file

```bash
cp csv_preview.py ~/.local/share/nautilus-python/extensions/
```

### Step 5: Restart Nautilus

```bash
nautilus -q
```

Reopen Nautilus normally.

## How to use

1. Open Nautilus and navigate to a CSV or TSV file
2. **Right-click** on the file
3. Select **"CSV Preview"**
4. A window will open with the file preview

### Window features

- **Resize columns**: Drag the header border
- **Sort data**: Click on a column header
- **Navigate tabs**: Click on "Data", "Statistics" or "Columns"
- **Open in editor**: Click the "Open with editor" button at the bottom

## Configuration

You can customize the extension by modifying constants in `csv_preview.py`:

```python
PREVIEW_ROWS = 100        # Number of rows to show
MAX_COL_WIDTH = 300       # Maximum column width in pixels
MIN_COL_WIDTH = 60        # Minimum column width in pixels
WINDOW_W = 1100           # Window width
WINDOW_H = 650            # Window height
```

## Supported formats

- `.csv` - Comma Separated Values
- `.tsv` - Tab Separated Values

The extension automatically detects the delimiter by analyzing the file content.

## Troubleshooting

### Extension doesn't appear in the menu

**Solution:**
```bash
# Verify that nautilus-python is installed
dpkg -l | grep nautilus-python

# Restart Nautilus
nautilus -q
```

### Error "ModuleNotFoundError: No module named 'pandas'"

**Solution:**
```bash
sudo apt install python3-pandas
```

**Note:** This error doesn't prevent using the extension, but disables statistics.

### CSV file not displayed correctly

**Possible causes:**
- Non-standard delimiter (extension tries to detect it automatically)
- File encoding not UTF-8
- Corrupted file

**Solution:** Try opening the file with a text editor to verify the format.

### Preview is slow

**Cause:** Very large file (>100MB)

**Solution:** Extension loads only the first 100 rows for speed. For huge files, consider using dedicated tools like LibreOffice Calc.

## Tips

### Performance

- Extension loads only the first 100 rows for speed
- Delimiter detection analyzes only the first 4KB of the file
- With pandas, statistics are calculated on the entire file (may take time for large files)

### Numeric columns

Numeric columns are highlighted in blue and right-aligned for easier reading.

### Null values

In the "Statistics" tab you can see how many null (missing) values there are in each column.

## Technical details

- **Nautilus version:** 43+ (GNOME 43+) with GTK 4
- **Python:** 3.8 or higher
- **Optional dependencies:** pandas (for statistics)
- **Threads:** File loading occurs in a separate thread to avoid blocking the interface

## Usage example

Suppose we have a `sales.csv` file:

```csv
date,product,quantity,price
2024-01-01,Laptop,5,899.99
2024-01-02,Mouse,15,29.99
2024-01-03,Keyboard,8,79.99
```

Right-clicking and selecting "CSV Preview", you'll see:

**Data tab:**
- Table with 3 rows and 4 columns
- "quantity" and "price" columns highlighted in blue

**Statistics tab:**
- Mean, median, min, max for "quantity" and "price"
- No null values

**Columns tab:**
- date: string
- product: string
- quantity: numeric (int64)
- price: numeric (float64)

## Uninstallation

```bash
rm ~/.local/share/nautilus-python/extensions/csv_preview.py
nautilus -q
```

## Contributions

Found a bug or want to improve the extension? Contributions are welcome.

---

**Back to [Main README](../README.md)**
