import cpu
import memory
import base64
import logging

logging.basicConfig(level=logging.ERROR, format='%(asctime)s %(name)s: %(message)s', filename='main.log', filemode='wt')

def calc_speed(_cpu):
    import timeit
    return 1E6/timeit.timeit("_cpu.run(1E6)", number=1, globals=locals())

def run_forever(_cpu):
    while True:
        _cpu.run(1E9)

def load_binary(fname):
    with open(fname, 'rb') as f:
        return f.read()

def main():
    code = load_binary('DownloadedImage')
    dtb = load_binary('sixtyfourmb.dtb')
    phy_size=1024*1024*64
    _addrspace = memory.Memory2(phy_size)
    _addrspace.write(0x80000000, code)
    dtb_addr = 0x80000000+phy_size-len(dtb)
    _addrspace.write(dtb_addr, dtb)
    _cpu = cpu.CPU(_addrspace)
    _cpu.regs.pc = 0x80000000
    _cpu.regs[11] = dtb_addr
    import IPython
    IPython.embed()

if __name__ == '__main__':
    main()

