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
mkdir -p "$OUTPUT_DIR/py"
mkdir -p "$OUTPUT_DIR/bin"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_blue() {
    echo -e "${BLUE}[CONFIG]${NC} $1"
}

# ==============================================
# 字体配置表 - 调整这里来自定义字体设置
# 格式: "字体名称|字符集|字体文件|字号|输出名称"
# ==============================================

# 小号字体配置
SMALL_FONT_CHARS="你好世界温度湿度1234567890.,?!℃°%:"
SMALL_FONT_FILE="$ASSETS_DIR/NotoSansSC-Regular.otf"
SMALL_FONT_SIZE=14
SMALL_FONT_OUTPUT="small_font"

# 中号字体配置
MEDIUM_FONT_CHARS="你好今天天气温度湿度空气质量良一般差零一二三四五六七八九十百千万亿点°%℃ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.-:"
MEDIUM_FONT_FILE="$ASSETS_DIR/NotoSansSC-Regular.otf"
MEDIUM_FONT_SIZE=18
MEDIUM_FONT_OUTPUT="medium_font"

# 大号字体配置
LARGE_FONT_CHARS="你好今天温度湿度一二三四五六七八九十°%℃:"
LARGE_FONT_FILE="$ASSETS_DIR/NotoSansSC-Regular.otf"
LARGE_FONT_SIZE=24
LARGE_FONT_OUTPUT="large_font"

# 天气字体配置
WEATHER_FONT_CHARS="晴多云阴雨雪雷风雾霾霜露冰雹"
WEATHER_FONT_FILE="$ASSETS_DIR/NotoSansSC-Regular.otf"
WEATHER_FONT_SIZE=28
WEATHER_FONT_OUTPUT="weather_font"

# ==============================================
# 图片转换配置表 - 调整这里来自定义图片设置
# ==============================================

# 默认图片颜色深度
DEFAULT_IMAGE_COLORS=8

# 支持的图片文件扩展名
IMAGE_EXTENSIONS=("png" "jpg" "jpeg" "bmp" "gif")



# ==============================================
# 函数定义
# ==============================================

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

