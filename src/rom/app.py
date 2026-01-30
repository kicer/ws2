# ESP8266天气站主程序
# 首先尝试连接已保存的WiFi，失败则启动CaptivePortal进行配置

import gc
import json
import sys
import time

import machine
import uasyncio
from config import config
from display import display  # 导入液晶屏管理模块
from wifi_manager import wifi_manager

# 全局变量存储最新的天气数据
latest_weather = None


def parse_url_params(url):
    # 解析URL中的查询参数，返回参数字典
    params = {}

    if "?" in url:
        query_string = url.split("?")[1]
        param_pairs = query_string.split("&")

        for pair in param_pairs:
            if "=" in pair:
                key, value = pair.split("=", 1)
                params[key] = value

    return params


# ntp时钟同步
def sync_ntp_time():
    import ntptime

    ntptime.host = config.get("ntphost", "ntp1.aliyun.com")
    t = ntptime.time() + 3600 * 8

    rtc = machine.RTC()
    tm = time.gmtime(t)
    rtc.datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))
    print(f"时间同步：{rtc.datetime()}")


# 简化的天气数据获取函数
def get_weather_data(city=None, force=False):
    """获取天气数据，返回JSON格式数据

    Args:
        city: 城市名称，如果为None则从配置文件获取
        force: 是否强制刷新，True则忽略缓存重新获取
    """
    global latest_weather

    # 检查是否需要强制更新或者缓存为空
    if not force and latest_weather is not None:
        # 使用缓存数据
        print("使用缓存的天气数据")
        return latest_weather

    try:
        import urequests

        # 从配置文件获取城市，如果没有提供则使用配置中的值
        if city is None:
            city = config.get("city", "北京")

        # 从配置获取API基础URL，默认使用官方API
        api_base = config.get("weather_api_url", "https://iot.foresh.com/api/weather")
        url = f"{api_base}?city={city}"
        print(f"正在获取{city}天气数据...")

        # 发送GET请求
        response = urequests.get(url)

        # 检查响应状态
        if response.status_code == 200:
            # 解析JSON数据
            wdata = response.json()
            response.close()  # 关闭连接释放内存

            # 提取关键信息，减少内存占用
            weather_report = {
                "t": wdata.get("temperature", "N/A"),
                "rh": wdata.get("humidity", "N/A"),
                "pm25": wdata.get("pm25", "N/A"),
                "weather": wdata.get("weather", "N/A"),
                "t_min": wdata.get("t_min", "N/A"),
                "t_max": wdata.get("t_max", "N/A"),
                "city": wdata.get("city", "N/A"),
                "aqi": wdata.get("aqi", "N/A"),
                "date": wdata.get("date", "N/A"),
                "advice": wdata.get("advice", "N/A"),
                "image": wdata.get("image", "N/A"),
            }

            print("天气数据获取成功")
            # 更新缓存
            latest_weather = weather_report

            return weather_report
        else:
            print(f"获取天气数据失败，状态码: {response.status_code}")
            response.close()
            return None

    except Exception as e:
        print(f"获取天气数据出错: {e}")
        return None


