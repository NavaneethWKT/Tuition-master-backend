from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app import models
from app.api.student.schemas import (
    StudentCreate, StudentResponse, 
    StudyMaterialWithSubjectResponse, StudentClassMaterialsResponse
)
from app.utils.password import hash_password
from datetime import datetime
from uuid import UUID

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


@router.get("/{student_id}/class-materials", response_model=StudentClassMaterialsResponse, status_code=status.HTTP_200_OK)
async def get_student_class_materials(
    student_id: UUID = Path(..., description="Student ID"),
    db: Session = Depends(get_db)
):
    """
    Get all study materials uploaded for a student's class.
    Returns materials with subject names, total materials count, and total subjects count.
    """
    # Verify student exists
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Check if student has a class assigned
    if not student.class_id:
        return StudentClassMaterialsResponse(
            materials=[],
            total_materials=0,
            total_subjects=0
        )
    
    # Get all study materials for the student's class with subject information
    materials_query = db.query(
        models.StudyMaterial,
        models.Subject.name.label('subject_name')
    ).join(
        models.Subject, models.StudyMaterial.subject_id == models.Subject.id
    ).filter(
        models.StudyMaterial.class_id == student.class_id
    ).all()
    
    # Format materials with subject name
    materials_list = []
    subject_ids = set()
    
    for material, subject_name in materials_query:
        subject_ids.add(material.subject_id)
        materials_list.append(StudyMaterialWithSubjectResponse(
            id=material.id,
            class_id=material.class_id,
            subject_id=material.subject_id,
            subject_name=subject_name,
            teacher_id=material.teacher_id,
            title=material.title,
            description=material.description,
            file_url=material.file_url,
            file_type=material.file_type,
            file_size=material.file_size,
            upload_date=material.upload_date,
            created_at=material.created_at
        ))
    
    return StudentClassMaterialsResponse(
        materials=materials_list,
        total_materials=len(materials_list),
        total_subjects=len(subject_ids)
    )

