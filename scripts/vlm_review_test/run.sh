#!/bin/bash
# Local vision-model slide review test on one V100: installs a pinned vLLM into its own venv (kept on Lustre and
# reused by later runs), serves the model, runs review.py on the manifest's 50 screenshots, then stops the server.
# Runs inside the project container with the GPU bound: as a Tapis job
#   python scripts/submit_phase2_rerun.py <job that holds the screenshots> --task vlm_test
# or under sbatch: singularity exec --nv --bind /expanse/lustre <image> bash /app/scripts/vlm_review_test/run.sh
# Results: ./vlm_review_test/ (summary.md, results.json, vllm_server.log, nvidia-smi.txt, versions.txt)
set -euo pipefail

MODEL="${VLM_MODEL:-Qwen/Qwen3-VL-8B-Instruct}"
SPEC="${VLLM_SPEC:-vllm<0.19}"  # 0.20+ requires compute capability 7.5; the V100 is 7.0
CACHE="${VLM_CACHE:-/expanse/lustre/scratch/harvest/temp_project/.cache/vlm_review_test}"
VENV="$CACHE/venv-$(printf '%s' "$SPEC" | tr -c 'A-Za-z0-9.' '_')"
PORT="${VLM_PORT:-8011}"
OUT="${VLM_OUT:-vlm_review_test}"
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$CACHE" "$OUT"
export HF_HOME="$CACHE/huggingface"  # the model download (~17 GB for 8B) is kept for later runs

echo "== GPU and driver (the vLLM wheel's CUDA version must be supported by this driver)"
nvidia-smi | tee "$OUT/nvidia-smi.txt"

if [ ! -x "$VENV/bin/vllm" ]; then
    echo "== Installing '$SPEC' into $VENV (first run only; several GB)"
    python -m venv "$VENV"
    "$VENV/bin/pip" install --upgrade pip
    "$VENV/bin/pip" install "$SPEC"
fi
"$VENV/bin/pip" list 2>/dev/null | grep -iE "^(vllm|torch|transformers|xgrammar) " | tee "$OUT/versions.txt"

echo "== Starting vLLM: $MODEL (fp16: the V100 has no bf16)"
# PYTHONPATH is the container's /app: cleared so the venv's vLLM imports only its own packages
PYTHONPATH= "$VENV/bin/vllm" serve "$MODEL" --dtype half --port "$PORT" --max-model-len 16384 \
    --gpu-memory-utilization 0.90 --limit-mm-per-prompt '{"image": 4}' ${VLLM_EXTRA_ARGS:-} \
    > "$OUT/vllm_server.log" 2>&1 &
SERVER=$!
trap 'kill "$SERVER" 2>/dev/null || true' EXIT

up() { python -c "import urllib.request; urllib.request.urlopen('http://localhost:$PORT/v1/models', timeout=5)" 2>/dev/null; }
for _ in $(seq 1 180); do  # up to 30 min: model download, load and CUDA graph capture
    if up; then break; fi
    if ! kill -0 "$SERVER" 2>/dev/null; then
        echo "[ERROR] vLLM exited during startup; last lines of $OUT/vllm_server.log:"
        tail -80 "$OUT/vllm_server.log"
        exit 1
    fi
    sleep 10
done
up || { echo "[ERROR] vLLM not up after 30 min"; tail -80 "$OUT/vllm_server.log"; exit 1; }
echo "== Server up"
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv | tee -a "$OUT/nvidia-smi.txt"

python "$HERE/review.py" --base-url "http://localhost:$PORT/v1" --model "$MODEL" \
    ${VLM_SHOTS_DIR:+--shots-root "$VLM_SHOTS_DIR"} --out "$OUT"
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv | tee -a "$OUT/nvidia-smi.txt"
echo "== Done: $OUT/summary.md"
