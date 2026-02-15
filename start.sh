#!/bin/bash
# Startup script for Hugging Face Spaces
# Starts Ollama server, pulls/warms the model, then launches Streamlit

set -e

# --- Start Ollama ---
# OLLAMA_HOST env from Dockerfile is "http://localhost:11434" (client format).
# The server needs "host:port" without the http:// prefix to bind correctly.
echo "=== Starting Ollama server ==="
OLLAMA_HOST=0.0.0.0:11434 ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready (up to 30 s)
echo "Waiting for Ollama server to start..."
for i in $(seq 1 30); do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "Ollama server is ready (PID: $OLLAMA_PID)."
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "ERROR: Ollama server failed to start after 30 seconds."
        exit 1
    fi
    sleep 1
done

# --- Pull the model if not already present ---
MODEL="${OLLAMA_MODEL:-llama3.2:3b}"
echo "=== Checking for model: $MODEL ==="
if ! ollama list 2>/dev/null | grep -q "${MODEL%%:*}"; then
    echo "Pulling model $MODEL (this may take a few minutes on first run)..."
    ollama pull "$MODEL"
    echo "Model $MODEL pulled successfully."
else
    echo "Model $MODEL already available."
fi

# --- Warm up model (pre-load into RAM so first user doesn't wait) ---
echo "=== Warming up model ==="
if curl -sf http://localhost:11434/api/chat \
    -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"stream\":false,\"options\":{\"num_predict\":1}}" \
    > /dev/null 2>&1; then
    echo "Model loaded into memory."
else
    echo "Warm-up call finished (model will load on first request)."
fi

# --- Launch Streamlit ---
echo "=== Starting Streamlit app ==="
export OLLAMA_HOST=http://localhost:11434   # switch back to client format for the app
exec streamlit run app.py \
    --server.port="${PORT:-8501}" \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
