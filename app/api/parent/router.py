from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.api.parent.schemas import ParentCreate, ParentResponse
from app.api.student.schemas import StudentResponse
from app.utils.password import hash_password
from uuid import UUID

router = APIRouter(
    prefix="/api/parent",
    tags=["Parent"]
)


@router.post("/parents", response_model=ParentResponse, status_code=status.HTTP_201_CREATED)
async def create_parent(
    parent_data: ParentCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new parent.
    """
    # Verify student exists
    student = db.query(models.Student).filter(models.Student.id == parent_data.student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Check if parent already exists for this student
    existing_parent = db.query(models.Parent).filter(
        models.Parent.student_id == parent_data.student_id
    ).first()
    if existing_parent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parent already exists for this student"
        )
    
    # Check if phone already exists
    existing_phone = db.query(models.Parent).filter(
        models.Parent.phone == parent_data.phone
    ).first()
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parent with this phone number already exists"
        )
    
    # Hash password
    password_hash = hash_password(parent_data.password)
    
    # Create parent
    parent = models.Parent(
        student_id=parent_data.student_id,
        full_name=parent_data.full_name,
        email=parent_data.email,
        phone=parent_data.phone,
        password_hash=password_hash
    )
    
    db.add(parent)
    db.commit()
    db.refresh(parent)
    
    return parent


@router.get("/{parent_id}/student", response_model=StudentResponse, status_code=status.HTTP_200_OK)
async def get_parent_student(
    parent_id: UUID = Path(..., description="Parent ID"),
    db: Session = Depends(get_db)
):
    """
    Get student details for a parent.
    """
    # Verify parent exists
    parent = db.query(models.Parent).filter(models.Parent.id == parent_id).first()
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent not found"
        )
    
    # Get the student associated with this parent
    student = db.query(models.Student).filter(models.Student.id == parent.student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found for this parent"
        )
    
    return student

