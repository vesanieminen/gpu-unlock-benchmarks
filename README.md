# gpu-unlock benchmarks

Reproducible stock/unlocked GPU benchmarks and a command journal, starting with
an RTX 3080 10 GB and continuing on a separate dual RTX 3090 system.

## Current results

| System | State | BF16 TFLOPS | FP16 TFLOPS | TF32 TFLOPS |
| --- | --- | ---: | ---: | ---: |
| RTX 3080 10 GB | Recorded stock baseline | 62.54 | 62.32 | 31.00 |
| RTX 3080 10 GB | Unlocked | 107.40 | 104.85 | 51.93 |
| RTX 3080 10 GB | Percentage increase | **+71.75%** | **+68.25%** | **+67.54%** |
| 2× RTX 3090 | Stock/unlocked | Pending | Pending | Pending |

Gains use the full-precision medians from the recorded repeat baseline; the
original stock run remains preserved in the raw results.

The selected vLLM application test also passes on the 3080 with native BF16
Qwen2.5-3B-Instruct and OMP_NUM_THREADS=1:

| Input tokens | Output tokens | Stock prefill tok/s | Unlocked prefill tok/s | Prefill increase | Stock decode tok/s | Unlocked decode tok/s | Decode increase |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 512 | 1 | 8,371.57 | 11,906.04 | **+42.22%** | — | — | — |
| 2,048 | 1 | 9,428.96 | 14,956.44 | **+58.62%** | — | — | — |
| 4,096 | 1 | 8,942.63 | 14,172.86 | **+58.49%** | — | — | — |
| 512 | 128 | 8,396.36 | 12,188.48 | **+45.16%** | 89.10 | 89.91 | +0.91% |

[Final vLLM baseline with raw timings and source snapshots](systems/rtx3080/results/baseline-final-vllm-20261025T162003.098487616Z/).
This is the stock application baseline to compare against the matching unlocked
run. The earlier successful vLLM fit test used six CPU threads; retain it as a
separate setup experiment. The PyTorch script explicitly sets its CPU threads
to six independently of the container's OMP setting; its GPU math is unchanged.

These are median GEMM results, not LLM throughput. Raw samples, precision flags,
software versions and GPU telemetry are under [systems/rtx3080](systems/rtx3080/).
The first stock PyTorch run predates the automatic recorder; its provenance is
documented in [reconstructed history](systems/rtx3080/history-reconstructed.md).
Failures and incomplete runs remain in the journal and must not be counted as
benchmark results. gpu-unlock is now installed and configured for automatic
early boot activation on the 3080; both prepared boot images passed validation.
Reboot activation and both unlocked benchmarks are now confirmed. BF16 GEMM
improved 71.75% against the recorded repeat baseline; vLLM 2K prefill improved
58.62%, with decode approximately unchanged (+0.91%). All tested output hashes
match. See the [full comparison and limitations](systems/rtx3080/RESULTS.md)
and [installation record](INSTALL.md).

## Run the benchmarks

Requirements: Linux, NVIDIA driver, Docker, NVIDIA Container Toolkit with
`nvidia.com/gpu=all` CDI devices, and host Python 3. The container contains PyTorch
and vLLM. No host Python packages are installed. The current 3B model requires
about 6 GB of downloads. Weights and caches are ignored by Git.

```bash
git clone https://github.com/vesanieminen/gpu-unlock-benchmarks.git
cd gpu-unlock-benchmarks
python3 record.py --system rtx3080 --phase preparation -- docker pull "$(cat image.lock)"
bash run.sh download
bash run.sh torch baseline
bash run.sh vllm baseline
# Install/enable gpu-unlock separately, record every command, and reboot.
bash run.sh torch unlocked
bash run.sh vllm unlocked
```

The launcher records its full expanded shell commands, merged stdout/stderr,
start/end times, working directory and exit status automatically. Results go
under `systems/rtx3080/results/`; command transcripts under
`systems/rtx3080/commands/`. No power limits, clocks or startup services are changed.
The [command index](systems/rtx3080/COMMANDS.md) links each command to its metadata,
exit status and complete transcript.
The GPU's existing firmware power ceiling remains in force; "no added cap" does
not mean unlimited board power. The initial 3080 ceiling is 320 W.

