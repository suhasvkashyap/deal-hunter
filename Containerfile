# Stage 1: Builder
FROM registry.access.redhat.com/ubi9/python-311:latest AS builder

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir uv && \
    uv sync --frozen --no-dev 2>/dev/null || uv sync --no-dev

# Stage 2: Runtime
FROM registry.access.redhat.com/ubi9/python-311:latest

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY mock_data/ /app/mock_data/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    USE_MOCK_DATA=true \
    LLM_PROVIDER=ollama \
    LLM_BASE_URL=http://localhost:11434/v1 \
    LLM_MODEL=granite3.2:8b \
    OUTPUT_DIR=/app/reports \
    MOCK_DATA_DIR=/app/mock_data

RUN mkdir -p /app/reports && chown -R 1001:0 /app/reports && chmod -R g=u /app/reports

VOLUME ["/app/reports"]

USER 1001

ENTRYPOINT ["python", "-m", "deal_hunter", "--non-interactive"]
