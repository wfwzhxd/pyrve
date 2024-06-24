import util
import cpu
import math

bitcut = lambda v,l,h:((v&(2<<h)-1))>>l
ru = lambda v:v&0xFFFFFFFF      # reg value to unsigned

class InstFormat:
    
    def __init__(self, value) -> None:
        self.value = value

    def exec(self, _cpu:cpu.CPU):
        raise NotImplementedError(self.__class__)
    
    @property
    def opcode(self):
        return bitcut(self.value, 0, 6)
    
    @property
    def rd(self):
        return bitcut(self.value, 7, 11)
    
    @property
    def funct3(self):
        return bitcut(self.value, 12, 14)
    
    @property
    def rs1(self):
        return bitcut(self.value, 15, 19)
    
    @property
    def rs2(self):
        return bitcut(self.value, 20, 24)
    
    @property
    def funct7(self):
        return bitcut(self.value, 25, 31)

    @property
    def imm(self):
        return None
    
    def __repr__(self) -> str:
        return '{}[opcode:{:b}, funct3:{:#x}, funct7:{:#x}, rs1:{}, rs2:{}, rd:{}, imm:{}]'.format(self.__class__.__name__, self.opcode, self.funct3, self.funct7, self.rs1, self.rs2, self.rd, util.u2s(self.imm, 32) if self.imm != None else None)


class Format_R(InstFormat):
    pass

class Format_I(InstFormat):

    @property
    def imm(self):
        r = bitcut(self.value, 20, 31)
        return util.msb_extend(r, 12, 32)

class Format_S(InstFormat):

    @property
    def imm(self):
        low = bitcut(self.value, 7, 11)
        high = bitcut(self.value, 25, 31)
        r = (high<<5)|low
        return util.msb_extend(r, 12, 32)

class Format_U(InstFormat):

    @property
    def imm(self):
        r = bitcut(self.value, 12, 31)
        return util.msb_extend(r, 20, 32)

class Format_B(InstFormat):

    @property
    def imm(self):
        low = bitcut(self.value, 8, 11)<<1
        high = bitcut(self.value, 25, 30)<<5
        r = (bitcut(self.value, 31, 31)<<12) | (bitcut(self.value, 7, 7)<<11) | high | low
        return util.msb_extend(r, 13, 32)

class Format_J(InstFormat):

    @property
    def imm(self):
        low = bitcut(self.value, 21, 30)<<1
        high = bitcut(self.value, 12, 19)<<12
        r = (bitcut(self.value, 31, 31)<<20) | high | (bitcut(self.value, 20, 20)<<11) | low
        return util.msb_extend(r, 21, 32)


# Base REG:

class ADD(Format_R):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu.regs[self.rs1] + _cpu.regs[self.rs2]

class SUB(Format_R):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu.regs[self.rs1] - _cpu.regs[self.rs2]

class XOR(Format_R):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu.regs[self.rs1] ^ _cpu.regs[self.rs2]

class OR(Format_R):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu.regs[self.rs1] | _cpu.regs[self.rs2]

class AND(Format_R):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu.regs[self.rs1] & _cpu.regs[self.rs2]

class SLL(Format_R):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu.regs[self.rs1] << (_cpu.regs[self.rs2] & 0x1F)

class SRL(Format_R):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu.regs[self.rs1] >> (_cpu.regs[self.rs2] & 0x1F)

class SRA(Format_R):

    def exec(self, _cpu: cpu.CPU):
        rs1 = util.msb_extend(_cpu.regs[self.rs1], _cpu.XLEN, _cpu.XLEN+_cpu.regs[self.rs2])
        _cpu.regs[self.rd] = rs1>>(_cpu.regs[self.rs2] & 0x1F)

class SLT(Format_R):

    def exec(self, _cpu: cpu.CPU):
        rs1 = util.u2s(_cpu.regs[self.rs1], _cpu.XLEN)
        rs2 = util.u2s(_cpu.regs[self.rs2], _cpu.XLEN)
        v = 1 if rs1<rs2 else 0
        _cpu.regs[self.rd] = v

