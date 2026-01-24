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
            self._brightness = 50  # 默认亮度50%
            self._initialized = True

    def init_display(self):
        """初始化液晶屏"""
        try:
            from machine import PWM, SPI, Pin

            # 初始化显示屏
            self.tft = st7789.ST7789(
                SPI(1, 40_000_000, polarity=1),
                240,
                240,
                dc=Pin(0, Pin.OUT),
                reset=Pin(2, Pin.OUT),
                buffer_size=0,
            )

            # 初始化PWM背光控制
            self._backlight = PWM(Pin(5), freq=1000)
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

    def driver(self):
        """获取液晶屏对象"""
        return self.tft

    def clear(self, color=st7789.BLACK):
        """清屏"""
        self.tft.fill(color)

    def show_jpg(self, filename, x=0, y=0, mode=st7789.FAST):
        """显示JPG图片"""
        self.tft.jpg(filename, x, y, mode)

    def brightness(self, _brightness=-1):
        """设置背光亮度 (0-100)"""
        if _brightness >= 0 and _brightness <= 100:
            # 将0-100范围映射到0-1023 (PWM占空比)
            duty = int(1023 * _brightness / 100)
            self._backlight.duty(duty)
            self._brightness = _brightness
        return self._brightness


# 全局液晶屏实例
display = Display()
