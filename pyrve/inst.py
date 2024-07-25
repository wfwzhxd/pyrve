from . import util
from . import cpu
import math

bitcut = util.bitcut
ru = lambda v: v & 0xFFFFFFFF  # reg value to unsigned


class InstFormat:

    def __init__(self, value) -> None:
        self.value = value
        self.opcode = bitcut(self.value, 0, 6)
        self.rd = bitcut(self.value, 7, 11)
        self.rs1 = bitcut(self.value, 15, 19)
        self.rs2 = bitcut(self.value, 20, 24)
        self.funct3 = bitcut(self.value, 12, 14)
        self.funct7 = bitcut(self.value, 25, 31)
        self.imm = None

    def exec(self, _cpu: cpu.CPU):
        raise NotImplementedError(self.__class__)

    def __repr__(self) -> str:
        return "{}[value:{:#x}, opcode:{:b}, funct3:{:#x}, funct7:{:#x}, rs1:{}, rs2:{}, rd:{}, imm:{}]".format(
            self.__class__.__name__,
            self.value,
            self.opcode,
            self.funct3,
            self.funct7,
            self.rs1,
            self.rs2,
            self.rd,
            hex(self.imm) if self.imm != None else None,
        )


class MayJumpInst:
    pass


class Format_R(InstFormat):
    pass


class Format_I(InstFormat):

    def __init__(self, value) -> None:
        super().__init__(value)
        r = bitcut(self.value, 20, 31)
        self.imm = util.msb_extend(r, 12, 32)


class Format_S(InstFormat):

    def __init__(self, value) -> None:
        super().__init__(value)
        low = bitcut(self.value, 7, 11)
        high = bitcut(self.value, 25, 31)
        r = (high << 5) | low
        self.imm = util.msb_extend(r, 12, 32)


class Format_U(InstFormat):

    def __init__(self, value) -> None:
        super().__init__(value)
        r = bitcut(self.value, 12, 31)
        self.imm = util.msb_extend(r, 20, 32)


class Format_B(InstFormat, MayJumpInst):

    def __init__(self, value) -> None:
        super().__init__(value)
        low = bitcut(self.value, 8, 11) << 1
        high = bitcut(self.value, 25, 30) << 5
        r = (
            (bitcut(self.value, 31, 31) << 12)
            | (bitcut(self.value, 7, 7) << 11)
            | high
            | low
        )
        self.imm = util.msb_extend(r, 13, 32)


class Format_J(InstFormat, MayJumpInst):

    def __init__(self, value) -> None:
        super().__init__(value)
        low = bitcut(self.value, 21, 30) << 1
        high = bitcut(self.value, 12, 19) << 12
        r = (
            (bitcut(self.value, 31, 31) << 20)
            | high
            | (bitcut(self.value, 20, 20) << 11)
            | low
        )
        self.imm = util.msb_extend(r, 21, 32)


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
        rs1 = util.msb_extend(
            _cpu.regs[self.rs1], _cpu.XLEN, _cpu.XLEN + _cpu.regs[self.rs2]
        )
        _cpu.regs[self.rd] = rs1 >> (_cpu.regs[self.rs2] & 0x1F)


class SLT(Format_R):

    def exec(self, _cpu: cpu.CPU):
        rs1 = util.u2s(_cpu.regs[self.rs1], _cpu.XLEN)
        rs2 = util.u2s(_cpu.regs[self.rs2], _cpu.XLEN)
        v = 1 if rs1 < rs2 else 0
        _cpu.regs[self.rd] = v


class SLTU(Format_R):

    def exec(self, _cpu: cpu.CPU):
        v = 1 if _cpu.regs[self.rs1] < _cpu.regs[self.rs2] else 0
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
        s = self.imm & 0x1F
        _cpu.regs[self.rd] = _cpu.regs[self.rs1] << s


class SRLI(Format_I):

    def exec(self, _cpu: cpu.CPU):
        s = self.imm & 0x1F
        _cpu.regs[self.rd] = _cpu.regs[self.rs1] >> s


class SRAI(Format_I):

    def exec(self, _cpu: cpu.CPU):
        s = self.imm & 0x1F
        rs1 = util.msb_extend(
            _cpu.regs[self.rs1], _cpu.XLEN, _cpu.XLEN + _cpu.regs[self.rs2]
        )
        _cpu.regs[self.rd] = rs1 >> s


class SLTI(Format_I):

    def exec(self, _cpu: cpu.CPU):
        rs1 = util.u2s(_cpu.regs[self.rs1], _cpu.XLEN)
        imm = util.u2s(self.imm, _cpu.XLEN)
        v = 1 if rs1 < imm else 0
        _cpu.regs[self.rd] = v


class SLTIU(Format_I):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = 1 if _cpu.regs[self.rs1] < self.imm & 0xFFFFFFFF else 0


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
        _cpu._addrspace.u16[_cpu.regs[self.rs1] + self.imm] = (
            _cpu.regs[self.rs2] & 0xFFFF
        )


