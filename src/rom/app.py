# ESP8266天气站主程序
# 首先尝试连接已保存的WiFi，失败则启动CaptivePortal进行配置

import gc
import sys
import time

import json
import machine

from wifi_manager import wifi_manager


def print_sysinfo():
    gc.collect()
    print(f'Memory Free: {gc.mem_free()}')

def start():
    if not wifi_manager.connect():
        print("Failed to connect to WiFi, starting CaptivePortal for configuration")
        from captive_portal import CaptivePortal
        portal = CaptivePortal()
        return portal.start()

    # init web server
    from rom.nanoweb import Nanoweb
    naw = Nanoweb()
    # website top directory  
    naw.STATIC_DIR = '/rom/www'

    # /ping: pong
    @naw.route('/ping')
    async def ping(request):
        await request.write("HTTP/1.1 200 OK\r\n")
        await request.write("Content-Type: text\r\n\r\n")
        await request.write("pong")

    # /status
    @naw.route('/status')
    async def ping(request):
        await request.write("HTTP/1.1 200 OK\r\n")
        await request.write("Content-Type: application/json\r\n\r\n")
        await request.write(json.dumps({
            'time':'{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'.format(*time.localtime()),
            'uptime': str(f'{time.ticks_ms()//1000} sec'),
            'memory': str(f'{gc.mem_free()//1000} KB'),
            'platform': str(sys.platform),
            'version': str(sys.version),
        }))

    # create task
    import uasyncio
    loop = uasyncio.get_event_loop()
    loop.create_task(naw.run())

    # run!
    print_sysinfo()
    loop.run_forever()
