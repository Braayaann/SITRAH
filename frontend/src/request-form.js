export const HIERARCHY='Docencia por jerarquía';
export const COURSE='Docencia por curso o diplomado';
export const ACTIVITIES=[HIERARCHY,COURSE,'Otras actividades'];
export const MONTHS=['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
export const CERTIFICATES=['Título profesional','Grado académico','Alumno regular','Experticia','Otro certificado afín'];
export const today=()=>new Intl.DateTimeFormat('sv-SE',{timeZone:'America/Santiago'}).format(new Date());
export const clp=n=>new Intl.NumberFormat('es-CL',{style:'currency',currency:'CLP'}).format(n||0);
export const isTeaching=category=>[HIERARCHY,COURSE,'Docencia por curso','Docencia'].includes(category);
export const stepsFor=(category,editing=false)=>['Identificación','Prestador','Actividad',...(category===HIERARCHY?[]:['Financiamiento']),'Declaraciones',...(!editing?['Datos bancarios']:[]),'Documentos'];
export function validRut(value){
 const rut=String(value||'').replace(/[.\s-]/g,'').toUpperCase();
 if(!/^\d{1,8}[0-9K]$/.test(rut)||!Number(rut.slice(0,-1)))return false;
 const sum=[...rut.slice(0,-1)].reverse().reduce((n,d,i)=>n+Number(d)*(2+i%6),0),dv=(11-sum%11)%11;
 return rut.at(-1)===(dv===10?'K':String(dv));
}
export function financeError(data){
 const parts=data.installments||[],amount=Number(data.amount);
 if(!Number.isSafeInteger(amount)||amount<=0||amount>999999999999)return 'Indica un total bruto en pesos chilenos enteros.';
 if(!parts.length)return 'Informa al menos un mes de pago.';
 if(parts.some(p=>!Number.isSafeInteger(Number(p.amount))||Number(p.amount)<=0))return 'Cada cuota debe tener un monto entero positivo.';
 if(parts.some(p=>p.month<data.start?.slice(0,7)||p.month>data.end?.slice(0,7))||new Set(parts.map(p=>p.month)).size!==parts.length)return 'Usa meses distintos dentro del período de la prestación.';
 if(new Set(parts.map(p=>Number(p.amount))).size!==parts.length)return 'Las cuotas deben tener montos distintos, con al menos $1 de diferencia.';
 if(parts.reduce((sum,p)=>sum+Number(p.amount),0)!==amount)return 'La suma de las cuotas debe coincidir exactamente con el monto total.';
 return '';
}
export function sectionError(section,d){
 if(section==='Prestador'){
  if(d.identity_type==='rut'&&!validRut(d.identifier))return 'Revisa el RUT del prestador y su dígito verificador.';
  if(d.identity_type==='passport'&&!/^[A-Za-z0-9][A-Za-z0-9 -]{2,29}$/.test(d.identifier||''))return 'Revisa el número de pasaporte.';
 }
 if(section==='Actividad'){
  if(d.end<d.start||d.start?.slice(0,4)!==d.end?.slice(0,4)||d.start<d.request_date)return 'El inicio debe ser igual o posterior a la solicitud y el período debe estar dentro del mismo año calendario.';
  if(!validRut(d.supervisor_identifier))return 'Revisa el RUT del supervisor y su dígito verificador.';
  if(!(Number(d.weekly_hours)>0)||!(Number(d.total_hours)>=Number(d.weekly_hours)))return 'Las horas deben ser positivas y el total no puede ser menor que las semanales.';
  if(isTeaching(d.category)&&(!Number.isFinite(Number(d.lective_hours))||!Number.isFinite(Number(d.non_lective_hours))||Number(d.lective_hours)<0||Number(d.non_lective_hours)<0||Math.abs(Number(d.lective_hours)+Number(d.non_lective_hours)-Number(d.total_hours))>.000001))return 'Las horas lectivas y no lectivas deben sumar las horas totales del convenio.';
 }
 if(section==='Financiamiento')return financeError(d);
 return '';
}
export function initialData(ctx,item){
 const d=item?.data;
 return d?{...d,public_employee:d.public_employee?'sí':'no',nationality_choice:d.nationality==='Chilena'?'Chilena':'Otra',chilean_id:d.identity_type==='rut'?'sí':'no',installments:item.installments.map(({month,amount})=>({month,amount})),bank:{pending:true}}:
 {request_date:today(),requester:ctx.user.name,position:'Secretaria',contact:ctx.user.email||'',honorarium_type:'Persona Natural',identity_type:'rut',nationality_choice:'Chilena',nationality:'Chilena',chilean_id:'sí',category:COURSE,public_employee:'',travel:'no',bank:{pending:true},installments:[]};
}
export function submissionData(d,item){
 const out={...d,form_version:2,version:item?.version,public_employee:d.public_employee==='sí',amount:d.category===HIERARCHY?null:Number(d.amount),installments:d.category===HIERARCHY?[]:d.installments.map(p=>({month:p.month,amount:Number(p.amount)}))};
 for(const key of ['weekly_hours','total_hours','lective_hours','non_lective_hours'])out[key]=d[key]==null||d[key]===''?null:Number(d[key]);
 if(!isTeaching(d.category)){delete out.lective_hours;delete out.non_lective_hours;}
 if(d.category===HIERARCHY){out.cost_center=item?.data?.category===HIERARCHY?item.data.cost_center||'':'';out.travel='no';delete out.travel_reason;}
 return out;
}
