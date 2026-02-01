# ESP8266天气站主程序
# 首先尝试连接已保存的WiFi，失败则启动CaptivePortal进行配置

import asyncio
import gc
import json
import sys
import time

import machine
from config import config
from display import display  # 导入液晶屏管理模块
from wifi_manager import wifi_manager


def uuid():
    return str(machine.unique_id().hex())


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


async def post_parse(request):
    if request.method != "POST":
        raise Exception("invalid request")
    content_length = int(request.headers["Content-Length"])
    return (await request.read(content_length)).decode()


async def json_response(request, data):
    await request.write("HTTP/1.1 200 OK\r\n")
    await request.write("Content-Type: application/json; charset=utf-8\r\n\r\n")
    await request.write(data)


CREDENTIALS = ("admin", config.get("web_password", "admin"))


def authenticate(credentials):
    async def fail(request):
        await request.write("HTTP/1.1 401 Unauthorized\r\n")
        await request.write('WWW-Authenticate: Basic realm="Restricted"\r\n\r\n')
        await request.write("<h1>Unauthorized</h1>")

    def decorator(func):
        async def wrapper(request):
            from ubinascii import a2b_base64 as base64_decode

            header = request.headers.get("Authorization", None)
            if header is None:
                return await fail(request)

            # Authorization: Basic XXX
            kind, authorization = header.strip().split(" ", 1)
            if kind != "Basic":
                return await fail(request)

            authorization = (
                base64_decode(authorization.strip()).decode("ascii").split(":")
            )

            if list(credentials) != list(authorization):
                return await fail(request)

            return await func(request)

        return wrapper

    return decorator

# /status: 获取系统状态
@authenticate(credentials=CREDENTIALS)
async def sys_status(request):
    await json_response(
        request,
        json.dumps(
            {
                "time": "{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                    *time.localtime()
                ),
                "uptime": time.ticks_ms(),
                "mem_free": gc.mem_free(),
                "mem_alloc": gc.mem_alloc(),
                "uuid": uuid(),
                "platform": str(sys.platform),
                "version": str(sys.version),
            }
        ),
    )


# /lcd: 获取LCD状态
@authenticate(credentials=CREDENTIALS)
async def lcd_status(request):
    # 返回LCD状态
    await json_response(
        request,
        json.dumps(
            {
                "ready": display.is_ready(),
                "brightness": display.brightness(),
                "ui_type": display.ui_type,
                "data": display.ui_data,
            }
        ),
    )


# /config: 获取当前配置
@authenticate(credentials=CREDENTIALS)
async def config_get(request):
    # 返回所有配置项
    await json_response(request, json.dumps(config.config_data))


# /lcd/set: 设置LCD状态
@authenticate(credentials=CREDENTIALS)
async def lcd_set(request):
    ack = {"status": "success"}
    try:
        post_data = await post_parse(request)

        for k, v in json.loads(post_data).items():
            if k == "brightness":
                display.brightness(int(v))
    except Exception as e:
        ack["status"] = "error"
        ack["message"] = str(e)
    finally:
        await json_response(request, json.dumps(ack))


# /config/set: 更新配置
# curl -H "Content-Type: application/json" -X POST -d '{"city":"xxx","who":"ami"}' 'http://<url>/config/set'
@authenticate(credentials=CREDENTIALS)
async def config_update(request):
    ack = {"status": "success"}
    try:
        post_data = await post_parse(request)

        for k, v in json.loads(post_data).items():
            config.set(k, v)
        config.write()
    except Exception as e:
        ack["status"] = "error"
        ack["message"] = str(e)
    finally:
        await json_response(request, json.dumps(ack))


# /exec: 执行命令并返回
# {"cmd":"import network;R=network.WLAN().config(\"mac\").hex()", "token":"xxx"}
@authenticate(credentials=CREDENTIALS)
async def eval_cmd(request):
    ack = {"status": "success"}
    try:
        post_data = await post_parse(request)

        cmd = json.loads(post_data).get("cmd")
        token = json.loads(post_data).get("token")
        if cmd and token == uuid:
            _NS = {}
            exec(cmd, _NS)
            ack["result"] = str(_NS.get("R"))
    except Exception as e:
        ack["status"] = "error"
        ack["message"] = str(e)
    finally:
        await json_response(request, json.dumps(ack))



