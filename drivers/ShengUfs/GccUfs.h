// SPDX-License-Identifier: BSD-2-Clause-Patent
// SM8450 (waipio) GCC registers used by UFS. Transcribed from the public
// mainline Linux gcc-sm8450.c and the device header
// UniXNU-sm8450-common/kits/Sm8450Platform/GccUfs.h.
#ifndef NATIVE_UFS_GCC_UFS_H
#define NATIVE_UFS_GCC_UFS_H

#define GCC_BASE                      0x00100000ULL
#define UFS_HC_BASE                   0x01d84000ULL
#define UFS_HC_SIZE                   0x3000ULL
#define GCC_UFS_WINDOW                0x87000

#define GCC_UFS_PHY_GDSCR             0x87004
#define GCC_UFS_PHY_AXI_ENABLE        0x87018
#define GCC_UFS_PHY_AHB_ENABLE        0x87020
#define GCC_UFS_PHY_TX_SYMBOL0_ENABLE 0x87024
#define GCC_UFS_PHY_RX_SYMBOL0_ENABLE 0x87028
#define GCC_UFS_PHY_UNIPRO_CORE_ENABLE 0x87064
#define GCC_UFS_PHY_ICE_CORE_ENABLE   0x8706c
#define GCC_UFS_PHY_PHY_AUX_ENABLE    0x870a4
#define GCC_UFS_PHY_RX_SYMBOL1_ENABLE 0x870c0
#define GCC_AGGRE_UFS_PHY_AXI_ENABLE  0x870d4

#define GCC_UFS_BRANCH_ENABLE_BIT     0x1U

// SM8450 has no separate UFS_MEM_PHY_GDSC (SM8550's 0x9e000); do not read it.
#endif
