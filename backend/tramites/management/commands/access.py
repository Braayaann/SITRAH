from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from tramites.flow import ROLES
from tramites.models import Profile, Unit

class Command(BaseCommand):
    help = "Asigna a un usuario de Django un perfil operativo de SITRAH."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("role", choices=ROLES)
        parser.add_argument("--unit", help="Nombre de unidad requirente")

    @transaction.atomic
    def handle(self, *args, **options):
        user = get_user_model().objects.filter(username=options["username"]).first()
        if not user:
            raise CommandError("Crea primero el usuario con createsuperuser o mediante la administración de usuarios de tu instalación.")
        unit=None
        if options["role"]=="requirente":
            name=(options["unit"] or "").strip()
            if not name or len(name)>160:
                raise CommandError("Para un requirente indica --unit con el nombre de la unidad.")
            unit,_=Unit.objects.get_or_create(name=name)
        Profile.objects.update_or_create(user=user,defaults={"role":options["role"],"unit":unit})
        self.stdout.write(self.style.SUCCESS("Perfil asignado."))
