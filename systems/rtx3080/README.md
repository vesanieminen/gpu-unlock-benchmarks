# RTX 3080 system

- GPU: NVIDIA GeForce RTX 3080, 10,240 MiB VRAM
- CPU: AMD Ryzen 5 5600X, 6 cores / 12 threads
- System RAM: 16 GB class (15 GiB reported)
- NVIDIA driver: 610.57.04
- Initial configured power ceiling: 320 W; maximum advertised ceiling: 375 W
- No power or clock settings changed for these benchmarks.

The stock baseline measured BF16 62.1915 TFLOPS, FP16 61.1553 TFLOPS,
and TF32 30.5349 TFLOPS. See the raw samples and telemetry in results/.

A second stock run verified the automatic recorder and source snapshots:
BF16 62.5351, FP16 62.3199, TF32 30.9953 TFLOPS. All three seeded parity hashes
match the first baseline. These are repeat measurements, not unlocked results.

The initial PyTorch run predates automatic command recording. Its copied raw
artifacts are unchanged; history-reconstructed.md documents its provenance.
vLLM Qwen2.5-3B-Instruct BF16 is verified with the full prefill/decode suite.
Loaded model memory is 5.79 GiB; vLLM reported 1.51 GiB available for KV cache.
The final stock baseline uses OMP_NUM_THREADS=1 and is saved under
results/baseline-final-vllm-20261025T162003.098487616Z/.
The 2,048-token prefill median is 9,428.96 tok/s; decode is 89.10 tok/s.
gpu-unlock has not been installed as part of this repository setup.
