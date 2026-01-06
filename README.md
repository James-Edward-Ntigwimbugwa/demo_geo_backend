# Interactive Maps Backend API

A Django REST Framework API for managing interactive maps with navigation routing capabilities using PostGIS and pgRouting.

## Features

- 🗺️ **Map Data Management**: Access base floors, corridors, and room points
- 🧭 **Navigation Nodes & Edges**: Multiple coordinate system support (EPSG:4326, EPSG:3857)
- 🛣️ **pgRouting Integration**: Advanced pathfinding algorithms
  - Dijkstra's shortest path
  - A* algorithm
  - Multi-waypoint routing
  - Isochrone/reachability analysis
- 📚 **Auto-Generated Documentation**: Swagger UI and ReDoc
- 🔒 **PostGIS Support**: Full spatial database support with geometry handling

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Server](#running-the-server)
- [API Endpoints](#api-endpoints)
  - [Map Data](#map-data-endpoints)
  - [Navigation Nodes](#navigation-nodes-endpoints)
  - [Navigation Edges](#navigation-edges-endpoints)
  - [Routing](#routing-endpoints)
- [Documentation](#api-documentation)
- [Database Setup](#database-setup)
- [Project Structure](#project-structure)

---

## Quick Start

```bash
# 1. Clone and navigate to the project
cd interactive_maps_backend

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations (if any)
python manage.py migrate

# 5. Start development server
python manage.py runserver
```

Server runs at: `http://localhost:8000`

---

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- PostGIS 3.0+
- pgRouting 3.0+
- GDAL/GEOS libraries

### Setup Steps

1. **Create Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install Python Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Configure Database** (see [Database Setup](#database-setup))

4. **Verify Installation**:
   ```bash
   python manage.py check
   ```

---

## Configuration

### Database Settings

Edit `interactive_maps_backend_config/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'interactive_maps_demo',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Environment Variables (Optional)

Create `.env` file:

```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_NAME=interactive_maps_demo
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

---

## Running the Server

### Development Server

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run development server
python manage.py runserver

# Access API at: http://localhost:8000/api/
```

### Production Server

For production, use Gunicorn:

```bash
pip install gunicorn
gunicorn interactive_maps_backend_config.wsgi:application --bind 0.0.0.0:8000
```

---

## API Endpoints

### Base URL
```
http://localhost:8000/api/
```

### Documentation
- **Swagger UI**: http://localhost:8000/api/docs/swagger/
- **ReDoc**: http://localhost:8000/api/docs/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/docs/schema/ (JSON)

---

## Map Data Endpoints

### 1. Base Floor

**Endpoint**: `GET /api/base_floor/`

**Description**: Retrieve base floor geometries (typically DWG/CAD lines)

**Response**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[lon, lat], [lon, lat]]
      },
      "properties": {
        "ogc_fid": 1,
        "layer": "0",
        "paperspace": false,
        "subclasses": "AcDbEntity",
        "linetype": "CONTINUOUS",
        "entityhandle": "12A",
        "text": "Wall"
      }
    }
  ]
}
```

**Example**:
```bash
curl http://localhost:8000/api/base_floor/
```

---

### 2. Corridors

**Endpoint**: `GET /api/corridors/`

**Description**: Retrieve corridor/pathway geometries

**Response**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[lon, lat], [lon, lat]]
      },
      "properties": {
        "ogc_fid": 1,
        "fid": 1,
        "label": "Corridor A",
        "type": "main"
      }
    }
  ]
}
```

**Example**:
```bash
curl http://localhost:8000/api/corridors/
```

---

### 3. Room Points

**Endpoint**: `GET /api/room_points/`

**Description**: Retrieve room/location point geometries

**Response**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [lon, lat]
      },
      "properties": {
        "ogc_fid": 1,
        "layer": "ROOM_POINTS",
        "text": "Room 101",
        "paperspace": false,
        "entityhandle": "15E"
      }
    }
  ]
}
```

**Example**:
```bash
curl http://localhost:8000/api/room_points/
```

---

## Navigation Nodes Endpoints

### 1. Navigation Nodes (Original - EPSG:4326)

**Endpoint**: `GET /api/nav_nodes/`

**Description**: Retrieve navigation nodes in geographic coordinates (WGS84)

**Response**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [lon, lat]
      },
      "properties": {
        "ogc_fid": 1,
        "fid": 1,
        "label": "Node-001",
        "node_type": "intersection"
      }
    }
  ]
}
```

**Example**:
```bash
curl http://localhost:8000/api/nav_nodes/
```

---

### 2. Navigation Nodes Projected (EPSG:3857)

**Endpoint**: `GET /api/nav_nodes_proj/`

**Description**: Retrieve navigation nodes in Web Mercator projection (for tile-based maps)

**Response**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [x, y]
      },
      "properties": {
        "id": 1,
        "label": "Node-001",
        "node_type": "intersection"
      }
    }
  ]
}
```

**Example**:
```bash
curl http://localhost:8000/api/nav_nodes_proj/
```

---

### 3. Navigation Nodes Snapped

**Endpoint**: `GET /api/nav_nodes_snapped/`

**Description**: Retrieve snapped navigation nodes (vertices with pgRouting topology)

**Response**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [x, y]
      },
      "properties": {
        "id": 1,
        "label": "Node-001",
        "node_type": "intersection"
      }
    }
  ]
}
```

**Example**:
```bash
curl http://localhost:8000/api/nav_nodes_snapped/
```

---

## Navigation Edges Endpoints

### 1. Navigation Edges (Original - EPSG:4326)

**Endpoint**: `GET /api/nav_edges/`

**Description**: Retrieve navigation edges in geographic coordinates

**Response**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[lon, lat], [lon, lat]]
      },
      "properties": {
        "ogc_fid": 1,
        "fid": 1,
        "label": "Edge-001",
        "from_id": 1,
        "to_id": 2
      }
    }
  ]
}
```

