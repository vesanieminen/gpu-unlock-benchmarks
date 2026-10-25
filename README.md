# gpu-unlock benchmarks

Reproducible stock/unlocked GPU benchmarks and a command journal, starting with
an RTX 3080 10 GB and continuing on a separate dual RTX 3090 system.

## Current results

| System | State | BF16 TFLOPS | FP16 TFLOPS | TF32 TFLOPS |
| --- | --- | ---: | ---: | ---: |
| RTX 3080 10 GB | Stock baseline | 62.19 | 61.16 | 30.53 |
| RTX 3080 10 GB | Unlocked | Pending | Pending | Pending |
| 2× RTX 3090 | Stock/unlocked | Pending | Pending | Pending |

These are median GEMM results, not LLM throughput. Raw samples, precision flags,
software versions and GPU telemetry are under [systems/rtx3080](systems/rtx3080/).
The first stock PyTorch run predates the automatic recorder; its provenance is
documented in [reconstructed history](systems/rtx3080/history-reconstructed.md).
Failures and incomplete runs remain in the journal and must not be counted as
benchmark results. gpu-unlock installation has not been performed yet.

## Run the benchmarks

Requirements: Linux, NVIDIA driver, Docker, NVIDIA Container Toolkit with
`nvidia.com/gpu=all` CDI devices, and host Python 3. The container contains PyTorch
and vLLM. No host Python packages are installed. About 8 GB is downloaded for
the model. Weights and caches are ignored by Git.

```bash
git clone https://github.com/vesanieminen/gpu-unlock-benchmarks.git
cd gpu-unlock-benchmarks
docker pull "$(cat image.lock)"
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
- **vLLM:** original, unquantized Qwen3-4B-Instruct-2507 BF16, entirely on GPU,
  no CPU offload, no speculative decoding, prefix caching disabled. A 2,048-token
  context, one sequence, CUDA graph capture for batch size one, and 92% GPU
  memory allocation target. This memory target does not limit compute or power.
- **LLM cases:** synthetic deterministic 512/1,024/1,792-token prompts with one
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
in model.lock.json. Each new run saves script hashes, kernel information, detailed
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
- [Qwen3-4B-Instruct-2507 original model](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)
