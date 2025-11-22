from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app import models
from app.api.school_admin.schemas import (
    SchoolCreate, SchoolResponse, TeacherCreate, TeacherResponse,
    SchoolDetailsResponse, ClassCreate, ClassResponse
)
from app.utils.password import hash_password
from datetime import datetime
from uuid import UUID

router = APIRouter(
    prefix="/api/school-admin",
    tags=["School Admin"]
)


@router.post("/schools", response_model=SchoolResponse, status_code=status.HTTP_201_CREATED)
async def create_school(
    school_data: SchoolCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new school.
    """
    # Check if contact_email already exists
    existing_school = db.query(models.School).filter(
        models.School.contact_email == school_data.contact_email
    ).first()
    
    if existing_school:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School with this contact email already exists"
        )
    
    # Hash password
    password_hash = hash_password(school_data.password)
    
    # Create school
    school = models.School(
        name=school_data.name,
        address=school_data.address,
        contact_phone=school_data.contact_phone,
        contact_email=school_data.contact_email,
        establishment_year=school_data.establishment_year,
        board_affiliation=school_data.board_affiliation,
        city=school_data.city,
        state=school_data.state,
        pincode=school_data.pincode,
        principal_name=school_data.principal_name,
        principal_email=school_data.principal_email,
        principal_phone=school_data.principal_phone,
        admin_name=school_data.admin_name,
        admin_email=school_data.admin_email,
        admin_phone=school_data.admin_phone,
        password_hash=password_hash
    )
    
    db.add(school)
    db.commit()
    db.refresh(school)
    
    return school


@router.post("/teachers", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    teacher_data: TeacherCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new teacher.
    """
    # Verify school exists
    school = db.query(models.School).filter(models.School.id == teacher_data.school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )
    
    # Check if phone or email already exists
    if teacher_data.phone:
        existing_teacher = db.query(models.Teacher).filter(
            models.Teacher.phone == teacher_data.phone
        ).first()
        if existing_teacher:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Teacher with this phone number already exists"
            )
    
    if teacher_data.email:
        existing_teacher = db.query(models.Teacher).filter(
            models.Teacher.email == teacher_data.email
        ).first()
        if existing_teacher:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Teacher with this email already exists"
            )
    
    # Hash password
    password_hash = hash_password(teacher_data.password)
    
    # Parse joining_date
    try:
        joining_date = datetime.strptime(teacher_data.joining_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    # Create teacher
    teacher = models.Teacher(
        school_id=teacher_data.school_id,
        full_name=teacher_data.full_name,
        email=teacher_data.email,
        phone=teacher_data.phone,
        password_hash=password_hash,
        subjects=teacher_data.subjects,
        qualification=teacher_data.qualification,
        experience_years=teacher_data.experience_years,
        joining_date=joining_date
    )
    
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    
    return teacher


@router.get("/schools/{school_id}", response_model=SchoolDetailsResponse, status_code=status.HTTP_200_OK)
async def get_school_details(
    school_id: UUID = Path(..., description="School ID"),
    db: Session = Depends(get_db)
):
    """
    Get school details with statistics (total students, classes, teachers).
    """
    # Get school
    school = db.query(models.School).filter(models.School.id == school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )
    
    # Get counts
    total_students = db.query(func.count(models.Student.id)).filter(
        models.Student.school_id == school_id
    ).scalar() or 0
    
    total_classes = db.query(func.count(models.Class.id)).filter(
        models.Class.school_id == school_id
    ).scalar() or 0
    
    total_teachers = db.query(func.count(models.Teacher.id)).filter(
        models.Teacher.school_id == school_id
    ).scalar() or 0
    
    # Build response
    response = SchoolDetailsResponse(
        id=school.id,
        name=school.name,
        address=school.address,
        contact_phone=school.contact_phone,
        contact_email=school.contact_email,
        establishment_year=school.establishment_year,
        board_affiliation=school.board_affiliation,
        city=school.city,
        state=school.state,
        pincode=school.pincode,
        principal_name=school.principal_name,
        principal_email=school.principal_email,
        principal_phone=school.principal_phone,
        admin_name=school.admin_name,
        admin_email=school.admin_email,
        admin_phone=school.admin_phone,
        created_at=school.created_at,
        total_students=total_students,
        total_classes=total_classes,
        total_teachers=total_teachers
    )
    
    return response


@router.get("/schools/{school_id}/teachers", response_model=List[TeacherResponse], status_code=status.HTTP_200_OK)
async def get_school_teachers(
    school_id: UUID = Path(..., description="School ID"),
    db: Session = Depends(get_db)
):
    """
    Get list of all teachers for a school.
    """
    # Verify school exists
    school = db.query(models.School).filter(models.School.id == school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )
    
    # Get all teachers for the school
    teachers = db.query(models.Teacher).filter(
        models.Teacher.school_id == school_id
    ).all()
    
    return teachers


@router.post("/classes", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    class_data: ClassCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new class for a school.
    """
    # Verify school exists
    school = db.query(models.School).filter(models.School.id == class_data.school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )
    
    # Validate grade range (1-12)
    if class_data.grade < 1 or class_data.grade > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Grade must be between 1 and 12"
        )
    
    # Verify class teacher exists and belongs to the same school (if provided)
    if class_data.class_teacher_id:
        teacher = db.query(models.Teacher).filter(
            models.Teacher.id == class_data.class_teacher_id
        ).first()
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class teacher not found"
            )
        if teacher.school_id != class_data.school_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Class teacher does not belong to the specified school"
            )
    
    # Check if class with same school_id, grade, and section already exists
    existing_class = db.query(models.Class).filter(
        models.Class.school_id == class_data.school_id,
        models.Class.grade == class_data.grade,
        models.Class.section == class_data.section
    ).first()
    
    if existing_class:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Class with grade {class_data.grade} and section {class_data.section} already exists for this school"
        )
    
    # Create class
    class_obj = models.Class(
        school_id=class_data.school_id,
        grade=class_data.grade,
        section=class_data.section,
        class_teacher_id=class_data.class_teacher_id
    )
    
    db.add(class_obj)
    db.commit()
    db.refresh(class_obj)
    
    return class_obj


@router.get("/schools/{school_id}/classes", response_model=List[ClassResponse], status_code=status.HTTP_200_OK)
async def get_school_classes(
    school_id: UUID = Path(..., description="School ID"),
    db: Session = Depends(get_db)
):
    """
    Get list of all classes for a school.
    """
    # Verify school exists
    school = db.query(models.School).filter(models.School.id == school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )
    
    # Get all classes for the school
    classes = db.query(models.Class).filter(
        models.Class.school_id == school_id
    ).all()
    
    return classes



