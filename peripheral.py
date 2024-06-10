import sys
import logging

logger = logging.getLogger(__name__)

class Peripheral:
    '''
    0xc0001000     uart read
    0xc0002000     uart write
    '''

    def __init__(self) -> None:
        self.uart_in_buf = bytearray()

    def read(self, address, length):
        logger.debug('read {} at {}'.format(length, address))
        if 0xc0001000 == address:
            while len(self.uart_in_buf) < length:
                self.uart_in_buf.extend(sys.stdin.readline().encode('ascii'))
            result, self.uart_in_buf = self.uart_in_buf[:length], self.uart_in_buf[length:]
            logger.debug(result.hex())
            return result
        raise IndexError('address {}'.format(address))

    def write(self, address, data:bytes):
        logger.debug('write {} at {}'.format(len(data), address))
        logger.debug(data.hex())        
        if 0xc0002000 == address:
            sys.stdout.write(data.decode(encoding='ascii'))
            sys.stdout.flush()
