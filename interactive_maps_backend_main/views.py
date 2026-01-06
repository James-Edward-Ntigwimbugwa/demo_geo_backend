import json
from django.http import JsonResponse
from django.db import connection


def _rows_to_featurecollection(rows, geom_key, props_keys):
	"""Convert database rows to GeoJSON FeatureCollection."""
	features = []
	for row in rows:
		geom_json = row.get(geom_key)
		try:
			geometry = json.loads(geom_json) if geom_json else None
		except Exception:
			geometry = None

		properties = {k: row.get(k) for k in props_keys if k in row}

		feature = {
			"type": "Feature",
			"geometry": geometry,
			"properties": properties,
		}
		features.append(feature)

	return {"type": "FeatureCollection", "features": features}


def _execute_geojson_query(sql, params=None):
	"""Execute a SQL query and return results as list of dicts."""
	with connection.cursor() as cursor:
		cursor.execute(sql, params or [])
		desc = [col[0] for col in cursor.description]
		rows = [dict(zip(desc, r)) for r in cursor.fetchall()]
	return rows


def base_floor_geojson(request):
	"""Get base floor geometries as GeoJSON."""
	sql = """
	SELECT ogc_fid, layer, paperspace, subclasses, linetype, entityhandle, text, ST_AsGeoJSON(wkb_geometry) AS geom
	FROM base_floor
	"""
	rows = _execute_geojson_query(sql)
	props = ['ogc_fid', 'layer', 'paperspace', 'subclasses', 'linetype', 'entityhandle', 'text']
	fc = _rows_to_featurecollection(rows, 'geom', props)
	return JsonResponse(fc, safe=False)


def corridors_geojson(request):
	"""Get corridors as GeoJSON."""
	sql = """
	SELECT ogc_fid, fid, label, type, ST_AsGeoJSON(wkb_geometry) AS geom
	FROM corridors
	"""
	rows = _execute_geojson_query(sql)
	fc = _rows_to_featurecollection(rows, 'geom', ['ogc_fid', 'fid', 'label', 'type'])
	return JsonResponse(fc, safe=False)


def room_points_geojson(request):
	"""Get room points as GeoJSON."""
	sql = """
	SELECT ogc_fid, layer, paperspace, subclasses, linetype, entityhandle, text, ST_AsGeoJSON(wkb_geometry) AS geom
	FROM room_points
	"""
	rows = _execute_geojson_query(sql)
	props = ['ogc_fid', 'layer', 'paperspace', 'subclasses', 'linetype', 'entityhandle', 'text']
	fc = _rows_to_featurecollection(rows, 'geom', props)
	return JsonResponse(fc, safe=False)


def nav_nodes_geojson(request):
	"""Get navigation nodes (original) as GeoJSON."""
	sql = """
	SELECT ogc_fid, fid, label, node_type, ST_AsGeoJSON(wkb_geometry) AS geom
	FROM nav_nodes
	"""
	rows = _execute_geojson_query(sql)
	fc = _rows_to_featurecollection(rows, 'geom', ['ogc_fid', 'fid', 'label', 'node_type'])
	return JsonResponse(fc, safe=False)


def nav_nodes_proj_geojson(request):
	"""Get projected navigation nodes as GeoJSON (EPSG:3857)."""
	sql = """
	SELECT id, label, node_type, ST_AsGeoJSON(geom) AS geom
	FROM nav_nodes_proj
	"""
	rows = _execute_geojson_query(sql)
	fc = _rows_to_featurecollection(rows, 'geom', ['id', 'label', 'node_type'])
	return JsonResponse(fc, safe=False)


def nav_nodes_snapped_geojson(request):
	"""Get snapped navigation nodes as GeoJSON."""
	sql = """
	SELECT id, label, node_type, ST_AsGeoJSON(geom) AS geom
	FROM nav_nodes_snapped
	"""
	rows = _execute_geojson_query(sql)
	fc = _rows_to_featurecollection(rows, 'geom', ['id', 'label', 'node_type'])
	return JsonResponse(fc, safe=False)


