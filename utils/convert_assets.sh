#!/bin/bash
# -*- coding: utf-8 -*-
# 资源转换脚本 - 将字体和图片转换为二进制文件供流式加载使用
# 使用方法: ./convert_assets.sh

set -e  # 遇到错误时退出

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSETS_DIR="$PROJECT_ROOT/utils/assets"
FONTS_DIR="$PROJECT_ROOT/utils/assets"
FONT_CONFIG_PATH="$ASSETS_DIR/fonts.json"
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
# 图片转换配置表 - 调整这里来自定义图片设置
# ==============================================

# 默认图片颜色深度
DEFAULT_IMAGE_COLORS=4

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

# 读取字体配置文件
load_font_configs() {
    local fonts_file="$FONT_CONFIG_PATH"

    if [ ! -f "$fonts_file" ]; then
        print_warn "字体配置文件不存在: $fonts_file"
        print_warn "将跳过字体转换"
        return
    fi

    print_info "加载字体配置文件: $fonts_file"
    print_blue "字体配置:"
    echo "----------------------------------------"
    printf "%-12s %-30s %-8s %-15s %s\n" "字体名称" "字符集预览" "字号" "输出名称" "描述"
    echo "----------------------------------------"

    # 检查是否有Python可用来解析JSON
    if ! command -v python3 &> /dev/null; then
        print_warn "Python3 不可用，无法解析JSON配置文件"
        print_warn "将跳过字体转换"
        return
    fi

    # 使用Python解析JSON并生成临时配置文件
    python3 -c "
import json
import sys

try:
    with open('$fonts_file', 'r', encoding='utf-8') as f:
        config = json.load(f)

    line_num = 0
    for font in config.get('fonts', []):
        name = font.get('name', '')
        file = font.get('file', '')
        size = font.get('size', '')
        chars = font.get('chars', '')
        output = font.get('output', '')
        description = font.get('description', '')

        if not name or not file or not size or not output:
            continue

        # 如果是相对路径，加上assets目录
        if not file.startswith('/'):
            file = '$ASSETS_DIR/' + file

        # 显示配置信息
        preview = chars[:25] + ('...' if len(chars) > 25 else '')
        print(f'{name:<12} {preview:<30} {size:<8} {output:<15} {description}')

        # 存储配置到临时文件
        with open('$TEMP_FONT_CONFIG_FILE', 'a') as f_out:
            f_out.write(f'{name}|{chars}|{file}|{size}|{output}|{description}\n')

        line_num += 1

    print(f'\n加载了 {line_num} 个字体配置')
except Exception as e:
    print(f'解析JSON配置文件时出错: {e}', file=sys.stderr)
    sys.exit(1)
"
}

# 显示图片配置
show_image_configs() {
    print_blue "图片转换:"
    echo "----------------------------------------"
    echo "支持格式: ${IMAGE_EXTENSIONS[*]}"
    echo "默认颜色深度: $DEFAULT_IMAGE_COLORS"
    echo "特殊配置: bx_开头的图片文件名中的x值将覆盖默认颜色深度"
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
    local file_name="$1"

    # 检查是否是b数字_或bx数字_开头的文件
    if [[ "$file_name" =~ ^b[0-9]+_ ]] || [[ "$file_name" =~ ^bx[0-9]+_ ]]; then
        # 提取数字部分
        local colors=$(echo "$file_name" | sed -E 's/^b(x?)([0-9]+)_.*/\2/')
        print_info "图片 $file_name 使用特殊颜色深度: $colors" >&2
        echo "$colors"
        return
    fi

    # 使用默认颜色深度
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
    local bin_file="$output_bin_dir/${output_name}.font"

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
    local bin_file="$output_bin_dir/${output_name}.img"

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

    # 初始化字体配置文件列表
    TEMP_FONT_CONFIG_FILE="/tmp/font_configs.$$"

    # 加载字体配置
    load_font_configs

    # 显示图片配置
    show_image_configs

    # 转换字体
    if [ ! -f "$TEMP_FONT_CONFIG_FILE" ] || [ ! -s "$TEMP_FONT_CONFIG_FILE" ]; then
        print_warn "没有找到任何字体配置，跳过字体转换"
    else
        while IFS='|' read -r font_name characters font_file font_size output_name description; do
            # 只在字体文件存在时转换
            if [ -f "$font_file" ]; then
                convert_font "$font_file" "$font_size" "$characters" "$output_name" "$OUTPUT_DIR/py" "$OUTPUT_DIR/bin"
            else
                print_warn "字体文件不存在: $font_file"
            fi
        done < "$TEMP_FONT_CONFIG_FILE"
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
    ls -lh "$OUTPUT_DIR/bin"/*.img "$OUTPUT_DIR/bin"/*.font 2>/dev/null || print_warn "没有生成二进制文件"

    echo -e "\n${GREEN}=== 信息文件 ===${NC}"
    ls -lh "$OUTPUT_DIR/py"/*.info 2>/dev/null || print_warn "没有生成信息文件"

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
    echo "  1. 字体 - 根据assets/fonts/fonts.txt配置转换为二进制字体文件"
    echo "  2. 图片 - 遍历assets目录下所有支持的图片文件，转换为二进制图片文件"
    echo ""
    echo "输入文件应位于: $ASSETS_DIR"
    echo "字体配置文件应位于: $FONTS_DIR/fonts.txt"
    echo "输出文件将保存到:"
    echo "  - Python模块: $OUTPUT_DIR/py"
    echo "  - 二进制文件: $OUTPUT_DIR/bin"
    echo ""
    echo "图片特殊命名规则:"
    echo "  - 默认使用 $DEFAULT_IMAGE_COLORS 色深度"
    echo "  - 如果图片名以 bx_N_ 开头，则使用 N 色深度"
    echo "    例如: bx_2_icon.png 将使用 2 色深度"
    echo ""
    echo "fonts.json 配置格式 (JSON):"
    echo "  {"
    echo "    \"fonts\": ["
    echo "      {"
    echo "        \"name\": \"小字体\","
    echo "        \"file\": \"NotoSansSC-Regular.otf\","
    echo "        \"size\": 14,"
    echo "        \"chars\": \"你好世界...ABCD...\","
    echo "        \"output\": \"small_font\","
    echo "        \"description\": \"用于基本UI元素的小号字体\""
    echo "      },"
    echo "      {"
    echo "        \"name\": \"中字体\","
    echo "        \"file\": \"NotoSansSC-Regular.otf\","
    echo "        \"size\": 18,"
    echo "        \"chars\": \"你好今天天气...ABCD...\","
    echo "        \"output\": \"medium_font\","
    echo "        \"description\": \"用于主要文本显示的中号字体\""
    echo "      }"
    echo "    ]"
    echo "  }"
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

# 清理临时文件
cleanup() {
    if [ -f "$TEMP_FONT_CONFIG_FILE" ]; then
        rm -f "$TEMP_FONT_CONFIG_FILE"
    fi
}

# 注册清理函数
trap cleanup EXIT

# 检查依赖并执行转换
check_dependencies
main
