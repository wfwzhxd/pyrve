
class Memory:
    
    def __init__(self, start, end) -> None:
        self.mem = bytearray(end-start+1)
        self.base = start

    def read(self, address, length):
        '''
            return unsigned byte array
        '''
        if address<self.base or address+length>self.base+len(self.mem):
            raise IndexError("read {} at address{} not valid in mem[{}:{}]".format(length, address, self.base, self.base+len(self.mem)))
        address -= self.base
        return self.mem[address:address+length]

    def write(self, address, data:bytes):
        if address<self.base or address+len(data)>self.base+len(self.mem):
            raise IndexError("write {} at address{} not valid in mem[{}:{}]".format(len(data), address, self.base, self.base+len(self.mem)))
        address -= self.base
        self.mem[address:address+len(data)] = data
