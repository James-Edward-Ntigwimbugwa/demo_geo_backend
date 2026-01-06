from django.db import models
from django.contrib.gis.db import models as gis_models


class BaseFloor(models.Model):
	ogc_fid = models.AutoField(primary_key=True)
	wkb_geometry = gis_models.LineStringField(srid=4326, null=True, blank=True)
	layer = models.CharField(max_length=255, null=True, blank=True)
	paperspace = models.BooleanField(null=True, blank=True)
	subclasses = models.CharField(max_length=255, null=True, blank=True)
	linetype = models.CharField(max_length=255, null=True, blank=True)
	entityhandle = models.CharField(max_length=255, null=True, blank=True)
	text = models.CharField(max_length=255, null=True, blank=True)

	class Meta:
		db_table = 'base_floor'
		managed = False


class Corridors(models.Model):
	ogc_fid = models.AutoField(primary_key=True)
	wkb_geometry = gis_models.LineStringField(srid=4326, null=True, blank=True)
	fid = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
	label = models.CharField(max_length=255, null=True, blank=True)
	type = models.CharField(max_length=255, null=True, blank=True)

	class Meta:
		db_table = 'corridors'
		managed = False


class NavNodes(models.Model):
	ogc_fid = models.AutoField(primary_key=True)
	wkb_geometry = gis_models.PointField(srid=4326, null=True, blank=True)
	fid = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
	label = models.CharField(max_length=255, null=True, blank=True)
	node_type = models.CharField(max_length=255, null=True, blank=True)

	class Meta:
		db_table = 'nav_nodes'
		managed = False


class NavNodesProj(models.Model):
	id = models.IntegerField(primary_key=True)
	geom = gis_models.PointField(srid=3857, null=True, blank=True)
	label = models.TextField(null=True, blank=True)
	node_type = models.TextField(null=True, blank=True)

	class Meta:
		db_table = 'nav_nodes_proj'
		managed = False


class NavNodesSnapped(models.Model):
	id = models.IntegerField(primary_key=True)
	geom = gis_models.PointField(null=True, blank=True)
	label = models.TextField(null=True, blank=True)
	node_type = models.TextField(null=True, blank=True)

	class Meta:
		db_table = 'nav_nodes_snapped'
		managed = False


class NavEdges(models.Model):
	ogc_fid = models.AutoField(primary_key=True)
	wkb_geometry = gis_models.LineStringField(srid=4326, null=True, blank=True)
	fid = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
	label = models.CharField(max_length=255, null=True, blank=True)
	from_id = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
	to_id = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)

	class Meta:
		db_table = 'nav_edges'
		managed = False


class NavEdgesProj(models.Model):
	id = models.IntegerField(primary_key=True)
	geom = gis_models.LineStringField(srid=3857, null=True, blank=True)
	label = models.TextField(null=True, blank=True)
	cost = models.FloatField(null=True, blank=True)

	class Meta:
		db_table = 'nav_edges_proj'
		managed = False


class NavEdgesFinal(models.Model):
	id = models.IntegerField(primary_key=True)
	geom = gis_models.LineStringField(srid=3857, null=True, blank=True)
	label = models.TextField(null=True, blank=True)
	cost = models.FloatField(null=True, blank=True)

	class Meta:
		db_table = 'nav_edges_final'
		managed = False


class NavEdgesWork(models.Model):
	id = models.IntegerField(primary_key=True)
	geom = gis_models.GeometryField(null=True, blank=True)
	cost = models.FloatField(null=True, blank=True)
	source = models.IntegerField(null=True, blank=True)
	target = models.IntegerField(null=True, blank=True)

	class Meta:
		db_table = 'nav_edges_work'
		managed = False


class NavEdgesWorkVerticesPgr(models.Model):
	id = models.BigIntegerField(primary_key=True)
	cnt = models.IntegerField(null=True, blank=True)
	chk = models.IntegerField(null=True, blank=True)
	ein = models.IntegerField(null=True, blank=True)
	eout = models.IntegerField(null=True, blank=True)
	the_geom = gis_models.PointField(srid=3857, null=True, blank=True)

	class Meta:
		db_table = 'nav_edges_work_vertices_pgr'
		managed = False


class RoomPoints(models.Model):
	ogc_fid = models.AutoField(primary_key=True)
	wkb_geometry = gis_models.PointField(null=True, blank=True)
	layer = models.CharField(max_length=255, null=True, blank=True)
	paperspace = models.BooleanField(null=True, blank=True)
	subclasses = models.CharField(max_length=255, null=True, blank=True)
	linetype = models.CharField(max_length=255, null=True, blank=True)
	entityhandle = models.CharField(max_length=255, null=True, blank=True)
	text = models.CharField(max_length=255, null=True, blank=True)

	class Meta:
		db_table = 'room_points'
		managed = False


class RouteResult(models.Model):
	seq = models.IntegerField(null=True, blank=True)
	node = models.BigIntegerField(null=True, blank=True)
	edge = models.BigIntegerField(null=True, blank=True)
	cost = models.FloatField(null=True, blank=True)
	geom = gis_models.GeometryField(null=True, blank=True)

	class Meta:
		db_table = 'route_result'
		managed = False
