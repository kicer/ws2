#!/usr/bin/env python3
"""
Convert pyfont files to binary font formats (BFont, HFont, or RFont).

This script automatically detects the font type based on the input file characteristics
and converts it to the appropriate binary format:
- BFont (BitmapFont): For bitmap fonts with character maps and offsets
- HFont (HersheyFont): For vector fonts with stroke data
- RFont (RomFont): For fixed-width bitmap fonts with sequential character ranges

Usage: pyfont_to_bin.py <input_pyfont_file> [output_file_or_directory]

output_file_or_directory can be:
- A file path to specify the output file name and location
- A directory path to place the output file in that directory with auto-generated name

Binary Formats:

1. BFont (BitmapFont) format:
   - 3 bytes: Magic number (0x42 0x46 0x54 = "BFT")
   - 1 byte: Version (0x01T
   - 1 byte: max_Width
   - 1 byte: HEIGHT of the font
   - 1 byte: bpp
   - 1 byte: OFFSET_WIDTH (number of bytes for each offset)
   - 2 bytes: Character count (big endian)
   - N*2 bytes: Character map (character count bytes, 2 bytes per Unicode char)
   - N*(1+OFFSET_WIDTH) bytes: WIDTH+Offset data
   - M bytes: Bitmap data

2. HFont (HersheyFont) format:
   - 3 bytes: Magic number (0x48 0x46 0x54 = "HFT")
   - 1 byte: Version (0x01)
   - 1 byte: WIDTH of the font
   - 1 byte: HEIGHT of the font
   - 1 byte: FIRST character code
   - 1 byte: LAST character code
   - 2 bytes: Maximum size of any character in bytes (big endian)
   - N bytes: Index data
   - M bytes: Font data (stroke vectors)

3. RFont (RomFont) format:
   - 8 bytes: RFont header
     - 3 bytes: Magic number (0x52 0x46 0x54 = "RFT")
     - 1 byte: Version (0x01)
     - 1 byte: WIDTH of the font
     - 1 byte: HEIGHT of the font
     - 1 byte: FIRST character code
     - 1 byte: LAST character code
   - N bytes: Character bitmap data
"""

import argparse
import os
import struct
import sys

# Magic numbers for different font formats
MAGIC_BFONT = b"BFT"  # Bitmap Font Binary
MAGIC_HFONT = b"HFT"  # Hershey Font Binary
MAGIC_RFONT = b"RFT"  # Rom Font Binary
VERSION = 0x01


def detect_font_type(namespace, input_file):
    """
    Detect the type of font based on file characteristics.
    Returns one of: 'bfont', 'hfont', 'rfont'
    """
    # Check for bitmap font format (proverbs/clock style)
    if (
        "MAP" in namespace
        and "WIDTHS" in namespace
        and "MAX_WIDTH" in namespace
        and "OFFSETS" in namespace
        and "BITMAPS" in namespace
    ):
        return "bfont"

    # Check for standard bitmap font format
    if (
        "WIDTH" in namespace
        and "HEIGHT" in namespace
        and "FIRST" in namespace
        and "LAST" in namespace
        and "FONT" in namespace
    ):
        # Check if it has sequential bitmap data (_FONT)
        if "INDEX" in namespace:
            return "hfont"
        else:
            return "rfont"

    # Unknown format
    return None


