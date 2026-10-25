# BF16 vLLM memory-fit attempts

The original Qwen3-4B BF16 checkpoint is 7.49 GiB on disk and vLLM reports
7.64 GiB for loaded model memory. CUDA, graph capture, profiling/compute
buffers and KV cache need additional space. This GPU also drives the desktop.
These are memory-capacity issues, not driver permissions or power throttling.

All attempts use the same pinned model/image, BF16 weights, 2,048-token maximum
context, one sequence and no CPU offload. Complete commands and engine logs
are retained, including failures.

| Attempt (UTC) | Prefill chunk | Memory fraction | Outcome |
| --- | ---: | ---: | --- |
| 15:56:46 | 2,048 | 0.92 | Host symlink target was not visible in Docker; corrected by copying the model into the ignored local model directory. |
| 15:58:59 | 2,048 | 0.92 | Model loads, but profiling leaves -0.35 GiB for KV cache. |
| 16:01:28 | 1,024 | 0.94 | Startup rejected: 8.87 GiB free is less than the requested 9.04 GiB. |
| 16:02:15 | 512 | 0.90 | 0.17 GiB KV cache available, but 0.28 GiB needed for the configured context; estimated maximum 1,248 tokens. |
| 16:03:34 | 512 | 0.92 | Engine starts, but inference exhausts GPU memory. |

The Qwen3-4B configuration was rejected as too tight for a reliable benchmark
on this desktop GPU. The application benchmark now uses Qwen2.5-3B-Instruct in
native BF16, with a larger 8,192-token context and 2,048-token prefill chunks.
Its smaller weights and two KV heads leave more room for inference buffers.
The original 4B lock is retained as qwen3-4b-model.lock.json and each failed run
keeps its original model lock and script hashes. Historical data is not relabeled
as the new model.

The memory fraction controls allocations; it does not cap GPU compute or power.
The final comparison must use the same successful chunk size, memory fraction
and context configuration before and after enabling gpu-unlock. Desktop memory
use can vary; if startup rejects the requested allocation, close other GPU
applications rather than silently changing benchmark settings between arms.
