# Changelog

All notable changes to the **product-image-prep-toolkit** project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.1.0] - 2026-05-07

### Added

- **4-pass spill removal** — Completely rewrote the color spill removal algorithm to handle dark products (rubber, black plastic, dark metal) where the v2.0 single-pass approach missed subtle green fringe:
  - Pass 1: Absolute excess detection with lowered threshold (10 → 2) to catch spill on dark surfaces
  - Pass 2: Ratio-based detection for dark pixels (max channel < 80) using proportional comparison instead of absolute differences
  - Pass 3: Edge desaturation within 16px of the product boundary, blending remaining color cast toward neutral gray
  - Pass 4: Hard edge clamp at outermost boundary pixels, forcing the spill channel down when it still exceeds the average of the other channels
- **Edge-proximity weighting** — Uses SciPy binary erosion to build a distance map from product edges. Corrections are strongest at the product boundary (where spill concentrates) and taper to 30% strength in the interior, preventing over-correction on legitimately colored surfaces.
- **Solid-background detection** — Spill removal now automatically detects whether the image has real transparency (alpha varies) or a solid background (alpha=255 everywhere with black background). Edge detection adapts accordingly using luminance-based product boundary detection as a fallback.
- **SciPy dependency** — Added to `-InstallRembg` installation and prerequisite checks. Used for `ndimage.binary_erosion` in edge proximity calculations. Falls back to uniform weighting if SciPy is not available.
- **Standalone SEO rename mode** — New `-RenameCSV` parameter enables copy-and-rename of existing images from a 3-column CSV (`SourceFileName`, `SEOFileName`, `AltText`) without any image processing. Useful for renaming already-processed images for e-commerce upload.
- **Alt text embedding** — New `-EmbedAltText` switch writes alt text from the CSV as PNG tEXt metadata (Alt, Description, and Comment chunks) for accessibility and image search SEO. Requires Python and Pillow; only applies to `.png` files.
- **Rename mode parameters** — `-RenameInputPath` (source folder) and `-RenameOutputPath` (destination folder, defaults to `SEO-Renamed` subfolder).
- **Rename report** — Generates `SEO-Rename-Report.csv` in the output folder with per-file status (Renamed, Skipped, Failed) and reasons.
- **Rename template** — `scripts/seo-rename-template.csv` included with example product entries.
- **Pillow 14 forward compatibility** — Metadata stripping now uses `get_flattened_data()` with a fallback to the deprecated `getdata()` for older Pillow versions.

### Changed

- Spill correction refactored from three separate color-specific code paths into a single generic `_apply_spill_correction()` function that handles green, blue, and red identically via channel index mapping.
- Dependency check (`Test-PillowInstalled`) now verifies SciPy alongside Pillow and NumPy.
- Install messages updated to reflect SciPy as a required dependency.

---

## [2.0.0] - 2026-05-02

### Added

- **Post-processing pipeline** — Automatic brightness, contrast, and shadow adjustment after background removal using a companion Python script (`scripts/postprocess_image.py`). Defaults are tuned for product photography shot on green screen and match common Canva adjustment values.
- **Green/blue/red screen spill removal** — Detects pixels where the chroma key color channel dominates and suppresses the excess proportionally. Strongest at edges where screen color bleeds onto the product, tapering off on neutral areas. Configurable via `-SpillColor` and `-SpillStrength`.
- **Metadata stripping** — Strips ALL metadata from output images by default: EXIF data (camera model, GPS coordinates, timestamps, software tags), ICC color profiles, PNG text chunks (tEXt, iTXt, zTXt), and XMP data. Prevents leaking studio/warehouse GPS coordinates into product listings and reduces file size.
- **SEO-friendly file naming** — Three modes for generating Google image search optimized filenames:
  - `-SEOName` / `-SEOPrefix` / `-SEOSuffix` for single-image or uniform batch naming
  - `-SEOMappingFile` for CSV-based batch renaming with per-image control
  - Automatic deduplication with numeric suffixes when multiple images share the same SEO name
- **New parameters:**
  - `-NoPostProcess` — Skip the entire post-processing pipeline
  - `-NoStripMetadata` — Preserve image metadata when needed for archival or print workflows
  - `-Brightness` (default: 1.03) — Brightness adjustment factor, range 0.5–2.0
  - `-Contrast` (default: 1.05) — Contrast adjustment factor, range 0.5–2.0
  - `-Shadows` (default: 15) — Shadow lightening amount, range 0–100
  - `-SpillColor` (default: `green`) — Chroma key color to remove: `green`, `blue`, `red`, or `none`
  - `-SpillStrength` (default: 0.85) — Spill removal intensity, range 0.0–1.0
  - `-SEOName` — SEO-friendly base name for output files
  - `-SEOPrefix` — Prefix added before SEO name (e.g., brand name)
  - `-SEOSuffix` — Suffix added after SEO name (e.g., `transparent`)
  - `-SEOMappingFile` — Path to CSV mapping source filenames to SEO names
