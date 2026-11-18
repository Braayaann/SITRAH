import json
from shutil import copyfileobj
from tempfile import SpooledTemporaryFile
from zipfile import ZipFile
from functools import wraps
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import RequestDataTooBig, TooManyFilesSent
from django.db import IntegrityError, connection, transaction
from django.db.models import Q
from django.http import FileResponse, JsonResponse
from django.middleware.csrf import get_token
from django.utils import timezone
from .flow import STAGES, SPECIALTIES, ROLES, REVIEW, STAGE_DOCS, INITIAL_DOCS
from .models import Case, Consultation, Document, Event, Installment, Profile, Unit
from .validation import Invalid, string, read_date, validate_payload, intake_files, check_file, validate_bank, validate_finance, TEACHING, TEACHING_HOURS

INDEX = {s[0]: i for i,s in enumerate(STAGES)}
STAGE_ROLES = {key: role for key, _, role in STAGES}
BANK_EDITORS = {"secretaria_dea","direccion_dea"}
FINANCIAL = {"amount","cost_center","start","end","category",*TEACHING_HOURS}
ACADEMIC = {"category","start","end","work","justification","supervisor","service_location","provider","identifier","identity_type",*TEACHING_HOURS}

def api(*methods, auth=True):
    def decorate(fn):
        @wraps(fn)
        def call(request, *args, **kwargs):
            try:
                if request.method not in methods:
                    raise Invalid("Método no permitido.",405)
                if auth and not profile(request):
                    raise Invalid("Inicia sesión para continuar.",401)
                result=fn(request,*args,**kwargs)
                result["Cache-Control"]="private, no-store"
                return result
            except Invalid as e:
                return JsonResponse({"error":e.message},status=e.status)
            except (json.JSONDecodeError, UnicodeDecodeError):
                return JsonResponse({"error":"Solicitud JSON inválida."},status=400)
            except (RequestDataTooBig, TooManyFilesSent):
                return JsonResponse({"error":"La solicitud supera el límite de carga."},status=413)
            except IntegrityError:
                return JsonResponse({"error":"El registro ya existe o cambió. Actualiza el expediente."},status=409)
        return call
    return decorate

def profile(request):
    if not request.user.is_authenticated:
        return None
    try:
        p = request.user.profile
        return p if p.role in ROLES else None
    except Profile.DoesNotExist:
        return None

def body(request, multipart=False):
    data = json.loads(request.POST.get("data","{}") if multipart else request.body or b"{}")
    if not isinstance(data,dict):
        raise Invalid("Formato inválido.")
    return data

@api("GET",auth=False)
def health(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"status":"ok"})

def context(request):
    p = profile(request)
    return {"user": {"name":request.user.get_full_name() or request.user.username, "role":p.role, "unit":p.unit_id} if p else None,
        "roles":ROLES,"stages":STAGES,"specialties":SPECIALTIES,"demo":settings.SITRAH_DEMO,
        "csrf":get_token(request), "intake_open":timezone.localdate().month!=2,
        "units":list(Unit.objects.filter(Q(active=True)|Q(pk=p.unit_id)).values("id","name")) if p else []}

@api("GET",auth=False)
def session(request):
    return JsonResponse(context(request))

@api("POST",auth=False)
def sign_in(request):
    data = body(request)
    user = authenticate(request, username=string(data,"username","usuario",150),password=string(data,"password","contraseña",200))
    if not user or not Profile.objects.filter(user=user,role__in=ROLES).exists():
        raise Invalid("Usuario o contraseña incorrectos.",401)
    login(request,user)
    return JsonResponse(context(request))

@api("POST")
def sign_out(request):
    logout(request)
    return JsonResponse(context(request))

def scope(p):
    if p.role=="requirente":
        return Case.objects.filter(unit_id=p.unit_id)
    if p.role in SPECIALTIES:
        return Case.objects.filter(consultations__specialty=p.role).distinct()
    return Case.objects.all()

def fetch(request, pk, lock=False):
    visible = scope(profile(request)).filter(pk=pk)
    if not visible.exists():
        raise Invalid("Expediente no encontrado.",404)
    qs = Case.objects.select_for_update() if lock else Case.objects
    return qs.get(pk=pk)

