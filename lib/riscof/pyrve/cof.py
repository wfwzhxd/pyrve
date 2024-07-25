import pyrve.cpu as cpu
import pyrve.addrspace as addrspace
import pyrve.util as util
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)s: %(message)s",
    filename="main.log",
    filemode="wt",
)


#           (base, size, name)
PHYMEM = (0x80000000, 0x04000000, "phy_mem")
CLINT = (0x02000000, 0x00010000, "clint")


class Memory(addrspace.BufferAddrSpace):

    def __init__(self) -> None:
        super().__init__(0, 0xFFFFFFFF, "memory", False)
        for memcfg in (PHYMEM, CLINT):
            self.sub_space.append(addrspace.BufferAddrSpace(*memcfg, True))
        ctrl = Ctrl(0x123, 0x123, "ctrl", False)
        self.sub_space.append(ctrl)


memory = Memory()


class Ctrl(addrspace.ByteAddrSpace):

    def __init__(self, base, size, name=None, init_mem=False) -> None:
        super().__init__(base, size, name, init_mem)

    @staticmethod
    def dump(buf, line_size):
        lines = []
        while buf:
            cur_line, buf = buf[:line_size], buf[line_size:]
            cur_line += bytes([0] * (line_size - len(cur_line)))
            lines.append(cur_line[::-1].hex())
        return "\n".join(lines) + "\n"

    def write_byte(self, addr, value):
        with open(sys.argv[2], "wt") as f:
            start_sig = int(sys.argv[3], 16)
            end_sig = int(sys.argv[4], 16)
            sigstr = Ctrl.dump(memory.read(start_sig, end_sig - start_sig), 4)
            logging.error(sigstr)
            f.write(sigstr)
        sys.exit()


def main():
    _cpu = cpu.CPU(memory, CLINT[0])
    util.run_forever(_cpu)


if __name__ == "__main__":
    main()
