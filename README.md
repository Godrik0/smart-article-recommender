# Smart Article Recommender

Сервис рекомендаций статей по смысловому сходству. Пользователь описывает, что хочет изучить, на естественном языке -- система с помощью ML-модели находит самые подходящие статьи из базы.

## Что используется

- **React + Vite** -- фронтенд, сборка статики раздаётся через nginx
- **FastAPI** -- REST API, асинхронный, Python 3.12
- **PostgreSQL 16** -- хранение статей и запросов, SQLAlchemy + Alembic для миграций
- **Redis** -- брокер задач Celery и хранилище результатов
- **Celery** -- фоновый запуск ML-модели, чтобы не блокировать API
- **sentence-transformers/all-MiniLM-L6-v2** -- модель эмбеддингов (384-мерные вектора, работает на CPU)
- **Nginx** -- обратный прокси, rate limiting, gzip
- **Prometheus + Grafana** -- мониторинг

## Как устроено

Все запросы проходят через Nginx на порту 80:

- `/` -- React UI
- `/api/*` -- проксируется в FastAPI (порт 8000)
- `/health` -- проверка состояния сервиса

ML-модель живёт только в Celery-worker. API не загружает модель -- он отправляет задачу в очередь и сразу возвращает 202. UI опрашивает результат. Готовность модели определяется по флагу `model:ready` в Redis.

Эмбеддинги всех статей предрасчитываются при первом запуске и сохраняются в файл, при последующих запусках загружаются из кеша.

Сервисы разделены на две Docker-сети: фронтенд (proxy, ui, api) и бэкенд (api, redis, postgres, worker). UI не имеет прямого доступа к Redis и PostgreSQL.

## Запуск

```bash
cp .env.example .env
docker compose up --build -d
```

После запуска доступны:

- Приложение: http://localhost
- Swagger: http://localhost/api/docs
- Health check: http://localhost/health
- Grafana: http://localhost:3000 (admin/admin)

Модель загружается асинхронно, первые несколько минут поле `model` в `/health` будет `not_ready`.

## API

### POST /api/v1/recommend

Создать запрос на рекомендацию. Возвращает 202 и ID запроса, результат нужно опрашивать.

```bash
curl -X POST "http://localhost/api/v1/recommend" \
  -H "Content-Type: application/json" \
  -d '{"query": "деплой Python в Docker", "top_k": 5}'
```

```json
{
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "task_id": "c8e9f0a1-2b3c-4d5e-6f7a-8b9c0d1e2f3a",
  "status": "pending"
}
```

Параметры тела:

- `query` (string, обязательно) -- текст запроса, 2--1200 символов
- `top_k` (integer, по умолчанию 5) -- количество рекомендаций, от 1 до 10

### GET /api/v1/recommend/{request_id}

Получить результат рекомендации по ID. Пока выполняется -- 202, когда готово -- 200.

```bash
curl "http://localhost/api/v1/recommend/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "query": "деплой Python в Docker",
  "top_k": 5,
  "status": "completed",
  "result": {
    "items": [
      {
        "id": 42,
        "title": "Deploying Python with Docker",
        "description": "A guide to containerizing Python applications.",
        "category": "DevOps",
        "tags": ["docker", "python", "deployment"],
        "url": "https://example.com/docker-python",
        "score": 0.87
      }
    ]
  },
  "error": null,
  "created_at": "2025-01-15T10:30:00Z"
}
```

### GET /api/v1/recommend

Список предыдущих запросов на рекомендацию.

```bash
curl "http://localhost/api/v1/recommend?limit=10"
```

Параметры:

- `limit` (integer, по умолчанию 20) -- максимум записей, от 1 до 100

### GET /api/v1/articles

Каталог статей с опциональной фильтрацией по категории.

```bash
curl "http://localhost/api/v1/articles"
curl "http://localhost/api/v1/articles?category=Machine%20Learning"
```

Параметры:

- `category` (string, необязательно) -- фильтр по категории

### GET /health

Проверка состояния сервиса. Возвращает статус БД, Redis и ML-модели.

```bash
curl "http://localhost/health"
```

```json
{
  "status": "ok",
  "db": "ok",
  "redis": "ok",
  "model": "ok"
}
```