class SW(Format_S):

    def exec(self, _cpu: cpu.CPU):
        _cpu._addrspace.u32[_cpu.regs[self.rs1] + self.imm] = _cpu.regs[self.rs2]


# Branch:


class BEQ(Format_B):

    def exec(self, _cpu: cpu.CPU):
        if _cpu.regs[self.rs1] == _cpu.regs[self.rs2]:
            _cpu.pc += self.imm


class BNE(Format_B):

    def exec(self, _cpu: cpu.CPU):
        if _cpu.regs[self.rs1] != _cpu.regs[self.rs2]:
            _cpu.pc += self.imm


class BLT(Format_B):

    def exec(self, _cpu: cpu.CPU):
        if util.u2s(_cpu.regs[self.rs1], 32) < util.u2s(_cpu.regs[self.rs2], 32):
            _cpu.pc += self.imm


class BGE(Format_B):

    def exec(self, _cpu: cpu.CPU):
        if util.u2s(_cpu.regs[self.rs1], 32) >= util.u2s(_cpu.regs[self.rs2], 32):
            _cpu.pc += self.imm


class BLTU(Format_B):

    def exec(self, _cpu: cpu.CPU):
        if _cpu.regs[self.rs1] < _cpu.regs[self.rs2]:
            _cpu.pc += self.imm


class BGEU(Format_B):

    def exec(self, _cpu: cpu.CPU):
        if _cpu.regs[self.rs1] >= _cpu.regs[self.rs2]:
            _cpu.pc += self.imm


# Jump:


class JAL(Format_J):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu.pc + 4
        _cpu.pc += self.imm


class JALR(Format_I, MayJumpInst):

    def exec(self, _cpu: cpu.CPU):
        old_pc = _cpu.pc
        _cpu.pc = (_cpu.regs[self.rs1] + self.imm) & 0xFFFFFFFE
        _cpu.regs[self.rd] = old_pc + 4


# Upper IMM:


class LUI(Format_U):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = self.imm << 12


class AUIPC(Format_U):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu.pc + (self.imm << 12)


# Environment


class Format_UI(Format_I):

    def __init__(self, value) -> None:
        super().__init__(value)
        self.imm &= 0xFFF


class ECALL(Format_UI, MayJumpInst):

    def exec(self, _cpu: cpu.CPU):
        if cpu.MODE_M == _cpu.mode:
            cause = cpu.EXCEPTION_ECALL_FROM_M
        elif cpu.MODE_S == _cpu.mode:
            cause = cpu.EXCEPTION_ECALL_FROM_S
        elif cpu.MODE_U == _cpu.mode:
            cause = cpu.EXCEPTION_ECALL_FROM_U
        else:
            raise RuntimeError("unknown cpu mode:{}".format(_cpu.mode))
        _cpu._go_trap(cause)


class EBREAK(Format_UI):
    pass


class MRET(Format_UI, MayJumpInst):

    def exec(self, _cpu: cpu.CPU):
        _cpu.pc = _cpu.csr.mepc
        _cpu.csr.mstatus.MIE = _cpu.csr.mstatus.MPIE
        _cpu.csr.mstatus.MPIE = 1
        _cpu.mode = _cpu.csr.mstatus.MPP
        _cpu.csr.mstatus.MPP = 0  # ?


class SRET(Format_UI, MayJumpInst):

    def exec(self, _cpu: cpu.CPU):
        _cpu.pc = _cpu.csr.sepc
        _cpu.csr.sstatus.SIE = _cpu.csr.sstatus.SPIE
        _cpu.csr.sstatus.SPIE = 1
        _cpu.mode = _cpu.csr.sstatus.SPP
        _cpu.csr.sstatus.SPP = 0  # ?


class SFENCEvma(Format_R, MayJumpInst):

    def exec(self, _cpu: cpu.CPU):
        if self.rs2 and _cpu.regs[self.rs2] in _cpu._addrspace.pte_cache:
            _cpu._addrspace.pte_cache[_cpu.regs[self.rs2]].clear()
        else:
            _cpu._addrspace.pte_cache.clear()


class WFI(Format_UI):

    def exec(self, _cpu: cpu.CPU):
        pass


# CSR


class CSRRW(Format_UI, MayJumpInst):

    def exec(self, _cpu: cpu.CPU):
        rs1 = _cpu.regs[self.rs1]
        if self.rd:
            _cpu.regs[self.rd] = _cpu.csr[self.imm]
        _cpu.csr[self.imm] = rs1


class CSRRS(Format_UI, MayJumpInst):

    def exec(self, _cpu: cpu.CPU):
        rs1 = _cpu.regs[self.rs1]
        _cpu.regs[self.rd] = _cpu.csr[self.imm]
        if rs1:
            _cpu.csr[self.imm] |= rs1


