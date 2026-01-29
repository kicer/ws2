#!/usr/bin/env python3
"""
图像转JPG二进制文件工具

将图像文件转换为ST7789显示所需的JPG二进制格式(.jbin文件)

使用方法:
    python image2jpgbin.py input.jpg output.jbin
    python image2jpgbin.py input.png output.jbin

支持格式:
    - JPEG (.jpg, .jpeg)
    - PNG (.png)
    - BMP (.bmp)

注意:
    对于PNG/BMP等非JPEG格式，会先转换为JPEG格式，quality参数控制最终JPEG质量
"""

import argparse
import os
import struct
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("错误: 需要安装Pillow库")
    print("请运行: pip install Pillow")
    sys.exit(1)


def convert_image_to_jbin(input_path, output_path, quality=85):
    """
    将图像文件转换为JBIN格式

    Args:
        input_path: 输入图像文件路径
        output_path: 输出JBIN文件路径
        quality: JPEG质量(1-100)

    Returns:
        True: 转换成功
        False: 转换失败
    """
    try:
        # 打开图像文件
        with Image.open(input_path) as img:
            # 转换为RGB模式
            if img.mode != "RGB":
                img = img.convert("RGB")

            # 获取图像尺寸
            width, height = img.size

            # 创建临时JPEG文件（内存中）
            import io

            jpeg_buffer = io.BytesIO()
            img.save(jpeg_buffer, format="JPEG", quality=quality, optimize=True)
            jpeg_data = jpeg_buffer.getvalue()

            # 打开输出文件
            with open(output_path, "wb") as f:
                # 写入头信息（宽度和高度，小端序）
                f.write(struct.pack("<HH", width, height))

                # 写入JPEG数据
                f.write(jpeg_data)

            print(f"成功转换: {input_path} ({width}x{height}) -> {output_path}")
            print(f"  输出文件大小: {os.path.getsize(output_path)} 字节")

            return True

    except Exception as e:
        print(f"转换失败: {e}")
        return False


def convert_image_to_jbin(input_path, output_path, quality=85):
    """
    将图像文件转换为JBIN格式

    Args:
        input_path: 输入图像文件路径
        output_path: 输出JBIN文件路径
        quality: JPEG质量(1-100)
            - 对于JPEG文件: 重新压缩时使用此质量
            - 对于PNG/BMP文件: 转换为JPEG时使用此质量

    Returns:
        True: 转换成功
        False: 转换失败
    """
    try:
        # 打开图像文件
        with Image.open(input_path) as img:
            # 转换为RGB模式
            if img.mode != "RGB":
                img = img.convert("RGB")

            # 获取图像尺寸
            width, height = img.size

            # 创建临时JPEG文件（内存中）
            import io

            jpeg_buffer = io.BytesIO()
            img.save(jpeg_buffer, format="JPEG", quality=quality, optimize=True)
            jpeg_data = jpeg_buffer.getvalue()

            # 打开输出文件
            with open(output_path, "wb") as f:
                # 写入头信息（宽度和高度，小端序）
                f.write(struct.pack("<HH", width, height))

                # 写入JPEG数据
                f.write(jpeg_data)

            print(f"成功转换: {input_path} ({width}x{height}) -> {output_path}")
            print(f"  输出文件大小: {os.path.getsize(output_path)} 字节")
            print(f"  JPEG质量: {quality}")

            return True

    except Exception as e:
        print(f"转换失败: {e}")
        return False


def main():
    parse = argparse.ArgumentParser(
        description="将图像文件转换为ST7789显示所需的JPG二进制格式(.jbin文件)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单文件转换
  python image2jpgbin.py input.jpg output.jbin

  # 转换非JPEG文件(PNG/BMP)
  python image2jpgbin.py input.png output.jbin

  # 指定JPEG质量
  python image2jpgbin.py --quality 95 input.jpg output.jbin

输出格式(.jbin):
  偏移  大小  描述
  0x00  2    图像宽度(小端序)
  0x02  2    图像高度(小端序)
  0x04  N    JPEG图像数据

注意:
  对于PNG/BMP等非JPEG格式，会先转换为JPEG格式，quality参数控制转换质量
        """,
    )

    parse.add_argument("input", help="输入图像文件路径")
    parse.add_argument("output", help="输出JBIN文件路径")

    parse.add_argument(
        "--quality",
        "-q",
        type=int,
        default=85,
        choices=range(1, 101),
        help="JPEG压缩质量(1-100),默认85",
    )

    args = parse.parse_args()

    # 检查输入文件是否存在
    if not os.path.isfile(args.input):
        print(f"错误: 输入文件不存在: {args.input}")
        return 1

    # 创建输出目录（如果需要）
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # 转换文件
    if convert_image_to_jbin(args.input, args.output, args.quality):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
