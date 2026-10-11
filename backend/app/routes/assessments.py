from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.assessment import AssessmentCreate, AssessmentRead, AssessmentUpdate
from app.models.models import Farm, Assessment, User
from app.services.soil_resolver import resolve_soil_values
from app.routes.auth import get_current_user, get_optional_current_user

router = APIRouter(
    prefix="/api/assessments",
    tags=["Assessments"]
)

@router.post("", response_model=AssessmentRead, status_code=status.HTTP_201_CREATED)
def create_assessment(
    assessment_in: AssessmentCreate,
    user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Creates a new farm assessment. If authenticated, automatically associates with current user."""
    # Verify farm exists
    farm = db.query(Farm).filter(Farm.id == assessment_in.farm_id).first()
    if not farm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

    # Resolve soil values
    resolved_soil_data = resolve_soil_values(assessment_in.data.soil)
    assessment_in.data.soil = resolved_soil_data

    # Store in DB with server-derived ownership (never client-supplied)
    db_assessment = Assessment(
        farm_id=assessment_in.farm_id,
        user_id=user.id if user else None,
        assessment_version=assessment_in.assessment_version,
        data=assessment_in.data.model_dump(mode='json')
    )
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)
    return db_assessment

@router.get("/mine", response_model=List[AssessmentRead], status_code=status.HTTP_200_OK)
def get_my_assessments(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists the authenticated user's assessments, ordered newest first."""
    assessments = (
        db.query(Assessment)
        .filter(Assessment.user_id == user.id)
        .order_by(Assessment.created_at.desc())
        .all()
    )
    return assessments

@router.get("/{assessment_id}", response_model=AssessmentRead)
def get_assessment(
    assessment_id: int,
    user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Fetches a specific assessment. Enforces ownership check if assessment is owned."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    # If owned by a user, ensure only that owner can access it
    if assessment.user_id is not None:
        if user is None or user.id != assessment.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this assessment"
            )

    return assessment

@router.put("/{assessment_id}", response_model=AssessmentRead)
def update_assessment(
    assessment_id: int,
    assessment_in: AssessmentUpdate,
    user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Updates an existing assessment with ownership verification."""
    db_assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not db_assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    # Enforce ownership if owned
    if db_assessment.user_id is not None:
        if user is None or user.id != db_assessment.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to update this assessment"
            )

    if assessment_in.assessment_version is not None:
        db_assessment.assessment_version = assessment_in.assessment_version

    if assessment_in.data is not None:
        resolved_soil_data = resolve_soil_values(assessment_in.data.soil)
        assessment_in.data.soil = resolved_soil_data
        db_assessment.data = assessment_in.data.model_dump(mode='json')

    db.commit()
    db.refresh(db_assessment)
    return db_assessment