class CSRRC(Format_UI, MayJumpInst):

    def exec(self, _cpu: cpu.CPU):
        rs1 = _cpu.regs[self.rs1]
        _cpu.regs[self.rd] = _cpu.csr[self.imm]
        if rs1:
            _cpu.csr[self.imm] &= ~rs1


class CSRRWI(Format_UI, MayJumpInst):

    def exec(self, _cpu: cpu.CPU):
        if self.rd:
            _cpu.regs[self.rd] = _cpu.csr[self.imm]
        _cpu.csr[self.imm] = self.rs1


class CSRRSI(Format_UI, MayJumpInst):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu.csr[self.imm]
        if self.rs1:
            _cpu.csr[self.imm] |= self.rs1


class CSRRCI(Format_UI, MayJumpInst):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs[self.rd] = _cpu.csr[self.imm]
        if self.rs1:
            _cpu.csr[self.imm] &= ~self.rs1


class FENCE(Format_I):

    def exec(self, _cpu: cpu.CPU):
        pass


# ATOMIC


class FORMAT_ATOMIC(Format_R):

    def __init__(self, value) -> None:
        super().__init__(value)
        self.aq = util.get_bit(self.value, 26)
        self.rl = util.get_bit(self.value, 25)
        self.funct5 = bitcut(self.value, 27, 31)


class LRw(FORMAT_ATOMIC):

    def exec(self, _cpu: cpu.CPU):
        data = _cpu._addrspace.u32[_cpu.regs[self.rs1]]
        _cpu.regs[self.rd] = data
        _cpu._addrspace.reserve[_cpu] = str(_cpu.regs[self.rs1]) + str(data)


class SCw(FORMAT_ATOMIC):

    def exec(self, _cpu: cpu.CPU):
        data = _cpu._addrspace.u32[_cpu.regs[self.rs1]]
        if str(_cpu.regs[self.rs1]) + str(data) == _cpu._addrspace.reserve[_cpu]:
            _cpu._addrspace.u32[_cpu.regs[self.rs1]] = _cpu.regs[self.rs2]
            _cpu.regs[self.rd] = 0
        else:
            _cpu.regs[self.rd] = 1
        _cpu._addrspace.reserve[_cpu] = None


class FORMAT_AMO(FORMAT_ATOMIC):

    def exec(self, _cpu: cpu.CPU):
        addr = _cpu.regs[self.rs1]
        # load
        mem_value = _cpu._addrspace.u32[addr]
        rs2_value = _cpu.regs[self.rs2]
        # op
        mem_value, rd_value = self.get_memvalue_rdvalue(mem_value, rs2_value)
        # logging.debug(_cpu.regs)
        # logging.debug("get_memvalue_rdvalue return {}".format(hex(value)))
        # store
        _cpu.regs[self.rd] = rd_value
        _cpu._addrspace.u32[addr] = mem_value & 0xFFFFFFFF

    def get_memvalue_rdvalue(self, mem_value, rs2_value):
        """
        return mem_value, rd_value
        """
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
        return (util.u2s(rs1, 32) * util.u2s(rs2, 32)) >> 32


class MULHSU(Format_MULDIV):

    def calc_rd(self, rs1, rs2):
        return (util.u2s(rs1, 32) * rs2) >> 32


class MULHU(Format_MULDIV):

    def calc_rd(self, rs1, rs2):
        return (rs1 * rs2) >> 32


class DIV(Format_MULDIV):

    def calc_rd(self, rs1, rs2):
        if rs2:
            rs1 = util.u2s(rs1, 32)
            rs2 = util.u2s(rs2, 32)
            if rs1 == -(2 ** (32 - 1)) and rs2 == -1:
                return -(2 ** (32 - 1))
            return math.trunc(util.u2s(rs1, 32) / util.u2s(rs2, 32))
        else:
            return 0xFFFFFFFF


class DIVU(Format_MULDIV):

    def calc_rd(self, rs1, rs2):
        if rs2:
            return math.trunc(rs1 / rs2)
        else:
            return -1


class REM(Format_MULDIV):

    def calc_rd(self, rs1, rs2):
        if rs2:
            rs1 = util.u2s(rs1, 32)
            rs2 = util.u2s(rs2, 32)
            if rs1 == -(2 ** (32 - 1)) and rs2 == -1:
                return 0
            return rs1 - math.trunc(rs1 / rs2) * rs2
        else:
            return rs1


class REMU(Format_MULDIV):

    def calc_rd(self, rs1, rs2):
        if rs2:
            return rs1 - math.trunc(rs1 / rs2) * rs2
        else:
            return rs1


class CBOzero(Format_I):

    BLOCK_SIZE = 4096

    def exec(self, _cpu: cpu.CPU):
        # print("!!!!!!!!!!!!!!!!!CBO.ZERO {}".format(hex(_cpu.regs[self.rs1])))
        _cpu._addrspace.write(_cpu.regs[self.rs1], bytes(CBOzero.BLOCK_SIZE))
