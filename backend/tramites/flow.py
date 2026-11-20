STAGES = [
    ("intake", "Solicitud y antecedentes", "requirente"),
    ("documental", "Revisión documental DEA", "secretaria_dea"),
    ("presupuesto", "Disponibilidad presupuestaria", "direccion_dea"),
    ("academica", "Dirección Académica", "academica"),
    ("decanato", "Decanato", "decanato"),
    ("elaboracion", "Elaboración del convenio", "personas"),
    ("firma_prestador", "Firma del prestador", "requirente"),
    ("firma_autoridad", "Firma de autoridad", "personas"),
    ("contraloria", "Contraloría", "personas"),
    ("boletas", "Boleta e informe de servicios", "requirente"),
    ("contabilidad", "Revisión de Contabilidad", "contabilidad"),
    ("pago", "Pago y cierre", "contabilidad"),
]
SPECIALTIES = {"pregrado": "Pregrado", "postgrado": "Postgrado"}
ROLES = {
    "requirente": "Unidad requirente", "secretaria_dea": "Secretaría DEA", "direccion_dea": "Dirección DEA",
    "academica": "Dirección Académica", "decanato": "Decanato", "personas": "Gestión de Personas",
    "contabilidad": "Contabilidad", **SPECIALTIES,
}
REVIEW = {"documental", "presupuesto", "academica", "decanato", "contabilidad"}
INITIAL_DOCS = {"memo": "Memo o respaldo de la unidad", "identidad": "Identificación", "cv": "Currículum", "titulo": "Título, grado o respaldo de experticia"}
STAGE_DOCS = {
    "elaboracion": {"convenio": "Convenio elaborado", "declaracion_simple":"Declaración jurada simple", "declaracion_consanguinidad":"Declaración jurada de consanguinidad"},
    "firma_prestador": {"firma_prestador": "Convenio firmado por el prestador", "declaracion_simple_firmada":"Declaración simple firmada", "declaracion_consang_firmada":"Declaración de consanguinidad firmada"},
    "firma_autoridad": {"firma_autoridad": "Convenio firmado por la autoridad"},
    "contraloria": {"decreto": "Decreto tramitado"},
    "boletas": {"boleta": "Boleta", "informe": "Informe de prestación"},
    "pago": {"comprobante": "Comprobante de pago"},
}
