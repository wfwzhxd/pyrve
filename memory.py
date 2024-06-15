import addrspace
import peripheral

PHYMEM_BASE = 0x80000000
MTIME_BASE = 0x0200bff8
MTIMECMP_BASE = 0x02004000

class Memory(addrspace.AddrSpace):
    
    def __init__(self, phy_size=1024*1024) -> None:
        super().__init__(0, 0xFFFFFFFF, 'memory', False)
        phy_mem = addrspace.AddrSpace(PHYMEM_BASE, PHYMEM_BASE+phy_size-1, 'phy_mem', True)
        mtime = addrspace.AddrSpace(MTIME_BASE, MTIME_BASE+7, 'mtime', True)
        mtimecmp = addrspace.AddrSpace(MTIMECMP_BASE, MTIMECMP_BASE+7, 'mtimecmp', True)
        uart = peripheral.UART()
        self.sub_space.extend([mtime, mtimecmp, phy_mem, uart])
