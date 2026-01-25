#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
imgtobitmap.py - Convert image files to Python bitmap modules for st7789_mpy

This script converts image files (PNG, JPG, etc.) to Python bitmap modules
compatible with the st7789_mpy library and the image2bin.py conversion script.
The output modules can be used with st7789.bitmap() method.

Usage:
    python imgtobitmap.py <image_file> <colors>

Example:
    python imgtobitmap.py logo.png 4 > logo.py
"""

import argparse
import sys

from PIL import Image


def convert_image_to_bitmap(image_path, colors):
    """
    Convert an image file to a Python bitmap module

    Args:
        image_path (str): Path to the input image file
        colors (int): Number of colors in the output (must be a power of 2, max 256)
    """
    try:
        # Validate colors
        if colors <= 0 or (colors & (colors - 1)) != 0 or colors > 256:
            print(f"Error: Colors must be a power of 2 between 1 and 256, got {colors}")
            return False

        # Calculate bits per pixel
        bpp = 0
        while (1 << bpp) < colors:
            bpp += 1

        # Load image
        img = Image.open(image_path)

        # Convert to palette image with specified number of colors
        img = img.convert("P", palette=Image.Palette.ADAPTIVE, colors=colors)
        palette = img.getpalette()

        # Get actual number of colors
        palette_colors = len(palette) // 3
        bits_required = palette_colors.bit_length()

        if bits_required < bpp:
            print(
                f"\nNOTE: Quantization reduced colors to {palette_colors} from the {colors} "
                f"requested, reconverting using {bits_required} bit per pixel could save memory.\n",
                file=sys.stderr,
            )

        # For all the colors in the palette
        colors_hex = []

        for color in range(palette_colors):
            # Get RGB values and convert to 565
            color565 = (
                ((palette[color * 3] & 0xF8) << 8)
                | ((palette[color * 3 + 1] & 0xFC) << 3)
                | (palette[color * 3 + 2] & 0xF8) >> 3
            )

            # Swap bytes in 565
            color_val = ((color565 & 0xFF) << 8) + ((color565 & 0xFF00) >> 8)

            # Append byte swapped 565 color to colors
            colors_hex.append(f"{color_val:04x}")

        # Generate bitmap data
        image_bitstring = ""

        # Run through the image and create a string with the ascii binary
        # representation of the color of each pixel.
        for y in range(img.height):
            for x in range(img.width):
                pixel = img.getpixel((x, y))
                bstring = "".join(
                    "1" if (pixel & (1 << bit - 1)) else "0"
                    for bit in range(bpp, 0, -1)
                )
                image_bitstring += bstring

        bitmap_bits = len(image_bitstring)
        max_colors = 1 << bpp

        # Create python source with image parameters
        print(f"HEIGHT = {img.height}")
        print(f"WIDTH = {img.width}")
        print(f"COLORS = {max_colors}")
        print(f"BPP = {bpp}")
        print("PALETTE = [", sep="", end="")

        for color, rgb in enumerate(colors_hex):
            if color:
                print(",", sep="", end="")
            print(f"0x{rgb}", sep="", end="")
        print("]")

        # Run though image bit string 8 bits at a time
        # and create python array source for memoryview

        print("_bitmap =\\", sep="")
        print("b'", sep="", end="")

        for i in range(0, bitmap_bits, 8):
            # Limit line length for readability
            if i and i % (16 * 8) == 0:
                print("'\\\nb'", end="", sep="")

            value = image_bitstring[i : i + 8]
            color = int(value, 2)
            print(f"\\x{color:02x}", sep="", end="")

        print("'")

        return True

    except Exception as e:
        print(f"Error processing image: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        prog="imgtobitmap",
        description="Convert image file to python module for use with bitmap method.",
    )

    parser.add_argument("image_file", help="Name of file containing image to convert")

    parser.add_argument(
        "bits_per_pixel",
        type=int,
        choices=range(1, 9),
        default=1,
        metavar="bits_per_pixel",
        help="The number of bits to use per pixel (1..8)",
    )

    args = parser.parse_args()
    bits = args.bits_per_pixel
    colors = 1 << bits

    return 0 if convert_image_to_bitmap(args.image_file, colors) else 1


if __name__ == "__main__":
    sys.exit(main())
