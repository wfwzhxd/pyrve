import logging

logger = logging.getLogger(__name__)
class Memory:
    
    def __init__(self, start, end) -> None:
        self.mem = bytearray(end-start+1)
        self.base = start

    def read(self, address, length):
        '''
            return unsigned byte array
        '''
        logger.debug('read {} at {}'.format(length, address))
        if address<self.base or address+length>self.base+len(self.mem):
            raise IndexError("read {} at address{} not valid in mem[{}:{}]".format(length, address, self.base, self.base+len(self.mem)))
        address -= self.base
        result = self.mem[address:address+length]
        logger.debug(result.hex())
        return result

    def write(self, address, data:bytes):
        logger.debug('write {} at {}'.format(len(data), address))
        logger.debug(data.hex())
        if address<self.base or address+len(data)>self.base+len(self.mem):
            raise IndexError("write {} at address{} not valid in mem[{}:{}]".format(len(data), address, self.base, self.base+len(self.mem)))
        address -= self.base
        self.mem[address:address+len(data)] = data
