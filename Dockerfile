# ==============================================================================
# Dockerfile for Meridian Enterprise Application
# Production-ready container image for deployment to AWS ECS Fargate
# Includes Python 3.11 runtime and Node.js for MeshCentral CLI (meshctrl.js)
# ==============================================================================

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    PORT=8001 \
    MESHCTRL_PATH=/app/backend/bin/meshctrl.js \
    MESHCENTRAL_URL=wss://meshcentral-nlb-57f1b2a74defca19.elb.us-east-1.amazonaws.com \
    MESHCENTRAL_USER=admin-sd \
    MESHCENTRAL_PASS=smartfix@1

# Set working directory
WORKDIR /app

# Install system dependencies including Node.js & npm for MeshCentral runner
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application backend, frontend, and configuration
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY catalog_config.json ./backend/catalog_config.json

# Install minimal Node.js runner dependencies for meshctrl.js
RUN cd /app/backend/bin && npm install --omit=dev

# Expose FastAPI port
EXPOSE 8001

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Start FastAPI application with uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"]