**Example**:
```bash
curl http://localhost:8000/api/nav_edges/
```

---

### 2. Navigation Edges Projected (EPSG:3857)

**Endpoint**: `GET /api/nav_edges_proj/`

**Description**: Retrieve navigation edges in Web Mercator projection

**Response**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[x, y], [x, y]]
      },
      "properties": {
        "id": 1,
        "label": "Edge-001",
        "cost": 15.5
      }
    }
  ]
}
```

**Example**:
```bash
curl http://localhost:8000/api/nav_edges_proj/
```

---

### 3. Navigation Edges Final

**Endpoint**: `GET /api/nav_edges_final/`

**Description**: Retrieve final optimized navigation edges used for routing

**Response**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[x, y], [x, y]]
      },
      "properties": {
        "id": 1,
        "label": "Edge-001",
        "cost": 15.5
      }
    }
  ]
}
```

**Example**:
```bash
curl http://localhost:8000/api/nav_edges_final/
```

---

## Routing Endpoints

### 1. Shortest Path (Dijkstra Algorithm)

**Endpoint**: `GET /api/route/shortest_path/`

**Description**: Find the shortest path between two nodes using Dijkstra's algorithm

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start` | integer | ✓ | Source node ID |
| `end` | integer | ✓ | Target node ID |

**Response**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[x, y], [x, y]]
      },
      "properties": {
        "id": 1,
        "label": "Edge-001",
        "edge_cost": 15.5,
        "path_sequence": 1,
        "cumulative_cost": 15.5
      }
    }
  ],
  "properties": {
    "start_node": 1,
    "end_node": 5,
    "total_cost": 45.5,
    "path_length": 3
  }
}
```

**Examples**:
```bash
# Find route from node 1 to node 5
curl http://localhost:8000/api/route/shortest_path/?start=1&end=5

# With Python requests
import requests
response = requests.get(
    'http://localhost:8000/api/route/shortest_path/',
    params={'start': 1, 'end': 5}
)
route = response.json()
```

**Error Responses**:
```bash
# Missing parameters
{"error": "Missing required parameters: start and end node IDs"}

# Node not found
{"error": "Start node 999 not found"}

# No route exists
{"error": "No path found between nodes 1 and 5"}
```

---

### 2. A* Pathfinding Algorithm

**Endpoint**: `GET /api/route/astar/`

