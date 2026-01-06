# Interactive Maps API Documentation

## Overview
The Interactive Maps API provides endpoints for accessing map data, navigation nodes/edges, and pgRouting-based pathfinding capabilities.

## API Documentation Endpoints

Once the development server is running, access the API documentation at:

- **Swagger UI**: http://localhost:8000/api/docs/swagger/
- **ReDoc**: http://localhost:8000/api/docs/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/docs/schema/

## Base URL
```
http://localhost:8000/api/
```

## Map Data Endpoints

### Base Floor
- **Endpoint**: `/base_floor/`
- **Method**: GET
- **Description**: Returns base floor geometries as GeoJSON
- **Returns**: GeoJSON FeatureCollection with LineString geometries

### Corridors
- **Endpoint**: `/corridors/`
- **Method**: GET
- **Description**: Returns corridor paths as GeoJSON
- **Returns**: GeoJSON FeatureCollection with LineString geometries
- **Properties**: fid, label, type

### Room Points
- **Endpoint**: `/room_points/`
- **Method**: GET
- **Description**: Returns room point locations as GeoJSON
- **Returns**: GeoJSON FeatureCollection with Point geometries

## Navigation Nodes Endpoints

### Nav Nodes (Original - EPSG:4326)
- **Endpoint**: `/nav_nodes/`
- **Method**: GET
- **Description**: Returns navigation nodes in geographic coordinates
- **Returns**: GeoJSON FeatureCollection with Point geometries
- **Properties**: ogc_fid, fid, label, node_type

### Nav Nodes Projected (EPSG:3857)
- **Endpoint**: `/nav_nodes_proj/`
- **Method**: GET
- **Description**: Returns navigation nodes in Web Mercator projection
- **Returns**: GeoJSON FeatureCollection with Point geometries
- **Properties**: id, label, node_type

### Nav Nodes Snapped
- **Endpoint**: `/nav_nodes_snapped/`
- **Method**: GET
- **Description**: Returns snapped navigation nodes (topology-aligned)
- **Returns**: GeoJSON FeatureCollection with Point geometries
- **Properties**: id, label, node_type

## Navigation Edges Endpoints

### Nav Edges (Original - EPSG:4326)
- **Endpoint**: `/nav_edges/`
- **Method**: GET
- **Description**: Returns navigation edges in geographic coordinates
- **Returns**: GeoJSON FeatureCollection with LineString geometries
- **Properties**: ogc_fid, fid, label, from_id, to_id

### Nav Edges Projected (EPSG:3857)
- **Endpoint**: `/nav_edges_proj/`
- **Method**: GET
- **Description**: Returns navigation edges in Web Mercator projection
- **Returns**: GeoJSON FeatureCollection with LineString geometries
- **Properties**: id, label, cost

### Nav Edges Final
- **Endpoint**: `/nav_edges_final/`
- **Method**: GET
- **Description**: Returns final optimized navigation edges for routing
- **Returns**: GeoJSON FeatureCollection with LineString geometries
- **Properties**: id, label, cost

## pgRouting Endpoints

### Shortest Path (Dijkstra)
- **Endpoint**: `/route/shortest_path/`
- **Method**: GET
- **Parameters**:
  - `start` (required): Source node ID (integer)
  - `end` (required): Target node ID (integer)
- **Description**: Finds the shortest path between two nodes using Dijkstra's algorithm
- **Returns**: GeoJSON FeatureCollection with the route edges
- **Response Properties**:
  - `start_node`: Source node ID
  - `end_node`: Target node ID
  - `total_cost`: Total distance/cost of the route
  - `path_length`: Number of edges in the route
- **Example**:
  ```
  GET /api/route/shortest_path/?start=1&end=5
  ```

### A* Pathfinding
- **Endpoint**: `/route/astar/`
- **Method**: GET
- **Parameters**:
  - `start` (required): Source node ID (integer)
  - `end` (required): Target node ID (integer)
  - `factor` (optional): Cost factor (default: 1.0)
- **Description**: Finds the shortest path using A* algorithm (more efficient for large graphs)
- **Returns**: GeoJSON FeatureCollection with the route edges
- **Example**:
  ```
  GET /api/route/astar/?start=1&end=5&factor=1.0
  ```

### Route via Waypoints
- **Endpoint**: `/route/via_points/`
- **Method**: GET
- **Parameters**:
  - `nodes` (required): Comma-separated list of node IDs in order
- **Description**: Finds a route passing through multiple waypoints sequentially
- **Returns**: GeoJSON FeatureCollection with all route segments
- **Response Properties**:
  - `waypoints`: List of node IDs
  - `segments`: Number of route segments
  - `total_cost`: Total distance/cost
  - `total_edges`: Total number of edges in the complete route
- **Example**:
  ```
  GET /api/route/via_points/?nodes=1,5,10,3
  ```

### Isochrone (Reachability)
- **Endpoint**: `/route/isochrone/`
- **Method**: GET
- **Parameters**:
  - `start` (required): Source node ID (integer)
  - `distance` (optional): Maximum cost distance (default: 100)
- **Description**: Returns all edges reachable from a node within a given cost distance
- **Returns**: GeoJSON FeatureCollection with reachable edges
- **Response Properties**:
  - `start_node`: Source node ID
  - `distance`: Maximum cost distance
  - `reachable_nodes`: Number of nodes within the distance
  - `reachable_edges`: Number of edges within the distance
- **Example**:
  ```
  GET /api/route/isochrone/?start=1&distance=100
  ```

## Response Format

All endpoints return GeoJSON FeatureCollections with the following structure:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point|LineString",
        "coordinates": [...] 
      },
      "properties": {
        // Feature-specific properties
      }
    }
  ],
  "properties": {
    // Collection-level metadata (for routing endpoints)
  }
}
```

## Error Responses

### 400 Bad Request
Missing or invalid parameters
```json
{
  "error": "Missing required parameters: start and end node IDs"
}
```

### 404 Not Found
Node or route not found
```json
{
  "error": "Start node 999 not found"
}
```

### 500 Internal Server Error
Database or pgRouting error
```json
{
  "error": "pgRouting error: No path found"
}
```

## Setup Instructions

### 1. Create Virtual Environment
```bash
cd interactive_maps_backend
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Development Server
```bash
python manage.py runserver
```

### 4. Access Documentation
- Swagger UI: http://localhost:8000/api/docs/swagger/
- ReDoc: http://localhost:8000/api/docs/redoc/

## Database Requirements

- PostgreSQL with PostGIS and pgRouting extensions
- Database schema with the following tables:
  - `base_floor`
  - `corridors`
  - `room_points`
  - `nav_nodes`
  - `nav_nodes_proj`
  - `nav_nodes_snapped`
  - `nav_edges`
  - `nav_edges_proj`
  - `nav_edges_final`
  - `nav_edges_work` (with pgRouting topology: source, target columns)
  - `nav_edges_work_vertices_pgr` (pgRouting vertices table)
  - `route_result`

## Notes

- All node IDs should reference nodes from `nav_nodes_proj` or `nav_nodes_snapped`
- Routing uses the `nav_edges_work` table which has pre-established pgRouting topology
- Cost values in responses represent the distance/weight of edges
- Coordinates are returned in GeoJSON format (longitude, latitude for geographic projections)
