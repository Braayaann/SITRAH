from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from tramites.flow import ROLES
from tramites.models import Case, Installment, Profile, Unit
from tramites.views import record

class Command(BaseCommand):
    help = "Crea cuentas y expedientes ficticios para evaluación local."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.SITRAH_DEMO:
            self.stderr.write("Activa SITRAH_DEMO=1 para habilitar los datos ficticios.")
            return
        unit,_ = Unit.objects.get_or_create(name="Departamento de Literatura")
        Unit.objects.get_or_create(name="Departamento de Historia")
        users={}
        for role,label in ROLES.items():
            u,created=get_user_model().objects.get_or_create(username=role,defaults={"first_name":label})
            if created:
                u.set_password("Sitrah-Demo-2026")
                u.save()
            Profile.objects.get_or_create(user=u,defaults={"role":role,"unit":unit if role=="requirente" else None})
            users[role]=u
        if Case.objects.exists():
            return
        date=timezone.localdate()
        year=date.year
        for name,category,stage in [("Camila Rojas Vidal","Docencia","documental"),("Martín Soto Lira","Investigación","presupuesto"),("Elisa Castro Reyes","Extensión","academica")]:
            data={"requester":"Unidad de demostración","position":"Secretaría","contact":"unidad@example.test","request_date":date.isoformat(),"provider":name,
                  "identifier":"12345678-5","identity_type":"rut","email":"prestador@example.test","address":"Dirección ficticia","nationality":"Chilena","public_employee":False,
                  "category":category,"work":"Preparación de materiales y apoyo a actividades de la Facultad.","cost_center":"CC-DEMO-01",
                  "start":f"{year}-08-01","end":f"{year}-11-30","amount":1200000,"summer_reason":""}
            c=Case.objects.create(unit=unit,created_by=users["requirente"],payload=data,stage="intake")
            Installment.objects.create(case=c,month=f"{year}-11",amount=data["amount"])
            record(c,users["requirente"],"Expediente de demostración","Estado inicial de muestra; usa una nueva solicitud para probar todos los respaldos.",stage)
        self.stdout.write(self.style.SUCCESS("Datos de demostración listos."))
