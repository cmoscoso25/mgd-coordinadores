from django.contrib import admin
from .models import (
    Coordinator,
    Period,
    Function,
    KPI,
    Evaluation,
    KPIResult,
    Evidence,
)


@admin.register(Coordinator)
class CoordinatorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "campus", "area", "is_active")
    list_filter = ("campus", "area", "is_active")
    search_fields = ("full_name", "email", "campus", "area")
    ordering = ("full_name",)


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ("year", "month", "closed")
    list_filter = ("year", "closed")
    ordering = ("-year", "-month")


@admin.register(Function)
class FunctionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "weight")
    list_filter = ("weight",)
    search_fields = ("code", "name")


@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = ("name", "function", "target", "weight")
    list_filter = ("function",)
    search_fields = ("name", "function__name")
    ordering = ("function__name", "-weight", "name")


class EvidenceInline(admin.TabularInline):
    model = Evidence
    extra = 0


class KPIResultInline(admin.TabularInline):
    model = KPIResult
    extra = 0
    fields = ("kpi", "value", "score")
    readonly_fields = ("score",)


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ("coordinator", "period", "total_score", "created_at")
    list_filter = ("period__year", "period__month", "coordinator__campus", "coordinator__area")
    search_fields = ("coordinator__full_name",)
    ordering = ("-period__year", "-period__month", "coordinator__full_name")
    inlines = [KPIResultInline]

    actions = ["recalcular_scores"]

    @admin.action(description="Recalcular score total de evaluaciones seleccionadas")
    def recalcular_scores(self, request, queryset):
        for ev in queryset:
            ev.recalc_score()


@admin.register(KPIResult)
class KPIResultAdmin(admin.ModelAdmin):
    list_display = ("evaluation", "kpi", "value", "score")
    list_filter = ("kpi__function", "evaluation__period__year", "evaluation__period__month")
    search_fields = ("evaluation__coordinator__full_name", "kpi__name", "kpi__function__name")
    ordering = ("-evaluation__period__year", "-evaluation__period__month")
    inlines = [EvidenceInline]
    actions = ["calcular_scores"]

    @admin.action(description="Calcular score (y recalcular evaluación) para KPIResults seleccionados")
    def calcular_scores(self, request, queryset):
        for r in queryset:
            r.calculate_score()


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ("description", "kpi_result", "created_at")
    list_filter = ("created_at", "kpi_result__kpi__function")
    search_fields = ("description", "kpi_result__kpi__name")
