import main_memory
import decoder
import util
import logging
import peripheral

logger = logging.getLogger(__name__)

class CPU:
    '''
    Mem Address Map:
    4GB
    Reserve     500MB   0xffffffff
    Peripheral  500MB   0xe0000000
    main_memory 3GB     0xc0000000
    0GB
    '''
    XLEN = 32
    XMASK = 0xFFFFFFFF

    def __init__(self, main_m:main_memory.Memory) -> None:
        self.regs = REGS()
        self.main_m = main_m
        self.peripheral = peripheral.Peripheral()

    def run(self, step, noexec=False):
        while(step):
            step -= 1
            logger.debug(self.regs)
            cached_pc = self.regs.pc
            inst_value = util.LittleEndness.read32u(self, self.regs.pc)
            decoded_inst = decoder.decode(inst_value)
            if not noexec:
                decoded_inst.exec(self)
            if cached_pc == self.regs.pc:
                self.regs.pc += 4  # IS THIS RIGHT?
            else:
                # print(hex(self.regs.pc))
                pass

    def read(self, addr, length):
        if addr < 0xc0000000:
            return self.main_m.read(addr, length)
        if addr < 0xe0000000:
            return self.peripheral.read(addr, length)
        raise IndexError('read addr {} not valid'.format(addr))

    def write(self, addr, data):
        if addr < 0xc0000000:
            return self.main_m.write(addr, data)
        if addr < 0xe0000000:
            return self.peripheral.write(addr, data)
        raise IndexError('write addr {} not valid'.format(addr))

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
    def pc(self, value):
        self._pc = value&CPU.XMASK

    def __repr__(self) -> str:
        return "pc:{},x:{}".format(self._pc, self._x)