- **Companion script** — `postprocess_image.py` handles all image manipulation via Pillow and NumPy, called automatically by the PowerShell script after rembg completes.
- **Enhanced CSV report** — New columns: `SEOFileName`, `PostProcessed`, `MetadataStripped`, `BrightnessSetting`, `ContrastSetting`, `ShadowsSetting`, `SpillColor`.
- **Pillow and NumPy** added to `-InstallRembg` dependency installation.
- **SEO mapping template** — `scripts/seo-mapping-template.csv` included as a starting point for batch product naming.

### Changed

- **Renamed script** from `Remove-ImageBackground.ps1` to `Process-ProductPics.ps1` to better reflect the full processing pipeline.
- **Reorganized repository** — Scripts moved to `scripts/`, documentation to `docs/`, with `examples/` and `templates/` directories added for future content.
- Banner and log headers updated from "JT Custom Trailers" to "Azure Innovators" branding.
- Version bumped to 2.0.0 to reflect breaking changes: renamed script, reorganized repo structure, and new dependency on `postprocess_image.py` companion script.
- Watcher mode now includes full post-processing pipeline, spill removal, and metadata stripping for automatically detected images.
- Processing summary now displays post-processing settings and post-processed image count.

---

## [1.1.0] - 2024-12-15

### Added

- **Processed folder** — Source images are automatically moved to a `Processed` subfolder after successful background removal, keeping the input directory clean.
- **CSV report generation** — Detailed per-image report with timestamps, source/output file paths, file sizes, size reduction percentage, processing time, model used, and error messages. Saved as `BackgroundRemoval-Report-{timestamp}.csv`.
- **Log file** — Timestamped processing log written to `BackgroundRemoval.log` in the input directory.
- **New parameters:**
  - `-NoMove` — Keep source files in place instead of moving them to the Processed folder
  - `-LogPath` — Custom path for the log file
  - `-ReportPath` — Custom path for the CSV report
- **Watcher mode improvements** — File watcher now moves processed source files to the Processed folder and logs results to the CSV report.
- **Processing statistics** — Summary includes total source/output sizes, average processing time, and file counts.

---

## [1.0.0] - 2024-12-14

### Added

- **Initial release** of the AI-powered background removal script for product photography.
- **Single image processing** — Process individual image files with background removal.
- **Batch folder processing** — Process all supported images in a folder with progress tracking.
- **File watcher mode** — Monitor a folder for new images and automatically process them as they arrive. Activate with `-Watch`.
- **Multiple AI model support** — Choose from 9 rembg models: `u2net` (default), `u2netp`, `u2net_human_seg`, `u2net_cloth_seg`, `silueta`, `isnet-general-use`, `isnet-anime`, `sam`, `birefnet-general`.
- **Alpha matting** — Optional edge refinement with `-AlphaMatting` for improved transparency boundaries on complex edges (hair, fur, fine details).
- **Recursive processing** — Process subfolders with `-Recursive`.
- **Automatic dependency installation** — Run `-InstallRembg` to install rembg and its dependencies via pip.
- **Progress tracking** — Progress bar with percentage, current file name, and file count during batch processing.
- **Color-coded console output** — Info (cyan), success (green), warning (yellow), error (red) messages with timestamps.
- **Error handling** — Try-catch blocks with detailed error messages, file accessibility retries in watcher mode, and graceful handling of unsupported file formats.
- **Supported formats** — JPG, JPEG, PNG, WEBP, BMP, TIFF.

---

## Links

- **Repository:** [https://github.com/JONeillSr/product-image-prep-toolkit](https://github.com/JONeillSr/product-image-prep-toolkit)
- **Author:** John O'Neill Sr. — [Azure Innovators](https://www.azureinnovators.com)
- **rembg:** [https://github.com/danielgatis/rembg](https://github.com/danielgatis/rembg)

[2.1.0]: https://github.com/JONeillSr/product-image-prep-toolkit/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/JONeillSr/product-image-prep-toolkit/compare/v1.1.0...v2.0.0
[1.1.0]: https://github.com/JONeillSr/product-image-prep-toolkit/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/JONeillSr/product-image-prep-toolkit/releases/tag/v1.0.0
