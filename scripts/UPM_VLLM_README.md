# UPM vLLM cluster — startup runbook

The thesis open-weights baseline (RQ1) runs on the UPM JupyterHub A100 cluster:
vLLM serves an OpenAI-compatible API on port 8000, ngrok exposes it publicly
with HTTP basic auth, and the e2r-adaptation API (running locally or in
Polytope) calls into it via a `VLLMClient` (TODOS Step 21).

JupyterHub pods reset frequently and the cluster blocks Cloudflare Tunnel,
`jupyter-server-proxy`, and most other "expose a port" mechanisms — ngrok is
the only outbound path that works. Two scripts live here:

- `upm_vllm_startup.sh` — bring the stack up (provision venv if needed,
  download model weights, launch vLLM, launch ngrok, print public URL).
- `upm_vllm_shutdown.sh` — bring the stack down cleanly. Important when
  switching models, because `pkill` alone doesn't always release CUDA
  memory in time for the next vLLM start (which fails with "Free memory <
  gpu_memory_utilization"). Run shutdown → wait → run startup with new env.

## Manual steps (per pod restart)

1. Open https://138.4.144.36/jupyterhub/user/jelle.vanlieshout/lab and sign
   in. (UPM SSO; no API access.)
2. Launch a terminal inside JupyterLab.
3. Copy `scripts/upm_vllm_startup.sh` into `/home/jovyan/` (one-off; persists
   on NFS — only needed when the script changes).
4. Export the required env vars:
   ```bash
   export NGROK_AUTHTOKEN="<your ngrok authtoken>"
   export BASIC_AUTH_USER="jelle"          # or any username
   export BASIC_AUTH_PASS="<>= 8 chars>"   # ngrok requires 8+ chars

   # Optional — for gated HuggingFace repos like meta-llama/*, mistralai/*.
   # Get one at https://huggingface.co/settings/tokens (read-only is enough).
   # Skip for ungated models (Qwen2.5, casperhansen/* AWQ mirrors, etc).
   export HF_TOKEN="<hf_xxx...>"
   ```
5. Run the script:
   ```bash
   bash /home/jovyan/upm_vllm_startup.sh
   ```
6. The script prints the rotating ngrok URL on success. Copy it.
7. On the e2r-adaptation API side, set the run-time env vars before launching
   the API:
   ```bash
   VLLM_BASE_URL="https://<rotating-subdomain>.ngrok-free.dev/v1"
   VLLM_BASIC_AUTH="<base64(BASIC_AUTH_USER:BASIC_AUTH_PASS)>"
   ```
   (Polytope: add to `set-values-and-secrets`. See TODOS Step 21c.)

## Switching models (cleanly stop, then restart)

To switch from one model to another (e.g. 7B → 70B → 8B), always run the
shutdown script first so VRAM is released before the new vLLM starts:

```bash
bash /home/jovyan/upm_vllm_shutdown.sh
# Wait for "GPU is clean" — the script polls nvidia-smi until VRAM drops
# below 1 GiB or it times out at 30s.

# Then export the new MODEL/QUANTIZATION/MAX_MODEL_LEN/etc. and run startup:
export MODEL="meta-llama/Llama-3.1-8B-Instruct"
export MAX_MODEL_LEN=4096
unset QUANTIZATION
unset GPU_MEMORY_UTILIZATION
bash /home/jovyan/upm_vllm_startup.sh
```

If shutdown reports "VRAM still pinned" after 30s, the pod itself needs
restarting from the JupyterHub admin UI (server → "Stop My Server" →
"Start My Server"). Stuck CUDA contexts that survive SIGKILL can only be
cleared that way.

## Switching to a 70B model (Step 21e)

The default config serves Qwen2.5-7B for smoke testing. To switch to a 70B
target on the same A100:

1. On the JupyterHub pod, before running the startup script, export:
   ```bash
   # Llama 3.3 70B Instruct, AWQ-quantized for vLLM
   export MODEL="casperhansen/llama-3.3-70b-instruct-awq"
   export QUANTIZATION="awq"
   export MAX_MODEL_LEN=2048           # tighter context — KV cache headroom is small
   export GPU_MEMORY_UTILIZATION=0.95  # squeeze every GB
   ```
   (DeepSeek R1 70B Distill works too but is a reasoning model — may
   produce verbose outputs that hit the API-side `max_tokens=3000` cap.
   Llama 3.3 70B Instruct is the safer choice for replacement quality.)

2. Run `bash /home/jovyan/upm_vllm_startup.sh` as usual. First launch will
   download ~37 GB of weights into the NFS HF cache (one-off; subsequent
   launches reuse the cache).

3. **Local-side: drop concurrency to 1.** In `set-values-and-secrets`, set
   `pt values set vllm-concurrency 1` (the 70B weights fill the card; no
   VRAM headroom for parallel KV cache). Re-run `bash set-values-and-secrets`
   and re-spawn the API container so the new value is picked up.

4. Smoke-test against the new endpoint with a 5-example run before firing
   anything larger. A 70B-Q4 model is slower per token than the 7B baseline;
   expect ~30s per detect_then_replace example sequentially.

## Logs

```bash
tail -f /home/jovyan/vllm.log
tail -f /home/jovyan/ngrok.log
```
ngrok also exposes a local inspection UI at `http://localhost:4040` inside the
pod (not externally reachable, but useful from a Jupyter terminal).

## Known wrinkles

- **ngrok subdomain rotates on every restart** — there is no static-domain
  free tier. `VLLM_BASE_URL` must be updated after every pod restart.
- **JupyterHub pod resets kill running processes.** The venv, HF cache, and
  ngrok binary all live on NFS (`/home/jovyan/...`) and persist; the running
  vLLM and ngrok processes do not. Re-run the script after every reset.
- **40 GB A100 with MIG single-slice.** Sweet spots for the 70B target:
  Llama 3.3 70B Q4 (~40 GB) or DeepSeek R1 70B Q4 (~40 GB) — both fit just.
  Larger contexts will OOM; keep `MAX_MODEL_LEN` ≤ 4096 unless you have a
  reason to increase it.
- **Concurrency caps (`VLLM_CONCURRENCY` env var on the API side).** vLLM
  itself supports concurrent requests via continuous batching, but on the
  40 GB A100 the KV cache shares VRAM with the model weights:
  - Qwen2.5-7B (~14 GB): `VLLM_CONCURRENCY=4` is the sweet spot.
  - Llama 3.3 70B / DeepSeek R1 70B at Q4 (~40 GB): set `VLLM_CONCURRENCY=1`
    — the model weights already fill the card, no headroom for parallel
    KV cache. Set this in `set-values-and-secrets` before re-firing runs
    against the 70B endpoint.
- **Basic auth password must be ≥ 8 characters** (ngrok rejects shorter).
- **Only `wget` is available** in the pod by default — no `curl`, no
  `cloudflared`. Stick to `wget` in any helper scripts you add.

## Why this isn't fully automated

- No SSH access to the pod — the only entry point is the JupyterHub web UI.
- No admin access to configure JupyterHub extensions or ingress rules.
- Cluster outbound rules block Cloudflare Tunnel and similar tools — ngrok is
  the only outbound channel that's reliably reachable from the pod.
- ngrok authtoken and basic-auth password should not be checked in, so they
  must be exported manually each time.
