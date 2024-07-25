from . import addrspace
from . import peripheral
from . import cpu
from . import util
import threading
import sys
import pathlib


#           (base, size, name)
PHYMEM = (0x80000000, 0x04000000, "phy_mem")  # 64MB
FLASH = (0x20000000, 0x04000000, "flash")  # 64MB
UART0 = (0x10000000, 0x00000100, "uart0")
CLINT = (0x02000000, 0x00010000, "clint")


class Memory(addrspace.BufferAddrSpace):

    def __init__(self) -> None:
        super().__init__(0, 0xFFFFFFFF, "memory", False)
        for memcfg in (PHYMEM, FLASH, CLINT):
            self.sub_space.append(addrspace.BufferAddrSpace(*memcfg, True))
        self.sub_space.append(peripheral.UART_8250(UART0[0]))


class Emulator:

    def __init__(self) -> None:
        self.memory = Memory()
        self._cpu = cpu.CPU(self.memory, CLINT[0])
        self._cpu.pc = PHYMEM[0]
        self.running = False

    def load_linux(self, kernel, rootfs):
        self.memory.write(PHYMEM[0], util.load_binary(kernel))
        self.memory.write(FLASH[0], util.load_binary(rootfs))

    def start(self):
        if self.running:
            return
        self.running = True

        def _run():
            print("started")
            while self.running:
                self._cpu.run(1e6)
            print("stoped")

        threading.Thread(target=_run, daemon=True).start()

    def stop(self):
        self.running = False


def main():
    pwd = pathlib.Path(__file__).parent.parent
    kernel = pathlib.Path(pwd, "lib/images/kernel_sbi.bin")
    rootfs = pathlib.Path(pwd, "lib/images/rootfs.ext2")
    rve = Emulator()
    rve.load_linux(kernel, rootfs)
    if len(sys.argv) == 1:  # no arg
        util.run_forever(rve._cpu)
    else:
        import IPython

        IPython.embed()


if __name__ == "__main__":
    main()
