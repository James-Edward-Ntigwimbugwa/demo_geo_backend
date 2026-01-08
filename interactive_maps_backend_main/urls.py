from django.urls import path
from rest_framework.schemas import get_schema_view
from .views import RoomsListAPIView, RouteAPIView, HealthAPIView, RouteCacheAPIView, BaseFloorAsyncAPIView

schema_view = get_schema_view(title='Indoor Routing API', description='Schema for routing API')

urlpatterns = [
    path('rooms/', RoomsListAPIView.as_view(), name='rooms-list'),
    path('base-floor/', BaseFloorAsyncAPIView.as_view(), name='base-floor-list'),
    path('route/', RouteAPIView.as_view(), name='route-create'),
    path('route/cache/<int:cache_id>/', RouteCacheAPIView.as_view(), name='route-cache-get'),
    path('health/', HealthAPIView.as_view(), name='health'),
    path('schema/', schema_view, name='api-schema'),
]
