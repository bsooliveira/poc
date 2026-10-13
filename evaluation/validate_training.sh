#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh
require_idle
if podman container exists simplfaq-model-validation || podman container exists simplfaq-final-smoke; then
  echo 'Aguarde o teste de geração local concluir antes de executar o smoke de treinamento.' >&2
  exit 1
fi
mkdir -p artifacts/training-smoke
# The fixture is synthetic; it does not approve or train on application events.
podman exec -i simplfaq-api python - <<'PY'
import httpx
from app.config import settings
cfg = settings()
httpx.post(cfg.ollama_url + '/api/generate', json={'model': cfg.ollama_model, 'keep_alive': 0}, timeout=30, trust_env=False).raise_for_status()
# Also unload the larger diagnostic model if it was tested.
httpx.post(cfg.ollama_url + '/api/generate', json={'model': 'qwen2.5:3b', 'keep_alive': 0}, timeout=30, trust_env=False).raise_for_status()
PY
podman run --rm --name simplfaq-training-smoke --network none --env HF_HOME=/data/models/huggingface --env HF_HUB_OFFLINE=1 --env TOKENIZERS_PARALLELISM=false \
  --volume simplfaq-data:/data --volume "$PWD/evaluation:/evaluation:ro" --volume "$PWD/artifacts/training-smoke:/output:rw" \
  localhost/simplfaq-api:poc python -m app.train_lora --dataset /evaluation/training-fixture.jsonl --output /output/adapter --steps 2
podman run --rm --network none --env HF_HOME=/data/models/huggingface --env HF_HUB_OFFLINE=1 \
  --volume simplfaq-data:/data --volume "$PWD/artifacts/training-smoke:/output:ro" localhost/simplfaq-api:poc \
  python -m app.predict_lora --adapter /output/adapter --prompt 'Evidence: O evento sintético será online. Question: What is the event format?'
