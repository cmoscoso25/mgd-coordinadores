from django.urls import path
from . import views

app_name = "desempenho"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
]
