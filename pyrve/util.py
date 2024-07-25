import functools
from typing import Any

WV = [(2 << w) - 1 for w in range(32)]

bitcut = lambda v, l, h: (v >> l) & WV[h - l]


def bitput(v, l, h, nv):
    return v & ~(WV[h - l] << l) | nv << l


def get_bit(value, bit):
    return 1 if bool(value & (1 << bit)) else 0


def clear_bit(value, bit):
    return value & ~(1 << bit)


def set_bit(value, bit):
    return value | (1 << bit)


def bit_set(value, bit, bitv):
    if bitv:
        return set_bit(value, bit)
    else:
        return clear_bit(value, bit)


def msb_extend(value, cur_len, dst_len):
    msb = value & (1 << (cur_len - 1))
    if msb:
        mask = (1 << cur_len) - 1
        return (~value) ^ mask
    else:
        return value


def zero_extend(value, cur_len):
    mask = (1 << cur_len) - 1
    return value & mask


def u2s(value, bit_len):
    if value & (1 << (bit_len - 1)):
        mask = (1 << (bit_len - 1)) - 1
        result = ~(value - 1) & mask
        if result == 0:
            result = 1 << (bit_len - 1)
        return -result
    else:  # >=0
        return value


class LittleEndness:

    @staticmethod
    def read8s(mem, address):
        return int.from_bytes(mem.read(address, 1), byteorder="little", signed=True)

    @staticmethod
    def write8s(mem, address, value):
        mem.write(address, int.to_bytes(value, 1, byteorder="little", signed=True))

    @staticmethod
    def read8u(mem, address):
        return int.from_bytes(mem.read(address, 1), byteorder="little", signed=False)

    @staticmethod
    def write8u(mem, address, value):
        mem.write(address, int.to_bytes(value, 1, byteorder="little", signed=False))

    @staticmethod
    def read16s(mem, address):
        return int.from_bytes(mem.read(address, 2), byteorder="little", signed=True)

    @staticmethod
    def write16s(mem, address, value):
        mem.write(address, int.to_bytes(value, 2, byteorder="little", signed=True))

    @staticmethod
    def read16u(mem, address):
        return int.from_bytes(mem.read(address, 2), byteorder="little", signed=False)

    @staticmethod
    def write16u(mem, address, value):
        mem.write(address, int.to_bytes(value, 2, byteorder="little", signed=False))

    @staticmethod
    def read32s(mem, address):
        return int.from_bytes(mem.read(address, 4), byteorder="little", signed=True)

    @staticmethod
    def write32s(mem, address, value):
        mem.write(address, int.to_bytes(value, 4, byteorder="little", signed=True))

    @staticmethod
    def read32u(mem, address):
        return int.from_bytes(mem.read(address, 4), byteorder="little", signed=False)

    @staticmethod
    def write32u(mem, address, value):
        mem.write(address, int.to_bytes(value, 4, byteorder="little", signed=False))

    @staticmethod
    def read64s(mem, address):
        return int.from_bytes(mem.read(address, 8), byteorder="little", signed=True)

    @staticmethod
    def write64s(mem, address, value):
        mem.write(address, int.to_bytes(value, 8, byteorder="little", signed=True))

    @staticmethod
    def read64u(mem, address):
        return int.from_bytes(mem.read(address, 8), byteorder="little", signed=False)

    @staticmethod
    def write64u(mem, address, value):
        mem.write(address, int.to_bytes(value, 8, byteorder="little", signed=False))


class NamedArray:

    def __init__(self, _inner_array, _index_map) -> None:
        self._inner_array = _inner_array
        self._index_map = _index_map  # name:index

    def __getitem__(self, key):
        return self._inner_array[key]

    def __setitem__(self, key, value):
        self._inner_array[key] = value

    def __getattr__(self, name):
        return self._inner_array[self._index_map[name]]

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("_inner_array", "_index_map"):
            super().__setattr__(name, value)
        elif name in self._index_map:
            self._inner_array[self._index_map[name]] = value
        else:
            super().__setattr__(name, value)

    def __repr__(self) -> str:
        return (
            self.__class__.__name__
            + ": "
            + "[{}]".format(", ".join(hex(x) for x in self._inner_array))
        )


def bit_container(cls_name, bitmap):
    """
    bitmap: {
        name:(low_bit, high_bit, def_value)
    }
    """

    def init(self, v=None):
        if v != None:
            self._value = v
        else:
            for name in self._bitmap.keys():
                setattr(self, name, self._bitmap[name][2])

    ns = {
        "_value": 0,
        "_bitmap": dict(bitmap),
        "__repr__": lambda x: "{}({})".format(cls_name, x._value),
        "__init__": init,
        "__int__": lambda x: x._value,
    }
    for name in bitmap:
        bit_low = bitmap[name][0]
        bit_high = bitmap[name][1]

        if bit_low == bit_high:  # single bit, easy to handle

            def bitput2(self, nv, b):
                self._value = bit_set(self._value, b, nv)

            _bitcut = functools.partial(
                lambda self, b: (self._value >> b) & 1, b=bit_low
            )
            _bitput = functools.partial(bitput2, b=bit_low)
            ns[name] = property(fget=_bitcut, fset=_bitput)
        else:

            def bitput2(self, nv, l, h):
                self._value = bitput(self._value, l, h, nv)

            _bitcut = functools.partial(
                lambda self, l, h: (self._value & ((2 << h) - 1)) >> l,
                l=bit_low,
                h=bit_high,
            )
            _bitput = functools.partial(bitput2, l=bit_low, h=bit_high)

            ns[name] = property(fget=_bitcut, fset=_bitput)

    return type(cls_name, (object,), ns)


def calc_speed(_cpu, step=1e6):
    import timeit

    return step / timeit.timeit("_cpu.run({})".format(step), number=1, globals=locals())


def load_binary(fname):
    with open(fname, "rb") as f:
        return f.read()


def run_forever(_cpu):
    while True:
        _cpu.run(1e9)
