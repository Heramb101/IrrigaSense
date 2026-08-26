from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.connection import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    farms = relationship("Farm", back_populates="owner", cascade="all, delete-orphan")

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
    assessment_version = Column(String, default="1.0")
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Store structured assessment data matching the Pydantic schema
    data = Column(JSON)
    
    farm = relationship("Farm", back_populates="assessments")
