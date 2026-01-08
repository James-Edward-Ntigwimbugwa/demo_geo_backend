# Deployment Guide

## Overview

This Django REST + PostGIS backend requires **ASGI** to support streaming endpoints (Server-Sent Events). WSGI is **not compatible** with async views or async generators.

---

## Development Setup

### 1. Install Dependencies

```bash
cd interactive_maps_backend
pip install -r requirements.txt
pip install uvicorn  # ASGI server for development
```

### 2. Run Development Server

```bash
# With auto-reload (watches for file changes)
uvicorn interactive_maps_backend_config.asgi:application \
  --host 0.0.0.0 \
  --port 8000 \
  --reload
```

Visit: `http://localhost:8000/api/rooms/`

---

## Production Deployment

### Option 1: Gunicorn + Uvicorn Workers (Recommended)

Best for production: process management, graceful reloads, multiple workers.

#### Install

```bash
pip install gunicorn uvicorn[standard]
```

#### Run

```bash
gunicorn \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --worker-connections 1000 \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  interactive_maps_backend_config.asgi:application
```

**Parameters explained:**
- `--workers 4`: Start 4 worker processes (tune based on CPU cores and memory)
- `--worker-connections 1000`: Allow up to 1000 concurrent connections per worker
- `--timeout 120`: Worker timeout in seconds (useful for long-running requests)
- `--access-logfile -`, `--error-logfile -`: Log to stdout (important for containerized deployments)

### Option 2: Uvicorn Only (Simple)

Suitable for smaller deployments or development.

```bash
uvicorn \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  interactive_maps_backend_config.asgi:application
```

### Option 3: Docker Compose

```yaml
version: '3.9'

services:
  backend:
    build: .
    command: >
      gunicorn
      --worker-class uvicorn.workers.UvicornWorker
      --workers 4
      --bind 0.0.0.0:8000
      interactive_maps_backend_config.asgi:application
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
      - POSTGRES_HOST=postgres
      - POSTGRES_DB=interactive_maps_demo
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=your-secure-password
    depends_on:
      - postgres
    volumes:
      - ./logs:/app/logs

  postgres:
    image: postgis/postgis:latest
    environment:
      - POSTGRES_DB=interactive_maps_demo
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=your-secure-password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gdal-bin \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn uvicorn[standard]

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--worker-class", "uvicorn.workers.UvicornWorker", "--workers", "4", "--bind", "0.0.0.0:8000", "interactive_maps_backend_config.asgi:application"]
```

---

## Reverse Proxy Setup (nginx)

### nginx Configuration

```nginx
upstream django_app {
    # Gunicorn/Uvicorn backend
    server backend:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    client_max_body_size 100M;

    # Disable buffering for SSE responses
    proxy_buffering off;
    proxy_cache off;

    location / {
        proxy_pass http://django_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Important for SSE: disable proxying chunked encoding
        proxy_http_version 1.1;
        proxy_set_header Connection "";

        # Timeout for long-running streams
        proxy_read_timeout 3600s;
        proxy_connect_timeout 60s;
    }

    location /api/rooms/ {
        # Additional config for SSE endpoint
        proxy_pass http://django_app;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_read_timeout 3600s;
    }

    location /api/base-floor/ {
        # Additional config for SSE endpoint
        proxy_pass http://django_app;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_read_timeout 3600s;
    }
}
```

**Key nginx settings for SSE:**
- `proxy_buffering off`: Do NOT buffer SSE events
- `proxy_cache off`: Do NOT cache SSE responses
- `proxy_http_version 1.1`: Use HTTP/1.1 for streaming
- `proxy_set_header Connection ""`: Remove Connection header to allow pipelining
- `proxy_read_timeout 3600s`: Long timeout for streaming

---

## Database Configuration

### Connection Pooling (Production Essential)

Use **PgBouncer** or similar for connection pooling:

```ini
; pgbouncer.ini
[databases]
interactive_maps_demo = host=postgres port=5432 dbname=interactive_maps_demo user=postgres password=your-password

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 10
```