def nav_edges_geojson(request):
	"""Get navigation edges (original) as GeoJSON."""
	sql = """
	SELECT ogc_fid, fid, label, from_id, to_id, ST_AsGeoJSON(wkb_geometry) AS geom
	FROM nav_edges
	"""
	rows = _execute_geojson_query(sql)
	fc = _rows_to_featurecollection(rows, 'geom', ['ogc_fid', 'fid', 'label', 'from_id', 'to_id'])
	return JsonResponse(fc, safe=False)


def nav_edges_proj_geojson(request):
	"""Get projected navigation edges as GeoJSON (EPSG:3857)."""
	sql = """
	SELECT id, label, cost, ST_AsGeoJSON(geom) AS geom
	FROM nav_edges_proj
	"""
	rows = _execute_geojson_query(sql)
	fc = _rows_to_featurecollection(rows, 'geom', ['id', 'label', 'cost'])
	return JsonResponse(fc, safe=False)


def nav_edges_final_geojson(request):
	"""Get final navigation edges as GeoJSON."""
	sql = """
	SELECT id, label, cost, ST_AsGeoJSON(geom) AS geom
	FROM nav_edges_final
	"""
	rows = _execute_geojson_query(sql)
	fc = _rows_to_featurecollection(rows, 'geom', ['id', 'label', 'cost'])
	return JsonResponse(fc, safe=False)


def route_shortest_path(request):
	"""
	Find shortest path between two nodes using pgr_dijkstra.
	
	GET Parameters:
		- start: source node id from nav_nodes_snapped or nav_nodes_proj
		- end: target node id from nav_nodes_snapped or nav_nodes_proj
	
	Returns GeoJSON FeatureCollection with the shortest path route.
	"""
	start_id = request.GET.get('start')
	end_id = request.GET.get('end')
	
	if not start_id or not end_id:
		return JsonResponse({
			'error': 'Missing required parameters: start and end node IDs'
		}, status=400)
	
	try:
		start_id = int(start_id)
		end_id = int(end_id)
	except (ValueError, TypeError):
		return JsonResponse({
			'error': 'start and end parameters must be valid integers'
		}, status=400)
	
	with connection.cursor() as cursor:
		# Verify that the nodes exist
		cursor.execute("SELECT id FROM nav_nodes_proj WHERE id = %s", [start_id])
		if not cursor.fetchone():
			return JsonResponse({
				'error': f'Start node {start_id} not found'
			}, status=404)
		
		cursor.execute("SELECT id FROM nav_nodes_proj WHERE id = %s", [end_id])
		if not cursor.fetchone():
			return JsonResponse({
				'error': f'End node {end_id} not found'
			}, status=404)
		
		# Run pgr_dijkstra using nav_edges_work (topology prepared)
		try:
			dijkstra_sql = """
			SELECT seq, path_seq, node, edge, cost
			FROM pgr_dijkstra(
				'SELECT id, source, target, cost FROM nav_edges_work',
				%s, %s, false
			) AS t(seq, path_seq, node, edge, cost)
			"""
			cursor.execute(dijkstra_sql, [start_id, end_id])
			path_results = cursor.fetchall()
			
			if not path_results:
				return JsonResponse({
					'error': f'No path found between nodes {start_id} and {end_id}'
				}, status=404)
			
			# Extract edge IDs from path results
			edge_ids = [row[3] for row in path_results if row[3] and row[3] != -1]
			
			if not edge_ids:
				return JsonResponse({
					'error': 'Path found but no edges in route'
				}, status=404)
			
			# Get the geometry and cost information for edges in order
			edges_sql = """
			SELECT id, label, cost, ST_AsGeoJSON(geom) AS geom
			FROM nav_edges_final
			WHERE id = ANY(%s)
			ORDER BY id
			"""
			cursor.execute(edges_sql, [edge_ids])
			edge_desc = [col[0] for col in cursor.description]
			edge_rows = [dict(zip(edge_desc, row)) for row in cursor.fetchall()]
			
		except Exception as e:
			return JsonResponse({
				'error': f'pgRouting error: {str(e)}'
			}, status=500)
	
	# Build ordered feature collection following the path sequence
	id_to_edge = {row['id']: row for row in edge_rows}
	features = []
	total_cost = 0
	
	for path_row in path_results:
		seq, path_seq, node, edge, cost = path_row
		if edge == -1 or edge not in id_to_edge:
			continue
		
		edge_data = id_to_edge[edge]
		try:
			geometry = json.loads(edge_data['geom']) if edge_data.get('geom') else None
		except Exception:
			geometry = None
		
		total_cost += cost if cost else 0
		
		feature = {
			'type': 'Feature',
			'geometry': geometry,
			'properties': {
				'id': edge_data['id'],
				'label': edge_data.get('label'),
				'edge_cost': edge_data.get('cost'),
				'path_sequence': seq,
				'cumulative_cost': total_cost,
			}
		}
		features.append(feature)
	
	fc = {
		'type': 'FeatureCollection',
		'features': features,
		'properties': {
			'start_node': start_id,
			'end_node': end_id,
			'total_cost': total_cost,
			'path_length': len(features),
		}
	}
	
	return JsonResponse(fc, safe=False)


