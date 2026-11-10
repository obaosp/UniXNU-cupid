#!/usr/bin/env python3
"""Dump the undefined-symbol tables of the iPhone 26 kexts.

Runs on macOS: unixnu.ipsw decrypts the OS and Cryptex1,SystemOS images with
/usr/bin/aea, hdiutil mounts them, and llvm-nm/llvm-objdump print the imports
of the relevant kext binaries. The output is a text log; Apple images are
removed afterwards.

usage: ios26-kext-imports.py <UniXNU checkout>
"""
import json
import pathlib
import subprocess
import sys
import types

ROOT = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT / 'scripts'))
from unixnu import ipsw  # noqa: E402

CFG = {
    'url': 'https://updates.cdn-apple.com/2026SpringFCS/fullrestores/140-26194/0358D1F3-1C15-44F7-A711-93D2987CA188/iPhone17,2_26.5.2_23F84_Restore.ipsw',
    'product': 'iPhone17,2', 'version': '26.5.2', 'build': '23F84',
    'device_class': 'd94ap', 'chip_id': 33088, 'board_id': 14,
    'fetch': ['KernelCache', 'DeviceTree', 'StaticTrustCache', 'Cryptex1,SystemTrustCache'],
}
CTX = types.SimpleNamespace(
    board={'ipsw': CFG}, out_root=ROOT / 'out', tree=ROOT,
    option=lambda *a, **k: None, option_text=lambda *a, **k: None,
)
WANT = (
    'AppleMobileFileIntegrity', 'sandbox', 'AppleImage4', 'apfs',
    'AppleARMPlatform', 'AppleT8140CLPC', 'AppleM2ScalerCSCDriver',
    'ApplePMGR', 'IODARTFamily', 'IOHIDFamily', 'IOGPUFamily',
    'IOSurface', 'ARMWatchdogTimer', 'corecrypto', 'IOStorageFamily',
    'IOCryptoAcceleratorFamily', 'CoreAnalyticsFamily', 'IOAVFamily',
)


def run(command, **kwargs):
    return subprocess.run(command, capture_output=True, text=True, **kwargs)


def dump_kext(kext):
    paths = list(kext.glob('Contents/MacOS/*'))
    print(f'==== KEXT {kext.name} {kext}')
    for binary in paths:
        if not binary.is_file():
            continue
        print(f'== BINARY {binary.name}')
        nm = run(['llvm-nm', '-u', str(binary)])
        print('-- nm -u')
        print(nm.stdout[:200000])
        if nm.stderr.strip():
            print('-- nm stderr', nm.stderr.strip()[:2000])
        obj = run(['llvm-objdump', '--macho', '--bind', str(binary)])
        print('-- objdump bind')
        print(obj.stdout[:300000])
        if obj.stderr.strip():
            print('-- objdump stderr', obj.stderr.strip()[:2000])


def main():
    source = ipsw.Ipsw(CTX, spec=CFG['url'])
    for component in ('OS', 'Cryptex1,SystemOS'):
        image = source.disk_image(component)
        print(f'==== IMAGE {component} {image.name} {image.stat().st_size}', flush=True)
        mount = pathlib.Path('/tmp/ios26-mnt-' + component.replace(',', '_'))
        mount.mkdir(parents=True, exist_ok=True)
        attached = run(['hdiutil', 'attach', '-noverify', '-noautoopen',
                        '-mountroot', str(mount), str(image)])
        print(attached.stdout, attached.stderr, flush=True)
        devices = [line.split()[0] for line in attached.stdout.splitlines()
                   if line.startswith('/dev/disk')]
        try:
            kexts = []
            for base in (mount, pathlib.Path('/Volumes')):
                for kext in base.rglob('*.kext'):
                    if any(name in kext.name for name in WANT):
                        kexts.append(kext)
            kexts = sorted(set(kexts))
            print(f'kexts {len(kexts)}')
            for kext in kexts:
                dump_kext(kext)
        finally:
            for device in devices:
                run(['hdiutil', 'detach', device])


if __name__ == '__main__':
    main()
