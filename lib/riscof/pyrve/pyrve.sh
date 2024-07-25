#!/bin/bash

set -e

elf=$1
sig=$2

addrs=$(~/xpack-riscv-none-elf-gcc-13.2.0-2/bin/riscv-none-elf-objdump -t $elf | grep begin_signature | cut -d" " -f1)
addre=$(~/xpack-riscv-none-elf-gcc-13.2.0-2/bin/riscv-none-elf-objdump -t $elf | grep end_signature | cut -d" " -f1)
~/xpack-riscv-none-elf-gcc-13.2.0-2/bin/riscv-none-elf-objcopy -O binary $elf "code.bin"
cd $(dirname $sig)
echo $sig $addrs $addre >> /tmp/pyrve.log
set +e
(timeout 120 python /media/hu2/Temp/rve/cof.py "code.bin" $sig $addrs $addre) || echo 'exception' > $sig

# export PATH=/home/hu2/Downloads/riscv32-unknown-elf.gcc-13.2.0/bin/:$PATH
# riscof --verbose info run --config ./config.ini --suite ./riscv-arch-test/riscv-test-suite/rv32i_m --env ./riscv-arch-test/riscv-test-suite/env --work-dir /media/hu2/Program/riscv_work/
