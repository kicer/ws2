import select
import socket


class BaseServer:
    """基础服务器类，为HTTP和DNS服务器提供通用功能"""

    def __init__(self, poller, port, sock_type, name):
        self.name = name
        # create socket with correct type: stream (TCP) or datagram (UDP)
        self.sock = socket.socket(socket.AF_INET, sock_type)

        # register to get event updates for this socket
        self.poller = poller
        self.poller.register(self.sock, select.POLLIN)

        addr = socket.getaddrinfo("0.0.0.0", port)[0][-1]
        # allow new requests while still sending last response
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(addr)

        print(self.name, "listening on", addr)

    def stop(self, poller):
        poller.unregister(self.sock)
        self.sock.close()
        print(self.name, "stopped")
