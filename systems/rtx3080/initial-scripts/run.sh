#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
action=${1:-help}
label=${2:-baseline}
if [[ ! "$label" =~ ^[a-zA-Z0-9_-]+$ ]]; then
  echo 'Use letters, numbers, underscores or hyphens for the run label.' >&2
  exit 2
fi
mkdir -p cache model results
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
    out="results/${label}-${action}-$(date -u +%Y%m%dT%H%M%SZ)"
    mkdir "$out"
    nvidia-smi -q > "$out/nvidia-before.txt"
    cat /proc/cmdline > "$out/kernel-cmdline.txt"
    uname -a > "$out/kernel.txt"
    cp image.lock "$out/"
    [[ ! -f model.lock.json ]] || cp model.lock.json "$out/"
    nvidia-smi --query-gpu=timestamp,name,pstate,temperature.gpu,power.draw,power.limit,clocks.sm,clocks.mem,utilization.gpu,memory.used --format=csv -l 1 > "$out/gpu.csv" &
    monitor=$!
    trap 'kill "$monitor" 2>/dev/null || true' EXIT
    docker run "${common[@]}" --network none --device nvidia.com/gpu=all \
      -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 \
      --entrypoint python3 "$image" "${action}_bench.py" --output "/bench/$out/result.json" 2>&1 | tee "$out/run.log"
    nvidia-smi -q > "$out/nvidia-after.txt"
    echo "Saved: $PWD/$out"
    ;;
  *)
    echo 'Usage: ./run.sh download | torch [baseline|unlocked] | vllm [baseline|unlocked]'
    ;;
esac
