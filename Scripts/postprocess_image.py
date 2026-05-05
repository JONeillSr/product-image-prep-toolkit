#!/usr/bin/env python3
"""
Post-Processing Script for Product Photography
Adjusts brightness, contrast, shadows, removes green screen color spill,
and strips all metadata from transparent PNG images after background removal.

Author: John O'Neill Sr.
Company: Azure Innovators

Usage:
    python postprocess_image.py <input.png> <output.png> [options]

Options:
    --brightness FLOAT      Brightness adjustment factor (default: 1.03)
    --contrast FLOAT        Contrast adjustment factor (default: 1.05)
    --shadows INT           Shadow lightening amount 0-100 (default: 15)
    --spill-color COLOR     Color to remove: green, blue, red (default: green)
    --spill-strength FLOAT  Spill removal strength 0.0-1.0 (default: 0.85)
    --no-spill              Skip spill removal
    --no-adjust             Skip brightness/contrast/shadow adjustments
    --no-strip-metadata     Keep image metadata (EXIF, ICC, PNG text chunks)
"""

import sys
import argparse
import numpy as np

try:
    from PIL import Image, ImageEnhance
except ImportError:
    print("ERROR: Pillow is required. Install with: pip install Pillow", file=sys.stderr)
    sys.exit(1)


def adjust_shadows(img_array, shadow_amount):
    """
    Lighten shadow areas of the image.
    shadow_amount: 0-100, where 15 matches Canva's Shadows +15 slider.
    Only affects pixels with alpha > 0 (non-transparent).
    """
    if shadow_amount == 0:
        return img_array

    result = img_array.copy().astype(np.float64)
    alpha = result[:, :, 3]
    mask = alpha > 0

    # Shadow threshold - pixels below this luminance are considered shadows
    rgb = result[:, :, :3]
    luminance = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]

    # Scale factor: shadow_amount of 15 gives a subtle lift
    lift = shadow_amount / 100.0 * 60.0  # Max lift of 60 levels at shadow_amount=100

    # Apply graduated lift - stronger on darker pixels, tapering off on brighter ones
    shadow_threshold = 128.0
    for c in range(3):
        channel = result[:, :, c]
        # Blend factor: 1.0 for pure black, 0.0 at threshold, 0.0 above
        blend = np.clip((shadow_threshold - luminance) / shadow_threshold, 0, 1)
        adjustment = lift * blend
        channel[mask] = np.clip(channel[mask] + adjustment[mask], 0, 255)
        result[:, :, c] = channel

    return result.astype(np.uint8)


def remove_color_spill(img_array, spill_color="green", strength=0.85):
    """
    Remove color spill (fringing) from green/blue/red screen edges.
    This replicates the Canva technique of selecting the spill color and
    setting Hue, Saturation, and Brightness all to -100.

    Works by detecting pixels with a dominant spill-color channel near
    semi-transparent edges and desaturating/darkening the spill color.
    """
    if strength <= 0:
        return img_array

    result = img_array.copy().astype(np.float64)
    alpha = result[:, :, 3]

    # Only process pixels that are visible (alpha > 0)
    visible = alpha > 0

    rgb = result[:, :, :3]
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]

    if spill_color == "green":
        # Detect green-dominant pixels
        # Green spill: G channel is significantly higher than R and B
        spill_excess = g - np.maximum(r, b)
        spill_mask = (spill_excess > 10) & visible

        if np.any(spill_mask):
            # Calculate how "green" each pixel is (0 to 1)
            max_rgb = np.maximum(np.maximum(r, g), b)
            max_rgb = np.where(max_rgb == 0, 1, max_rgb)  # avoid div by zero
            green_ratio = spill_excess / max_rgb
            green_ratio = np.clip(green_ratio, 0, 1)

            # Apply correction: reduce green, boost red and blue slightly
            correction = green_ratio * strength
            result[:, :, 1][spill_mask] = np.clip(
                g[spill_mask] - (spill_excess[spill_mask] * correction[spill_mask]),
                0, 255
            )
            # Slight warmth compensation
            result[:, :, 0][spill_mask] = np.clip(
                r[spill_mask] + (spill_excess[spill_mask] * correction[spill_mask] * 0.1),
                0, 255
            )

    elif spill_color == "blue":
        spill_excess = b - np.maximum(r, g)
        spill_mask = (spill_excess > 10) & visible

        if np.any(spill_mask):
            max_rgb = np.maximum(np.maximum(r, g), b)
            max_rgb = np.where(max_rgb == 0, 1, max_rgb)
            blue_ratio = spill_excess / max_rgb
            blue_ratio = np.clip(blue_ratio, 0, 1)

            correction = blue_ratio * strength
            result[:, :, 2][spill_mask] = np.clip(
                b[spill_mask] - (spill_excess[spill_mask] * correction[spill_mask]),
                0, 255
            )

    elif spill_color == "red":
        spill_excess = r - np.maximum(g, b)
        spill_mask = (spill_excess > 10) & visible

        if np.any(spill_mask):
            max_rgb = np.maximum(np.maximum(r, g), b)
            max_rgb = np.where(max_rgb == 0, 1, max_rgb)
            red_ratio = spill_excess / max_rgb
            red_ratio = np.clip(red_ratio, 0, 1)

            correction = red_ratio * strength
            result[:, :, 0][spill_mask] = np.clip(
                r[spill_mask] - (spill_excess[spill_mask] * correction[spill_mask]),
                0, 255
            )

    return result.astype(np.uint8)