# 定时调度任务（时间不敏感，但考虑错开以节约内存）
async def sysinfo_update_task():
    """定时后台任务"""
    weather_ts = 2  # 启动2s后更新
    ntptime_ts = 1  # 启动1s后更新

    # 初始化时间戳
    start_ticks = time.ticks_ms()
    last_weather = last_ntptime = start_ticks

    while True:
        task_id = None  # task执行失败后，要快速重试
        try:
            current_ticks = time.ticks_ms()
            # 计算时间差，处理溢出
            weather_diff = time.ticks_diff(current_ticks, last_weather)
            ntp_diff = time.ticks_diff(current_ticks, last_ntptime)

            if weather_diff >= weather_ts * 1000:
                # 更新天气数据
                gc.collect()
                task_id = "weather"
                get_weather_data(force=True)
                last_weather = current_ticks
                weather_ts = int(config.get("weather_ts", 600))  # 10min
            elif ntp_diff >= ntptime_ts * 1000:
                # 更新NTP时间
                gc.collect()
                task_id = "ntp"
                sync_ntp_time()
                last_ntptime = current_ticks
                ntptime_ts = int(config.get("ntptime_ts", 3600)) + 13  # 1hour
        except Exception as e:
            print(f"定时任务更新错误: {e}")
            if task_id == "ntp":
                ntptime_ts = 10
            elif task_id == "weather":
                weather_ts = 60

        # 等待x秒再检查（1~30）
        _x = min(30, 1 + min(weather_ts, ntptime_ts) // 10)
        await uasyncio.sleep(_x)


# 精简的动画显示任务
async def animation_task():
    """显示JPG动画的后台任务"""
    # 检查液晶屏是否已初始化
    if not display.is_ready():
        print("液晶屏未初始化，跳过动画任务")
        return

    try:
        # 动画参数
        frame_count = 20
        frame_delay = 100  # 帧延迟(毫秒)

        await uasyncio.sleep_ms(2 * 1000)
        print(f"开始JPG动画，帧延迟: {frame_delay}ms")

        frame = 0
        while True:
            try:
                # 计算当前帧号(1-20)
                current_frame = (frame % frame_count) + 1
                filename = f"/rom/images/T{current_frame}.jpg"

                # 显示当前帧，右下角
                display.show_jpg(filename, 160, 160)

                # 控制帧率
                await uasyncio.sleep_ms(frame_delay)

                # 每轮清理一次内存
                gc.collect()

                frame += 2

            except Exception as e:
                print(f"动画帧错误: {e}")
                # 出错后等待1秒再继续
                await uasyncio.sleep_ms(1000)

    except Exception as e:
        print(f"动画任务初始化失败: {e}")

def cb_progress(data):
    if isinstance(data, bytes):
        if data == b'/':
            display.portal_info('load iwconfig page    ')
        elif data == b'/login':
            display.portal_info('WiFi connecting ...   ')
    elif isinstance(data, str):
        display.message(data, 19, 204)

    if data: print(f'progress: {str(data)}')

def start():
    # 初始化液晶屏
    #display.init_display(config.get("bl_mode") != "gpio")
    display.init_display(False, buffer_size=5000)
    display.brightness(int(config.get("brightness", 10)))
    display.show_jpg("/rom/images/T1.jpg", 80, 80)
    gc.collect()
    cb_progress("WiFi connect ...")

    if not wifi_manager.connect(cb_progress):
        gc.collect()
        from captive_portal import CaptivePortal
        portal = CaptivePortal()
        display.portal_win(portal.essid.decode('ascii'))
        portal.start(cb_progress)
        # just reboot
        machine.reset()

    gc.collect()
    display.load_ui()

    # init web server
    from rom.nanoweb import Nanoweb

    naw = Nanoweb()
    # website top directory
    naw.STATIC_DIR = "/rom/www"

    # /ping: pong
    @naw.route("/ping")
    async def ping(request):
        await request.write("HTTP/1.1 200 OK\r\n")
        await request.write("Content-Type: text\r\n\r\n")
        await request.write("pong")

    # /status
    @naw.route("/status")
    async def ping(request):
        await request.write("HTTP/1.1 200 OK\r\n")
        await request.write("Content-Type: application/json\r\n\r\n")
        await request.write(
            json.dumps(
                {
                    "time": "{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                        *time.localtime()
                    ),
                    "uptime": str(f"{time.ticks_ms() // 1000} sec"),
                    "memory": str(f"{gc.mem_free() // 1000} KB"),
                    "uuid": str(machine.unique_id().hex()),
                    "platform": str(sys.platform),
                    "version": str(sys.version),
                }
            )
        )

    # /weather: 返回天气数据
    @naw.route("/weather*")
    async def weather_status(request):
        await request.write("HTTP/1.1 200 OK\r\n")
        await request.write("Content-Type: application/json\r\n\r\n")

        # 解析URL参数
        params = parse_url_params(request.url)
        # 获取天气数据
        weather = get_weather_data(
            city=params.get("city"), force=params.get("force", False)
        )
        if weather:
            await request.write(json.dumps(weather))
        else:
            await request.write(json.dumps({"error": "Failed to get weather data"}))

    # /lcd: 获取LCD状态
    @naw.route("/lcd")
    async def lcd_status(request):
        await request.write("HTTP/1.1 200 OK\r\n")
        await request.write("Content-Type: application/json\r\n\r\n")

        # 返回LCD状态
        lcd_status = {
            "ready": display.is_ready(),
            "brightness": display.brightness(),
            "ui_type": display.ui_type,
        }
        await request.write(json.dumps(lcd_status))

    # /lcd/set: 设置LCD状态
    @naw.route("/lcd/set")
    async def lcd_set(request):
        ack = {"status": "success"}
        try:
            if request.method != "POST":
                raise Exception("invalid request")
            content_length = int(request.headers["Content-Length"])
            post_data = (await request.read(content_length)).decode()

            for k, v in json.loads(post_data).items():
                if k == "brightness":
                    display.brightness(int(v))
        except Exception as e:
            ack["status"] = "error"
            ack["message"] = str(e)
        finally:
            await request.write(
                "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"
            )
            await request.write(json.dumps(ack))

    # /exec: 执行命令并返回
    # {"cmd":"import network;R=network.WLAN().config(\"mac\").hex()", "token":"xxx"}
    @naw.route("/exec")
    async def eval_cmd(request):
        ack = {"status": "success"}
        try:
            if request.method != "POST":
                raise Exception("invalid request")
            content_length = int(request.headers["Content-Length"])
            post_data = (await request.read(content_length)).decode()

            cmd = json.loads(post_data).get("cmd")
            token = json.loads(post_data).get("token")
            if cmd and token == machine.unique_id().hex():
                _NS = {}
                exec(cmd, _NS)
                ack["result"] = str(_NS.get("R"))
        except Exception as e:
            ack["status"] = "error"
            ack["message"] = str(e)
        finally:
            await request.write(
                "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"
            )
            await request.write(json.dumps(ack))

    # /config: 获取当前配置
    @naw.route("/config")
    async def config_get(request):
        await request.write("HTTP/1.1 200 OK\r\n")
        await request.write("Content-Type: application/json\r\n\r\n")
        # 返回所有配置项
        await request.write(json.dumps(config.config_data))

    # /config/set: 更新配置
    # curl -H "Content-Type: application/json" -X POST -d '{"city":"xxx","who":"ami"}' 'http://<url>/config/set'
    @naw.route("/config/set")
    async def config_update(request):
        ack = {"status": "success"}
        try:
            if request.method != "POST":
                raise Exception("invalid request")
            content_length = int(request.headers["Content-Length"])
            post_data = (await request.read(content_length)).decode()

            for k, v in json.loads(post_data).items():
                config.set(k, v)
            config.write()
        except Exception as e:
            ack["status"] = "error"
            ack["message"] = str(e)
        finally:
            await request.write(
                "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"
            )
            await request.write(json.dumps(ack))

    # create task
    loop = uasyncio.get_event_loop()
    loop.create_task(naw.run())

    # 启动定时更新任务
    loop.create_task(sysinfo_update_task())

    # 启动动画显示任务
    loop.create_task(animation_task())

    gc.collect()
    print(f"success: {gc.mem_free()}...")

    # run!
    loop.run_forever()
