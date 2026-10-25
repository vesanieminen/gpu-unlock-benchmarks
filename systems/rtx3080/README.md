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
vLLM remains unverified until a successful result is recorded. gpu-unlock has
not been installed as part of this repository setup.
