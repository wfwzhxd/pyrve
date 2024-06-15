import cpu
import memory
import base64
import logging

logging.basicConfig(level=logging.ERROR, format='%(asctime)s %(name)s: %(message)s', filename='main.log', filemode='wt')

def calc_speed(_cpu):
    import timeit
    return 1E6/timeit.timeit("_cpu.run(1E6)", number=1, globals=locals())

def main():
    binname = 'RTOSDemo.bin'
    with open(binname, 'rb') as f:
        code = f.read()
    _addrspace = memory.Memory()
    _addrspace.write(0x80000000, code)
    _cpu = cpu.CPU(_addrspace)
    _cpu.regs.pc = 0x80000000
    import IPython
    IPython.embed()
    #_cpu.run(1024)

if __name__ == '__main__':
    main()

