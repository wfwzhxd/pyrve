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
        self.csr.mstatus = util.clear_bit(self.csr.mstatus, MIE_BIT)
        self.regs.pc = self.csr.mtvec&0xFFFFFFFC  # Only Direct Mode

    @functools.cache
    def _read_inst_value(self, pc):
        '''
            ASSERT TEXT CODE IS READONLY
        '''
        return util.LittleEndness.read32u(self._addrspace, pc)

    def run(self, step):
        while(step):
            self.skip_step += 1
            step -= 1
            logger.debug(self.regs)
            logger.debug(self.csr)

            # exec inst
            cached_pc = self.regs.pc
            decoded_inst = decoder.decode(self._read_inst_value(self.regs.pc))
            decoded_inst.exec(self)
            if cached_pc == self.regs.pc:
                self.regs.pc += 4  # IS THIS RIGHT?

            if self.skip_step>>10:
                # mtime
                mtime = util.LittleEndness.read64u(self._addrspace, memory.MTIME_BASE) + self.skip_step
                mtimecmp = util.LittleEndness.read64u(self._addrspace, memory.MTIMECMP_BASE)
                util.LittleEndness.write64u(self._addrspace, memory.MTIME_BASE, mtime)
                mtime_pend = 1 if mtime >= mtimecmp else 0
                self.csr.mip = util.bit_set(self.csr.mip, MTIME_BIT, mtime_pend)
                # handle interrupt
                if util.get_bit(self.csr.mstatus, MIE_BIT): # MIE ENABLE
                    if util.get_bit(self.csr.mip, MTIME_BIT) and util.get_bit(self.csr.mie, MTIME_BIT): # TIMER
                        self._go_mtrap(0x80000007)
                self.skip_step = 0


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
        return "pc:{},x:{}".format(hex(self._pc), [*map(hex,self._x)])


class CSR:

    ADDR_MAP = {
        0x300: 'mstatus',
        0x304: 'mie',
        0x305: 'mtvec',

        0x341: 'mepc',
        0x342: 'mcause',
        0x344: 'mip',

        0xF14: 'mhartid'
    }

    def __init__(self) -> None:
        self.mstatus = 0
        self.mie = 0
        self.mtvec = 0
        self.mepc = 0
        self.mcause = 0
        self.mip = 0
        self.mhartid = 0

    def read(self, addr):
        name = CSR.ADDR_MAP.get(addr)
        return getattr(self, name)

    def write(self, addr, value):
        name = CSR.ADDR_MAP.get(addr)
        setattr(self, name, value)

    def __repr__(self) -> str:
        return "CSR({})".format(self.__dict__)
