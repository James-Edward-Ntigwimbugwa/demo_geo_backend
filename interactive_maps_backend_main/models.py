from django.db import models
from django.contrib.gis.db import models as geomodels


class RoomPoint(models.Model):
    """Represents `room_points` table (rooms / POIs)."""
    ogc_fid = models.IntegerField(primary_key=True)
    text = models.CharField(max_length=255)
    wkb_geometry = geomodels.PointField(srid=4326)

    class Meta:
        db_table = 'room_points'
        managed = False


class NavEdgesFinal(models.Model):
    """Final routable graph table used by pgRouting."""
    ogc_fid = models.IntegerField(primary_key=True)
    source = models.IntegerField()
    target = models.IntegerField()
    cost = models.FloatField()
    wkb_geometry = geomodels.LineStringField(srid=4326)

    class Meta:
        db_table = 'nav_edges_final'
        managed = False


class NavEdgesWorkVerticesPgr(models.Model):
    """pgRouting vertices table (internal vertex ids and geometry)."""
    id = models.IntegerField(primary_key=True)
    the_geom = geomodels.PointField(srid=4326)

    class Meta:
        db_table = 'nav_edges_work_vertices_pgr'
        managed = False
