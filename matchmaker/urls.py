from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("match/<uuid:match_id>/", views.match_detail, name="match_detail"),
    path("match/<uuid:match_id>/status/", views.match_status, name="match_status"),
]
