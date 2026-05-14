# product-image-prep-toolkit

AI-powered background removal and post-processing pipeline for product photography. Built for e-commerce sellers who need transparent PNGs ready for WooCommerce, eBay, Amazon, and Etsy — without the manual Canva/Photoshop cleanup.

![PowerShell](https://img.shields.io/badge/PowerShell-5.1%2B-blue?logo=powershell)
![Python](https://img.shields.io/badge/Python-3.10%2B-yellow?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

## What It Does

Drop your product photos in a folder and this script handles the entire pipeline:

1. **Background Removal** — Uses the [rembg](https://github.com/danielgatis/rembg) AI library to remove backgrounds and produce transparent PNGs
2. **Color Correction** — Adjusts brightness, contrast, and shadows automatically (defaults match common Canva adjustments)
3. **Green Screen Spill Removal** — Detects and suppresses color fringing from green, blue, or red screen setups
4. **Metadata Stripping** — Removes ALL EXIF data, GPS coordinates, ICC profiles, and PNG text chunks so your studio location doesn't leak into product listings
5. **SEO File Naming** — Renames output files with Google-friendly, hyphen-separated, lowercase names optimized for image search indexing
6. **Batch Processing & File Watcher** — Process entire folders at once, or run in watch mode for automatic processing as new photos land

## Quick Start

### 1. Install Dependencies

```powershell
# One-time setup — installs rembg, Pillow, and NumPy
.\scripts\Process-ProductPics.ps1 -InstallRembg
```

> **Prerequisite:** Python 3.10+ must be installed. If you don't have it:
> ```powershell
> winget install Python.Python.3.12
> ```

### 2. Process Your Images

```powershell
# Basic — process a folder with all defaults (post-processing + metadata stripping)
.\scripts\Process-ProductPics.ps1 -InputPath "C:\Photos\Products" -OutputPath "C:\Photos\Transparent"

# Single image with SEO naming
.\scripts\Process-ProductPics.ps1 -InputPath "C:\Photos\valve.jpg" -OutputPath "C:\Photos\Ready" `
    -SEOName "check valve 2 inch" -SEOPrefix "jt-custom" -SEOSuffix "transparent"
# Output: jt-custom-check-valve-2-inch-transparent.png

# Watch mode — automatically process new images as they're added
.\scripts\Process-ProductPics.ps1 -InputPath "C:\Photos\Incoming" -OutputPath "C:\Photos\Ready" -Watch
```

### 3. File Placement

The PowerShell script and Python companion script must be in the **same directory**. If you clone this repo and run from the `scripts/` folder, they're already co-located:

```powershell
cd scripts
.\Process-ProductPics.ps1 -InputPath "C:\Photos\Products" -OutputPath "C:\Photos\Transparent"
```

## Repository Structure

```
product-image-prep-toolkit/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── .gitignore
│
├── scripts/
│   ├── Process-ProductPics.ps1       # Main PowerShell script
│   ├── postprocess_image.py          # Companion Python post-processing script
│   ├── seo-mapping-template.csv      # Template for batch SEO naming during processing
│   └── seo-rename-template.csv       # Template for standalone SEO rename mode
│
├── examples/                          # Example images and usage demos
│
├── docs/
│   └── TROUBLESHOOTING.md            # Common issues and solutions
│
└── templates/                         # Reusable templates
```

## Features

### Background Removal

Powered by rembg with support for multiple AI models:

| Model | Best For | Speed |
|-------|----------|-------|
| `u2net` (default) | General purpose, good all-around | Medium |
| `u2netp` | Lightweight, faster processing | Fast |
| `isnet-general-use` | High accuracy on complex backgrounds | Slow |
| `birefnet-general` | Latest generation, excellent edges | Slow |
| `u2net_human_seg` | People/portraits | Medium |
| `silueta` | Similar to u2net, different training | Medium |

```powershell
# Use a different model
.\scripts\Process-ProductPics.ps1 -InputPath "C:\Photos" -OutputPath "C:\Output" -Model "isnet-general-use"

# Enable alpha matting for cleaner edges (slower)
.\scripts\Process-ProductPics.ps1 -InputPath "C:\Photos" -OutputPath "C:\Output" -AlphaMatting
```

### Post-Processing Pipeline

Runs automatically after background removal. The defaults are tuned for product photography shot on a green screen:

| Setting | Default | Equivalent |
|---------|---------|------------|
| Brightness | 1.03 | Canva Brightness +5 |
| Contrast | 1.05 | Canva Contrast +5 |
| Shadows | 15 | Canva Shadows +15 |
| Spill Color | green | Canva Color Edit: select green, all sliders -100 |
| Spill Strength | 0.85 | 85% removal intensity |
| Metadata Strip | On | Removes EXIF, GPS, ICC, PNG text chunks |

```powershell
# Custom values for darker products
.\scripts\Process-ProductPics.ps1 -InputPath "C:\Photos" -OutputPath "C:\Output" `
    -Brightness 1.08 -Contrast 1.10 -Shadows 25

# Blue screen setup
.\scripts\Process-ProductPics.ps1 -InputPath "C:\Photos" -OutputPath "C:\Output" `
    -SpillColor "blue" -SpillStrength 0.9

# Skip all post-processing (raw background removal only)
.\scripts\Process-ProductPics.ps1 -InputPath "C:\Photos" -OutputPath "C:\Output" -NoPostProcess

# Keep metadata (for archival or print workflows)
.\scripts\Process-ProductPics.ps1 -InputPath "C:\Photos" -OutputPath "C:\Output" -NoStripMetadata
```

### Green Screen Spill Removal

When shooting products on a green screen, the edges of the product often pick up a green tint ("spill" or "fringing"). This is especially problematic on dark products like rubber, black plastic, and dark metal where the absolute color differences are tiny but the green cast is still visually obvious.

The script uses a **4-pass approach** to eliminate spill:

1. **Absolute excess** (threshold of 2) — catches obvious green dominance, tuned low enough for dark products
2. **Ratio-based detection** — for pixels darker than 80 luminance, uses proportional comparison instead of absolute, catching subtle spill the first pass misses
3. **Edge desaturation** — within 16px of the product boundary, desaturates any remaining color cast toward neutral gray
4. **Hard edge clamp** — at the outermost product boundary pixels, forces the spill channel down if it still exceeds the average of the other two channels

Edge proximity is calculated using SciPy binary erosion, so corrections are strongest at the product outline (where spill concentrates) and gentler in the interior to avoid over-correcting legitimately colored surfaces.

The algorithm also automatically detects whether the image has real transparency (alpha varies) or a solid background (alpha=255 everywhere, background is black), and adjusts its edge detection accordingly.

Also supports `-SpillColor blue` and `-SpillColor red` for other chroma key setups. Use `-SpillColor none` to skip spill removal while keeping other adjustments.

### Metadata Stripping

By default, ALL metadata is stripped from output images:

- **EXIF data** — Camera model, lens info, timestamps, software tags
- **GPS coordinates** — Your studio/warehouse location
- **ICC color profiles** — Safe to remove for web-destined sRGB PNGs
- **PNG text chunks** — tEXt, iTXt, zTXt ancillary data
- **XMP data** — Adobe metadata

This is critical for e-commerce: you don't want GPS coordinates in your product photos exposing your business address. It also shaves a few KB off each file.

Use `-NoStripMetadata` if you need to preserve color profiles or other embedded data for print workflows.

### SEO File Naming

Output filenames follow Google image search best practices:

- Lowercase
- Hyphens as word separators (Google treats hyphens as spaces)
- No special characters, underscores, or spaces
- Primary keywords front-loaded
- Automatic deduplication with numeric suffixes for batch processing

Three ways to use it:

**Single image or uniform naming:**

```powershell
.\scripts\Process-ProductPics.ps1 -InputPath "C:\Photos\IMG_0042.jpg" -OutputPath "C:\Ready" `
    -SEOName "check valve 2 inch abs" -SEOPrefix "jt-custom" -SEOSuffix "transparent"
# Output: jt-custom-check-valve-2-inch-abs-transparent.png
```

**Batch with CSV mapping file:**

```powershell
.\scripts\Process-ProductPics.ps1 -InputPath "C:\Photos\Products" -OutputPath "C:\Ready" `
    -SEOMappingFile ".\scripts\seo-mapping-template.csv"
```

**CSV format** (see [`scripts/seo-mapping-template.csv`](scripts/seo-mapping-template.csv)):

```csv
SourceFileName,SEOName,SEOPrefix,SEOSuffix
IMG_0001.jpg,check-valve-2-inch-abs,jt-custom,transparent
IMG_0002.jpg,backflow-preventer-pvc,jt-custom,transparent
IMG_0003.jpg,swing-check-valve-1-5-inch,jt-custom,transparent
DSC_1001.jpg,trailer-hitch-heavy-duty,jt-custom,product-photo
```

**Without SEO naming:**

If you don't pass `-SEOName` or `-SEOMappingFile`, the original filename is used with a `.png` extension.

### Standalone SEO Rename Mode

Already have processed images and just need to rename them with SEO filenames and alt text? Use rename mode — no background removal or post-processing, just fast copy-and-rename from a CSV:

```powershell
# Basic rename from CSV
.\scripts\Process-ProductPics.ps1 -RenameCSV "C:\Photos\seo-names.csv" `
    -RenameInputPath "C:\Photos\Transparent"
# Output goes to C:\Photos\Transparent\SEO-Renamed\

# Rename with custom output folder and embedded alt text
.\scripts\Process-ProductPics.ps1 -RenameCSV "C:\Photos\seo-names.csv" `
    -RenameInputPath "C:\Photos\Transparent" `
    -RenameOutputPath "C:\Photos\Ready" `
    -EmbedAltText
```

**CSV format** (see [`scripts/seo-rename-template.csv`](scripts/seo-rename-template.csv)):

```csv
SourceFileName,SEOFileName,AltText
IMG_0001.png,check-valve-2-inch-abs-transparent.png,2 inch ABS check valve for plumbing
IMG_0002.png,rubber-weather-stripping-door-seal.png,Automotive rubber weather stripping door seal
IMG_0003.png,push-retainer-clip-nylon-black.png,Black nylon push retainer clip for door panels
```

The `-EmbedAltText` switch writes the alt text as PNG tEXt metadata (Alt, Description, and Comment chunks). This helps with accessibility and some e-commerce platforms that read embedded image metadata. Requires Python and Pillow; only applies to `.png` files.

### File Watcher Mode

Drop images into a watched folder and they're automatically processed:

```powershell
.\scripts\Process-ProductPics.ps1 -InputPath "C:\Photos\Incoming" -OutputPath "C:\Photos\Ready" -Watch
```

All post-processing settings apply in watch mode. Press `Ctrl+C` to stop.

### Reporting & Logging

Every run generates:

- **Log file** (`BackgroundRemoval.log`) — Timestamped processing details
- **CSV report** (`BackgroundRemoval-Report-{timestamp}.csv`) — Per-image results including source/output sizes, processing time, SEO filename, post-processing settings, metadata status, and any errors

Processed source images are automatically moved to a `Processed` subfolder (disable with `-NoMove`).

## All Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `-InputPath` | String | *(required)* | Path to image file or folder |
| `-OutputPath` | String | *(required)* | Output folder for processed images |
| `-Watch` | Switch | Off | Enable file watcher mode |
| `-Model` | String | `u2net` | rembg AI model to use |
| `-InstallRembg` | Switch | — | Install/update all dependencies |
| `-AlphaMatting` | Switch | Off | Improved edge quality (slower) |
| `-Recursive` | Switch | Off | Process subfolders recursively |
| `-NoMove` | Switch | Off | Don't move source files after processing |
| `-NoPostProcess` | Switch | Off | Skip all post-processing |
| `-NoStripMetadata` | Switch | Off | Keep image metadata |
| `-Brightness` | Double | `1.03` | Brightness factor (0.5–2.0) |
| `-Contrast` | Double | `1.05` | Contrast factor (0.5–2.0) |
| `-Shadows` | Int | `15` | Shadow lightening (0–100) |
| `-SpillColor` | String | `green` | Spill to remove: `green`, `blue`, `red`, `none` |
| `-SpillStrength` | Double | `0.85` | Spill removal strength (0.0–1.0) |
| `-SEOName` | String | — | SEO-friendly base filename |
| `-SEOPrefix` | String | — | Prefix before SEO name |
| `-SEOSuffix` | String | — | Suffix after SEO name |
| `-SEOMappingFile` | String | — | CSV file for batch SEO naming |
| `-RenameCSV` | String | — | CSV file for standalone rename mode (no processing) |
| `-RenameInputPath` | String | — | Source folder for rename mode |
| `-RenameOutputPath` | String | Auto | Output folder for rename mode (default: SEO-Renamed subfolder) |
| `-EmbedAltText` | Switch | Off | Embed alt text from CSV as PNG metadata |
| `-LogPath` | String | Auto | Custom log file path |
| `-ReportPath` | String | Auto | Custom CSV report path |

## Supported Image Formats

JPG, JPEG, PNG, WEBP, BMP, TIFF

## Requirements

- **Windows** with PowerShell 5.1+
- **Python 3.10+** ([download](https://www.python.org/downloads/) or `winget install Python.Python.3.12`)
- **pip** (included with Python)
- **rembg** — installed via `-InstallRembg`
- **Pillow** — installed via `-InstallRembg`
- **NumPy** — installed via `-InstallRembg`
- **SciPy** — installed via `-InstallRembg` (used for edge-proximity spill detection)

## Troubleshooting

See [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) for common issues and solutions.

## Author

**John O'Neill Sr.**
[Azure Innovators](https://www.azureinnovators.com) — Cloud Security & Enterprise IT Consulting

## License

MIT License — see [LICENSE](LICENSE) for details.
