# BF16 vLLM memory-fit attempts

The original Qwen3-4B BF16 checkpoint is 7.49 GiB on disk and vLLM reports
7.64 GiB for loaded model memory. CUDA, graph capture, profiling/compute
buffers and KV cache need additional space. This GPU also drives the desktop.
These are memory-capacity issues, not driver permissions or power throttling.

The following 4B attempts use the same pinned model/image, BF16 weights, 2,048-token maximum
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

The 3B download completed at the pinned revision. Its first launcher invocation
exited 2 after download completion because run.sh was edited while that shell
was active; the parser then reported an unexpected EOF. The saved launcher
passed bash -n, and a repeat download invocation using the completed cache
exited 0. Both transcripts are retained. Do not edit scripts during active runs.

## Verified replacement and final baseline

Qwen2.5-3B-Instruct native BF16 passed the complete application test at 16:18 UTC:
5.79 GiB loaded model memory, 1.51 GiB available for KV cache, 8,192-token maximum
context and 2,048-token prefill chunks. The initial successful run used six CPU
threads. Following vLLM's contention warning, the final baseline at 16:20 UTC
uses OMP_NUM_THREADS=1 and also passed all four cases. It reports 9,428.96 tok/s
for 2,048-token prefill and 89.10 tok/s for decode. Both successful runs and all
failed attempts are preserved. No power/clock settings were changed.

The memory fraction controls allocations; it does not cap GPU compute or power.
The final comparison must use the same successful chunk size, memory fraction
and context configuration before and after enabling gpu-unlock. Desktop memory
use can vary; if startup rejects the requested allocation, close other GPU
applications rather than silently changing benchmark settings between arms.
