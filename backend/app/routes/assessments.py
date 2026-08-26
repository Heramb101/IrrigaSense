from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.assessment import AssessmentCreate, AssessmentRead, AssessmentUpdate
from app.models.models import Farm, Assessment
from app.services.soil_resolver import resolve_soil_values

router = APIRouter(
    prefix="/api/assessments",
    tags=["Assessments"]
)

@router.post("", response_model=AssessmentRead, status_code=status.HTTP_201_CREATED)
def create_assessment(assessment_in: AssessmentCreate, db: Session = Depends(get_db)):
    # Verify farm exists
    farm = db.query(Farm).filter(Farm.id == assessment_in.farm_id).first()
    if not farm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")
        
    # Resolve soil values
    resolved_soil_data = resolve_soil_values(assessment_in.data.soil)
    assessment_in.data.soil = resolved_soil_data
    
    # Store in DB
    db_assessment = Assessment(
        farm_id=assessment_in.farm_id,
        assessment_version=assessment_in.assessment_version,
        data=assessment_in.data.model_dump(mode='json')
    )
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)
    return db_assessment

@router.get("/{assessment_id}", response_model=AssessmentRead)
def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return assessment

@router.put("/{assessment_id}", response_model=AssessmentRead)
def update_assessment(assessment_id: int, assessment_in: AssessmentUpdate, db: Session = Depends(get_db)):
    db_assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not db_assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        
    if assessment_in.assessment_version is not None:
        db_assessment.assessment_version = assessment_in.assessment_version
        
    if assessment_in.data is not None:
        resolved_soil_data = resolve_soil_values(assessment_in.data.soil)
        assessment_in.data.soil = resolved_soil_data
        db_assessment.data = assessment_in.data.model_dump(mode='json')
        
    db.commit()
    db.refresh(db_assessment)
    return db_assessment
