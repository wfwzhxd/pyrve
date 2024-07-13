import addrspace
import peripheral
import logging

PHYMEM_BASE = 0x80000000
CLINET_BASE = 0x2000000 #0x11000000
MTIME_BASE = CLINET_BASE + 0xbff8
MTIMECMP_BASE = CLINET_BASE + 0x4000

class Memory1(addrspace.BufferAddrSpace):
    
    def __init__(self, phy_size=1024*1024) -> None:
        super().__init__(0, 0xFFFFFFFF, 'memory', True)
        
        # ctrl = Ctrl(0x123, 0x123, 'ctrl', False)

    def read(self, addr, length):
        logging.debug('read addr {}'.format(hex(addr)))
        if addr >= 0x10000000 and addr <= 0x10000100:
            return bytes([0xFF])
        result = self.mem[addr: addr+length]
        logging.debug(result.hex())
        return result
    
    def write(self, addr, data):
        logging.debug('write addr {}'.format(hex(addr)))
        logging.debug(data.hex())
        if 0x10000000 == addr:
            sys.stdout.write(chr(data[0]))
            sys.stdout.flush()
        if 0x123 == addr:
            save_signature()
        else:
            self.mem[addr: addr+len(data)] = data


class Memory2(addrspace.BufferAddrSpace):
    
    def __init__(self, phy_size=1024*1024) -> None:
        super().__init__(0, 0xFFFFFFFF, 'memory', False)
        phy_mem = addrspace.BufferAddrSpace(PHYMEM_BASE, PHYMEM_BASE+phy_size-1, 'phy_mem', True)
        # mtime = addrspace.BufferAddrSpace(MTIME_BASE, MTIME_BASE+7, 'mtime', True)
        # mtimecmp = addrspace.BufferAddrSpace(MTIMECMP_BASE, MTIMECMP_BASE+7, 'mtimecmp', True)
        clint = addrspace.BufferAddrSpace(CLINET_BASE, CLINET_BASE+0x10000-1, 'clint', True)
        uart = peripheral.UART_8250()
        ctrl = Ctrl(0x123, 0x123, 'ctrl', False)
        self.sub_space.extend([phy_mem, clint, uart, ctrl])

class Memory3(addrspace.AddrSpace):

    def __init__(self, phy_size=1024*1024) -> None:
        super().__init__(0, 0xFFFFFFFF, 'memory', False)
        self.phy_mem = memoryview(bytearray(phy_size))
        self.clint_mem = memoryview(bytearray(0x10000))
        self.uart = peripheral.UART_8250()

    def read(self, addr, length):
        if addr >= PHYMEM_BASE:
            offset = addr - PHYMEM_BASE
            return self.phy_mem[offset: offset + length]
        if addr >= CLINET_BASE and addr < CLINET_BASE+0x10000:
            offset = addr - CLINET_BASE
            return self.clint_mem[offset: offset + length]
        return self.uart.read(addr, length)

    def write(self, addr, data):
        length = len(data)
        if addr >= PHYMEM_BASE:
            offset = addr - PHYMEM_BASE
            self.phy_mem[offset: offset + length] = data
            return
        if addr >= CLINET_BASE and addr < CLINET_BASE+0x10000:
            offset = addr - CLINET_BASE
            # print("{} {} {}".format(offset, offset + length, data))
            self.clint_mem[offset: offset + length] = data
            return
        return self.uart.write(addr, data)


import sys


def _dump_signature(buf, line_size):
    lines = []
    while buf:
        cur_line, buf = buf[:line_size], buf[line_size:]
        cur_line += bytes([0]*(line_size-len(cur_line)))
        lines.append(cur_line[::-1].hex())
    return '\n'.join(lines) + '\n'


def save_signature():
    import __main__ as cof
    with open(sys.argv[2], 'wt') as f:
        start_sig = int(sys.argv[3], 16)
        end_sig = int(sys.argv[4], 16)
        sigstr = _dump_signature(cof.global_cpu._addrspace.read(start_sig, end_sig-start_sig), 4)
        f.write(sigstr)
    sys.exit()

class Ctrl(addrspace.ByteAddrSpace):

    def __init__(self, start, end, name=None, init_mem=False) -> None:
        super().__init__(start, end, name, init_mem)

    @staticmethod
    def dump(buf, line_size):
        lines = []
        while buf:
            cur_line, buf = buf[:line_size], buf[line_size:]
            cur_line += bytes([0]*(line_size-len(cur_line)))
            lines.append(cur_line[::-1].hex())
        return '\n'.join(lines) + '\n'

    def write_byte(self, addr, value):
        import __main__ as cof
        import logging
        logging.error(cof)
        logging.error(cof.__dict__)
        cof.fuck()
        with open(sys.argv[2], 'wt') as f:
            start_sig = int(sys.argv[3], 16)
            end_sig = int(sys.argv[4], 16)
            logging.error(start_sig)
            logging.error(end_sig)
            sigstr = Ctrl.dump(cof.global_cpu._addrspace.read(start_sig, end_sig-start_sig), 4)
            logging.error(sigstr)
            f.write(sigstr)
        sys.exit()
