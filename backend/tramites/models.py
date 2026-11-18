import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone

class Unit(models.Model):
    name = models.CharField(max_length=160, unique=True)
    active = models.BooleanField(default=True)

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=30)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, null=True, blank=True)

class Case(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    payload = models.JSONField(default=dict)
    stage = models.CharField(max_length=30, default="documental")
    returned_from = models.CharField(max_length=30, blank=True)
    review_queue = models.JSONField(default=list, blank=True)
    bank = models.JSONField(default=dict, blank=True)
    analyst = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="assigned_cases")
    version = models.PositiveIntegerField(default=1)
    stage_since = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    agreement = models.CharField(max_length=80, null=True, blank=True, unique=True)
    decree = models.CharField(max_length=80, null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    @property
    def number(self):
        return f"SIT-{timezone.localtime(self.created_at).year}-{self.pk:05d}"

class Event(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=80)
    origin = models.CharField(max_length=30)
    destination = models.CharField(max_length=30)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Consultation(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="consultations")
    specialty = models.CharField(max_length=30)
    question = models.TextField()
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    decision = models.CharField(max_length=20, default="pending")
    answer = models.TextField(blank=True)
    answered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["case", "specialty"], condition=models.Q(decision="pending"), name="unique_pending_consultation")]

class Installment(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="installments")
    month = models.CharField(max_length=7)
    amount = models.PositiveBigIntegerField()
    paid_on = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["case", "month"], name="unique_installment_month")]

def document_path(instance, filename):
    return f"cases/{instance.case_id}/{uuid.uuid4().hex}.pdf"

class Document(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="documents")
    installment = models.ForeignKey(Installment, on_delete=models.PROTECT, null=True, blank=True)
    kind = models.CharField(max_length=30)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to=document_path)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
