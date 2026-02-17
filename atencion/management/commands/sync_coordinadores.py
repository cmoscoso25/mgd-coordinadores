from django.core.management.base import BaseCommand
from django.apps import apps
from atencion.models import Coordinador


class Command(BaseCommand):
    help = "Sincroniza coordinadores desde desempenho.Coordinator hacia atencion.Coordinador"

    def handle(self, *args, **options):
        # 1) Obtener modelo origen correcto (OJO: es Coordinator, no Coordinador)
        try:
            OrigenCoordinator = apps.get_model("desempenho", "Coordinator")
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"No pude cargar desempenho.Coordinator. Error: {e}\n"
                f"Verifica que 'apps.desempenho' esté en INSTALLED_APPS y que exista el modelo Coordinator."
            ))
            return

        origen_qs = OrigenCoordinator.objects.all()
        total_origen = origen_qs.count()

        if total_origen == 0:
            self.stdout.write(self.style.WARNING("No hay registros en desempenho.Coordinator para sincronizar."))
            return

        created = 0
        updated = 0

        for src in origen_qs:
            # Ajusta nombres de campos según tu modelo de desempenho
            # En tu admin se ve: nombre completo, sede, área académica, is_active
            nombre = getattr(src, "nombre_completo", None) or getattr(src, "nombre", None) or str(src)
            sede = getattr(src, "sede", "") or ""
            area = getattr(src, "area_academica", "") or ""
            activo = getattr(src, "is_active", True)

            obj, was_created = Coordinador.objects.update_or_create(
                nombre_completo=nombre,
                defaults={
                    "sede": sede,
                    "area_academica": area,
                    "is_active": bool(activo),
                }
            )

            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"OK. Coordinadores sincronizados desde desempenho.Coordinator -> atencion.Coordinador | "
            f"Origen={total_origen} | Creados={created} | Actualizados={updated}"
        ))