## Record the optimization process

Use the recorder for every setup, installation, configuration, verification and
rollback command. Failures are useful evidence and should be retained.

```bash
python3 record.py --system rtx3080 --phase inspection -- nvidia-smi -q
python3 record.py --system rtx3080 --phase preparation -- docker pull "$(cat image.lock)"
# For a shell script or pipeline, include bash -x to capture its inner commands:
python3 record.py --system rtx3080 --phase inspection -- bash -x -c 'uname -a; lscpu; free -h'
# If an authorized step needs root, put pkexec after -- and authenticate in its dialog.
```

For installation scripts, use `bash -x path/to/script` through the recorder.
For interactive root changes, record individual commands rather than opening
an unlogged root shell. For reboot, record `pkexec systemctl reboot`; an abrupt
shutdown may leave the journal's exit status null. After reboot, record kernel
logs and verification, including the gpu_unlock boot message. A null exit status
means the recorder did not observe completion, not success.

Do not put credentials in argv or scripts; review logs before committing. The
recorder captures commands invoked through it, not unrelated terminal activity.
It records no environment dump or authentication input. Source changes live in
Git; this journal records the operational steps. Do not fabricate transcripts
for work done before the recorder existed.

## Benchmark method

- **PyTorch:** 8192×8192 GEMM in BF16, FP16 and explicitly enabled TF32, with
  FP32 accumulation. Preallocated output, 20 warm-ups, five samples of 50 calls,
  CUDA-event timing. Reports TFLOPS and a seeded output hash for numerical parity.
- **vLLM:** original, unquantized Qwen2.5-3B-Instruct BF16, entirely on GPU,
  no CPU offload, no speculative decoding, prefix caching disabled. An 8,192-token
  context, one sequence, CUDA graph capture for batch size one, 2,048-token
  prefill chunks, and 90% GPU
  memory allocation target. This memory target does not limit compute or power.
  OMP_NUM_THREADS=1 follows vLLM's CPU-thread recommendation.
- **LLM cases:** synthetic deterministic 512/2,048/4,096-token prompts with one
  output token for prefill; 512 input / 128 output for decode. Two warm-ups and
  five measured requests per case. These measure speed, not model answer quality.
- **Timing:** prefill is first scheduling to first token; TTFT includes frontend
  and queue latency. Decode excludes the first token. Client wall time is separate.
  These are offline engine measurements without HTTP overhead.

Close unrelated GPU workloads and run one benchmark at a time. Compare identical
cases on the same machine, with the same model revision, image, scripts, power
and clock configuration. Inspect recorded temperatures, power and clocks.
Changing a power ceiling between arms invalidates attribution to gpu-unlock alone.

The image is pinned by portable digest in image.lock; the model by Git revision
in model.lock.json. Each new run saves source snapshots, script hashes, exit status, kernel information, detailed
NVIDIA state and one-second GPU telemetry. The imported first run used the same
image but recorded its local image ID instead of the portable digest.

## Second system: two RTX 3090s

Inspect the second machine first; its CPU, memory and GPU interconnect are unknown.

```bash
BENCH_SYSTEM=dual-rtx3090 bash run.sh download
BENCH_SYSTEM=dual-rtx3090 BENCH_GPU=0 bash run.sh torch baseline-gpu0
BENCH_SYSTEM=dual-rtx3090 BENCH_GPU=1 bash run.sh torch baseline-gpu1
BENCH_SYSTEM=dual-rtx3090 BENCH_TP=2 bash run.sh vllm baseline
```

For manual commands use `record.py --system dual-rtx3090`. Repeat with unlocked
labels after enabling the optimization. Single-card versus tensor-parallel LLM
results are different configurations; compare each only to its matching baseline.
The small model permits a shared test across systems, not a maximum-capacity test
of 48 GB aggregate VRAM. See [dual-3090 notes](systems/dual-rtx3090/).

## References

- [gpu-unlock](https://github.com/Zagitta/gpu-unlock)
- [RTX 3080 10 GB report and GEMM methodology](https://github.com/Zagitta/gpu-unlock/issues/14)
- [Qwen2.5-3B-Instruct original model](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct)
- [Why the initial Qwen3-4B choice was replaced](systems/rtx3080/vllm-memory-fit.md)
