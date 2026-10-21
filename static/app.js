const $ = (id) => document.getElementById(id);
const csrf = document.querySelector('meta[name="csrf-token"]').content;
const actions = {on:'Encender',off:'Apagar',restart:'Reiniciar'};
const days = ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'];
let current, pending, busy = false, toastTimer;
const el = (tag, text, cls) => { const n = document.createElement(tag); if(text !== undefined)n.textContent=text; if(cls)n.className=cls; return n; };
function button(text, fn, cls) { const b=el('button',text,cls); b.type='button'; b.addEventListener('click',fn); return b; }
function notify(text) { $('toast').textContent=text; $('toast').hidden=false; clearTimeout(toastTimer); toastTimer=setTimeout(()=>$('toast').hidden=true,4000); }
async function api(path, method='GET', data) {
  const response=await fetch(path,{method,headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:data===undefined?undefined:JSON.stringify(data)});
  const result=await response.json(); if(!response.ok)throw new Error(result.error||'No se pudo completar la solicitud.'); return result;
}
function showError(error) { $('error').textContent=error.message; $('error').hidden=false; }
async function perform(path,method,data,message) { if(busy)return; busy=true; try { await api(path,method,data); await refresh(); notify(message); } catch(e){showError(e);} finally{busy=false;} }
function confirmAction(title,text,fn) { $('confirm-title').textContent=title; $('confirm-text').textContent=text; pending=fn; $('confirm-dialog').showModal(); }
$('confirm-yes').onclick=()=>{const fn=pending; pending=null; $('confirm-dialog').close(); if(fn)fn();};
document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>$(b.dataset.close).close());
function empty(target,title,text) { const box=el('div',undefined,'empty'); box.append(el('strong',title),el('span',text)); target.append(box); }
function render(data) {
  current=data; $('error').hidden=true;
  $('clock').textContent=new Intl.DateTimeFormat('es',{timeZone:data.timezone,hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(data.now));
  $('total').textContent=data.servers.length; $('online').textContent=data.servers.filter(s=>s.state==='on').length; $('rules').textContent=data.schedules.filter(s=>s.enabled).length;
  const names=Object.fromEntries(data.servers.map(s=>[s.id,s.name]));
  $('servers').replaceChildren();
  data.servers.forEach(s=>{
    const card=el('article',undefined,'server-card'),top=el('div',undefined,'server-top');
    top.append(el('span','▤','server-icon'),el('span',{on:'Encendido · simulado',off:'Apagado · simulado',unknown:'Sin simular'}[s.state],`status ${s.state}`));
    card.append(top,el('h3',s.name),el('div',`${s.user}@${s.host}`,'host'));
    const meta=el('div',undefined,'server-meta'); meta.append(el('span','UBUNTU'),el('span','ETHERNET'),el('span','SIMULACIÓN')); card.append(meta);
    const controls=el('div',undefined,'actions');
    Object.entries(actions).forEach(([action,label])=>{
      const run=()=>perform('/api/actions','POST',{server:s.id,action,confirmed:true},`${label}: simulación registrada.`);
      controls.append(button(label,()=>action==='on'?run():confirmAction(`${label} ${s.name}`, 'Esta acción es simulada. No se enviará ninguna orden al servidor.',run),action==='on'?'primary':''));
    }); card.append(controls); $('servers').append(card);
  });
  $('schedule-list').replaceChildren();
  if(!data.schedules.length)empty($('schedule-list'),'Tu semana empieza aquí','Crea un horario para simular el encendido, apagado o reinicio.');
  data.schedules.forEach(s=>{
    const row=el('div',undefined,`schedule-row ${s.enabled?'':'paused'}`), info=el('div',undefined,'row-main');
    info.append(el('strong',`${actions[s.action]} · ${names[s.server]}`),el('small',s.days.map(d=>days[d]).join(' · ') + (s.enabled?' · Activo':' · Pausado')));
    const controls=el('div',undefined,'row-buttons');
    controls.append(button(s.enabled?'Pausar':'Activar',()=>perform(`/api/schedules/${s.id}/toggle`,'POST',{enabled:!s.enabled},'Horario actualizado.')),
      button('Eliminar',()=>confirmAction('Eliminar horario',`${actions[s.action]} ${names[s.server]} a las ${s.time}.`,()=>perform(`/api/schedules/${s.id}`,'DELETE',undefined,'Horario eliminado.'))));
    row.append(el('span',s.time,'schedule-time'),info,controls); $('schedule-list').append(row);
  });
  $('events').replaceChildren();
  if(!data.events.length)empty($('events'),'Todavía no hay actividad','Las acciones manuales y programadas aparecerán aquí.');
  data.events.forEach(e=>{const row=el('div',undefined,'event-row'),info=el('div',undefined,'row-main');
    info.append(el('strong',`${actions[e.action]} · ${names[e.server]}`),el('small',e.detail));
    row.append(el('time',new Intl.DateTimeFormat('es',{timeZone:data.timezone,month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}).format(new Date(e.at)),'event-time'),info,el('span',e.source==='manual'?'MANUAL':'PROGRAMADO','event-badge')); $('events').append(row);
  });
}
async function refresh(){const data=await api('/api/state');render(data);}
days.forEach((d,i)=>{const label=el('label'),input=el('input');input.type='checkbox';input.name='day';input.value=i;label.append(input,el('span',d));$('day-options').append(label);});
$('new-rule').onclick=()=>{if(!current)return; $('schedule-form').reset();$('form-error').textContent='';$('server-select').replaceChildren(...current.servers.map(s=>{const o=el('option',s.name);o.value=s.id;return o;}));$('schedule-dialog').showModal();};
$('schedule-form').onsubmit=async event=>{
  event.preventDefault();const form=event.target,selected=[...form.querySelectorAll('[name="day"]:checked')].map(n=>Number(n.value));
  if(!selected.length){$('form-error').textContent='Selecciona al menos un día.';return;}
  const submit=form.querySelector('[type="submit"]');submit.disabled=true;
  try{await api('/api/schedules','POST',{server:form.elements.server.value,action:form.elements.action.value,time:form.elements.time.value,days:selected});$('schedule-dialog').close();await refresh();notify('Horario guardado en modo simulación.');}
  catch(e){$('form-error').textContent=e.message;}finally{submit.disabled=false;}
};
refresh().catch(showError);
setInterval(()=>{if(!document.hidden&&!busy&&!document.querySelector('dialog[open]'))refresh().catch(showError);},10000);
