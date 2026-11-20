# SITRAH · Sistema de Tramitación de Honorarios

Primera versión local para la Facultad de Filosofía y Humanidades de la Universidad de Chile. Incluye frontend React, API Django, PostgreSQL y un proxy Nginx. El código usa los materiales de la segunda reunión como referencia y el correo de Roberto como confirmación del orden. Los datos de demostración son ficticios.

Si te estás incorporando al equipo, empieza por la [guía de incorporación](GUIA-INCORPORACION.md): contexto, acuerdos, flujo, perfiles y pasos para probar la versión actual.

## Versión 0.2 · Acuerdos de la reunión del 12 de noviembre

- **Docencia por jerarquía:** la unidad indica las horas lectivas y no lectivas y envía sin monto ni cuotas. En Disponibilidad presupuestaria, el perfil Dirección DEA registra el cálculo que realizó la DEA y luego visa. Las tarifas no se calculan automáticamente.
- **Docencia por curso y otras actividades:** la unidad registra el bruto y las cuotas por mes. Las fechas deben quedar dentro del mismo año; se eliminó el límite automático de seis meses. En febrero se bloquean solo las solicitudes nuevas.
- **Devoluciones:** la unidad corrige y reenvía. El sistema vuelve al área que devolvió y repite las revisiones anteriores afectadas: presupuesto si cambian horas, monto, cuotas o financiamiento; Académica si cambia la pertinencia o el respaldo académico; Secretaría DEA si cambian documentos o antecedentes administrativos. Una devolución de Contabilidad exige adjuntar un PDF corregido y vuelve directamente a Contabilidad.
- **Datos bancarios:** la unidad puede ingresarlos al crear la solicitud o dejarlos pendientes. Secretaría DEA y Dirección DEA pueden consultar, completar y corregir los datos de expedientes abiertos. Contabilidad los consulta una vez registrado el decreto y confirma los datos vigentes antes de registrar un pago. Los números de cuenta no se incluyen en el historial ni en el ZIP documental.
- **Gestión de Personas:** tras las visaciones se habilita la descarga conjunta de antecedentes y un analista puede tomar el expediente. Las declaraciones juradas se adjuntan en elaboración y se devuelven firmadas junto con el convenio; no se exigen al crear la solicitud.

Para actualizar una instalación de demostración anterior, conserva la misma carpeta o el mismo nombre de proyecto de Compose, copia los archivos nuevos y ejecuta `docker compose up --build`. Las migraciones agregan los campos sin reiniciar los volúmenes. Los expedientes anteriores conservan su tipo de docencia y los datos bancarios quedan pendientes si nunca se ingresaron; la DEA puede completarlos.

## Levantar con Docker

Requiere Docker Desktop en ejecución (contenedores Linux) o Docker Engine con Compose. Abre PowerShell dentro de la carpeta `sitrah` y ejecuta:

```powershell
docker compose up --build
```

Una vez iniciados los servicios, abre **http://localhost:8080**. Solo se expone el frontend en la interfaz local; PostgreSQL y Django están en la red interna de Compose. Las migraciones se aplican al iniciar. La base de datos y los documentos persisten en volúmenes distintos.

```powershell
docker compose ps
docker compose logs -f backend
docker compose exec backend python manage.py test
docker compose down
```

`docker compose down` conserva los volúmenes. La API de salud está en `/api/health/`. Si no carga enseguida, revisa el estado de los servicios y el registro del backend.

## Probar una solicitud

El formulario del requirente conserva las siete secciones del prototipo revisado el 12 de noviembre. En docencia por jerarquía se omite Financiamiento: la unidad informa horas y antecedentes, y Dirección DEA registra posteriormente el monto, centro de costo y cuotas. En docencia por curso o diplomado y otras actividades se informa el monto en CLP y se distribuye manualmente en una grilla mensual; los meses sin pago quedan vacíos y se muestran cantidad de cuotas, total y diferencia. Se mantienen las reglas del piloto sobre montos distintos y suma exacta.

