from typing import Any
import struct
import functools

bitcut = lambda v,l,h:((v&(2<<h)-1))>>l

def bitput(v, l, h, nv):
    up = bitcut(v, h+1, int.bit_length(v)+ 1)<<(h+1)
    mid = nv << l
    down = bitcut(v, 0, l-1) if l else 0
    # print("{} {} {}".format(bin(up), bin(mid), bin(down)))
    return up | mid | down

def get_bit(value, bit):
    return 1 if bool(value & (1<<bit)) else 0

def clear_bit(value, bit):
    return value & ~(1<<bit)

def set_bit(value, bit):
    return value | (1<<bit)

def bit_set(value, bit, bitv):
    if bitv:
        return set_bit(value, bit)
    else:
        return clear_bit(value, bit)

def msb_extend(value, cur_len, dst_len):
    msb = value&(1<<(cur_len-1))
    if msb:
        mask = (1<<cur_len)-1
        return (~value)^mask
    else:
        return value
    
def zero_extend(value, cur_len):
    mask = (1<<cur_len)-1
    return value&mask

    
def u2s(value, bit_len):
    if value&(1<<(bit_len-1)):
        mask = (1<<(bit_len-1))-1
        result = ~(value-1) & mask
        if result == 0:
            result = 1<<(bit_len-1)
        return -result
    else:   # >=0
        return value

class LittleEndness:

    @staticmethod
    def read8s(mem, address):
        return struct.unpack('<b', mem.read(address, 1))[0]

    @staticmethod
    def write8s(mem, address, value):
        mem.write(address, struct.pack('<b', value))

    @staticmethod
    def read8u(mem, address):
        return struct.unpack('<B', mem.read(address, 1))[0]

    @staticmethod
    def write8u(mem, address, value):
        mem.write(address, struct.pack('<B', value))
    
    @staticmethod
    def read16s(mem, address):
        return struct.unpack("<h", mem.read(address, 2))[0]

    @staticmethod
    def write16s(mem, address, value):
        mem.write(address, struct.pack("<h", value))

    @staticmethod
    def read16u(mem, address):
        return struct.unpack("<H", mem.read(address, 2))[0]
    
    @staticmethod
    def write16u(mem, address, value):
        mem.write(address, struct.pack("<H", value))
    
    @staticmethod
    def read32s(mem, address):
        return struct.unpack("<l", mem.read(address, 4))[0]

    @staticmethod
    def write32s(mem, address, value):
        mem.write(address, struct.pack("<l", value))

    @staticmethod
    def read32u(mem, address):
        return struct.unpack("<L", mem.read(address, 4))[0]

    @staticmethod
    def write32u(mem, address, value):
        mem.write(address, struct.pack("<L", value))

    @staticmethod
    def read64s(mem, address):
        return struct.unpack("<q", mem.read(address, 8))[0]

    @staticmethod
    def write64s(mem, address, value):
        mem.write(address, struct.pack("<q", value))

    @staticmethod
    def read64u(mem, address):
        return struct.unpack("<Q", mem.read(address, 8))[0]

    @staticmethod
    def write64u(mem, address, value):
        mem.write(address, struct.pack("<Q", value))


class NamedArray:

    def __init__(self, _inner_array, _index_map) -> None:
        self._inner_array = _inner_array
        self._index_map = _index_map   # name:index

    def __getitem__(self, key):
        return self._inner_array[key]

    def __setitem__(self, key, value):
        self._inner_array[key] = value

    def __getattr__(self, name):
        if name in self._index_map:
            return self._inner_array[self._index_map[name]]
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ('_inner_array', '_index_map'):
            super().__setattr__(name, value)
        elif name in self._index_map:
            self[self._index_map[name]] = value
        else:
            raise AttributeError(name)
    
    def __repr__(self) -> str:
        return self.__class__.__name__ + ": " + '[{}]'.format(', '.join(hex(x) for x in self._inner_array))


def bit_container(cls_name, bitmap):
    '''
    bitmap: {
        name:(low_bit, high_bit, def_value)
    }
    '''

    def init(self, v=None):
        if v:
            self._value = v
        else:
            for name in self._bitmap.keys():
                setattr(self, name, self._bitmap[name][2])

    ns = {
        '_value':0,
        '_bitmap':dict(bitmap),
        '__repr__': lambda x:'{}({})'.format(cls_name, x._value),
        '__init__': init,
        '__int__': lambda x:x._value
    }
    for name in bitmap:
        bit_low = bitmap[name][0]
        bit_high = bitmap[name][1]

        def bitput2(self, nv, l, h):
            self._value = bitput(self._value, l, h, nv)

        _bitcut = functools.partial(lambda self, l, h: (self._value&((2<<h)-1))>>l, l=bit_low, h=bit_high)
        _bitput = functools.partial(bitput2, l=bit_low, h=bit_high)

        ns[name] = property(fget=_bitcut, fset=_bitput)

    return type(cls_name, (object,), ns)
