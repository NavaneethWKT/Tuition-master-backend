from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app import models
from app.api.teacher.schemas import ClassResponse, StudyMaterialResponse, TeacherStatisticsResponse
from app.api.student.schemas import StudentResponse
from uuid import UUID

router = APIRouter(
    prefix="/api/teacher",
    tags=["Teacher"]
)


@router.get("/{teacher_id}/classes", response_model=List[ClassResponse], status_code=status.HTTP_200_OK)
async def get_teacher_classes(
    teacher_id: UUID = Path(..., description="Teacher ID"),
    db: Session = Depends(get_db)
):
    """
    Get list of all classes handled by a teacher (where teacher is the class teacher).
    """
    # Verify teacher exists
    teacher = db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Get all classes where this teacher is the class teacher
    classes = db.query(models.Class).filter(
        models.Class.class_teacher_id == teacher_id
    ).all()
    
    return classes


@router.get("/{teacher_id}/materials", response_model=List[StudyMaterialResponse], status_code=status.HTTP_200_OK)
async def get_teacher_materials(
    teacher_id: UUID = Path(..., description="Teacher ID"),
    db: Session = Depends(get_db)
):
    """
    Get list of all study materials uploaded by a teacher for classes under her.
    Only returns materials for classes where the teacher is the class teacher.
    """
    # Verify teacher exists
    teacher = db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Get all class IDs where this teacher is the class teacher
    teacher_class_ids = [
        class_obj.id for class_obj in db.query(models.Class.id).filter(
            models.Class.class_teacher_id == teacher_id
        ).all()
    ]
    
    # Get all study materials uploaded by this teacher for her classes
    if teacher_class_ids:
        materials = db.query(models.StudyMaterial).filter(
            models.StudyMaterial.teacher_id == teacher_id,
            models.StudyMaterial.class_id.in_(teacher_class_ids)
        ).all()
    else:
        materials = []
    
    return materials


@router.get("/{teacher_id}/statistics", response_model=TeacherStatisticsResponse, status_code=status.HTTP_200_OK)
async def get_teacher_statistics(
    teacher_id: UUID = Path(..., description="Teacher ID"),
    db: Session = Depends(get_db)
):
    """
    Get total number of classes and total number of students for a teacher.
    Counts all students across all classes where the teacher is the class teacher.
    """
    # Verify teacher exists
    teacher = db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Get all class IDs where this teacher is the class teacher
    teacher_class_ids = [
        class_obj.id for class_obj in db.query(models.Class.id).filter(
            models.Class.class_teacher_id == teacher_id
        ).all()
    ]
    
    # Count total classes
    total_classes = db.query(func.count(models.Class.id)).filter(
        models.Class.class_teacher_id == teacher_id
    ).scalar() or 0
    
    # Count total students across all classes
    if teacher_class_ids:
        total_students = db.query(func.count(models.Student.id)).filter(
            models.Student.class_id.in_(teacher_class_ids)
        ).scalar() or 0
    else:
        total_students = 0
    
    return TeacherStatisticsResponse(
        teacher_id=teacher_id,
        total_classes=total_classes,
        total_students=total_students
    )


@router.get("/classes/{class_id}/students", response_model=List[StudentResponse], status_code=status.HTTP_200_OK)
async def get_class_students(
    class_id: UUID = Path(..., description="Class ID"),
    db: Session = Depends(get_db)
):
    """
    Get list of all students belonging to a specific class.
    Only returns students if the class belongs to a teacher's classes.
    """
    # Verify class exists
    class_obj = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Get all students in this class
    students = db.query(models.Student).filter(
        models.Student.class_id == class_id
    ).all()
    
    return students

