import json
from datetime import date
from tempfile import TemporaryDirectory
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.utils import timezone
from .models import Case, Consultation, Event, Profile, Unit
from .validation import TEACHING

BANK = {"bank_name":"Banco ficticio","account_type":"Corriente","account_number":"000123456","holder":"Persona Ficticia"}

def pdf():
    return SimpleUploadedFile("respaldo-prueba.pdf",b"%PDF-1.4\n%%EOF",content_type="application/pdf")

class WorkflowTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.unit=Unit.objects.create(name="Unidad A")
        other=Unit.objects.create(name="Unidad B")
        for role in ("requirente","secretaria_dea","direccion_dea","academica","decanato","personas","contabilidad","pregrado","postgrado"):
            u=get_user_model().objects.create_user(username=role)
            Profile.objects.create(user=u,role=role,unit=cls.unit if role=="requirente" else None)
        u=get_user_model().objects.create_user(username="otra_unidad")
        Profile.objects.create(user=u,role="requirente",unit=other)

    def setUp(self):
        tmp=TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.enterContext(override_settings(MEDIA_ROOT=tmp.name))
        year=timezone.localdate().year
        self.payload={"requester":"Responsable","position":"Secretaría","contact":"contacto@example.test","request_date":timezone.localdate().isoformat(),
          "provider":"Persona Ficticia","identifier":"12.345.678-5","identity_type":"rut","email":"persona@example.test","address":"Domicilio de prueba","nationality":"Chilena",
          "public_employee":False,"category":"Docencia","work":"Preparación de clases","cost_center":"123","start":f"{year}-08-01","end":f"{year}-12-31","amount":310000,
          "installments":[{"month":f"{year}-08","amount":160000},{"month":f"{year}-10","amount":150000}]}
        self.c=Client()

    def login_as(self,username):
        self.c.force_login(get_user_model().objects.get(username=username))

    def create(self,data=None):
        self.login_as("requirente")
        return self.c.post("/api/cases/",{"data":json.dumps(data or self.payload),**{k:pdf() for k in ("memo","identidad","cv","titulo")}})

    def detail(self):
        return self.c.get(self.url).json()

    def do(self,operation,expected=200,**data):
        r=self.c.post(self.url+"action/",{"action":operation,"version":self.detail()["version"],**data},content_type="application/json")
        self.assertEqual(r.status_code,expected,r.content)

    def attach(self,kind,installment=None):
        data={"kind":kind,"version":self.detail()["version"],"file":pdf()}
        if installment:
            data["installment"]=installment
        r=self.c.post(self.url+"documents/",data)
        self.assertEqual(r.status_code,201,r.content)

    def test_workflow_roles_consultations_documents_and_two_payments(self):
        r=self.create()
        self.assertEqual(r.status_code,201,r.content)
        self.url=f"/api/cases/{r.json()['id']}/"
        identity=next(d["id"] for d in self.detail()["documents"] if d["kind"]=="identidad")
        self.login_as("otra_unidad")
        self.assertEqual(self.c.get(self.url).status_code,404)
        self.assertEqual(self.c.get(f"/api/documents/{identity}/").status_code,404)

        self.login_as("secretaria_dea")
        self.do("return",note="Revisar glosa.")
        self.login_as("requirente")
        self.assertEqual(self.detail()["stage"],"intake")
        r=self.c.post(self.url+"correct/",{"data":json.dumps({**self.payload,"version":self.detail()["version"],"work":"Dictar y evaluar clases."})})
        self.assertEqual(r.status_code,200,r.content)

        self.login_as("secretaria_dea")
        stale=self.detail()["version"]
        self.do("advance")
        self.login_as("academica")
        self.do("advance",403)
        self.login_as("direccion_dea")
        self.do("advance",409,version=stale)
        self.do("advance")

        self.login_as("academica")
        self.do("consult",specialty="pregrado",note="¿Corresponde a la asignatura?")
        self.do("consult",specialty="pregrado",note="Duplicada.",expected=409)
        self.do("advance",409)
        self.login_as("postgrado")
        self.assertEqual(self.c.get(self.url).status_code,404)
        self.login_as("pregrado")
        d=self.detail()
        self.assertNotIn("identifier",d["data"])
        self.assertEqual(self.c.get(f"/api/documents/{identity}/").status_code,404)
        self.do("return",400,note="No tiene permiso para devolver.")
        self.do("reply",consultation=d["consultations"][0]["id"],decision="observed",note="Aclarar el resultado de aprendizaje.")
        self.login_as("academica")
        self.do("advance",400)
        self.do("advance",note="Resultado aclarado con la unidad.")
        self.login_as("decanato")
        self.do("advance")
        self.login_as("personas")
        self.do("claim")
        self.assertEqual(self.detail()["analyst"],"personas")
        self.do("advance",400,agreement="C-01")
        self.attach("convenio")
        self.attach("declaracion_simple")
        self.attach("declaracion_consanguinidad")
        bundle=self.c.get(self.url+"bundle/")
        self.assertEqual(bundle.status_code,200)
        self.assertTrue(b"".join(bundle.streaming_content).startswith(b"PK"))
        self.do("advance",agreement="C-01")
        self.login_as("requirente")
        self.assertEqual(self.detail()["analyst"],"personas")
        self.attach("firma_prestador")
        self.do("advance",400)
        self.attach("declaracion_simple_firmada")
        self.attach("declaracion_consang_firmada")
        self.do("advance")
        self.login_as("personas")
        self.attach("firma_autoridad")
        self.do("advance")
        self.attach("decreto")
        self.do("advance",decree="D-01")
        self.login_as("requirente")
        self.do("advance",400)
        parts=[i["id"] for i in self.detail()["installments"]]
        for part in parts:
            self.attach("boleta",part)
            self.attach("informe",part)
        self.do("advance")
        self.login_as("contabilidad")
        self.do("return",note="Falta corregir la boleta.")
        self.login_as("requirente")
        self.assertEqual(self.detail()["stage"],"boletas")
        self.do("advance",400)
        self.attach("boleta",parts[0])
        self.do("advance")
        self.login_as("contabilidad")
        self.assertEqual(self.detail()["stage"],"contabilidad")
        self.do("advance")
        self.do("pay",400,installment=parts[0],paid_on=timezone.localdate().isoformat())
        self.login_as("secretaria_dea")
        self.do("bank",bank=BANK)
        self.login_as("contabilidad")
        self.assertEqual(self.detail()["bank"],BANK)
        for index,part in enumerate(parts):
            self.attach("comprobante",part)
            self.do("pay",installment=part,paid_on=timezone.localdate().isoformat(),bank_verified=True)
            self.assertEqual(self.detail()["stage"],"closed" if index==1 else "pago")
        self.assertEqual(self.detail()["agreement"],"C-01")
        self.assertEqual(self.detail()["decree"],"D-01")
        self.assertTrue(Event.objects.filter(action="Respuesta de Pregrado").exists())

    def test_rejects_bad_totals_and_accepts_passport_with_initial_documents(self):
        bad={**self.payload,"amount":999999}
        self.assertEqual(self.create(bad).status_code,400)
        passport={**self.payload,"identity_type":"passport","identifier":"PRUEBA001"}
        r=self.create(passport)
        self.assertEqual(r.status_code,201,r.content)
        self.assertEqual(Case.objects.count(),1)

    def updated_payload(self,category="Docencia por curso o diplomado"):
        year=timezone.localdate().year
        return {**self.payload,"form_version":2,"category":category,"honorarium_type":"Persona Natural",
            "workload":"Parcial","provider_phone":"222222222","locality":"Santiago",
            "supervisor":"Supervisor Ficticio","supervisor_identifier":"12.345.678-5",
            "service_location":"Santiago","justification":"Actividad de prueba","certificate_type":"Experticia",
            "weekly_hours":2.5,"total_hours":10.5,"lective_hours":8,"non_lective_hours":2.5,
            "travel":"no","start":f"{year}-11-20","end":f"{year}-12-31",
            "installments":[{"month":f"{year}-11","amount":160000},{"month":f"{year}-12","amount":150000}]}

    @patch("django.utils.timezone.localdate",return_value=date(2026,11,20))
    def test_updated_form_preserves_details_and_uses_server_date(self,_):
        data={**self.updated_payload(),"request_date":"2020-01-01","bank":{"pending":True}}
        r=self.create(data)
        self.assertEqual(r.status_code,201,r.content)
        case=Case.objects.get(pk=r.json()["id"])
        self.assertEqual(case.payload["request_date"],"2026-11-20")
        for key in ("honorarium_type","workload","weekly_hours","total_hours","supervisor_identifier","certificate_type","lective_hours","non_lective_hours"):
            self.assertEqual(case.payload[key],data[key] if key!="supervisor_identifier" else "12345678-5")
        self.assertEqual(case.bank,{})
        self.assertEqual(case.installments.count(),2)

    @patch("django.utils.timezone.localdate",return_value=date(2026,11,20))
    def test_updated_hierarchy_skips_finance_and_supports_internal_calculation(self,_):
        data={**self.updated_payload(TEACHING),"cost_center":"","amount":None,"installments":[]}
        r=self.create(data)
        self.assertEqual(r.status_code,201,r.content)
        self.url=f"/api/cases/{r.json()['id']}/"
        self.login_as("secretaria_dea")
        self.do("advance")
        self.login_as("direccion_dea")
        self.do("finance",400,amount=310000,installments=self.updated_payload()["installments"])
        self.do("finance",cost_center="CC-123",amount=310000,installments=self.updated_payload()["installments"])
        self.assertEqual(self.detail()["data"]["cost_center"],"CC-123")
        self.do("advance")

    @patch("django.utils.timezone.localdate",return_value=date(2026,11,20))
    def test_updated_form_rejects_invalid_hours_supervisor_and_missing_certificate(self,_):
        for change in ({"non_lective_hours":2},{"supervisor_identifier":"12.345.678-0"},{"certificate_type":""},{"start":"2026-11-19"},{"public_employee":True,"public_entity":"Otra institución","public_contract":"Contrata","public_hours":"2.5","public_duties":"Docencia"}):
            with self.subTest(change=change):
                self.assertEqual(self.create({**self.updated_payload(),**change}).status_code,400)
        self.assertEqual(Case.objects.count(),0)

    @patch("django.utils.timezone.localdate",return_value=date(2026,3,1))
    def test_updated_form_allows_more_than_six_months_in_same_year(self,_):
        data={**self.updated_payload(),"start":"2026-03-01","end":"2026-12-31"}
        self.assertEqual(self.create(data).status_code,201)

    def test_teaching_calculation_and_hours_return(self):
        payload={**self.payload,"category":TEACHING,"lective_hours":20,"non_lective_hours":5}
        r=self.create({**payload,"amount":None,"installments":[]})
        self.assertEqual(r.status_code,201,r.content)
        self.url=f"/api/cases/{r.json()['id']}/"
        self.assertIsNone(self.detail()["amount"])
        self.login_as("secretaria_dea")
        self.do("advance")
        self.login_as("direccion_dea")
        self.do("advance",400)
        self.do("finance",amount=payload["amount"],installments=payload["installments"])
        self.do("advance")
        self.login_as("academica")
        self.do("return",note="Revisar horas.")
        self.login_as("requirente")
        response=self.c.post(self.url+"correct/",{"data":json.dumps({**payload,"lective_hours":25,"version":self.detail()["version"]})})
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(self.detail()["stage"],"presupuesto")
        self.assertIsNone(self.detail()["amount"])
        self.assertFalse(self.detail()["installments"])
        self.login_as("direccion_dea")
        self.do("finance",amount=payload["amount"],installments=payload["installments"])
        self.do("advance")
        self.assertEqual(self.detail()["stage"],"academica")

    def test_amount_only_from_decanato_rechecks_budget_then_decanato(self):
        r=self.create()
        self.assertEqual(r.status_code,201,r.content)
        self.url=f"/api/cases/{r.json()['id']}/"
        for role in ("secretaria_dea","direccion_dea","academica"):
            self.login_as(role)
            self.do("advance")
        self.login_as("decanato")
        self.do("return",note="Corregir el monto informado.")
        self.login_as("requirente")
        parts=[{**i,"amount":i["amount"]+10000} for i in self.payload["installments"]]
        response=self.c.post(self.url+"correct/",{"data":json.dumps({**self.payload,"amount":330000,"installments":parts,"version":self.detail()["version"]})})
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(self.detail()["stage"],"presupuesto")
        self.login_as("direccion_dea")
        self.do("advance")
        self.assertEqual(self.detail()["stage"],"decanato")

    def test_bank_access_audit_and_february_intake(self):
        r=self.create({**self.payload,"bank":BANK})
        self.assertEqual(r.status_code,201,r.content)
        self.url=f"/api/cases/{r.json()['id']}/"
        for role in ("requirente","academica","decanato","contabilidad","personas"):
            self.login_as(role)
            self.assertIsNone(self.detail()["bank"])
            self.do("bank",403,bank=BANK)
        self.login_as("direccion_dea")
        self.assertEqual(self.detail()["bank"],BANK)
        version=self.detail()["version"]
        self.do("bank",bank={**BANK,"account_number":"000789"})
        self.assertEqual(self.detail()["stage"],"documental")
        self.do("bank",409,bank=BANK,version=version)
        self.assertNotIn("000789",json.dumps(self.detail()["events"]))
        with patch("tramites.views.timezone.localdate",return_value=date(2026,2,15)):
            r=self.create()
            self.assertEqual(r.status_code,400)
            self.assertIn("febrero",r.json()["error"])

    def test_csrf_and_session_lifecycle(self):
        u=get_user_model().objects.get(username="academica")
        u.set_password("una-clave-prueba")
        u.save()
        c=Client(enforce_csrf_checks=True)
        self.assertEqual(c.get("/api/cases/").status_code,401)

        data={"username":"academica","password":"una-clave-prueba"}
        self.assertEqual(c.post("/api/login/",data,content_type="application/json").status_code,403)
        token=c.get("/api/session/").json()["csrf"]
        login=c.post("/api/login/",data,content_type="application/json",HTTP_X_CSRFTOKEN=token)
        self.assertEqual(login.status_code,200)
        self.assertEqual(login.json()["user"]["role"],"academica")
        self.assertEqual(c.post("/api/logout/",{},content_type="application/json",HTTP_X_CSRFTOKEN=login.json()["csrf"]).status_code,200)
        self.assertEqual(c.get("/api/cases/").status_code,401)

    def test_only_pregrado_and_postgrado_can_receive_optional_consultations(self):
        from .flow import ROLES, SPECIALTIES
        self.assertEqual(set(SPECIALTIES),{"pregrado","postgrado"})
        self.assertNotIn("admin",ROLES)
        self.assertNotIn("extension",ROLES)
        r=self.create()
        self.url=f"/api/cases/{r.json()['id']}/"
        for role in ("secretaria_dea","direccion_dea"):
            self.login_as(role)
            self.do("advance")
        self.login_as("academica")
        self.do("consult",400,specialty="extension",note="Consulta ya no disponible.")
        self.do("consult",specialty="pregrado",note="Revisar pertinencia de pregrado.")
        self.login_as("postgrado")
        self.assertEqual(self.c.get(self.url).status_code,404)
        self.login_as("academica")
        self.do("consult",specialty="postgrado",note="Revisar pertinencia de postgrado.")
        self.do("advance",409)
        for role in ("pregrado","postgrado"):
            self.login_as(role)
            detail=self.detail()
            self.assertEqual([q["specialty"] for q in detail["consultations"]],[role])
            self.assertIsNone(detail["bank"])
            self.assertNotIn("identifier",detail["data"])
            self.do("reply",consultation=detail["consultations"][0]["id"],decision="approved")
        self.login_as("academica")
        self.do("advance")
        self.assertEqual(self.detail()["stage"],"decanato")

    def test_retired_roles_cannot_sign_in_or_keep_session_access(self):
        for role in ("extension","admin"):
            user=get_user_model().objects.create_user(username=role,password="retired-test-only")
            Profile.objects.create(user=user,role=role)
            self.c.logout()
            response=self.c.post("/api/login/",{"username":role,"password":"retired-test-only"},content_type="application/json")
            self.assertEqual(response.status_code,401)
            self.c.force_login(user)
            self.assertIsNone(self.c.get("/api/session/").json()["user"])
            self.assertEqual(self.c.get("/api/cases/").status_code,401)

    def test_migration_cancels_only_pending_extension_consultations(self):
        from importlib import import_module
        from django.apps import apps
        from django.db import connection
        migrate=import_module("tramites.migrations.0004_retire_extension_consultations").retire_pending_consultations
        r=self.create()
        case=Case.objects.get(pk=r.json()["id"])
        case.stage="academica"
        case.save()
        actor=get_user_model().objects.get(username="academica")
        pending=Consultation.objects.create(case=case,specialty="extension",requested_by=actor,question="Consulta antigua")
        resolved=Consultation.objects.create(case=case,specialty="extension",requested_by=actor,question="Consulta resuelta",decision="approved",answer="Respuesta anterior")
        current=Consultation.objects.create(case=case,specialty="pregrado",requested_by=actor,question="Consulta vigente")
        initial_version=case.version
        from types import SimpleNamespace
        editor=SimpleNamespace(connection=connection)
        migrate(apps,editor)
        migrate(apps,editor)
        pending.refresh_from_db();resolved.refresh_from_db();current.refresh_from_db();case.refresh_from_db()
        self.assertEqual(pending.decision,"cancelled")
        self.assertEqual(resolved.answer,"Respuesta anterior")
        self.assertEqual(current.decision,"pending")
        self.assertEqual(case.stage,"academica")
        self.assertEqual(case.version,initial_version+1)
        self.assertEqual(Event.objects.filter(case=case,action="Consulta retirada por actualización del sistema").count(),1)
