# Dual RTX 3090 system — pending

This system has not been inspected or benchmarked yet. Do not infer CPU, RAM,
GPU interconnect, driver, clocks or power configuration from the 3080 system.

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
