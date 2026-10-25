#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
action=${1:-help}
label=${2:-baseline}
system=${BENCH_SYSTEM:-rtx3080}
if [[ ! "$label" =~ ^[a-zA-Z0-9_-]+$ ]]; then
  echo 'Use letters, numbers, underscores or hyphens for the run label.' >&2
  exit 2
fi
if [[ ! "$system" =~ ^[a-zA-Z0-9_-]+$ ]]; then
  echo 'Invalid BENCH_SYSTEM.' >&2
  exit 2
fi
if [[ "$action" != help && "${GPU_BENCH_RECORDED:-0}" != 1 ]]; then
  exec python3 record.py --system "$system" --phase "$label" -- \
    env GPU_BENCH_RECORDED=1 bash -x "$0" "$@"
fi
mkdir -p cache model
if [[ ! -f image.lock ]]; then
  docker image inspect vllm/vllm-openai:v0.29.0 --format '{{.Id}}' > image.lock
fi
image=$(cat image.lock)
common=(--rm --user "$(id -u):$(id -g)" --shm-size 1g
  -v "$PWD:/bench" -w /bench -e HOME=/bench/cache
  -e HF_HOME=/bench/cache/huggingface -e VLLM_CACHE_ROOT=/bench/cache/vllm
  -e TRITON_CACHE_DIR=/bench/cache/triton -e OMP_NUM_THREADS=6)
case "$action" in
  download)
    docker run "${common[@]}" --entrypoint python3 "$image" download.py
    ;;
  torch|vllm)
    out="systems/$system/results/${label}-${action}-$(date -u +%Y%m%dT%H%M%S.%NZ)"
    mkdir -p "systems/$system/results"
    mkdir "$out"
    nvidia-smi -q > "$out/nvidia-before.txt"
    cat /proc/cmdline > "$out/kernel-cmdline.txt"
    uname -a > "$out/kernel.txt"
    cp image.lock "$out/"
    sha256sum run.sh record.py torch_bench.py vllm_bench.py download.py > "$out/scripts.sha256"
    mkdir "$out/source"
    cp run.sh record.py torch_bench.py vllm_bench.py download.py "$out/source/"
    [[ ! -f model.lock.json ]] || cp model.lock.json "$out/"
    nvidia-smi --query-gpu=timestamp,name,pstate,temperature.gpu,power.draw,power.limit,clocks.sm,clocks.mem,utilization.gpu,memory.used --format=csv -l 1 > "$out/gpu.csv" &
    monitor=$!
    finish() {
      status=$?
      trap - EXIT
      kill "$monitor" 2>/dev/null || true
      printf '{"exit_code": %d}\n' "$status" > "$out/status.json"
      nvidia-smi -q > "$out/nvidia-after.txt" || true
      exit "$status"
    }
    trap finish EXIT
    docker run "${common[@]}" --network none --device nvidia.com/gpu=all \
      -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 \
      -e BENCH_TP="${BENCH_TP:-1}" \
      -e BENCH_GPU="${BENCH_GPU:-0}" \
      --entrypoint python3 "$image" "${action}_bench.py" --output "/bench/$out/result.json" 2>&1 | tee "$out/run.log"
    echo "Saved: $PWD/$out"
    ;;
  *)
    echo 'Usage: ./run.sh download | torch [baseline|unlocked] | vllm [baseline|unlocked]'
    ;;
esac
