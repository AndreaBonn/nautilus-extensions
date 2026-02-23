# 📗 Excel Preview - Nautilus Extension

**Language:** [🇮🇹 Italiano](README.md) | **🇬🇧 English**

---

Nautilus extension that adds advanced preview for Excel and LibreOffice Calc files directly from the context menu.

## 🎯 Features

- **View all sheets** in the document
- **Formatted table** with the first 100 rows per sheet
- **Descriptive statistics** for numeric columns
- **Document metadata** (author, creation/modification date)
- **Null value information** for each column
- **Numeric column highlighting** with blue color
- **Multi-stage support** for documents with many sheets

## 📸 What you'll see

When you open an Excel file preview, you'll see a window with:

**Top bar:**
- Number of sheets
- Total rows (sum of all sheets)
- File size
- Author and last modification date

**For each sheet, 3 tabs:**
1. **📊 Data**: Table with data, headers with column type
2. **📈 Statistics**: Descriptive statistics for numeric columns
3. **🗂 Columns**: Detailed information about each column

## 🚀 Installation

### Step 1: Install nautilus-python

```bash
sudo apt update
sudo apt install python3-nautilus
```

### Step 2: Install dependencies

```bash
sudo apt install python3-pandas python3-openpyxl
```

**Note:** Both dependencies are required for this extension.

### Step 3: Create the extensions folder

```bash
mkdir -p ~/.local/share/nautilus-python/extensions
```

### Step 4: Copy the extension file

```bash
cp excel_preview.py ~/.local/share/nautilus-python/extensions/
```

### Step 5: Restart Nautilus

```bash
nautilus -q
```

Reopen Nautilus normally.

## 📖 How to use

1. Open Nautilus and navigate to an Excel or ODS file
2. **Right-click** on the file
3. Select **"Excel Preview"**
4. A window will open with the file preview

### Multi-sheet navigation

- If the file has **one sheet**, you'll see directly the Data/Statistics/Columns tabs
- If the file has **multiple sheets**, you'll first see the sheet tabs (on the left), then the internal tabs for each sheet

### Window features

- **Change sheet**: Click on side tabs (if there are multiple sheets)
- **Resize columns**: Drag the header border
- **Sort data**: Click on a column header
- **Open with LibreOffice**: Click the button at the bottom

## 🔧 Configuration

You can customize the extension by modifying constants in `excel_preview.py`:

```python
PREVIEW_ROWS = 100        # Number of rows to show per sheet
MIN_COL_WIDTH = 80        # Minimum column width in pixels
MAX_COL_WIDTH = 300       # Maximum column width in pixels
WINDOW_W = 1150           # Window width
WINDOW_H = 700            # Window height
```

## 📋 Supported formats

- `.xlsx` - Excel 2007+ (Office Open XML)
- `.xlsm` - Excel with macros
- `.xltx` - Excel template
- `.xltm` - Excel template with macros
- `.ods` - OpenDocument Spreadsheet (LibreOffice/OpenOffice)

## 🐛 Troubleshooting

### Extension doesn't appear in the menu

**Solution:**
```bash
# Verify that nautilus-python is installed
dpkg -l | grep nautilus-python

# Restart Nautilus
nautilus -q
```

### Error "ModuleNotFoundError: No module named 'openpyxl'"

**Solution:**
```bash
sudo apt install python3-openpyxl
```

### Error "ModuleNotFoundError: No module named 'pandas'"

**Solution:**
```bash
sudo apt install python3-pandas
```

### Excel file not displayed correctly

**Possible causes:**
- Corrupted file
- Unsupported format (e.g., old Excel 97-2003 .xls files)
- Password-protected file

**Solution for old .xls files:**
Open the file with LibreOffice and save it as `.xlsx`

### Preview is slow

**Cause:** File with many sheets or many rows

**Solution:** Extension loads only the first 100 rows per sheet. For huge files, use LibreOffice Calc.

### Error "Password-protected file"

**Solution:** Extension doesn't support protected files. Remove protection with LibreOffice.

## 💡 Tips

### Performance

- Extension loads all sheets but only the first 100 rows per sheet
- Total row count is fast (uses file metadata)
- Statistics are calculated on the entire sheet (may take time for large sheets)

### Metadata

In the top bar you can see:
- **Author**: Who created the file
- **Created**: Creation date
- **Modified**: Last modification date
- **Sheets**: Number of sheets in the document

### Numeric columns

Numeric columns are highlighted in blue and show:
- Data type (int64, float64, etc.)
- Descriptive statistics (mean, median, min, max, etc.)
- Null values

## 🔍 Technical details

- **Nautilus version:** 43+ (GNOME 43+) with GTK 4
- **Python:** 3.8 or higher
- **Dependencies:** pandas, openpyxl
- **Threads:** File loading occurs in a separate thread to avoid blocking the interface
- **Optimization:** All sheets are read in a single pandas call for speed

## 📝 Usage example

Suppose we have a `budget.xlsx` file with 2 sheets:

**"Income" sheet:**
```
month,amount,category
January,5000,Sales
February,5500,Sales
```

**"Expenses" sheet:**
```
month,amount,category
January,3000,Salaries
February,3200,Salaries
```

Right-clicking and selecting "Excel Preview", you'll see:

**Top bar:**
- 2 sheets, 4 total rows, file size

**Side tabs:**
- Income
- Expenses

**For each sheet:**
- Data tab: table with "amount" column in blue
- Statistics tab: mean, min, max for "amount"
- Columns tab: month (string), amount (int64), category (string)

## 🗑️ Uninstallation

```bash
rm ~/.local/share/nautilus-python/extensions/excel_preview.py
nautilus -q
```

## 🤝 Contributions

Found a bug or want to improve the extension? Feel free to modify the code!

---

**Back to [Main README](../README_EN.md)**
