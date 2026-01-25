#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
image2bin.py - Convert image bitmap modules to binary streaming format

This script converts Python image modules (created by imgtobitmap.py) to
binary files that can be streamed from the file system. This is especially
useful for large images or animations on memory-constrained devices.

Usage:
    python image2bin.py <image_module> <output_binary>

Example:
    python image2bin.py logo.py logo.bin
"""

import importlib.util
import os
import struct
import sys


def read_image_module(module_path):
    """Load and extract image data from a Python image module"""
    try:
        # Load the module
        spec = importlib.util.spec_from_file_location("image_module", module_path)
        image_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(image_module)

        # Extract image metadata and data
        image_data = {
            "width": image_module.WIDTH,
            "height": image_module.HEIGHT,
            "colors": image_module.COLORS,
            "bpp": image_module.BPP,
            "palette": getattr(image_module, "PALETTE", []),
            "bitmap": bytes(image_module._bitmap),
        }

        return image_data
    except Exception as e:
        print(f"Error loading image module: {e}")
        return None


def write_binary_file(image_data, output_path):
    """Write image data to a binary file with a specific format"""
    try:
        with open(output_path, "wb") as f:
            # Write header information
            f.write(b"IMG ")  # Magic number ("IMG " with trailing space)
            f.write(struct.pack("H", image_data["width"]))  # Image width
            f.write(struct.pack("H", image_data["height"]))  # Image height
            f.write(struct.pack("B", image_data["colors"]))  # Number of colors
            f.write(struct.pack("B", image_data["bpp"]))  # Bits per pixel

            # Write palette
            if image_data["palette"]:
                f.write(struct.pack("B", len(image_data["palette"])))  # Palette length
                for color in image_data["palette"]:
                    f.write(struct.pack("H", color))  # RGB565 color value
            else:
                f.write(struct.pack("B", 0))  # Zero palette length

            # Write bitmap data
            f.write(struct.pack("I", len(image_data["bitmap"])))  # Bitmap length
            f.write(image_data["bitmap"])

        print(f"Successfully wrote image data to {output_path}")
        print(f"File size: {os.path.getsize(output_path)} bytes")
        return True
    except Exception as e:
        print(f"Error writing binary file: {e}")
        return False


def create_info_file(image_data, output_path):
    """Create a text file with image information"""
    info_path = output_path.replace(".bin", ".info")
    try:
        with open(info_path, "w") as f:
            f.write(f"Image Information\n")
            f.write(f"================\n")
            f.write(f"Width: {image_data['width']} pixels\n")
            f.write(f"Height: {image_data['height']} pixels\n")
            f.write(f"Colors: {image_data['colors']}\n")
            f.write(f"BPP: {image_data['bpp']}\n")
            if image_data["palette"]:
                f.write(f"Palette: {len(image_data['palette'])} colors\n")
            else:
                f.write(f"Palette: None\n")
            f.write(f"Bitmap Size: {len(image_data['bitmap'])} bytes\n")
            f.write(
                f"Total File Size: {os.path.getsize(output_path.replace('.info', '.bin'))} bytes\n"
            )

        print(f"Image information written to {info_path}")
        return True
    except Exception as e:
        print(f"Error writing info file: {e}")
        return False


def main():
    if len(sys.argv) != 3:
        print("Usage: python image2bin.py <image_module> <output_binary>")
        print("Example: python image2bin.py logo.py logo.bin")
        print(
            "\nThis converts Python image modules (from imgtobitmap.py) to streaming format."
        )
        return 1

    image_module_path = sys.argv[1]
    output_path = sys.argv[2]

    # Check if input file exists
    if not os.path.exists(image_module_path):
        print(f"Error: Image module not found at {image_module_path}")
        return 1

    # Load image data
    image_data = read_image_module(image_module_path)
    if image_data is None:
        return 1

    # Write binary file
    if not write_binary_file(image_data, output_path):
        return 1

    # Create info file
    if not create_info_file(image_data, output_path):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
