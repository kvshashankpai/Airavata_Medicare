import os
os.environ['DATABASE_URL']='sqlite:///./test_medcare.db'
from app.services.extraction_service import extract, emergency_flags
from app.services.triage_service import missing, next_question, assess

def test_basic_hinglish_extraction_no_hallucination():
    a=extract('mere haath pe garam paani gir gaya')
    assert a['cause_of_burn']=='hot_liquid'; assert a['body_part_affected']=='hand'
    assert 'pain_level' not in a and 'approximate_size' not in a and 'age' not in a

def test_incremental_fields_and_correction():
    a=extract('2 ghante pehle hua'); assert a['time_since_burn'].startswith('2')
    assert extract('pain mild hai')['pain_level']=='mild'
    assert extract('actually bahut zyada pain hai')['pain_level']=='severe'

def test_emergency_face_smoke():
    flags=emergency_flags('face aur gale pe jal gaya tha aur smoke bhi tha')
    assert 'face/airway involvement' in flags and 'smoke/inhalation exposure' in flags

def test_one_question_priority():
    field,q=next_question({'cause_of_burn':'hot_liquid','body_part_affected':'hand'})
    assert field=='smoke_or_enclosed_space_exposure' and q.endswith('?')

def test_triage_unknown_until_complete():
    assert assess({'cause_of_burn':'hot_liquid'})[0]=='UNKNOWN'
