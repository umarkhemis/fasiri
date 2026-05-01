# ============================================================
# Fasiri API – Production Dockerfile
# Multi-stage build: keeps final image lean (~180MB)
# Runs as non-root user for security
# ============================================================

# ── Stage 1: Builder ─────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python deps into a prefix
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --prefix=/install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ─────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Security: create non-root user
RUN groupadd -r fasiri && useradd -r -g fasiri -d /app -s /sbin/nologin fasiri

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY app/       ./app/
COPY sdk/       ./sdk/

# Fix ownership
RUN chown -R fasiri:fasiri /app

# Switch to non-root
USER fasiri

# Expose the API port
EXPOSE 8000

# Health check — Docker will restart the container if this fails
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8000/health', timeout=8); exit(0 if r.status_code == 200 else 1)"

# Production server: uvicorn with multiple workers
# Workers = (2 * CPU cores) + 1  — override via WORKERS env var
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS:-2} --loop uvloop --http httptools --log-level ${LOG_LEVEL:-info} --proxy-headers --forwarded-allow-ips='*'"]
