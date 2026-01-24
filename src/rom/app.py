# ESP8266天气站主程序
# 首先尝试连接已保存的WiFi，失败则启动CaptivePortal进行配置

import gc
import sys
import time

import machine

# 使用全局的WiFiManager实例
from wifi_manager import wifi_manager

print("Trying to connect to saved WiFi network...")

if wifi_manager.connect():
    # 连接成功
    ip = wifi_manager.get_ip()
    print(f"WiFi connected successfully, IP address: {ip}")

    # 在这里可以添加主应用程序代码
    # 例如：启动天气数据获取和显示
    print("Starting main application...")

    # 示例：保持连接
    try:
        while True:
            # 检查连接状态
            if not wifi_manager.is_connected():
                print("WiFi connection lost")
                break

            # 每3秒报告一次状态
            time.sleep(3)
            gc.collect()
            print(f"Running normally, IP: {ip}, Free memory: {gc.mem_free()} bytes")

    except KeyboardInterrupt:
        print("User interrupted")

    finally:
        wifi_manager.disconnect()
        print("Application ended")

else:
    # 连接失败，启动CaptivePortal进行WiFi配置
    print("Failed to connect to WiFi, starting CaptivePortal for configuration")

    from captive_portal import CaptivePortal

    # 启动CaptivePortal
    portal = CaptivePortal()

    try:
        if portal.start():
            # clear
            del portal
            sys.modules.pop("CaptivePortal", None)
            sys.modules.pop("captive_dns", None)
            sys.modules.pop("captive_http", None)
            sys.modules.pop("server_base", None)
            gc.collect()
            # CaptivePortal成功配置并连接
            print("WiFi configured successfully and connected")

            # 在这里可以添加主应用程序代码
            print("Starting main application...")

            # 示例：保持连接
            try:
                while True:
                    # 检查连接状态
                    if not wifi_manager.is_connected():
                        print("WiFi connection lost")
                        break

                    # 每3秒报告一次状态
                    time.sleep(3)
                    gc.collect()
                    print(f"Running normally, Free memory: {gc.mem_free()} bytes")

            except KeyboardInterrupt:
                print("User interrupted")

            finally:
                wifi_manager.disconnect()
                print("Application ended")
        else:
            print("CaptivePortal failed to establish connection")

    except KeyboardInterrupt:
        print("User interrupted")

    finally:
        time.sleep(3)
        machine.reset()
