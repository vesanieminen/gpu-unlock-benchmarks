# Dual RTX 3090 installation

Status on 2026-10-25: installed, boot image validated, and activation confirmed
on both RTX 3090s after the authorized reboot. Both PyTorch runs and the TP=2
vLLM run passed, with matching paired output hashes. See [the full results](RESULTS.md).

Source commit: `af28cbbfd3d922a659227ecfb7369adfd924cf03`. Both local packages
are 1.0.0-1. NVIDIA input checksum checks and all five upstream tests passed.
DKMS reports gpu-unlock/1.0.0 installed for 7.2.5-3-omarchy. NVIDIA remains
610.57.04; neither clocks nor the two 350 W power limits were changed.

Successful stock baselines were checked before installation. Their image/model
locks and script hashes match the current files. Package SHA-256 values were
checked against the built artifacts before installing.

## Backups and boot image

Original UKI, Limine configuration, mkinitcpio configuration and drop-ins are
under `/home/vesanieminen/.local/state/gpu-unlock/backups/20261025T174628Z/`.
Keep these local binaries out of Git. [The manifest](installation/backup-manifest.json)
contains paths and hashes. `/etc/default/limine.before-gpu-unlock` is also kept.

The added option is exactly:

```text
gpu_unlock.targets=0000:0b:00.0,0000:0c:00.0
```

The package drop-in places gpu_unlock before nvidia. This host's effective
initramfs hooks use udev. Its single UKI,
`/boot/EFI/Linux/omarchy_linux-omarchy.efi`, was regenerated and passed all five
[content checks](installation/boot-images.json): one target option, all other
kernel options preserved, correct early module ordering, module present and all
five firmware assets present. Rebuild warnings concerned xhci_pci_renesas and
qat_6xxx firmware; required gpu-unlock firmware checks passed.

## After reboot

The 19:48:51 local-time boot logged `gpu_unlock: unlocked` for both
`0000:0b:00.0` and `0000:0c:00.0`. NVIDIA remained bound to both, the kernel and
driver matched stock, and both power ceilings remained 350 W. No NVRM Xid
messages were found during initial verification. See [activation evidence](installation/activation.json).
The unsigned out-of-tree module produced kernel-taint messages; it then
completed unlocking both cards. Secure Boot remains disabled.
After benchmark completion, `llama-swap.service` was restored and confirmed
active. Its startup configuration was not changed.

Record verification with `record.py --system dual-rtx3090 --phase verification`:
inspect `/proc/cmdline`, `journalctl -k -b`, both PCI bindings, `nvidia-smi` and
power ceilings. Require `gpu_unlock: unlocked` for **both** PCI addresses and
NVIDIA still driving both cards. Inspect NVRM Xid errors.

`llama-swap.service` may start again on boot. Its stop for benchmarking is
authorized; record stopping it and confirm that the inference workload releases
both cards before measuring. Preserve the active Wayland desktop on GPU 0.

Use the same pinned image, model, scripts and environment as the stock runs:

```bash
BENCH_SYSTEM=dual-rtx3090 BENCH_GPU=0 bash run.sh torch unlocked-gpu0
BENCH_SYSTEM=dual-rtx3090 BENCH_GPU=1 bash run.sh torch unlocked-gpu1
BENCH_SYSTEM=dual-rtx3090 BENCH_TP=2 bash run.sh vllm unlocked
```

Direct Docker socket access is denied; the ignored local Docker wrapper can
request pkexec from the desktop session. Each launcher records itself. If Docker
fails on a stale CDI device path, retain that failure and record regenerating
`/etc/cdi/nvidia.yaml` with `nvidia-ctk cdi generate` through pkexec before retry.
Do not treat an incomplete run or missing exit status as a successful result.

## Rollback

Remove only the added gpu_unlock.targets line from `/etc/default/limine`,
regenerate the UKI with limine-mkinitcpio and reboot, recording each action.
Alternatively restore the saved original Limine file only after checking that
it does not discard later edits. Optionally remove the two gpu-unlock packages
and regenerate the UKI. Keep the stock measurements and backup files.

All operational output, including build/authentication failures, is retained in
[the command journal](COMMANDS.md). Installation completed in command record
`20261025T174639.522769Z-e229c0.json`; the subsequent review is
`20261025T174713.602195Z-f050a5.json`.
