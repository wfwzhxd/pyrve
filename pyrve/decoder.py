import functools
from . import util
import logging

logger = logging.getLogger(__name__)

@functools.lru_cache(maxsize=2048*10)
def decode(inst_value):
    from . import inst
    t = inst.InstFormat(inst_value)
    inst_class = None
    if 0b0110011 == t.opcode:   
        # Base Reg
        if 0x1 == t.funct7: # MUL/DIV
            if 0x0 == t.funct3:
                inst_class = inst.MUL
            elif 0x1 == t.funct3:
                inst_class = inst.MULH
            elif 0x2 == t.funct3:
                inst_class = inst.MULHSU
            elif 0x3 == t.funct3:
                inst_class = inst.MULHU
            elif 0x4 == t.funct3:
                inst_class = inst.DIV
            elif 0x5 == t.funct3:
                inst_class = inst.DIVU
            elif 0x6 == t.funct3:
                inst_class = inst.REM
            elif 0x7 == t.funct3:
                inst_class = inst.REMU
            else:
                pass
        else:
            if 0x0 == t.funct3:
                if 0x0 == t.funct7:
                    inst_class = inst.ADD
                elif 0x20 == t.funct7:
                    inst_class = inst.SUB
                else:
                    pass
            elif 0x4 == t.funct3 and 0x0 == t.funct7:
                inst_class = inst.XOR
            elif 0x6 == t.funct3 and 0x0 == t.funct7:
                inst_class = inst.OR
            elif 0x7 == t.funct3 and 0x0 == t.funct7:
                inst_class = inst.AND
            elif 0x1 == t.funct3 and 0x0 == t.funct7:
                inst_class = inst.SLL
            elif 0x5 == t.funct3:
                if 0x0 == t.funct7:
                    inst_class = inst.SRL
                elif 0x20 == t.funct7:
                    inst_class = inst.SRA
                else:
                    pass
            elif 0x2 == t.funct3 and 0x0 == t.funct7:
                inst_class = inst.SLT
            elif 0x3 == t.funct3 and 0x0 == t.funct7:
                inst_class = inst.SLTU
            else:
                pass
    elif 0b0010011 == t.opcode:  # Base Imm
        t = inst.Format_I(inst_value)
        if 0x0 == t.funct3:
            inst_class = inst.ADDI
        elif 0x4 == t.funct3:
            inst_class = inst.XORI
        elif 0x6 == t.funct3:
            inst_class = inst.ORI
        elif 0x7 == t.funct3:
            inst_class = inst.ANDI
        elif 0x1 == t.funct3 and 0x0 == util.bitcut(t.imm, 5, 11):
            inst_class = inst.SLLI
        elif 0x5 == t.funct3 and 0x0 == util.bitcut(t.imm, 5, 11):
            inst_class = inst.SRLI
        elif 0x5 == t.funct3 and 0x20 == util.bitcut(t.imm, 5, 11):
            inst_class = inst.SRAI
        elif 0x2 == t.funct3:
            inst_class = inst.SLTI
        elif 0x3 == t.funct3:
            inst_class = inst.SLTIU
        else:
            pass
    elif 0b0000011 == t.opcode: # Load
        if 0x0 == t.funct3:
            inst_class = inst.LB
        elif 0x1 == t.funct3:
            inst_class = inst.LH
        elif 0x2 == t.funct3:
            inst_class = inst.LW
        elif 0x4 == t.funct3:
            inst_class = inst.LBU
        elif 0x5 == t.funct3:
            inst_class = inst.LHU
        else:
            pass
    elif 0b0100011 == t.opcode: # Store
        if 0x0 == t.funct3:
            inst_class = inst.SB
        elif 0x1 == t.funct3:
            inst_class = inst.SH
        elif 0x2 == t.funct3:
            inst_class = inst.SW
        else:
            pass
    elif 0b1100011 == t.opcode: # Branch
        if 0x0 == t.funct3:
            inst_class = inst.BEQ
        elif 0x1 == t.funct3:
            inst_class = inst.BNE
        elif 0x4 == t.funct3:
            inst_class = inst.BLT
        elif 0x5 == t.funct3:
            inst_class = inst.BGE
        elif 0x6 == t.funct3:
            inst_class = inst.BLTU
        elif 0x7 == t.funct3:
            inst_class = inst.BGEU
        else:
            pass
    elif 0b1101111 == t.opcode: # Jal
        inst_class = inst.JAL
    elif 0b1100111 == t.opcode: # Jalr
        if 0x0 == t.funct3:
            inst_class = inst.JALR
    elif 0b0110111 == t.opcode: # Lui
        inst_class = inst.LUI
    elif 0b0010111 == t.opcode: # Auipc
        inst_class = inst.AUIPC
    elif 0b1110011 == t.opcode: # System
        t = inst.Format_UI(inst_value)
        if 0x0 == t.funct3:
            if 0x0 == t.imm:
                inst_class = inst.ECALL
            elif 0x1 == t.imm:
                inst_class = inst.EBREAK
            elif 0x302 == t.imm:
                inst_class = inst.MRET
            elif 0x102 == t.imm:
                inst_class = inst.SRET
            elif 0x105 == t.imm:
                inst_class = inst.WFI
            elif 0x09 == t.funct7:
                inst_class = inst.SFENCEvma
        # CSR
        elif 0x1 == t.funct3:
            inst_class = inst.CSRRW
        elif 0x2 == t.funct3:
            inst_class = inst.CSRRS
        elif 0x3 == t.funct3:
            inst_class = inst.CSRRC
        elif 0x5 == t.funct3:
            inst_class = inst.CSRRWI
        elif 0x6 == t.funct3:
            inst_class = inst.CSRRSI
        elif 0x7 == t.funct3:
            inst_class = inst.CSRRCI
        else:
            pass
    elif 0b0001111 == t.opcode: # Fence
        t = inst.Format_I(inst_value)
        if 0 == t.funct3:
            inst_class = inst.FENCE
        if 1 == t.funct3:
            inst_class = inst.FENCE # fenci.i, current not use
        elif 2 == t.funct3: # CBO
            if 4 == t.imm:
                inst_class = inst.CBOzero
    elif 0b0101111 == t.opcode:   # Atomic
        t = inst.FORMAT_ATOMIC(inst_value)
        if 0x2 == t.funct3:
            if 0x02 == t.funct5:
                inst_class = inst.LRw
            elif 0x03 == t.funct5:
                inst_class = inst.SCw
            elif 0x01 == t.funct5:
                inst_class = inst.AMOSWAPw
            elif 0x00 == t.funct5:
                inst_class = inst.AMOADDw
            elif 0x0C == t.funct5:
                inst_class = inst.AMOANDw
            elif 0x08 == t.funct5:
                inst_class = inst.AMOORw
            elif 0x04 == t.funct5:
                inst_class = inst.AMOXORw
            elif 0x14 == t.funct5:
                inst_class = inst.AMOMAXw
            elif 0x10 == t.funct5:
                inst_class = inst.AMOMINw
            elif 0x18 == t.funct5:
                inst_class = inst.AMOMINUw
            elif 0x1C == t.funct5:
                inst_class = inst.AMOMAXUw
            else:
                pass
    else:
        pass
    if not inst_class:
        raise RuntimeError("Undecode inst({})".format(hex(inst_value)))
    return inst_class(inst_value)
