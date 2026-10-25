#!/usr/bin/env python3
"""Preview or atomically add gpu-unlock targets to this host's Limine config."""
import argparse
import difflib
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--targets', required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    addresses = args.targets.split(',')
    for address in addresses:
        if not re.fullmatch(r'[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]', address):
            parser.error('Use explicit full PCI addresses, separated by commas.')
        device = Path('/sys/bus/pci/devices') / address
        if (device / 'vendor').read_text().strip() != '0x10de' or not (device / 'class').read_text().startswith('0x03'):
            parser.error(f'{address} is not an NVIDIA display device on this host.')
    config = Path('/etc/default/limine')
    if config.is_symlink():
        parser.error('Refusing to replace a symlinked configuration.')
    before = config.read_text()
    existing = re.findall(r'gpu_unlock\.targets=([^\s"\x27]+)', before)
    if existing:
        if existing == [args.targets]:
            print('The requested targets are already configured.')
            return
        parser.error('An existing target option differs; inspect it before changing it.')
    after = before.rstrip('\n') + f'\n\nKERNEL_CMDLINE[default]+=" gpu_unlock.targets={args.targets}"\n'
    print(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                     fromfile=str(config), tofile=str(config))), end='')
    if not args.apply:
        print('Preview only; configuration unchanged.')
        return
    if os.geteuid() != 0:
        parser.error('--apply requires root; invoke through pkexec.')
    backup = config.with_name('limine.before-gpu-unlock')
    if not backup.exists():
        shutil.copy2(config, backup)
    details = config.stat()
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=config.parent, prefix='.limine.gpu-unlock.', delete=False) as file:
            temporary = Path(file.name)
            file.write(after)
            file.flush()
            os.fsync(file.fileno())
            os.fchmod(file.fileno(), stat.S_IMODE(details.st_mode))
            os.fchown(file.fileno(), details.st_uid, details.st_gid)
        os.replace(temporary, config)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(f'Applied. Original configuration backup: {backup}')

if __name__ == '__main__':
    main()
