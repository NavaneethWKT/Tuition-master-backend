from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.api.student.schemas import StudentCreate, StudentResponse
from app.utils.password import hash_password
from datetime import datetime

router = APIRouter(
    prefix="/api/student",
    tags=["Student"]
)


@router.post("/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new student.
    """
    # Verify school exists
    school = db.query(models.School).filter(models.School.id == student_data.school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )
    
    # Verify class exists if provided
    if student_data.class_id:
        class_obj = db.query(models.Class).filter(models.Class.id == student_data.class_id).first()
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found"
            )
        # Verify class belongs to the same school
        if class_obj.school_id != student_data.school_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Class does not belong to the specified school"
            )
    
    # Check if phone or email already exists
    if student_data.phone:
        existing_student = db.query(models.Student).filter(
            models.Student.phone == student_data.phone
        ).first()
        if existing_student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student with this phone number already exists"
            )
    
    if student_data.email:
        existing_student = db.query(models.Student).filter(
            models.Student.email == student_data.email
        ).first()
        if existing_student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student with this email already exists"
            )
    
    # Hash password
    password_hash = hash_password(student_data.password)
    
    # Parse dates
    try:
        date_of_birth = datetime.strptime(student_data.date_of_birth, "%Y-%m-%d").date()
        admission_date = datetime.strptime(student_data.admission_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    # Create student
    student = models.Student(
        school_id=student_data.school_id,
        class_id=student_data.class_id,
        full_name=student_data.full_name,
        email=student_data.email,
        phone=student_data.phone,
        password_hash=password_hash,
        date_of_birth=date_of_birth,
        roll_number=student_data.roll_number,
        admission_date=admission_date
    )
    
    db.add(student)
    db.commit()
    db.refresh(student)
    
    return student

