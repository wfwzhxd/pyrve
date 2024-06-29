from typing import Any
import addrspace
import memory
import decoder
import util
import logging
import functools

logger = logging.getLogger(__name__)

MODE_U = 0b00
MODE_S = 0b01
MODE_M = 0b11

INTERRUPT_TIMER_S = 0x80000005
INTERRUPT_TIMER_M = 0x80000007

EXCEPTION_ECALL_FROM_U = 8
EXCEPTION_ECALL_FROM_S = 9
EXCEPTION_ECALL_FROM_M = 11

EXCEPTION_INST_PAGE_FAULT = 12
EXCEPTION_LOAD_PAGE_FAULT = 13
EXCEPTION_STORE_AMO_PAGE_FAULT = 15


class CPU:

    XLEN = 32
    XMASK = 0xFFFFFFFF

    def __init__(self, _addrspace:addrspace.AddrSpace) -> None:
        self.regs = REGS()
        self.csr = CSR()
        self._addrspace = MMU(self, _addrspace)
        self.skip_step = 0
        self.mode = MODE_M

    def _go_mtrap(self, mcause, mtval=0):
        logger.debug("go_mtrap, mode: {}, mcause {}".format(bin(self.mode), hex(mcause)))
        self.csr.mcause = mcause
        self.csr.mepc = self.regs.pc
        self.csr.mstatus.MPIE = self.csr.mstatus.MIE
        self.csr.mstatus.MIE = 0
        self.csr.mstatus.MPP = self.mode
        self.mode = MODE_M
        self.csr.mtval = mtval
        self.regs.pc = self.csr.mtvec&0xFFFFFFFC  # Only Direct Mode

    def _go_strap(self, scause, stval=0):
        logger.debug("go_strap, mode: {}, scause {}".format(bin(self.mode), hex(scause)))
        self.csr.scause = scause
        self.csr.sepc = self.regs.pc
        self.csr.sstatus.SPIE = self.csr.sstatus.SIE
        self.csr.sstatus.SIE = 0
        self.csr.sstatus.SPP = self.mode
        self.mode = MODE_S
        self.csr.stval = stval
        self.regs.pc = self.csr.stvec&0xFFFFFFFC  # Only Direct Mode

    def _go_trap(self, cause, tval=0):
        if cause>>31:   # msb=1, interrupt
            if util.get_bit(self.csr.mideleg, cause&0x7FFFFFFF):
                if MODE_M == self.mode:
                    logger.warn('interrupt cause[{}] is deleg, but current in M mode, just return'.format(cause))
                    return
                self._go_strap(cause, tval)
            else:
                self._go_mtrap(cause, tval)
        else:   # exception
            if util.get_bit(self.csr.medeleg, cause):   # not support medelegh
                self._go_strap(cause, tval)
            else:
                self._go_mtrap(cause, tval)

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
            try:
                decoded_inst = decoder.decode(self._read_inst_value(self.regs.pc))
            except MMU.PageFaultException as e:
                self._go_trap(EXCEPTION_INST_PAGE_FAULT, e.vaddr)
                continue

            logger.debug(decoded_inst)

            try:
                decoded_inst.exec(self)
            except MMU.PageFaultException as e:
                if isinstance(e, MMU.LoadPageFault):
                    cause = EXCEPTION_LOAD_PAGE_FAULT
                else:
                    cause = EXCEPTION_STORE_AMO_PAGE_FAULT
                self._go_trap(cause, e.vaddr)
                continue
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
                        self._go_trap(INTERRUPT_TIMER_M)
                self.skip_step = 0

                if MODE_U == self.mode or (MODE_S == self.mode and self.csr.sstatus.SIE):
                    if self.csr.sip.STIP and self.csr.sie.STIE: # TIMER
                        self._go_trap(INTERRUPT_TIMER_S)

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
        'sstatus': 0x100,
        'sie': 0x104,
        'stvec': 0x105,

        'sepc': 0x141,
        'scause': 0x142,
        'stval': 0x143,
        'sip': 0x144,

        'satp': 0x180,

        'mstatus': 0x300,
        'medeleg': 0x302,
        'mideleg': 0x303,
        'mie': 0x304,
        'mtvec': 0x305,
        'medelegh': 0x312,

        'mepc': 0x341,
        'mcause': 0x342,
        'mtval': 0x343,
        'mip': 0x344,

        'mhartid': 0xF14
    }

    MSTATUS_BITMAP = {
        'SIE': (1, 1, 0),
        'MIE': (3, 3, 0),
        'SPIE': (5, 5, 0),
        'MPIE': (7, 7, 0),
        'SPP': (8, 8, 0),
        'MPP': (11, 12, 0b11)
    }

    MIE_BITMAP = {
        'STIE': (5, 5, 0),
        'MTIE': (7, 7, 0)
    }

    MIP_BITMAP = {
        'STIP': (5, 5, 0),
        'MTIP': (7, 7, 0)
    }

    SATP_BITMAP = {
        'PPN': (0, 21, 0),
        'ASID': (22, 30, 0),
        'MODE': (31, 31, 0)
    }

    def __init__(self) -> None:
        super().__init__([0]*4096, CSR.ADDR_MAP)
        self.mstatus = self.sstatus = util.bit_container('[m/s]status', CSR.MSTATUS_BITMAP)()
        self.mie = self.sie = util.bit_container('[m/s]ie', CSR.MIE_BITMAP)()
        self.mip = self.sip = util.bit_container('[m/s]ip', CSR.MIP_BITMAP)()
        self.satp = util.bit_container('satp', CSR.SATP_BITMAP)()

    def __getitem__(self, key):
        return int(self._inner_array[key])
    
    def __setitem__(self, key, value):
        if type(self._inner_array[key]) == int:
            self._inner_array[key] = value
        else:   # bit_container
            self._inner_array[key]._value = value

    def __repr__(self) -> str:
        return self.__class__.__name__ + ": " + '[{}]'.format(', '.join(hex(int(x)) for x in self._inner_array))


