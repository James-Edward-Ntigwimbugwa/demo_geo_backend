# API Summary

## ASGI Requirement

**This backend REQUIRES an ASGI server** (not WSGI). The API supports Server-Sent Events (SSE) streaming which is only possible on ASGI.

### Running the Backend

#### Development (ASGI)

```bash
# Install uvicorn (async ASGI server)
pip install uvicorn

# Run with uvicorn on localhost:8000
uvicorn interactive_maps_backend_config.asgi:application --host 0.0.0.0 --port 8000

# Or with auto-reload during development:
uvicorn interactive_maps_backend_config.asgi:application --host 0.0.0.0 --port 8000 --reload
```

**Why ASGI?**
- WSGI is synchronous and cannot handle async views or async iterators.
- ASGI is async-first and natively supports streaming responses with async generators.
- Our SSE endpoints use `async def` views and `StreamingHttpResponse` with async iterators, which only work on ASGI.

#### Production (ASGI)

Use a production ASGI server like:
- **Uvicorn** (recommended for simplicity) with Gunicorn workers
- **Daphne** (Django Channels-compatible)
- **Hypercorn**

Example with Gunicorn + Uvicorn workers:

```bash
gunicorn \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8000 \
  interactive_maps_backend_config.asgi:application
```

---

## Endpoints

- GET `/api/rooms/` — list rooms
  - Query parameters:
    - `q` (search)
    - `limit` (if provided: paginated JSON response; if omitted: SSE streaming)
    - `offset` (used only when `limit` provided)
  - **Paginated response** (when `limit` provided):

    ```json
    [
      {
        "id": 1,
        "name": "Room A",
        "location": { "type": "Point", "coordinates": [...] }
      }
    ]
    ```
  - **SSE Streaming response** (when `limit` omitted):

    Each event is sent as SSE `data: {...}\n\n`:

    ```json
    {
      "batch": 1,
      "fetched": 500,
      "more_pending": true,
      "items": [
        {
          "id": 1,
          "name": "Room A",
          "location": { "type": "Point", "coordinates": [...] }
        },
        ...
      ]
    }
    ```

  - Example: paginated request

    ```bash
    curl -sS 'http://localhost:8000/api/rooms/?limit=10&offset=0' | jq '.'
    ```

  - Example: streaming request (SSE)

    ```bash
    # Using curl with -N (--no-buffer) to see events as they arrive
    curl -N 'http://localhost:8000/api/rooms/' | head -20
    ```

  - Example: JavaScript client (EventSource)

    ```javascript
    const es = new EventSource('/api/rooms/');
    const items = [];
    
    es.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      items.push(...payload.items);
      console.log(`Batch ${payload.batch}: ${payload.fetched} items, more: ${payload.more_pending}`);
      
      if (!payload.more_pending) {
        es.close();
        console.log(`Done! Total: ${items.length}`);
      }
    };
    
    es.onerror = () => es.close();
    ```

---

- POST `/api/route/` — compute route
  - Body: `{start_room_id: int, end_room_id: int, simplify_tolerance?: float}`
  - Response: `{distance_meters, route: GeoJSON LineString}`

- GET `/api/health/` — simple health check

- GET `/api/base-floor/` — list `base_floor` polylines (async, supports both modes)
  - Query parameters:
    - `limit` (if provided: paginated JSON; if omitted: SSE streaming)
    - `offset` (used only when `limit` provided)
  - **Paginated response** (when `limit` provided):

    ```json
    [
      {
        "ogc_fid": 1,
        "layer": "L1",
        "paperspace": false,
        "text": "floor A",
        "geometry": { "type": "LineString", "coordinates": [...] }
      }
    ]
    ```
  - **SSE Streaming response** (when `limit` omitted):

    Same structure as `/api/rooms/` streaming, but with `base_floor` fields.

  - Example: paginated request

    ```bash
    curl -sS 'http://localhost:8000/api/base-floor/?limit=5' | jq '.'
    ```

  - Example: streaming request

    ```bash
    curl -N 'http://localhost:8000/api/base-floor/'
    ```

- GET `/api/schema/` — API schema (OpenAPI-like)
- GET `/api/route/cache/{id}` — fetch cached route from `route_result` (optional table)

---

## Behavior Notes

### Default Batch Size
- All streaming endpoints use a default batch size of **500 rows**.
- Clients must not rely on receiving exactly 500 rows per event; use `more_pending` to determine if additional batches are available.

### Disconnect Handling
- If a client disconnects during SSE streaming, the server gracefully stops fetching additional batches.
- If a client disconnects during a paginated request, the server exits without error logging.
- No stack traces are logged for client disconnects (BrokenPipeError, ConnectionResetError) — this is expected behavior.

### Performance
- All geometry is serialized using PostGIS's `ST_AsGeoJSON` (server-side, efficient).
- No full querysets are loaded into memory; batching uses index-friendly LIMIT/OFFSET.
- Database connections are pooled; use an external connection pooler (pgbouncer) for production scaling.

### Caching & Buffering
- SSE responses have explicit headers to prevent caching:
  - `Cache-Control: no-cache, no-store, must-revalidate`
  - `X-Accel-Buffering: no` (for reverse proxies like nginx)
  - `Connection: keep-alive`

---

## Index Requirements

For large geospatial tables, ensure these indexes exist:

```sql
-- room_points
CREATE INDEX IF NOT EXISTS idx_room_points_text ON room_points(text);
CREATE INDEX IF NOT EXISTS idx_room_points_geom ON room_points USING GIST(wkb_geometry);

-- base_floor
CREATE INDEX IF NOT EXISTS idx_base_floor_geom ON base_floor USING GIST(wkb_geometry);

-- nav_edges_final
CREATE INDEX IF NOT EXISTS idx_nav_edges_final_geom ON nav_edges_final USING GIST(wkb_geometry);
```