Update Django settings to connect via PgBouncer:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'HOST': 'pgbouncer-host',  # PgBouncer instead of direct DB
        'PORT': 6432,              # PgBouncer default port
        'NAME': 'interactive_maps_demo',
        'USER': 'postgres',
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'CONN_MAX_AGE': 0,         # Let PgBouncer manage pooling
    }
}
```

### Index Optimization

Ensure these indexes exist in PostgreSQL:

```sql
-- room_points
CREATE INDEX IF NOT EXISTS idx_room_points_text ON room_points(text);
CREATE INDEX IF NOT EXISTS idx_room_points_geom ON room_points USING GIST(wkb_geometry);

-- base_floor
CREATE INDEX IF NOT EXISTS idx_base_floor_geom ON base_floor USING GIST(wkb_geometry);

-- nav_edges_final
CREATE INDEX IF NOT EXISTS idx_nav_edges_final_geom ON nav_edges_final USING GIST(wkb_geometry);
```

---

## Environment Variables

Set these in `.env` or in your deployment platform (e.g., Docker, Kubernetes):

```bash
# Django
DEBUG=False
SECRET_KEY=your-secret-key-change-in-production
ALLOWED_HOSTS=your-domain.com,api.your-domain.com

# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=interactive_maps_demo
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password

# Connection pooling
CONN_MAX_AGE=600
PG_CONNECT_TIMEOUT=5
PG_OPTIONS=-c statement_timeout=5000
```

---

## Health Checks & Monitoring

### Health Check Endpoint

```bash
curl -sS http://localhost:8000/api/health/
# Response: {"ok": true}
```

Use this for load balancer health checks (Kubernetes, ALB, etc.).

### Logging

Configure structured logging in production:

```python
# In settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
```

### Metrics

Monitor key metrics:
- **Response time**: SSE events should stream within 500ms per batch
- **Database connections**: Watch for connection pool saturation
- **Worker CPU/Memory**: Ensure workers aren't OOMing
- **Network latency**: High latency can delay SSE events

---

## Scaling Considerations

### Horizontal Scaling

1. **Multiple Gunicorn workers** (on same machine): Scale to CPU count
2. **Multiple containers/machines**: Use load balancer (ALB, nginx, etc.)
3. **Database scaling**: Use read replicas for non-mutation queries (all our endpoints are read-only)

### Vertical Scaling

- Increase `--workers` in Gunicorn
- Increase `--worker-connections` to handle more concurrent SSE clients
- Allocate more memory to the application container

### Connection Pooling

- Always use PgBouncer or Pgpool2 in production
- Set `pool_mode = transaction` for web applications
- Monitor pool saturation: `SELECT count(*) FROM pgbouncer.pools;`

---

## Troubleshooting

### "Broken pipe" or "Client disconnected" Errors

**Expected behavior**: Clients can cancel requests or close browser tabs. The backend logs these gracefully and continues.

- **Not an error**: These are normal client disconnects
- **No action needed**: Backend handles these in `RoomsListAPIView` and `base_floor_view` with try/except

### SSE Not Streaming (Events not arriving)

**Possible causes:**
1. Running on WSGI (e.g., `python manage.py runserver`): Use ASGI (`uvicorn`) instead
2. nginx buffering enabled: Add `proxy_buffering off`
3. HTTP/1.0 client: Update to HTTP/1.1 or HTTP/2

### Slow SSE Streams

**Check:**
1. Database query speed: `EXPLAIN ANALYZE SELECT ... FROM base_floor LIMIT 500 OFFSET 0`
2. Network latency: Measure RTT from client to server
3. Worker saturation: Check CPU/memory usage of Gunicorn workers
4. Connection pool: Ensure PgBouncer isn't saturated

---

## Security

- **Set `DEBUG = False`** in production
- **Set secure `SECRET_KEY`** (use Django's `get_random_secret_key()`)
- **Configure `ALLOWED_HOSTS`** explicitly
- **Use HTTPS** (always; consider HSTS headers)
- **Rate limit** public endpoints if needed
- **Validate input**: All SQL is parameterized; no SQL injection risk

---

## Backup & Recovery

Backup your PostGIS database regularly:

```bash
pg_dump -U postgres -h postgres interactive_maps_demo > backup.sql
```

Restore:

```bash
psql -U postgres -h postgres interactive_maps_demo < backup.sql
```

---

## Further Reading

- [Django Deployment Documentation](https://docs.djangoproject.com/en/6.0/howto/deployment/)
- [Uvicorn Server](https://www.uvicorn.org/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [PostGIS Documentation](https://postgis.net/documentation/)
