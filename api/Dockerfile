FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
RUN pip install --no-cache-dir uv

WORKDIR /app

COPY api/requirements-api.txt /tmp/requirements.txt
RUN uv pip install --system --no-cache -r /tmp/requirements.txt


FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY api/ /app/

CMD ["sh", "-c", "if [ ! -f seed_data.json ]; then python generate_seed.py; fi && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
