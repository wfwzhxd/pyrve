import util
import cpu

bitcut = lambda v,l,h:((v&(2<<h)-1))>>l

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
        _cpu.regs.set_x(self.rd, _cpu.regs.get_x(self.rs1)+_cpu.regs.get_x(self.rs2))

class SUB(Format_R):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs.set_x(self.rd, _cpu.regs.get_x(self.rs1)-_cpu.regs.get_x(self.rs2))

class XOR(Format_R):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs.set_x(self.rd, _cpu.regs.get_x(self.rs1)^_cpu.regs.get_x(self.rs2))

class OR(Format_R):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs.set_x(self.rd, _cpu.regs.get_x(self.rs1)|_cpu.regs.get_x(self.rs2))

class AND(Format_R):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs.set_x(self.rd, _cpu.regs.get_x(self.rs1)&_cpu.regs.get_x(self.rs2))

class SLL(Format_R):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs.set_x(self.rd, _cpu.regs.get_x(self.rs1)<<_cpu.regs.get_x(self.rs2))

class SRL(Format_R):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs.set_x(self.rd, _cpu.regs.get_x(self.rs1)>>_cpu.regs.get_x(self.rs2))

class SRA(Format_R):

    def exec(self, _cpu: cpu.CPU):
        rs1 = util.msb_extend(_cpu.regs.get_x(self.rs1), _cpu.XLEN, _cpu.XLEN+_cpu.regs.get_x(self.rs2))
        _cpu.regs.set_x(self.rd, rs1>>_cpu.regs.get_x(self.rs2))

class SLT(Format_R):

    def exec(self, _cpu: cpu.CPU):
        rs1 = util.u2s(_cpu.regs.get_x(self.rs1), _cpu.XLEN)
        rs2 = util.u2s(_cpu.regs.get_x(self.rs2), _cpu.XLEN)
        v = 1 if rs1<rs2 else 0
        _cpu.regs.set_x(self.rd, v)

class SLTU(Format_R):

    def exec(self, _cpu: cpu.CPU):
        v = 1 if _cpu.regs.get_x(self.rs1)<_cpu.regs.get_x(self.rs2) else 0
        _cpu.regs.set_x(self.rd, v)


# Base IMM:

class ADDI(Format_I):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs.set_x(self.rd, _cpu.regs.get_x(self.rs1)+self.imm)

class XORI(Format_I):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs.set_x(self.rd, _cpu.regs.get_x(self.rs1)^self.imm)

class ORI(Format_I):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs.set_x(self.rd, _cpu.regs.get_x(self.rs1)|self.imm)

class ANDI(Format_I):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs.set_x(self.rd, _cpu.regs.get_x(self.rs1)&self.imm)

class SLLI(Format_I):

    def exec(self, _cpu: cpu.CPU):
        s = self.imm&0x1F
        _cpu.regs.set_x(self.rd, _cpu.regs.get_x(self.rs1)<<s)

class SRLI(Format_I):

    def exec(self, _cpu: cpu.CPU):
        s = self.imm&0x1F
        _cpu.regs.set_x(self.rd, _cpu.regs.get_x(self.rs1)>>s)

class SRAI(Format_I):

    def exec(self, _cpu: cpu.CPU):
        s = self.imm&0x1F
        rs1 = util.msb_extend(_cpu.regs.get_x(self.rs1), _cpu.XLEN, _cpu.XLEN+_cpu.regs.get_x(self.rs2))
        _cpu.regs.set_x(self.rd, rs1>>s)

class SLTI(Format_I):

    def exec(self, _cpu: cpu.CPU):
        rs1 = util.u2s(_cpu.regs.get_x(self.rs1), _cpu.XLEN)
        imm = util.u2s(self.imm, _cpu.XLEN)
        v = 1 if rs1<imm else 0
        _cpu.regs.set_x(self.rd, v)

class SLTIU(Format_I):

    def exec(self, _cpu: cpu.CPU):
        v = 1 if _cpu.regs.get_x(self.rs1)<self.imm else 0
        _cpu.regs.set_x(self.rd, v)

# Load Store:

class LB(Format_I):

    def exec(self, _cpu: cpu.CPU):
        address = (_cpu.regs.get_x(self.rs1) + self.imm)&cpu.CPU.XMASK
        v = util.LittleEndness.read8u(_cpu._addrspace, address)
        _cpu.regs.set_x(self.rd, util.msb_extend(v, 8, 32))

class LH(Format_I):

    def exec(self, _cpu: cpu.CPU):
        address = (_cpu.regs.get_x(self.rs1) + self.imm)&cpu.CPU.XMASK
        v = util.LittleEndness.read16u(_cpu._addrspace, address)
        _cpu.regs.set_x(self.rd, util.msb_extend(v, 16, 32))

class LW(Format_I):

    def exec(self, _cpu: cpu.CPU):
        address = (_cpu.regs.get_x(self.rs1) + self.imm)&cpu.CPU.XMASK
        v = util.LittleEndness.read32u(_cpu._addrspace, address)
        _cpu.regs.set_x(self.rd, v)

class LBU(Format_I):

    def exec(self, _cpu: cpu.CPU):
        address = (_cpu.regs.get_x(self.rs1) + self.imm)&cpu.CPU.XMASK
        v = util.LittleEndness.read8u(_cpu._addrspace, address)
        _cpu.regs.set_x(self.rd, v)

class LHU(Format_I):

    def exec(self, _cpu: cpu.CPU):
        address = (_cpu.regs.get_x(self.rs1) + self.imm)&cpu.CPU.XMASK
        v = util.LittleEndness.read16u(_cpu._addrspace, address)
        _cpu.regs.set_x(self.rd, v)