def route_astar_path(request):
	"""
	Find shortest path between two nodes using pgr_astar algorithm.
	Requires heuristic and more efficient than Dijkstra for large graphs.
	
	GET Parameters:
		- start: source node id from nav_nodes_snapped or nav_nodes_proj
		- end: target node id from nav_nodes_snapped or nav_nodes_proj
		- factor: cost factor (default: 1.0)
	
	Returns GeoJSON FeatureCollection with the shortest path route.
	"""
	start_id = request.GET.get('start')
	end_id = request.GET.get('end')
	factor = request.GET.get('factor', 1.0)
	
	if not start_id or not end_id:
		return JsonResponse({
			'error': 'Missing required parameters: start and end node IDs'
		}, status=400)
	
	try:
		start_id = int(start_id)
		end_id = int(end_id)
		factor = float(factor)
	except (ValueError, TypeError):
		return JsonResponse({
			'error': 'Invalid parameter types'
		}, status=400)
	
	with connection.cursor() as cursor:
		# Verify nodes exist
		cursor.execute("SELECT id FROM nav_nodes_proj WHERE id = %s", [start_id])
		if not cursor.fetchone():
			return JsonResponse({
				'error': f'Start node {start_id} not found'
			}, status=404)
		
		cursor.execute("SELECT id FROM nav_nodes_proj WHERE id = %s", [end_id])
		if not cursor.fetchone():
			return JsonResponse({
				'error': f'End node {end_id} not found'
			}, status=404)
		
		try:
			# pgr_astar with geometry heuristic
			astar_sql = """
			SELECT seq, path_seq, node, edge, cost
			FROM pgr_astar(
				'SELECT id, source, target, cost, x1, y1, x2, y2 
				 FROM (SELECT nf.id, nf.source, nf.target, nf.cost,
				       ST_X(ST_StartPoint(nf.geom)) as x1, ST_Y(ST_StartPoint(nf.geom)) as y1,
				       ST_X(ST_EndPoint(nf.geom)) as x2, ST_Y(ST_EndPoint(nf.geom)) as y2
				 FROM nav_edges_work nf) sub',
				%s, %s, factor => %s, directed => false
			) AS t(seq, path_seq, node, edge, cost)
			"""
			cursor.execute(astar_sql, [start_id, end_id, factor])
			path_results = cursor.fetchall()
			
			if not path_results:
				return JsonResponse({
					'error': f'No path found between nodes {start_id} and {end_id}'
				}, status=404)
			
			edge_ids = [row[3] for row in path_results if row[3] and row[3] != -1]
			
			if not edge_ids:
				return JsonResponse({
					'error': 'Path found but no edges in route'
				}, status=404)
			
			edges_sql = """
			SELECT id, label, cost, ST_AsGeoJSON(geom) AS geom
			FROM nav_edges_final
			WHERE id = ANY(%s)
			"""
			cursor.execute(edges_sql, [edge_ids])
			edge_desc = [col[0] for col in cursor.description]
			edge_rows = [dict(zip(edge_desc, row)) for row in cursor.fetchall()]
			
		except Exception as e:
			return JsonResponse({
				'error': f'pgRouting A* error: {str(e)}'
			}, status=500)
	
	id_to_edge = {row['id']: row for row in edge_rows}
	features = []
	total_cost = 0
	
	for path_row in path_results:
		seq, path_seq, node, edge, cost = path_row
		if edge == -1 or edge not in id_to_edge:
			continue
		
		edge_data = id_to_edge[edge]
		try:
			geometry = json.loads(edge_data['geom']) if edge_data.get('geom') else None
		except Exception:
			geometry = None
		
		total_cost += cost if cost else 0
		
		feature = {
			'type': 'Feature',
			'geometry': geometry,
			'properties': {
				'id': edge_data['id'],
				'label': edge_data.get('label'),
				'edge_cost': edge_data.get('cost'),
				'path_sequence': seq,
				'cumulative_cost': total_cost,
			}
		}
		features.append(feature)
	
	fc = {
		'type': 'FeatureCollection',
		'features': features,
		'properties': {
			'start_node': start_id,
			'end_node': end_id,
			'total_cost': total_cost,
			'path_length': len(features),
			'algorithm': 'A*',
		}
	}
	
	return JsonResponse(fc, safe=False)


