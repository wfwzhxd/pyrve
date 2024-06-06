import main_memory
import decoder
import util

class CPU:

    XLEN = 32
    XMASK = 0xFFFFFFFF

    def __init__(self, main_m:main_memory.Memory) -> None:
        self.regs = REGS()
        self.main_m = main_m

    def run(self, step):
        while(step):
            cached_pc = self.regs.pc
            inst_value = util.LittleEndness.read32u(self.main_m, self.regs.pc)
            decoded_inst = decoder.decode(inst_value)
            decoded_inst.exec(self)
            if cached_pc == self.regs.pc:
                self.regs.pc += 4  # IS THIS RIGHT?
        step -= 1


class REGS:

    def __init__(self) -> None:
        self._pc = 0
        self._x = [0] * 32

    def get_x(self, idx):
        if idx:
            return self._x[idx]
        return 0
    
    def set_x(self, idx, value):
        if idx:
            self._x[idx] = value&CPU.XMASK

    @property
    def pc(self):
        return self._pc
    
    @pc.setter
    def set_pc(self, value):
        self._pc = value&CPU.XMASK

    def __repr__(self) -> str:
        return "pc:{},x:{}".format(self._pc, self._x)
