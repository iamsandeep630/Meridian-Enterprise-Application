# ==============================================================================
# Dockerfile for Meridian Enterprise Application
# Production-ready container image for deployment to AWS ECS Fargate
# Includes Python 3.11 runtime and Node.js for MeshCentral CLI (meshctrl.js)
# ==============================================================================

FROM python:3.11-slim-bookworm as base

# Copy Node.js runtime from official Node image (shares exact same Debian Bookworm glibc base)
COPY --from=node:20-bookworm-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:20-bookworm-slim /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=node:20-bookworm-slim /usr/local/bin/npm /usr/local/bin/npm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    PORT=8001 \
    MESHCTRL_PATH=/app/backend/bin/meshctrl.js \
    MESHCENTRAL_URL=wss://meshcentral-nlb-57f1b2a74defca19.elb.us-east-1.amazonaws.com \
    MESHCENTRAL_USER=admin \
    MESHCENTRAL_PASS=admin-smartfix

# Set working directory
WORKDIR /app

# Install Python dependencies with CPU-optimized PyTorch
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy application backend, frontend, and configuration
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Ensure Node modules are installed if not present
RUN cd /app/backend/bin && if [ ! -d "node_modules/ws" ]; then npm install --omit=dev; fi

# Expose FastAPI port
EXPOSE 8001

# Healthcheck using native Python standard library (no external curl dependency)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

# Start FastAPI application with uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"]