def can_act(c,p):
    if c.closed_at:
        return False
    if p.role in SPECIALTIES:
        return c.stage=="academica" and c.consultations.filter(specialty=p.role,decision="pending").exists()
    return STAGE_ROLES.get(c.stage)==p.role

def summary(c,p):
    return {"id":c.pk,"number":c.number,"unit":c.unit.name,"provider":c.payload["provider"],"category":c.payload["category"],
        "amount":c.payload["amount"],"stage":c.stage,"stage_since":c.stage_since,"returned_from":c.returned_from,
        "closed_at":c.closed_at,"agreement":c.agreement,"decree":c.decree,"pending":can_act(c,p)}

def record(c,user,action,note="",dest=None):
    Event.objects.create(case=c,actor=user,action=action,note=note,origin=c.stage,destination=dest or c.stage)
    if dest and dest!=c.stage:
        c.stage,c.stage_since=dest,timezone.now()
    c.version+=1
    c.save()

def add_file(c,user,kind,f,part=None):
    Document.objects.create(case=c,kind=kind,name=f.name,file=f,uploaded_by=user,installment=part)

@api("GET","POST")
def cases(request):
    p=profile(request)
    if request.method=="GET":
        return JsonResponse({"cases":[summary(c,p) for c in scope(p).select_related("unit").order_by("-created_at")]})
    if p.role!="requirente" or not p.unit_id or not p.unit.active:
        raise Invalid("Tu perfil no puede crear solicitudes para esta unidad.",403)
    if timezone.localdate().month==2:
        raise Invalid("En febrero no se reciben solicitudes nuevas.")
    data=body(request,multipart=True)
    clean,parts=validate_payload(data)
    bank=validate_bank(data.get("bank",{}))
    intake_files(request,clean)
    with transaction.atomic():
        c=Case.objects.create(unit=p.unit,created_by=request.user,payload=clean,bank=bank,stage="intake")
        Installment.objects.bulk_create([Installment(case=c,**x) for x in parts])
        for kind,f in request.FILES.items():
            add_file(c,request.user,kind,f)
        record(c,request.user,"Solicitud ingresada",dest="documental")
        if bank:
            record(c,request.user,"Datos bancarios ingresados")
    return JsonResponse({"id":c.pk,"number":c.number},status=201)

@api("GET")
def detail(request,pk):
    c,p=fetch(request,pk),profile(request)
    special=p.role in SPECIALTIES
    payload={k:v for k,v in c.payload.items() if k in {"provider","category","work","start","end","amount"}} if special else c.payload
    docs=c.documents.all()
    if special:
        docs=docs.filter(kind__in=("memo","titulo"))
    cons=c.consultations.all()
    if special:
        cons=cons.filter(specialty=p.role)
    bank_visible=p.role in BANK_EDITORS or (p.role=="contabilidad" and bool(c.decree))
    out=summary(c,p)|{"data":payload,"version":c.version,"review_queue":c.review_queue,
        "analyst":(c.analyst.get_full_name() or c.analyst.username) if c.analyst_id and not special else None,
        "bank":c.bank if bank_visible else None,"can_edit_bank":p.role in BANK_EDITORS and not c.closed_at,
        "can_download_bundle":p.role=="personas" and INDEX.get(c.stage,99)>=INDEX["elaboracion"],
        "consultations":list(cons.order_by("id").values("id","specialty","question","decision","answer","created_at","answered_at")),
        "documents":list(docs.order_by("-id").values("id","kind","name","installment_id","created_at")),
        "installments":list(c.installments.order_by("month").values("id","month","amount","paid_on")) if not special else [],
        "events":[{"actor":e.actor.get_full_name() or e.actor.username,"action":e.action,"origin":e.origin,"destination":e.destination,"note":e.note,"created_at":e.created_at} for e in c.events.select_related("actor").order_by("-id")] if not special else []}
    return JsonResponse(out)

