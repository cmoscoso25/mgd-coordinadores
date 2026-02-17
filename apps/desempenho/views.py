from django.shortcuts import render


def dashboard(request):
    context = {
        "title": "MGD Coordinadores",
        "subtitle": "Modelo de Gestión de Desempeño - Coordinador de Carrera (MVP)"
    }
    return render(request, "dashboard.html", context)
