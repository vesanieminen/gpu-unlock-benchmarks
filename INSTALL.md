# Automatic gpu-unlock on the RTX 3080 host

Status: **installed and configured; both boot images verified; reboot activation pending**.
The installation below completed on 2026-10-25 from upstream commit
`af28cbbfd3d922a659227ecfb7369adfd924cf03`. Both packages are version 1.0.0-1,
and DKMS reports the module installed for both kernels. All five upstream tests
passed, as did the pinned firmware checksum checks. This becomes a confirmed
working optimization only after reboot verification and matching unlocked
benchmarks are recorded. No reboot or unlock activation has been performed yet.

The [installation evidence](systems/rtx3080/installation/) contains package/source
metadata, the backup manifest and checks of both generated boot images. Every
operational command and output is linked from the [journal](systems/rtx3080/COMMANDS.md).

## Checked on this machine

- Omarchy 4.0.4, Limine with generated UKIs and mkinitcpio's udev hook.
- Running kernel 7.2.5-3-omarchy; matching linux-omarchy-headers installed.
- Secondary Arch kernel 7.2.3-arch1-3 and linux-headers also installed.
- DKMS 3.4.3; NVIDIA open DKMS driver 610.57.04.
- Secure Boot is off. Build tools git/python/zstd/gcc/make are present.
- GPU: RTX 3080 LHR, PCI ID 10de:2216, address 0000:07:00.0.
  The upstream module's supported-ID list includes 0x2216.

The automatic mechanism is an early-loaded kernel module inside the boot image.
It must run before nvidia binds the card. The DKMS package supplies the module,
the firmware package supplies its assets, and the kernel command line opts in.
Loading the module after normal desktop startup cannot unlock an already-bound
card. A desktop autostart or ordinary startup service would be too late.

## Commands to run, preserving the journal

Run from a terminal. Define this helper again after reboot:

```bash
cd ~/Projects/gpu-unlock-benchmarks
record() {
  python3 "$HOME/Projects/gpu-unlock-benchmarks/record.py" \
    --system rtx3080 --phase "$1" -- "${@:2}"
}
```

Build as the regular user, then authenticate with pkexec for package installation:

```bash
record install git clone https://github.com/Zagitta/gpu-unlock.git "$HOME/Projects/gpu-unlock"
record install bash -x -c 'cd "$HOME/Projects/gpu-unlock" && git rev-parse HEAD && make arch'
record install pkexec pacman -U --noconfirm "$HOME/Projects/gpu-unlock/packaging/arch/gpu-unlock-dkms-1.0.0-1-any.pkg.tar.zst" "$HOME/Projects/gpu-unlock/packaging/arch/gpu-unlock-firmware-1.0.0-1-x86_64.pkg.tar.zst"
record verification dkms status
record verification bash -x -c 'modinfo -k "$(uname -r)" gpu_unlock; cat /etc/mkinitcpio.conf.d/zz-gpu-unlock.conf'
```

Proceed only if the packages build/install successfully and DKMS reports the
module installed for the kernel that will boot. The package's mkinitcpio drop-in
places gpu_unlock before nvidia. On this udev-hook host, its optional-module `?`
suffix is handled by mkinitcpio; do not apply the separate systemd-hook workaround
unless the actual installed hook configuration requires it. Never run makepkg
or the whole upstream build as root.

For a future reproduction, pin the checkout to the exact commit above before
building; the live installation checked and recorded its HEAD before make arch.
Pre-install copies of both UKIs, /boot/limine.conf, /etc/default/limine and
/etc/mkinitcpio.conf were also saved under
`~/.local/state/gpu-unlock/backups/20261025T163126Z/`. The binaries are local
backups and are not uploaded to Git; their paths and hashes are in the manifest.

Preview and apply the target for this specific GPU, preserving a backup and
atomically replacing the configuration while keeping ownership and mode:

