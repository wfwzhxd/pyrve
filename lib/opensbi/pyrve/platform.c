/*
 * SPDX-License-Identifier: BSD-2-Clause
 *
 * Copyright (c) 2019 Western Digital Corporation or its affiliates.
 */

#include <sbi/riscv_asm.h>
#include <sbi/riscv_encoding.h>
#include <sbi/sbi_const.h>
#include <sbi/sbi_platform.h>

/*
 * Include these files as needed.
 * See objects.mk PLATFORM_xxx configuration parameters.
 */
#include <sbi_utils/ipi/aclint_mswi.h>
#include <sbi_utils/serial/uart8250.h>
#include <sbi_utils/timer/aclint_mtimer.h>


#define PLATFORM_HART_COUNT		1
#define PLATFORM_ACLINT_MTIMER_FREQ	10000000

#define PLATFORM_UART_ADDR		0x10000000
#define PLATFORM_UART_INPUT_FREQ	10000000
#define PLATFORM_UART_BAUDRATE		115200

#define PLATFORM_CLINT_ADDR		0x2000000
#define PLATFORM_ACLINT_MTIMER_FREQ	10000000


static struct aclint_mswi_data mswi = {
	.addr = 0x2000000 + 0x0,
	.size = 0x4000,
	.first_hartid = 0,
	.hart_count = PLATFORM_HART_COUNT,
};

static struct aclint_mtimer_data mtimer = {
	.mtime_freq = PLATFORM_ACLINT_MTIMER_FREQ,
	.mtime_addr = 0x2000000 + 0xbff8,
	.mtime_size = ACLINT_DEFAULT_MTIME_SIZE,
	.mtimecmp_addr = 0x2000000 + 0x4000,
	.mtimecmp_size = ACLINT_DEFAULT_MTIMECMP_SIZE,
	.first_hartid = 0,
	.hart_count = PLATFORM_HART_COUNT,
	.has_64bit_mmio = true,
};

/*
 * Initialize the platform console.
 */
static int platform_console_init(void)
{
	*(uint32_t *)PLATFORM_UART_ADDR = 'f';
	/* Example if the generic UART8250 driver is used */
	return uart8250_init(PLATFORM_UART_ADDR, PLATFORM_UART_INPUT_FREQ,
			     PLATFORM_UART_BAUDRATE, 0, 1, 0);
}

/*
 * Initialize IPI for current HART.
 */
static int platform_ipi_init(bool cold_boot)
{
	int ret;

	/* Example if the generic ACLINT driver is used */
	if (cold_boot) {
		ret = aclint_mswi_cold_init(&mswi);
		if (ret)
			return ret;
	}

	return aclint_mswi_warm_init();
}


/*
 * Initialize platform timer for current HART.
 */
static int platform_timer_init(bool cold_boot)
{
	int ret;

	/* Example if the generic ACLINT driver is used */
	if (cold_boot) {
		ret = aclint_mtimer_cold_init(&mtimer, NULL);
		if (ret)
			return ret;
	}

	return aclint_mtimer_warm_init();
}

/*
 * Platform descriptor.
 */
const struct sbi_platform_operations platform_ops = {
	.console_init		= platform_console_init,
	.ipi_init		= platform_ipi_init,
	.timer_init		= platform_timer_init
};
const struct sbi_platform platform = {
	.opensbi_version	= OPENSBI_VERSION,
	.platform_version	= SBI_PLATFORM_VERSION(0x0, 0x00),
	.name			= "pyrve",
	.features		= SBI_PLATFORM_DEFAULT_FEATURES,
	.hart_count		= PLATFORM_HART_COUNT,
	.hart_stack_size	= SBI_PLATFORM_DEFAULT_HART_STACK_SIZE,
	.heap_size		= SBI_PLATFORM_DEFAULT_HEAP_SIZE(1),
	.platform_ops_addr	= (unsigned long)&platform_ops
};