def convert_to_bfont(namespace, input_file, output_file=None):
    """
    Convert pyfont to BFont format (bitmap font with variable width characters)
    """
    # Extract font parameters
    char_map_str = namespace.get("MAP")
    height = namespace.get("HEIGHT")
    max_width = namespace.get("MAX_WIDTH")
    width = max_width if max_width else height
    bpp = namespace.get("BPP", 1)  # Default to 1 BPP if not specified

    widths = namespace.get("_WIDTHS")
    offset_width = namespace.get("OFFSET_WIDTH", 2)  # Default to 2 bytes
    offsets = namespace.get("_OFFSETS")
    bitmaps = namespace.get("_BITMAPS")

    if None in (char_map_str, height, max_width, offsets, bitmaps):
        return None

    # Convert character map to bytes - use UTF-8 encoding for Unicode characters
    # Since we need to store Unicode code points, we'll use 2 bytes per character
    char_map = b""
    for c in char_map_str:
        # Pack each Unicode code point as 2 bytes (big endian)
        char_map += struct.pack(">H", ord(c))
    char_count = len(char_map_str)

    # Handle memoryview objects
    if offsets and hasattr(offsets, "tobytes"):
        offsets = offsets.tobytes()
    if bitmaps and hasattr(bitmaps, "tobytes"):
        bitmaps = bitmaps.tobytes()
    if widths and hasattr(widths, "tobytes"):
        widths = widths.tobytes()

    # Calculate the actual max width from widths data if available
    if widths and len(widths) > 0:
        actual_max_width = max(widths)
    else:
        actual_max_width = width

    font_info = {
        "width": actual_max_width,  # Use actual max width for the header
        "height": height,
        "char_count": char_count,
        "char_map": char_map,
        "offset_width": offset_width,
        "offsets": offsets,
        "font_data": bitmaps,
        "widths": widths,  # Store WIDTH data
        "bpp": bpp,  # Store BPP value
    }

    # Update output filename if needed
    if output_file and os.path.isdir(output_file):
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_dir = output_file
        output_name = f"{base_name}-{width}x{height}.bfont"
        output_file = os.path.join(output_dir, output_name)

    # Write BFont file
    write_bfont_file(font_info, output_file)

    # Calculate merged data size
    merged_data_size = font_info["char_count"] * (1 + font_info["offset_width"])

    # Print font information
    print(f"Bitmap Font Detected")
    print(f"  Source: {input_file}")
    print(f"  Output format: BFont ({output_file})")
    print(f"  Character count: {font_info['char_count']}")
    print(f"  Font dimensions: {font_info['width']}x{font_info['height']}")
    print(f"  BPP: {bpp}")
    print(f"  Font data size: {len(font_info['font_data'])} bytes")
    print(f"  Width+Offset data size: {merged_data_size} bytes")
    print(f"  Offset width: {font_info['offset_width']} bytes")

    return True


def convert_to_hfont(namespace, input_file, output_file=None):
    """
    Convert pyfont to HFont format (Hershey vector font)
    """
    # Extract font parameters
    first = namespace.get("FIRST")
    last = namespace.get("LAST")
    width = namespace.get("WIDTH", 0)
    height = namespace.get("HEIGHT", 0)

    # Check for Hershey-specific data
    indices = namespace.get("_index")
    font_data = namespace.get("_font")

    # Handle memoryview objects
    if indices and hasattr(indices, "tobytes"):
        indices = indices.tobytes()
    if font_data and hasattr(font_data, "tobytes"):
        font_data = font_data.tobytes()

    # Check if we have the required data
    if indices is None or font_data is None:
        print("Error: HFont requires _index and _font data")
        return False

    # Calculate character count
    char_count = last - first + 1 if first is not None and last is not None else 0

    # Calculate maximum character size
    max_char_size = 0
    if indices and font_data:
        # Parse the index data to get offsets (2 bytes per entry)
        offsets = []
        for i in range(0, len(indices), 2):
            offset = indices[i] + (indices[i + 1] << 8)
            offsets.append(offset)

        # Add the end offset
        offsets.append(len(font_data))

        # Calculate the size of each character
        for i in range(len(offsets) - 1):
            size = offsets[i + 1] - offsets[i]
            if size > max_char_size:
                max_char_size = size

    # Update output filename if needed
    if output_file and os.path.isdir(output_file):
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_dir = output_file
        output_name = f"{base_name}-{width}x{height}.hfont"
        output_file = os.path.join(output_dir, output_name)

    # Write HFont file
    with open(output_file, "wb") as f:
        # Write magic number
        f.write(MAGIC_HFONT)

        # Write version
        f.write(bytes([VERSION]))

        # Write font metadata (each as a single byte)
        f.write(bytes([width if width < 256 else 255]))  # 1 byte: WIDTH
        f.write(bytes([height if height < 256 else 255]))  # 1 byte: HEIGHT
        f.write(
            bytes([first if first is not None else 0])
        )  # 1 byte: FIRST character code
        f.write(bytes([last if last is not None else 0]))  # 1 byte: LAST character code

        # Write maximum character size (2 bytes, big endian)
        f.write(struct.pack(">H", max_char_size))

        # Write index data
        if indices:
            f.write(indices)

        # Write font data
        if font_data:
            f.write(font_data)

    # Print font information
    print(f"Vector Font (Hershey Style) Detected")
    print(f"  Source: {input_file}")
    print(f"  Output format: HFont ({output_file})")
    print(f"  Character range: {first}-{last} ({char_count} chars)")
    print(f"  Font dimensions: {width}x{height}")
    print(f"  Font data size: {len(font_data) if font_data else 0} bytes")
    print(f"  Index data size: {len(indices) if indices else 0} bytes")
    print(f"  Maximum character size: {max_char_size} bytes")

    return True


