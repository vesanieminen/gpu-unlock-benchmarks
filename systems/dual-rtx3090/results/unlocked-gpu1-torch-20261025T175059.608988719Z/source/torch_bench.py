"""8192-cubed GEMM; CUDA-event timing, FP32 accumulation, output parity hash."""
import argparse
import hashlib
import json
import os
import statistics
from pathlib import Path
import torch

p = argparse.ArgumentParser()
p.add_argument('--output', required=True)
args = p.parse_args()
torch.cuda.set_device(int(os.environ.get('BENCH_GPU', '0')))
torch.set_num_threads(6)
torch.manual_seed(20261025)
torch.backends.cuda.matmul.allow_fp16_reduced_precision_reduction = False
torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = False
if hasattr(torch.backends.cuda.matmul, 'allow_fp16_accumulation'):
    torch.backends.cuda.matmul.allow_fp16_accumulation = False
torch.backends.cuda.matmul.allow_tf32 = True
result = {'torch': torch.__version__, 'cuda': torch.version.cuda,
          'gpu': torch.cuda.get_device_name(), 'size': 8192,
          'gpu_index': torch.cuda.current_device(),
          'warmup_calls': 20, 'calls_per_sample': 50, 'samples': 5,
          'fp32_accumulation': True, 'results': []}
with torch.inference_mode():
    for name, dtype in [('BF16', torch.bfloat16), ('FP16', torch.float16), ('TF32', torch.float32)]:
        a = torch.randn(8192, 8192, device='cuda', dtype=dtype)
        b = torch.randn_like(a)
        c = torch.empty_like(a)
        for _ in range(20):
            torch.mm(a, b, out=c)
        torch.cuda.synchronize()
        samples = []
        for _ in range(5):
            start, end = (torch.cuda.Event(enable_timing=True) for _ in range(2))
            start.record()
            for _ in range(50):
                torch.mm(a, b, out=c)
            end.record()
            end.synchronize()
            samples.append(2 * 8192**3 * 50 / (start.elapsed_time(end) / 1000) / 1e12)
        # Smaller seeded output records numerical parity independently of timing.
        torch.manual_seed(42)
        x = torch.randn(1024, 1024, device='cuda', dtype=dtype)
        y = torch.randn_like(x)
        z = x @ y
        row = {'precision': name, 'median_tflops': statistics.median(samples),
               'samples_tflops': samples,
               'finite': bool(torch.isfinite(c).all().item()),
               'parity_sha256': hashlib.sha256(z.contiguous().view(torch.uint8).cpu().numpy().tobytes()).hexdigest()}
        result['results'].append(row)
        print(json.dumps(row), flush=True)
        del a, b, c, x, y, z
Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
