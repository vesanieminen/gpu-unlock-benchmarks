# Dual RTX 3090: confirmed stock/unlocked comparison

All three stock benchmarks and all three unlocked benchmarks completed
successfully on 2026-10-25. Both cards logged `gpu_unlock: unlocked` after
reboot. Each run retains source snapshots, pinned image/model locks, raw timing
samples, exit status and one-second telemetry. All paired output hashes match.

## PyTorch GEMM

| GPU | Precision | Stock TFLOPS | Unlocked TFLOPS | Change |
| --- | --- | ---: | ---: | ---: |
| GPU 0, 0000:0b:00.0 | BF16 | 71.77 | 115.55 | +61.01% |
| GPU 0 | FP16 | 70.29 | 111.96 | +59.27% |
| GPU 0 | TF32 | 38.44 | 62.85 | +63.51% |
| GPU 1, 0000:0c:00.0 | BF16 | 72.51 | 117.40 | +61.91% |
| GPU 1 | FP16 | 71.02 | 114.85 | +61.72% |
| GPU 1 | TF32 | 38.26 | 63.67 | +66.43% |

These are separate single-GPU measurements, not combined throughput. Each
reports the median of five samples of 50 calls at 8192×8192, with 20 warm-ups
and FP32 accumulation. All finite checks passed. The seeded output hashes match
between cards for each precision.

- [GPU 0 raw result](results/baseline-gpu0-torch-20261025T170547.636586110Z/result.json)
- [GPU 1 raw result](results/baseline-gpu1-torch-20261025T174345.952612565Z/result.json)
- [GPU 0 unlocked result](results/unlocked-gpu0-torch-20261025T175031.232765274Z/result.json)
- [GPU 1 unlocked result](results/unlocked-gpu1-torch-20261025T175059.608988719Z/result.json)
- [GPU 0 comparison](comparison/torch-gpu0.json) and [GPU 1 comparison](comparison/torch-gpu1.json)

The GPU 0 launcher began at 17:05 UTC and waited for Docker authentication;
the GPU 1 launcher began at 17:43 UTC. CUDA-event timing excludes the
authentication wait. Telemetry includes that wait, so whole-run aggregates
must distinguish idle authentication time from GPU computation.

## vLLM, tensor parallel size 2

Qwen2.5-3B-Instruct native BF16, pinned revision, no quantization or CPU offload.
Both cards participate in this run. The context limit is 8192, with one active
request, prefix caching disabled and OMP_NUM_THREADS=1.

| Input / output tokens | Metric | Stock tokens/s | Unlocked tokens/s | Change |
| --- | --- | ---: | ---: | ---: |
| 512 / 1 | Prefill | 8,738.60 | 11,610.22 | +32.86% |
| 2048 / 1 | Prefill | 10,780.42 | 13,869.97 | +28.66% |
| 4096 / 1 | Prefill | 10,515.30 | 13,571.47 | +29.06% |
| 512 / 128 | Decode | 160.74 | 164.53 | +2.36% |

Two warm-ups and five measured requests per case. Each case's five output
hashes are identical, and all paired hashes match stock. Initial engine startup
is excluded from request timings. Stock compiled the engine artifacts; unlocked
reused them. Both runs used two warm-ups per case and both reported the same
gumbel sampling kernel JIT warning before their first case summary. This is a
single stock/unlocked pair; the small decode difference is not evidence of a
large or universal generation benefit.

Both arms reported the same KV cache capacity (18.06 GiB / 1,051,824 tokens).
Both disabled custom allreduce because GPU P2P capability was absent or its test
failed. These TP=2 results reflect this PCIe-connected machine, not NVLink or a
single-card run.

[Raw vLLM result](results/baseline-vllm-20261025T174416.354859858Z/result.json).
[Unlocked vLLM result](results/unlocked-vllm-20261025T175124.012244512Z/result.json),
[comparison](comparison/vllm.json).

## Comparison conditions

Kernel 7.2.5-3-omarchy, NVIDIA 610.57.04, both board power ceilings 350 W.
No clocks or power limits were changed. `llama-swap.service` was stopped with
the user's authorization. Hyprland and its desktop processes remain on GPU 0.
The comparison verified identical runtime metadata, image, model revision and
all five script hashes; TP=2 was preserved. Every recorded power-ceiling sample
was 350 W. No NVRM Xid errors were found through benchmark completion. See
[validation and telemetry summary](comparison/validation.json) and
[activation evidence](installation/activation.json).

High-utilization GEMM samples showed similar board power (about 347–349 W)
with lower median SM clocks after unlocking. Whole-run peak temperatures were
55/56 C stock/unlocked in the GPU 0 run, and 54/57 C in the GPU 1 run. The CSVs
contain both cards and one-second sampling is coarse; these are short sequential
runs with different initial thermal conditions, not sustained power/cooling
or stability measurements. No repeated-boot study was performed.