def strip_metadata(img):
    """
    Strip ALL metadata from a PIL Image, returning a clean copy.

    Removes EXIF data (camera model, GPS coordinates, timestamps, software
    tags), ICC color profiles, PNG text chunks (tEXt, iTXt, zTXt), XMP data,
    and any other ancillary metadata. The result is a pixel-identical image
    with zero embedded metadata — safe for public product listings on
    WooCommerce, eBay, Amazon, Etsy, and similar platforms.

    Why this matters for e-commerce:
    - EXIF GPS tags can expose your studio/warehouse location
    - Camera and software metadata reveals your production workflow
    - Some platforms inject their own metadata on upload; starting clean
      avoids conflicts and keeps file sizes minimal
    - Stripping ICC profiles is safe for web-destined PNGs rendered in sRGB
    """
    # Create a brand-new image with only pixel data — no metadata carries over
    clean = Image.new(img.mode, img.size)
    clean.putdata(list(img.getdata()))
    return clean


def postprocess_image(input_path, output_path,
                      brightness=1.03, contrast=1.05,
                      shadow_amount=15, spill_color="green",
                      spill_strength=0.85, do_spill=True,
                      do_adjust=True, do_strip_metadata=True):
    """
    Main post-processing pipeline.
    Order: Spill removal -> Shadow lift -> Brightness -> Contrast -> Metadata strip
    """
    try:
        img = Image.open(input_path).convert("RGBA")
    except Exception as e:
        print(f"ERROR: Cannot open image: {e}", file=sys.stderr)
        return False

    img_array = np.array(img)

    # Step 1: Remove color spill (do this first on raw data)
    if do_spill:
        img_array = remove_color_spill(img_array, spill_color, spill_strength)

    # Step 2: Adjust shadows
    if do_adjust and shadow_amount > 0:
        img_array = adjust_shadows(img_array, shadow_amount)

    # Convert back to PIL for enhancement filters
    img = Image.fromarray(img_array, "RGBA")

    if do_adjust:
        # Step 3: Brightness
        if brightness != 1.0:
            # Split alpha to preserve it through enhancement
            r, g, b, a = img.split()
            rgb_img = Image.merge("RGB", (r, g, b))
            enhancer = ImageEnhance.Brightness(rgb_img)
            rgb_img = enhancer.enhance(brightness)
            r2, g2, b2 = rgb_img.split()
            img = Image.merge("RGBA", (r2, g2, b2, a))

        # Step 4: Contrast
        if contrast != 1.0:
            r, g, b, a = img.split()
            rgb_img = Image.merge("RGB", (r, g, b))
            enhancer = ImageEnhance.Contrast(rgb_img)
            rgb_img = enhancer.enhance(contrast)
            r2, g2, b2 = rgb_img.split()
            img = Image.merge("RGBA", (r2, g2, b2, a))

    # Step 5: Strip metadata
    if do_strip_metadata:
        img = strip_metadata(img)

    try:
        img.save(output_path, "PNG", optimize=True)
        return True
    except Exception as e:
        print(f"ERROR: Cannot save image: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Post-process transparent PNGs: adjust brightness, contrast, shadows, and remove color spill."
    )
    parser.add_argument("input", help="Input PNG file path")
    parser.add_argument("output", help="Output PNG file path")
    parser.add_argument("--brightness", type=float, default=1.03,
                        help="Brightness factor (default: 1.03, Canva +5 equivalent)")
    parser.add_argument("--contrast", type=float, default=1.05,
                        help="Contrast factor (default: 1.05, Canva +5 equivalent)")
    parser.add_argument("--shadows", type=int, default=15,
                        help="Shadow lightening 0-100 (default: 15)")
    parser.add_argument("--spill-color", choices=["green", "blue", "red"],
                        default="green", help="Spill color to remove (default: green)")
    parser.add_argument("--spill-strength", type=float, default=0.85,
                        help="Spill removal strength 0.0-1.0 (default: 0.85)")
    parser.add_argument("--no-spill", action="store_true",
                        help="Skip spill removal")
    parser.add_argument("--no-adjust", action="store_true",
                        help="Skip brightness/contrast/shadow adjustments")
    parser.add_argument("--no-strip-metadata", action="store_true",
                        help="Keep image metadata (EXIF, ICC profiles, PNG text chunks)")

    args = parser.parse_args()

    success = postprocess_image(
        args.input, args.output,
        brightness=args.brightness,
        contrast=args.contrast,
        shadow_amount=args.shadows,
        spill_color=args.spill_color,
        spill_strength=args.spill_strength,
        do_spill=not args.no_spill,
        do_adjust=not args.no_adjust,
        do_strip_metadata=not args.no_strip_metadata
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
