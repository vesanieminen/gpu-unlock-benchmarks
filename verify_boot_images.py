#!/usr/bin/env python3
"""Verify prepared UKIs without loading the unlock module or rebooting."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

def commandline(image):
    with tempfile.TemporaryDirectory(prefix='gpu-unlock-verify-') as directory:
        output = Path(directory) / 'cmdline'
        # An explicit output prevents objcopy from modifying the input UKI.
        subprocess.run(['objcopy', '--dump-section', f'.cmdline={output}',
                        str(image), str(Path(directory) / 'copy.efi')], check=True)
        return output.read_bytes().split(b'\0', 1)[0].decode().strip()

def sha256(path):
    with path.open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--targets', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    target = 'gpu_unlock.targets=' + args.targets
    images = sorted(Path('/boot/EFI/Linux').glob('*.efi'))
    if not images:
        p.error('No UKIs found.')
    expected_firmware = ['booter_load_ga102.bin', 'gsp_boot_desc_ga102.bin',
                         'gsp_boot_ga102.bin', 'gsp_ga10x.bin', 'v67-ga102-610.43.03.bin']
    results = []
    for image in images:
        before = commandline(args.baseline / image.name)
        after = commandline(image)
        config = subprocess.check_output(['lsinitcpio', '-c', str(image)], text=True)
        # Evaluate the trusted local build configuration saved by mkinitcpio,
        # as the regular user, to include its array-editing drop-ins.
        modules = subprocess.check_output(
            ['bash', '-c', 'source /dev/stdin; printf "%s\\n" "${MODULES[@]}"'],
            input=config, text=True).splitlines()
        modules = [module.removesuffix('?') for module in modules]
        contents = subprocess.check_output(['lsinitcpio', '-l', str(image)], text=True).splitlines()
        firmware = [line for line in contents if '/firmware/gpu-unlock/' in line]
        module_files = [line for line in contents if 'gpu_unlock.ko' in line]
        checks = {
            'target_present_once': after.split().count(target) == 1,
            'other_kernel_options_preserved': [x for x in after.split() if x != target] == before.split(),
            'unlock_loads_before_nvidia': 'gpu_unlock' in modules and 'nvidia' in modules and modules.index('gpu_unlock') < modules.index('nvidia'),
            'module_in_image': bool(module_files),
            'all_firmware_in_image': all(any(line.endswith('/' + name) or line.endswith('/' + name + '.zst') for line in firmware) for name in expected_firmware),
        }
        results.append({'image': str(image), 'sha256': sha256(image),
                        'baseline_sha256': sha256(args.baseline / image.name),
                        'baseline_cmdline': before, 'prepared_cmdline': after,
                        'module_order': modules, 'module_files': module_files,
                        'firmware_files': firmware, 'checks': checks})
    report = {'status': 'prepared; reboot verification pending', 'images': results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    if not all(all(row['checks'].values()) for row in results):
        raise SystemExit(1)

if __name__ == '__main__':
    main()
