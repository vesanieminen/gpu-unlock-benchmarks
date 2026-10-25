# RTX 3080 gpu-unlock benchmarks

Run from this directory. Docker and working NVIDIA CDI (`nvidia.com/gpu=all`) are required.

```bash
bash run.sh download
bash run.sh torch baseline
bash run.sh vllm baseline
# After installing gpu-unlock and rebooting:
bash run.sh torch unlocked
bash run.sh vllm unlocked
```

No power limits, clock offsets, driver settings or startup services are changed.
The card's existing firmware power limit still applies; GPU telemetry is saved.
Run one benchmark at a time with other GPU workloads closed.

The installed vLLM 0.29.0 Docker image is pinned by image ID in image.lock.
The original Qwen3-4B-Instruct-2507 BF16 weights are pinned by commit in
model.lock.json. About 8 GB must be downloaded. Both tests reuse that exact image
and run without network access. Preserve these locks and scripts across boots.

PyTorch measures 8192×8192 GEMM in BF16, FP16 and TF32 using FP32 accumulation,
20 warm-up calls, five samples of 50 calls, CUDA events and preallocated outputs.
It records median TFLOPS, all samples, finite-output checks and a seeded output
hash for checking before/after numerical parity. TF32 is explicitly enabled.

vLLM runs unquantized BF16 entirely on one GPU with no CPU offload, no speculative
decoding, no prefix caching and CUDA graph capture for batch size one. The
2,048-token context and one active sequence keep memory use small. Chunked
prefill supports batches up to 2,048 tokens. The 92% GPU memory setting reserves
memory for the model and KV cache; it does not throttle compute or power.

Deterministic synthetic token inputs test performance, not model answer quality.
There are two warm-ups and five measured runs per case. The prefill cases are
512/1,024/1,792 input tokens and one output token; the decode case is 512 input
and 128 forced output tokens. Prefill timing runs from first scheduling to first
token; TTFT includes queue time. Decode throughput excludes the first token.
The client wall time is recorded separately. These are offline vLLM engine
measurements, without HTTP overhead. Prefix caching stays disabled even for
identical warm-up prompts.

Each run creates a unique directory under results containing result.json,
run.log, GPU telemetry, detailed before/after NVIDIA state, kernel and image/model
versions. Compare medians for corresponding cases across boots and inspect
temperature, power and clock telemetry for throttling or changed conditions.
