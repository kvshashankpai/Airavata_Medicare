import json, secrets
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.models import Patient, Call, Assessment, ConversationMessage, FollowUp

def uid(prefix): return f'{prefix}-{secrets.token_hex(4).upper()}'
def patient_dict(p): return {'patient_uid':p.patient_uid,'name':p.name,'age':p.age,'gender':p.gender,'phone':p.phone,'location':p.location,'preferred_language':p.preferred_language}
def assessment_dict(a):
    d={k:getattr(a,k) for k in ['age','cause_of_burn','time_since_burn','first_aid_given','body_part_affected','approximate_size','blistering_or_skin_appearance','pain_level','circumferential','smoke_or_enclosed_space_exposure']}
    d['missing_information']=json.loads(a.missing_information or '[]'); return d

def create_patient(db, data):
    p=Patient(patient_uid=uid('PAT'), **data.model_dump()); db.add(p); db.commit(); db.refresh(p); return p

def create_call(db, patient, returning=False):
    c=Call(call_uid=uid('CALL'), patient_id=patient.id, is_returning_user=returning, current_stage='ASSESS_BURN')
    c.assessment=Assessment(); db.add(c); db.commit(); db.refresh(c); return c

def add_message(db, call, role, message):
    m=ConversationMessage(call_id=call.id, role=role, message=message, transcript=message); db.add(m); db.commit(); return m

def dump_call(c):
    return {'call_uid':c.call_uid,'patient':patient_dict(c.patient),'condition':c.condition,'status':c.status,'stage':c.current_stage,'severity':c.severity,'severity_reasons':json.loads(c.severity_reasons or '[]'),'requires_follow_up':c.requires_follow_up,'follow_up_status':c.follow_up_status,'summary':c.summary,'assessment':assessment_dict(c.assessment),'messages':[{'role':m.role,'message':m.message,'timestamp':m.timestamp.isoformat()} for m in c.messages]}