```bash
record boot-config-preview python3 configure_limine.py --targets 0000:07:00.0
record boot-config pkexec python3 "$HOME/Projects/gpu-unlock-benchmarks/configure_limine.py" --targets 0000:07:00.0 --apply
record boot-config env AUTH_METHOD=pkexec limine-mkinitcpio
```

The added line is exactly:

```bash
KERNEL_CMDLINE[default]+=" gpu_unlock.targets=0000:07:00.0"
```

limine-mkinitcpio regenerates this system's boot images and manages its own
privilege authentication; AUTH_METHOD=pkexec selects its graphical authentication
path without changing the saved authentication configuration. Check its output
for failures. Preserve the existing
encryption/root options. For the future dual-3090 host, discover its addresses
and bootloader independently; do not copy 0000:07:00.0 blindly.

The completed image check is reproducible with:

```bash
record verification python3 verify_boot_images.py \
  --baseline "$HOME/.local/state/gpu-unlock/backups/20261025T163126Z" \
  --targets 0000:07:00.0 \
  --output systems/rtx3080/installation/boot-images.json
```

Both images passed: target present once, other kernel options preserved exactly
as tokens, gpu_unlock ordered before nvidia, the kernel-specific module present,
and all five firmware files present. The udev hook's local write_config code
strips the optional-module question mark before writing the runtime module list.
The initial verifier used objcopy's /dev/null output and returned nonzero; it was
corrected to use a disposable temporary output file. This did not modify any UKI;
both the failure and successful verification are recorded.

The rebuild emitted warnings about xhci_pci_renesas/qat_6xxx firmware and an unset
console font, while completing both UKIs successfully. These are not failures
to include the gpu-unlock firmware; the explicit content checks passed.
An NVIDIA status check inside the sandbox failed as during earlier setup; the
recorded check outside the sandbox succeeded: driver 610.57.04, power limit 320 W.

When ready to restart, record a user-initiated reboot (not executed yet):

```bash
record reboot pkexec systemctl reboot
```

A shutdown can interrupt the recorder before it saves the exit status; null
means completion was not observed. That alone is not a failed reboot.

## Verification after reboot

Define the helper again, then:

```bash
record verification cat /proc/cmdline
record verification bash -x -c 'journalctl -k -b --no-pager | rg "gpu_unlock|NVRM: Xid"'
record verification lspci -nnk -s 0000:07:00.0
record verification nvidia-smi
bash run.sh torch unlocked
bash run.sh vllm unlocked
```

Require the target option in the running kernel command line, a kernel message
reporting `gpu_unlock: unlocked` for 0000:07:00.0, and NVIDIA still driving the
card. Compare the new results with the stored stock baselines, keeping the
same model/image/scripts, runtime settings and power/clock configuration.
The benchmarks also establish whether throughput actually improved. A configured
boot parameter alone is not proof that the unlock ran.

After verification, update this document with the exact upstream commit,
package versions, successful command records, observed boot messages and measured
gains. Push the installation journal and unlocked results alongside the baseline.
Record any deviations from the prepared procedure rather than rewriting history.

## Rollback

Remove the added KERNEL_CMDLINE line from /etc/default/limine, run
limine-mkinitcpio, and reboot, recording those operations. That removes the
opt-in, so the module does no unlocking on subsequent boots. The original Limine
configuration is backed up at /etc/default/limine.before-gpu-unlock; restore it
only if it does not discard other later configuration changes. Optionally remove
gpu-unlock-dkms and gpu-unlock-firmware with the package manager, and regenerate
the images. Keep the original stock benchmark artifacts.

No power limits or clock settings are part of this procedure.

Sources: [upstream installation and boot flow](https://github.com/Zagitta/gpu-unlock),
[Arch packaging](https://github.com/Zagitta/gpu-unlock/blob/main/packaging/arch/PKGBUILD),
[supported PCI IDs](https://github.com/Zagitta/gpu-unlock/blob/main/kernel/gpu_unlock/main.c).