def convert_to_rfont(namespace, input_file, output_file=None):
    """
    Convert pyfont to RFont format (RomFont, fixed-width bitmap font)
    """
    # Extract font parameters
    first = namespace.get("FIRST")
    last = namespace.get("LAST")
    width = namespace.get("WIDTH")
    height = namespace.get("HEIGHT")
    font_data = namespace.get("_FONT")

    # Handle case where font_data is a memoryview
    if font_data is not None and hasattr(font_data, "tobytes"):
        font_data = font_data.tobytes()

    if None in (first, last, width, height, font_data):
        return False

    # Calculate character count
    char_count = last - first + 1

    # Calculate bytes per character
    bytes_per_line = (width + 7) // 8
    bytes_per_char = bytes_per_line * height

    # Update output filename if needed
    if output_file and os.path.isdir(output_file):
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_dir = output_file
        output_name = f"{base_name}-{width}x{height}.rfont"
        output_file = os.path.join(output_dir, output_name)

    # Write RFont file
    with open(output_file, "wb") as f:
        # Write header
        f.write(MAGIC_RFONT)  # 3 bytes: Magic number
        f.write(bytes([VERSION]))  # 1 byte: Version

        # Verify that all values fit in a single byte
        if max(first, last, width, height) > 255:
            print(f"Warning: Font metadata values > 255 will be truncated to 255")
            first = min(first, 255)
            last = min(last, 255)
            width = min(width, 255)
            height = min(height, 255)

        f.write(bytes([width]))  # 1 byte: WIDTH
        f.write(bytes([height]))  # 1 byte: HEIGHT
        f.write(bytes([first]))  # 1 byte: FIRST character code
        f.write(bytes([last]))  # 1 byte: LAST character code

        # Write font data
        f.write(font_data)

    # Print font information
    print(f"Fixed-Width Bitmap Font Detected")
    print(f"  Source: {input_file}")
    print(f"  Output format: RFont ({output_file})")
    print(f"  Character range: {first}-{last} ({char_count} chars)")
    print(f"  Font dimensions: {width}x{height}")
    print(f"  Fixed character size: {bytes_per_char} bytes")
    print(f"  Total font data size: {len(font_data)} bytes")

    return True


