FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Prevent Python from writing pyc files & enable logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (if needed by some Python packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend_v3 backend_v3
COPY retrieval retrieval

# Hugging Face requires port 7860
EXPOSE 7860

# Start FastAPI app
CMD ["uvicorn", "backend_v3.main:app", "--host", "0.0.0.0", "--port", "7860"]
