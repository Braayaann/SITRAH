# SITRAH · Guía de incorporación al proyecto

**Para:** integrante que se suma al desarrollo · **Versión:** 0.2 · **Actualizada:** 17 de noviembre de 2026

## 1. Qué estamos construyendo

SITRAH es el Sistema de Tramitación de Honorarios de la Facultad de Filosofía y Humanidades de la Universidad de Chile. Centraliza la solicitud, los documentos, las revisiones y el seguimiento hasta el pago. La unidad requirente puede ver el estado de sus propios expedientes sin tener que preguntar por correo en qué etapa están.

La primera maqueta tomó como referencia la bandeja de solicitudes del sistema de compras. Después, el equipo revisó el formulario con la Facultad y Roberto confirmó por correo el orden principal: **primero revisión documental de la DEA, luego presupuesto, después Dirección Académica y finalmente Decanato**. La reunión del 12 de noviembre precisó el cálculo docente, las fechas, los datos bancarios y los documentos. Las conversaciones posteriores aclararon cómo aplicar las devoluciones y quién da el visto bueno cuando hay una consulta académica.

**DEA** significa Dirección Económica y Administrativa. En SITRAH interviene con dos perfiles: **Secretaría DEA**, que revisa antecedentes, y **Dirección DEA**, que valida el presupuesto. «Visar» significa dar el visto bueno de una etapa dentro de SITRAH. Se distingue de la firma formal del convenio.

## 2. Flujo y responsables

Cada área da su propio visto bueno en la etapa que le corresponde. El sistema habilita el paso siguiente con esa acción; la DEA no visa por Académica ni por Decanato.

| N.º | Etapa | Responsable y acción |
| --- | --- | --- |
| 1 | Solicitud y antecedentes | La **unidad requirente** completa el formulario y adjunta los respaldos. Se genera el número de solicitud SITRAH. |
| 2 | Revisión documental | **Secretaría DEA** verifica que los antecedentes estén completos; visa o devuelve con un motivo. |
| 3 | Disponibilidad presupuestaria | **Dirección DEA** valida financiamiento y centro de costo. En docencia por jerarquía registra primero el cálculo interno y las cuotas. |
| 4 | Dirección Académica | **Académica** revisa la pertinencia y visa o devuelve. Puede pedir una consulta opcional dentro de esta misma etapa. |
| 5 | Decanato | **Decanato** registra su propia autorización o devuelve con observaciones. |
| 6 | Elaboración | **Gestión de Personas** puede tomar el expediente, descargar los antecedentes juntos y elaborar el convenio en el sistema universitario. Registra el número de convenio y adjunta el PDF con las declaraciones juradas. |
| 7 | Firma del prestador | La **unidad requirente** coordina la firma y devuelve el convenio y las declaraciones firmadas, en PDF. |
| 8 | Firma de autoridad | **Gestión de Personas** registra la firma de la autoridad y adjunta su respaldo. |
| 9 | Contraloría | El trámite ocurre fuera de SITRAH. **Gestión de Personas** registra el resultado y adjunta el decreto con su número. |
| 10 | Boleta e informe | La **unidad requirente** adjunta la boleta y el informe de prestación por cuota. La boleta debe identificar el decreto. |
| 11 | Revisión contable | **Contabilidad** verifica los respaldos y puede pedir que la unidad corrija un documento. |
| 12 | Pago y cierre | **Contabilidad** confirma los datos bancarios vigentes, adjunta el comprobante y registra la fecha del pago por cuota. El expediente se cierra cuando se registran todas las cuotas. |

**Número de solicitud, número de convenio y número de decreto son distintos.** El primero identifica el expediente en SITRAH; el segundo identifica el convenio elaborado en el sistema universitario; el tercero corresponde al decreto y se usa en la boleta.

### Consulta académica opcional

Académica puede visar sin consultar. Si necesita una revisión adicional, solicita un visto bueno a **Extensión, Pregrado o Postgrado** desde el expediente. Puede consultar a más de una dirección. Cada una responde en el sistema y su respuesta queda registrada. Mientras haya respuestas pendientes, el expediente sigue en Académica.

