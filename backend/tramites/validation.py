from datetime import date
from pathlib import Path
import re
import math
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone
from .flow import INITIAL_DOCS

class Invalid(Exception):
    def __init__(self, message, status=400):
        self.message, self.status = message, status

TEACHING = "Docencia por jerarquía"
COURSE = "Docencia por curso o diplomado"
CERTIFICATES = ("Título profesional", "Grado académico", "Alumno regular", "Experticia", "Otro certificado afín")
TEACHING_HOURS = ("lective_hours", "non_lective_hours")
BANK_FIELDS = {"bank_name":"banco", "account_type":"tipo de cuenta", "account_number":"número de cuenta", "holder":"titular de la cuenta"}

def validate_bank(value):
    if not isinstance(value,dict):
        raise Invalid("Revisa los datos bancarios.")
    if not value or value.get("pending") is True:
        return {}
    out = {k:string(value,k,label,120) for k,label in BANK_FIELDS.items()}
    if not re.fullmatch(r"[0-9 -]{3,40}",out["account_number"]) or not any(c.isdigit() for c in out["account_number"]):
        raise Invalid("Revisa el número de cuenta.")
    return out

def string(data, field, label, limit=200, required=True):
    value = data.get(field, "")
    if not isinstance(value, str) or len(value.strip()) > limit or (required and not value.strip()):
        raise Invalid(f"Revisa el campo «{label}».")
    return value.strip()

def read_date(value, label):
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        raise Invalid(f"Indica una fecha válida para {label}.")

def validate_payload(data):
    required = {
        "requester":"responsable", "position":"cargo", "contact":"correo de contacto",
        "provider":"nombre del prestador", "identifier":"RUT o pasaporte",
        "email":"correo del prestador", "address":"domicilio", "nationality":"nacionalidad",
        "identity_type":"tipo de identificación", "category":"tipo de actividad",
        "work":"glosa de la prestación",
        "start":"inicio", "end":"término", "request_date":"fecha de solicitud",
    }
    clean = {k: string(data,k,label,2500 if k=="work" else 200) for k,label in required.items()}
    for key in ("contact","email"):
        try:
            validate_email(clean[key])
        except ValidationError:
            raise Invalid(f"Revisa «{required[key]}».")
    if clean["category"] not in ("Docencia",TEACHING,COURSE,"Docencia por curso","Investigación","Extensión","Otra actividad","Otras actividades"):
        raise Invalid("Selecciona una actividad válida.")
    clean["cost_center"] = string(data,"cost_center","centro de costo",200,clean["category"]!=TEACHING)
    for key,label in {"requester_phone":"teléfono o anexo","provider_phone":"teléfono del prestador","locality":"comuna o ciudad","supervisor":"supervisor responsable","service_location":"lugar de la prestación","justification":"objetivo o justificación","remarks":"observaciones adicionales"}.items():
        value=string(data,key,label,1000,False)
        if value:
            clean[key]=value
    if clean["identity_type"] not in ("rut","passport"):
        raise Invalid("Selecciona RUT o pasaporte.")
    if clean["identity_type"] == "rut":
        rut = re.sub(r"[.\s-]", "", clean["identifier"]).upper()
        if not re.fullmatch(r"\d{1,8}[0-9K]", rut) or int(rut[:-1]) == 0:
            raise Invalid("Indica un RUT válido.")
        dv = (11-sum(int(n)*(2+i%6) for i,n in enumerate(reversed(rut[:-1])))%11)%11
        if rut[-1] != ("K" if dv==10 else str(dv)):
            raise Invalid("El dígito verificador del RUT no coincide.")
        clean["identifier"] = f"{int(rut[:-1])}-{rut[-1]}"
    elif not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 -]{2,29}",clean["identifier"]):
        raise Invalid("Revisa el número de pasaporte.")
    employed = data.get("public_employee")
    if not isinstance(employed,bool):
        raise Invalid("Indica si trabaja en una institución pública.")
    clean["public_employee"] = employed
    if employed:
        for key, label in {"public_entity":"institución pública","public_contract":"calidad contractual","public_hours":"horas semanales","public_duties":"funciones públicas"}.items():
            clean[key] = string(data,key,label,1000)
        for key,label in {"public_schedule":"jornada y horario","public_period":"período del vínculo"}.items():
            value=string(data,key,label,1000,False)
            if value:
                clean[key]=value
        if clean["public_contract"] not in ("Planta","Contrata","Honorarios","Otra") or not re.fullmatch(r"\d{1,3}(\.\d{1,2})?",clean["public_hours"]) or not 0 < float(clean["public_hours"]) <= 168:
            raise Invalid("Revisa la calidad contractual y las horas semanales.")
    start,end = read_date(clean["start"],"inicio"),read_date(clean["end"],"término")
    request_date = read_date(clean["request_date"],"solicitud")
    if request_date > timezone.localdate():
        raise Invalid("La fecha de solicitud no puede ser futura.")
    if end<start or start.year!=end.year:
        raise Invalid("El período debe estar ordenado y dentro del mismo año calendario.")
    clean["summer_reason"] = string(data,"summer_reason","justificación de enero/febrero",1000,start.month <= 2)
    if data.get("form_version")==2:
        validate_form_details(data,clean,start,request_date)
    if clean["category"]==TEACHING:
        for key in TEACHING_HOURS:
            value=data.get(key)
            if type(value) not in (int,float) or not math.isfinite(value) or not 0 <= value <= 10000:
                raise Invalid("Indica horas lectivas y no lectivas válidas.")
            clean[key]=value
        if not sum(clean[k] for k in TEACHING_HOURS):
            raise Invalid("La docencia por jerarquía requiere al menos una hora.")
        return clean|{"amount":None}, []
    amount,parts=validate_finance(data,start,end)
    return clean|{"amount":amount}, parts

