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
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from interactive_maps_backend_main import views as map_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Documentation endpoints
    path('api/docs/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Map data endpoints
    path('api/base_floor/', map_views.base_floor_geojson, name='base_floor_geojson'),
    path('api/corridors/', map_views.corridors_geojson, name='corridors_geojson'),
    path('api/room_points/', map_views.room_points_geojson, name='room_points_geojson'),
    
    # Navigation nodes endpoints
    path('api/nav_nodes/', map_views.nav_nodes_geojson, name='nav_nodes_geojson'),
    path('api/nav_nodes_proj/', map_views.nav_nodes_proj_geojson, name='nav_nodes_proj_geojson'),
    path('api/nav_nodes_snapped/', map_views.nav_nodes_snapped_geojson, name='nav_nodes_snapped_geojson'),
    
    # Navigation edges endpoints
    path('api/nav_edges/', map_views.nav_edges_geojson, name='nav_edges_geojson'),
    path('api/nav_edges_proj/', map_views.nav_edges_proj_geojson, name='nav_edges_proj_geojson'),
    path('api/nav_edges_final/', map_views.nav_edges_final_geojson, name='nav_edges_final_geojson'),
    
    # pgRouting endpoints
    path('api/route/shortest_path/', map_views.route_shortest_path, name='route_shortest_path'),
    path('api/route/astar/', map_views.route_astar_path, name='route_astar_path'),
    path('api/route/via_points/', map_views.route_via_points, name='route_via_points'),
    path('api/route/isochrone/', map_views.route_isochrone, name='route_isochrone'),
]
