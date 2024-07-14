import logging
import util


class ByteWrap:

    SIGN_LEN_FUNC_READ_MAP = {
        True:{
            1:util.LittleEndness.read8s,
            2:util.LittleEndness.read16s,
            4:util.LittleEndness.read32s,
            8:util.LittleEndness.read64s
        },
        False:{
            1:util.LittleEndness.read8u,
            2:util.LittleEndness.read16u,
            4:util.LittleEndness.read32u,
            8:util.LittleEndness.read64u
        }
    }

    SIGN_LEN_FUNC_WRITE_MAP = {
        True:{
            1:util.LittleEndness.write8s,
            2:util.LittleEndness.write16s,
            4:util.LittleEndness.write32s,
            8:util.LittleEndness.write64s
        },
        False:{
            1:util.LittleEndness.write8u,
            2:util.LittleEndness.write16u,
            4:util.LittleEndness.write32u,
            8:util.LittleEndness.write64u
        }
    }

    def __init__(self, signed, byte_len, _addrspace) -> None:
        if byte_len not in (1, 2, 4, 8):
            raise ValueError("byte_len {} not valid".format(byte_len))
        self._addrspace = _addrspace
        self._read_func = ByteWrap.SIGN_LEN_FUNC_READ_MAP[bool(signed)][byte_len]
        self._write_func = ByteWrap.SIGN_LEN_FUNC_WRITE_MAP[bool(signed)][byte_len]

    def __getitem__(self, key):
        return self._read_func(self._addrspace, key)

    def __setitem__(self, key, value):
        return self._write_func(self._addrspace, key, value)


class InvalidAddress(Exception):
    pass


class AddrSpace:

    def __init__(self, base, size, name=None, init_mem=False) -> None:
        self.logger = logging.getLogger(name if name else self.__class__.__name__)
        self.name = name
        self.base, self.end = base, base + size - 1
        if init_mem:
            self.mem = memoryview(bytearray(size))
        else:
            self.mem = None
        self.reserve = {}
        self.s8 = ByteWrap(True, 1, self)
        self.u8 = ByteWrap(False, 1, self)
        self.s16 = ByteWrap(True, 2, self)
        self.u16 = ByteWrap(False, 2, self)
        self.s32 = ByteWrap(True, 4, self)
        self.u32 = ByteWrap(False, 4, self)
        self.s64 = ByteWrap(True, 8, self)
        self.u64 = ByteWrap(False, 8, self)

    def contain(self, addr):
        return addr >= self.base and addr <= self.end

    def read(self, addr, length):
        raise NotImplementedError()

    def write(self, addr, data):
        raise NotImplementedError()

    def __repr__(self) -> str:
        #return "{}(name:{}, base:{}, end:{}, sub_space:{})".format(self.__class__.__name__, self.name, self.base, self.end, self.sub_space)
        d = dict(self.__dict__)
        del d['mem']
        return "{}[{}]".format(self.__class__.__name__, repr(d))


class BufferAddrSpace(AddrSpace):

    def __init__(self, base, size, name=None, init_mem=False) -> None:
        super().__init__(base, size, name, init_mem)
        self.sub_space = []

    def read(self, addr, length):
        if self.contain(addr):
            for sub in self.sub_space:
                if sub.contain(addr):
                    return sub.read(addr, length)
            if self.mem:
                offset = addr - self.base
                return self.mem[offset: offset + length]
        raise InvalidAddress("{} unhandled read at {}".format(self.name, hex(addr)))

    def write(self, addr, data):
        if self.contain(addr):
            for sub in self.sub_space:
                if sub.contain(addr):
                    sub.write(addr, data)
                    return
            if self.mem:
                offset = addr - self.base
                self.mem[offset: offset + len(data)] = data
                return
        raise InvalidAddress("{} unhandled write at {}".format(self.name, hex(addr)))


class ByteAddrSpace(AddrSpace):

    def read(self, addr, length):
        result = bytearray(length)
        for idx in range(length):
            _addr = addr + idx
            result[idx] = self.read_byte(_addr)
        return result

    def write(self, addr, data):
        for idx in range(len(data)):
            _addr = addr + idx
            self.write_byte(_addr, data[idx])

    def read_byte(self, addr):
        if self.mem:
            return self.mem[addr-self.base]
        else:
            raise InvalidAddress("{} unhandled read at {}".format(self.name, hex(addr)))

    def write_byte(self, addr, value):
        if self.mem:
            self.mem[addr-self.base] = value&0xFF
        else:
            raise InvalidAddress("{} unhandled write at {}".format(self.name, hex(addr)))