**La respuesta de una dirección consultada no envía el expediente a Decanato.** Académica revisa el resultado, resuelve las observaciones o devuelve si hace falta, y da su propio visto bueno. Decanato luego hace su revisión por separado.

### Qué pasa si se devuelve una solicitud

La unidad corrige, el sistema retoma la etapa que devolvió y repite las revisiones anteriores afectadas:

| Corrección | Ejemplo de recorrido |
| --- | --- |
| Falta un PDF en la revisión inicial | Unidad → Secretaría DEA → continúa su trámite normal. |
| Académica pide cambiar las horas | Unidad → Dirección DEA recalcula y vuelve a validar → Académica vuelve a revisar. |
| Decanato observa solo el monto | Unidad → Dirección DEA vuelve a validar → Decanato. No se repite Académica si no se cambió nada que deba revisar. |
| Contabilidad observa una boleta | Unidad adjunta el PDF corregido → Contabilidad. No vuelve a etapas académicas. |
| Se corrige únicamente la cuenta bancaria | La DEA actualiza el dato sin mover el expediente. Contabilidad verifica la cuenta vigente antes del pago. |

## 3. Reglas del formulario y los documentos

- **Docencia por jerarquía:** el requirente informa horas lectivas y no lectivas. Envía sin indicar bruto ni cuotas. La DEA hace el cálculo con sus criterios internos y Dirección DEA registra el resultado en la revisión presupuestaria antes de visar. SITRAH no aplica una tabla de tarifas ni calcula antigüedad automáticamente.
- **Docencia por curso y otras actividades:** la unidad registra el monto bruto en pesos chilenos y los meses y montos de cada cuota. No se ingresan cuotas para meses sin pago. La suma tiene que cuadrar con el total informado. El piloto valida que los montos de las cuotas sean distintos.
- **Fechas:** inicio y término dentro del mismo año calendario. Se quitó el tope automático de seis meses; la revisión del plazo es manual. En febrero se bloquea el ingreso de solicitudes nuevas, no los pagos.
- **Datos del prestador:** identificación por RUT o pasaporte, contacto, domicilio y nacionalidad. Si se informa un vínculo con otra institución pública, se despliegan campos adicionales.
- **Documentos iniciales:** memo o respaldo de la unidad, identificación, CV y título, grado o acreditación de experticia. Las declaraciones juradas que acompañan al convenio se incorporan en elaboración y se devuelven firmadas; no se exigen al ingresar la solicitud.
- **Datos bancarios:** el requirente puede ingresarlos al crear la solicitud o indicar que están pendientes. Secretaría DEA y Dirección DEA pueden consultar, completar o corregir la información de expedientes abiertos. Contabilidad la consulta tras el decreto. Académica, Decanato y las direcciones consultadas no ven esos datos. La auditoría registra quién hizo el cambio y cuándo, sin copiar el número de cuenta al historial.
- **Visibilidad:** el requirente accede a expedientes de su unidad y puede seguir su avance. Un perfil consultado accede a sus propias consultas y a un resumen restringido del expediente. Gestión de Personas puede descargar los antecedentes juntos cuando llega la etapa de elaboración.

## 4. Cómo levantarlo y probarlo

Con Docker Desktop abierto, entra desde PowerShell a la carpeta del proyecto y ejecuta:

```powershell
docker compose up --build
```

