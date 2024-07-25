from typing import Any
from . import addrspace
from . import decoder
from . import util
import logging
import collections
import time


logger = logging.getLogger(__name__)

MODE_U = 0b00
MODE_S = 0b01
MODE_M = 0b11

INTERRUPT_TIMER_S = 0x80000005
INTERRUPT_TIMER_M = 0x80000007

EXCEPTION_ILLEGAL_INSTRUCTION = 2

EXCEPTION_ECALL_FROM_U = 8
EXCEPTION_ECALL_FROM_S = 9
EXCEPTION_ECALL_FROM_M = 11

EXCEPTION_INST_PAGE_FAULT = 12
EXCEPTION_LOAD_PAGE_FAULT = 13
EXCEPTION_STORE_AMO_PAGE_FAULT = 15


class GOTRAP(Exception):
    pass

class CPU:

    XLEN = 32
    XMASK = 0xFFFFFFFF
    TIMEBASE_FREQ = 1000000

    MTIME_OFFSET = 0xbff8
    MTIMECMP_OFFSET = 0x4000

    def __init__(self, _addrspace:addrspace.AddrSpace, clint_base) -> None:
        self.regs = REGS()
        self.csr = CSR(self)
        self._addrspace_nommu = _addrspace
        self._addrspace = MMU(self, _addrspace)
        self.skip_step = 0
        self.mode = MODE_M
        self._start_time = time.monotonic_ns()
        self.inst_cache = collections.defaultdict(dict)    # {ppn, {vaddr:inst}}
        self.clint_base = clint_base


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
        logger.debug("_go_trap, mode: {}, cause {}, tval: {}".format(bin(self.mode), hex(cause), hex(tval)))
        if cause>>31:   # msb=1, interrupt
            a = (MODE_M == self.mode and self.csr.mstatus.MIE) or MODE_M > self.mode
            c = util.get_bit(self.csr.mideleg, cause&0x7FFFFFFF)
            if a and not c: 
                self._go_mtrap(cause, tval)
                return True
            a = (MODE_S == self.mode and self.csr.sstatus.SIE) or MODE_S > self.mode
            if a and c:
                self._go_strap(cause, tval)
                return True
            logger.debug("interrupt {} not handled, mode={}, MIE={}, SIE={}".format(cause, self.mode, self.csr.mstatus.MIE, self.csr.sstatus.SIE))
            return False
        else:   # exception
            if MODE_M > self.mode and util.get_bit(self.csr.medeleg, cause):   # not support medelegh
                self._go_strap(cause, tval)
            else:
                self._go_mtrap(cause, tval)
        return True


    def run(self, step):
        while(step):
            self.skip_step += 1
            step -= 1
            logger.debug(self.regs)
            # logger.debug(self.csr)

            # exec inst
            cached_pc = self.regs.pc
            try:
                paddr = self._addrspace.translate_addr(cached_pc)
                decoded_inst = self.inst_cache[paddr>>12].get(cached_pc)
                if not decoded_inst:
                    decoded_inst = decoder.decode(self._addrspace.u32[cached_pc])
                    self.inst_cache[paddr>>12][cached_pc] = decoded_inst
            except MMU.PageFaultException as e:
                self._go_trap(EXCEPTION_INST_PAGE_FAULT, e.vaddr)
                continue

            logger.debug(decoded_inst)

            try:
                decoded_inst.exec(self)
            except GOTRAP:
                continue
            except MMU.PageFaultException as e:
                if isinstance(e, MMU.LoadPageFault):
                    cause = EXCEPTION_LOAD_PAGE_FAULT
                else:
                    cause = EXCEPTION_STORE_AMO_PAGE_FAULT
                self._go_trap(cause, e.vaddr)
                continue
            if cached_pc == self.regs.pc:
                self.regs.pc += 4  # IS THIS RIGHT?

            if self.skip_step>2048:
                # mtime
                cur_time = int((time.monotonic_ns() - self._start_time) * 1E-9 * CPU.TIMEBASE_FREQ)
                self._addrspace_nommu.u64[self.clint_base + CPU.MTIME_OFFSET] = cur_time
                self.csr.time = cur_time & 0xFFFFFFFF
                self.csr.timeh = cur_time>>32
                self.skip_step = 0
                mtime_pend = 1 if cur_time >= self._addrspace_nommu.u64[self.clint_base + CPU.MTIMECMP_OFFSET] else 0
                self.csr.mip.MTIP = mtime_pend

                # check interrupt
                if self.csr.mip.MTIP and self.csr.mie.MTIE: # MTIMER
                    if self._go_trap(INTERRUPT_TIMER_M):
                        continue

                if self.csr.sip.STIP and self.csr.sie.STIE: # STIMER
                    if self._go_trap(INTERRUPT_TIMER_S):
                        continue

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
        'time': 0xc01,
        'timeh': 0xc81,

        'mvendorid': 0xf11,
        'marchid': 0xf12,
        'mimpid': 0xf13,
        'mhartid': 0xf14,
        'mconfigptr': 0xf15,

        'sstatus': 0x100,
        'sie': 0x104,
        'stvec': 0x105,
        'senvcfg': 0x10A,

        'sscratch': 0x140,
        'sepc': 0x141,
        'scause': 0x142,
        'stval': 0x143,
        'sip': 0x144,

        'satp': 0x180,

        'mstatus': 0x300,
        'misa': 0x301,
        'medeleg': 0x302,
        'mideleg': 0x303,
        'mie': 0x304,
        'mtvec': 0x305,
        'medelegh': 0x312,

        'mscratch': 0x340,
        'mepc': 0x341,
        'mcause': 0x342,
        'mtval': 0x343,
        'mip': 0x344,

        'mhartid': 0xF14
    }

    ADDRS = set(ADDR_MAP.values())

    MSTATUS_BITMAP = {
        'SIE': (1, 1, 0),
        'MIE': (3, 3, 0),
        'SPIE': (5, 5, 0),
        'MPIE': (7, 7, 0),
        'SPP': (8, 8, 0),
        'MPP': (11, 12, 0b11),
        'SUM': (18, 18, 0),
        'MXR': (19, 19, 0)
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

    def __init__(self, _cpu:CPU) -> None:
        super().__init__([0]*4096, CSR.ADDR_MAP)
        self._cpu = _cpu
        self.mstatus = self.sstatus = util.bit_container('[m/s]status', CSR.MSTATUS_BITMAP)()
        self.mie = self.sie = util.bit_container('[m/s]ie', CSR.MIE_BITMAP)()
        self.mip = self.sip = util.bit_container('[m/s]ip', CSR.MIP_BITMAP)()
        self.satp = util.bit_container('satp', CSR.SATP_BITMAP)()
        self.misa = 0x40141101    # rv32ima S/U mode
        self.mvendorid = 0xff0ff0ff

    def __getitem__(self, key):
        value = int(self._inner_array[key])
        if key not in CSR.ADDRS: 
            self._cpu._go_trap(EXCEPTION_ILLEGAL_INSTRUCTION, self._cpu.regs.pc)
            raise GOTRAP()
        return value
    
    def __setitem__(self, key, value):
        if key not in CSR.ADDRS: 
            self._cpu._go_trap(EXCEPTION_ILLEGAL_INSTRUCTION, self._cpu.regs.pc)
            raise GOTRAP()
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
        self.cache = collections.defaultdict(dict) # {asid:{vaddr&0xFFFFF000:(pte, pte_addr, superpage)}}
        self.cache_hit = 0
        self.cache_mis = 0

    def find_pte(self, addr):
        asid = self._cpu.csr.satp.ASID
        key = addr & 0xFFFFF000
        p =  self.cache[asid].get(key, None)
        if p:
            self.cache_hit += 1
            return p
        self.cache_mis += 1
        result_error = (None, None, False)
        va = MMU.VA(addr)
        pte_addr = self._cpu.csr.satp.PPN * MMU.PAGE_SIZE + va.VPN1 * MMU.PTE_SIZE
        pte = MMU.PTE(self._addrspace.u32[pte_addr])
        if not pte.V or (1 == pte.W and 0 == pte.R):
            return result_error    # page fault
        if not (pte.R or pte.X):    # next level
            if pte.W + pte.R + pte.X:   # should not happen
                logger.error('PTE({}) at addr {} error: non-leaf pte RWX != 0'.format(pte, pte_addr))
            pte_addr = (pte.PPN1<<10|pte.PPN0) * MMU.PAGE_SIZE + va.VPN0 * MMU.PTE_SIZE
            pte = MMU.PTE(self._addrspace.u32[pte_addr])
            if not pte.V or (1 == pte.W and 0 == pte.R) or not (pte.R or pte.X):
                return result_error
            superpage = False
        else:
            superpage = True
        result_ok = (pte, pte_addr, superpage)
        self.cache.get(asid)[key] = result_ok
        return result_ok

    def translate_addr(self, addr, write=False):
        if MODE_M != self._cpu.mode and self._cpu.csr.satp.MODE:
            pte, pte_addr, superpage = self.find_pte(addr)
            pagefault = MMU.StorePageFault(addr) if write else MMU.LoadPageFault(addr)
            va = MMU.VA(addr)
            if not pte:
                raise pagefault
            if MODE_U == self._cpu.mode and not pte.U:
                logger.debug('PTE({}) at addr {} error: U mode without U flag'.format(pte, pte_addr))
                raise pagefault
            if MODE_S == self._cpu.mode and pte.U and not self._cpu.csr.sstatus.SUM:
                logger.debug('PTE({}) at addr {} error: S mode without SUM flag'.format(pte, pte_addr))
                raise pagefault
            if not self._cpu.csr.sstatus.MXR and not pte.R:
                logger.debug('PTE({}) at addr {} error: MXR=0, pte.R=0'.format(pte, pte_addr))
                raise pagefault
            if superpage and pte.PPN0:
                logger.debug('PTE({}) at addr {} error: MISALIGN superpage'.format(pte, pte_addr))
                raise pagefault
            if not pte.W and write:
                logger.debug('PTE({}) at addr {} error: NO write perm'.format(pte, pte_addr))
                raise pagefault
            if addr == self._cpu.regs.pc:
                if not pte.X:
                    logger.debug('PTE({}) at addr {} error: NO exec perm'.format(pte, pte_addr))
                    raise pagefault
            else:
                if not pte.R:
                    logger.debug('PTE({}) at addr {} error: NO read perm'.format(pte, pte_addr))
                    raise pagefault

            if 0 == pte.A or (0 == pte.D and write):
                logger.debug('PTE({}) at addr {} error: A/D flag not valid, do repare'.format(pte, pte_addr))
                pte.A = 1
                if write:
                    pte.D = 1
                self._addrspace.u32[pte_addr] = int(pte)
            pa = MMU.PA()
            pa.OFFSET = va.OFFSET
            pa.PPN0 = va.VPN0 if superpage else pte.PPN0
            pa.PPN1 = pte.PPN1
            paddr = int(pa)
        else:
            paddr = addr
        if write:
            self._cpu.inst_cache[paddr>>12].clear()
        return paddr

    def read(self, addr, length):
        start_offset = addr&0xfff
        end_offset = (addr+length-1)&0xfff
        if end_offset < start_offset:   # should not happen
            logger.error("read addr {} length {} across page".format(addr, length))
        return self._addrspace.read(self.translate_addr(addr), length)

    def write(self, addr, data):
        length = len(data)
        start_offset = addr&0xfff
        end_offset = (addr+length-1)&0xfff
        if end_offset < start_offset:
            logger.error("write addr {} length {} across page".format(addr, length))
        self._addrspace.write(self.translate_addr(addr, write=True), data)
