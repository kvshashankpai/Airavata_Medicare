import json, logging
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db.database import Base, engine, get_db
from app.db.models import Patient, Call, FollowUp
from app.schemas.api import PatientCreate, CallCreate, MessageCreate, FollowUpCreate
from app.services.extraction_service import extract, context_extract, emergency_flags, is_burn_message, patient_details
from app.services.triage_service import missing, next_question, assess, guidance, immediate_first_aid, follow_up
from app.services.persistence import create_patient, create_call, add_message, dump_call, assessment_dict
from app.services.model_service import safe_model_response, catalog
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('medcare')
app = FastAPI(title='Hinglish MedCare', version='1.1.0')
app.mount('/static', StaticFiles(directory='app/static'), name='static')
templates = Jinja2Templates(directory='app/templates')

@app.on_event('startup')
def startup():
    Base.metadata.create_all(bind=engine)

@app.get('/', response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name='chat.html', context={})

@app.get('/api/models')
def models():
    return catalog()

@app.post('/api/patients')
def new_patient(data: PatientCreate, db: Session = Depends(get_db)):
    return create_patient(db, data).__dict__

@app.get('/api/patients/{patient_uid}')
def get_patient(patient_uid: str, db: Session = Depends(get_db)):
    p = db.query(Patient).filter_by(patient_uid=patient_uid).first()
    if not p: raise HTTPException(404, 'Patient not found')
    return {'patient': {'patient_uid': p.patient_uid, 'name': p.name, 'age': p.age, 'gender': p.gender, 'phone': p.phone, 'location': p.location}, 'calls': [dump_call(c) for c in p.calls]}

@app.post('/api/calls')
def new_call(data: CallCreate, db: Session = Depends(get_db)):
    returning = False
    if data.patient_uid:
        p = db.query(Patient).filter_by(patient_uid=data.patient_uid).first()
        if not p: raise HTTPException(404, 'Patient not found')
        returning = True
    elif data.patient:
        p = create_patient(db, data.patient)
    else:
        # A provisional local record lets the conversation start with the incident.
        p = create_patient(db, PatientCreate(name='Pending details', preferred_language='hinglish'))
    c = create_call(db, p, returning)
    welcome = ('Welcome back. Pehle current incident samajhte hain; purani details ko is burn mein assume nahi karunga.' if returning else
               'Namaste! Aapko kis tarah ki problem hui hai? Burn/scald, jalna, ya skin par koi injury — pehle incident bataiye. Main pehle safety aur first aid samjhaunga, details baad mein loonga.')
    add_message(db, c, 'assistant', welcome)
    return {'call_uid': c.call_uid, 'assistant_response': welcome, 'case': dump_call(c)}

@app.get('/api/calls/{call_uid}')
def get_call(call_uid: str, db: Session = Depends(get_db)):
    c = db.query(Call).filter_by(call_uid=call_uid).first()
    if not c: raise HTTPException(404, 'Call not found')
    return dump_call(c)

@app.get('/api/calls/{call_uid}/messages')
def messages(call_uid: str, db: Session = Depends(get_db)):
    c = db.query(Call).filter_by(call_uid=call_uid).first()
    if not c: raise HTTPException(404, 'Call not found')
    return [{'role': m.role, 'message': m.message, 'timestamp': m.timestamp.isoformat()} for m in c.messages]

