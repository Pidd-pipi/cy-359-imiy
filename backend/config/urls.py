from django.urls import path
from domain.views import health, overview

urlpatterns = [
    path("health", health),
    path("api/health", health),
    path("overview", overview),
    path("api/overview", overview),
]
