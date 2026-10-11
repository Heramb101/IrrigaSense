from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.connection import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    name = Column(String(100), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    farms = relationship("Farm", back_populates="owner", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="owner")

class UserSession(Base):
    __tablename__ = 'user_sessions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    csrf_token = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    last_used_at = Column(DateTime(timezone=True), default=utc_now)
    is_active = Column(Boolean, default=True, index=True)

    user = relationship("User", back_populates="sessions")

class Farm(Base):
    __tablename__ = 'farms'
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    location_name = Column(String)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    owner = relationship("User", back_populates="farms")
    assessments = relationship("Assessment", back_populates="farm", cascade="all, delete-orphan")

class Assessment(Base):
    __tablename__ = 'assessments'
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey('farms.id'))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    assessment_version = Column(String, default="1.0")
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Store structured assessment data matching the Pydantic schema
    data = Column(JSON)

    farm = relationship("Farm", back_populates="assessments")
    owner = relationship("User", back_populates="assessments")
