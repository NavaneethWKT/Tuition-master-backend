"""
Script to clean up phone numbers in the database.
Removes +91- prefix and all dashes from phone numbers.
"""
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
import re

def clean_phone_number(phone: str) -> str:
    """Clean phone number by removing +91- prefix and all dashes"""
    if not phone:
        return phone
    
    # Remove +91- prefix (case insensitive)
    phone = re.sub(r'^\+91-?', '', phone, flags=re.IGNORECASE)
    
    # Remove all dashes
    phone = phone.replace('-', '')
    
    # Remove any other non-digit characters except spaces (optional)
    # But keep it simple - just remove dashes as requested
    return phone.strip()

def cleanup_phone_numbers():
    """Clean up all phone numbers in the database"""
    db = SessionLocal()
    
    try:
        # Clean schools table
        print("Cleaning schools table...")
        schools = db.query(models.School).all()
        for school in schools:
            if school.contact_phone:
                school.contact_phone = clean_phone_number(school.contact_phone)
            if school.principal_phone:
                school.principal_phone = clean_phone_number(school.principal_phone)
            if school.admin_phone:
                school.admin_phone = clean_phone_number(school.admin_phone)
        print(f"  Updated {len(schools)} schools")
        
        # Clean teachers table
        print("Cleaning teachers table...")
        teachers = db.query(models.Teacher).all()
        for teacher in teachers:
            if teacher.phone:
                teacher.phone = clean_phone_number(teacher.phone)
        print(f"  Updated {len(teachers)} teachers")
        
        # Clean students table
        print("Cleaning students table...")
        students = db.query(models.Student).all()
        for student in students:
            if student.phone:
                student.phone = clean_phone_number(student.phone)
        print(f"  Updated {len(students)} students")
        
        # Clean parents table
        print("Cleaning parents table...")
        parents = db.query(models.Parent).all()
        for parent in parents:
            if parent.phone:
                parent.phone = clean_phone_number(parent.phone)
        print(f"  Updated {len(parents)} parents")
        
        db.commit()
        print("\n✓ All phone numbers cleaned successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error cleaning phone numbers: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_phone_numbers()

