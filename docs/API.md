# API Summary

## Endpoints

- GET `/api/rooms/` — list rooms
  - Query parameters: `q` (search), `limit`, `offset`
  - Response: `[{id, name, location: GeoJSON}]`

- POST `/api/route/` — compute route
  - Body: `{start_room_id: int, end_room_id: int, simplify_tolerance?: float}`
  - Response: `{distance_meters, route: GeoJSON LineString}`

- GET `/api/health/` — simple health check
- GET `/api/base-floor/` — list `base_floor` polylines (async streaming when `limit` is omitted)
  - Query parameters:
    - `limit` (explicit pagination; if provided, returns a normal JSON array)  
      - If omitted, endpoint streams in batches of **500** via Server-Sent Events (SSE)
    - `offset` (used only when `limit` is provided)
  - Response when `limit` provided: `[{id, layer, paperspace, text, geometry: GeoJSON LineString}]`
  - Streaming behavior when `limit` omitted (SSE): each SSE event contains a JSON payload:

      {
        "batch": 1,
        "fetched": 500,
        "more_pending": true,
        "items": [{...}, ...]
      }

  - Example: paginated request

      curl -sS 'http://localhost:8000/api/base-floor/?limit=5' | jq '.'

  - Example: streaming request (SSE — using `curl` to show raw events):

      curl -N 'http://localhost:8000/api/base-floor/'

    In browser you can use EventSource to append events incrementally:

    ```js
    const es = new EventSource('/api/base-floor/');
    es.onmessage = (ev) => {
      const payload = JSON.parse(ev.data);
      // payload.items is an array you can append to your UI
    }
    ```

- GET `/api/schema/` — API schema (OpenAPI-like)
- GET `/api/route/cache/{id}` — fetch cached route from `route_result` (optional table)

## Notes
- All routing runs entirely in the database using `pgr_dijkstra` on `nav_edges_final`.
- Geometry returned is GeoJSON; `simplify_tolerance` is applied in geometry units (prefer metric CRS).