def route_via_points(request):
	"""
	Find route passing through multiple waypoints using pgr_dijkstra in sequence.
	
	GET Parameters:
		- nodes: comma-separated list of node IDs in order
	
	Returns GeoJSON FeatureCollection with the complete route through all waypoints.
	"""
	nodes_param = request.GET.get('nodes')
	
	if not nodes_param:
		return JsonResponse({
			'error': 'Missing required parameter: nodes (comma-separated list)'
		}, status=400)
	
	try:
		nodes = [int(n.strip()) for n in nodes_param.split(',')]
		if len(nodes) < 2:
			return JsonResponse({
				'error': 'At least 2 nodes are required'
			}, status=400)
	except (ValueError, TypeError):
		return JsonResponse({
			'error': 'Invalid node IDs'
		}, status=400)
	
	with connection.cursor() as cursor:
		# Verify all nodes exist
		for nid in nodes:
			cursor.execute("SELECT id FROM nav_nodes_proj WHERE id = %s", [nid])
			if not cursor.fetchone():
				return JsonResponse({
					'error': f'Node {nid} not found'
				}, status=404)
		
		# Calculate routes between consecutive nodes
		all_features = []
		total_cost = 0
		feature_sequence = 0
		
		for i in range(len(nodes) - 1):
			start_node = nodes[i]
			end_node = nodes[i + 1]
			
			try:
				dijkstra_sql = """
				SELECT seq, path_seq, node, edge, cost
				FROM pgr_dijkstra(
					'SELECT id, source, target, cost FROM nav_edges_work',
					%s, %s, false
				) AS t(seq, path_seq, node, edge, cost)
				"""
				cursor.execute(dijkstra_sql, [start_node, end_node])
				path_results = cursor.fetchall()
				
				if not path_results:
					continue
				
				edge_ids = [row[3] for row in path_results if row[3] and row[3] != -1]
				
				if edge_ids:
					edges_sql = """
					SELECT id, label, cost, ST_AsGeoJSON(geom) AS geom
					FROM nav_edges_final
					WHERE id = ANY(%s)
					"""
					cursor.execute(edges_sql, [edge_ids])
					edge_desc = [col[0] for col in cursor.description]
					edge_rows = [dict(zip(edge_desc, row)) for row in cursor.fetchall()]
					
					id_to_edge = {row['id']: row for row in edge_rows}
					
					for path_row in path_results:
						seq, path_seq, node, edge, cost = path_row
						if edge == -1 or edge not in id_to_edge:
							continue
						
						edge_data = id_to_edge[edge]
						try:
							geometry = json.loads(edge_data['geom']) if edge_data.get('geom') else None
						except Exception:
							geometry = None
						
						total_cost += cost if cost else 0
						feature_sequence += 1
						
						feature = {
							'type': 'Feature',
							'geometry': geometry,
							'properties': {
								'id': edge_data['id'],
								'label': edge_data.get('label'),
								'edge_cost': edge_data.get('cost'),
								'segment': i + 1,
								'sequence': feature_sequence,
								'cumulative_cost': total_cost,
							}
						}
						all_features.append(feature)
			
			except Exception as e:
				return JsonResponse({
					'error': f'pgRouting error in segment {i + 1}: {str(e)}'
				}, status=500)
	
	if not all_features:
		return JsonResponse({
			'error': 'No route found through the specified waypoints'
		}, status=404)
	
	fc = {
		'type': 'FeatureCollection',
		'features': all_features,
		'properties': {
			'waypoints': nodes,
			'segments': len(nodes) - 1,
			'total_cost': total_cost,
			'total_edges': len(all_features),
		}
	}
	
	return JsonResponse(fc, safe=False)