La fecha se asigna en el servidor y la unidad proviene de la cuenta. El formulario incorpora jornada, horas semanales y totales, supervisión con RUT, viáticos condicionales y tipo de certificado. Los datos bancarios pueden quedar pendientes. Se solicitan al inicio memorando, CV, identificación y certificado; las declaraciones juradas se incorporan al elaborar el convenio. Un pasaporte no exige automáticamente un permiso laboral: los respaldos adicionales y la procedencia del circuito los revisa DEA. Estos ajustes reproducen la propuesta del formulario y no constituyen una aprobación institucional de los puntos pendientes.

Para verificar las reglas del formulario: `npm --prefix frontend test`. La compilación sigue usando `npm --prefix frontend run build`; las pruebas de la API se ejecutan con `python manage.py test` desde `backend/`.

Las cuentas aparecen en la pantalla de acceso con `SITRAH_DEMO=1` (valor local predeterminado). Todas usan la clave de ejemplo **Sitrah-Demo-2026**.

1. Ingresa como `requirente`. Completa el formulario por pasos y adjunta PDF ficticios. Usa por ejemplo el RUT de prueba `12.345.678-5`. Para probar una solicitud sin monto, selecciona «Docencia por jerarquía».
2. Ingresa como `secretaria_dea` y abre la solicitud de tu bandeja. Puedes devolver con un motivo o visar. Después, ingresa como `direccion_dea` y visa la disponibilidad presupuestaria.
3. Ingresa como `academica`. En «Acción» puedes solicitar aprobación a Pregrado (`pregrado`) o Postgrado (`postgrado`). Cambia a la cuenta correspondiente para responder y luego vuelve a `academica`. Puedes usar el expediente académico de demostración para probar esta rama sin completar el formulario.
4. Tras la visación de Académica y `decanato`, `personas` adjunta el convenio y ambas declaraciones, y registra el número de convenio. `requirente` devuelve los tres PDF firmados; `personas` registra la firma de autoridad y el decreto al terminar Contraloría.
5. La unidad adjunta boleta e informe por cada cuota. `contabilidad` revisa o devuelve los respaldos a la unidad; luego adjunta cada comprobante y registra la fecha de pago. El expediente cierra al registrar todas las cuotas.

**Consultas opcionales:** Dirección Académica puede visar directamente o consultar a Pregrado o Postgrado, según el caso. Puede abrir consultas simultáneas a distintas direcciones, con una pendiente como máximo por dirección. Cada dirección responde en SITRAH y ve sus propias consultas y un resumen con acceso limitado a documentos. La respuesta queda registrada como antecedente. Mientras haya consultas pendientes, el expediente permanece en Dirección Académica. Una vez respondidas, **solo el visto bueno de Dirección Académica envía el expediente a Decanato**, donde se requiere la visación propia de Decanato. Si una respuesta trae observaciones, Académica puede devolver la solicitud o dejar constancia de cómo las resolvió antes de visar. Esta es la regla acordada para el piloto.

## Alcance y decisiones por validar

Las consultas opcionales se asignan únicamente a Pregrado y Postgrado. Ambos perfiles usan la misma vista y solo pueden responder sus propias consultas. Se retiraron los roles Extensión y Administración de seguimiento; sus cuentas previas ya no permiten acceder a SITRAH. La migración cancela las consultas pendientes a Extensión con una anotación de actualización del sistema y conserva las respuestas anteriores y el historial.

