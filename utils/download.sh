#!/bin/sh

# 连接并打印文件列表
mpremote connect /dev/tty.wchusbserial14310 ls

# 生成romfs文件系统并上传
mpremote romfs deploy src/rom

# 复制文件
for file in src/*.py; do
    if [ -f "$file" ]; then
        mpremote fs cp "$file" :
    fi
done

# 打印文件列表
mpremote ls /
mpremote ls /rom
