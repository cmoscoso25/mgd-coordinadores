from django.contrib import admin
from django.urls import path
from atencion import views

urlpatterns = [
    path("admin/", admin.site.urls),

    path("dashboard/", views.dashboard_gestion, name="dashboard_gestion"),
    path("crear-evaluacion/<int:coordinador_id>/<int:periodo_id>/", views.crear_evaluacion, name="crear_evaluacion"),
    path("evaluacion/<int:evaluacion_id>/", views.evaluacion_detalle, name="evaluacion_detalle"),

    # ACTA: HTML y PDF (mismo endpoint con ?format=pdf)
    path("acta/<int:evaluacion_id>/", views.acta_evaluacion, name="acta_evaluacion"),
]
