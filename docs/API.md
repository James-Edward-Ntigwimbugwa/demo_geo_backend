# API Summary

## Endpoints

- GET `/api/rooms/` — list rooms
  - Query parameters: `q` (search), `limit`, `offset`
  - Response: `[{id, name, location: GeoJSON}]`

- POST `/api/route/` — compute route
  - Body: `{start_room_id: int, end_room_id: int, simplify_tolerance?: float}`
  - Response: `{distance_meters, route: GeoJSON LineString}`

- GET `/api/health/` — simple health check
- GET `/api/schema/` — API schema (OpenAPI-like)
- GET `/api/route/cache/{id}` — fetch cached route from `route_result` (optional table)

## Notes
- All routing runs entirely in the database using `pgr_dijkstra` on `nav_edges_final`.
- Geometry returned is GeoJSON; `simplify_tolerance` is applied in geometry units (prefer metric CRS).
