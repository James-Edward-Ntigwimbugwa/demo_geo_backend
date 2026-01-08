# Production Deployment Notes ✅

This document contains recommendations and best practices for deploying the Django REST backend that serves indoor routing using PostGIS + pgRouting.

## DB and Connection Pooling 🔧
- Use a connection pooler like **pgbouncer** in transaction pooling mode to scale many short requests.
- In Django, set `CONN_MAX_AGE` to a moderate value (e.g. 600) and rely on pgbouncer for true pooling.
- For systems with high concurrency, consider `pgbouncer` + multiple worker processes for Gunicorn/Uvicorn.
- Keep `PG_CONNECT_TIMEOUT` low (e.g. 3–5s) and use `statement_timeout` DB-level safeguards to avoid long-running queries.

## Indexes & Query Performance 📈
- Ensure spatial indexes exist on geometry columns used in queries:
  - `room_points(wkb_geometry)`
  - `nav_edges_final(wkb_geometry)`
  - `nav_edges_work_vertices_pgr(the_geom)`
- Use KNN (<->) operators for nearest-neighbor lookups which leverage GiST/GIN indexes.
- Precompute metric reprojections (already present in `nav_edges_final` / internal prep tables).

## Routing (pgRouting) ⚡
- All routing logic should run in the DB via `pgr_dijkstra` (no topology recomputation in Django).
- Keep `nav_edges_final` clean, indexed, and with a metric `cost` column in meters.

## Geometry Handling & Transfer 🌐
- Return geometry as GeoJSON (ST_AsGeoJSON) and only transfer simplified geometries where acceptable.
- For very large routes, use streaming responses or segment-by-segment pagination.

## Caching 🗄️
- Cache frequently requested routes in a `route_result` table or an external cache (Redis). Avoid re-running heavy pgr queries for identical start/end pairs.
- Invalidate cache on topology or significant data updates.

## Timeouts & Worker Configuration ⏱️
- For Gunicorn + Uvicorn workers: keep worker timeout > maximum expected query duration but bounded (e.g. 30s).
- Use a reasonable number of workers based on CPU cores and database capacity.

## Security & Input Validation 🔒
- Validate input thoroughly and avoid exposing raw SQL construction points.
- Rate-limit routing endpoints if needed.

## Monitoring & Observability 📊
- Monitor slow queries (pg_stat_statements), database connections, and pgbouncer stats.
- Log pgr_dijkstra runtimes and edge counts for performance analysis.

## Notes
- This backend intentionally uses `managed = False` models and raw SQL for routing — **do not run migrations that recreate the existing tables**.
