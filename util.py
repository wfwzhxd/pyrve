

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
    def read16u(mem, address):
        data = mem.read(address, 2)
        v = data[1]<<8 + data[0]
        return v&0xFFFF
    
    @staticmethod
    def write16u(mem, address, value):
        data = bytes([value&0XFF, (value>>8)&0XFF])
        mem.write(address, data)
    
    @staticmethod
    def read32u(mem, address):
        data = mem.read(address, 4)
        v = data[3]<<24 + data[2]<<16 + data[1]<<8 + data[0]
        return v&0xFFFFFFFF

    @staticmethod
    def write32u(mem, address, value):
        data = bytes([value&0XFF, (value>>8)&0XFF, (value>>16)&0XFF, (value>>24)&0XFF])
        mem.write(address, data)
