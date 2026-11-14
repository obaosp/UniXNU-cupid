# Root mount milestone — the next blocker is SM8450 UFS

Date: 2026-11-12 21:31. Image: `boot-v4-ios27.img` build `43296559153`
(sha256 `2166ad71…`), 36 stubbed imports.

## What happened

The kernel now gets past every remaining import stub and reaches BSD init.
The loader handoff screen (green/blue/magenta, `SecurityLock::LockType:
SOFTWARE_LOCK … LockCapsuleInterface`) stays for ~5 s, then the kernel panics:

```
Failed to mount root device            IOKitBSDInit.cpp:938
frames ... (native kernel)
```

`iokit/bsddev/IOKitBSDInit.cpp:938` is the iOS branch after
`IOService::waitForService(matching, &t)` has timed out 10 times
(`mountAttempts == 10`, `wdt != -1`):

```c
if ((-1 != wdt) && (!service || (mountAttempts == 10))) {
    ...
    panic("Failed to mount root device");
}
```

No `IOMedia` with the root volume UUID was published. The profile asks for
the iOS 27 OS volume:

```
[root] os_volume_uuid = E3F4AED0-4454-4D5B-833C-E27E99C4F67B
[payload.adt] root_match_volume_uuid = E3F4AED0-…
```

## Cause 1 (primary): no SM8450 UFS block driver

- `configs/cupid_ios27_defconfig` says **`CONFIG_XNU_NATIVE_UFS is not set`**.
- `package/Sm8450Ufs` is only `Sm8450UfsHci.h`, `Sm8450UfsRegs.h` and a host
  register test — no kext/block driver.
- sheng's `ShengUfs` targets SM8550: its GCC window (`0x770xx`) is not an
  offset of SM8450's (`0x870xx`); `port/UniXNU-sm8450-common/kits/Sm8450Platform/GccUfs.h`
  records the correct SM8450 clock/GDSC offsets.
- Without a block driver there is no `IOMedia` for the userdata partition or
  its windows, so the root match can never succeed. The kernel waits, then
  panics.

## Cause 2: the iOS 27 userdata image is not installed

The root content comes from the userdata partition's `SHNGROOT` windows
(docs/concepts/userdata): the unchanged OS and SystemOS images at 1 MiB
alignment behind a 4 KiB manifest. The CI `macos.yml` builds only the boot
image; `./unixnu userdata` is a separate step and needs macOS `/usr/bin/aea`
to decrypt the AEA images from the IPSW. Its output is
`out/<device>/<os>/<config>/userdata/userdata-root.img` plus
`userdata-root.json`, whose `flash_command` is
`fastboot flash userdata <image>`.

The phone's userdata currently has either no `SHNGROOT` or the iOS 26 windows
(`1A2E284A…`/`21AAD942…`), so even a working driver would not match the iOS 27
UUIDs.

## Next work

1. SM8450 UFS native block driver: UFSHCI init, UCD/PRDT, READ(10), GCC/PHY/
   ICE and SMMU, then publish the userdata windows as `IOMedia` (or parse the
   `SHNGROOT` manifest in the driver). Inputs: `package/Sm8450Ufs`,
   `Sm8450Platform/GccUfs.h`, `upstream/ShengUfs` (SM8550 reference).
2. Build and flash the iOS 27 userdata image on macOS (`./unixnu userdata
   --os 27`), or add a macOS Actions job that uploads it in <10 GB chunks.
3. Boot the same `boot-v4-ios27.img` and check for the OS volume match.

The stub-panic path is finished; this is the storage milestone the roadmap
already listed.

## Work started (2026-11-12 22:00)

- `patches/xnu/ufs-probe.patch` (device XNU series): at `IOFindBSDRoot`, when
  `unixnu-ufs-probe=1`, map GCC `0x187000` + UFSHCI `0x1d84000` and panic with
  the read-only register dump. It writes no register.
- `board.toml` carries `unixnu-ufs-probe=1` for build `43315093230`
  (`a91e0ba`); the diagnostic image is staged as
  `boot-v4-ios27-ufsprobe.img` (not `boot-v4-ios27.img`).
- `.github/workflows/userdata.yml` (manual dispatch) builds the iOS 27
  userdata image on macOS `./unixnu userdata --os 27`, splits it into two
  <10 GB artifacts (`cupid-userdata-aa`, `cupid-userdata-ab`) and records the
  `userdata-root.json` hashes. Run `43315159441` is the first attempt.
- The iOS 26 profile, `cupid_ios26_defconfig`, the 23F84 fixture, the one-off
  ios26 workflows/tools and the fallback image references were removed.

## Probe retry

The first probe image (`43316884744`, sha `9de44f55…`) had no
`unixnu-ufs-probe=1`: the edit matched `"kernel_args"` but board.toml uses the
bare TOML key. It booted straight to the root-device panic. `ffeffee` adds the
argument; build `43389189012` is the corrected diagnostic image.

## Probe result (2026-11-13)

The corrected probe image (`43389189012`, sha `2c9a20d3…`) reported:

```
gcc gdscr=f822f000 axi=221 ahb=1 tx0=1 rx0=1 unipro=221 ice=221 aux=1 aggre=1
hc cap=1587031f ver=300 hcs=10f hce=1 is=400 ie=0
   utrlba=ff12f000 utrlbau=0 dbr=0 rsr=1
```

The firmware left UFS **powered, clocked, enabled and running**. The SM8450
GCC offsets are correct; the driver can adopt the live controller and does not
need to program the QMP PHY/GCC resets first. Details:
`notes/UFS-PROBE-2026-11-13.md`.

The normal build no longer carries `unixnu-ufs-probe=1` (`0742b0c`).

## Architecture decision

The sheng source-storage runtime is tied to the sheng device repo's
`SourceStorage.cpp`/`SourceRootPolicies.cpp` and owner-signed iPad root
policies, so it cannot be dropped into cupid. Cupid should use a **standalone
SM8450 UFS driver**:

1. Adopt the firmware controller (the probe proves it is live), with the
   UFSHCI transport, PRDT, SMMU stream `0x60`, and the `RootCommands`/
   `TransferPoll`/`CompletionWait` helpers adapted from ShengUfs.
2. Read the userdata GPT + first block (the `native-ufs-probe=10` equivalent)
   and panic with the values; no policies or storage runtime.
3. Publish the SHNGROOT OS/SystemOS windows as standard `IOBlockStorageDevice`
   /`IOMedia` objects through the public IOStorageFamily, then let the
   original APFS kext attach.
