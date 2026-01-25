#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
font2bin.py - Convert font modules to binary files for streaming

This script converts Python font modules (like those created by font2bitmap)
to binary files that can be streamed from the file system. This significantly
reduces RAM usage on memory-constrained devices like ESP8266.

Usage:
    python font2bin.py <font_module> <output_binary>

Example:
    python font2bin.py proverbs_font font_data.font
"""

import importlib.util
import os
import struct
import sys
from pathlib import Path


def read_font_module(module_path):
    """Load and extract font data from a Python font module"""
    try:
        # Load the module
        spec = importlib.util.spec_from_file_location("font_module", module_path)
        font_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(font_module)

        # Extract font metadata and data
        font_data = {
            "map": font_module.MAP,
            "bpp": getattr(font_module, "BPP", 1),
            "height": font_module.HEIGHT,
            "max_width": font_module.MAX_WIDTH,
            "widths": bytes(font_module._WIDTHS),
            "offsets": bytes(font_module._OFFSETS),
            "bitmaps": bytes(font_module._BITMAPS),
            "offset_width": getattr(font_module, "OFFSET_WIDTH", 2),
        }

        return font_data
    except Exception as e:
        print(f"Error loading font module: {e}")
        return None


def write_binary_file(font_data, output_path):
    """Write font data to a binary file with a specific format"""
    try:
        with open(output_path, "wb") as f:
            # Write header information
            f.write(b"FONT")  # Magic number
            f.write(struct.pack("B", font_data["bpp"]))  # Bits per pixel
            f.write(struct.pack("H", font_data["height"]))  # Font height
            f.write(struct.pack("H", font_data["max_width"]))  # Maximum width
            f.write(
                struct.pack("B", font_data["offset_width"])
            )  # Offset width in bytes

            # Write character map
            map_bytes = font_data["map"].encode("utf-8")
            f.write(struct.pack("H", len(map_bytes)))  # Map length
            f.write(map_bytes)

            # Write widths
            f.write(struct.pack("H", len(font_data["widths"])))  # Widths length
            f.write(font_data["widths"])

            # Write offsets
            f.write(struct.pack("I", len(font_data["offsets"])))  # Offsets length
            f.write(font_data["offsets"])

            # Write bitmaps
            f.write(struct.pack("I", len(font_data["bitmaps"])))  # Bitmaps length
            f.write(font_data["bitmaps"])

        print(f"Successfully wrote font data to {output_path}")
        print(f"File size: {os.path.getsize(output_path)} bytes")
        return True
    except Exception as e:
        print(f"Error writing binary file: {e}")
        return False


def create_info_file(font_data, output_path):
    """Create a text file with font information"""
    # Extract the base filename without extension
    base_name = os.path.splitext(os.path.basename(output_path))[0]
    # Get the py directory path (assuming output_path is in bin directory)
    bin_dir = os.path.dirname(output_path)
    py_dir = os.path.join(os.path.dirname(bin_dir), "py")
    info_path = os.path.join(py_dir, base_name + ".info")

    try:
        with open(info_path, "w") as f:
            f.write(f"Font Information\n")
            f.write(f"==============\n")
            f.write(f"BPP: {font_data['bpp']}\n")
            f.write(f"Height: {font_data['height']}\n")
            f.write(f"Max Width: {font_data['max_width']}\n")
            f.write(f"Offset Width: {font_data['offset_width']}\n")
            f.write(f"Character Count: {len(font_data['map'])}\n")
            f.write(f"Widths Size: {len(font_data['widths'])} bytes\n")
            f.write(f"Offsets Size: {len(font_data['offsets'])} bytes\n")
            f.write(f"Bitmaps Size: {len(font_data['bitmaps'])} bytes\n")
            f.write(
                f"Total Size: {len(font_data['widths']) + len(font_data['offsets']) + len(font_data['bitmaps'])} bytes\n"
            )

        print(f"Font information written to {info_path}")
        return True
    except Exception as e:
        print(f"Error writing info file: {e}")
        return False


def main():
    if len(sys.argv) != 3:
        print("Usage: python font2bin.py <font_module> <output_binary>")
        print("Example: python font2bin.py proverbs_font font_data.font")
        return 1

    font_module_path = sys.argv[1]
    output_path = sys.argv[2]

    # Check if input file exists
    if not os.path.exists(font_module_path):
        print(f"Error: Font module not found at {font_module_path}")
        return 1

    # Load font data
    font_data = read_font_module(font_module_path)
    if font_data is None:
        return 1

    # Write binary file
    if not write_binary_file(font_data, output_path):
        return 1

    # Create info file
    if not create_info_file(font_data, output_path):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
