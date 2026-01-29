import gc

import network
import ubinascii as binascii
import uselect as select
import utime as time
from captive_dns import DNSServer
from captive_http import HTTPServer
from config import config
from wifi_manager import wifi_manager


class CaptivePortal:
    AP_IP = "192.168.4.1"
    MAX_CONN_ATTEMPTS = 10

    def __init__(self, essid=None):
        self.local_ip = self.AP_IP
        self.ap_if = network.WLAN(network.AP_IF)

        if essid is None:
            essid = b"WS2-%s" % binascii.hexlify(self.ap_if.config("mac")[-3:])
        self.essid = essid

        self.dns_server = None
        self.http_server = None
        self.poller = select.poll()

    def start_access_point(self):
        # sometimes need to turn off AP before it will come up properly
        self.ap_if.active(False)
        while not self.ap_if.active():
            print("Waiting for access point to turn on")
            self.ap_if.active(True)
            time.sleep(1)
        # IP address, netmask, gateway, DNS
        self.ap_if.ifconfig(
            (self.local_ip, "255.255.255.0", self.local_ip, self.local_ip)
        )
        self.ap_if.config(essid=self.essid, authmode=network.AUTH_OPEN)
        print("AP mode configured:", self.ap_if.ifconfig())

    def connect_to_wifi(self):
        # 使用全局WiFiManager进行连接
        if wifi_manager.connect():
            self.local_ip = wifi_manager.get_ip()
            return True
        return False

    def check_valid_wifi(self, callback):
        if not wifi_manager.is_connected():
            if config.is_valid():
                # have credentials to connect, but not yet connected
                # return value based on whether the connection was successful
                return True
            # not connected, and no credentials to connect yet
            return False

        return True

    def captive_portal(self, callback):
        print("Starting captive portal")
        self.start_access_point()

        if self.http_server is None:
            self.http_server = HTTPServer(self.poller, self.local_ip)
            print("Configured HTTP server")
        if self.dns_server is None:
            self.dns_server = DNSServer(self.poller, self.local_ip)
            print("Configured DNS server")

        try:
            while True:
                gc.collect()
                # check for socket events and handle them
                for response in self.poller.ipoll(1000):
                    sock, event, *others = response
                    is_handled = self.handle_dns(sock, event, others)
                    if not is_handled:
                        callback(self.handle_http(sock, event, others))

                if self.check_valid_wifi(callback):
                    print("Connected to WiFi!")
                    self.http_server.stop(self.poller)
                    self.dns_server.stop(self.poller)
                    break

        except KeyboardInterrupt:
            print("Captive portal stopped")
        self.cleanup()
        return wifi_manager.is_connected()

    def handle_dns(self, sock, event, others):
        if sock is self.dns_server.sock:
            # ignore UDP socket hangups
            if event == select.POLLHUP:
                return True
            self.dns_server.handle(sock, event, others)
            return True
        return False

    def handle_http(self, sock, event, others):
        return self.http_server.handle(sock, event, others)

    def cleanup(self):
        print("Cleaning up")
        if self.ap_if.active():
            self.ap_if.active(False)
            print("Turned off access point")
        if self.dns_server:
            self.dns_server.stop(self.poller)
            self.dns_server = None
            print("Discard portal.dns_server")
        if self.http_server:
            self.http_server.stop(self.poller)
            self.http_server = None
            print("Discard portal.http_server")
        gc.collect()

    def try_connect_from_file(self):
        if config.is_valid():
            if self.connect_to_wifi():
                return True

        # WiFi Connection failed but keep credentials for future retries
        print("Connection failed but keeping configuration for retry")
        return False

    def start(self, callback):
        # turn off station interface to force a reconnect
        wifi_manager.disconnect()
        if not self.try_connect_from_file():
            return self.captive_portal(callback)
