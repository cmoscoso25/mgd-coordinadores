from django.contrib import admin
from .models import (
    Coordinador, Periodo, Pauta, Objetivo, ConductaSello,
    Evaluacion, RespuestaObjetivo, RespuestaConducta
)


@admin.register(Coordinador)
class CoordinadorAdmin(admin.ModelAdmin):
    list_display = ("nombre_completo", "sede", "area_academica", "is_active")
    search_fields = ("nombre_completo", "sede", "area_academica")
    list_filter = ("sede", "is_active")


@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Pauta)
class PautaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "url")
    search_fields = ("nombre",)


@admin.register(Objetivo)
class ObjetivoAdmin(admin.ModelAdmin):
    list_display = ("objetivo", "eje_estrategico", "ponderacion")
    search_fields = ("objetivo", "eje_estrategico", "indicador")
    list_filter = ("eje_estrategico",)


@admin.register(ConductaSello)
class ConductaSelloAdmin(admin.ModelAdmin):
    list_display = ("conducta", "ponderacion")
    search_fields = ("conducta", "descripcion")


class RespuestaObjetivoInline(admin.TabularInline):
    model = RespuestaObjetivo
    extra = 0


class RespuestaConductaInline(admin.TabularInline):
    model = RespuestaConducta
    extra = 0


@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ("coordinador", "periodo", "score_total", "cerrada", "fecha_creacion")
    list_filter = ("periodo", "cerrada")
    search_fields = ("coordinador__nombre_completo",)
    inlines = [RespuestaObjetivoInline, RespuestaConductaInline]


@admin.register(RespuestaObjetivo)
class RespuestaObjetivoAdmin(admin.ModelAdmin):
    list_display = ("evaluacion", "objetivo", "cumplimiento")
    search_fields = ("evaluacion__coordinador__nombre_completo", "objetivo__objetivo")


@admin.register(RespuestaConducta)
class RespuestaConductaAdmin(admin.ModelAdmin):
    list_display = ("evaluacion", "conducta", "cumplimiento")
    search_fields = ("evaluacion__coordinador__nombre_completo", "conducta__conducta")
