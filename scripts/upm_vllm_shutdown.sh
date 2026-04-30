#!/bin/bash
# =============================================================================
# upm_vllm_shutdown.sh
#
# Cleanly shut down the vLLM + ngrok stack on the UPM JupyterHub pod.
# Handy when switching models (e.g. 7B -> 70B -> 8B) since `pkill` alone
# doesn't always release CUDA memory immediately, and a stale process
# blocks the next vLLM startup with "Free memory < gpu_memory_utilization".
#
# Pairs with upm_vllm_startup.sh. Idempotent — safe to run on a pod where
# nothing is running.
# =============================================================================

set -e

log() { echo "[$(date '+%H:%M:%S')] $*"; }

# ----------------------------------------------------------------------------
# Stop ngrok
# ----------------------------------------------------------------------------

if pgrep -f "ngrok http" > /dev/null; then
  log "Stopping ngrok..."
  pkill -f "ngrok http" || true
  sleep 1
  if pgrep -f "ngrok http" > /dev/null; then
    log "ngrok still running, force-killing..."
    pkill -9 -f "ngrok http" || true
  fi
  log "ngrok stopped."
else
  log "ngrok not running."
fi

# ----------------------------------------------------------------------------
# Stop vLLM (graceful first, then SIGKILL, then verify VRAM is free)
# ----------------------------------------------------------------------------

VLLM_PATTERN="vllm.entrypoints.openai.api_server"

if pgrep -f "$VLLM_PATTERN" > /dev/null; then
  log "Stopping vLLM (SIGTERM)..."
  pkill -f "$VLLM_PATTERN" || true

  # Give it up to 15s to shut down gracefully.
  for i in $(seq 1 15); do
    if ! pgrep -f "$VLLM_PATTERN" > /dev/null; then
      log "vLLM exited gracefully."
      break
    fi
    sleep 1
  done

  # If still alive, SIGKILL.
  if pgrep -f "$VLLM_PATTERN" > /dev/null; then
    log "vLLM did not exit, force-killing..."
    pkill -9 -f "$VLLM_PATTERN" || true
    sleep 2
  fi
else
  log "vLLM not running."
fi

# ----------------------------------------------------------------------------
# Wait for CUDA memory to actually release
# ----------------------------------------------------------------------------
# nvidia-smi --query-gpu=memory.used reports MiB used by all processes on the
# device. After SIGKILL the kernel needs a moment to tear down CUDA contexts;
# poll until used memory drops below 1 GiB or we time out.

if command -v nvidia-smi > /dev/null; then
  # Sanity-check: can we actually query the GPU? On some JupyterHub pods the
  # user can launch GPU processes but lacks permission to query nvidia-smi
  # directly — it returns a string like "[Insufficient Permissions]" instead
  # of a number, which would trip the integer comparison below.
  PROBE=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1)
  if ! [[ "$PROBE" =~ ^[0-9]+$ ]]; then
    log "nvidia-smi returned non-numeric output (\"$PROBE\") — likely permission-restricted on this pod. Skipping VRAM verification."
    log "If the next startup fails with \"Free memory < gpu_memory_utilization\", give the pod 30–60s and retry — VRAM usually drains on its own once vLLM exits. If it stays stuck, restart the JupyterHub server from the admin UI."
    exit 0
  fi

  log "Waiting for VRAM to release (timeout 30s)..."
  for i in $(seq 1 30); do
    USED=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1)
    if [[ "$USED" =~ ^[0-9]+$ ]] && [ "$USED" -lt 1024 ]; then
      log "VRAM released — ${USED} MiB used. GPU is clean."
      exit 0
    fi
    sleep 1
  done
  log "WARNING: VRAM still pinned (${USED} MiB used) after 30s."
  log "Stuck CUDA contexts can sometimes only be cleared by restarting the JupyterHub pod."
  log "Inspect: nvidia-smi"
  log "If you see python PIDs there with no matching ps entry, the pod restart is the fix."
  exit 1
else
  log "nvidia-smi not available — skipping VRAM check. Stack stopped."
fi
