"""
液晶屏管理模块 - 单例模式实现

提供液晶屏的统一初始化和管理接口，确保整个系统中只有一个液晶屏实例。
适用于ESP8266等内存有限的平台。
"""

import gc

import st7789


class Display:
    """液晶屏管理类 - 单例模式"""

    _instance = None
    _initialized = False

    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(Display, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化液晶屏，只在第一次调用时执行"""
        if not self._initialized:
            self.tft = None
            self._backlight = None
            self._brightness = 80  # 默认亮度80%
            self._initialized = True
            self.en_font = '/rom/fonts/en-8x16.rfont'
            self.cn_font = '/rom/fonts/cn-22x24.bfont'
            self.vector_font = '/rom/fonts/en-32x32.hfont'
            # 前景色、背景色、提示框背景色
            self._COLORS = (0xFE19, 0x0000, 0x7800)

    def init_display(self, bl_pwm=True, buffer_size=2048):
        """初始化液晶屏，默认2048够用且不易有内存碎片"""
        try:
            from machine import PWM, SPI, Pin

            # 初始化显示屏
            self.tft = st7789.ST7789(
                SPI(1, 40_000_000, polarity=1),
                240,
                240,
                dc=Pin(0, Pin.OUT),
                reset=Pin(2, Pin.OUT),
                buffer_size=buffer_size,
            )

            # 初始化PWM背光控制
            if bl_pwm:
                self._backlight = PWM(Pin(5), freq=1000)
            else:
                self._backlight = Pin(5, Pin.OUT)
            self.brightness(self._brightness)

            # 初始化并清屏
            self.tft.init()
            gc.collect()
            self.tft.fill(st7789.BLACK)
            print("液晶屏初始化成功")
            return True

        except Exception as e:
            print(f"液晶屏初始化失败: {e}")
            self.tft = None
            self._backlight = None
            return False

    def is_ready(self):
        """检查液晶屏是否已初始化"""
        return self.tft is not None

    def clear(self, color=st7789.BLACK):
        """清屏"""
        self.tft.fill(color)

    def show_jpg(self, filename, x=0, y=0, mode=st7789.SLOW):
        """显示JPG图片"""
        self.tft.jpg(filename, x, y, mode)

    def brightness(self, _brightness=-1):
        """设置背光亮度 (0-100)"""
        if _brightness >= 0 and _brightness <= 100:
            from machine import PWM
            if type(self._backlight) == PWM: # pwm设备
                # 将0-100范围映射到0-1023 (PWM占空比)
                duty = int(1023 * (100 - _brightness) / 100)
                self._backlight.duty(duty)
            elif _brightness == 0: # 关闭背光
                self._backlight.on()
            else: # 打开背光
                self._backlight.off()
                _brightness = 100
            self._brightness = _brightness
        return self._brightness

    def message(self, msg, x=10, y=10, fg=st7789.WHITE, bg=st7789.BLACK):
        self.tft.text(self.en_font, msg, x, y, fg, bg)

    def window(self, title=None, content=None, info=None):
        C_FG,C_BG,C_BT = self._COLORS
        self.tft.fill(C_BG)
        self.tft.rect(8, 8, 224, 224, C_FG)
        self.tft.fill_rect(9, 9, 222, 40, C_BT)
        self.tft.hline(9, 48, 222, C_FG)
        self.tft.fill_rect(9, 192, 222, 39, C_BT)
        self.tft.hline(9, 192, 222, C_FG)
        if title:
            self.tft.write(self.cn_font, title, 19, 17, C_FG, C_BT)
        if info:
            self.tft.text(self.en_font, info, 19, 204, C_FG, C_BT)
        for i, line in enumerate(content):
            if line:
                self.tft.write(self.cn_font, line, 19, 68+i*28, C_FG, C_BG)

    def portal_win(self, ssid):
        tips = [
            "> 连接热点:",
            f"> {ssid}",
            "",
            "> 自动进入配置页面",
        ]
        self.window("配置设备网络连接", tips, "portal ip: 192.168.4.1")


# 全局液晶屏实例
display = Display()
