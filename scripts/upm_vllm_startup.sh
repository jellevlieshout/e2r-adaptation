#!/bin/bash
# =============================================================================
# upm_vllm_startup.sh
#
# Starts a vLLM inference server on the UPM JupyterHub A100 cluster and
# exposes it publicly via ngrok with HTTP basic auth. Designed for
# JupyterHub environments that reset on every pod restart — installs
# vLLM into a persistent NFS-backed venv, downloads model weights to
# the persistent HF cache, then launches both processes in the background.
#
# Manual prerequisites (cannot currently be automated due to cluster
# security restrictions; see scripts/UPM_VLLM_README.md):
#   1. Log in to https://138.4.144.36/jupyterhub/user/jelle.vanlieshout/lab
#   2. Open a terminal in JupyterLab.
#   3. Export the three env vars below, then run this script.
#
# Required environment variables:
#   NGROK_AUTHTOKEN  — ngrok account authtoken (free tier is fine)
#   BASIC_AUTH_USER  — username for the public endpoint (default: jelle)
#   BASIC_AUTH_PASS  — password for the public endpoint (>= 8 chars)
#
# Logs:
#   tail -f /home/jovyan/vllm.log
#   tail -f /home/jovyan/ngrok.log
#
# Note: the ngrok subdomain rotates on every restart. Update the
# corresponding env var (VLLM_BASE_URL) on the e2r-adaptation API after
# each restart.
# =============================================================================

set -e

# =============================================================================
# CONFIGURATION — edit these before running
# =============================================================================

# --- Model selection -----------------------------------------------------
# Defaults are for the 7B baseline. To run the 70B target on the 40 GB A100,
# either edit these defaults or override via env, e.g.:
#
#   export MODEL="casperhansen/llama-3.3-70b-instruct-awq"
#   export QUANTIZATION="awq"
#   export MAX_MODEL_LEN=2048
#   export GPU_MEMORY_UTILIZATION=0.95
#
# Llama 3.3 70B Q4 weights are ~37 GB, leaving ~3 GB for the KV cache; that's
# enough for a single in-flight request at MAX_MODEL_LEN=2048. The API-side
# concurrency cap (VLLM_CONCURRENCY) must drop to 1 when using a 70B model.
MODEL="${MODEL:-Qwen/Qwen2.5-7B-Instruct}"           # HuggingFace model ID
QUANTIZATION="${QUANTIZATION:-}"                       # vLLM --quantization (awq, gptq, fp8...) or empty
MAX_MODEL_LEN="${MAX_MODEL_LEN:-4096}"                 # max context length
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.90}"  # vLLM GPU memory fraction
VLLM_PORT="${VLLM_PORT:-8000}"                         # vLLM listen port

HF_HOME="/home/jovyan/.cache/huggingface"  # Persistent HF cache (NFS)
VLLM_ENV="/home/jovyan/vllm-env"           # Persistent venv (NFS)
NGROK_BIN="/home/jovyan/ngrok"             # Persistent ngrok binary (NFS)
NGROK_LOG="/home/jovyan/ngrok.log"
VLLM_LOG="/home/jovyan/vllm.log"

# Auth — set your ngrok authtoken and basic auth credentials
NGROK_AUTHTOKEN="${NGROK_AUTHTOKEN:-}"     # Set via env or hardcode here
BASIC_AUTH_USER="${BASIC_AUTH_USER:-jelle}"       # Username for basic auth
BASIC_AUTH_PASS="${BASIC_AUTH_PASS:-}"            # Password for basic auth (>= 8 chars)

# Optional — HuggingFace token for gated repos (meta-llama/*, mistralai/*, etc).
# Get one at https://huggingface.co/settings/tokens (read-only is enough).
# Leave empty for ungated models — Qwen2.5, casperhansen/* AWQ mirrors, etc.
HF_TOKEN="${HF_TOKEN:-}"

# =============================================================================
# HELPERS
# =============================================================================

log() { echo "[$(date '+%H:%M:%S')] $*"; }

require_var() {
  if [ -z "${!1}" ]; then
    echo "ERROR: $1 is not set. Export it before running or edit this script."
    exit 1
  fi
}

# =============================================================================
# PREFLIGHT
# =============================================================================

require_var NGROK_AUTHTOKEN
require_var BASIC_AUTH_PASS

log "Starting LLM stack..."
log "Model:        $MODEL"
log "vLLM port:    $VLLM_PORT"
log "HF cache:     $HF_HOME"
if [ -n "$HF_TOKEN" ]; then
  log "HF auth:      <set> (gated repos accessible)"
else
  log "HF auth:      <not set> (gated repos will 401)"
fi

mkdir -p "$HF_HOME"

# Persist the HF token to disk so subsequent vLLM and snapshot_download calls
# in this venv pick it up automatically (huggingface_hub looks here first).
if [ -n "$HF_TOKEN" ]; then
  mkdir -p "$HF_HOME"
  echo "$HF_TOKEN" > "$HF_HOME/token"
  chmod 600 "$HF_HOME/token"
fi

# =============================================================================
# STEP 1 — Set up Python venv with vLLM
# =============================================================================

if [ ! -f "$VLLM_ENV/bin/python" ]; then
  log "Creating virtual environment at $VLLM_ENV ..."
  python -m venv "$VLLM_ENV"
  log "Installing vLLM (this may take a few minutes)..."
  "$VLLM_ENV/bin/pip" install --quiet vllm
  log "vLLM installed."