**Description**: Find the shortest path using A* algorithm (more efficient for large graphs)

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start` | integer | ✓ | - | Source node ID |
| `end` | integer | ✓ | - | Target node ID |
| `factor` | float | ✗ | 1.0 | Cost multiplication factor |

**Response**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[x, y], [x, y]]
      },
      "properties": {
        "id": 1,
        "label": "Edge-001",
        "edge_cost": 15.5,
        "path_sequence": 1,
        "cumulative_cost": 15.5
      }
    }
  ],
  "properties": {
    "start_node": 1,
    "end_node": 5,
    "total_cost": 45.5,
    "path_length": 3,
    "algorithm": "A*"
  }
}
```

**Examples**:
```bash
# Basic A* routing
curl http://localhost:8000/api/route/astar/?start=1&end=5

# With cost factor
curl http://localhost:8000/api/route/astar/?start=1&end=5&factor=1.5
```

---

### 3. Route via Multiple Waypoints

**Endpoint**: `GET /api/route/via_points/`

**Description**: Find a route passing through multiple waypoints in sequence

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `nodes` | string | ✓ | Comma-separated node IDs (min 2) |

**Response**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[x, y], [x, y]]
      },
      "properties": {
        "id": 1,
        "label": "Edge-001",
        "edge_cost": 15.5,
        "segment": 1,
        "sequence": 1,
        "cumulative_cost": 15.5
      }
    }
  ],
  "properties": {
    "waypoints": [1, 5, 10, 3],
    "segments": 3,
    "total_cost": 120.5,
    "total_edges": 8
  }
}
```

**Examples**:
```bash
# Route through 4 waypoints: 1 -> 5 -> 10 -> 3
curl http://localhost:8000/api/route/via_points/?nodes=1,5,10,3

# With Python requests
import requests
response = requests.get(
    'http://localhost:8000/api/route/via_points/',
    params={'nodes': '1,5,10,3'}
)
route = response.json()
```

**Error Responses**:
```bash
# Invalid format
{"error": "Invalid node IDs"}

# Insufficient waypoints
{"error": "At least 2 nodes are required"}
```

---

### 4. Isochrone / Reachability Analysis

**Endpoint**: `GET /api/route/isochrone/`

**Description**: Get all nodes and edges reachable from a start node within a maximum cost distance

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start` | integer | ✓ | - | Source node ID |
| `distance` | float | ✗ | 100 | Maximum cost distance |

**Response**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[x, y], [x, y]]
      },
      "properties": {
        "id": 1,
        "label": "Edge-001",
        "cost": 15.5
      }
    }
  ],
  "properties": {
    "start_node": 1,
    "distance": 100,
    "reachable_nodes": 12,
    "reachable_edges": 8
  }
}
```

**Examples**:
```bash
# Get all edges reachable within 100 units from node 1
curl http://localhost:8000/api/route/isochrone/?start=1&distance=100

# With custom distance
curl http://localhost:8000/api/route/isochrone/?start=1&distance=50

# With Python requests
import requests
response = requests.get(
    'http://localhost:8000/api/route/isochrone/',
    params={'start': 1, 'distance': 100}
)
reachable = response.json()
print(f"Reachable nodes: {reachable['properties']['reachable_nodes']}")
```

---

## API Documentation

The API automatically generates comprehensive documentation:

### Swagger UI
- **URL**: http://localhost:8000/api/docs/swagger/
- **Features**: Interactive endpoint testing, real-time API exploration
- **Best for**: Learning the API, quick testing

### ReDoc
- **URL**: http://localhost:8000/api/docs/redoc/
- **Features**: Beautiful, searchable API documentation
- **Best for**: Reading documentation, integration guides

### OpenAPI Schema
- **URL**: http://localhost:8000/api/docs/schema/
- **Format**: JSON
- **Use case**: API clients, code generation

---

## Database Setup

### Prerequisites

Ensure PostgreSQL, PostGIS, and pgRouting are installed:

```bash
# On Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib postgis postgresql-postgis-scripts pgrouting

# On macOS (with Homebrew)
brew install postgresql postgis pgrouting
```

### Create Database and Extensions

```sql
-- Connect as superuser
sudo -u postgres psql

-- Create database
CREATE DATABASE interactive_maps_demo;

-- Connect to database
\c interactive_maps_demo

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgrouting;

