import json

from django.http import JsonResponse
from django.db import connection


def _rows_to_featurecollection(rows, geom_key, props_keys):
	features = []
	for row in rows:
		geom_json = row[geom_key]
		try:
			geometry = json.loads(geom_json) if geom_json else None
		except Exception:
			geometry = None

		properties = {k: row[k] for k in props_keys}

		feature = {
			"type": "Feature",
			"geometry": geometry,
			"properties": properties,
		}
		features.append(feature)

	return {"type": "FeatureCollection", "features": features}


def _execute_geojson_query(sql, params=None):
	with connection.cursor() as cursor:
		cursor.execute(sql, params or [])
		desc = [col[0] for col in cursor.description]
		rows = [dict(zip(desc, r)) for r in cursor.fetchall()]
	return rows


def path_ways_geojson(request):
	sql = """
	SELECT ogc_fid, fid, pathway_name, metres, ST_AsGeoJSON(wkb_geometry) AS geom
	FROM path_ways
	"""
	rows = _execute_geojson_query(sql)
	fc = _rows_to_featurecollection(rows, 'geom', ['ogc_fid', 'fid', 'pathway_name', 'metres'])
	return JsonResponse(fc, safe=False)


def nav_nodes_geojson(request):
	sql = """
	SELECT ogc_fid, fid, node_type, ST_AsGeoJSON(wkb_geometry) AS geom
	FROM nav_nodes
	"""
	rows = _execute_geojson_query(sql)
	fc = _rows_to_featurecollection(rows, 'geom', ['ogc_fid', 'fid', 'node_type'])
	return JsonResponse(fc, safe=False)


def base_floor_geojson(request):
	sql = """
	SELECT ogc_fid, layer, paperspace, subclasses, linetype, entityhandle, text, ST_AsGeoJSON(wkb_geometry) AS geom
	FROM base_floor
	"""
	rows = _execute_geojson_query(sql)
	props = ['ogc_fid', 'layer', 'paperspace', 'subclasses', 'linetype', 'entityhandle', 'text']
	fc = _rows_to_featurecollection(rows, 'geom', props)
	return JsonResponse(fc, safe=False)


def room_points_geojson(request):
	sql = """
	SELECT ogc_fid, layer, paperspace, subclasses, linetype, entityhandle, text, ST_AsGeoJSON(wkb_geometry) AS geom
	FROM room_points
	"""
	rows = _execute_geojson_query(sql)
	props = ['ogc_fid', 'layer', 'paperspace', 'subclasses', 'linetype', 'entityhandle', 'text']
	fc = _rows_to_featurecollection(rows, 'geom', props)
	return JsonResponse(fc, safe=False)


def route_between_nodes(request):
	"""Return a GeoJSON FeatureCollection representing the shortest path between two nav_nodes.

	Expects GET params `start` and `end` which are `ogc_fid` values from `nav_nodes`.
	Uses pgRouting `pgr_createTopology` (if needed) and `pgr_dijkstra` on `path_ways`.
	"""
	start_id = request.GET.get('start')
	end_id = request.GET.get('end')
	if not start_id or not end_id:
		return JsonResponse({'error': 'provide start and end nav_nodes ogc_fid'}, status=400)

	with connection.cursor() as cursor:
		# get WKT of start/end nav node
		cursor.execute("SELECT ST_AsText(wkb_geometry) FROM nav_nodes WHERE ogc_fid = %s", [start_id])
		r = cursor.fetchone()
		if not r or not r[0]:
			return JsonResponse({'error': 'start node not found'}, status=404)
		start_wkt = r[0]

		cursor.execute("SELECT ST_AsText(wkb_geometry) FROM nav_nodes WHERE ogc_fid = %s", [end_id])
		r = cursor.fetchone()
		if not r or not r[0]:
			return JsonResponse({'error': 'end node not found'}, status=404)
		end_wkt = r[0]

		# ensure pgRouting functions are available
		cursor.execute("SELECT proname FROM pg_proc WHERE proname IN ('pgr_createTopology','pgr_dijkstra')")
		funcs = [f[0] for f in cursor.fetchall()]
		if 'pgr_createTopology' not in funcs or 'pgr_dijkstra' not in funcs:
			return JsonResponse({'error': 'pgRouting not available on database. Install the pgrouting extension (CREATE EXTENSION pgrouting) and retry.'}, status=500)

		# ensure topology columns exist on path_ways
		cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='path_ways' AND column_name IN ('source','target')")
		cols = [c[0] for c in cursor.fetchall()]
		if 'source' not in cols or 'target' not in cols:
			# tolerance chosen small for geographic coords; adjust if needed
			cursor.execute("SELECT pgr_createTopology('path_ways', 0.00001, 'wkb_geometry', 'ogc_fid')")

		# find nearest vertex id in the edge topology for start and end points
		nearest_sql = """
		WITH verts AS (
		  SELECT source AS vid, ST_StartPoint(wkb_geometry) AS geom FROM path_ways
		  UNION ALL
		  SELECT target AS vid, ST_EndPoint(wkb_geometry) AS geom FROM path_ways
		), unique_verts AS (
		  SELECT vid, geom FROM verts GROUP BY vid, geom
		)
		SELECT vid FROM unique_verts ORDER BY geom <-> ST_GeomFromText(%s,4326) LIMIT 1
		"""
		cursor.execute(nearest_sql, [start_wkt])
		r = cursor.fetchone()
		if not r:
			return JsonResponse({'error': 'no nearest vertex for start'}, status=500)
		start_vid = r[0]

		cursor.execute(nearest_sql, [end_wkt])
		r = cursor.fetchone()
		if not r:
			return JsonResponse({'error': 'no nearest vertex for end'}, status=500)
		end_vid = r[0]

		# run pgr_dijkstra
		dj_sql = "SELECT seq, path_seq, node, edge, cost FROM pgr_dijkstra(\n+            'SELECT ogc_fid AS id, source, target, metres AS cost FROM path_ways', %s, %s, false\n+        )"
		cursor.execute(dj_sql, [start_vid, end_vid])
		dj_rows = cursor.fetchall()
		cols = [c[0] for c in cursor.description]
		dj = [dict(zip(cols, r)) for r in dj_rows]

		# collect edge ids (ogc_fid) used in path
		edge_ids = [d['edge'] for d in dj if d.get('edge') and d.get('edge') != -1]
		if not edge_ids:
			return JsonResponse({'error': 'no route found'}, status=404)

		# fetch geometries for those edges in order of path
		cursor.execute(
			"SELECT ogc_fid, ST_AsGeoJSON(wkb_geometry) AS geom, pathway_name, metres FROM path_ways WHERE ogc_fid = ANY(%s)",
			[edge_ids],
		)
		rows = [dict(zip([c[0] for c in cursor.description], r)) for r in cursor.fetchall()]

	# preserve ordering of edges according to pgr_dijkstra
	id_to_row = {r['ogc_fid']: r for r in rows}
	features = []
	for d in dj:
		eid = d.get('edge')
		if not eid or eid == -1:
			continue
		row = id_to_row.get(eid)
		if not row:
			continue
		try:
			geometry = json.loads(row['geom']) if row.get('geom') else None
		except Exception:
			geometry = None
		feat = {
			'type': 'Feature',
			'geometry': geometry,
			'properties': {
				'ogc_fid': row.get('ogc_fid'),
				'pathway_name': row.get('pathway_name'),
				'metres': row.get('metres'),
				'seq': d.get('seq'),
				'cost': d.get('cost'),
			}
		}
		features.append(feat)

	fc = {'type': 'FeatureCollection', 'features': features}
	return JsonResponse(fc, safe=False)
