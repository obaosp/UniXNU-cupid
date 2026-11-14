// SPDX-License-Identifier: BSD-2-Clause-Patent
// Cupid bring-up stub. The full sheng UFS log writer (BootLog.c) also composes
// the BootProgress, VM and verified-root rows, whose symbols live in sheng's
// board-page components that cupid does not have yet. SourceStorage only needs
// the writer state; the full source is kept in package/sheng-full/BootLog.c and
// can replace this file once those board pages are ported.
volatile unsigned int boot_log_state, boot_log_rounds, boot_log_errors;
const char *volatile boot_log_open_refusal = "boot log not ported (cupid bring-up)";

void boot_log_tick(unsigned now)
{
    (void) now;
}
