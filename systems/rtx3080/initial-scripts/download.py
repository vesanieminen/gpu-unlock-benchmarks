"""Download original BF16 weights, fixing the exact revision for both boots."""
import json
from pathlib import Path
from huggingface_hub import HfApi, snapshot_download

repo = 'Qwen/Qwen3-4B-Instruct-2507'
lock = Path('model.lock.json')
if lock.exists():
    spec = json.loads(lock.read_text())
else:
    spec = {'repo': repo, 'revision': HfApi().model_info(repo).sha}
    lock.write_text(json.dumps(spec, indent=2) + '\n')
snapshot_download(repo_id=spec['repo'], revision=spec['revision'], local_dir='model',
                  allow_patterns=['*.safetensors', '*.json', '*.jinja', '*.txt'],
                  max_workers=2)
config = json.loads(Path('model/config.json').read_text())
assert config.get('torch_dtype', config.get('dtype')) == 'bfloat16'
assert not config.get('quantization_config')
print('Original BF16 model ready:', spec, flush=True)
