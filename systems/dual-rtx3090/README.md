# Dual RTX 3090 system — stock/unlocked comparison complete

Initial live inspection on 2026-10-25 identified hostname `ai-box`, an AMD
Ryzen 7 5800X (8 cores / 16 threads), 125 GiB reported RAM, and two RTX 3090
24 GB GPUs. The kernel is 7.2.5-3-omarchy and NVIDIA driver is 610.57.04.
Both cards report a 350 W power limit; no limits or clocks were changed.
The GPU topology reports PHB connectivity, not NVLink. Initial stock inspection
found no gpu_unlock boot entry, loaded module or installed packages.
After installation and reboot, both cards logged successful unlocking.

At inspection, `strata-dsv41` used approximately
23 GiB on each card under `llama-swap.service`. The user authorized stopping
that workload for benchmarking. Initial recorded `pkexec systemctl stop`
attempts failed because the agent session had no authentication agent or
controlling terminal; interactive attempts also logged `No session for cookie`.
After the user started Wayland, dispatching the recorded stop command through
Hyprland allowed desktop authentication. The service was confirmed inactive
and the inference workload released both GPUs.

Direct Docker socket access is denied for the agent user. An ignored local
wrapper in `cache/docker-pkexec-bin/` runs `/usr/bin/docker` through pkexec
from the desktop session. Containers retain UID/GID 1000 and the existing
benchmark settings; no Docker group membership or socket permissions changed.
The pinned image pull and pinned model download succeeded. Both single-GPU
PyTorch baselines and the TP=2 vLLM baseline completed successfully after desktop
authentication. The matching unlocked runs also passed. See [results](RESULTS.md).
Local `model/` and `cache/` were initially absent.
The desktop remains active on GPU 0 and must be kept consistent for comparison.
After all benchmarks and comparisons completed, `llama-swap.service` was
restored and verified active. No startup policy was changed.

The user authorized gpu-unlock installation after the stock benchmarks finish.
Read-only preparation found Secure Boot disabled, matching linux-omarchy headers,
DKMS and build tools installed, and no gpu-unlock packages installed. This host
has only the Omarchy kernel installed. Its mkinitcpio drop-ins override the main
configuration to use udev and early NVIDIA loading. The intended targets are
`0000:0b:00.0,0000:0c:00.0`; the old 3080 target must not be reused. Back up this
host's boot images and configurations before installation, validate rebuilt
images before reboot, and verify both GPUs after activation. Installation and
reboot are described in [the installation record](INSTALL.md). Installation is
complete, the boot image passed all five validation checks, and the authorized
reboot activated both cards. All six stock/unlocked runs passed; output hashes
and runtime metadata match. The model, image, scripts and power ceilings match.

While waiting for benchmark authentication, source commit
`af28cbbfd3d922a659227ecfb7369adfd924cf03` was fetched into ignored
`cache/gpu-unlock-src/`. The first package build failed because the filtered Git
clone could not serve objects to makepkg's local clone. Refetching the complete
repository fixed that issue. The subsequent regular-user `make arch` succeeded:
both NVIDIA input SHA-256 checks passed, all five upstream tests passed, and
DKMS/firmware packages version 1.0.0-1 were built. The package build checkout's
commit was verified. A Limine preview validated both local PCI targets; it did
not apply changes. After stock baselines passed, the packages were installed,
both targets were applied, and the rebuilt boot image passed validation.

See [the command journal](COMMANDS.md) for live output, including failures.
The first inspection was initially labeled rtx3080; its metadata and transcript
were moved here with an explicit correction note preserving the original argv.
Do not infer this machine's state from the separate 3080 system.

Use `BENCH_SYSTEM=dual-rtx3090` for every launcher invocation. Use `BENCH_TP=2`
for the vLLM test across both cards. Keep that setting identical before/after.
The PyTorch script measures one GPU at a time. Run once with `BENCH_GPU=0` and
once with `BENCH_GPU=1`, labeling each run (e.g. baseline-gpu0). Do not treat
one GPU's TFLOPS as the pair's throughput. Test simultaneous loads separately
if shared power or cooling behavior matters.

Capture `nvidia-smi -q`, `nvidia-smi topo -m`, CPU/RAM, kernel, bootloader and
driver details before optimization. Record all install, configuration, reboot
and verification commands with record.py. Record commands on this system,
not on the 3080 host. Reuse the pinned image and model for comparisons.
