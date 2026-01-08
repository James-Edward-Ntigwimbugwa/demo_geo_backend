import json
import logging
from typing import List, Optional

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import connection, OperationalError
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import RoomSerializer, RouteRequestSerializer, RouteResultSerializer

logger = logging.getLogger(__name__)


def _dictfetchall(cursor):
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


class RoomsListAPIView(APIView):
    """GET /api/rooms/?q=&limit=&offset=

    Lightweight list of rooms (id, name, location GeoJSON)
    Uses raw SQL to avoid loading heavy geometry objects into Python.
    """

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        limit = min(int(request.query_params.get('limit', 100)), 1000)
        offset = int(request.query_params.get('offset', 0))

        # Build SQL; use parameterized query
        if q:
            sql = """
            SELECT ogc_fid, text, ST_AsGeoJSON(wkb_geometry) AS location
            FROM room_points
            WHERE text ILIKE %s
            ORDER BY text
            LIMIT %s OFFSET %s
            """
            params = [f"%{q}%", limit, offset]
        else:
            sql = """
            SELECT ogc_fid, text, ST_AsGeoJSON(wkb_geometry) AS location
            FROM room_points
            ORDER BY text
            LIMIT %s OFFSET %s
            """
            params = [limit, offset]

        try:
            rows = self._execute_and_fetch(sql, params)
        except OperationalError as e:
            return Response({"detail": "Database error"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Convert location JSON string to object
        for r in rows:
            r['location'] = json.loads(r['location']) if r.get('location') else None

        serializer = RoomSerializer(rows, many=True)
        return Response(serializer.data)

    def _execute_and_fetch(self, sql: str, params: Optional[List] = None):
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return _dictfetchall(cursor)


async def base_floor_view(request):
    """Async GET /api/base-floor/ - returns `base_floor` rows with GeoJSON geometry.

    Implemented as an async function-based view that Django will await.
    Returns a `JsonResponse` (safe=False) with an array of objects.
    """

    limit = min(int(request.GET.get('limit', 100)), 1000)
    offset = int(request.GET.get('offset', 0))

    sql = """
    SELECT ogc_fid, layer, paperspace, text, ST_AsGeoJSON(wkb_geometry) AS geometry
    FROM base_floor
    ORDER BY ogc_fid
    LIMIT %s OFFSET %s
    """
    params = [limit, offset]

    def _execute_and_fetch(sql_inner, params_inner=None):
        with connection.cursor() as cursor:
            cursor.execute(sql_inner, params_inner)
            return _dictfetchall(cursor)

    try:
        rows = await sync_to_async(_execute_and_fetch)(sql, params)
    except OperationalError:
        return JsonResponse({"detail": "Database error"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    for r in rows:
        r['geometry'] = json.loads(r['geometry']) if r.get('geometry') else None

    return JsonResponse(rows, safe=False)


class RouteAPIView(APIView):
    """POST /api/route/

    Body: { start_room_id, end_room_id, simplify_tolerance (optional) }

    Runs all heavy lifting in SQL using pgr_dijkstra on `nav_edges_final`. Returns
    GeoJSON LineString and total distance in meters.
    """

    def post(self, request):
        """Compute route by delegating to DB function `get_route_between_rooms`.

        The database function is expected to return a JSONB with keys:
          - start_vertex, end_vertex
          - total_cost_meters
          - route_geojson (GeoJSON object) or NULL
          - or {"error": "..."}

        Note: this function (provided by the DB) projects room geometries to metric CRS (3857) and runs routing on `nav_edges_work`.
        """
        serializer = RouteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        start_room_id = serializer.validated_data['start_room_id']
        end_room_id = serializer.validated_data['end_room_id']
        simplify_tolerance = serializer.validated_data.get('simplify_tolerance', 0.0)

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT public.get_route_between_rooms(%s, %s)", [start_room_id, end_room_id])
                row = cursor.fetchone()

            if not row or not row[0]:
                return Response({"detail": "Route function returned no data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            res = row[0]
            # psycopg may return JSON as str or already parsed python object
            if isinstance(res, str):
                res = json.loads(res)

            if isinstance(res, dict) and 'error' in res:
                return Response({"detail": res['error']}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            # Extract fields
            total_cost = res.get('total_cost_meters')
            route_geojson = res.get('route_geojson')

            if route_geojson is None:
                return Response({"detail": "No path found between the selected rooms."}, status=status.HTTP_404_NOT_FOUND)

            result = {"distance_meters": float(total_cost or 0.0), "route": route_geojson}
            result_serializer = RouteResultSerializer(result)
            return Response(result_serializer.data)

        except OperationalError:
            logger.exception("OperationalError during route computation")
            return Response({"detail": "Database error"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            logger.exception("Route computation failed")
            err_str = str(e)
            # Helpful hint when function is missing
            if 'get_route_between_rooms' in err_str or 'function get_route_between_rooms' in err_str.lower():
                hint = (
                    "Database function `get_route_between_rooms` is missing or failed. "
                    "Run the provided SQL to create it and ensure it runs successfully in psql."
                )
                details = f"{hint} Details: {err_str}"
                return Response({"detail": details}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            if getattr(settings, 'DEBUG', False):
                return Response({"detail": err_str}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({"detail": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _find_nearest_vertex(self, room_id: int) -> int:
        # Robust nearest-vertex lookup that handles missing SRID on room geometries.
        # If the room's geometry has SRID=0 (unknown), we assume it's already in the same
        # coordinate system as the vertex table and set the SRID to the target vertex SRID
        # instead of calling ST_Transform which fails for SRID=0.
        sql = """
            SELECT v.id
            FROM nav_edges_work_vertices_pgr v
            JOIN room_points r ON r.ogc_fid = %s
            ORDER BY v.the_geom <-> (
                CASE
                    WHEN ST_SRID(r.wkb_geometry) = 0 THEN ST_SetSRID(r.wkb_geometry, ST_SRID(v.the_geom))
                    WHEN ST_SRID(r.wkb_geometry) = ST_SRID(v.the_geom) THEN r.wkb_geometry
                    ELSE ST_Transform(r.wkb_geometry, ST_SRID(v.the_geom))
                END
            )
            LIMIT 1
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, [room_id])
                row = cursor.fetchone()
        except OperationalError as e:
            # Surface a more helpful message when ST_Transform fails due to unknown SRID
            if 'Input geometry has unknown (0) SRID' in str(e):
                raise ValueError(f"Room with id={room_id} has geometry with unknown SRID. "
                                 "Please set an appropriate SRID on room_points.wkb_geometry or ensure it is stored in the same CRS as nav vertices.")
            raise

        if not row:
            raise ValueError(f"Room with id={room_id} not found or no nearby vertex")
        return int(row[0])

    def _detect_nav_edges_final_schema(self):
        """Detect and cache column names for nav_edges_final table.

        Returns a dict: {id_col, source_col, target_col, cost_col, geom_col}
        Raises RuntimeError with helpful message if required columns are missing.
        """
        if hasattr(self, '_nav_edges_schema'):
            return self._nav_edges_schema

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = %s",
                ['nav_edges_final'],
            )
            cols = {row[0] for row in cursor.fetchall()}

        # Candidate names
        id_candidates = ['ogc_fid', 'gid', 'id', 'edge_id']
        source_candidates = ['source', 'start_vid', 'u', 'from_id', 'from']
        target_candidates = ['target', 'end_vid', 'v', 'to_id', 'to']
        cost_candidates = ['cost', 'length', 'distance', 'weight']
        geom_candidates = ['wkb_geometry', 'geom', 'the_geom', 'geometry']

        def pick(cands):
            for c in cands:
                if c in cols:
                    return c
            return None

        id_col = pick(id_candidates)
        source_col = pick(source_candidates)
        target_col = pick(target_candidates)
        cost_col = pick(cost_candidates)
        geom_col = pick(geom_candidates)

        missing = []
        if id_col is None:
            missing.append('id column (e.g. ogc_fid, id, gid)')
        if source_col is None or target_col is None:
            missing.append('source/target columns (e.g. source, target)')
        if cost_col is None:
            missing.append('cost column (e.g. cost, length)')
        if geom_col is None:
            missing.append('geometry column (e.g. wkb_geometry, geom)')

        if missing:
            raise RuntimeError(
                'nav_edges_final is missing required columns: ' + ', '.join(missing) +
                ". Columns found: " + ','.join(sorted(cols))
            )

        schema = {
            'id_col': id_col,
            'source_col': source_col,
            'target_col': target_col,
            'cost_col': cost_col,
            'geom_col': geom_col,
        }
        self._nav_edges_schema = schema
        logger.debug('Detected nav_edges_final schema: %s', schema)
        return schema

    def _compute_route_edges(self, start_vid: int, end_vid: int) -> List[int]:
        # Run pgr_dijkstra in DB and return ordered list of edge ids
        schema = self._detect_nav_edges_final_schema()
        inner_sql = f"SELECT {schema['id_col']} AS id, {schema['source_col']} AS source, {schema['target_col']} AS target, {schema['cost_col']} AS cost FROM nav_edges_final"

        sql = f"""
            WITH route AS (
                SELECT * FROM pgr_dijkstra(
                    '{inner_sql}',
                    %s, %s, directed := false
                )
            )
            SELECT array_remove(array_agg(edge ORDER BY seq), -1) AS edges
            FROM route
        """
        with connection.cursor() as cursor:
            cursor.execute(sql, [start_vid, end_vid])
            row = cursor.fetchone()
            if not row or not row[0]:
                return []
            return [int(e) for e in row[0]]

    def _assemble_route_geometry(self, edge_id_list: List[int], simplify_tolerance: float):
        schema = self._detect_nav_edges_final_schema()
        geom_col = schema['geom_col']
        id_col = schema['id_col']
        # Use ST_LineMerge(ST_Collect(geom)) to get a single LineString; apply ST_Simplify if requested
        # The simplify_tolerance must be in the same units as nav_edges_final geometry (prefer metric)
        sql = f"""
            SELECT
                ST_AsGeoJSON(
                    CASE WHEN %s > 0 THEN ST_Simplify(ST_LineMerge(ST_Collect({geom_col})), %s) ELSE ST_LineMerge(ST_Collect({geom_col})) END
                ) AS geojson,
                SUM({schema['cost_col']}) AS distance_meters
            FROM nav_edges_final
            WHERE {id_col} = ANY(%s::int[])
        """
        with connection.cursor() as cursor:
            cursor.execute(sql, [simplify_tolerance, simplify_tolerance, edge_id_list])
            row = cursor.fetchone()
            if not row:
                raise RuntimeError('Failed to assemble route geometry')
            return row[0], row[1]

class HealthAPIView(APIView):
    def get(self, request):
        try:
            ok = self._check_db()
        except OperationalError:
            return Response({"ok": False, "db": False}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({"ok": ok})

    def _check_db(self):
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            return bool(cursor.fetchone())


class RouteCacheAPIView(APIView):
    """Optional endpoint to fetch cached route geometry from `route_result` table by id."""

    def get(self, request, cache_id: int):
        sql = "SELECT ST_AsGeoJSON(the_geom) as geojson, distance_meters FROM route_result WHERE id = %s"
        try:
            rows = self._execute_and_fetch(sql, [cache_id])
        except OperationalError:
            return Response({"detail": "Database error"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if not rows:
            return Response({"detail": "Cache not found"}, status=status.HTTP_404_NOT_FOUND)

        item = rows[0]
        return Response({"distance_meters": float(item.get('distance_meters') or 0.0), "route": json.loads(item.get('geojson') or '{"type":"LineString","coordinates":[]}')})

    def _execute_and_fetch(self, sql: str, params: Optional[List] = None):
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return _dictfetchall(cursor)
