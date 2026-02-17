from django.db import models


class Coordinador(models.Model):
    nombre_completo = models.CharField(max_length=200)
    sede = models.CharField(max_length=100, blank=True, default="Arica")
    area_academica = models.CharField(max_length=200, blank=True, default="")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre_completo


class Periodo(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Pauta(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, default="")
    url = models.URLField(blank=True, default="")

    def __str__(self):
        return self.nombre


class Objetivo(models.Model):
    eje_estrategico = models.CharField(max_length=200, blank=True, default="")
    objetivo = models.CharField(max_length=250)
    indicador = models.TextField(blank=True, default="")
    nivel_esperado = models.TextField(blank=True, default="")
    ponderacion = models.PositiveIntegerField(default=0)  # %
    pauta = models.ForeignKey(Pauta, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.objetivo


class ConductaSello(models.Model):
    conducta = models.CharField(max_length=250)
    descripcion = models.TextField(blank=True, default="")
    nivel_esperado = models.TextField(blank=True, default="")
    ponderacion = models.PositiveIntegerField(default=0)  # %
    pauta = models.ForeignKey(Pauta, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.conducta


class Evaluacion(models.Model):
    coordinador = models.ForeignKey(Coordinador, on_delete=models.CASCADE)
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    cerrada = models.BooleanField(default=False)

    # Comentarios
    fortalezas = models.TextField(blank=True, default="")
    oportunidades_mejora = models.TextField(blank=True, default="")
    resumen_comentarios = models.TextField(blank=True, default="")
    retroalimentacion = models.TextField(blank=True, default="")

    # Score total calculable
    score_total = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.coordinador} - {self.periodo}"


class RespuestaObjetivo(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE, related_name="resp_objetivos")
    objetivo = models.ForeignKey(Objetivo, on_delete=models.CASCADE)

    # ejemplo: "Destacado/Logrado/En desarrollo" o 0-100
    cumplimiento = models.CharField(max_length=50, blank=True, default="")

    def __str__(self):
        return f"{self.evaluacion} | {self.objetivo}"


class RespuestaConducta(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE, related_name="resp_conductas")
    conducta = models.ForeignKey(ConductaSello, on_delete=models.CASCADE)

    cumplimiento = models.CharField(max_length=50, blank=True, default="")

    def __str__(self):
        return f"{self.evaluacion} | {self.conducta}"
