# Multi-stage build for RAG Chatbot Backend
# Optimized for Hugging Face Spaces deployment

# Stage 1: Build stage
FROM python:3.13-slim as builder

WORKDIR /build

# Copy only requirements first (for better caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.13-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH \
    PYTHONPATH=/app:$PYTHONPATH

# Install system dependencies for health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code (main structure)
COPY src/ ./src/
COPY main.py .
COPY .env.example ./env.example

# Optional: Copy tests if needed for runtime validation
# COPY tests/ ./tests/

# Create non-root user for security (optional for Spaces)
# RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
# USER appuser

# Health check (using curl instead of requests)
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run FastAPI application with Uvicorn
# Using single worker for Hugging Face Spaces (free tier)
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
