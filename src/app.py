# ESP8266天气站主程序
# 首先尝试连接已保存的WiFi，失败则启动CaptivePortal进行配置

import gc, time, sys, machine

# 使用全局的WiFiManager实例
from wifi_manager import wifi_manager



print("尝试连接已保存的WiFi网络...")

if wifi_manager.connect():
    # 连接成功
    ip = wifi_manager.get_ip()
    print(f"WiFi连接成功，IP地址: {ip}")

    # 在这里可以添加主应用程序代码
    # 例如：启动天气数据获取和显示
    print("启动主应用程序...")

    # 示例：保持连接
    try:
        while True:
            # 检查连接状态
            if not wifi_manager.is_connected():
                print("WiFi连接断开")
                break

            # 每3秒报告一次状态
            time.sleep(3)
            gc.collect()
            print(f"正常运行中，IP: {ip}, 可用内存: {gc.mem_free()} bytes")

    except KeyboardInterrupt:
        print("用户中断")

    finally:
        wifi_manager.disconnect()
        print("应用程序结束")

else:
    # 连接失败，启动CaptivePortal进行WiFi配置
    print("无法连接到WiFi，启动CaptivePortal进行配置")

    from captive_portal import CaptivePortal

    # 启动CaptivePortal
    portal = CaptivePortal()

    try:
        if portal.start():
            # clear
            del portal
            sys.modules.pop('CaptivePortal', None)
            sys.modules.pop('captive_dns', None)
            sys.modules.pop('captive_http', None)
            sys.modules.pop('server_base', None)
            gc.collect()
            # CaptivePortal成功配置并连接
            print("WiFi配置成功并已连接")

            # 在这里可以添加主应用程序代码
            print("启动主应用程序...")

            # 示例：保持连接
            try:
                while True:
                    # 检查连接状态
                    if not wifi_manager.is_connected():
                        print("WiFi连接断开")
                        break

                    # 每3秒报告一次状态
                    time.sleep(3)
                    gc.collect()
                    print(f"正常运行中，可用内存: {gc.mem_free()} bytes")

            except KeyboardInterrupt:
                print("用户中断")

            finally:
                wifi_manager.disconnect()
                print("应用程序结束")
        else:
            print("CaptivePortal未能成功建立连接")

    except KeyboardInterrupt:
        print("用户中断")

    finally:
        time.sleep(3)
        machine.reset()
