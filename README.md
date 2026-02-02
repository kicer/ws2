# WS2 桌面气象站

([English](README_en.md) | 中文)

基于ESP8266的桌面气象站，能够实时显示天气信息、环境数据和时间。

![WS2气象站](docs/ws2.jpg)
![web管理页面](docs/web.jpg)

## 功能特点

- 🌤️ **实时天气显示**：获取并显示当前天气状况、温度、湿度和空气质量
- 📺 **TFT LCD彩色显示**：1.54寸240x240像素彩色液晶屏
- 🕐 **多种显示模式**：支持多种UI界面，包括天气时钟和电子相册模式
- 🌐 **Web管理界面**：内置轻量级Web服务器，支持浏览器配置和管理
- 📊 **系统监控**：实时显示设备状态、内存使用和网络信息
- 📡 **WiFi连接**：支持2.4GHz WiFi网络，自动重连机制

## 硬件规格

- **主控芯片**：ESP8266/ESP32
- **显示屏**：1.54寸 TFT LCD 240×240像素
- **网络**：802.11 b/g/n WiFi

## 软件架构

本项目基于MicroPython开发，包含以下核心模块：

- **app.py** - 主应用程序
- **config.py** - 配置管理
- **wifi_manager.py** - WiFi连接管理
- **display.py** - 显示屏控制
- **nanoweb.py** - 轻量级异步Web服务器
- **captive_portal.py** - 配置门户

## 快速开始

1. 购物网站搜: WiFi天气时钟
> 务必与商家确认可以通过usb下载固件

2. 连接设备usb，下载完整版固件到ESP8266
   ```bash
   esptool.py --port /dev/ttyUSB0 --baud 460800 write-flash --flash-size=detect 0 firmware.bin
   ```

### 初次配置

1. 设备启动后会创建WiFi热点 `WS2-xxxx`
2. 连接该热点，浏览器会自动跳转访问 `192.168.4.1`
3. 在配置页面输入WiFi信息
4. 设备将自动连接并获取天气信息

## Web管理界面

设备Web界面提供以下功能：

### 设备状态
- 查看系统运行状态、内存使用情况
- 监控设备IP地址和运行时间
- 实时显示UUID和固件版本

### 屏幕显示
- 调节屏幕亮度
-切换显示模式
- LCD内容预览

### 系统配置
- 选择城市和地区
- 设置自动熄屏时间
- 保存/加载配置

### 高级设置
- 执行系统命令
- 查看MAC地址
- 重启设备
- 清空配置

## API接口

设备提供RESTful API接口，可通过HTTP请求获取数据：

```
GET /lcd                    - 获取LCD设置
GET /status                 - 获取系统状态
GET /config                 - 获取配置信息
POST /exec                  - 执行系统命令 {cmd: "命令内容", token: "认证令牌"}
POST /lcd/set               - 设置LCD参数 {brightness: 80, ui_type: "default"}
POST /config/set            - 设置配置 {city: "北京", standby_time: "22:00"}
```

## 开发指南

1. 修改/src/rom下相关文件，使用mpremote romfs更新
2. 自行编译micropython固件需要集成*st7789py_mpy*（未整理）

## 故障排除

### 常见问题

**Q: 设备无法连接WiFi**
- A: 检查WiFi密码是否正确，或重启设备重新配置

**Q: 天气数据不更新**
- A1: 检查网络连接，或尝试强制刷新天气数据
- A2: 个人的天气服务器失联~

## 许可证

本项目采用MIT许可证

## 致谢

- [MicroPython](https://micropython.org/) - 高效的Python微控制器实现
- [ST7789驱动](https://github.com/devbis/st7789py_mpy) - LCD显示屏驱动
- [captive-portal](https://github.com/anson-vandoren/esp8266-captive-portal) - 认证门户
- [Nanoweb](https://github.com/hugokernel/micropython-nanoweb) - 轻量级异步Web服务器
- [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html) - mp控制终端

## 联系方式

- 项目主页: https://github.com/kicer/ws2
- 项目主页: https://iot.foresh.com/git/kicer/ws2
- 问题反馈: https://github.com/kicer/ws2/issues
- QQ联络群: 697580459