def write_bfont_file(font_info, output_file):
    """Write the BFont binary file"""
    # Make sure the output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_file, "wb") as f:
        # Write magic number
        f.write(MAGIC_BFONT)

        # Write version
        f.write(bytes([VERSION]))

        # Write max_Width
        f.write(bytes([font_info["width"]]))  # 1 byte: max_Width

        # Write HEIGHT of the font
        f.write(bytes([font_info["height"]]))  # 1 byte: HEIGHT

        # Write bpp
        f.write(bytes([font_info.get("bpp", 1)]))  # 1 byte: bpp

        # Write OFFSET_WIDTH (1 byte)
        f.write(bytes([font_info["offset_width"]]))

        # Write character count (2 bytes, big endian)
        f.write(struct.pack(">H", font_info["char_count"]))

        # Write character map (as packed Unicode code points)
        f.write(font_info["char_map"])

        # Write merged WIDTH+Offset data
        widths = font_info.get("widths")
        offsets = font_info["offsets"]
        offset_width = font_info["offset_width"]

        # If no widths data provided, use max_width for each character
        if not widths:
            widths = bytes([font_info["width"]] * font_info["char_count"])

        # Merge width and offset data for each character
        # Each character has 1 byte width followed by offset_width bytes offset
        for i in range(font_info["char_count"]):
            # Write width (1 byte)
            f.write(bytes([widths[i]]))

            # Write offset (offset_width bytes) directly from the offsets byte array
            offset_start = i * offset_width
            offset_end = offset_start + offset_width
            f.write(offsets[offset_start:offset_end])

        # Write bitmap data
        f.write(font_info["font_data"])

    return True


def convert_to_binary(input_file, output_file=None):
    """Convert a pyfont file to binary format, auto-detecting the format"""
    try:
        # Check if output_file is a directory
        if output_file and os.path.isdir(output_file):
            output_dir = output_file
            output_file = None
        else:
            output_dir = None

        # Generate default output file name if not provided or directory specified
        if output_file is None:
            base_name = os.path.splitext(os.path.basename(input_file))[0]

            if output_dir:
                output_path = output_dir
            else:
                output_path = os.path.dirname(input_file)

            output_file = output_path

        # Parse the pyfont file using exec()
        namespace = {}
        with open(input_file, "r") as f:
            exec(f.read(), namespace)

        # Detect the font type
        font_type = detect_font_type(namespace, input_file)

        '''
        # Generate default output file name if not provided or directory specified
        if output_file is None:
            base_name = os.path.splitext(os.path.basename(input_file))[0]

            if output_dir:
                output_path = output_dir
            else:
                output_path = os.path.dirname(input_file)

            # Create output file name based on detected format
            if font_type == "bfont":
                # Get width and height for filename
                if "MAX_WIDTH" in namespace and "HEIGHT" in namespace:
                    width = namespace["MAX_WIDTH"]
                    height = namespace["HEIGHT"]
                else:
                    width = namespace.get("WIDTH", 0)
                    height = namespace.get("HEIGHT", 0)
                output_name = f"{base_name}-{width}x{height}.bfont"
            elif font_type == "hfont":
                width = namespace.get("WIDTH", 0)
                height = namespace.get("HEIGHT", 0)
                output_name = f"{base_name}-{width}x{height}.hfont"
            elif font_type == "rfont":
                width = namespace.get("WIDTH", 0)
                height = namespace.get("HEIGHT", 0)
                output_name = f"{base_name}-{width}x{height}.rfont"
            else:
                output_name = f"{base_name}.bin"

            output_file = os.path.join(output_path, output_name)
        '''

        # Convert based on the detected format
        if font_type == "bfont":
            return convert_to_bfont(namespace, input_file, output_file)
        elif font_type == "hfont":
            return convert_to_hfont(namespace, input_file, output_file)
        elif font_type == "rfont":
            return convert_to_rfont(namespace, input_file, output_file)
        else:
            print(f"Error: Unable to detect font type for {input_file}")
            print(
                "Available variables:",
                [k for k in namespace.keys() if not k.startswith("__")],
            )
            return False

    except Exception as e:
        print(f"Error converting {input_file}: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Convert pyfont files to binary font formats (BFont, HFont, or RFont)"
    )
    parser.add_argument("input_file", help="Input pyfont file path")
    parser.add_argument(
        "output", nargs="?", help="Output file or directory path (optional)"
    )

    args = parser.parse_args()

    if not convert_to_binary(args.input_file, args.output):
        sys.exit(1)


if __name__ == "__main__":
    main()
