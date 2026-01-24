import time

import network
from config import config


class WiFiManager:
    """WiFi连接管理类，负责处理WiFi连接相关功能"""

    MAX_CONN_ATTEMPTS = 12

    def __init__(self):
        self.sta_if = network.WLAN(network.STA_IF)
        self.config = config
        self._interface_initialized = False

    def _ensure_interface_active(self):
        """确保WLAN接口处于活动状态"""
        try:
            if not self.sta_if.active():
                self.sta_if.active(True)
                time.sleep(1)  # 等待接口激活
            self._interface_initialized = True
            return True
        except Exception as e:
            print(f"激活WiFi接口失败: {e}")
            return False

    def _safe_connect_check(self):
        """安全地检查连接状态"""
        try:
            return self.sta_if.isconnected()
        except:
            return False

    def is_connected(self):
        """检查是否已连接到WiFi"""
        if not self._interface_initialized:
            return False
        return self._safe_connect_check()

    def get_ip(self):
        """获取当前IP地址"""
        if self.is_connected():
            try:
                return self.sta_if.ifconfig()[0]
            except:
                return None
        return None

    def connect(self):
        """尝试连接到WiFi"""
        # 加载配置
        if not self.config.load().is_valid():
            print("没有有效的WiFi配置")
            return False

        ssid = self.config.get("ssid")
        password = self.config.get("password")

        if not ssid or not password:
            print("SSID或密码为空")
            return False

        print(f"正在尝试连接到SSID: {ssid}")

        try:
            # 确保接口处于活动状态
            if not self._ensure_interface_active():
                return False

            # 如果已经连接，先断开
            if self._safe_connect_check():
                self.sta_if.disconnect()
                time.sleep(1)

            # 执行连接
            self.sta_if.connect(ssid, password)

            # 等待连接完成
            attempts = 1
            while attempts <= self.MAX_CONN_ATTEMPTS:
                if self._safe_connect_check():
                    ip = self.get_ip()
                    if ip:
                        print(f"连接成功! IP: {ip}")
                        return True

                print(f"连接尝试 {attempts}/{self.MAX_CONN_ATTEMPTS}...")
                time.sleep(2)
                attempts += 1

            # 连接失败
            print(f"连接失败: {ssid}")
            self.clear_config()
            try:
                print(f"WLAN状态: {self.sta_if.status()}")
            except:
                pass
            return False

        except Exception as e:
            print(f"连接过程中发生错误: {e}")
            return False

    def disconnect(self):
        """断开WiFi连接"""
        try:
            if self._safe_connect_check():
                self.sta_if.disconnect()
                time.sleep(1)
            print("已断开WiFi连接")
        except Exception as e:
            print(f"断开连接时出错: {e}")

    def scan_networks(self):
        """扫描可用的WiFi网络"""
        try:
            # 确保接口处于活动状态
            if not self._ensure_interface_active():
                return []

            # 如果已连接，先断开
            if self._safe_connect_check():
                self.sta_if.disconnect()
                time.sleep(1)

            # 执行扫描
            networks = self.sta_if.scan()

            # 处理结果
            result = []
            for net in networks:
                try:
                    ssid = net[0].decode("utf-8", "ignore")
                    if ssid:  # 只添加非隐藏网络
                        result.append({"ssid": ssid, "rssi": net[3]})
                except:
                    continue  # 跳过有问题的网络

            return result
        except Exception as e:
            print(f"扫描WiFi网络时出错: {e}")
            return []

    def reset(self):
        """重置WiFi配置"""
        try:
            self.config.remove()
            print("WiFi配置已重置")
        except Exception as e:
            print(f"重置配置时出错: {e}")

    def clear_config(self):
        """清除WiFi配置（可选操作）"""
        try:
            self.config.set("ssid", None)
            print("WiFi配置已临时清空")
        except Exception as e:
            print(f"清除配置时出错: {e}")


# 全局WiFi管理器实例
wifi_manager = WiFiManager()
