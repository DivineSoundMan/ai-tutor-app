#!/bin/bash
# Startup script for Hugging Face Spaces
# Starts Ollama server, pulls the model, then launches Streamlit

set -e

echo "=== Starting Ollama server ==="
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama server to start..."
for i in $(seq 1 30); do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "Ollama server is ready."
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "ERROR: Ollama server failed to start after 30 seconds."
        exit 1
    fi
    sleep 1
done

# Pull the model if not already present
MODEL="${OLLAMA_MODEL:-llama3.2:3b}"
echo "=== Checking for model: $MODEL ==="
if ! ollama list 2>/dev/null | grep -q "${MODEL%%:*}"; then
    echo "Pulling model $MODEL (this may take a few minutes on first run)..."
    ollama pull "$MODEL"
    echo "Model $MODEL pulled successfully."
else
    echo "Model $MODEL already available."
fi

echo "=== Starting Streamlit app ==="
exec streamlit run app.py \
    --server.port="${PORT:-8501}" \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
