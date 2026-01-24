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


# 定时获取天气数据的任务
async def weather_update_task():
    """定时更新天气数据的后台任务"""

    # 获取更新间隔，默认10分钟
    interval_minutes = config.get("weather_interval", 10)
    interval_ms = interval_minutes * 60 * 1000  # 转换为毫秒

    print(f"开始定时更新天气数据，间隔{interval_minutes}分钟")
    await uasyncio.sleep_ms(1 * 1000)

    while True:
        try:
            # 定期更新天气数据缓存
            weather = get_weather_data()
            if weather:
                print("天气数据缓存已更新")

            # 等待指定的间隔时间
            await uasyncio.sleep_ms(interval_ms)

        except Exception as e:
            print(f"天气更新任务出错: {e}")
            # 出错后等待1分钟再重试
            await uasyncio.sleep_ms(60 * 1000)


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
        frame_delay = 10  # 帧延迟(毫秒)

        await uasyncio.sleep_ms(2 * 1000)
        print(f"开始JPG动画，帧延迟: {frame_delay}ms")

        frame = 0
        while True:
            try:
                # 计算当前帧号(1-20)
                current_frame = (frame % frame_count) + 1
                filename = f"/rom/www/images/T{current_frame}.jpg"

                # 显示当前帧，右下角
                display.show_jpg(filename, 160, 160)

                # 控制帧率
                await uasyncio.sleep_ms(frame_delay)

                # 每轮清理一次内存
                gc.collect()
                if current_frame == frame_count:
                    # gc.collect()
                    print(f"Memory: {gc.mem_free()}")

                frame += 1

            except Exception as e:
                print(f"动画帧错误: {e}")
                # 出错后等待1秒再继续
                await uasyncio.sleep_ms(1000)

    except Exception as e:
        print(f"动画任务初始化失败: {e}")


def start():
    # 初始化液晶屏
    display.init_display()
    display.show_jpg("/rom/www/images/T1.jpg", 80, 80)
    gc.collect()

    if not wifi_manager.connect():
        print("Failed to connect to WiFi, starting CaptivePortal for configuration")
        from captive_portal import CaptivePortal

        portal = CaptivePortal()
        return portal.start()
    gc.collect()

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
            "ui_type": config.get("ui_type", "default"),
        }
        await request.write(json.dumps(lcd_status))

    # /lcd/set: 设置LCD状态
    @naw.route("/lcd/set")
    async def lcd_set(request):
        ack = {"status": "success"}
        try:
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

    # 启动定时天气更新任务
    loop.create_task(weather_update_task())

    # 启动动画显示任务
    loop.create_task(animation_task())

    # run!
    gc.collect()
    print(f"App Memory Free: {gc.mem_free()}")
    loop.run_forever()
