from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.api.parent.schemas import ParentCreate, ParentResponse
from app.utils.password import hash_password

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

