const $=id=>document.getElementById(id);

const MODEL={
  airavata:{
    label:'Airavata',
    note:'Airavata (ai4bharat/Airavata) is used only at the final user-facing wording stage. Safety, first aid and triage are deterministic.'
  }
};

let activeModel='airavata';
let currentPatientUid=localStorage.getItem('medcare_patient_uid')||null;
let callUid=localStorage.getItem('medcare_call_uid_v4_airavata')||null;

function bubble(role,text){
  const d=document.createElement('div');
  d.className='bubble '+role;
  d.textContent=text;
  $('messages').appendChild(d);
  $('messages').scrollTop=$('messages').scrollHeight;
}

function render(c){
  if(!c)return;
  const p=c.patient||{};
  if(p.patient_uid&&p.name&&p.name!=='Pending details'){
    currentPatientUid=p.patient_uid;
    localStorage.setItem('medcare_patient_uid',currentPatientUid);
  }
  $('p-name').textContent=p.name==='Pending details'?'To be collected':(p.name||'—');
  $('p-age').textContent=p.age??'To be collected';
  $('p-uid').textContent=p.patient_uid||'—';
  $('c-uid').textContent=c.call_uid||'—';
  $('stage').textContent=c.stage||'—';
  $('severity').textContent=c.severity||'UNKNOWN';
  $('follow').textContent=c.requires_follow_up||'unknown';
  const a=c.assessment||{};
  const map={
    cause_of_burn:'Cause',
    time_since_burn:'Time',
    body_part_affected:'Body part',
    approximate_size:'Size',
    blistering_or_skin_appearance:'Appearance',
    pain_level:'Pain',
    circumferential:'Circumferential',
    smoke_or_enclosed_space_exposure:'Smoke exposure'
  };
  $('known').innerHTML=Object.entries(map)
    .map(([k,l])=>`<li>${l}: ${a[k]||'unknown'}</li>`).join('');
  $('missing').innerHTML=(a.missing_information||[])
    .map(x=>`<li>${x}</li>`).join('')||'<li>None</li>';
  $('reasons').textContent=(c.severity_reasons||[]).join(' • ');
}

async function api(url,opt={}){
  const r=await fetch(url,{headers:{'Content-Type':'application/json'},...opt});
  if(!r.ok){
    let msg='Request failed';
    try{msg=(await r.json()).detail||msg}catch(e){}
    throw new Error(msg);
  }
  return r.json();
}

async function startCase(){
  const body=currentPatientUid?{patient_uid:currentPatientUid}:{};
  const x=await api('/api/calls',{method:'POST',body:JSON.stringify(body)});
  callUid=x.call_uid;
  localStorage.setItem('medcare_call_uid_v4_airavata',callUid);
  $('messages').innerHTML='';
  bubble('assistant','Model: Airavata (ai4bharat/Airavata) will be used only after the burn incident has been assessed.');
  bubble('assistant',x.assistant_response);
  render(x.case);
  $('model-status').textContent='Safety engine ready';
}

async function loadCase(){
  $('active-model').textContent='Airavata';
  $('model-note').textContent=MODEL.airavata.note;
  $('messages').innerHTML='';

  if(!callUid){
    try{await startCase()}
    catch(e){bubble('assistant','Could not start this chat. '+e.message)}
    return;
  }

  try{
    const c=await api('/api/calls/'+callUid);
    c.messages.forEach(m=>bubble(m.role,m.message));
    render(c);
    $('model-status').textContent='Ready';
  }catch(e){
    localStorage.removeItem('medcare_call_uid_v4_airavata');
    callUid=null;
    try{await startCase()}
    catch(err){bubble('assistant','Could not start this chat. '+err.message)}
  }
}

$('composer').addEventListener('submit',async e=>{
  e.preventDefault();
  const text=$('input').value.trim();
  if(!text||!callUid)return;

  bubble('user',text);
  $('input').value='';
  $('send').disabled=true;
  $('thinking').classList.remove('hidden');
  $('model-status').textContent='Processing…';

  try{
    const x=await api('/api/calls/'+callUid+'/message',{
      method:'POST',
      body:JSON.stringify({message:text,model_key:'airavata'})
    });
    bubble('assistant',x.assistant_response);
    render(x.case);
    if(x.model.model_status==='authoritative_backend'){
      $('model-status').textContent='Safety/Triage response';
    }else{
      $('model-status').textContent='Airavata: '+(x.model.model_status||'done');
    }
    if(x.model.model_status==='unavailable_fallback'){
      $('model-note').textContent='Airavata unavailable; approved deterministic backend wording was used.';
    }
  }catch(err){
    bubble('assistant','Sorry, something went wrong while processing this message. Please try again.');
    $('model-status').textContent='Error';
  }finally{
    $('send').disabled=false;
    $('thinking').classList.add('hidden');
    $('input').focus();
  }
});

$('input').addEventListener('keydown',e=>{
  if(e.key==='Enter'&&!e.shiftKey){
    e.preventDefault();
    $('composer').requestSubmit();
  }
});

$('new-case').addEventListener('click',async()=>{
  try{
    await startCase();
  }catch(e){
    alert('Could not start a new case. Please try again.');
  }
});

loadCase();