def route_isochrone(request):
	"""
	Get all nodes and edges reachable within a cost distance from a start node.
	
	GET Parameters:
		- start: source node id
		- distance: maximum cost distance (default: 100)
	
	Returns GeoJSON FeatureCollection with reachable edges.
	"""
	start_id = request.GET.get('start')
	distance = request.GET.get('distance', 100)
	
	if not start_id:
		return JsonResponse({
			'error': 'Missing required parameter: start node ID'
		}, status=400)
	
	try:
		start_id = int(start_id)
		distance = float(distance)
	except (ValueError, TypeError):
		return JsonResponse({
			'error': 'Invalid parameter types'
		}, status=400)
	
	with connection.cursor() as cursor:
		cursor.execute("SELECT id FROM nav_nodes_proj WHERE id = %s", [start_id])
		if not cursor.fetchone():
			return JsonResponse({
				'error': f'Start node {start_id} not found'
			}, status=404)
		
		try:
			# Use pgr_dijkstraCost to find all reachable nodes
			cost_sql = """
			SELECT node, cost
			FROM pgr_dijkstraCost(
				'SELECT id, source, target, cost FROM nav_edges_work',
				%s, (SELECT array_agg(id) FROM nav_nodes_proj), false
			) AS t(start_vid, node, cost)
			WHERE cost <= %s
			"""
			cursor.execute(cost_sql, [start_id, distance])
			cost_results = cursor.fetchall()
			
			if not cost_results:
				return JsonResponse({
					'type': 'FeatureCollection',
					'features': [],
					'properties': {
						'start_node': start_id,
						'distance': distance,
						'reachable_nodes': 0,
					}
				}, safe=False)
			
			reachable_nodes = [row[0] for row in cost_results]
			
			# Get all edges that connect these nodes
			edges_sql = """
			SELECT DISTINCT nf.id, nf.label, nf.cost, ST_AsGeoJSON(nf.geom) AS geom
			FROM nav_edges_final nf
			JOIN nav_edges_work nw ON nf.id = nw.id
			WHERE nw.source = ANY(%s) OR nw.target = ANY(%s)
			"""
			cursor.execute(edges_sql, [reachable_nodes, reachable_nodes])
			edge_desc = [col[0] for col in cursor.description]
			edge_rows = [dict(zip(edge_desc, row)) for row in cursor.fetchall()]
			
		except Exception as e:
			return JsonResponse({
				'error': f'pgRouting error: {str(e)}'
			}, status=500)
	
	features = []
	for edge in edge_rows:
		try:
			geometry = json.loads(edge['geom']) if edge.get('geom') else None
		except Exception:
			geometry = None
		
		feature = {
			'type': 'Feature',
			'geometry': geometry,
			'properties': {
				'id': edge['id'],
				'label': edge.get('label'),
				'cost': edge.get('cost'),
			}
		}
		features.append(feature)
	
	fc = {
		'type': 'FeatureCollection',
		'features': features,
		'properties': {
			'start_node': start_id,
			'distance': distance,
			'reachable_nodes': len(reachable_nodes),
			'reachable_edges': len(features),
		}
	}
	
	return JsonResponse(fc, safe=False)
