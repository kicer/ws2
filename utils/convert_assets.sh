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
