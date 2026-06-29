# Build Stage
FROM python:3.11-slim as builder
WORKDIR /app

# Install UV
RUN pip install uv

# Install dependencies using UV
COPY pyproject.toml ./
RUN uv pip install --system -r pyproject.toml

# Production Stage
FROM python:3.11-slim
WORKDIR /app

# Non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
