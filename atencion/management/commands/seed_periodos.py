from django.core.management.base import BaseCommand
from atencion.models import Periodo


class Command(BaseCommand):
    help = "Crea periodos base si no existen (atencion.Periodo)"

    def handle(self, *args, **options):
        # Ajusta el nombre por defecto que quieres
        default_name = "Evaluación Desempeño Coordinadores 2025"

        # Tu modelo antes tenía 'nombre' y ahora 'name'
        # Vamos a soportar ambos sin romper.
        fields = [f.name for f in Periodo._meta.fields]

        if "name" in fields:
            obj, created = Periodo.objects.get_or_create(name=default_name)
        elif "nombre" in fields:
            obj, created = Periodo.objects.get_or_create(nombre=default_name)
        else:
            self.stdout.write(self.style.ERROR(
                "Periodo no tiene campo 'name' ni 'nombre'. Revisa atencion/models.py"
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f"OK Periodo listo: {obj} (created={created})"
        ))
