# Multi-stage build for RAG Chatbot Backend
# Optimized for Hugging Face Spaces deployment with aggressive path handling

# Stage 1: Build stage
FROM python:3.11-slim as builder

WORKDIR /build

# Copy only requirements first (for better caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Set environment variables - CRITICAL for module discovery
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/src:$PYTHONPATH \
    PATH=/root/.local/bin:$PATH

# Install system dependencies for health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code (MUST include both src and root files)
COPY src/ ./src/
COPY main.py .
COPY .env.example ./env.example

# Verify directory structure
RUN ls -la / && ls -la /app && ls -la /app/src/ || true

# Optional: Copy tests if needed for runtime validation
# COPY tests/ ./tests/

# Health check (using curl instead of requests)
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run FastAPI application with Uvicorn
# Using single worker for Hugging Face Spaces (free tier)
# Log level set to debug for troubleshooting
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--log-level", "info"]
