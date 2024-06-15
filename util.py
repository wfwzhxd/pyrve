import struct

bitcut = lambda v,l,h:((v&(2<<h)-1))>>l

def get_bit(value, bit):
    return value & (1<<bit)

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
    def read8u(mem, address):
        data = mem.read(address, 1)
        return data[0]&0xFF

    @staticmethod
    def write8u(mem, address, value):
        data = bytes([value&0XFF])
        mem.write(address, data)
    
    @staticmethod
    def read16u(mem, address):
        return struct.unpack("<H", mem.read(address, 2))[0]
    
    @staticmethod
    def write16u(mem, address, value):
        mem.write(address, struct.pack("<H", value&0xFFFF))
    
    @staticmethod
    def read32u(mem, address):
        return struct.unpack("<L", mem.read(address, 4))[0]

    @staticmethod
    def write32u(mem, address, value):
        mem.write(address, struct.pack("<L", value&0xFFFFFFFF))

    @staticmethod
    def read64u(mem, address):
        return struct.unpack("<Q", mem.read(address, 8))[0]

    @staticmethod
    def write64u(mem, address, value):
        mem.write(address, struct.pack("<Q", value&0xFFFFFFFFFFFFFFFF))
