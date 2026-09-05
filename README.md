# Distributed Lock Service

Flask + Redis example of a distributed lock with ownership tokens and TTL.

## Features
- Redis-backed distributed lock
- Unique owner token
- TTL to prevent permanent locks
- Safe owner-only release using atomic Lua logic
- Conflict response when a resource is already locked
- Tests without requiring Redis

## Run

```bash
docker run --name day320-redis -p 6379:6379 -d redis:7-alpine
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Endpoints:
- `POST /api/lock/<resource>`
- `DELETE /api/lock/<resource>` with `Authorization: Bearer <token>`
- `GET /health`

Run tests:

```bash
pytest
```
