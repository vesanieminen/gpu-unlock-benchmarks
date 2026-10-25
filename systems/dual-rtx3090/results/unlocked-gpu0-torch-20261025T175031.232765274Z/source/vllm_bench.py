"""Sequential, uncached BF16 prefill and decode with deterministic token inputs."""
import argparse
import hashlib
import json
import os
import random
import statistics
import time
from pathlib import Path
import torch
import vllm
from vllm import LLM, SamplingParams

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', required=True)
    args = p.parse_args()
    tp = int(os.environ.get('BENCH_TP', '1'))
    llm = LLM(model='/bench/model', dtype='bfloat16', tensor_parallel_size=tp,
              max_model_len=8192, max_num_seqs=1, max_num_batched_tokens=2048,
              gpu_memory_utilization=0.90, enable_prefix_caching=False,
              enable_chunked_prefill=True, seed=42,
              compilation_config={'cudagraph_capture_sizes': [1]},
              disable_log_stats=False)
    rng = random.Random(42)
    tokens = [rng.randrange(1000, 30000) for _ in range(4096)]
    result = {'torch': torch.__version__, 'vllm': vllm.__version__,
              'gpu': torch.cuda.get_device_name(), 'dtype': 'bfloat16',
              'tensor_parallel_size': tp,
              'max_model_len': 8192, 'max_num_seqs': 1, 'prefix_cache': False,
              'gpu_memory_utilization': 0.90, 'max_num_batched_tokens': 2048,
              'model': json.loads(Path('model.lock.json').read_text()),
              'warmups_per_case': 2, 'measured_runs_per_case': 5, 'results': []}
    for length, output in [(512, 1), (2048, 1), (4096, 1), (512, 128)]:
        params = SamplingParams(temperature=0, max_tokens=output, min_tokens=output, ignore_eos=True)
        prompt = {'prompt_token_ids': tokens[:length]}
        rows = []
        for run in range(7):
            start = time.perf_counter()
            response = llm.generate([prompt], params, use_tqdm=False)[0]
            wall = time.perf_counter() - start
            m = response.metrics
            prefill = m.first_token_ts - m.scheduled_ts
            count = len(response.outputs[0].token_ids)
            row = {'wall_seconds': wall, 'prefill_seconds': prefill,
                   'prefill_tok_s': length / prefill,
                   'ttft_seconds': m.first_token_latency,
                   'output_tokens': count,
                   'output_sha256': hashlib.sha256(json.dumps(response.outputs[0].token_ids).encode()).hexdigest()}
            if count > 1:
                row['decode_tok_s'] = (count - 1) / (m.last_token_ts - m.first_token_ts)
            if run >= 2:
                rows.append(row)
        medians = {key: statistics.median(r[key] for r in rows)
                   for key in rows[0] if key not in ('output_sha256', 'output_tokens')}
        case = {'input_tokens': length, 'output_tokens': output, 'medians': medians, 'runs': rows}
        result['results'].append(case)
        Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps({'input_tokens': length, 'output_tokens': output, **medians}), flush=True)

if __name__ == '__main__':
    main()
