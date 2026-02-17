from django.core.management.base import BaseCommand
from atencion.models import (
    Colaborador,
    Periodo,
    Pauta,
    Objetivo,
    ConductaSello,
    Evaluacion,
    RespuestaObjetivo,
    RespuestaConducta
)
from datetime import date


class Command(BaseCommand):
    help = "Carga datos iniciales de Evaluación de Desempeño (seed)"

    def handle(self, *args, **kwargs):

        # -------------------------
        # PERIODO
        # -------------------------
        periodo, _ = Periodo.objects.get_or_create(
            nombre="Evaluación Desempeño Docente 2025",
            anio=2025,
            defaults={"activo": True}
        )

        # -------------------------
        # PAUTA
        # -------------------------
        pauta, _ = Pauta.objects.get_or_create(
            nombre="Evaluación Desempeño Docente",
            version="2025",
            defaults={"activa": True}
        )

        # -------------------------
        # OBJETIVOS
        # -------------------------
        objetivos_data = [
            {
                "eje_estrategico": "Modelo Educativo",
                "objetivo": "Implementación del proceso de Enseñanza y Aprendizaje",
                "indicador": "Aplica estrategias didácticas y evaluativas definidas",
                "nivel_esperado": "Utiliza correctamente estrategias y evaluaciones alineadas",
                "ponderacion": 15,
            },
            {
                "eje_estrategico": "Modelo Educativo",
                "objetivo": "Participación activa de estudiantes",
                "indicador": "Promueve participación e interés",
                "nivel_esperado": "Fomenta participación constante y contextualizada",
                "ponderacion": 15,
            },
            {
                "eje_estrategico": "Gestión Académica",
                "objetivo": "Cumplimiento administrativo",
                "indicador": "Entrega oportuna de evaluaciones",
                "nivel_esperado": "Cumple plazos y registros institucionales",
                "ponderacion": 15,
            },
            {
                "eje_estrategico": "Estudiantes y Egresados",
                "objetivo": "Retroalimentación de aprendizajes",
                "indicador": "Entrega feedback oportuno",
                "nivel_esperado": "Retroalimenta de forma clara y oportuna",
                "ponderacion": 15,
            },
            {
                "eje_estrategico": "Resultados",
                "objetivo": "Resultado encuesta Evaluación Docente",
                "indicador": "Promedio encuestas institucionales",
                "nivel_esperado": "Promedio ≥ 75%",
                "ponderacion": 20,
            },
        ]

        objetivos = []
        for data in objetivos_data:
            obj, _ = Objetivo.objects.get_or_create(
                pauta=pauta,
                eje_estrategico=data["eje_estrategico"],
                objetivo=data["objetivo"],
                defaults=data
            )
            objetivos.append(obj)

        # -------------------------
        # CONDUCTA SELLO
        # -------------------------
        conducta, _ = ConductaSello.objects.get_or_create(
            pauta=pauta,
            conducta="Conductas Sello INACAP",
            defaults={
                "descripcion": "Representa el sello INACAP y lo lleva a la acción",
                "nivel_esperado": "Demuestra compromiso con valores institucionales",
                "ponderacion": 20,
            }
        )

        # -------------------------
        # COLABORADORES
        # -------------------------
        colab1, _ = Colaborador.objects.get_or_create(
            nombre="Alejandra Denise Nina Huanca",
            defaults={"cargo": "Docente"}
        )

        colab2, _ = Colaborador.objects.get_or_create(
            nombre="Alejandro José Apata Espina",
            defaults={"cargo": "Docente"}
        )

        # -------------------------
        # EVALUACION
        # -------------------------
        evaluacion, _ = Evaluacion.objects.get_or_create(
            colaborador=colab1,
            periodo=periodo,
            pauta=pauta,
            defaults={
                "fecha_creacion": date.today(),
                "fortalezas": "Demuestra alto compromiso y responsabilidad.",
                "oportunidades_mejora": "Potenciar uso de metodologías activas.",
                "resumen_comentarios": "Desempeño sólido y alineado al modelo educativo."
            }
        )

        # -------------------------
        # RESPUESTAS OBJETIVOS
        # -------------------------
        for obj in objetivos:
            RespuestaObjetivo.objects.get_or_create(
                evaluacion=evaluacion,
                objetivo=obj,
                defaults={
                    "autoevaluacion": "DESTACADO",
                    "evaluacion_jefatura": "DESTACADO",
                }
            )

        # -------------------------
        # RESPUESTA CONDUCTA
        # -------------------------
        RespuestaConducta.objects.get_or_create(
            evaluacion=evaluacion,
            conducta=conducta,
            defaults={
                "autoevaluacion": "LOGRADO",
                "evaluacion_jefatura": "DESTACADO",
            }
        )

        self.stdout.write(self.style.SUCCESS("✅ Seed de Evaluación cargado correctamente"))
