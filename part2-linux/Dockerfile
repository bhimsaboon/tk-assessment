FROM python:3.11-slim AS builder

WORKDIR /app

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --prefix=/install -r requirements.txt

COPY app.py ./

FROM python:3.11-slim AS production

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:${PATH}"

# Install only runtime essentials
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /usr/sbin/nologin appuser

# Copy installed dependencies and app code from builder
COPY --from=builder /install /usr/local
COPY --from=builder /app/app.py /app/app.py

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -fsS http://127.0.0.1:5000/health || exit 1

CMD ["python", "app.py"]