# ntp时钟同步
def sync_ntp_time():
    import ntptime

    ntptime.host = config.get("ntphost", "ntp1.aliyun.com")
    t = ntptime.time() + 3600 * 8

    rtc = machine.RTC()
    tm = time.gmtime(t)
    rtc.datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))

    # 同步完成后，等待调度自动更新UI
    print(f"时间同步：{rtc.datetime()}")


# 简化的天气数据获取函数
async def fetch_weather_data(city=None):
    # 获取天气数据，返回JSON格式数据
    try:
        import aiohttp

        # 从配置文件获取城市，如果没有提供则使用配置中的值
        if not city:
            city = config.get("city") or "北京"

        print(f"正在获取{city}天气数据...")
        # 从配置获取API基础URL，默认使用官方API
        url = config.get("weather_api_url", "http://esp.tangofu.com/api/ws2/")
        params = {"uuid": uuid(), "city": city}

        # 发送GET请求
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                # 检查响应状态
                if response.status == 200:
                    # 解析JSON数据
                    wdata = await response.json()

                    # 提取关键信息，减少内存占用
                    city = wdata.get("city", "N/A")
                    weather = wdata.get("weather", 0)
                    t = wdata.get("temperature", "-")
                    rh = wdata.get("humidity", "-")
                    pm = wdata.get("pm25", "-")
                    ap = wdata.get("atmosp", None)
                    co2 = wdata.get("co2", None)
                    aqi = wdata.get("aqi", 0)
                    advice = wdata.get("advice", [])
                    lunar = wdata.get("lunar", None)

                    ip = wifi_manager.get_ip()

                    display.update_ui(
                        city,
                        weather,
                        advice,
                        aqi,
                        lunar,
                        ip,
                        envdat={"t": t, "rh": rh, "co2": co2, "pm": pm, "ap": ap},
                    )
                else:
                    print(f"获取天气数据失败，状态码: {response.status}")

    except Exception as e:
        print(f"获取天气数据出错: {e}")


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
                await fetch_weather_data()
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
        await asyncio.sleep(_x)


# LCD UI显示任务
async def ui_task():
    """显示JPG动画的后台任务"""
    # 检查液晶屏是否已初始化
    if not display.is_ready():
        print("液晶屏未初始化，跳过动画任务")
        return

    try:
        # 延迟2s后开始更新
        await asyncio.sleep_ms(2 * 1000)

        F = 0
        while True:
            try:
                t0 = time.ticks_ms()

                # 计算当前帧号(1-10)，更新动画
                cframe = F % 10
                pic = f"/rom/images/T{cframe}.jpg"
                display.show_jpg(pic, 160, 160)

                # 每隔100帧，更新一次UI显示
                F += 1
                if F % 100 == 0:
                    display.update_ui()

                # 每轮清理一次内存
                gc.collect()

                # 控制帧率
                now = time.ticks_ms()
                ts = time.ticks_diff(now, t0)
                _sT = (100 - ts) if ts < 90 else 10
                await asyncio.sleep_ms(_sT)

            except Exception as e:
                print(f"动画帧错误: {e}")
                # 出错后等待1秒再继续
                await asyncio.sleep_ms(1000)

    except Exception as e:
        print(f"动画任务初始化失败: {e}")


def cb_progress(data):
    if isinstance(data, bytes):
        if data == b"/":
            display.portal_info("load iwconfig page    ")
        elif data == b"/login":
            display.portal_info("WiFi connecting ...   ")
    elif isinstance(data, str):
        display.message(data, 19, 204)

    if data:
        print(f"progress: {str(data)}")


def start():
    # 初始化液晶屏
    display.init_display(config.get("bl_mode") == "pwm", 7000)
    display.brightness(int(config.get("brightness", 10)))
    cb_progress("WiFi connect ...")

    if not wifi_manager.connect(cb_progress):
        gc.collect()
        from captive_portal import CaptivePortal

        portal = CaptivePortal()
        display.portal_win(portal.essid.decode("ascii"))
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
    naw.INDEX_FILE = "/rom/www/index.html"

    # Declare route from a dict
    naw.routes = {
        '/lcd': lcd_status,
        '/config': config_get,
        '/status': sys_status,
        '/exec': eval_cmd,
        '/lcd/set': lcd_set,
        '/config/set': config_update,
    }

    # create task
    loop = asyncio.get_event_loop()
    loop.create_task(naw.run())

    # 启动定时更新任务
    loop.create_task(sysinfo_update_task())

    # 启动动画显示任务
    loop.create_task(ui_task())

    gc.collect()
    print(f"success: {gc.mem_free()}...")

    # run!
    loop.run_forever()
