from django.core.management.base import BaseCommand
from apps.desempenho.models import Function, KPI


class Command(BaseCommand):
    help = "Carga/actualiza el catálogo base (Funciones + KPIs) para Coordinador de Carrera"

    def handle(self, *args, **options):
        # Funciones base (peso a nivel función)
        functions = [
            {
                "code": "ACADEMIC_QUALITY",
                "name": "Calidad académica (programas de estudio)",
                "description": "Apoyar al Director(a) de Carrera en garantizar y mantener la calidad académica del programa.",
                "weight": 30,
                "kpis": [
                    {"name": "Cumplimiento hitos académicos del mes (%)", "target": 95, "weight": 60},
                    {"name": "Cierres académicos dentro de plazo (%)", "target": 95, "weight": 40},
                ],
            },
            {
                "code": "TEACHER_MGMT",
                "name": "Gestión y soporte a docentes",
                "description": "Apoyar la selección, preparación y soporte a docentes según requisitos del programa.",
                "weight": 25,
                "kpis": [
                    {"name": "Docentes validados según requisitos (%)", "target": 100, "weight": 60},
                    {"name": "Tiempo de respuesta a incidencias docentes (meta en días)", "target": 3, "weight": 40},
                ],
            },
            {
                "code": "STUDENT_CARE",
                "name": "Atención y preocupación por estudiantes",
                "description": "Mantener una preocupación constante por los estudiantes, gestionando casos y apoyos.",
                "weight": 25,
                "kpis": [
                    {"name": "Casos estudiantiles resueltos dentro de SLA (%)", "target": 90, "weight": 70},
                    {"name": "Satisfacción atención (1-5)", "target": 4.3, "weight": 30},
                ],
            },
            {
                "code": "PROGRAM_PLANNING",
                "name": "Planificación y desarrollo del programa",
                "description": "Apoyar la planificación y el desarrollo del programa de estudio.",
                "weight": 10,
                "kpis": [
                    {"name": "Ejecución del plan mensual (%)", "target": 90, "weight": 100},
                ],
            },
            {
                "code": "ACADEMIC_ADMIN",
                "name": "Gestión administrativa académica con alumnos",
                "description": "Apoyar labores administrativas relacionadas a la gestión académica con alumnos.",
                "weight": 10,
                "kpis": [
                    {"name": "Solicitudes académicas procesadas en plazo (%)", "target": 90, "weight": 100},
                ],
            },
        ]

        created_functions = 0
        created_kpis = 0
        updated_kpis = 0

        for f in functions:
            func, func_created = Function.objects.update_or_create(
                code=f["code"],
                defaults={
                    "name": f["name"],
                    "description": f["description"],
                    "weight": f["weight"],
                },
            )
            if func_created:
                created_functions += 1

            for k in f["kpis"]:
                kpi, kpi_created = KPI.objects.update_or_create(
                    function=func,
                    name=k["name"],
                    defaults={
                        "target": k["target"],
                        "weight": k["weight"],
                    },
                )
                if kpi_created:
                    created_kpis += 1
                else:
                    updated_kpis += 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ Seed catálogo listo. Funciones nuevas: {created_functions}, KPIs nuevos: {created_kpis}, KPIs actualizados: {updated_kpis}"
        ))
