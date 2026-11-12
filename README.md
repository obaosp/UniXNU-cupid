> [!WARNING]
> **Work in progress — this port does not boot yet.**
>
> iOS 27 on the Xiaomi 12 (`cupid`, SM8450) is under active development. The iOS 26.5.2 image is kept as a fallback. It
> currently stops in a kernel panic during early kext start. Build failures,
> boot loops and kernel panics are expected while the port is unfinished.
>
> **Please do not open issues about build errors, boot loops or kernel panics
> until this notice is removed.** The issue tracker is closed to those reports;
> progress is tracked in `STATE.md`, `NEXT.md` and the build notes.

# UniXNU cupid — iOS 27 (iOS 26 fallback) on the Xiaomi 12

Bring-up of **iOS 27.0.1 (24A446, arm64e)** on the **Xiaomi 12** (`cupid`,
Qualcomm **SM8450**), presented to iOS as an **iPhone 16 Pro Max**
(`iPhone17,2`, `D94AP`).

This is a phone port, so it uses an **iPhone-flavoured** OS profile. It does
**not** boot the iPadOS 27 profile that ships in UniXNU main: different IPSW,
original kexts and product identity. The iOS 26.5.2 (23F84) profile remains as
a fallback.

## Why iOS 26, not iOS 27

> **Update (2026-11-12): iOS 27 is the current target.** The sheng port boots
> 24A446 with XnuPrelink's upstream 156-binding `fileset-24A446-symbols.json`.
> Retargeted to the iPhone17,2 24A446 kernelcache, that fixture leaves **55
> stubs / 17 missing** versus 137 stubs for the old 30-shim attempt. The iOS
> 27 profile is restored and selected; the iOS 26.5.2 image remains staged as
> fallback.

iOS 27.0.1 (24A446) reports `xnu-13432.2.10~2`, while the newest public XNU
source is `12377.121.6`. That mismatch forced a large reviewed-symbol fixture
(30 shims) and repeated early-kext panics. iOS 26.5.2 (23F84) reports
`xnu-12377.122.8~1`, the same major/minor as the public source, so prelink
pairs the real kernel natively: the exact source reference plus eight reviewed
bindings leaves 72 stubbed targets in the local exact-pair run, and the
remaining work is bring-up rather than chasing 13432-only functions.

## Hardware

| Block | cupid |
| --- | --- |
| SoC | SM8450 (Snapdragon 8 Gen 1), 8 cores: 4x A510, 3x A710, 1x X2 |
| RAM | 8 / 12 GiB LPDDR5 |
| Storage | UFS 3.1; UFS HC `0x1d84000`, QMP PHY `0x1d87000` |
| Display | 1080x2400, DSI command mode + DSC, 60/90/120 Hz, cont-splash `0xb8000000` |
| Touch | STMicroelectronics FTS over QUPv3 SE4 SPI, IRQ GPIO 21, reset GPIO 20 |
| GPU | Adreno 730 `0x3d00000`, GMU 730.1 `0x3d6a000`, SMMU `0x3da0000` |
| PMIC | PM8550 / PMK8550 |
| Identity | iPhone17,2 / D94AP, `qcom,msm-id = <457>` |

Sources: mainline Linux `sm8450.dtsi` at
`f1586048fb1dabb91c82fbe11557e505587973d3`; LineageOS
`android_kernel_xiaomi_sm8450-devicetrees` (`cupid-sm8450.dtsi`,
`waipio-sde-display.dtsi`, `dsi-panel-l3-42-02-0a-dsc-cmd.dtsi`).

## Structure

