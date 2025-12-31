# Stage 1: Base image with Python 3.11 slim
FROM python:3.11-slim

# Set metadata labels
LABEL maintainer="BookRAGAgent Team"
LABEL version="1.0"
LABEL description="FastAPI backend for hallucination-free RAG chatbot"

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

   # hadolint ignore=DL3008
 
# Install system dependencies (minimal for security)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY --chown=appuser:appuser backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy entire backend application
COPY --chown=appuser:appuser backend/ .

# Switch to non-root user
USER appuser

# Expose port for Render
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:10000/ || exit 1

# Start uvicorn server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000", "--workers", "1"]