else
  log "vLLM venv already exists, skipping install."
fi

# =============================================================================
# STEP 2 — Pre-download model weights if not cached
# =============================================================================

log "Checking model cache..."
HF_HOME="$HF_HOME" HF_TOKEN="$HF_TOKEN" "$VLLM_ENV/bin/python" -c "
from huggingface_hub import snapshot_download
import os
token = os.environ.get('HF_TOKEN') or None
print('Downloading model weights if not cached...')
snapshot_download('$MODEL', token=token)
print('Model ready.')
"

# =============================================================================
# STEP 3 — Start vLLM server
# =============================================================================

# Kill any existing vLLM process
pkill -f "vllm.entrypoints.openai.api_server" 2>/dev/null && log "Stopped existing vLLM process." || true

log "Starting vLLM server (model=$MODEL quant=${QUANTIZATION:-none} max_len=$MAX_MODEL_LEN gpu_util=$GPU_MEMORY_UTILIZATION)..."
QUANT_FLAG=""
if [ -n "$QUANTIZATION" ]; then
  QUANT_FLAG="--quantization $QUANTIZATION"
fi
nohup bash -c "
  HF_HOME=$HF_HOME \
  HF_TOKEN=$HF_TOKEN \
  $VLLM_ENV/bin/python -m vllm.entrypoints.openai.api_server \
    --model $MODEL \
    --dtype auto \
    --max-model-len $MAX_MODEL_LEN \
    --gpu-memory-utilization $GPU_MEMORY_UTILIZATION \
    $QUANT_FLAG \
    --port $VLLM_PORT
" > "$VLLM_LOG" 2>&1 &

VLLM_PID=$!
log "vLLM PID: $VLLM_PID"

# Wait for vLLM to become healthy
log "Waiting for vLLM to become ready..."
for i in $(seq 1 60); do
  if wget -q -O- "http://localhost:$VLLM_PORT/health" > /dev/null 2>&1; then
    log "vLLM is up."
    break
  fi
  if [ "$i" -eq 60 ]; then
    log "ERROR: vLLM did not start within 60 seconds. Check $VLLM_LOG."
    exit 1
  fi
  sleep 5
done

# =============================================================================
# STEP 4 — Install ngrok if not present
# =============================================================================

if [ ! -f "$NGROK_BIN" ]; then
  log "Downloading ngrok..."
  wget -q -O /tmp/ngrok.tgz https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
  tar -xf /tmp/ngrok.tgz -C /home/jovyan/
  chmod +x "$NGROK_BIN"
  log "ngrok installed."
else
  log "ngrok already present, skipping download."
fi

# =============================================================================
# STEP 5 — Configure and start ngrok
# =============================================================================

pkill -f ngrok 2>/dev/null && log "Stopped existing ngrok process." || true

log "Configuring ngrok authtoken..."
"$NGROK_BIN" config add-authtoken "$NGROK_AUTHTOKEN" > /dev/null

log "Starting ngrok tunnel on port $VLLM_PORT with basic auth..."
nohup "$NGROK_BIN" http "$VLLM_PORT" \
  --basic-auth "$BASIC_AUTH_USER:$BASIC_AUTH_PASS" \
  > "$NGROK_LOG" 2>&1 &

NGROK_PID=$!
log "ngrok PID: $NGROK_PID"

# Wait for ngrok to register the tunnel
sleep 5
for i in $(seq 1 12); do
  PUBLIC_URL=$(wget -q -O- http://localhost:4040/api/tunnels 2>/dev/null \
    | python -c "import sys,json; d=json.load(sys.stdin); print(d['tunnels'][0]['public_url'])" 2>/dev/null || true)
  if [ -n "$PUBLIC_URL" ]; then
    break
  fi
  sleep 3
done

if [ -z "$PUBLIC_URL" ]; then
  log "ERROR: Could not retrieve ngrok public URL. Check $NGROK_LOG."
  exit 1
fi

# =============================================================================
# DONE
# =============================================================================

echo ""
echo "============================================================"
echo "  LLM stack is running"
echo "============================================================"
echo "  Public URL:    $PUBLIC_URL"
echo "  Username:      $BASIC_AUTH_USER"
echo "  Password:      $BASIC_AUTH_PASS"
echo ""
echo "  Test with:"
echo "    wget -q -O- \\"
echo "      --user='$BASIC_AUTH_USER' --password='$BASIC_AUTH_PASS' \\"
echo "      '$PUBLIC_URL/v1/models'"
echo ""
echo "  Or pass credentials in the URL:"
echo "    $( echo $PUBLIC_URL | sed "s|https://|https://$BASIC_AUTH_USER:$BASIC_AUTH_PASS@|" )/v1/models"
echo ""
echo "  Chat completion:"
echo "    POST $PUBLIC_URL/v1/chat/completions"
echo "    Headers: Authorization: Basic <base64($BASIC_AUTH_USER:$BASIC_AUTH_PASS)>"
echo "             Content-Type: application/json"
echo "    Body:    {\"model\": \"$MODEL\","
echo "              \"messages\": [{\"role\": \"user\", \"content\": \"Hello!\"}]}"
echo ""
echo "  vLLM log:  $VLLM_LOG"
echo "  ngrok log: $NGROK_LOG"
echo "  ngrok UI:  http://localhost:4040"
echo "============================================================"
