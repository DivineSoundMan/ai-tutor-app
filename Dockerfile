FROM python:3.11-slim

# --- System dependencies ---
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# --- Install Ollama ---
RUN curl -fsSL https://ollama.com/install.sh | sh

# --- Create non-root user (required by HF Spaces) ---
RUN useradd -m -u 1000 appuser

# --- App directory ---
WORKDIR /app

# --- Python dependencies ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Copy application files ---
COPY . .

# --- Ensure directories exist ---
RUN mkdir -p data/uploads transcripts && \
    chown -R appuser:appuser /app

# --- Pre-pull model during build for faster startup ---
# This bakes the model into the Docker image so it doesn't need
# to be downloaded on every container start.
ENV OLLAMA_MODEL=llama3.2:3b
RUN ollama serve & \
    sleep 5 && \
    ollama pull llama3.2:3b && \
    kill %1 2>/dev/null; exit 0

# --- Ensure Ollama data is accessible to appuser ---
RUN mkdir -p /home/appuser/.ollama && \
    cp -r /root/.ollama/* /home/appuser/.ollama/ 2>/dev/null || true && \
    chown -R appuser:appuser /home/appuser/.ollama

# --- Switch to non-root user ---
USER appuser

# --- Environment ---
ENV OLLAMA_HOST=http://localhost:11434
ENV HOME=/home/appuser
ENV PORT=8501

# --- Expose Streamlit port ---
EXPOSE 8501

# --- Health check ---
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# --- Start ---
CMD ["bash", "start.sh"]