def require_current(request,c,data):
    if not can_act(c,profile(request)):
        raise Invalid("Tu perfil no puede actuar en esta etapa.",403)
    if data.get("version")!=c.version:
        raise Invalid("El expediente cambió. Actualiza antes de continuar.",409)

@api("POST")
@transaction.atomic
def correct(request,pk):
    c,data=fetch(request,pk,lock=True),body(request,multipart=True)
    require_current(request,c,data)
    if c.stage!="intake" or not c.returned_from:
        raise Invalid("No hay una devolución pendiente.")
    clean,parts=validate_payload(data)
    intake_files(request,clean,c.documents.values_list("kind",flat=True))
    old_parts=list(c.installments.order_by("month").values("month","amount"))
    # Conservar el cálculo interno cuando la corrección no cambia sus insumos.
    teacher_unchanged=clean["category"]==c.payload["category"]==TEACHING and all(
        clean.get(k)==c.payload.get(k) for k in ("start","end",*TEACHING_HOURS))
    if teacher_unchanged:
        clean["amount"],parts=c.payload["amount"],old_parts
    changed={k for k in set(clean)|set(c.payload) if clean.get(k)!=c.payload.get(k)}
    finance_changed=bool(changed & FINANCIAL) or parts!=old_parts
    academic_changed=bool(changed & ACADEMIC) or bool(set(request.FILES)&{"titulo","memo","identidad"})
    previous={c.returned_from,*(k for k in c.review_queue if k in REVIEW)}
    redo=set(previous)
    if finance_changed:
        redo.add("presupuesto")
    if academic_changed:
        redo.add("academica")
    if request.FILES or changed - (FINANCIAL|ACADEMIC) or changed & {"provider","identifier","identity_type"}:
        redo.add("documental")
    # Después de la última revisión previamente alcanzada se retoma el flujo normal.
    # Los pasos posteriores al punto de devolución aún no estaban aprobados.
    end=max(INDEX[k] for k in previous)
    queue=sorted((k for k in redo if INDEX[k]<=end),key=INDEX.__getitem__)
    queue.append(STAGES[end+1][0])
    c.payload=clean
    if parts!=old_parts:
        c.installments.all().delete()
        Installment.objects.bulk_create([Installment(case=c,**x) for x in parts])
    for kind,f in request.FILES.items():
        add_file(c,request.user,kind,f)
    c.returned_from=""
    dest,*c.review_queue=queue
    record(c,request.user,"Solicitud corregida",dest=dest)
    return JsonResponse({"id":c.pk})

