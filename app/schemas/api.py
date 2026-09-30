from pydantic import BaseModel, Field

class PatientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    age: int | None = Field(default=None, ge=0, le=130)
    gender: str | None = None
    phone: str | None = None
    location: str | None = None
    preferred_language: str = 'hinglish'

class PatientOut(PatientCreate):
    patient_uid: str
    class Config: from_attributes = True

class CallCreate(BaseModel):
    patient_uid: str | None = None
    patient: PatientCreate | None = None

class MessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    model_key: str = 'local'

class FollowUpCreate(BaseModel):
    notes: str = ''
