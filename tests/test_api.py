import os
os.environ['DATABASE_URL']='sqlite:///./test_api.db'
from fastapi.testclient import TestClient
from app.main import app

def test_create_call_and_message():
    with TestClient(app) as client:
        r=client.post('/api/calls',json={'patient':{'name':'Test User','age':21}}); assert r.status_code==200
        uid=r.json()['call_uid']
        r=client.post(f'/api/calls/{uid}/message',json={'message':'mere haath pe garam paani gir gaya'})
        assert r.status_code==200; body=r.json(); assert body['assessment']['cause_of_burn']=='hot_liquid'; assert body['severity']=='UNKNOWN'; assert len(body['missing_information'])>1
        r=client.get(f'/api/calls/{uid}'); assert r.status_code==200; assert len(r.json()['messages'])==3

def test_emergency_override():
    with TestClient(app) as client:
        uid=client.post('/api/calls',json={'patient':{'name':'Emergency User'}}).json()['call_uid']
        body=client.post(f'/api/calls/{uid}/message',json={'message':'face burn and difficulty breathing with smoke'}).json()
        assert body['severity']=='RED'; assert 'emergency' in body['assistant_response'].lower()
