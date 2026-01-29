#!/bin/bash
# -*- coding: utf-8 -*-

CN_TEXT='配置设备网络连接热点自动进入页面0123456789 abcdefghijklmnopqrstuvwxyz:ABCDEFGHIJKLMNOPQRSTUVWXYZ!%*+,-./()[]\"<>=?℃'

SRC_DIR=./assets
DST_DIR=../src/rom/fonts
OTF_FONT=$SRC_DIR/NotoSansSC-Regular.otf

python3 pyfont_to_bin.py $SRC_DIR/romand.py $DST_DIR/en-32x32.hfont
python3 pyfont_to_bin.py $SRC_DIR/vga1_8x16.py $DST_DIR/en-8x16.rfont
python3 pyfont_to_bin.py $SRC_DIR/vga1_16x32.py $DST_DIR/en-16x32.rfont

python3 font2bitmap.py -s "$CN_TEXT" $OTF_FONT 22 > $SRC_DIR/cn-22x24.py
python3 pyfont_to_bin.py $SRC_DIR/cn-22x24.py $DST_DIR/cn-22x24.bfont
