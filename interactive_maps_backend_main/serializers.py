from rest_framework import serializers


class RoomSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='ogc_fid')
    name = serializers.CharField(source='text')
    location = serializers.JSONField()  # expected GeoJSON dict


class RouteRequestSerializer(serializers.Serializer):
    start_room_id = serializers.IntegerField()
    end_room_id = serializers.IntegerField()
    simplify_tolerance = serializers.FloatField(default=0.0, required=False)


class RouteResultSerializer(serializers.Serializer):
    distance_meters = serializers.FloatField()
    route = serializers.JSONField()  # GeoJSON LineString


class BaseFloorSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='ogc_fid')
    layer = serializers.CharField(allow_null=True)
    paperspace = serializers.BooleanField(allow_null=True)
    text = serializers.CharField(allow_null=True)
    geometry = serializers.JSONField()  # GeoJSON LineString
