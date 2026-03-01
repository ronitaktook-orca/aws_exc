# Build for ECS Fargate (linux/amd64). Required when building on ARM (e.g. Apple Silicon).
# Build stage: install dependencies with Poetry
FROM --platform=linux/amd64 python:3.11-slim AS builder
WORKDIR /app
ENV POETRY_VERSION=1.7.1
RUN pip install poetry==${POETRY_VERSION}
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-root --no-dev

# Run stage: minimal image
FROM python:3.11-slim
WORKDIR /app
RUN useradd --create-home app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY config config
COPY api api
COPY manage.py .
USER app
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "2", "config.wsgi:application"]
