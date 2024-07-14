
import addrspace
import peripheral
import cpu
import threading

#           (base, size, name)
PHYMEM =    (0x80000000, 0x04000000, 'phy_mem')    # 64MB
FLASH =     (0x20000000, 0x04000000, 'flash')     # 64MB
UART0 =     (0x10000000, 0x00000100, 'uart0')
CLINT =     (0x02000000, 0x00010000, 'clint')


class Memory(addrspace.BufferAddrSpace):

    def __init__(self) -> None:
        super().__init__(0, 0xFFFFFFFF, 'memory', False)
        for memcfg in (PHYMEM, FLASH, CLINT):
            self.sub_space.append(addrspace.BufferAddrSpace(*memcfg, True))
        self.sub_space.append(peripheral.UART_8250(UART0[0]))


def load_binary(fname):
    with open(fname, 'rb') as f:
        return f.read()


class Emulator:

    def __init__(self) -> None:
        self.memory = Memory()
        self._cpu = cpu.CPU(self.memory, CLINT[0])
        self._cpu.regs.pc = PHYMEM[0]
        self.running = False

    def load_linux(self, kernel, rootfs):
        self.memory.write(PHYMEM[0], load_binary(kernel))
        self.memory.write(FLASH[0], load_binary(rootfs))

    def run(self):
        if self.running:
            return
        self.running = True
        def _run():
            print('started')
            while self.running:
                self._cpu.run(1E6)
            print('stoped')
        threading.Thread(target=_run, daemon=True).start()

    def stop(self):
        self.running = False


def main():
    kernel = '/home/hu2/opensbi/build/platform/pyrve/firmware/fw_payload.bin'
    rootfs = '/media/hu2/deepin/buildroot-2024.02.3/output/images/rootfs.ext2'
    rve = Emulator()
    rve.load_linux(kernel, rootfs)
    import IPython
    IPython.embed()


if __name__ == '__main__':
    main()
