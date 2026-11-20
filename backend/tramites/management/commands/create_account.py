from getpass import getpass
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from tramites.flow import ROLES
from tramites.models import Profile, Unit


class Command(BaseCommand):
    help = "Crea una cuenta personal operativa sin permisos de administrador."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("role", choices=ROLES)
        parser.add_argument("--unit")
        parser.add_argument("--name", required=True)
        parser.add_argument("--email", required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.filter(username=options["username"]).exists():
            raise CommandError("El usuario ya existe; no se modificó su cuenta.")
        if options["role"] == "requirente" and not options["unit"]:
            raise CommandError("Indica la unidad requirente con --unit.")
        password = getpass("Contraseña: ")
        if password != getpass("Repite la contraseña: "):
            raise CommandError("Las contraseñas no coinciden.")
        user = User(username=options["username"], first_name=options["name"], email=options["email"])
        try:
            user.full_clean(exclude=["password"])
            validate_password(password, user, password_validators=None)
        except ValidationError as error:
            raise CommandError("; ".join(error.messages))
        if len(password) < 12:
            raise CommandError("Usa al menos 12 caracteres.")
        user.set_password(password)
        user.save()
        unit = None
        if options["role"] == "requirente":
            unit, _ = Unit.objects.get_or_create(name=options["unit"].strip())
        Profile.objects.create(user=user, role=options["role"], unit=unit)
        self.stdout.write(self.style.SUCCESS("Cuenta personal creada."))