-- Create roles if needed
CREATE ROLE django WITH LOGIN PASSWORD 'password';
ALTER ROLE django CREATEDB;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE interactive_maps_demo TO django;
```

### Database Schema

The application expects the following tables:

- **Map Data**:
  - `base_floor` - Floor geometries (LineString)
  - `corridors` - Corridor paths
  - `room_points` - Room/location points

- **Navigation**:
  - `nav_nodes` - Navigation nodes (original coordinates)
  - `nav_nodes_proj` - Projected navigation nodes (EPSG:3857)
  - `nav_nodes_snapped` - Snapped nodes (topology-aligned)
  - `nav_edges` - Navigation edges (original coordinates)
  - `nav_edges_proj` - Projected navigation edges
  - `nav_edges_final` - Final optimized edges for routing
  - `nav_edges_work` - Working edges with pgRouting topology
  - `nav_edges_work_vertices_pgr` - pgRouting vertices table

- **Results**:
  - `route_result` - Routing results storage

---

## Project Structure

```
interactive_maps_backend/
├── interactive_maps_backend_config/    # Project settings
│   ├── settings.py                      # Django settings
│   ├── urls.py                          # URL routing
│   ├── wsgi.py                          # WSGI application
│   └── asgi.py                          # ASGI application
├── interactive_maps_backend_main/       # Main application
│   ├── models.py                        # Database models
│   ├── views.py                         # API endpoints
│   ├── admin.py                         # Admin interface
│   └── migrations/                      # Database migrations
├── manage.py                            # Django management script
├── requirements.txt                     # Python dependencies
├── .gitignore                           # Git ignore rules
├── README.md                            # This file
├── API_DOCUMENTATION.md                 # Detailed API docs
└── db.sql                               # Database schema
```

---

## Troubleshooting

### Common Issues

**1. PostgreSQL Connection Error**
```
django.db.utils.OperationalError: could not connect to server
```
**Solution**: Verify PostgreSQL is running and credentials are correct in settings.py

**2. PostGIS Extension Not Found**
```
ProgrammingError: function st_asgeojson does not exist
```
**Solution**: Enable PostGIS extension:
```sql
CREATE EXTENSION postgis;
```

**3. pgRouting Function Not Available**
```
UndefinedFunction: function pgr_dijkstra does not exist
```
**Solution**: Enable pgRouting extension:
```sql
CREATE EXTENSION pgrouting;
```

**4. GDAL/GEOS Not Installed**
```
ImportError: GDAL/GEOS installation not found
```
**Solution**: Install geospatial libraries:
```bash
# Ubuntu/Debian
sudo apt-get install libgdal-dev libgeos-dev

# macOS
brew install gdal geos
```

---

## Development

### Running Tests

```bash
python manage.py test
```

### Creating Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Admin Interface

Access Django admin at: http://localhost:8000/admin/

---

## API Response Format

All successful responses return GeoJSON FeatureCollections:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point|LineString|Polygon",
        "coordinates": [...]
      },
      "properties": {
        // Feature-specific properties
      }
    }
  ],
  "properties": {
    // Optional collection-level metadata
  }
}
```

### Error Response Format

```json
{
  "error": "Description of the error"
}
```

**HTTP Status Codes**:
- `200 OK` - Successful request
- `400 Bad Request` - Invalid parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Performance Tips

1. **Index Database Columns**: Ensure geometry columns have spatial indices
   ```sql
   CREATE INDEX idx_nav_edges_work_geom ON nav_edges_work USING GIST(geom);
   CREATE INDEX idx_nav_nodes_proj_geom ON nav_nodes_proj USING GIST(geom);
   ```

2. **Optimize pgRouting**: Update table statistics
   ```sql
   ANALYZE nav_edges_work;
   ```

3. **Cache Responses**: Implement Redis caching for frequently requested data

4. **Pagination**: Use pagination for large datasets

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

---

## License

This project is licensed under the MIT License.

---

## Support

For issues, questions, or suggestions:

1. Check existing documentation
2. Review API documentation at `/api/docs/swagger/`
3. Check troubleshooting section above
4. Open an issue on GitHub

---

## References

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [PostGIS Documentation](https://postgis.net/documentation/)
- [pgRouting Documentation](https://pgrouting.org/)
- [drf-spectacular](https://drf-spectacular.readthedocs.io/)
- [GeoJSON Specification](https://tools.ietf.org/html/rfc7946)
