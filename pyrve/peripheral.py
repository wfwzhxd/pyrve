from . import addrspace
import logging
import queue
import threading
import socketserver
import socket

logger = logging.getLogger(__name__)


class UART_8250(addrspace.ByteAddrSpace):

    BUFFER_SIZE = 10 * 1024

    def __init__(self, base, host="127.0.0.1", port=8250) -> None:
        super().__init__(
            base, 0x100, "uart_8250@{}[({}, {})]".format(hex(base), host, port), False
        )
        self.read_queue = queue.Queue(UART_8250.BUFFER_SIZE)
        self.write_queue = queue.Queue(UART_8250.BUFFER_SIZE)
        self.rw_event = threading.Event()
        self.server = socketserver.ThreadingTCPServer(
            (host, port), self._socket_handler, bind_and_activate=False
        )
        self.server.allow_reuse_address = True
        self.server.allow_reuse_port = True
        self.server.server_bind()
        self.server.server_activate()
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.client_id = 0

    def _socket_handler(self, request: socket.socket, client_address, server):
        self.client_id += 1
        my_client_id = self.client_id
        request.settimeout(0.01)
        MAX_HANDLED = 1024
        while True:
            if my_client_id != self.client_id:
                return
            # read
            try:
                readed = request.recv(MAX_HANDLED)
                if readed:
                    for r in readed:
                        self.read_queue.put_nowait(r)
            except (socket.timeout, queue.Full):
                pass
            # write
            sent = 0
            while sent < MAX_HANDLED and self.write_queue.qsize() > 0:
                try:
                    write_char = self.write_queue.get_nowait()
                    request.send(bytes([write_char]))
                    sent += 1
                except (socket.timeout, queue.Empty):
                    pass
            if self.write_queue.qsize() == 0:
                self.rw_event.wait(2)
                self.rw_event.clear()

    def read_byte(self, addr):
        self.rw_event.set()
        result = 0
        if 0x10000005 == addr:
            result = 0x60 | (1 if self.read_queue.qsize() != 0 else 0)
        if 0x10000000 == addr and self.read_queue.qsize() != 0:
            try:
                result = self.read_queue.get_nowait()
            except queue.Empty:
                pass
        return result

    def write_byte(self, addr, value):
        if 0x10000000 == addr:
            try:
                self.write_queue.put_nowait(value)
                self.rw_event.set()
            except queue.Full:
                pass