@app.post('/api/calls/{call_uid}/message')
def process_message(call_uid: str, data: MessageCreate, db: Session = Depends(get_db)):
    c = db.query(Call).filter_by(call_uid=call_uid).first()
    if not c: raise HTTPException(404, 'Call not found')
    text = data.message.strip()
    model_key = data.model_key if data.model_key in catalog() else 'local'
    add_message(db, c, 'user', text)
    
    # Early identity check: if the user volunteers their name before the final stage
    early_ack = ""
    if c.patient.name == 'Pending details' and c.current_stage != 'COLLECT_BASIC_INFO':
        # Simple heuristic to extract name from common intros
        search_name = text.lower().replace('mei', '').replace('hun', '').replace('mera', '').replace('naam', '').replace('hai', '').replace('i am', '').replace('my name is', '').strip()
        if search_name and len(search_name.split()) <= 3:
            existing_p = db.query(Patient).filter(Patient.name.ilike(f"%{search_name}%")).first()
            if existing_p:
                c.patient_id = existing_p.id
                c.is_returning_user = True
                early_ack = f"Welcome back {existing_p.name}! "
                db.commit()
                db.refresh(c)
            else:
                c.patient.name = search_name.title()
                db.commit()

    a = c.assessment
    # Determine which field was being asked *before* this message
    current_field, _ = next_question(assessment_dict(a))
    found = extract(text)
    # If extract() didn't capture the field being asked, try context-aware extraction
    if current_field and current_field not in found:
        ctx = context_extract(text, current_field)
        found.update(ctx)
    for key, value in found.items(): setattr(a, key, value)
    flags = emergency_flags(text)
    user_turns = sum(1 for m in c.messages if m.role == 'user')
    miss = missing(assessment_dict(a))
    a.missing_information = json.dumps(miss)
    log.info('message received call=%s extracted=%s missing=%s flags=%s', call_uid, found, miss, flags)

    # Once the incident is handled, collect identity at the end, not at the beginning.
    if c.current_stage == 'COLLECT_BASIC_INFO':
        details = patient_details(text)
        if 'name' in details and c.patient.name == 'Pending details': c.patient.name = details['name']
        if 'age' in details:
            c.patient.age = int(details['age']); a.age = details['age']
        if c.patient.name == 'Pending details':
            response = 'Theek hai. Ab patient ka naam bataiye.'
        elif c.patient.age is None:
            response = 'Dhanyavaad. Ab patient ki age bataiye.'
        else:
            req, reason = follow_up(c.severity)
            c.requires_follow_up = req; c.follow_up_status = 'pending' if req == 'required' else 'not_required'
            c.summary = f'Burn/scald case for {c.patient.name}. Age: {c.patient.age}. Severity: {c.severity}. Reasons: {", ".join(json.loads(c.severity_reasons or "[]"))}.\n\n{guidance(c.severity, json.loads(c.severity_reasons or "[]"))}'
            c.status = 'completed'; c.current_stage = 'COMPLETE'
            if req == 'required' and not c.follow_ups: db.add(FollowUp(call_id=c.id, required=True, reason=reason, status='pending'))
            response = 'Dhanyavaad. Details save kar diye gaye hain. Agar pain, redness, swelling, blistering ya koi naya symptom badhe, turant medical help lein aur is case par wapas update dein.\n\nCASE SUMMARY\n' + c.summary
        response, model_info = safe_model_response(model_key, text, response)
        add_message(db, c, 'assistant', response); db.commit(); db.refresh(c)
        return _message_response(c, response, model_info)

    # Emergency takes priority over routine questions and gets first-aid instructions immediately.
    if flags:
        c.severity = 'RED'; c.severity_reasons = json.dumps(flags); c.requires_follow_up = 'required'; c.current_stage = 'COLLECT_BASIC_INFO'
        response = immediate_first_aid(flags) + ' Jab aap safe hon, patient ka naam bataiye — baaki details end mein save karenge.'
    elif is_burn_message(text) and user_turns == 1:
        field, question = next_question(assessment_dict(a))
        c.current_stage = 'ASK_MISSING_INFO'; c.severity = 'UNKNOWN'; c.severity_reasons = '[]'
        response = immediate_first_aid() + question
    elif miss:
        field, question = next_question(assessment_dict(a))
        c.current_stage = 'ASK_MISSING_INFO'; c.severity = 'UNKNOWN'; c.severity_reasons = '[]'
        response = ('Samajh gaya. ' if found else 'Thik hai. ') + question
    else:
        severity, reasons = assess(assessment_dict(a))
        c.severity = severity; c.severity_reasons = json.dumps(reasons); c.current_stage = 'COLLECT_BASIC_INFO'
        response = guidance(severity, reasons) + '\n\nIncident assessment ho gaya. Ab patient ka naam bataiye; age baad mein confirm karunga.'
        req, reason = follow_up(severity); c.requires_follow_up = req; c.follow_up_status = 'pending' if req == 'required' else 'not_required'
    response, model_info = safe_model_response(model_key, text, response)
    if early_ack: response = early_ack + "\n\n" + response
    add_message(db, c, 'assistant', response); db.commit(); db.refresh(c)
    return _message_response(c, response, model_info)

def _message_response(c, response, model_info=None):
    return {'assistant_response': response, 'model': model_info or {'model_key':'local'}, 'stage': c.current_stage, 'assessment': assessment_dict(c.assessment), 'missing_information': json.loads(c.assessment.missing_information or '[]'), 'severity': c.severity, 'severity_reasons': json.loads(c.severity_reasons or '[]'), 'requires_follow_up': c.requires_follow_up, 'case_complete': c.status == 'completed', 'case': dump_call(c)}

@app.get('/api/calls/{call_uid}/assessment')
def get_assessment(call_uid: str, db: Session = Depends(get_db)):
    c = db.query(Call).filter_by(call_uid=call_uid).first()
    if not c: raise HTTPException(404, 'Call not found')
    return assessment_dict(c.assessment)

@app.get('/api/calls/{call_uid}/summary')
def summary(call_uid: str, db: Session = Depends(get_db)):
    c = db.query(Call).filter_by(call_uid=call_uid).first()
    if not c: raise HTTPException(404, 'Call not found')
    return {'summary': c.summary, 'severity': c.severity, 'reasons': json.loads(c.severity_reasons or '[]')}

@app.post('/api/calls/{call_uid}/follow-up')
def create_followup(call_uid: str, data: FollowUpCreate, db: Session = Depends(get_db)):
    c = db.query(Call).filter_by(call_uid=call_uid).first()
    if not c: raise HTTPException(404, 'Call not found')
    f = FollowUp(call_id=c.id, required=True, reason='Manual follow-up requested', notes=data.notes)
    db.add(f); c.requires_follow_up = 'required'; c.follow_up_status = 'pending'; db.commit()
    return {'status': 'pending', 'reason': f.reason}
