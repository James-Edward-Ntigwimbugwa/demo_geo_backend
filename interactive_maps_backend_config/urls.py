"""
URL configuration for interactive_maps_backend_config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from interactive_maps_backend_main import views as map_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/path_ways/', map_views.path_ways_geojson, name='path_ways_geojson'),
    path('api/nav_nodes/', map_views.nav_nodes_geojson, name='nav_nodes_geojson'),
    path('api/base_floor/', map_views.base_floor_geojson, name='base_floor_geojson'),
    path('api/room_points/', map_views.room_points_geojson, name='room_points_geojson'),
    path('api/route/', map_views.route_between_nodes, name='route_between_nodes'),
]
