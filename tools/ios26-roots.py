#!/usr/bin/env python3
"""Print the iPhone 26.5.2 OS/SystemOS APFS volume UUIDs and raw image digests.

Runs on macOS: unixnu.ipsw decrypts the AEA archives with /usr/bin/aea and the
key fetched by `ipsw fw aea --key`; then hdiutil/diskutil read the volume UUIDs.
Nothing is written to the repository; the caller removes out/ipsw afterwards.

usage: ios26-roots.py <UniXNU checkout>
"""
import hashlib
import json
import pathlib
import plistlib
import subprocess
import sys
import types
import uuid

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


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def scan_apsb(path):
    """Read every APFS volume superblock (obj_phys magic APSB at +0x20)."""
    volumes, seen = [], set()
    with path.open('rb') as stream:
        block = stream.read(4096)
        index = 0
        while len(block) == 4096:
            if block[32:36] == b'APSB':
                value = str(uuid.UUID(bytes=block[240:256])).upper()
                if value not in seen:
                    seen.add(value)
                    name = block[704:960].split(b'\0', 1)[0].decode('utf-8', 'replace')
                    volumes.append({'block': index, 'uuid': value, 'name': name})
            block = stream.read(4096)
            index += 1
    return volumes


def attach_volumes(path):
    """Mount nothing; ask diskutil for the APFS volumes of this image's container."""
    attached = subprocess.run(
        ['hdiutil', 'attach', '-nomount', '-noverify', '-noautoopen', str(path)],
        capture_output=True, text=True)
    if attached.returncode:
        return {'error': attached.stderr.strip()[-400:]}
    devices = [line.split()[0] for line in attached.stdout.splitlines()
               if line.startswith('/dev/disk')]
    try:
        listing = subprocess.run(['diskutil', 'apfs', 'list', '-plist'], capture_output=True)
        if listing.returncode:
            return {'devices': devices, 'error': listing.stderr.decode('utf-8', 'replace')[-400:]}
        volumes = []

        def walk(node):
            if isinstance(node, dict):
                if node.get('APFSVolumeUUID'):
                    volumes.append({
                        'uuid': node['APFSVolumeUUID'],
                        'name': node.get('APFSVolumeName'),
                        'role': node.get('APFSVolumeRole'),
                        'device': node.get('DeviceIdentifier'),
                        'container': node.get('APFSContainerReference'),
                    })
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(plistlib.loads(listing.stdout))
        prefixes = tuple(device.rsplit('s', 1)[0] for device in devices if 's' in device) + tuple(devices)
        volumes = [v for v in volumes
                   if (v.get('device') or '').startswith(prefixes)
                   or (v.get('container') or '').startswith(prefixes)]
        return {'devices': devices, 'volumes': volumes}
    finally:
        for device in devices:
            subprocess.run(['hdiutil', 'detach', device], capture_output=True)


def main():
    source = ipsw.Ipsw(CTX, spec=CFG['url'])
    result = {}
    for component in ('OS', 'Cryptex1,SystemOS'):
        image = source.disk_image(component)
        entry = {'path': image.name, 'bytes': image.stat().st_size, 'sha256': sha256(image)}
        entry['apsb'] = scan_apsb(image)
        entry['diskutil'] = attach_volumes(image)
        result[component] = entry
        print(json.dumps({component: entry}, indent=2), flush=True)
    print('ROOTS_JSON: ' + json.dumps(result, separators=(',', ':')))


if __name__ == '__main__':
    main()
