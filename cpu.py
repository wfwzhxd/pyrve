from typing import Any
import addrspace
import memory
import decoder
import util
import logging
import functools

logger = logging.getLogger(__name__)

MTIME_BIT = 7
MIE_BIT = 3

class CPU:

    XLEN = 32
    XMASK = 0xFFFFFFFF

    def __init__(self, _addrspace:addrspace.AddrSpace) -> None:
        self.regs = REGS()
        self.csr = CSR()
        self._addrspace = _addrspace
        self.skip_step = 0

    def _go_mtrap(self, mcause):
        # MEPC=PC, MIE = 0, GO MTVEC
        logger.debug("go_mtrap, mcause: {}".format(hex(mcause)))
        self.csr.mcause = mcause
        self.csr.mepc = self.regs.pc
        self.csr.mstatus &= ~(1<<MIE_BIT)
        self.regs.pc = self.csr.mtvec&0xFFFFFFFC  # Only Direct Mode

    @functools.cache
    def _read_inst_value(self, pc):
        '''
            ASSERT TEXT CODE IS READONLY
        '''
        return self._addrspace.u32[pc]

    def run(self, step):
        while(step):
            self.skip_step += 1
            step -= 1
            logger.debug(self.regs)
            # logger.debug(self.csr)

            # exec inst
            cached_pc = self.regs.pc
            decoded_inst = decoder.decode(self._read_inst_value(self.regs.pc))
            decoded_inst.exec(self)
            if cached_pc == self.regs.pc:
                self.regs.pc += 4  # IS THIS RIGHT?

            if self.skip_step>>10:
                # mtime
                self._addrspace.u64[memory.MTIME_BASE] += self.skip_step
                mtime_pend = 1 if self._addrspace.u64[memory.MTIME_BASE] >= self._addrspace.u64[memory.MTIMECMP_BASE] else 0
                self.csr.mip = util.bit_set(self.csr.mip, MTIME_BIT, mtime_pend)
                # handle interrupt
                if util.get_bit(self.csr.mstatus, MIE_BIT): # MIE ENABLE
                    if util.get_bit(self.csr.mip, MTIME_BIT) and util.get_bit(self.csr.mie, MTIME_BIT): # TIMER
                        self._go_mtrap(0x80000007)
                self.skip_step = 0


class REGS(util.NamedArray):

    def __init__(self) -> None:
        super().__init__([0]*32, {'pc':0})

    def __getitem__(self, key):
        if 0 == key:
            return 0
        else:
            return super().__getitem__(key)

    def __setitem__(self, key, value):
        if key:
            super().__setitem__(key, value & 0xFFFFFFFF)

    def __setattr__(self, name: str, value: Any) -> None:
        if 'pc' == name:
            self._inner_array[0] = value & 0xFFFFFFFF
        else:
            super().__setattr__(name, value)


class CSR(util.NamedArray):

    ADDR_MAP = {
        'mstatus': 0x300,
        'mie': 0x304,
        'mtvec': 0x305,

        'mepc': 0x341,
        'mcause': 0x342,
        'mip': 0x344,

        'mhartid': 0xF14
    }

    def __init__(self) -> None:
        super().__init__([0]*4096, CSR.ADDR_MAP)
