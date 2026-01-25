# ST7789 MPY 流式加载指南

本文档详细说明了如何在 ESP8266/ESP32 等 MicroPython 设备上使用 st7789_mpy 库以流式加载方式高效显示图片和文字，避免内存不足的问题。

## 目录

1. [流式加载概述](#流式加载概述)
2. [字体流式加载](#字体流式加载)
3. [图片流式加载](#图片流式加载)
4. [转换工具使用](#转换工具使用)
5. [实际应用示例](#实际应用示例)
6. [常见问题解答](#常见问题解答)

## 流式加载概述

### 为什么需要流式加载？

在内存受限的设备（如 ESP8266）上，传统方式加载大型资源会导致以下问题：
- **内存不足**：大型字体或图片会占用大量 RAM
- **启动缓慢**：加载大型资源需要较长时间
- **资源浪费**：一次性加载全部数据，即使当前只使用一小部分

**流式加载解决方案**：
- 将资源数据存储在文件系统中
- 只在需要时读取部分数据
- 释放不需要的数据内存
- 大幅减少内存占用（可节省 90% 以上内存）

### st7789_mpy 流式支持

st7789_mpy 库提供了以下流式加载支持：
- `StreamingFont` 类：流式加载字体
- `StreamingImage` 类：流式加载图片
- `StreamingAnimation` 类：流式加载动画帧

## 字体流式加载

### 字体二进制格式

流式字体二进制文件格式如下：

```
字节偏移  内容                  说明
0-3      Magic Number          4字节 "FONT"
4        BPP                   每像素位数
5-6      Height                字体高度 (uint16)
7-8      Max Width             最大字符宽度 (uint16)
9        Offset Width          偏移量字节数
10-11    Map Length            字符映射长度 (uint16)
12-...   Character Map         字符映射 (UTF-8)
...      Widths Section        字符宽度数据
...      Offsets Section       位图偏移量
...      Bitmaps Section       位图数据
```

### 使用方法

1. **加载流式字体**：
```python
import st7789
import st7789.streaming_font_mpy

# 初始化显示器，使用小缓冲区
display = st7789.ST7789(
    spi,
    240, 320,
    reset=PIN_RESET,
    dc=PIN_DC,
    cs=PIN_CS,
    backlight=PIN_BL,
    buffer_size=512  # 使用小缓冲区
)

# 加载流式字体
font = st7789.streaming_font_mpy.StreamingFont("font.font")

# 使用与普通字体相同的方式显示文字
display.write(font, "你好，世界！", 10, 50, st7789.WHITE)
```

2. **关闭字体**（释放文件句柄）：
```python
font.close()
```

### 字体流式加载优势

- **内存占用小**：只加载当前显示所需的字符数据
- **支持大型字体**：可以处理包含 CJK 字符的大型字体文件
- **兼容性好**：与 st7789.write() 方法完全兼容
- **按需加载**：只加载实际使用的字符

## 图片流式加载

### 图片二进制格式

流式图片二进制文件格式如下：

```
字节偏移  内容                  说明
0-3      Magic Number          4字节 "IMG "
4-5      Width                 图片宽度 (uint16)
6-7      Height                图片高度 (uint16)
8        Colors                颜色数量
9        BPP                   每像素位数
10       Palette Length        调色板长度
11-...   RGB565 Palette        RGB565调色板值
...      Bitmap Data           位图数据
```

### 使用方法

1. **加载流式图片**：
```python
import st7789
import st7789.streaming_image

# 初始化显示器
display = st7789.ST7789(
    spi,
    240, 320,
    reset=PIN_RESET,
    dc=PIN_DC,
    cs=PIN_CS,
    backlight=PIN_BL,
    buffer_size=1024
)

# 加载流式图片
image = st7789.streaming_image.StreamingImage("image.img")

# 显示图片
display.bitmap(image, 0, 0, 0)
```

2. **动画支持**：
```python
# 初始化动画
animation = st7789.streaming_image.StreamingAnimation("sprite", total_frames=8)

# 显示动画帧
frame = animation.get_frame(0)  # 获取第0帧
display.bitmap(frame, x, y, 0)

# 播放下一个帧
frame = animation.next_frame()
display.bitmap(frame, x, y, 0)

# 清理资源
animation.cleanup()
```

### 图片流式加载优势

- **内存占用小**：只加载当前显示的部分图片
- **支持大尺寸图片**：可以处理比显示器更大的图片
- **动画支持**：高效处理多帧动画
- **按需加载**：只加载需要显示的部分

## 转换工具使用

### 字体转换流程

1. **将 TrueType 字体转换为 Python 模块**：
```bash
python font2bitmap.py 字体文件.oft 字体大小 -s "要包含的字符"
# 示例
python font2bitmap.py NotoSansSC-Regular.otf 20 -s "你好世界0123456789"
```

2. **将 Python 字体模块转换为二进制文件**：
```bash
python font2bin.py 字体模块.py 输出文件.font
# 示例
python font2bin.py noto_sans_sc_20.py ch_font.font
```

### 图片转换流程

1. **将图片转换为 Python 模块**：
```bash
python image2bitmap.py 图片文件.图片格式 颜色深度
# 示例
python image2bitmap.py python-logo.png 4
```

2. **将 Python 图片模块转换为二进制文件**：
```bash
python image2bin.py 图片模块.py 输出文件.img
# 示例
python image2bin.py python_logo.py logo.img
```

### 自动转换脚本

我们提供了一个便捷的脚本，可以一键完成字体和图片的转换：

```bash
# 使用提供的转换脚本
./convert_assets.sh
```

脚本内容见 [convert_assets.sh](#convert_assets.sh) 部分。

## 实际应用示例

### 示例1：显示中英文混合文本

```python
import st7789
import st7789.streaming_font_mpy
import machine

# 初始化SPI
spi = machine.SPI(1, baudrate=40000000, sck=machine.Pin(14), mosi=machine.Pin(13))

# 初始化显示器
display = st7789.ST7789(
    spi,
    240, 320,
    reset=machine.Pin(2),
    dc=machine.Pin(4),
    cs=machine.Pin(5),
    backlight=machine.Pin(15),
    buffer_size=512
)

# 加载中文字体
font = st7789.streaming_font_mpy.StreamingFont("ch_font.font")

# 显示文本
display.write(font, "温度: 25.3°C", 10, 10, st7789.WHITE)
display.write(font, "湿度: 68.5%", 10, 40, st7789.WHITE)
display.write(font, "空气质量: 良", 10, 70, st7789.GREEN)

# 释放资源
font.close()
```

### 示例2：显示图片和动画

```python
import st7789
import st7789.streaming_image
import machine
import time

# 初始化SPI和显示器（同上）
...

# 加载Logo图片
logo = st7789.streaming_image.StreamingImage("logo.img")
display.bitmap(logo, 60, 20, 0)
logo.close()

# 加载天气动画
weather_anim = st7789.streaming_image.StreamingAnimation("weather", 8)

# 播放动画
for i in range(80):  # 循环播放10次
    frame = weather_anim.get_frame(i % 8)
    display.bitmap(frame, 80, 100, 0)
    time.sleep_ms(100)

# 清理资源
weather_anim.cleanup()
```

### 示例3：天气站应用

```python
import st7789
import st7789.streaming_font_mpy
import st7789.streaming_image
import machine
import time
import network
import urequests

# 网络配置（根据实际情况修改）
WIFI_SSID = "your_wifi_ssid"
WIFI_PASSWORD = "your_wifi_password"

# 初始化显示器
...

# 加载字体
ch_font = st7789.streaming_font_mpy.StreamingFont("ch_font.font")
en_font = st7789.streaming_font_mpy.StreamingFont("en_font.font")

# 加载天气图标
weather_icons = st7789.streaming_image.StreamingAnimation("weather_icon", 10)

def connect_wifi():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('连接到WiFi...')
        sta_if.active(True)
        sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
        while not sta_if.isconnected():
            pass
    print('网络配置:', sta_if.ifconfig())

def get_weather_data():
    # 示例API调用，请替换为实际的API
    try:
        response = urequests.get("http://api.example.com/weather")
        data = response.json()
        response.close()
        return data
    except:
        return None

def update_display(weather_data):
    # 清屏
    display.fill(st7789.BLACK)
    
    # 显示日期时间
    current_time = time.localtime()
    date_str = f"{current_time[0]}年{current_time[1]}月{current_time[2]}日"
    time_str = f"{current_time[3]:02d}:{current_time[4]:02d}"
    
    display.write(ch_font, date_str, 10, 10, st7789.WHITE)
    display.write(en_font, time_str, 10, 40, st7789.WHITE)
    
    # 显示温度
    if weather_data:
        temp = weather_data.get('temperature', 'N/A')
        humidity = weather_data.get('humidity', 'N/A')
        condition = weather_data.get('condition', '未知')
        icon_index = weather_data.get('icon_index', 0)
        
        display.write(ch_font, f"温度: {temp}°C", 10, 80, st7789.WHITE)
        display.write(ch_font, f"湿度: {humidity}%", 10, 110, st7789.WHITE)
        display.write(ch_font, f"天气: {condition}", 10, 140, st7789.WHITE)
        
        # 显示天气图标
        icon = weather_icons.get_frame(icon_index)
        display.bitmap(icon, 150, 80, 0)
    
    display.show()

def main():
    # 连接WiFi
    connect_wifi()
    
    # 主循环
    while True:
        # 获取天气数据
        weather_data = get_weather_data()
        
        # 更新显示
        update_display(weather_data)
        
        # 每小时更新一次
        time.sleep(3600)

try:
    main()
finally:
    # 清理资源
    ch_font.close()
    en_font.close()
    weather_icons.cleanup()
```

## 常见问题解答

### Q1: 流式加载比传统方式慢吗？

**A**: 流式加载主要影响的是首次访问字符/图片时的加载时间，后续访问会有缓存。对于大型资源，流式加载总体上更高效，因为避免了一次性加载全部数据的延迟。

### Q2: 如何选择适当的缓冲区大小？

**A**: 缓冲区大小取决于显示需求和可用内存：
- 最小：256-512字节（可显示基本文本）
- 推荐：1024-2048字节（平衡性能和内存）
- 最大：4096-8192字节（适合复杂图像）

### Q3: 可以同时使用流式和传统资源吗？

**A**: 是的，你可以在同一应用中混合使用流式和传统资源。对于大型字体和图片使用流式加载，对于小资源使用传统方式。

### Q4: 如何处理文件不存在的情况？

**A**: 使用 try-except 块捕获异常：
```python
try:
    font = st7789.streaming_font_mpy.StreamingFont("font.font")
except OSError:
    print("字体文件不存在，使用备用字体")
    font = st7789.streaming_font_mpy.StreamingFont("fallback_font.font")
```

### Q5: 流式加载支持哪些文件系统？

**A**: st7789_mpy 流式加载支持 MicroPython 支持的所有文件系统，包括：
- 内置的 Flash 文件系统
- SD 卡（通过 `sdcard` 模块）
- SPIFFS
- LittleFS

## 参考资源

- [st7789_mpy GitHub 仓库](https://github.com/russhughes/st7789_mpy)
- [MicroPython 文件系统文档](https://docs.micropython.org/en/latest/reference/filesystem.html)
- [ESP8266 内存管理指南](https://docs.micropython.org/en/latest/esp8266/tutorial/intro.html#esp8266-boards)
```

<file_path>
weather_station/utils/convert_assets.sh
</file_path>
<edit_description>
创建转换脚本，用于将字体和图片转换为二进制文件
</edit_description>

```bash
#!/bin/bash
#!/bin/bash
# -*- coding: utf-8 -*-
# 资源转换脚本 - 将字体和图片转换为二进制文件供流式加载使用
# 使用方法: ./convert_assets.sh

set -e  # 遇到错误时退出

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSETS_DIR="$PROJECT_ROOT/utils/assets"
OUTPUT_DIR="$PROJECT_ROOT/utils/output"

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的信息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装，请先安装 Python3"
        exit 1
    fi
    
    # 检查freetype-py
    if ! python3 -c "import freetype" &> /dev/null; then
        print_warn "freetype-py 未安装，尝试安装..."
        pip3 install freetype-py
    fi
    
    # 检查Pillow
    if ! python3 -c "import PIL" &> /dev/null; then
        print_warn "Pillow 未安装，尝试安装..."
        pip3 install Pillow
    fi
    
    print_info "依赖检查完成"
}

# 转换字体
convert_font() {
    local font_file="$1"
    local font_size="$2"
    local characters="$3"
    local output_name="$4"
    
    print_info "转换字体: $font_file (大小: $font_size)"
    
    local font_name=$(basename "$font_file" | cut -d'.' -f1)
    local temp_py="$OUTPUT_DIR/${font_name}_${font_size}.py"
    local bin_file="$OUTPUT_DIR/${output_name}.bin"
    
    # 步骤1: 转换为Python模块
    print_info "步骤1: 将字体转换为Python模块..."
    python3 "$PROJECT_ROOT/utils/font2bitmap.py" "$font_file" "$font_size" -s "$characters" > "$temp_py"
    
    # 步骤2: 转换为二进制文件
    print_info "步骤2: 将Python模块转换为二进制文件..."
    python3 "$PROJECT_ROOT/utils/font2bin.py" "$temp_py" "$bin_file"
    
    print_info "字体转换完成: $bin_file"
}

# 转换图片
convert_image() {
    local image_file="$1"
    local colors="$2"
    local output_name="$3"
    
    print_info "转换图片: $image_file (颜色深度: $colors)"
    
    local image_name=$(basename "$image_file" | cut -d'.' -f1)
    local temp_py="$OUTPUT_DIR/${image_name}.py"
    
    # 检查imgtobitmap.py是否存在
    if [ ! -f "$PROJECT_ROOT/utils/imgtobitmap.py" ]; then
        print_warn "imgtobitmap.py 不存在，跳过图片转换"
        return
    fi
    
    # 步骤1: 转换为Python模块
    print_info "步骤1: 将图片转换为Python模块..."
    python3 "$PROJECT_ROOT/utils/imgtobitmap.py" "$image_file" "$colors" > "$temp_py"
    
    # 步骤2: 转换为二进制文件
    print_info "步骤2: 将Python模块转换为二进制文件..."
    python3 "$PROJECT_ROOT/utils/image2bin.py" "$temp_py" "$OUTPUT_DIR/${output_name}.bin"
    
    print_info "图片转换完成: $OUTPUT_DIR/${output_name}.bin"
}

# 主转换函数
main() {
    print_info "开始转换资源..."
    print_info "输出目录: $OUTPUT_DIR"
    
    # 定义常用字符集
    CHINESE_CHARS="你好世界温度湿度天气空气质量良一般差零一二三四五六七八九十百千万亿点℃°%‰"
    ENGLISH_CHARS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?-+%:="
    WEATHER_CHARS="晴多云阴雨雪雷风雾霾霜露冰雹"
    
    # 转换中文字体
    if [ -f "$ASSETS_DIR/NotoSansSC-Regular.otf" ]; then
        convert_font "$ASSETS_DIR/NotoSansSC-Regular.otf" "20" "$CHINESE_CHARS" "ch_font_20"
        convert_font "$ASSETS_DIR/NotoSansSC-Regular.otf" "16" "$CHINESE_CHARS" "ch_font_16"
    else
        print_warn "中文字体文件不存在: $ASSETS_DIR/NotoSansSC-Regular.otf"
    fi
    
    # 转换英文字体
    if [ -f "$ASSETS_DIR/NotoSansSC-Regular.otf" ]; then
        convert_font "$ASSETS_DIR/NotoSansSC-Regular.otf" "18" "$ENGLISH_CHARS" "en_font_18"
        convert_font "$ASSETS_DIR/NotoSansSC-Regular.otf" "14" "$ENGLISH_CHARS" "en_font_14"
    fi
    
    # 转换天气字体
    if [ -f "$ASSETS_DIR/NotoSansSC-Regular.otf" ]; then
        convert_font "$ASSETS_DIR/NotoSansSC-Regular.otf" "24" "$WEATHER_CHARS$CHINESE_CHARS$ENGLISH_CHARS" "weather_font_24"
    fi
    
    # 转换图片
    if [ -f "$ASSETS_DIR/python-logo.png" ]; then
        convert_image "$ASSETS_DIR/python-logo.png" "4" "python_logo"
    else
        print_warn "Python Logo图片不存在: $ASSETS_DIR/python-logo.png"
    fi
    
    if [ -f "$ASSETS_DIR/boot.jpg" ]; then
        convert_image "$ASSETS_DIR/boot.jpg" "4" "boot_image"
    else
        print_warn "启动图片不存在: $ASSETS_DIR/boot.jpg"
    fi
    
    # 显示输出文件信息
    print_info "转换完成! 生成的二进制文件:"
    ls -lh "$OUTPUT_DIR"/*.bin 2>/dev/null || print_warn "没有生成二进制文件"
    
    print_info "信息文件:"
    ls -lh "$OUTPUT_DIR"/*.info 2>/dev/null || print_warn "没有生成信息文件"
    
    print_info "Python模块:"
    ls -lh "$OUTPUT_DIR"/*.py 2>/dev/null || print_warn "没有生成Python模块"
    
    print_info "转换脚本执行完成!"
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo ""
    echo "此脚本将转换以下资源:"
    echo "  1. 中文字体 - 转换为不同大小的二进制字体文件"
    echo "  2. 英文字体 - 转换为不同大小的二进制字体文件"
    echo "  3. 天气图标字体 - 转换为二进制字体文件"
    echo "  4. 图片 - 转换为二进制图片文件"
    echo ""
    echo "输入文件应位于: $ASSETS_DIR"
    echo "输出文件将保存到: $OUTPUT_DIR"
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
    shift
done

# 检查依赖并执行转换
check_dependencies
main
```

<file_path>
weather_station/utils/image2bitmap.py
</file_path>
<edit_description>
创建图片转换脚本，将图片转换为Python位图模块
</edit_description>

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
image2bitmap.py - Convert image files to Python bitmap modules for st7789_mpy

This script converts image files (PNG, JPG, etc.) to Python bitmap modules
compatible with the st7789_mpy library. The output modules can be used with
st7789.bitmap() method.

Usage:
    python image2bitmap.py <image_file> <colors> [output_file]

Example:
    python image2bitmap.py logo.png 4 logo.py
"""

import sys
import os
import shlex
from PIL import Image, ImageOps
import struct


def convert_image_to_bitmap(image_path, colors, output_path=None):
    """
    Convert an image file to a Python bitmap module
    
    Args:
        image_path (str): Path to the input image file
        colors (int): Number of colors in the output (must be a power of 2, max 256)
        output_path (str, optional): Path to the output Python file
        
    Returns:
        bool: True if successful, False otherwise
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
        
        # Load and convert image
        print(f"Loading image: {image_path}")
        image = Image.open(image_path)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Get dimensions
        width, height = image.size
        print(f"Image dimensions: {width}x{height}")
        
        # Convert to palette image with specified number of colors
        palette_image = image.convert(
            mode='P', 
            palette=Image.ADAPTIVE, 
            colors=colors
        )
        
        # Get palette
        palette = palette_image.getpalette()
        
        # Create Python bitmap code
        image_name = os.path.splitext(os.path.basename(image_path))[0]
        cmd_line = " ".join(map(shlex.quote, sys.argv))
        
        # Determine output file
        if not output_path:
            output_path = f"{image_name}.py"
        
        print(f"Generating Python module: {output_path}")
        
        # Write Python module
        with open(output_path, 'w') as f:
            f.write("# -*- coding: utf-8 -*-\n")
            f.write(f"# Converted from {image_path} using:\n")
            f.write(f"#     {cmd_line}\n\n")
            
            # Write constants
            f.write(f"WIDTH = {width}\n")
            f.write(f"HEIGHT = {height}\n")
            f.write(f"COLORS = {colors}\n")
            f.write(f"BPP = {bpp}\n\n")
            
            # Write palette
            f.write("PALETTE = [\n")
            for i in range(colors):
                r = palette[i * 3]
                g = palette[i * 3 + 1]
                b = palette[i * 3 + 2]
                
                # Convert to RGB565 format
                rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                
                # Byte swap for little endian
                color = ((rgb565 & 0xFF) << 8) | ((rgb565 >> 8) & 0xFF)
                
                f.write(f"    0x{color:04X}")
                if i < colors - 1:
                    f.write(",")
                f.write("\n")
            f.write("]\n\n")
            
            # Generate bitmap data
            bitmap_data = bytearray()
            
            for y in range(height):
                for x in range(width):
                    pixel_color_index = palette_image.getpixel((x, y))
                    
                    # Add bits to bitmap
                    for bit in range(bpp - 1, -1, -1):
                        bit_value = (pixel_color_index >> bit) & 1
                        
                        # Pack bits into bytes
                        byte_index = len(bitmap_data)
                        bit_index = 7 - (len(bitmap_data) % 8)
                        
                        if bit_index == 7:
                            bitmap_data.append(0)
                        
                        if bit_value:
                            bitmap_data[byte_index] |= (1 << bit_index)
            
            # Write bitmap data
            f.write("_bitmap = \\\n")
            line_bytes = 16
            for i in range(0, len(bitmap_data), line_bytes):
                line = bitmap_data[i:i+line_bytes]
                hex_string = "".join([f"\\x{b:02X}" for b in line])
                f.write(f"    b'{hex_string}'")
                if i + line_bytes < len(bitmap_data):
                    f.write(" \\\n")
                else:
                    f.write("\n\n")
            
            # Create memoryview for efficient access
            f.write("BITMAP = memoryview(_bitmap)\n")
        
        print(f"Successfully created {output_path}")
        return True
    
    except Exception as e:
        print(f"Error processing image: {e}")
        return False


def main():
    if len(sys.argv) < 3:
        print("Usage: python image2bitmap.py <image_file> <colors> [output_file]")
        print("Example: python image2bitmap.py logo.png 4 logo.py")
        print("")
        print("Arguments:")
        print("  image_file    Input image file (PNG, JPG, etc.)")
        print("  colors        Number of colors in the output (must be power of 2, max 256)")
        print("  output_file   Optional output Python file name")
        return 1
    
    image_path = sys.argv[1]
    
    try:
        colors = int(sys.argv[2])
    except ValueError:
        print(f"Error: Colors must be an integer, got {sys.argv[2]}")
        return 1
    
    output_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Check if input file exists
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return 1
    
    # Convert image
    success = convert_image_to_bitmap(image_path, colors, output_path)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
```

<file_path>
weather_station/utils/imgtobitmap.py
</file_path>
<edit_description>
创建图片转换脚本，将图片转换为Python位图模块
</edit_description>

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
imgtobitmap.py - Convert image files to Python bitmap modules for st7789_mpy

This script converts image files (PNG, JPG, etc.) to Python bitmap modules
compatible with the st7789_mpy library. The output modules can be used with
st7789.bitmap() method.

Usage:
    python imgtobitmap.py <image_file> <colors> [output_file]

Example:
    python imgtobitmap.py logo.png 4 logo.py
"""

import sys
import os
import shlex
from PIL import Image, ImageOps
import struct


def convert_image_to_bitmap(image_path, colors, output_path=None):
    """
    Convert an image file to a Python bitmap module
    
    Args:
        image_path (str): Path to the input image file
        colors (int): Number of colors in the output (must be a power of 2, max 256)
        output_path (str, optional): Path to the output Python file
        
    Returns:
        bool: True if successful, False otherwise
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
        
        # Load and convert image
        print(f"Loading image: {image_path}")
        image = Image.open(image_path)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Get dimensions
        width, height = image.size
        print(f"Image dimensions: {width}x{height}")
        
        # Convert to palette image with specified number of colors
        palette_image = image.convert(
            mode='P', 
            palette=Image.ADAPTIVE, 
            colors=colors
        )
        
        # Get palette
        palette = palette_image.getpalette()
        
        # Create Python bitmap code
        image_name = os.path.splitext(os.path.basename(image_path))[0]
        cmd_line = " ".join(map(shlex.quote, sys.argv))
        
        # Determine output file
        if not output_path:
            output_path = f"{image_name}.py"
        
        print(f"Generating Python module: {output_path}")
        
        # Write Python module
        with open(output_path, 'w') as f:
            f.write("# -*- coding: utf-8 -*-\n")
            f.write(f"# Converted from {image_path} using:\n")
            f.write(f"#     {cmd_line}\n\n")
            
            # Write constants
            f.write(f"WIDTH = {width}\n")
            f.write(f"HEIGHT = {height}\n")
            f.write(f"COLORS = {colors}\n")
            f.write(f"BPP = {bpp}\n\n")
            
            # Write palette
            f.write("PALETTE = [\n")
            for i in range(colors):
                r = palette[i * 3]
                g = palette[i * 3 + 1]
                b = palette[i * 3 + 2]
                
                # Convert to RGB565 format
                rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                
                # Byte swap for little endian
                color = ((rgb565 & 0xFF) << 8) | ((rgb565 >> 8) & 0xFF)
                
                f.write(f"    0x{color:04X}")
                if i < colors - 1:
                    f.write(",")
                f.write("\n")
            f.write("]\n\n")
            
            # Generate bitmap data
            bitmap_data = bytearray()
            
            for y in range(height):
                for x in range(width):
                    pixel_color_index = palette_image.getpixel((x, y))
                    
                    # Add bits to bitmap
                    for bit in range(bpp - 1, -1, -1):
                        bit_value = (pixel_color_index >> bit) & 1
                        
                        # Pack bits into bytes
                        byte_index = len(bitmap_data)
                        bit_index = 7 - (len(bitmap_data) % 8)
                        
                        if bit_index == 7:
                            bitmap_data.append(0)
                        
                        if bit_value:
                            bitmap_data[byte_index] |= (1 << bit_index)
            
            # Write bitmap data
            f.write("_bitmap = \\\n")
            line_bytes = 16
            for i in range(0, len(bitmap_data), line_bytes):
                line = bitmap_data[i:i+line_bytes]
                hex_string = "".join([f"\\x{b:02X}" for b in line])
                f.write(f"    b'{hex_string}'")
                if i + line_bytes < len(bitmap_data):
                    f.write(" \\\n")
                else:
                    f.write("\n\n")
            
            # Create memoryview for efficient access
            f.write("BITMAP = memoryview(_bitmap)\n")
        
        print(f"Successfully created {output_path}")
        return True
    
    except Exception as e:
        print(f"Error processing image: {e}")
        return False


def main():
    if len(sys.argv) < 3:
        print("Usage: python imgtobitmap.py <image_file> <colors> [output_file]")
        print("Example: python imgtobitmap.py logo.png 4 logo.py")
        print("")
        print("Arguments:")
        print("  image_file    Input image file (PNG, JPG, etc.)")
        print("  colors        Number of colors in the output (must be power of 2, max 256)")
        print("  output_file   Optional output Python file name")
        return 1
    
    image_path = sys.argv[1]
    
    try:
        colors = int(sys.argv[2])
    except ValueError:
        print(f"Error: Colors must be an integer, got {sys.argv[2]}")
        return 1
    
    output_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Check if input file exists
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return 1
    
    # Convert image
    success = convert_image_to_bitmap(image_path, colors, output_path)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
```

## 文档和脚本说明

### 流式加载使用指南.md

该文档详细说明了如何使用 st7789_mpy 库进行流式加载，包括：

1. 流式加载概述和优势
2. 字体流式加载技术
3. 图片流式加载技术
4. 转换工具使用方法
5. 实际应用示例（包括天气站应用）
6. 常见问题解答

### convert_assets.sh

这是一个 Bash 脚本，用于一键将字体和图片转换为二进制文件，具有以下功能：

1. 检查并安装必要的依赖（freetype-py 和 Pillow）
2. 将 NotoSansSC-Regular.otf 字体转换为不同大小的中文和英文字体
3. 将 python-logo.png 和 boot.jpg 转换为二进制文件
4. 生成相应的信息文件
5. 提供彩色输出和详细的日志

### imgtobitmap.py

这是一个 Python 脚本，用于将图片文件（PNG、JPG 等）转换为 Python 位图模块：

1. 支持多种图片格式
2. 可配置颜色数量（1-256，必须是2的幂）
3. 自动转换为 RGB565 格式调色板
4. 生成可直接与 st7789.bitmap() 一起使用的 Python 模块

## 使用流程

1. 运行转换脚本：
   ```bash
   cd /path/to/project/weather_station/utils
   chmod +x convert_assets.sh
   ./convert_assets.sh
   ```

2. 将生成的二进制文件上传到 ESP8266/ESP32

3. 在 MicroPython 中使用流式加载：
   ```python
   import st7789
   import st7789.streaming_font_mpy
   import st7789.streaming_image
   
   # 加载流式字体
   font = st7789.streaming_font_mpy.StreamingFont("ch_font_20.font")
   
   # 加载流式图片
   image = st7789.streaming_image.StreamingImage("python_logo.img")
   
   # 使用...
   ```

这份文档和脚本提供了一个完整的解决方案，使开发者能够利用 st7789_mpy 库以流式加载方式显示图片和文字，特别适合 ESP8266 等内存受限设备。