class SLTU(Format_R):

    def exec(self, _cpu: cpu.CPU):
        v = 1 if _cpu.regs[self.rs1]<_cpu.regs[self.rs2] else 0
        _cpu.regs[self.rd] = v


# Base IMM:

class ADDI(Format_I):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu.regs[self.rs1] + self.imm

class XORI(Format_I):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu.regs[self.rs1] ^ self.imm

class ORI(Format_I):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu.regs[self.rs1] | self.imm

class ANDI(Format_I):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu.regs[self.rs1] & self.imm

class SLLI(Format_I):

    def exec(self, _cpu: cpu.CPU):
        s = self.imm&0x1F
        _cpu.regs[self.rd] = _cpu.regs[self.rs1] << s

class SRLI(Format_I):

    def exec(self, _cpu: cpu.CPU):
        s = self.imm&0x1F
        _cpu.regs[self.rd] = _cpu.regs[self.rs1] >> s

class SRAI(Format_I):

    def exec(self, _cpu: cpu.CPU):
        s = self.imm&0x1F
        rs1 = util.msb_extend(_cpu.regs[self.rs1], _cpu.XLEN, _cpu.XLEN+_cpu.regs[self.rs2])
        _cpu.regs[self.rd] = rs1 >> s

class SLTI(Format_I):

    def exec(self, _cpu: cpu.CPU):
        rs1 = util.u2s(_cpu.regs[self.rs1], _cpu.XLEN)
        imm = util.u2s(self.imm, _cpu.XLEN)
        v = 1 if rs1<imm else 0
        _cpu.regs[self.rd] = v

class SLTIU(Format_I):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = 1 if _cpu.regs[self.rs1]<ru(self.imm) else 0

# Load Store:

class LB(Format_I):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu._addrspace.s8[_cpu.regs[self.rs1] + self.imm]

class LH(Format_I):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu._addrspace.s16[_cpu.regs[self.rs1] + self.imm]

class LW(Format_I):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu._addrspace.u32[_cpu.regs[self.rs1] + self.imm]

class LBU(Format_I):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu._addrspace.u8[_cpu.regs[self.rs1] + self.imm]

class LHU(Format_I):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu._addrspace.u16[_cpu.regs[self.rs1] + self.imm]

class SB(Format_S):

    def exec(self, _cpu: cpu.CPU):
        _cpu._addrspace.u8[_cpu.regs[self.rs1] + self.imm] = _cpu.regs[self.rs2] & 0xFF

class SH(Format_S):

    def exec(self, _cpu: cpu.CPU):
        _cpu._addrspace.u16[_cpu.regs[self.rs1] + self.imm] = _cpu.regs[self.rs2] & 0xFFFF

class SW(Format_S):

    def exec(self, _cpu: cpu.CPU):
        _cpu._addrspace.u32[_cpu.regs[self.rs1] + self.imm] = _cpu.regs[self.rs2]

# Branch:

class BEQ(Format_B):

    def exec(self, _cpu: cpu.CPU):
        if _cpu.regs[self.rs1] == _cpu.regs[self.rs2]:
            _cpu.regs.pc += self.imm

class BNE(Format_B):

    def exec(self, _cpu: cpu.CPU):
        if _cpu.regs[self.rs1] != _cpu.regs[self.rs2]:
            _cpu.regs.pc += self.imm

class BLT(Format_B):

    def exec(self, _cpu: cpu.CPU):
        if util.u2s(_cpu.regs[self.rs1], 32) < util.u2s(_cpu.regs[self.rs2], 32):
            _cpu.regs.pc += self.imm

class BGE(Format_B):

    def exec(self, _cpu: cpu.CPU):
        if util.u2s(_cpu.regs[self.rs1], 32) >= util.u2s(_cpu.regs[self.rs2], 32):
            _cpu.regs.pc += self.imm

class BLTU(Format_B):

    def exec(self, _cpu: cpu.CPU):
        if (_cpu.regs[self.rs1] < _cpu.regs[self.rs2]):
            _cpu.regs.pc += self.imm

class BGEU(Format_B):

    def exec(self, _cpu: cpu.CPU):
        if (_cpu.regs[self.rs1] >= _cpu.regs[self.rs2]):
            _cpu.regs.pc += self.imm

