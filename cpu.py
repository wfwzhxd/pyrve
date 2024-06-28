from typing import Any
import addrspace
import memory
import decoder
import util
import logging
import functools

logger = logging.getLogger(__name__)


class CPU:

    XLEN = 32
    XMASK = 0xFFFFFFFF

    def __init__(self, _addrspace:addrspace.AddrSpace) -> None:
        self.regs = REGS()
        self.csr = CSR()
        self._addrspace = _addrspace
        self.skip_step = 0
        self.mode = 0b11

    def _go_mtrap(self, mcause):
        logger.debug("go_mtrap, mode: {}, mcause {}".format(bin(self.mode), hex(mcause)))
        self.csr.mcause = mcause
        self.csr.mepc = self.regs.pc
        self.csr.mstatus.MPIE = self.csr.mstatus.MIE
        self.csr.mstatus.MIE = 0
        self.csr.mstatus.MPP = self.mode
        self.csr.mtval = 0
        self.regs.pc = self.csr.mtvec&0xFFFFFFFC  # Only Direct Mode

    # @functools.cache
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
            logger.debug(decoded_inst)
            decoded_inst.exec(self)
            if cached_pc == self.regs.pc:
                self.regs.pc += 4  # IS THIS RIGHT?

            if self.skip_step>>10:
                # mtime
                self._addrspace.u64[memory.MTIME_BASE] += self.skip_step
                mtime_pend = 1 if self._addrspace.u64[memory.MTIME_BASE] >= self._addrspace.u64[memory.MTIMECMP_BASE] else 0
                self.csr.mip.MTIP = mtime_pend
                # handle interrupt
                if self.csr.mstatus.MIE: # MIE ENABLE
                    if self.csr.mip.MTIP and self.csr.mie.MTIE: # TIMER
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
        'mtval': 0x343,
        'mip': 0x344,

        'mhartid': 0xF14
    }

    MSTATUS_BITMAP = {
        'MIE': (3, 3, 0),
        'MPIE': (7, 7, 0),
        'MPP': (11, 12, 0b11)
    }

    MIE_BITMAP = {
        'MTIE': (7, 7, 0)
    }

    MIP_BITMAP = {
        'MTIP': (7, 7, 0)
    }

    def __init__(self) -> None:
        super().__init__([0]*4096, CSR.ADDR_MAP)
        setattr(self, 'mstatus', util.bit_container('mstatus', CSR.MSTATUS_BITMAP)())
        setattr(self, 'mie', util.bit_container('mie', CSR.MIE_BITMAP)())
        setattr(self, 'mip', util.bit_container('mip', CSR.MIP_BITMAP)())

    def __getitem__(self, key):
        return int(self._inner_array[key])
    
    def __setitem__(self, key, value):
        if type(self._inner_array[key]) == int:
            self._inner_array[key] = value
        else:   # bit_container
            self._inner_array[key]._value = value

    def __repr__(self) -> str:
        return self.__class__.__name__ + ": " + '[{}]'.format(', '.join(hex(int(x)) for x in self._inner_array))
