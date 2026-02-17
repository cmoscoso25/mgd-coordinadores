from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


# -------------------------------------------------
# Coordinador de Carrera
# -------------------------------------------------
class Coordinator(models.Model):
    full_name = models.CharField("Nombre completo", max_length=150)
    email = models.EmailField(blank=True, null=True)
    campus = models.CharField("Sede", max_length=100)
    area = models.CharField("Área académica", max_length=120)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.full_name


# -------------------------------------------------
# Periodo de evaluación (mensual)
# -------------------------------------------------
class Period(models.Model):
    year = models.PositiveIntegerField()
    month = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    closed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("year", "month")
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"{self.month:02d}-{self.year}"


# -------------------------------------------------
# Funciones del Coordinador de Carrera
# -------------------------------------------------
class Function(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    weight = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )

    def __str__(self):
        return self.name


# -------------------------------------------------
# Indicadores (KPIs)
# -------------------------------------------------
class KPI(models.Model):
    function = models.ForeignKey(Function, on_delete=models.CASCADE, related_name="kpis")
    name = models.CharField(max_length=200)
    target = models.FloatField("Meta")
    weight = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )

    def __str__(self):
        return f"{self.function.name} - {self.name}"


# -------------------------------------------------
# Evaluación mensual del coordinador
# -------------------------------------------------
class Evaluation(models.Model):
    coordinator = models.ForeignKey(Coordinator, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    total_score = models.FloatField(default=0)

    class Meta:
        unique_together = ("coordinator", "period")

    def recalc_score(self):
        results = self.kpi_results.all()
        if not results:
            self.total_score = 0
            return

        weighted_sum = sum(r.score * r.kpi.weight for r in results)
        weight_total = sum(r.kpi.weight for r in results)
        self.total_score = round(weighted_sum / weight_total, 2)
        self.save()

    def __str__(self):
        return f"{self.coordinator} - {self.period}"


# -------------------------------------------------
# Resultado del KPI
# -------------------------------------------------
class KPIResult(models.Model):
    evaluation = models.ForeignKey(
        Evaluation, related_name="kpi_results", on_delete=models.CASCADE
    )
    kpi = models.ForeignKey(KPI, on_delete=models.CASCADE)
    value = models.FloatField("Valor medido")
    score = models.FloatField(default=0)

    def calculate_score(self):
        if self.kpi.target > 0:
            self.score = min(100, (self.value / self.kpi.target) * 100)
        else:
            self.score = 0
        self.save()
        self.evaluation.recalc_score()

    def __str__(self):
        return f"{self.kpi.name}: {self.score}"


# -------------------------------------------------
# Evidencias
# -------------------------------------------------
class Evidence(models.Model):
    kpi_result = models.ForeignKey(
        KPIResult, related_name="evidences", on_delete=models.CASCADE
    )
    description = models.CharField(max_length=200)
    file = models.FileField(upload_to="evidences/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.description
