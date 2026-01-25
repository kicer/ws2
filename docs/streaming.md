### 各工具的区别与用途

1. **font2bitmap.py**
   - 用途：将TrueType字体转换为等宽（或比例）位图字体模块
   - 输入：TrueType字体文件（.ttf/.otf）
   - 输出：Python字体模块（如proverbs_font.py）
   - 特点：
     - 支持比例字体（字符宽度可变）
     - 支持CJK字符和Unicode
     - 生成4个数据结构：MAP、_WIDTHS、_OFFSETS、_BITMAPS
   - 使用方式：`display.write(font_module, "Hello", x, y, color)`

2. **monofont2bitmap.py**
   - 用途：将等宽TrueType字体转换为位图字体模块
   - 输入：TrueType字体文件（.ttf/.otf）
   - 输出：Python字体模块（如inconsolata_32.py）
   - 特点：
     - 固定宽度字符
     - 简单数据结构：HEIGHT、WIDTH、_BITMAP
     - 支持多色字体
   - 使用方式：`display.bitmap(font_module, x, y, char_index)`

3. **font_from_romfont.py**
   - 用途：将ROM字体二进制文件转换为Python模块
   - 输入：老旧计算机/游戏机的ROM字体数据
   - 输出：Python字体模块
   - 特点：
     - 保留复古计算机字体风格
     - 通常8x8固定大小
   - 使用方式：`display.bitmap(font_module, x, y, char_index)`

4. **imgtobitmap.py**
   - 用途：将图像文件转换为位图模块
   - 输入：图像文件（PNG、JPG等）
   - 输出：Python图像模块
   - 特点：
     - 支持任何图像到位图的转换
     - 支持1-8位/像素的颜色深度
     - 生成调色板
   - 使用方式：`display.bitmap(image_module, x, y, 0)`

### 哪个可以转成流式格式？

**所有这些工具的输出都可以转换为流式格式！**

我创建了相应的转换工具：

1. **font2bin.py**：将font2bitmap.py生成的字体模块转换为二进制流式格式
2. **image2bin.py**：将imgtobitmap.py生成的图像模块转换为二进制流式格式

**原理相同**：
- Python模块在导入时加载全部数据到RAM
- 二进制文件可以按需读取，只加载需要的数据
- 针对ESP8266等内存受限设备特别有效

### 流式格式的优势

1. **font2bitmap.py → 流式格式**：
   - 节省93%内存（6.4KB → ~400字节）
   - 适合大型字体，特别是包含CJK字符的字体
   - 保持与原有`st7789.write()`接口的兼容性

2. **imgtobitmap.py → 流式格式**：
   - 适合大型图像或动画
   - 支持动态帧加载（StreamingAnimation类）
   - 可以存储在文件系统而不是RAM中

3. **monofont2bitmap.py → 流式格式**：
   - 简单结构使流式加载更容易
   - 虽然已经很紧凑，但在极小内存环境中仍有价值

4. **font_from_romfont.py → 流式格式**：
   - 超简单结构，流式实现非常直接
   - 对于大批量老旧字体集合有意义

### 实际应用建议

对于ESP8266等内存受限设备：
1. 使用`font2bin.py`将大型字体转换为流式格式
2. 使用`image2bin.py`将大型图像或动画帧转换为流式格式
3. 使用`streaming_font.py`和`streaming_image.py`加载和显示
4. 这样可以在保持功能的同时，最大限度地减少内存使用

这种流式方式使得ESP8266等设备可以显示大型字体和图像，而不会因内存不足而失效。