@api("POST")
@transaction.atomic
def action(request,pk):
    c,data,p=fetch(request,pk,lock=True),body(request),profile(request)
    operation = data.get("action")
    if operation=="bank":
        if p.role not in BANK_EDITORS or c.closed_at:
            raise Invalid("Tu perfil no puede modificar los datos bancarios.",403)
        if data.get("version")!=c.version:
            raise Invalid("El expediente cambió. Actualiza antes de continuar.",409)
        bank=validate_bank(data.get("bank"))
        if bank!=c.bank:
            c.bank=bank
            record(c,request.user,"Datos bancarios actualizados")
        return JsonResponse({"id":c.pk,"version":c.version})
    require_current(request,c,data)
    note=string(data,"note","observación",2000,False)
    if operation=="claim":
        if c.stage!="elaboracion" or p.role!="personas":
            raise Invalid("Solo Gestión de Personas puede tomar el expediente en elaboración.",403)
        if c.analyst_id and c.analyst_id!=request.user.pk:
            raise Invalid("El expediente ya tiene un analista asignado.",409)
        if not c.analyst_id:
            c.analyst=request.user
            record(c,request.user,"Analista asignado")
    elif operation=="finance":
        if c.stage!="presupuesto" or c.payload["category"]!=TEACHING:
            raise Invalid("El cálculo docente corresponde a la revisión presupuestaria.",403)
        amount,parts=validate_finance(data,read_date(c.payload["start"],"inicio"),read_date(c.payload["end"],"término"))
        c.payload["amount"]=amount
        c.installments.all().delete()
        Installment.objects.bulk_create([Installment(case=c,**x) for x in parts])
        record(c,request.user,"Cálculo docente registrado")
    elif operation=="consult":
        if c.stage!="academica" or p.role!="academica":
            raise Invalid("Solo Dirección Académica puede solicitar consultas.",403)
        specialty=data.get("specialty")
        if not isinstance(specialty,str) or specialty not in SPECIALTIES or not note:
            raise Invalid("Selecciona una dirección e indica qué debe revisar.")
        if c.consultations.filter(specialty=specialty,decision="pending").exists():
            raise Invalid("Ya existe una consulta pendiente para esta dirección.",409)
        Consultation.objects.create(case=c,specialty=specialty,question=note,requested_by=request.user)
        record(c,request.user,"Consulta a "+SPECIALTIES[specialty],note)
    elif operation=="reply":
        decision=data.get("decision")
        if p.role not in SPECIALTIES or decision not in ("approved","observed") or (decision=="observed" and not note):
            raise Invalid("Elige el resultado. Las observaciones requieren un motivo.")
        q=c.consultations.filter(pk=data.get("consultation") if type(data.get("consultation")) is int else None,specialty=p.role,decision="pending").first()
        if not q:
            raise Invalid("Consulta pendiente no encontrada.",404)
        q.decision,q.answer,q.answered_at,q.answered_by=decision,note,timezone.now(),request.user
        q.save()
        record(c,request.user,"Respuesta de "+SPECIALTIES[p.role],("Visto bueno. " if decision=="approved" else "Con observaciones. ")+note)
    elif operation=="return":
        if p.role in SPECIALTIES or c.stage not in REVIEW or not note:
            raise Invalid("La devolución requiere una etapa de revisión y un motivo.")
        c.consultations.filter(decision="pending").update(decision="cancelled",answered_at=timezone.now())
        if c.stage=="contabilidad":
            record(c,request.user,"Respaldos devueltos a la unidad",note,"boletas")
        else:
            c.returned_from=c.stage
            record(c,request.user,"Solicitud devuelta a la unidad",note,"intake")
    elif operation=="pay":
        if c.stage!="pago":
            raise Invalid("El expediente no está en pago.")
        if not c.bank or data.get("bank_verified") is not True:
            raise Invalid("Confirma los datos bancarios vigentes antes de registrar el pago.")
        part=c.installments.filter(pk=data.get("installment") if type(data.get("installment")) is int else None).first()
        if not part or part.paid_on or not c.documents.filter(installment=part,kind="comprobante").exists():
            raise Invalid("La cuota debe estar pendiente y contar con comprobante.")
        day=read_date(data.get("paid_on"),"pago")
        if day>timezone.localdate():
            raise Invalid("La fecha de pago no puede ser futura.")
        part.paid_on=day
        part.save(update_fields=["paid_on"])
        if not c.installments.filter(paid_on__isnull=True).exists():
            c.closed_at=timezone.now()
        record(c,request.user,"Cuota pagada: "+part.month,day.isoformat()+(" · "+note if note else ""), "closed" if c.closed_at else None)
    elif operation=="advance":
        if p.role in SPECIALTIES or c.stage in ("intake","pago"):
            raise Invalid("No se puede avanzar con esta acción.",403)
        if c.stage=="academica":
            if c.consultations.filter(decision="pending").exists():
                raise Invalid("Espera las respuestas de las direcciones consultadas.",409)
            if c.consultations.filter(decision="observed",created_at__gte=c.stage_since).exists() and not note:
                raise Invalid("Indica cómo se resolvieron las observaciones antes de visar.")
        if c.stage=="presupuesto" and (not c.payload["amount"] or not c.installments.exists()):
            raise Invalid("Registra el monto y las cuotas antes de aprobar el presupuesto.")
        required=STAGE_DOCS.get(c.stage,{})
        if c.stage=="firma_prestador":
            # Los expedientes que ya salieron de elaboración conservan sus requisitos originales.
            originals={"declaracion_simple_firmada":"declaracion_simple","declaracion_consang_firmada":"declaracion_consanguinidad"}
            required={k:v for k,v in required.items() if k not in originals or c.documents.filter(kind=originals[k]).exists()}
        if c.stage=="boletas":
            if any(not set(required)<=set(c.documents.filter(installment=i).values_list("kind",flat=True)) for i in c.installments.all()):
                raise Invalid("Adjunta boleta e informe para cada cuota.")
            if c.events.filter(action="Respaldos devueltos a la unidad",created_at__lte=c.stage_since).exists() and not c.documents.filter(kind__in=required,created_at__gte=c.stage_since).exists():
                raise Invalid("Adjunta el respaldo corregido antes de reenviar a Contabilidad.")
        elif not set(required)<=set(c.documents.filter(installment__isnull=True).values_list("kind",flat=True)):
            raise Invalid("Falta adjuntar el PDF requerido para esta etapa.")
        if c.stage=="elaboracion":
            c.agreement=string(data,"agreement","número de convenio",80)
            if not c.analyst_id:
                c.analyst=request.user
        if c.stage=="contraloria":
            c.decree=string(data,"decree","número de decreto",80)
        dest=c.review_queue.pop(0) if c.review_queue else STAGES[INDEX[c.stage]+1][0]
        record(c,request.user,"Etapa completada",note,dest)
    else:
        raise Invalid("Acción desconocida.")
    return JsonResponse({"id":c.pk,"version":c.version})

