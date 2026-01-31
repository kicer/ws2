#!/bin/bash
# -*- coding: utf-8 -*-

# switch to local path
cd "$(dirname "$0")" || exit 1

TIME_TEXT='0123456789: .-'

CN_TEXT='!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~'
CN_TEXT="${CN_TEXT} '℃，。（）"
CN_TEXT="${CN_TEXT}0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

SRC_DIR=./assets
DST_DIR=../src/rom/fonts
README="$DST_DIR/README.md"

# 中文黑体源字体
CN_OTF_FONT="$SRC_DIR/fonts/STHeiti.ttc"
# 英文时间源字体
TIME_OTF_FONT="$SRC_DIR/fonts/BloodWaxItalic.otf"

# 追加中文常用汉字列表
CN_TEXT="${CN_TEXT}$(< $SRC_DIR/cn-words.txt)"

echo "# 字体文件说明" > "$README"
echo "" >>"$README"

echo "1. en0.rfont/en1.rfont 英文字体" >> "$README"
echo ">  顺序排列，相等大小、可快速定位" >> "$README"
echo "" >>"$README"
python3 pyfont_to_bin.py "$SRC_DIR/pyfont/vga1_8x16.py" "$DST_DIR/en0.rfont"
python3 pyfont_to_bin.py "$SRC_DIR/pyfont/vga1_16x32.py" "$DST_DIR/en1.rfont"

echo "2. en.hfont 矢量英文字体" >> "$README"
echo ">  顺序排列，带索引表，只画线无背景色，可自由缩放，显示速度快" >> "$README"
echo "" >>"$README"
python3 pyfont_to_bin.py "$SRC_DIR/pyfont/romand.py" "$DST_DIR/en.hfont"

echo "3. cn.bfont 中文字体" >> "$README"
echo ">  有字符MAP表，二叉树查找" >> "$README"
echo "" >>"$README"
SORTED_TEXT=$(python3 -c "text = '''$CN_TEXT''';sorted_unique = ''.join(sorted(set(text), key=lambda c: ord(c)));print(sorted_unique, end='')")
python3 font2bitmap.py -s "$SORTED_TEXT" "$CN_OTF_FONT" 20 > "$SRC_DIR/pyfont/cn.py"
python3 pyfont_to_bin.py "$SRC_DIR/pyfont/cn.py" "$DST_DIR/cn.bfont"

echo "4. time.bfont 时间字体" >> "$README"
echo ">  有字符MAP表，二叉树查找" >> "$README"
echo "" >>"$README"
SORTED_TEXT=$(python3 -c "text = '''$TIME_TEXT''';sorted_unique = ''.join(sorted(set(text), key=lambda c: ord(c)));print(sorted_unique, end='')")
python3 font2bitmap.py -s "$SORTED_TEXT" "$TIME_OTF_FONT" 48 > "$SRC_DIR/pyfont/time.py"
python3 pyfont_to_bin.py "$SRC_DIR/pyfont/time.py" "$DST_DIR/time.bfont"


# 开始转换图片文件
SRC_DIR=./assets/images
DST_DIR=../src/rom/images

# 透明色转换成黑色背景，质量95%
python3 png_to_jpg.py -d "$SRC_DIR/" --color black --quality 100
mv -v "$SRC_DIR"/*.jpg "$DST_DIR/"
