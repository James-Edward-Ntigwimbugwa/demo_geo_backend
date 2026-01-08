-- Example flow to compute a route entirely in the DB (adapt SRIDs as needed)

-- 1) Find nearest vertex to a room (room_id)
-- Use KNN for fast nearest neighbor lookup
SELECT v.id
FROM nav_edges_work_vertices_pgr v
JOIN room_points r ON r.ogc_fid = 123
ORDER BY v.the_geom <-> ST_Transform(r.wkb_geometry, ST_SRID(v.the_geom))
LIMIT 1;

-- 2) Run pgr_dijkstra between two vertices (start_vid, end_vid)
-- Return sequence of edges used (edge ids)
WITH route AS (
  SELECT * FROM pgr_dijkstra(
    'SELECT ogc_fid AS id, source, target, cost FROM nav_edges_final',
    10, 200, directed := false
  )
)
SELECT seq, node, edge, cost, agg_cost
FROM route;

-- 3) Assemble route geometry and total distance
SELECT
  ST_AsGeoJSON(ST_LineMerge(ST_Collect(wkb_geometry))) AS geojson,
  SUM(cost) AS distance_meters
FROM nav_edges_final
WHERE ogc_fid = ANY(ARRAY[45,46,47]::int[]);

-- Note: apply ST_Simplify if you need to reduce geometry vertex count:
-- ST_Simplify(geom, tolerance) -- tolerance in geometry units (prefer metric)
