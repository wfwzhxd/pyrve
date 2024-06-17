import collections
import functools
import logging

logger = logging.getLogger(__name__)


class InvalidAddress(Exception):
    pass


class AddrSpace:

    def __init__(self, start, end, name=None, init_mem=False) -> None:
        self.name = name
        self.start, self.end = start, end
        self.sub_space = []
        if init_mem:
            self.mem = bytearray(end-start+1)
        else:
            self.mem = None
        self.reserve = collections.defaultdict(set)

    def contain(self, addr):
        return addr >= self.start and addr <= self.end

    def read(self, addr, length):
        raise NotImplementedError()

    def write(self, addr, data):
        raise NotImplementedError()

    def __repr__(self) -> str:
        #return "{}(name:{}, start:{}, end:{}, sub_space:{})".format(self.__class__.__name__, self.name, self.start, self.end, self.sub_space)
        d = dict(self.__dict__)
        del d['mem']
        return "{}[{}]".format(self.__class__.__name__, repr(d))


class BufferAddrSpace(AddrSpace):

    @functools.lru_cache(maxsize=32*1024)
    def _get_space_for_rw(self, addr):
        if self.contain(addr):
            for sub in self.sub_space:
                if sub.contain(addr):
                    return sub
            if self.mem:
                return self
        raise InvalidAddress("{} addr:{}".format(self.name, hex(addr)))

    def read(self, addr, length):
        _start, _end = addr, addr+length-1
        space = self._get_space_for_rw(_start)
        if space != self:
            return space.read(addr, length)
        else:
            if _end <= self.end:
                result = self.mem[_start-self.start: _end-self.start+1]
                logging.getLogger(self.name).debug("read addr {}: {}".format(hex(addr), result))
                return result
            else:
                raise InvalidAddress("{} read addr {}, len {}".format(self.name, hex(addr), length))

    def write(self, addr, data):
        _start, _end = addr, addr+len(data)-1
        space = self._get_space_for_rw(_start)
        if space != self:
            space.write(addr, data)
        else:
            if _end <= self.end:
                logging.getLogger(self.name).debug("write addr {}: {}".format(hex(addr), data))
                space.mem[_start-self.start: _end-self.start+1] = data
            else:
                raise InvalidAddress("{} write {}, len {}".format(self.name, hex(addr), len(data)))


class ByteAddrSpace(AddrSpace):

    @functools.lru_cache(maxsize=32*1024)
    def _get_space_for_rw(self, addr):
        if self.contain(addr):
            for sub in self.sub_space:
                if sub.contain(addr):
                    return ByteAddrSpace._get_space_for_rw(sub, addr)
            return self
        raise InvalidAddress("{} addr:{}".format(self.name, hex(addr)))

    def read(self, addr, length):
        result = bytearray(length)
        for idx in range(length):
            _addr = addr + idx
            result[idx] = self._get_space_for_rw(_addr).read_byte(_addr)
        logging.getLogger(self.name).debug("read addr {}: {}".format(hex(addr), result))
        return result

    def write(self, addr, data):
        logging.getLogger(self.name).debug("write addr {}: {}".format(hex(addr), data))
        for idx in range(len(data)):
            _addr = addr + idx
            self._get_space_for_rw(_addr).write_byte(_addr, data[idx])

    def read_byte(self, addr):
        if self.mem:
            return self.mem[addr-self.start]
        else:
            raise InvalidAddress("{} read addr:{}".format(self.name, hex(addr)))

    def write_byte(self, addr, value):
        if self.mem:
            self.mem[addr-self.start] = value&0xFF
        else:
            raise InvalidAddress("{} write addr:{}".format(self.name, hex(addr)))
