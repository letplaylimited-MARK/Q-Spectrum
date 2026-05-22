# Q-SpecTrum AI Superbrain — Docker Image
# Multi-stage: build (deps) → runtime (slim)
#
# Usage:
#   docker build -t qspectrum .
#   docker run -p 8765:8765 qspectrum
#
# With API auth:
#   docker run -p 8765:8765 -e QSPECTRUM_API_TOKEN=your-secret qspectrum
#
# With custom CORS:
#   docker run -p 8765:8765 -e QSPECTRUM_CORS_ORIGIN=https://yourapp.com qspectrum
#
# Environment variables:
#   QSPECTRUM_PORT          — HTTP port (default: 8765)
#   QSPECTRUM_API_TOKEN     — Bearer token for API auth (default: disabled)
#   QSPECTRUM_CORS_ORIGIN   — CORS allowed origin (default: same-origin)
#   QSPECTRUM_MAX_CONCURRENT — Max concurrent requests (default: 8)
#   QSPECTRUM_LOG_FORMAT    — "json" for structured logs (default: human-readable)
#   QSPECTRUM_MASTER_SEED   — Master key seed for Ghost Channel activation

FROM python:3.12-slim AS runtime

LABEL maintainer="Q-SpecTrum Team"
LABEL description="Q-SpecTrum AI Superbrain — Open-source AI OS kernel"
LABEL version="3.0.1"

WORKDIR /app

# Copy only what's needed (excludes tests, docs, debug artifacts)
COPY api_server.py .
COPY run.py .
COPY ghost_channel_gate.py .
COPY ghost_channel_adapter.py .
COPY file_ops.py .
COPY qspectrum_engine.py .
COPY smart_mock_llm.py .
COPY LAUNCH.html .
COPY chat.html .
COPY requirements.txt .
COPY BOOT.md .
COPY ROLE-REGISTRY.md .
COPY SYSTEM-PROMPT.md .

COPY brain_core/ brain_core/
COPY AI项目管理/ AI项目管理/

# Non-root user for security
RUN groupadd -r qspectrum && useradd -r -g qspectrum qspectrum
RUN chown -R qspectrum:qspectrum /app
USER qspectrum

# Expose port
EXPOSE 8765

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8765/api/status')" || exit 1

# Default command
CMD ["python", "api_server.py", "--host", "0.0.0.0"]
