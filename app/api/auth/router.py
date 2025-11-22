from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from typing import Union
from app.database import get_db
from app import models
from app.api.auth.schemas import (
    LoginRequest,
    ParentLoginResponse,
    StudentLoginResponse,
    TeacherLoginResponse,
    SchoolLoginResponse
)
from app.utils.password import verify_password

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


@router.post(
    "/login/{persona}",
    response_model=Union[ParentLoginResponse, StudentLoginResponse, TeacherLoginResponse, SchoolLoginResponse],
    status_code=status.HTTP_200_OK
)
async def login(
    persona: str = Path(..., description="Persona type: parent, student, teacher, or school"),
    login_data: LoginRequest = ...,
    db: Session = Depends(get_db)
):
    """
    Unified login endpoint for all personas.
    Supports: parent, student, teacher, school
    """
    persona = persona.lower()
    
    if persona == "parent":
        return await _login_parent(login_data, db)
    elif persona == "student":
        return await _login_student(login_data, db)
    elif persona == "teacher":
        return await _login_teacher(login_data, db)
    elif persona == "school":
        return await _login_school(login_data, db)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid persona. Must be one of: parent, student, teacher, school"
        )


async def _login_parent(login_data: LoginRequest, db: Session) -> ParentLoginResponse:
    """Login for parent persona"""
    if not login_data.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number is required for parent login"
        )
    
    parent = db.query(models.Parent).filter(models.Parent.phone == login_data.phone).first()
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password"
        )
    
    if not verify_password(login_data.password, parent.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password"
        )
    
    return ParentLoginResponse(
        message="Login successful",
        id=parent.id,
        student_id=parent.student_id,
        full_name=parent.full_name,
        email=parent.email,
        phone=parent.phone,
        created_at=parent.created_at
    )


async def _login_student(login_data: LoginRequest, db: Session) -> StudentLoginResponse:
    """Login for student persona"""
    student = None
    
    if login_data.phone:
        student = db.query(models.Student).filter(models.Student.phone == login_data.phone).first()
    elif login_data.email:
        student = db.query(models.Student).filter(models.Student.email == login_data.email).first()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number or email is required for student login"
        )
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not verify_password(login_data.password, student.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    return StudentLoginResponse(
        message="Login successful",
        id=student.id,
        school_id=student.school_id,
        class_id=student.class_id,
        full_name=student.full_name,
        email=student.email,
        phone=student.phone,
        roll_number=student.roll_number,
        created_at=student.created_at
    )


async def _login_teacher(login_data: LoginRequest, db: Session) -> TeacherLoginResponse:
    """Login for teacher persona"""
    teacher = None
    
    if login_data.phone:
        teacher = db.query(models.Teacher).filter(models.Teacher.phone == login_data.phone).first()
    elif login_data.email:
        teacher = db.query(models.Teacher).filter(models.Teacher.email == login_data.email).first()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number or email is required for teacher login"
        )
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not verify_password(login_data.password, teacher.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    return TeacherLoginResponse(
        message="Login successful",
        id=teacher.id,
        school_id=teacher.school_id,
        full_name=teacher.full_name,
        email=teacher.email,
        phone=teacher.phone,
        subjects=teacher.subjects,
        qualification=teacher.qualification,
        created_at=teacher.created_at
    )


async def _login_school(login_data: LoginRequest, db: Session) -> SchoolLoginResponse:
    """Login for school persona"""
    school = None
    
    # School login can use email (admin_email or contact_email) or phone (contact_phone, admin_phone, or principal_phone)
    if login_data.email:
        school = db.query(models.School).filter(
            (models.School.admin_email == login_data.email) | 
            (models.School.contact_email == login_data.email)
        ).first()
    elif login_data.phone:
        school = db.query(models.School).filter(
            (models.School.contact_phone == login_data.phone) |
            (models.School.admin_phone == login_data.phone) |
            (models.School.principal_phone == login_data.phone)
        ).first()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or phone number is required for school login"
        )
    
    if not school:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password if password_hash exists
    if school.password_hash:
        if not verify_password(login_data.password, school.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
    # If no password_hash is set, allow login (for backward compatibility)
    # In production, you should require password_hash
    
    return SchoolLoginResponse(
        message="Login successful",
        id=school.id,
        name=school.name,
        contact_email=school.contact_email,
        contact_phone=school.contact_phone,
        city=school.city,
        state=school.state,
        board_affiliation=school.board_affiliation,
        created_at=school.created_at
    )

