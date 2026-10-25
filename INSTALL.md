# Automatic gpu-unlock on the RTX 3080 host

Status: **procedure prepared; packages not installed; boot activation not verified**.
The recorded prerequisite inspection is complete. This document becomes a
confirmed working recipe only after successful installation, reboot verification
and matching unlocked benchmarks are recorded. Do not label planned steps as run.

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
record install bash -x -c 'pkexec pacman -U "$HOME"/Projects/gpu-unlock/packaging/arch/gpu-unlock-dkms-*.pkg.tar.zst "$HOME"/Projects/gpu-unlock/packaging/arch/gpu-unlock-firmware-*.pkg.tar.zst'
record verification dkms status
record verification bash -x -c 'modinfo -k "$(uname -r)" gpu_unlock; cat /etc/mkinitcpio.conf.d/zz-gpu-unlock.conf'
```

Proceed only if the packages build/install successfully and DKMS reports the
module installed for the kernel that will boot. The package's mkinitcpio drop-in
places gpu_unlock before nvidia. On this udev-hook host, its optional-module `?`
suffix is handled by mkinitcpio; do not apply the separate systemd-hook workaround
unless the actual installed hook configuration requires it. Never run makepkg
or the whole upstream build as root.

Back up Limine's configuration, then append an opt-in for this specific GPU:

```bash
record boot-config pkexec cp -an /etc/default/limine /etc/default/limine.before-gpu-unlock
record boot-config pkexec python3 -c 'from pathlib import Path; p=Path("/etc/default/limine"); s=p.read_text(); assert "gpu_unlock.targets=" not in s, "Existing gpu-unlock option: inspect it first"; p.write_text(s + "\nKERNEL_CMDLINE[default]+=\" gpu_unlock.targets=0000:07:00.0\"\n")'
record boot-config limine-mkinitcpio
```

The added line is exactly:

```bash
KERNEL_CMDLINE[default]+=" gpu_unlock.targets=0000:07:00.0"
```

limine-mkinitcpio regenerates this system's boot images and manages its own
privilege authentication. Check its output for failures. Preserve the existing
encryption/root options. For the future dual-3090 host, discover its addresses
and bootloader independently; do not copy 0000:07:00.0 blindly.

When ready to restart, record a user-initiated reboot:

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
