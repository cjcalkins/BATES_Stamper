# PDF Combiner & Stamper

A desktop GUI application for applying BATES stamps to PDF and image documents. Combine multiple files into a single stamped PDF, control stamp placement and color on a per-file and per-page basis, remove stamps from previously processed documents, and extract pages for export — all from a clean tabbed interface.

---

## Features

### Combine & Stamp
- Add any mix of PDF and image files (`.pdf`, `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.gif`, `.webp`)
- Reorder files with **Move Up / Move Down** controls before combining
- Hover over a file's thumbnail to preview a larger version before processing
- Configure a **prefix**, **starting number**, and optional **suffix** for each stamp (e.g. `EXH.000042 CONFIDENTIAL`)
- Stamps are placed at both the **top-right and bottom-right** of every page by default
- **Manual Placement** mode lets you drag stamps to any position on a per-page basis using a live preview editor
- Choose **stamp color** per file, with per-page color overrides available in the placement editor
- Select **font** (Helvetica, Times, Courier — bold or regular) and **font size** (10–20pt)
- Output filename is auto-generated from the prefix/number/suffix if no path is specified
- Option to automatically open the result in the **View & Export** tab after saving

### Remove Stamp
- Strip all stamps from a PDF previously produced by this tool using PDF redaction
- Outputs a clean copy to a user-specified path (defaults to `<original>_clean.pdf`)

### View & Export Pages
- Open any PDF in a full-screen viewer with **Tile View** (5-column thumbnail grid) and **Full View** (single-page, zoomable)
- Zoom in/out and **Fit to Window** in Full View; pan with click-and-drag
- Keyboard navigation with left/right arrow keys
- Click thumbnails or checkboxes in Tile View to select pages; toggle individual pages in Full View
- Export any selection of pages as a new PDF
- Visual indicators mark pages that have already been exported in the current session

---

## Requirements

Python 3.8 or later with the following packages:

```
pymupdf
pillow
sv-ttk
```

Install with:

```bash
pip install pymupdf pillow sv-ttk
```

---

## Usage

```bash
python pdf.py
```

The application launches maximized. Use the three tabs along the top to switch between Combine & Stamp, Remove Stamp, and View & Export Pages.

### Basic Stamping Workflow

1. Open the **Combine & Stamp** tab.
2. Click **Add Files** and select one or more PDFs or images.
3. Reorder them if needed using **Move Up / Move Down**.
4. Set your **Prefix** (e.g. `EXH`), **Starting Number**, and optional **Suffix**.
5. Choose a **Font**, **Font Size**, and **stamp color** for each file. Enable **Manual Placement** on any file to drag stamps to exact positions page by page.
6. Set an output path with **Browse...**, or leave it blank to auto-generate one.
7. Click **COMBINE PDFs & APPLY STAMPS**.

### Stamp Format

Each page receives a stamp in the format:

```
PREFIX.000001
PREFIX.000001 SUFFIX
```

The number is zero-padded to six digits and increments by one for every page across all input files.

### Manual Placement Editor

When **Manual Placement** is checked for a file, a **Set Position** button appears. Clicking it opens a full-page preview where two stamp labels — one for the top, one for the bottom — can be dragged freely. Colors can also be set per page in this editor. Click **Save All Positions** when done.

### Removing Stamps

1. Open the **Remove Stamp** tab.
2. Browse for the stamped input PDF.
3. Set an output path (auto-fills to `<filename>_clean.pdf`).
4. Click **REMOVE STAMPS**.

> Note: This uses PDF redaction to white out the entire page annotation layer. It is best suited for PDFs produced by this tool.

### Viewing and Exporting Pages

1. Open the **View & Export Pages** tab and click **Open PDF for Viewing**, or check **Open in View & Export after saving** on the Combine tab.
2. Browse pages in **Tile View** or **Full View**.
3. Check pages to select them, then click **Export Selected Pages** to save a subset as a new PDF.

---

## File Support

| Format | Input | Notes |
|--------|-------|-------|
| PDF | ✅ | Multi-page supported |
| JPEG / JPG | ✅ | Converted to single-page PDF internally |
| PNG | ✅ | Converted to single-page PDF internally |
| BMP | ✅ | Converted to single-page PDF internally |
| TIFF | ✅ | Converted to single-page PDF internally |
| GIF | ✅ | Converted to single-page PDF internally |
| WebP | ✅ | Converted to single-page PDF internally |

---

## Dependencies

| Package | Purpose |
|---------|---------|
| [PyMuPDF](https://pymupdf.readthedocs.io/) (`fitz`) | PDF rendering, text insertion, redaction, and merging |
| [Pillow](https://python-pillow.org/) | Image loading and thumbnail generation |
| [sv-ttk](https://github.com/rdbende/Sun-Valley-ttk-theme) | Sun Valley light theme for the tkinter UI |
| tkinter | GUI framework (included with standard Python) |

---

## Notes

- The application saves output PDFs with garbage collection, compression, and cleaning enabled (`garbage=1, deflate=True, clean=True`) for compact file sizes.
- Stamp removal uses full-page redaction and will erase any annotation layer content, not just BATES text. Use on a copy if the original annotations need to be preserved.
- There is no undo within a session; reorder and configure files carefully before processing.