# Jump:

class JAL(Format_J):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu.regs.pc + 4
        _cpu.regs.pc += self.imm


class JALR(Format_I):

    def exec(self, _cpu: cpu.CPU):
        old_pc = _cpu.regs.pc
        _cpu.regs.pc = (_cpu.regs[self.rs1] + self.imm)&0xFFFFFFFE
        _cpu.regs[self.rd] = old_pc + 4


# Upper IMM:

class LUI(Format_U):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = self.imm << 12

class AUIPC(Format_U):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu.regs.pc + (self.imm<<12)

# Environment

class Format_UI(Format_I):

    @property
    def imm(self):
        return super().imm & 0xFFF

class ECALL(Format_UI):
    
    def exec(self, _cpu: cpu.CPU):
        _cpu._go_mtrap(11)  #  Environment call from M-mode

class EBREAK(Format_UI):
    pass

class MRET(Format_UI):
    
    def exec(self, _cpu: cpu.CPU):
        _cpu.regs.pc = _cpu.csr.mepc
        _cpu.csr.mstatus |= 1 << cpu.MIE_BIT

# CSR

class CSRRW(Format_UI):

    def exec(self, _cpu: cpu.CPU):
        rs1 = _cpu.regs[self.rs1]
        if self.rd:
            _cpu.regs[self.rd] = _cpu.csr[self.imm]
        _cpu.csr[self.imm] = rs1

class CSRRS(Format_UI):

    def exec(self, _cpu: cpu.CPU):
        rs1 = _cpu.regs[self.rs1]
        _cpu.regs[self.rd] = _cpu.csr[self.imm]
        if rs1:
            _cpu.csr[self.imm] |= rs1

class CSRRC(Format_UI):
    
    def exec(self, _cpu: cpu.CPU):
        rs1 = _cpu.regs[self.rs1]
        _cpu.regs[self.rd] = _cpu.csr[self.imm]
        if rs1:
            _cpu.csr[self.imm] &= ~rs1

class CSRRWI(Format_UI):
    
    def exec(self, _cpu: cpu.CPU):
        if self.rd:
            _cpu.regs[self.rd] = _cpu.csr[self.imm]
        _cpu.csr[self.imm] = self.rs1

class CSRRSI(Format_UI):
    
    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu.csr[self.imm]
        if self.rs1:
            _cpu.csr[self.imm] |= self.rs1

class CSRRCI(Format_UI):
    
    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu.csr[self.imm]
        if self.rs1:
            _cpu.csr[self.imm] &= ~self.rs1


class FENCE(Format_I):

    def exec(self, _cpu: cpu.CPU):
        pass


# ATOMIC

class FORMAT_ATOMIC(Format_R):

    @property
    def aq(self):
        return util.get_bit(self.value, 26)
    
    @property
    def rl(self):
        return util.get_bit(self.value, 25)
    
    @property
    def funct5(self):
        return bitcut(self.value, 27, 31)


class LRw(FORMAT_ATOMIC):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu._addrspace.u32[_cpu.regs[self.rs1]]
        _cpu._addrspace.reserve[_cpu].add(_cpu.regs[self.rs1])


class SCw(FORMAT_ATOMIC):

    def exec(self, _cpu: cpu.CPU):
        if _cpu.regs[self.rs1] in _cpu._addrspace.reserve[_cpu]:
            _cpu._addrspace.u32[_cpu.regs[self.rs1]] = _cpu.regs[self.rs2]
            _cpu.regs[self.rd] = 0
        else:
            _cpu.regs[self.rd] = 1
        _cpu._addrspace.reserve[_cpu].clear()

import logging
class FORMAT_AMO(FORMAT_ATOMIC):

    def exec(self, _cpu: cpu.CPU):
        addr = _cpu.regs[self.rs1]
        # load
        mem_value = _cpu._addrspace.u32[addr]
        rs2_value = _cpu.regs[self.rs2]
        # op
        mem_value, rd_value = self.get_memvalue_rdvalue(mem_value, rs2_value)
        logging.debug(_cpu.regs)
        # logging.debug("get_memvalue_rdvalue return {}".format(hex(value)))
        # store
        _cpu.regs[self.rd] = rd_value
        _cpu._addrspace.u32[addr] = mem_value&0xFFFFFFFF

    def get_memvalue_rdvalue(self, mem_value, rs2_value):
        '''
        return mem_value, rd_value
        '''
        raise NotImplementedError()


