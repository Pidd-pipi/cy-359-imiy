from django.urls import path

from domain import views

# Nginx 把 /api/ 代理到后端 /，因此同时注册带 /api 与不带前缀两套路径。
urlpatterns = [
    path("health", views.health),
    path("api/health", views.health),
    path("routes", views.routes),
    path("api/routes", views.routes),
    path("overview", views.overview),
    path("api/overview", views.overview),
    path("results/submit", views.submit),
    path("api/results/submit", views.submit),
    path("results/<int:result_id>/revoke", views.revoke),
    path("api/results/<int:result_id>/revoke", views.revoke),
]
