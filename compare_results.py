#!/usr/bin/env python3
"""Compare two successful runs; retain raw paths and checks for reproducibility."""
import argparse
import hashlib
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('unlocked', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    for directory in (args.baseline, args.unlocked):
        assert json.loads((directory / 'status.json').read_text())['exit_code'] == 0
    baseline = json.loads((args.baseline / 'result.json').read_text())
    unlocked = json.loads((args.unlocked / 'result.json').read_text())
    assert (args.baseline / 'image.lock').read_text() == (args.unlocked / 'image.lock').read_text()
    assert (args.baseline / 'kernel.txt').read_text() == (args.unlocked / 'kernel.txt').read_text()
    name = 'torch_bench.py' if 'size' in baseline else 'vllm_bench.py'
    assert (args.baseline / 'source' / name).read_bytes() == (args.unlocked / 'source' / name).read_bytes()
    if name == 'vllm_bench.py':
        assert (args.baseline / 'model.lock.json').read_bytes() == (args.unlocked / 'model.lock.json').read_bytes()
        assert (args.baseline / 'source/run.sh').read_bytes() == (args.unlocked / 'source/run.sh').read_bytes()
    rows = []
    for before, after in zip(baseline['results'], unlocked['results'], strict=True):
        if 'precision' in before:
            assert before['precision'] == after['precision']
            pairs = [('median_tflops', before['median_tflops'], after['median_tflops'])]
            row = {'precision': before['precision'], 'output_hashes_match': before['parity_sha256'] == after['parity_sha256']}
        else:
            assert (before['input_tokens'], before['output_tokens']) == (after['input_tokens'], after['output_tokens'])
            pairs = [(key, value, after['medians'][key]) for key, value in before['medians'].items()]
            row = {'input_tokens': before['input_tokens'], 'output_tokens': before['output_tokens'],
                   'output_hashes_match': [x['output_sha256'] for x in before['runs']] == [x['output_sha256'] for x in after['runs']]}
        row['metrics'] = {key: {'baseline': before_value, 'unlocked': after_value,
                               'change_percent': (after_value / before_value - 1) * 100}
                          for key, before_value, after_value in pairs}
        rows.append(row)
    report = {'baseline': str(args.baseline), 'unlocked': str(args.unlocked),
              'same_image': True, 'same_kernel': True, 'same_benchmark_source': True,
              'source_sha256': hashlib.sha256((args.baseline / 'source' / name).read_bytes()).hexdigest(),
              'results': rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
