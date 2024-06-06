
import util
import logging

logger = logging.getLogger(__name__)

def decode(inst_value):
    import inst
    t = inst.InstFormat(inst_value)
    inst_class = None
    if 0b0110011 == t.opcode:   # Base Reg
        if 0x0 == t.funct3:
            if 0x0 == t.funct7:
                inst_class = inst.ADD
            if 0x20 == t.funct7:
                inst_class = inst.SUB
        if 0x4 == t.funct3 and 0x0 == t.funct7:
            inst_class = inst.XOR
        if 0x6 == t.funct3 and 0x0 == t.funct7:
            inst_class = inst.OR
        if 0x7 == t.funct3 and 0x0 == t.funct7:
            inst_class = inst.AND
        if 0x1 == t.funct3 and 0x0 == t.funct7:
            inst_class = inst.SLL
        if 0x5 == t.funct3:
            if 0x0 == t.funct7:
                inst_class = inst.SRL
            if 0x20 == t.funct7:
                inst_class = inst.SRA
        if 0x2 == t.funct3 and 0x0 == t.funct7:
            inst_class = inst.SLT
        if 0x3 == t.funct3 and 0x0 == t.funct7:
            inst_class = inst.SLTU
    elif 0b0010011 == t.opcode:  # Base Imm
        t = inst.Format_I(inst_value)
        if 0x0 == t.funct3:
            inst_class = inst.ADDI
        if 0x4 == t.funct3:
            inst_class = inst.XORI
        if 0x6 == t.funct3:
            inst_class = inst.ORI
        if 0x7 == t.funct3:
            inst_class = inst.ANDI
        if 0x1 == t.funct3 and 0x0 == util.bitcut(t.imm, 5, 11):
            inst_class = inst.SLLI
        if 0x5 == t.funct3 and 0x0 == util.bitcut(t.imm, 5, 11):
            inst_class = inst.SRLI
        if 0x5 == t.funct3 and 0x20 == util.bitcut(t.imm, 5, 11):
            inst_class = inst.SRAI
        if 0x2 == t.funct3:
            inst_class = inst.SLTI
        if 0x3 == t.funct3:
            inst_class = inst.SLTIU
    elif 0b0000011 == t.opcode: # Load
        if 0x0 == t.funct3:
            inst_class = inst.LB
        if 0x1 == t.funct3:
            inst_class = inst.LH
        if 0x2 == t.funct3:
            inst_class = inst.LW
        if 0x4 == t.funct3:
            inst_class = inst.LBU
        if 0x5 == t.funct3:
            inst_class = inst.LHU
    elif 0b0100011 == t.opcode: # Store
        if 0x0 == t.funct3:
            inst_class = inst.SB
        if 0x1 == t.funct3:
            inst_class = inst.SH
        if 0x2 == t.funct3:
            inst_class = inst.SW
    elif 0b1100011 == t.opcode: # Branch
        if 0x0 == t.funct3:
            inst_class = inst.BEQ
        if 0x1 == t.funct3:
            inst_class = inst.BNE
        if 0x4 == t.funct3:
            inst_class = inst.BLT
        if 0x5 == t.funct3:
            inst_class = inst.BGE
        if 0x6 == t.funct3:
            inst_class = inst.BLTU
        if 0x7 == t.funct3:
            inst_class = inst.BGEU
    elif 0b1101111 == t.opcode: # Jal
        inst_class = inst.JAL
    elif 0b1100111 == t.opcode: # Jalr
        if 0x0 == t.funct3:
            inst_class = inst.JALR
    elif 0b0110111 == t.opcode: # Lui
        inst_class = inst.LUI
    elif 0b0010111 == t.opcode: # Auipc
        inst_class = inst.AUIPC
    elif 0b1110011 == t.opcode: # Environment
        t = inst.Format_I(inst_value)
        if 0x0 == t.funct3 and 0x0 == t.imm:
            inst_class = inst.ECALL
        if 0x0 == t.funct3 and 0x1 == t.imm:
            inst_class = inst.EBREAK
    if not inst_class:
        raise RuntimeError("Undecode inst({})".format(inst_value))
    result = inst_class(inst_value)
    logger.debug('value:{}, inst:{}'.format(inst_value, result))
    return result
