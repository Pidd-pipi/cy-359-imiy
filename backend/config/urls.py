from django.urls import path

from domain import views

urlpatterns = [
    path("health", views.health),
    path("api/health", views.health),
    path("overview", views.overview),
    path("api/overview", views.overview),
    # 赛后成绩结算
    path("api/course", views.course_detail),
    path("api/results/submit", views.results_submit),
    path("api/results/overview", views.results_overview),
    path("api/results/<int:result_id>/revoke", views.results_revoke),
]
