# RTX 3080: confirmed stock/unlocked comparison

On 2026-10-25, the rebooted Omarchy host logged
`pci 0000:07:00.0: gpu_unlock: unlocked`. NVIDIA remained the active driver.
The kernel stayed 7.2.5-3-omarchy, NVIDIA stayed 610.57.04, and the board power
ceiling stayed 320 W. No NVRM Xid messages were found in this boot through the
end of the benchmarks. This is a short benchmark validation, not a sustained
stability or suspend/resume test.

## PyTorch GEMM

| Precision | Stock TFLOPS | Unlocked TFLOPS | Change |
| --- | ---: | ---: | ---: |
| BF16 | 62.54 | 107.40 | +71.75% |
| FP16 | 62.32 | 104.85 | +68.25% |
| TF32 | 31.00 | 51.93 | +67.54% |

Medians of five samples of 50 calls; 8192-cubed GEMM with FP32 accumulation.
All seeded output hashes match. The benchmark source, image and kernel match.
The launcher OMP environment changed from six to one after the recorded stock
GEMM run, but the PyTorch script explicitly sets its CPU threads to six in both
arms. No GPU math settings changed.

One-second telemetry during >=90% GPU utilization showed median board power
318.78 W stock versus 319.39 W unlocked, and median SM clocks 1905 versus
1635 MHz. Whole-run peak temperatures were 60 versus 55 C. These are short,
sequential runs under different initial thermal conditions, not evidence of
improved sustained cooling. The power ceiling was 320 W in every sample.

[Raw comparison](comparison/torch.json), [telemetry summary](comparison/torch-telemetry.json).
Stock: results/baseline-recorded-torch-20261025T160747.100955724Z/.
Unlocked: results/unlocked-torch-20261025T164410.686576570Z/.

## vLLM: Qwen2.5-3B-Instruct native BF16

| Input / output tokens | Metric | Stock tok/s | Unlocked tok/s | Change |
| --- | --- | ---: | ---: | ---: |
| 512 / 1 | Prefill | 8,371.57 | 11,906.04 | +42.22% |
| 2,048 / 1 | Prefill | 9,428.96 | 14,956.44 | +58.62% |
| 4,096 / 1 | Prefill | 8,942.63 | 14,172.86 | +58.49% |
| 512 / 128 | Decode | 89.10 | 89.91 | +0.91% |

Two warm-ups and five measured requests per case, deterministic synthetic
prompts, no prefix caching, no CPU offload, no quantization, one active request.
The model revision, image, kernel, launcher, benchmark source and configuration
match exactly between the final stock and unlocked vLLM runs. All generated
token hashes match across the paired samples. The generation gain is small
enough to treat as approximately unchanged rather than a proven decode benefit.

The stock run compiled kernels and the unlocked run reused those artifacts;
initialization is excluded from timings and both arms warm up each case.
vLLM's automatic memory profiling allocated different KV cache capacities
(about 1.51 GiB stock and 2.50 GiB unlocked) with the same 90% memory setting.
Desktop memory and startup profiling differed. Both capacities exceed the
tested context requirements; neither arm used prefix caching. The results are
one stock/unlocked pair on this desktop, not an isolated repeated-boot study.

[Raw comparison](comparison/vllm.json).
Stock: results/baseline-final-vllm-20261025T162003.098487616Z/.
Unlocked: results/unlocked-vllm-20261025T164435.283078631Z/.

## Exact installation and reboot correction

The [installation procedure](../../INSTALL.md) worked: build the pinned upstream
commit af28cbbfd3d922a659227ecfb7369adfd924cf03, install the DKMS/firmware
packages, add the explicit Limine PCI target, and rebuild UKIs. The unlock
activated automatically before NVIDIA on the next boot.

The first benchmark after reboot could not start because the saved Docker CDI
spec referred to /dev/dri/card1, while the display GPU was now /dev/dri/card0.
This is a stale container device mapping, not failure of the unlock. Regenerating
the mapping fixed it:

```bash
python3 record.py --system rtx3080 --phase docker-repair -- \
  pkexec nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml
```

No automatic CDI refresh service was present on this host. If device numbering
changes again, refresh the mapping before Docker benchmarks. No new refresh
service was installed. The failed attempt and successful repair remain in
[the command journal](COMMANDS.md), along with the boot verification and both
successful benchmarks. This system's work is complete; the dual-3090 host is
still pending its own inspection and baseline.