class MMU(addrspace.AddrSpace):

    class PageFaultException(Exception):

        def __init__(self, vaddr, *args: object) -> None:
            super().__init__(*args)
            self.vaddr = vaddr

    class LoadPageFault(PageFaultException):
        pass

    class StorePageFault(PageFaultException):
        pass

    PAGE_SIZE = 4096
    PTE_SIZE = 4

    PTE_BITMAP = {
        'V':(0, 0, 0),
        'R':(1, 1, 0),
        'W':(2, 2, 0),
        'X':(3, 3, 0),
        'U':(4, 4, 0),
        'G':(5, 5, 0),
        'A':(6, 6, 0),
        'D':(7, 7, 0),
        'RSW':(8, 9, 0),
        'PPN0':(10, 19, 0),
        'PPN1':(20, 31, 0)
    }
    VA = util.bit_container('VA', {'VPN1':(22, 31, 0), 'VPN0':(12, 21, 0), 'OFFSET':(0, 11, 0)})
    PA = util.bit_container('PA', {'PPN1':(22, 33, 0), 'PPN0':(12, 21, 0), 'OFFSET':(0, 11, 0)})
    PTE = util.bit_container('PTE', PTE_BITMAP)

    def __init__(self, _cpu:CPU, _addrspace:addrspace.AddrSpace) -> None:
        super().__init__(0, 0xFFFFFFFF, self.__class__.__name__, False)
        self._cpu = _cpu
        self._addrspace = _addrspace

    def translate_addr(self, addr, write=False):
        pagefault = MMU.StorePageFault(addr) if write else MMU.LoadPageFault(addr)
        if MODE_M != self._cpu.mode and self._cpu.csr.satp.MODE:
            va = MMU.VA(addr)
            pte_addr = self._cpu.csr.satp.PPN * MMU.PAGE_SIZE + va.VPN1
            pte = MMU.PTE(self._addrspace.u32[pte_addr])
            if not pte.V or (1 == pte.W and 0 == pte.R):
                raise pagefault    # page fault
            if not (pte.R or pte.X):    # next level
                pte_addr = pte.PPN1 * MMU.PAGE_SIZE + va.VPN0
                pte = MMU.PTE(self._addrspace.u32[pte_addr])
                if not pte.V or (1 == pte.W and 0 == pte.R) or not (pte.R or pte.X):
                    raise pagefault    # page fault
                superpage = False
            else:
                superpage = True
            # leaf, skip check, just return address
            pa = MMU.PA()
            pa.OFFSET = va.OFFSET
            pa.PPN0 = va.VPN0 if superpage else pte.PPN0
            pa.PPN1 = pte.PPN1
            return int(pa)
        else:
            return addr

    def read(self, addr, length):
        return self._addrspace.read(self.translate_addr(addr), length)

    def write(self, addr, data):
        self._addrspace.write(self.translate_addr(addr, write=True), data)
