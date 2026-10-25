# Earlier commands — reconstructed from the assistant session

These commands ran before record.py existed. This is a human-readable
reconstruction from visible session tool calls, not a live terminal recording
or a claim of complete shell history. Per-command timestamps and complete raw
output are unavailable unless an artifact below supplies them. Read-only
exploratory searches unrelated to the benchmarks are not reproduced here.

## Hardware and existing setup

```bash
nvidia-smi --query-gpu=name,memory.total,driver_version,power.limit --format=csv
lscpu
free -h
cat ~/.local/share/vllm/server-config.json
ls ~/.local/share/vllm/models
rg --files ~/.local/share/ollama/models/manifests
```

The sandboxed nvidia-smi failed to communicate with the driver. The read-only
probe was repeated outside the sandbox; no driver repair was needed:

```bash
nvidia-smi --query-gpu=name,memory.total,driver_version,power.limit,pcie.link.gen.current,pcie.link.width.current --format=csv
nvidia-smi topo -m
nvidia-smi --query-gpu=name,memory.total,memory.used,power.limit,power.max_limit,temperature.gpu --format=csv
```

Found one RTX 3080 10 GB, driver 610.57.04, 320 W current ceiling, 375 W advertised
maximum, Ryzen 5 5600X and 16 GB class RAM. Historical two-GPU configuration
files do not describe the hardware currently attached to this host.

```bash
systemctl is-enabled vllm-boot.service ollama.service
systemctl is-active vllm-boot.service ollama.service
docker inspect --format '{{.Name}} restart={{.HostConfig.RestartPolicy.Name}} status={{.State.Status}}' qwen38-vllm
docker ps -a --format '{{.Names}}\t{{.Image}}\t{{.Status}}'
docker images --format '{{.Repository}}:{{.Tag}}'
```

Both model services were disabled/inactive; the saved qwen38-vllm container was
exited with restart=no. No startup services were modified.

## PyTorch/container verification

```bash
docker image inspect vllm/vllm-openai:v0.29.0 --format '{{.Id}} {{json .Config.Entrypoint}}'
docker run --rm --network none --entrypoint python vllm/vllm-openai:v0.29.0 -c 'import torch,vllm; print("torch",torch.__version__,"vllm",vllm.__version__)'
```

The second command failed: the image has python3, not a python executable.

```bash
docker run --rm --network none --device nvidia.com/gpu=all --entrypoint python3 vllm/vllm-openai:v0.29.0 -c 'import torch,vllm; print("torch",torch.__version__,"vllm",vllm.__version__,"cuda",torch.version.cuda); print(torch.cuda.get_device_name()); print((torch.ones(8,8,device="cuda",dtype=torch.bfloat16) @ torch.ones(8,8,device="cuda",dtype=torch.bfloat16)).sum())'
```

Succeeded: PyTorch 2.13.0+cu130, vLLM 0.29.0, CUDA 13.0; BF16 multiplication
returned 512 on the RTX 3080. No packages were installed on the host.

## Original working directory and first baseline

Scripts were created with the assistant's file patch tool in
`/home/vesanieminen/gpu-unlock-bench`. Script creation was not a shell command.

```bash
mkdir -p /home/vesanieminen/gpu-unlock-bench
bash -n gpu-unlock-bench/run.sh
python3 -m py_compile gpu-unlock-bench/download.py gpu-unlock-bench/torch_bench.py gpu-unlock-bench/vllm_bench.py
cd /home/vesanieminen/gpu-unlock-bench
bash run.sh download
bash run.sh torch baseline
```

The download fetched original BF16 Qwen3-4B-Instruct-2507 weights at revision
cdbee75f17c01a7cc42f958dc650907174af0554 (about 7.6 GiB on disk).
The stock PyTorch baseline began at 2026-10-25 15:11:29 UTC. Raw artifacts are
preserved under results/baseline-torch-20261025T151129Z/.

| Precision | Median TFLOPS |
| --- | ---: |
| BF16 | 62.1914653457 |
| FP16 | 61.1552973068 |
| TF32 | 30.5349469254 |

No power/clock changes, gpu-unlock installation or boot configuration changes
were performed. vLLM timing fields were adapted to the installed version:
first_token_ts, scheduled_ts, last_token_ts and first_token_latency. An early
import probe for RequestMetrics from vllm.sequence failed; the installed type
is RequestStateStats in vllm.v1.metrics.stats. Source files inside the image
were read to confirm the field names and the need for disable_log_stats=False.

## Repository setup

```bash
git ls-remote https://github.com/vesanieminen/gpu-unlock-benchmarks.git
gh auth status
git clone https://github.com/vesanieminen/gpu-unlock-benchmarks.git /home/vesanieminen/Projects/gpu-unlock-benchmarks
docker image inspect vllm/vllm-openai:v0.29.0 --format '{{json .RepoDigests}}'
```

The repository was empty and GitHub authenticated as vesanieminen. Scripts,
model lock, image lock and the first baseline directory were copied from the
original working directory. Initially model/cache were host symlinks; the first
live-recorded vLLM run failed because those targets were not mounted in Docker.
The recorded correction copies them using filesystem reflinks into ignored
local directories. Both failure and correction are retained in commands/.
All benchmark launcher invocations after this point record themselves.
