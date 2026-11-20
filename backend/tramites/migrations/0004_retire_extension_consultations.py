from django.db import migrations
from django.db.models import F
from django.utils import timezone


def retire_pending_consultations(apps, schema_editor):
    Consultation = apps.get_model("tramites", "Consultation")
    Case = apps.get_model("tramites", "Case")
    Event = apps.get_model("tramites", "Event")
    alias = schema_editor.connection.alias
    note = "Actualización del sistema: se retira Extensión de las direcciones consultadas. Dirección Académica puede continuar la revisión o consultar a Pregrado o Postgrado."
    for consultation in Consultation.objects.using(alias).filter(specialty="extension", decision="pending"):
        consultation.decision = "cancelled"
        consultation.answer = note
        consultation.answered_at = timezone.now()
        consultation.save(using=alias, update_fields=["decision", "answer", "answered_at"])
        case = Case.objects.using(alias).get(pk=consultation.case_id)
        Case.objects.using(alias).filter(pk=case.pk).update(version=F("version") + 1)
        Event.objects.using(alias).create(
            case_id=case.pk, actor_id=consultation.requested_by_id,
            action="Consulta retirada por actualización del sistema",
            origin=case.stage, destination=case.stage, note=note,
        )


class Migration(migrations.Migration):
    dependencies = [("tramites", "0003_case_analyst")]
    operations = [migrations.RunPython(retire_pending_consultations, migrations.RunPython.noop)]