# 显示字体配置
show_font_configs() {
    print_blue "字体配置:"
    echo "----------------------------------------"
    printf "%-12s %-8s %-15s %-30s %s\n" "字体名称" "字号" "输出名称" "描述" "字符集预览"
    echo "----------------------------------------"

    # 小字体
    local preview="${SMALL_FONT_CHARS:0:25}"
    if [[ ${#SMALL_FONT_CHARS} -gt 25 ]]; then
        preview="$preview..."
    fi
    printf "%-12s %-8s %-15s %-30s %s\n" "小字体" "$SMALL_FONT_SIZE" "$SMALL_FONT_OUTPUT" "基本UI元素" "$preview"

    # 中字体
    preview="${MEDIUM_FONT_CHARS:0:25}"
    if [[ ${#MEDIUM_FONT_CHARS} -gt 25 ]]; then
        preview="$preview..."
    fi
    printf "%-12s %-8s %-15s %-30s %s\n" "中字体" "$MEDIUM_FONT_SIZE" "$MEDIUM_FONT_OUTPUT" "主要文本显示" "$preview"

    # 大字体
    preview="${LARGE_FONT_CHARS:0:25}"
    if [[ ${#LARGE_FONT_CHARS} -gt 25 ]]; then
        preview="$preview..."
    fi
    printf "%-12s %-8s %-15s %-30s %s\n" "大字体" "$LARGE_FONT_SIZE" "$LARGE_FONT_OUTPUT" "标题和重要信息" "$preview"

    # 天气字体
    preview="${WEATHER_FONT_CHARS:0:25}"
    if [[ ${#WEATHER_FONT_CHARS} -gt 25 ]]; then
        preview="$preview..."
    fi
    printf "%-12s %-30s %-8s %-15s %s\n" "天气字体" "$WEATHER_FONT_SIZE" "$WEATHER_FONT_OUTPUT" "天气图标" "$preview"

    echo
}

# 显示图片配置
show_image_configs() {
    print_blue "图片转换:"
    echo "----------------------------------------"
    echo "支持格式: ${IMAGE_EXTENSIONS[*]}"
    echo "默认颜色深度: $DEFAULT_IMAGE_COLORS"
    echo
    echo "所有图片将使用默认颜色深度: $DEFAULT_IMAGE_COLORS"
    echo
}

# 检查图片文件
is_image_file() {
    local file_name="$1"
    local ext="${file_name##*.}"

    for supported_ext in "${IMAGE_EXTENSIONS[@]}"; do
        if [[ "$ext" == "$supported_ext" ]]; then
            return 0
        fi
    done
    return 1
}

# 获取图片颜色深度
get_image_colors() {
    # 统一使用默认颜色深度
    echo "$DEFAULT_IMAGE_COLORS"
}

# 转换字体
convert_font() {
    local font_file="$1"
    local font_size="$2"
    local characters="$3"
    local output_name="$4"
    local output_py_dir="$5"
    local output_bin_dir="$6"

    print_info "转换字体: $(basename "$font_file") (字号: $font_size)"

    local font_name=$(basename "$font_file" | cut -d'.' -f1)
    local temp_py="$output_py_dir/${output_name}.py"
    local bin_file="$output_bin_dir/${output_name}.bin"

    # 步骤1: 转换为Python模块
    print_info "  步骤1: 将字体转换为Python模块..."
    python3 "$PROJECT_ROOT/utils/font2bitmap.py" "$font_file" "$font_size" -s "$characters" > "$temp_py"

    # 步骤2: 转换为二进制文件
    print_info "  步骤2: 将Python模块转换为二进制文件..."
    python3 "$PROJECT_ROOT/utils/font2bin.py" "$temp_py" "$bin_file"

    print_info "  字体转换完成: $bin_file"
}

# 转换图片
convert_image() {
    local image_file="$1"
    local colors="$2"
    local output_name="$3"
    local output_py_dir="$4"
    local output_bin_dir="$5"

    print_info "转换图片: $(basename "$image_file") (颜色深度: $colors)"

    local temp_py="$output_py_dir/${output_name}.py"
    local bin_file="$output_bin_dir/${output_name}.bin"

    # 检查imgtobitmap.py是否存在
    if [ ! -f "$PROJECT_ROOT/utils/imgtobitmap.py" ]; then
        print_warn "imgtobitmap.py 不存在，跳过图片转换"
        return
    fi

    # 步骤1: 转换为Python模块
    print_info "  步骤1: 将图片转换为Python模块..."
    python3 "$PROJECT_ROOT/utils/imgtobitmap.py" "$image_file" "$colors" > "$temp_py"

    # 步骤2: 转换为二进制文件
    print_info "  步骤2: 将Python模块转换为二进制文件..."
    python3 "$PROJECT_ROOT/utils/image2bin.py" "$temp_py" "$bin_file"

    print_info "  图片转换完成: $bin_file"
}

# 主转换函数
main() {
    print_info "开始转换资源..."
    print_info "输出目录: $OUTPUT_DIR"

    # 显示配置
    show_font_configs
    show_image_configs

    # 确认字体文件存在
    local font_files_exist=false

    if [ -f "$SMALL_FONT_FILE" ]; then
        font_files_exist=true
    elif [ -f "$MEDIUM_FONT_FILE" ]; then
        font_files_exist=true
    elif [ -f "$LARGE_FONT_FILE" ]; then
        font_files_exist=true
    elif [ -f "$WEATHER_FONT_FILE" ]; then
        font_files_exist=true
    fi

    if [ "$font_files_exist" = false ]; then
        print_warn "没有找到任何配置的字体文件，跳过字体转换"
    else
        # 转换小字体
        if [ -f "$SMALL_FONT_FILE" ]; then
            convert_font "$SMALL_FONT_FILE" "$SMALL_FONT_SIZE" "$SMALL_FONT_CHARS" "$SMALL_FONT_OUTPUT" "$OUTPUT_DIR/py" "$OUTPUT_DIR/bin"
        else
            print_warn "字体文件不存在: $SMALL_FONT_FILE"
        fi

        # 转换中字体
        if [ -f "$MEDIUM_FONT_FILE" ]; then
            convert_font "$MEDIUM_FONT_FILE" "$MEDIUM_FONT_SIZE" "$MEDIUM_FONT_CHARS" "$MEDIUM_FONT_OUTPUT" "$OUTPUT_DIR/py" "$OUTPUT_DIR/bin"
        else
            print_warn "字体文件不存在: $MEDIUM_FONT_FILE"
        fi

        # 转换大字体
        if [ -f "$LARGE_FONT_FILE" ]; then
            convert_font "$LARGE_FONT_FILE" "$LARGE_FONT_SIZE" "$LARGE_FONT_CHARS" "$LARGE_FONT_OUTPUT" "$OUTPUT_DIR/py" "$OUTPUT_DIR/bin"
        else
            print_warn "字体文件不存在: $LARGE_FONT_FILE"
        fi

        # 转换天气字体
        if [ -f "$WEATHER_FONT_FILE" ]; then
            convert_font "$WEATHER_FONT_FILE" "$WEATHER_FONT_SIZE" "$WEATHER_FONT_CHARS" "$WEATHER_FONT_OUTPUT" "$OUTPUT_DIR/py" "$OUTPUT_DIR/bin"
        else
            print_warn "字体文件不存在: $WEATHER_FONT_FILE"
        fi
    fi

    # 检查并转换图片
    local image_files_exist=false

    # 遍历assets目录下的所有图片文件
    for image_file in "$ASSETS_DIR"/*; do
        if [ -f "$image_file" ]; then
            local file_name=$(basename "$image_file")

            if is_image_file "$file_name"; then
                image_files_exist=true
                break
            fi
        fi
    done

    if [ "$image_files_exist" = false ]; then
        print_warn "assets目录下没有找到支持的图片文件，跳过图片转换"
    else
        print_info "开始转换图片文件..."

        # 遍历assets目录下的所有图片文件
        for image_file in "$ASSETS_DIR"/*; do
            if [ -f "$image_file" ]; then
                local file_name=$(basename "$image_file")

                if is_image_file "$file_name"; then
                    local image_name="${file_name%.*}"
                    local colors=$(get_image_colors "$file_name")

                    convert_image "$image_file" "$colors" "$image_name" "$OUTPUT_DIR/py" "$OUTPUT_DIR/bin"
                fi
            fi
        done
    fi

    # 显示输出文件信息
    print_info "转换完成! 生成的文件:"

    echo -e "\n${GREEN}=== 二进制文件 ===${NC}"
    ls -lh "$OUTPUT_DIR/bin"/*.bin 2>/dev/null || print_warn "没有生成二进制文件"

    echo -e "\n${GREEN}=== 信息文件 ===${NC}"
    ls -lh "$OUTPUT_DIR/bin"/*.info 2>/dev/null || print_warn "没有生成信息文件"

    echo -e "\n${GREEN}=== Python模块 ===${NC}"
    ls -lh "$OUTPUT_DIR/py"/*.py 2>/dev/null || print_warn "没有生成Python模块"

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
    echo "  1. 字体 - 根据配置表转换为不同大小的二进制字体文件"
    echo "  2. 图片 - 遍历assets目录下所有支持的图片文件，转换为二进制图片文件"
    echo ""
    echo "输入文件应位于: $ASSETS_DIR"
    echo "输出文件将保存到:"
    echo "  - Python模块: $OUTPUT_DIR/py"
    echo "  - 二进制文件: $OUTPUT_DIR/bin"
    echo ""
    echo "字体和图片配置可在脚本顶部的配置表中调整"
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
