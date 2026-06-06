FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
RUN pip install --no-cache-dir uv

WORKDIR /app

COPY api/requirements.txt /tmp/requirements.txt
RUN uv pip install --system --no-cache torch --index-url https://download.pytorch.org/whl/cpu && \
    uv pip install --system --no-cache -r /tmp/requirements.txt


FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY api/ /app/api/
ENV PYTHONPATH=/app/api

CMD ["celery", "-A", "app.tasks.celery_app", "worker", "--loglevel=info"]
