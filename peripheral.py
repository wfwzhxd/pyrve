import addrspace
import sys
import logging

logger = logging.getLogger(__name__)

class UART(addrspace.ByteAddrSpace):

    def __init__(self) -> None:
        super().__init__(0x10000000, 0x10000100, 'uart', False)
        self.uart_in_buf = bytearray()

    def read_byte(self, addr):
        # if 0xc0001000 == addr:
        #     return ord(sys.stdin.read(1))&0xFF
        return 0xFF

    def write_byte(self, addr, value):
        if 0x10000000 == addr:
            sys.stdout.write(chr(value))
            sys.stdout.flush()
