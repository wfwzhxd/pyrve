from . import cpu


class Dbg:

    def __init__(self, _cpu: cpu.CPU) -> None:
        self.breaks = []
        self._cpu = _cpu

    def add_break(self, test_func):
        self.breaks.append(test_func)

    def do_continue(self, step=1e100):
        while step:
            step -= 1
            self._cpu.run(1)
            for func in self.breaks:
                if func(self._cpu):
                    return func


class TestFunc:

    @staticmethod
    def pc(addr):
        def _wrap(_cpu: cpu.CPU):
            return addr == _cpu.regs.pc

        return _wrap

    def mem(addr, data):
        def _wrap(_cpu: cpu.CPU):
            return data == _cpu._addrspace.read(addr, len(data))

        return _wrap

    def backtrace(pc_array):
        def _wrap(_cpu: cpu.CPU):
            if len(pc_array) == 0 or pc_array[-1] + 4 != _cpu.regs.pc:
                pc_array.append(_cpu.regs.pc)
            return False

        return _wrap
