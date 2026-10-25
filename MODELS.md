# Model selection for BF16 prefill testing

The application benchmark should run original BF16 weights entirely on the GPU
and leave enough memory for substantial prompt-processing batches. Weight-only
size is insufficient to establish fit; model loading, profiling, CUDA graphs,
KV cache and actual requests all need to pass.

## RTX 3080 10 GB

The first candidate, Qwen3-4B-Instruct-2507 BF16, loaded its weights in 7.64 GiB
but did not complete the inference test reliably with the tried configurations.
Those failures remain in [the memory-fit log](systems/rtx3080/vllm-memory-fit.md).

The current candidate is [Qwen2.5-3B-Instruct](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct),
a dense 3.09B model. Its official config specifies bfloat16 and two KV heads,
reducing weight and cache memory compared with the first candidate. Its status
must remain unverified until an actual successful benchmark is saved. The
benchmark pins its original weights; no quantization or CPU offload is used.

## Gemma 4 and the future RTX 3090 system

Gemma 4 E2B and E4B have original BF16 checkpoints and floating-point matrix
operations in their attention and feed-forward layers. They are candidates for
testing prefill improvement, not a guarantee of a particular speedup.

The E denotes effective compute parameters. Large per-layer embedding tables
mean stored weights require more memory than the E2B/E4B names suggest. Google's
published approximate BF16 loading memory, including its loading overhead, is
11.4 GB for E2B and 17.9 GB for E4B; actual runtime and context requirements vary.
These are not comfortable default fully resident BF16 candidates for a 10 GB
3080. A 24 GB 3090 is a more suitable host to validate E2B and potentially E4B.
No Gemma download or benchmark has been performed as part of this setup.

Sources:

- [Google's Gemma 4 memory and architecture guidance](https://ai.google.dev/gemma/docs/core)
- [NVIDIA's Gemma 4 BF16 checkpoint overview](https://developer.nvidia.com/blog/?p=115165)
- [vLLM's Gemma 4 recipe](https://github.com/vllm-project/recipes/blob/main/Google/Gemma4.md)

Quantized model performance depends on the kernels the engine actually uses.
A config declaring a BF16 activation dtype does not mean its weight matmuls
are unquantized BF16 operations. Keep the native BF16 model test and the
PyTorch GEMM test as separate pieces of evidence.