def validate_form_details(data,clean,start,request_date):
    """Campos del formulario actualizado; los expedientes previos siguen siendo legibles."""
    clean["form_version"]=2
    for key,label in {"honorarium_type":"tipo de honorario","workload":"jornada","locality":"comuna y ciudad","provider_phone":"teléfono del prestador","supervisor":"supervisor responsable","supervisor_identifier":"RUT del supervisor","service_location":"localidad de prestación","justification":"objetivo o justificación","certificate_type":"tipo de certificado"}.items():
        clean[key]=string(data,key,label,1000)
    if clean["honorarium_type"] not in ("Persona Natural","Persona Jurídica") or clean["workload"] not in ("Completa","Media jornada","Parcial") or clean["certificate_type"] not in CERTIFICATES:
        raise Invalid("Revisa el tipo de honorario, la jornada y el certificado.")
    rut=re.sub(r"[.\s-]","",clean["supervisor_identifier"]).upper()
    if not re.fullmatch(r"\d{1,8}[0-9K]",rut) or not int(rut[:-1]):
        raise Invalid("Revisa el RUT del supervisor.")
    dv=(11-sum(int(n)*(2+i%6) for i,n in enumerate(reversed(rut[:-1])))%11)%11
    if rut[-1]!=("K" if dv==10 else str(dv)):
        raise Invalid("El dígito verificador del supervisor no coincide.")
    clean["supervisor_identifier"]=f"{int(rut[:-1])}-{rut[-1]}"
    if start<request_date:
        raise Invalid("El inicio debe ser igual o posterior a la fecha de solicitud.")
    for key in ("weekly_hours","total_hours"):
        value=data.get(key)
        if type(value) not in (int,float) or not math.isfinite(value) or not 0<value<=10000:
            raise Invalid("Revisa las horas semanales y totales.")
        clean[key]=value
    if clean["total_hours"]<clean["weekly_hours"]:
        raise Invalid("Las horas totales no pueden ser menores que las semanales.")
    if clean["category"] in (TEACHING,COURSE,"Docencia por curso","Docencia"):
        values=[data.get(k) for k in TEACHING_HOURS]
        if any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=10000 for v in values) or abs(sum(values)-clean["total_hours"])>0.000001:
            raise Invalid("Las horas lectivas y no lectivas deben sumar las horas totales.")
        clean.update(zip(TEACHING_HOURS,values))
    if clean["public_employee"]:
        for key in ("public_schedule","public_period"):
            clean[key]=string(data,key,key,1000)
    if clean["category"]!=TEACHING:
        clean["travel"]=string(data,"travel","viáticos",10)
        if clean["travel"] not in ("sí","no"):
            raise Invalid("Indica si considera viáticos.")
        if clean["travel"]=="sí":
            clean["travel_reason"]=string(data,"travel_reason","detalle de viáticos",1000)

def validate_finance(data,start,end):
    amount = data.get("amount")
    if type(amount) is not int or not 0 < amount <= 999999999999:
        raise Invalid("Indica un total bruto en pesos chilenos enteros.")
    installments = data.get("installments")
    if not isinstance(installments,list) or not 1 <= len(installments) <= 12:
        raise Invalid("Agrega de una a doce cuotas.")
    seen, amounts, total = set(), set(), 0
    parts = []
    for item in installments:
        if not isinstance(item,dict):
            raise Invalid("Formato de cuota inválido.")
        month, value = item.get("month"), item.get("amount")
        if not isinstance(month,str) or not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])",month) or not start.strftime("%Y-%m") <= month <= end.strftime("%Y-%m") or month in seen:
            raise Invalid("Las cuotas deben corresponder a meses distintos dentro de la prestación.")
        if type(value) is not int or not 0 < value <= amount:
            raise Invalid("Cada cuota debe tener un monto entero positivo.")
        if value in amounts:
            raise Invalid("Los montos de las cuotas deben ser distintos en este piloto.")
        seen.add(month)
        amounts.add(value)
        total += value
        parts.append({"month":month,"amount":value})
    if total != amount:
        raise Invalid("La suma de las cuotas debe coincidir con el monto bruto.")
    return amount, sorted(parts,key=lambda part:part["month"])

def required_docs(payload):
    return set(INITIAL_DOCS)

def check_file(file):
    if not 5 <= file.size <= 8*1024*1024 or Path(file.name).suffix.lower() != ".pdf" or file.read(5)!=b"%PDF-":
        raise Invalid("Cada archivo debe ser un PDF de hasta 8 MB.")
    file.seek(0)

def intake_files(request, payload, existing=()):
    required = required_docs(payload)
    allowed = set(INITIAL_DOCS) | {"permiso","declaracion","otros"}
    if set(request.FILES)-allowed or any(len(request.FILES.getlist(k))!=1 for k in request.FILES):
        raise Invalid("Envía un PDF por tipo de antecedente.")
    missing = required - set(request.FILES) - set(existing)
    if missing:
        names = INITIAL_DOCS | {"permiso":"respaldo de autorización para labores remuneradas","declaracion":"declaración de función pública"}
        raise Invalid("Faltan PDF: "+", ".join(names[k] for k in sorted(missing))+".")
    for file in request.FILES.values():
        check_file(file)