@api("POST")
@transaction.atomic
def upload(request,pk):
    c=fetch(request,pk,lock=True)
    try:
        version=int(request.POST.get("version",""))
    except ValueError:
        raise Invalid("Actualiza el expediente.")
    require_current(request,c,{"version":version})
    kind=request.POST.get("kind","")
    if kind not in STAGE_DOCS.get(c.stage,{}):
        raise Invalid("Este documento no corresponde a la etapa.")
    part=None
    if c.stage in ("boletas","pago"):
        try:
            part=c.installments.get(pk=int(request.POST.get("installment","")),paid_on__isnull=True)
        except (ValueError,Installment.DoesNotExist):
            raise Invalid("Selecciona una cuota pendiente.")
    f=request.FILES.get("file")
    if not f or len(request.FILES.getlist("file"))!=1:
        raise Invalid("Selecciona un PDF.")
    check_file(f)
    add_file(c,request.user,kind,f,part)
    record(c,request.user,"Documento adjuntado: "+STAGE_DOCS[c.stage][kind]+(" · "+part.month if part else ""))
    return JsonResponse({"id":c.pk},status=201)

@api("GET")
def bundle(request,pk):
    c=fetch(request,pk)
    if profile(request).role!="personas" or INDEX.get(c.stage,99)<INDEX["elaboracion"]:
        raise Invalid("La descarga conjunta se habilita a Gestión de Personas tras las visaciones.",403)
    allowed=set(INITIAL_DOCS)|{"permiso","otros"}
    archive=SpooledTemporaryFile(max_size=1024*1024)
    try:
        with ZipFile(archive,"w") as out:
            seen=set()
            for doc in c.documents.filter(kind__in=allowed).order_by("-id"):
                if doc.kind not in seen:
                    with doc.file.open("rb") as source, out.open(doc.kind+".pdf","w") as dest:
                        copyfileobj(source,dest)
                    seen.add(doc.kind)
        if not seen:
            raise Invalid("No hay antecedentes adjuntos para descargar.",404)
        archive.seek(0)
    except FileNotFoundError:
        archive.close()
        raise Invalid("Uno de los antecedentes ya no está disponible.",404)
    except Exception:
        archive.close()
        raise
    return FileResponse(archive,as_attachment=True,filename=c.number+"-antecedentes.zip",content_type="application/zip")

@api("GET")
def download(request,pk):
    d=Document.objects.filter(pk=pk,case__in=scope(profile(request))).first()
    if not d or (profile(request).role in SPECIALTIES and d.kind not in ("memo","titulo")):
        raise Invalid("Documento no encontrado.",404)
    try:
        return FileResponse(d.file.open("rb"),as_attachment=True,filename=d.name,content_type="application/pdf",headers={"Cache-Control":"private, no-store"})
    except FileNotFoundError:
        raise Invalid("El archivo no está disponible.",404)