class SB(Format_S):

    def exec(self, _cpu: cpu.CPU):
        address = (_cpu.regs.get_x(self.rs1) + self.imm)&cpu.CPU.XMASK
        util.LittleEndness.write8u(_cpu._addrspace, address, _cpu.regs.get_x(self.rs2))

class SH(Format_S):

    def exec(self, _cpu: cpu.CPU):
        address = (_cpu.regs.get_x(self.rs1) + self.imm)&cpu.CPU.XMASK
        util.LittleEndness.write16u(_cpu._addrspace, address, _cpu.regs.get_x(self.rs2)&0XFFFF)

class SW(Format_S):

    def exec(self, _cpu: cpu.CPU):
        address = (_cpu.regs.get_x(self.rs1) + self.imm)&cpu.CPU.XMASK
        util.LittleEndness.write32u(_cpu._addrspace, address, _cpu.regs.get_x(self.rs2))

# Branch:

class BEQ(Format_B):

    def exec(self, _cpu: cpu.CPU):
        if (util.u2s(_cpu.regs.get_x(self.rs1), 32) == util.u2s(_cpu.regs.get_x(self.rs2), 32)):
            _cpu.regs.pc += self.imm

class BNE(Format_B):

    def exec(self, _cpu: cpu.CPU):
        if (util.u2s(_cpu.regs.get_x(self.rs1), 32) != util.u2s(_cpu.regs.get_x(self.rs2), 32)):
            _cpu.regs.pc += self.imm

class BLT(Format_B):

    def exec(self, _cpu: cpu.CPU):
        if (util.u2s(_cpu.regs.get_x(self.rs1), 32) < util.u2s(_cpu.regs.get_x(self.rs2), 32)):
            _cpu.regs.pc += self.imm

class BGE(Format_B):

    def exec(self, _cpu: cpu.CPU):
        if (util.u2s(_cpu.regs.get_x(self.rs1), 32) >= util.u2s(_cpu.regs.get_x(self.rs2), 32)):
            _cpu.regs.pc += self.imm

class BLTU(Format_B):

    def exec(self, _cpu: cpu.CPU):
        if (_cpu.regs.get_x(self.rs1) < _cpu.regs.get_x(self.rs2)):
            _cpu.regs.pc += self.imm

class BGEU(Format_B):

    def exec(self, _cpu: cpu.CPU):
        if (_cpu.regs.get_x(self.rs1) >= _cpu.regs.get_x(self.rs2)):
            _cpu.regs.pc += self.imm

# Jump:

class JAL(Format_J):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs.set_x(self.rd, _cpu.regs.pc+4)
        _cpu.regs.pc += self.imm


class JALR(Format_I):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs.set_x(self.rd, _cpu.regs.pc+4)
        _cpu.regs.pc = _cpu.regs.get_x(self.rs1) + self.imm


# Upper IMM:

class LUI(Format_U):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs.set_x(self.rd, self.imm<<12)

class AUIPC(Format_U):

    def exec(self, _cpu: cpu.CPU):
        _cpu.regs.set_x(self.rd, _cpu.regs.pc + (self.imm<<12))

# Environment

class Format_UI(Format_I):

    @property
    def imm(self):
        return super().imm & 0xFFF

class ECALL(Format_UI):
    
    def exec(self, _cpu: cpu.CPU):
        _cpu._go_mtrap(0x0000000B)

class EBREAK(Format_UI):
    pass

class MRET(Format_UI):
    
    def exec(self, _cpu: cpu.CPU):
        _cpu.regs.pc = _cpu.csr.mepc
        _cpu.csr.mstatus = util.set_bit(_cpu.csr.mstatus, cpu.MIE_BIT)

# CSR

class CSRRW(Format_UI):
    
    def exec(self, _cpu: cpu.CPU):
        if self.rd:
            _cpu.regs.set_x(self.rd, _cpu.csr.read(self.imm))
        _cpu.csr.write(self.imm, _cpu.regs.get_x(self.rs1))

class CSRRS(Format_UI):

    def exec(self, _cpu: cpu.CPU):
        old_csr = _cpu.csr.read(self.imm)
        _cpu.regs.set_x(self.rd, old_csr)
        new_v = _cpu.regs.get_x(self.rs1)
        if new_v:
            _cpu.csr.write(self.imm, old_csr|new_v)

class CSRRC(Format_UI):
    
    def exec(self, _cpu: cpu.CPU):
        old_csr = _cpu.csr.read(self.imm)
        _cpu.regs.set_x(self.rd, old_csr)
        new_v = _cpu.regs.get_x(self.rs1)
        if new_v:
            _cpu.csr.write(self.imm, old_csr&~new_v)

class CSRRWI(Format_UI):
    
    def exec(self, _cpu: cpu.CPU):
        if self.rd:
            _cpu.regs.set_x(self.rd, _cpu.csr.read(self.imm))
        _cpu.csr.write(self.imm, self.rs1)

class CSRRSI(Format_UI):
    
    def exec(self, _cpu: cpu.CPU):
        old_csr = _cpu.csr.read(self.imm)
        _cpu.regs.set_x(self.rd, old_csr)
        new_v = self.rs1
        if new_v:
            _cpu.csr.write(self.imm, old_csr|new_v)

class CSRRCI(Format_UI):
    
    def exec(self, _cpu: cpu.CPU):
        old_csr = _cpu.csr.read(self.imm)
        _cpu.regs.set_x(self.rd, old_csr)
        new_v = self.rs1
        if new_v:
            _cpu.csr.write(self.imm, old_csr&~new_v)
