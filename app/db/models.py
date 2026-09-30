from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

def now(): return datetime.now(timezone.utc)

class Patient(Base):
    __tablename__ = 'patients'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_uid: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(40), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    location: Mapped[str | None] = mapped_column(String(160), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(30), default='hinglish')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    calls = relationship('Call', back_populates='patient', cascade='all, delete-orphan')

class Call(Base):
    __tablename__ = 'calls'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    call_uid: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey('patients.id'))
    condition: Mapped[str] = mapped_column(String(40), default='burns_scalds')
    status: Mapped[str] = mapped_column(String(20), default='active')
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_returning_user: Mapped[bool] = mapped_column(Boolean, default=False)
    current_stage: Mapped[str] = mapped_column(String(40), default='IDENTIFY_USER')
    severity: Mapped[str] = mapped_column(String(10), default='UNKNOWN')
    severity_reasons: Mapped[str] = mapped_column(Text, default='[]')
    requires_follow_up: Mapped[str] = mapped_column(String(20), default='unknown')
    follow_up_status: Mapped[str] = mapped_column(String(20), default='not_created')
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    patient = relationship('Patient', back_populates='calls')
    messages = relationship('ConversationMessage', back_populates='call', cascade='all, delete-orphan', order_by='ConversationMessage.timestamp')
    assessment = relationship('Assessment', back_populates='call', uselist=False, cascade='all, delete-orphan')
    follow_ups = relationship('FollowUp', back_populates='call', cascade='all, delete-orphan')

class ConversationMessage(Base):
    __tablename__ = 'conversation_messages'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    call_id: Mapped[int] = mapped_column(ForeignKey('calls.id'))
    role: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(Text)
    input_type: Mapped[str] = mapped_column(String(20), default='text')
    language: Mapped[str] = mapped_column(String(30), default='hinglish')
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    call = relationship('Call', back_populates='messages')

class Assessment(Base):
    __tablename__ = 'assessments'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    call_id: Mapped[int] = mapped_column(ForeignKey('calls.id'), unique=True)
    age: Mapped[str] = mapped_column(String(80), default='unknown')
    cause_of_burn: Mapped[str] = mapped_column(String(80), default='unknown')
    time_since_burn: Mapped[str] = mapped_column(String(120), default='unknown')
    first_aid_given: Mapped[str] = mapped_column(String(120), default='unknown')
    body_part_affected: Mapped[str] = mapped_column(String(120), default='unknown')
    approximate_size: Mapped[str] = mapped_column(String(120), default='unknown')
    blistering_or_skin_appearance: Mapped[str] = mapped_column(String(120), default='unknown')
    pain_level: Mapped[str] = mapped_column(String(50), default='unknown')
    circumferential: Mapped[str] = mapped_column(String(40), default='unknown')
    smoke_or_enclosed_space_exposure: Mapped[str] = mapped_column(String(80), default='unknown')
    other_relevant_details: Mapped[str] = mapped_column(Text, default='')
    missing_information: Mapped[str] = mapped_column(Text, default='[]')
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    call = relationship('Call', back_populates='assessment')

class FollowUp(Base):
    __tablename__ = 'follow_ups'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    call_id: Mapped[int] = mapped_column(ForeignKey('calls.id'))
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    follow_up_type: Mapped[str] = mapped_column(String(40), default='check_in')
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[str] = mapped_column(Text, default='')
    status: Mapped[str] = mapped_column(String(20), default='pending')
    notes: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    call = relationship('Call', back_populates='follow_ups')
