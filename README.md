# RISCV Emulator writen in Python3

## It can run Linux with MMU

### Features
- ISA
    - RV32IMA_zicsr
    - M/S/U mode
- Peripheral
    - UART
    - FLASH

### Start
 1. Install PyPy for performance.(optional)
 2. Run emulator:\
    ``pypy -m pyrve.emulator``
 3. Connect console:
    1. ``busybox telnet 127.0.0.1 8250``
    2. disable local echo: type Ctrl+C, then type 'c' to character mode.
 4. Wait Linux to boot up.