- Se usa la misma ruta para docencia y otras actividades; no se han confirmado rutas alternativas. Las consultas opcionales no dependen automáticamente del tipo de convenio.
- Orden: solicitud → Secretaría DEA → presupuesto (Dirección DEA) → Académica → Decanato → elaboración → firma del prestador → firma de autoridad → Contraloría → boleta e informe → Contabilidad → pago y cierre. Cada unidad registra su visto bueno para habilitar el avance. Contraloría se registra internamente desde Gestión de Personas.
- La unidad se toma del perfil del usuario. Los departamentos ficticios son ejemplos; reemplazar con el catálogo institucional. Los perfiles internos se asignan por rol; las acciones se verifican en la API.
- El piloto valida RUT, fechas dentro de un año, monto total y cuotas mensuales de monto distinto. Quedan por ratificar el catálogo documental y las excepciones de docencia o proyectos. La tarifa docente, el cálculo por antigüedad, el catálogo institucional de unidades y el PDF en formato institucional quedan pendientes.
- El proceso contable del piloto reúne todos los respaldos de cuotas antes de pasar a revisión y permite registrar pagos individuales después. Confirmar si Contabilidad debe revisar y pagar una cuota mientras se siguen recibiendo respaldos de las demás; requeriría estados independientes por cuota.
- El convenio se elabora fuera de SITRAH. Se registran documentos y números, sin integración con el sistema universitario, firma electrónica, Contraloría ni tesorería. Las bandejas reflejan los pendientes; no hay correos ni alertas automáticas.
- Los PDF del piloto son de acceso autenticado, con validación básica de tipo y tamaño, sin análisis antimalware. El control de acceso a datos bancarios es por perfil en la API; antes de cargar datos reales, configurar el almacenamiento seguro de la base y de los respaldos.
- La autenticación local es para evaluación. Antes de usar expedientes reales se requiere SSO institucional, configuración segura de producción, revisión de roles y privacidad, almacenamiento y respaldos, monitoreo y política de conservación. Cambiar `SITRAH_DEMO=0` y secretos antes de iniciar un entorno nuevo; esa opción no elimina cuentas de una base ya sembrada.

## Estructura

- `frontend/`: React, Vite, interfaz y proxy Nginx de origen único.
- `backend/`: Django, migración, lógica de etapas, auditoría, almacenamiento privado de PDF y pruebas.
- `compose.yaml`: PostgreSQL, backend, frontend y volúmenes.

Para crear una cuenta de prueba en una base sin demo, usa `docker compose exec backend python manage.py createsuperuser` y después `docker compose exec backend python manage.py access NOMBRE ROL`. Para el rol `requirente` agrega `--unit "Nombre de la unidad"`. La creación como superusuario es solo un medio local para probar la asignación; los permisos de SITRAH se rigen por el perfil.

## Despliegue automático

Preparación del piloto: Compose desactiva los ejemplos por defecto (`SITRAH_DEMO=0`), conserva los volúmenes y todas las solicitudes existentes. Si AWS ya define `SITRAH_DEMO=1`, esa configuración tiene prioridad y debe cambiarse en el servidor. No se ejecuta ninguna limpieza de datos.

Cada persona debe tener su propia cuenta; varias cuentas pueden compartir rol. Las unidades delimitan las solicitudes visibles para requirentes. Las operaciones sobre expedientes usan bloqueo de fila y versión para rechazar cambios desactualizados. El formulario bloquea envíos repetidos mientras hay una operación pendiente. Para crear cuentas sin permisos de superusuario: `docker compose exec backend python manage.py create_account USUARIO ROL --name "Nombre" --email "correo@institucion.cl"`; agrega `--unit "Unidad"` para requirentes. La contraseña se solicita de forma oculta en la terminal.

El backend usa dos procesos con cuatro hilos cada uno, conexiones PostgreSQL reutilizadas con comprobación de salud y reinicio de procesos tras un número acotado de peticiones. Los servicios se reinician si terminan; el frontend espera a que la API y la base respondan antes de iniciar. Estas medidas no garantizan una capacidad concreta: antes de convocar usuarios debe verificarse el despliegue, los recursos de EC2 y una prueba de carga en un entorno de ensayo con PostgreSQL. Las pruebas locales verifican persistencia, permisos y rechazo de una segunda acción desactualizada; no equivalen a una prueba simultánea de carga en AWS.

SITRAH se encuentra alojado en AWS EC2 y cuenta con
despliegue automático desde la rama main de GitHub.