class AMOSWAPw(FORMAT_AMO):

    def get_memvalue_rdvalue(self, mem_value, rs2_value):
        return rs2_value, mem_value


class AMOADDw(FORMAT_AMO):

    def get_memvalue_rdvalue(self, mem_value, rs2_value):
        return rs2_value + mem_value, mem_value


class AMOANDw(FORMAT_AMO):

    def get_memvalue_rdvalue(self, mem_value, rs2_value):
        return rs2_value & mem_value, mem_value


class AMOORw(FORMAT_AMO):

    def get_memvalue_rdvalue(self, mem_value, rs2_value):
        return rs2_value | mem_value, mem_value


class AMOXORw(FORMAT_AMO):

    def get_memvalue_rdvalue(self, mem_value, rs2_value):
        return rs2_value ^ mem_value, mem_value


class AMOMAXw(FORMAT_AMO):

    def get_memvalue_rdvalue(self, mem_value, rs2_value):
        return max(util.u2s(rs2_value, 32), util.u2s(mem_value, 32)), mem_value


class AMOMINw(FORMAT_AMO):

    def get_memvalue_rdvalue(self, mem_value, rs2_value):
        return min(util.u2s(rs2_value, 32), util.u2s(mem_value, 32)), mem_value


class AMOMAXUw(FORMAT_AMO):

    def get_memvalue_rdvalue(self, mem_value, rs2_value):
        return max(mem_value, rs2_value), mem_value


class AMOMINUw(FORMAT_AMO):

    def get_memvalue_rdvalue(self, mem_value, rs2_value):
        return min(mem_value, rs2_value), mem_value


# Mul/Div

class Format_MULDIV(Format_R):
    
    def exec(self, _cpu: cpu.CPU):
        rs1 = _cpu.regs[self.rs1]
        rs2 = _cpu.regs[self.rs2]
        _cpu.regs[self.rd] = self.calc_rd(rs1, rs2)

    def calc_rd(self, rs1, rs2):
        raise NotImplementedError()


class MUL(Format_MULDIV):

    def calc_rd(self, rs1, rs2):
        return rs1 * rs2


class MULH(Format_MULDIV):

    def calc_rd(self, rs1, rs2):
        return (util.u2s(rs1, 32) * util.u2s(rs2, 32))>>32


class MULHSU(Format_MULDIV):

    def calc_rd(self, rs1, rs2):
        return (util.u2s(rs1, 32) * rs2)>>32


class MULHU(Format_MULDIV):

    def calc_rd(self, rs1, rs2):
        return (rs1 * rs2)>>32


class DIV(Format_MULDIV):

    def calc_rd(self, rs1, rs2):
        if rs2:
            rs1 = util.u2s(rs1, 32)
            rs2 = util.u2s(rs2, 32)
            if rs1 == -(2**(32-1)) and rs2 == -1:
                return -(2**(32-1))
            return math.trunc(util.u2s(rs1, 32)/util.u2s(rs2, 32))
        else:
            return 0xFFFFFFFF


class DIVU(Format_MULDIV):

    def calc_rd(self, rs1, rs2):
        if rs2:
            return math.trunc(rs1/rs2)
        else:
            return -1


class REM(Format_MULDIV):

    def calc_rd(self, rs1, rs2):
        if rs2:
            rs1 = util.u2s(rs1, 32)
            rs2 = util.u2s(rs2, 32)
            if rs1 == -(2**(32-1)) and rs2 == -1:
                return 0
            return rs1-math.trunc(rs1/rs2)*rs2
        else:
            return rs1


class REMU(Format_MULDIV):

    def calc_rd(self, rs1, rs2):
        if rs2:
            return rs1-math.trunc(rs1/rs2)*rs2
        else:
            return rs1