Abre [http://localhost:8080](http://localhost:8080). En el modo de demostración (`SITRAH_DEMO=1`, predeterminado para desarrollo) todas las cuentas de abajo usan **`Sitrah-Demo-2026`**. Usa solo datos ficticios.

| Usuario | Para qué usarlo |
| --- | --- |
| `requirente` | Crear una solicitud, corregirla, subir los PDF firmados y entregar boletas e informes. |
| `secretaria_dea` | Revisar requisitos, devolver o visar. También puede completar datos bancarios. |
| `direccion_dea` | Registrar cálculo docente, aprobar presupuesto y gestionar datos bancarios. |
| `academica` | Consultar a otra dirección, revisar la respuesta y dar el visto bueno académico. |
| `extension`, `pregrado`, `postgrado` | Responder una consulta que les fue asignada. |
| `decanato` | Dar el visto bueno de Decanato. |
| `personas` | Tomar expediente, descargar el ZIP de antecedentes, registrar el convenio, firmas y decreto. |
| `contabilidad` | Verificar boletas, informes y cuenta bancaria; registrar los pagos. |
| `admin` | Consultar expedientes para seguimiento. En el piloto no equivale a una interfaz completa de administración de usuarios. |

**Demostración recomendada:** crea una solicitud de docencia por jerarquía con 20 horas lectivas y 5 no lectivas, RUT de prueba `12.345.678-5`, fechas de agosto a noviembre del mismo año y PDF ficticios. Como Secretaría DEA, visa los antecedentes. Como Dirección DEA, comprueba que no puedes visar hasta cargar el cálculo; puedes usar un bruto ficticio de $310.000 y dos cuotas de $160.000 y $150.000. Como Académica, consulta a Pregrado; responde con `pregrado` y vuelve a `academica` para comprobar que todavía debe visar antes de que Decanato la reciba. Para continuar hasta el cierre, usa el orden y los documentos de la tabla de etapas.

```powershell
docker compose ps
docker compose logs --tail=80 backend
docker compose exec backend python manage.py test
docker compose down
```

El arranque aplica las migraciones. La base y los archivos usan volúmenes separados; `docker compose down` los conserva. Si el navegador no carga, revisa `docker compose ps` y [la API de salud](http://localhost:8080/api/health/). No uses `docker compose down -v` si quieres conservar las solicitudes, los usuarios y sus documentos.

**Última comprobación (17 de noviembre de 2026):** los tres servicios de Compose estaban en ejecución, PostgreSQL estaba saludable, la API respondió `ok` y las seis pruebas de Django pasaron dentro del contenedor con una base de pruebas PostgreSQL separada.

## 5. Dónde cambiar qué

| Archivo o carpeta | Qué encontrarás |
| --- | --- |
| [compose.yaml](compose.yaml) | Servicios frontend, backend y PostgreSQL; puerto local y volúmenes. |
| [frontend/src/main.jsx](frontend/src/main.jsx) | Interfaz React: login, bandejas, formulario, expediente y acciones. |
| [backend/tramites/flow.py](backend/tramites/flow.py) | Catálogo de etapas, perfiles y documentos por etapa. |
| [backend/tramites/views.py](backend/tramites/views.py) | API de sesión, permisos, devoluciones, consultas, documentos y pagos. |
| [backend/tramites/validation.py](backend/tramites/validation.py) | Validaciones del formulario, cuotas y datos bancarios. |
| [backend/tramites/models.py](backend/tramites/models.py) | Expediente, documentos, cuotas, consultas y eventos de auditoría. |
| [backend/tramites/tests.py](backend/tramites/tests.py) | Pruebas del flujo completo y de los permisos y reglas críticas. |
| [README.md](README.md) | Instrucciones técnicas de arranque, actualización y configuración. |

Al ajustar una regla del flujo, revisa **la API y la interfaz**. Ocultar un botón no basta para limitar un permiso: la API debe rechazar la operación. Si cambias el modelo, incluye la migración correspondiente.

## 6. Qué queda pendiente

- Confirmar el catálogo institucional de unidades, la nómina de accesos y si se necesita una interfaz para administrarlos. El piloto usa perfiles y cuentas locales; falta definir el acceso institucional.
- Ratificar excepciones al calendario, requisitos documentales por tipo de convenio, reglas de cuotas y si se incorporará la tabla institucional de tarifas docentes.
- Confirmar si Contabilidad debe tramitar una cuota mientras aún faltan respaldos de otras. El piloto pide los respaldos de todas las cuotas antes de la revisión contable, aunque registra cada pago por separado.
- Definir la exportación con formato institucional, las notificaciones, los reportes avanzados y las integraciones que se decida incorporar. La elaboración oficial, la firma, Contraloría y el pago efectivo hoy se realizan fuera de SITRAH.
- Antes de usar expedientes reales, resolver configuración de producción, acceso institucional, protección y respaldo de datos y archivos, y las políticas acordadas con la Facultad.