| Path | Contents |
| --- | --- |
| `board.toml` | Format 2 board: SM8450 source, iOS 26 profile, stage-0 components |
| `profiles/os/ios-27.0.1-24A446/` | The iPhone17,2 iOS 27 profile (current target) |
| `profiles/os/ios-26.5.2-23F84/` | The iPhone17,2 iOS 26 fallback profile |
| `configs/cupid_ios27_defconfig` | Stage-0 iOS 27 kernel configuration |
| `configs/cupid_ios26_defconfig` | Stage-0 iOS 26 fallback configuration |
| `dts/cupid.dts` | Memory, splash, CPU clusters; peripherals as they are enabled |
| `feeds.toml` | Pinned [`UniXNU-sm8450-common`](https://github.com/obaosp/UniXNU-sm8450-common) source |
| `porting.toml` | Per-area inputs, findings, limits and next action |
| `scripts/install-os-profile.sh` | Copies the iOS 26 profile into a UniXNU checkout |
| `scripts/package.sh` | Standard UniXNU packaging script (do not edit) |

## Why a shipped profile

UniXNU resolves `profiles/os/<name>` from its own checkout and main has only
`ipados-17.7.11`, `ipados-26.5.2` and `ipados-27.0.1`. The iPhone 27 profile here is built from the iPhone17,2 27.0.1 kernelcache and
XnuPrelink's retargeted 24A446 fixture; the iOS 26 profile is built from the
iPhone17,2 26.5.2 kernelcache (302 fileset entries, `xnu-12377.122.8~1`) and the
matching `xnu-12377.121.6` source: iPhone17,2 IPSW
pins, the AMFI early-init wrapper `0xfffffff008edda30`, the iPhone prelink roots
(no `IOHIDEventDriver` bundle), and the OS/SystemOS volume UUIDs and image
digests from the macOS AEA pass. A RELEASE-LTO build of the same source is the
prelink reference, and `patches/xnuprelink/fileset-cupid-23F84-symbols.json`
binds the eight functions the reference still cannot shape-match.
`scripts/install-os-profile.sh` installs the profile before `defconfig`.

## Build (host)

```sh
git clone https://github.com/UniXNU/UniXNU ../UniXNU
scripts/install-os-profile.sh ../UniXNU
cd ../UniXNU
./unixnu defconfig cupid_ios27_defconfig -D ../UniXNU-cupid
./unixnu fetch -D ../UniXNU-cupid
./unixnu status --json -D ../UniXNU-cupid
./unixnu build kernel -D ../UniXNU-cupid      # Xcode + iphoneos SDK
```

Full images need `uefi-cupid` (not published yet), the platform seed
`UNIXNU_UNIQUE_CHIP_ID` and a Data seed:

```sh
scripts/package.sh --os ios-27.0.1-24A446 --uefi ../uefi-cupid
```

## CI

`.github/workflows/macos.yml` runs resolve + `build kernel` + prelink on a
`macos-26` runner and uploads text logs. It needs no firmware and no secrets.
The prelink builds the fileset reference, applies the reviewed fixture and
publishes the stub/missing counts; `logs/*.log` and `kernel/*.json` are uploaded
even when the kernel step fails. `.github/workflows/package.yml` is the full
image build and still needs the platform seed and Data seed.

## Status

| Area | State |
| --- | --- |
| Configuration, CPU/interrupts | `implemented` (host) |
| Kernel build + prelink | CI job; iOS 27 prelink with the retargeted 24A446 fixture (local 55 stubs / 17 missing); iOS 26 image staged as fallback |
| Firmware, storage, display, input, GPU, network, audio, power | `planned` |

Device-side work is blocked on the phone: the build host has no `adb`,
`fastboot` or USB bus. The first device gates are the arm64e PAC requirement
checks from <https://unixnu.com/porting/arm64e> (PAuth keys writable at EL1, PAC
instructions not trapped, native 4 KiB stage 1).

## Documentation

- [Porting](https://unixnu.com/porting/) · [arm64e profiles](https://unixnu.com/porting/arm64e)
- [Device repository](https://unixnu.com/porting/device-repository) · [Records](https://unixnu.com/porting/records)
- [Building](https://unixnu.com/building) · [Bring-up](https://unixnu.com/porting/bring-up)
- [UFS](https://unixnu.com/porting/ufs) · [Display](https://unixnu.com/porting/display) · [Input](https://unixnu.com/porting/input)

Released under the BSD-2-Clause-Patent License.
