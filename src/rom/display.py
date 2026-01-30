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
            self._pos_y0 = 10
            self.en_font = '/rom/fonts/en0.rfont'
            self.vector_font = '/rom/fonts/en.hfont'
            self.cn_font = '/rom/fonts/cn.bfont'
            self.time_font = '/rom/fonts/time.bfont'
            # 前景色、背景色、提示框背景色
            self._COLORS = (0xFE19, 0x0000, 0x7800)
            self.ui_type = 'default'
            # ui数据
            self.ui_data = {}
            self.ticks = 0 # 据此切换多行显示

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
        self._pos_y0 = 10

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

    def message(self, msg, x=10, y=None, fg=st7789.WHITE, bg=st7789.BLACK):
        if y == None:
            y = self._pos_y0
        self.tft.text(self.en_font, msg, x, y, fg, bg)
        # 每次打印完消息则滚动到下一行
        self._pos_y0 += 20
        if self._pos_y0 >= 240-20:
            self._pos_y0 = 10

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

    def portal_info(self, msg):
        C_FG,C_BG,C_BT = self._COLORS
        self.tft.text(self.en_font, msg, 19, 204, C_FG, C_BT)
    def portal_win(self, ssid):
        tips = [
            "> 连接热点:",
            f"> {ssid}",
            "",
            "> 自动进入配置页面",
        ]
        self.window("配置设备网络连接", tips, "portal ip: 192.168.4.1")

    # 更新ui数据
    def update_ui(self, city=None, weather=None, advice=None, aqi=None, lunar=None, envdat=None):
        self.ticks += 1
        if self.ui_type == 'default':
            # 中文的城市名称
            if city is not None and city != self.ui_data.get('city'):
                self.ui_data['city'] = city
                if self.tft.write(self.cn_font, city, 15,10) == 0:
                    # 城市可能未包括，则显示??
                    self.tft.write(self.cn_font, '??', 15,10)
            # 天气符号: 0-7 (晴、云、雨、雷、雪、雾、风、未知)
            if weather is not None and weather != self.ui_data.get('weather'):
                self.tft.jpg(f"/rom/images/{weather}.jpg",165,10,st7789.SLOW)
                self.ui_data['weather'] = weather
            # 建议信息可能有很多条，需要轮换展示
            if advice is not None and advice != self.ui_data.get('advice'):
                self.ui_data['advice'] = advice
            # AQI等级分成0-5级，分别对应优、良、中、差、污、恶
            if aqi is not None and aqi != self.ui_data.get('aqi'):
                _t = (('优',0x07E0),('良',0xFFE0),('中',0xFD20),('差',0xF800),('污',0x8010),('恶',0x7800))
                _l,_c = _t[aqi]
                self.tft.fill_rect(105, 8, 40, 25, _c)
                self.tft.write(self.cn_font, _l, 114,10, 0,_c)
                self.ui_data['aqi'] = aqi
            # 农历日期，需要和当前日期轮换展示
            if lunar is not None and lunar != self.ui_data.get('lunar'):
                self.ui_data['lunar'] = lunar
            # 环境数据
            if envdat is not None:
                t,rh = envdat.get('t'),envdat.get('rh')
                pm,ap = envdat.get('pm'),envdat.get('ap')
                # 填充后再更新文本
                if t is not None and t != self.ui_data.get('t'):
                    self.ui_data['t'] = t
                    self.tft.fill_rect(35,179,40,16,0)
                    self.tft.draw(self.vector_font, str(t), 35,187,0xFFFF,0.5)
                if rh is not None and rh != self.ui_data.get('rh'):
                    self.ui_data['rh'] = rh
                    self.tft.fill_rect(110,179,40,16,0)
                    self.tft.draw(self.vector_font, str(rh), 110,187,0xFFFF,0.5)
                if pm is not None and pm != self.ui_data.get('pm'):
                    self.ui_data['pm'] = pm
                    self.tft.fill_rect(35,213,40,16,0)
                    self.tft.draw(self.vector_font, str(pm), 35,221,0xFFFF,0.5)
                if ap is not None and ap != self.ui_data.get('ap'):
                    self.ui_data['ap'] = ap
                    self.tft.fill_rect(110,213,40,16,0)
                    self.tft.draw(self.vector_font, str(ap), 110,221,0xFFFF,0.5)
            # 处理日期
            from machine import RTC
            y,m,d,_w,H,M,*_ = RTC().datetime()
            w = ('一','二','三','四','五','六','天')[_w]
            if m!=self.ui_data.get('month') or d!=self.ui_data.get('day'):
                self.ui_data['month'] = m
                self.ui_data['day'] = d
                self.ui_data['weekday'] = w
                # just stop lunar, wait refresh
                self.ui_data['lunar'] = None
            # 切换日期显示
            lunar = self.ui_data.get('lunar')
            if lunar is not None and self.ticks & 0x01:
                w = self.tft.write(self.cn_font, f'{lunar} 星期{w}', 15,135)
            else:
                w = self.tft.write(self.cn_font, f'{m:2d}月{d:2d}日 星期{w}', 15,135)
            print(f'todo: fill date.tail: {w}')
            # 处理时间显示
            if H != self.ui_data.get('hour'):
                self.ui_data['hour'] = H
                self.tft.write(self.time_font,f'{H:02d}:',25,80,0xF080)
            if M != self.ui_data.get('minute'):
                self.ui_data['minute'] = M
                self.tft.write(self.time_font,f'{M:02d}',135,80,0xFF80)
            # 处理建议显示
            advice = self.ui_data.get('advice')
            if isinstance(advice, list) and advice:
                i = self.ticks % len(advice)
                c = advice[i]
                w = self.tft.write(self.cn_font, advice[i], 15,45)
                print(f'todo: fill advice.tail: {w}')

    # 初始化ui固定元素
    def load_ui(self):
        if self.ui_type == 'default':
            # 默认黑色背景 
            self.tft.fill(0)
            # 固定的环境数据图标
            self.tft.jpg("/rom/images/t.jpg",11,177,st7789.SLOW)
            self.tft.jpg("/rom/images/rh.jpg",85,177,st7789.SLOW)
            self.tft.jpg("/rom/images/pm.jpg",11,209,st7789.SLOW)
            self.tft.jpg("/rom/images/ap.jpg",85,208,st7789.SLOW)

        # 更新其他默认数据
        self.update_ui()

# 全局液晶屏实例
display = Display()
