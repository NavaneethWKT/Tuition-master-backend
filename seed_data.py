"""
Seed script to populate database with sample data.
Run this script to populate all tables with realistic test data.
"""
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app import models
from app.utils.password import hash_password
import uuid

# Default password for all users (for testing)
DEFAULT_PASSWORD = "password123"


def seed_schools(db: Session):
    """Seed schools table"""
    print("Seeding schools...")
    
    schools_data = [
        {
            "id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
            "name": "Greenwood High School",
            "address": "123 Education Street, Bangalore",
            "contact_phone": "8012345678",
            "contact_email": "info@greenwood.edu",
            "establishment_year": 1995,
            "board_affiliation": "CBSE",
            "city": "Bangalore",
            "state": "Karnataka",
            "pincode": "560001",
            "principal_name": "Dr. Ramesh Kumar",
            "principal_email": "principal@greenwood.edu",
            "principal_phone": "8012345679",
            "admin_name": "Mrs. Priya Sharma",
            "admin_email": "admin@greenwood.edu",
            "admin_phone": "8012345680",
            "password_hash": hash_password(DEFAULT_PASSWORD)
        },
        {
            "id": uuid.UUID("22222222-2222-2222-2222-222222222222"),
            "name": "Sunshine International School",
            "address": "456 Learning Avenue, Mumbai",
            "contact_phone": "2298765432",
            "contact_email": "contact@sunshine.edu",
            "establishment_year": 2000,
            "board_affiliation": "ICSE",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400001",
            "principal_name": "Dr. Anjali Mehta",
            "principal_email": "principal@sunshine.edu",
            "principal_phone": "2298765433",
            "admin_name": "Mr. Rajesh Patel",
            "admin_email": "admin@sunshine.edu",
            "admin_phone": "2298765434",
            "password_hash": hash_password(DEFAULT_PASSWORD)
        }
    ]
    
    for school_data in schools_data:
        school = models.School(**school_data)
        db.add(school)
    
    db.commit()
    print(f"✓ Seeded {len(schools_data)} schools")
    return schools_data


def seed_subjects(db: Session, school_ids: list):
    """Seed subjects table"""
    print("Seeding subjects...")
    
    subjects_data = [
        {"name": "Mathematics", "code": "MATH", "description": "Mathematics and Algebra"},
        {"name": "Science", "code": "SCI", "description": "Physics, Chemistry, Biology"},
        {"name": "English", "code": "ENG", "description": "English Language and Literature"},
        {"name": "Social Studies", "code": "SOC", "description": "History, Geography, Civics"},
        {"name": "Computer Science", "code": "CS", "description": "Computer Programming and Applications"},
    ]
    
    subjects = []
    for school_id in school_ids:
        for subject_data in subjects_data:
            subject = models.Subject(
                school_id=school_id,
                **subject_data
            )
            db.add(subject)
            subjects.append(subject)
    
    db.commit()
    print(f"✓ Seeded {len(subjects)} subjects")
    return subjects


def seed_teachers(db: Session, school_ids: list):
    """Seed teachers table"""
    print("Seeding teachers...")
    
    teachers_data = [
        {
            "id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
            "school_id": school_ids[0],
            "full_name": "Mr. Suresh Kumar",
            "email": "suresh.kumar@greenwood.edu",
            "phone": "9876543210",
            "password_hash": hash_password(DEFAULT_PASSWORD),
            "subjects": ["Mathematics", "Computer Science"],
            "qualification": "M.Sc Mathematics, B.Ed",
            "experience_years": 10,
            "joining_date": date(2014, 1, 15)
        },
        {
            "id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
            "school_id": school_ids[0],
            "full_name": "Mrs. Kavita Sharma",
            "email": "kavita.sharma@greenwood.edu",
            "phone": "9876543211",
            "password_hash": hash_password(DEFAULT_PASSWORD),
            "subjects": ["Science"],
            "qualification": "M.Sc Physics, B.Ed",
            "experience_years": 8,
            "joining_date": date(2016, 6, 1)
        },
        {
            "id": uuid.UUID("55555555-5555-5555-5555-555555555555"),
            "school_id": school_ids[0],
            "full_name": "Ms. Priya Reddy",
            "email": "priya.reddy@greenwood.edu",
            "phone": "9876543212",
            "password_hash": hash_password(DEFAULT_PASSWORD),
            "subjects": ["English"],
            "qualification": "M.A English, B.Ed",
            "experience_years": 5,
            "joining_date": date(2019, 4, 1)
        },
        {
            "id": uuid.UUID("66666666-6666-6666-6666-666666666666"),
            "school_id": school_ids[1],
            "full_name": "Mr. Amit Patel",
            "email": "amit.patel@sunshine.edu",
            "phone": "9876543213",
            "password_hash": hash_password(DEFAULT_PASSWORD),
            "subjects": ["Mathematics", "Science"],
            "qualification": "M.Sc Mathematics, B.Ed",
            "experience_years": 12,
            "joining_date": date(2012, 3, 1)
        },
        {
            "id": uuid.UUID("77777777-7777-7777-7777-777777777777"),
            "school_id": school_ids[1],
            "full_name": "Mrs. Neha Desai",
            "email": "neha.desai@sunshine.edu",
            "phone": "9876543214",
            "password_hash": hash_password(DEFAULT_PASSWORD),
            "subjects": ["English", "Social Studies"],
            "qualification": "M.A English, B.Ed",
            "experience_years": 7,
            "joining_date": date(2017, 7, 1)
        }
    ]
    
    teachers = []
    for teacher_data in teachers_data:
        teacher = models.Teacher(**teacher_data)
        db.add(teacher)
        teachers.append(teacher)
    
    db.commit()
    print(f"✓ Seeded {len(teachers)} teachers")
    return teachers


def seed_classes(db: Session, school_ids: list, teachers: list):
    """Seed classes table"""
    print("Seeding classes...")
    
    classes_data = []
    # Create classes for each school
    for school_id in school_ids:
        # Grades 9, 10, 11, 12 with sections A and B
        for grade in [9, 10, 11, 12]:
            for section in ["A", "B"]:
                # Assign class teacher (first teacher for school 1, second for school 2)
                teacher_index = 0 if school_id == school_ids[0] else 3
                class_teacher_id = teachers[teacher_index].id if grade == 9 and section == "A" else None
                
                class_data = {
                    "school_id": school_id,
                    "grade": grade,
                    "section": section,
                    "class_teacher_id": class_teacher_id
                }
                classes_data.append(class_data)
    
    classes = []
    for class_data in classes_data:
        class_obj = models.Class(**class_data)
        db.add(class_obj)
        classes.append(class_obj)
    
    db.commit()
    print(f"✓ Seeded {len(classes)} classes")
    return classes


def seed_students(db: Session, school_ids: list, classes: list):
    """Seed students table"""
    print("Seeding students...")
    
    students_data = []
    student_names = [
        ("Rahul", "Sharma"), ("Priya", "Patel"), ("Arjun", "Kumar"),
        ("Ananya", "Singh"), ("Vikram", "Reddy"), ("Sneha", "Nair"),
        ("Karan", "Mehta"), ("Divya", "Joshi"), ("Rohan", "Gupta"),
        ("Isha", "Desai"), ("Aryan", "Shah"), ("Maya", "Iyer"),
        ("Aditya", "Rao"), ("Kavya", "Menon"), ("Rishi", "Pillai"),
        ("Sara", "Verma"), ("Ravi", "Malhotra"), ("Neha", "Kapoor"),
        ("Vivek", "Agarwal"), ("Pooja", "Bansal"), ("Manish", "Chopra"),
        ("Deepika", "Saxena"), ("Rohit", "Tiwari"), ("Anjali", "Mishra"),
        ("Siddharth", "Jain"), ("Tanvi", "Goyal"), ("Kunal", "Bhatia"),
        ("Shreya", "Dutta"), ("Amit", "Sengupta"), ("Riya", "Bose"),
        ("Varun", "Chatterjee")
    ]
    
    student_counter = 0
    for school_idx, school_id in enumerate(school_ids):
        # Get classes for this school
        school_classes = [c for c in classes if c.school_id == school_id]
        
        # Create 15 students per school
        for i in range(15):
            first_name, last_name = student_names[student_counter % len(student_names)]
            class_obj = school_classes[i % len(school_classes)]
            
            # Make email unique by adding school index and counter
            student = {
                "id": uuid.UUID(f"{(student_counter + 1):08d}-{(student_counter + 1):04d}-{(student_counter + 1):04d}-{(student_counter + 1):04d}-{(student_counter + 1):012d}"),
                "school_id": school_id,
                "class_id": class_obj.id,
                "full_name": f"{first_name} {last_name}",
                "email": f"{first_name.lower()}.{last_name.lower()}.s{school_idx + 1}.{student_counter + 1}@student.edu",
                "phone": f"98765{43210 + student_counter}",
                "password_hash": hash_password(DEFAULT_PASSWORD),
                "date_of_birth": date(2008, 1, 1) + timedelta(days=student_counter * 30),
                "roll_number": f"ROLL{student_counter + 1:03d}",
                "admission_date": date(2020, 4, 1)
            }
            students_data.append(student)
            student_counter += 1
    
    students = []
    for student_data in students_data:
        student = models.Student(**student_data)
        db.add(student)
        students.append(student)
    
    db.commit()
    print(f"✓ Seeded {len(students)} students")
    return students


def seed_parents(db: Session, students: list):
    """Seed parents table"""
    print("Seeding parents...")
    
    parents_data = []
    for i, student in enumerate(students):
        student_name_parts = student.full_name.split()
        parent = {
            "id": uuid.UUID(f"{(i + 100):08d}-{(i + 100):04d}-{(i + 100):04d}-{(i + 100):04d}-{(i + 100):012d}"),
            "student_id": student.id,
            "full_name": f"Mr./Mrs. {student_name_parts[0]} {student_name_parts[-1]}",
            "email": f"parent.{student.email}",
            "phone": f"98765{54321 + i}",
            "password_hash": hash_password(DEFAULT_PASSWORD)
        }
        parents_data.append(parent)
    
    parents = []
    for parent_data in parents_data:
        parent = models.Parent(**parent_data)
        db.add(parent)
        parents.append(parent)
    
    db.commit()
    print(f"✓ Seeded {len(parents)} parents")
    return parents


def seed_study_materials(db: Session, classes: list, subjects: list, teachers: list):
    """Seed study materials table"""
    print("Seeding study materials...")
    
    materials_data = []
    material_types = ["PDF", "Video", "Document", "Presentation"]
    
    # Create materials for first school's classes
    school_1_classes = [c for c in classes if c.school_id == classes[0].school_id]
    school_1_subjects = [s for s in subjects if s.school_id == classes[0].school_id]
    school_1_teachers = [t for t in teachers if t.school_id == classes[0].school_id]
    
    for i, class_obj in enumerate(school_1_classes[:4]):  # First 4 classes
        for j, subject in enumerate(school_1_subjects[:3]):  # First 3 subjects
            teacher = school_1_teachers[j % len(school_1_teachers)]
            material = {
                "class_id": class_obj.id,
                "subject_id": subject.id,
                "teacher_id": teacher.id,
                "title": f"{subject.name} - Chapter {j + 1} Notes",
                "description": f"Study material for {subject.name} Chapter {j + 1}",
                "file_url": f"https://storage.example.com/materials/{subject.code}_ch{j+1}.pdf",
                "file_type": material_types[(i + j) % len(material_types)],
                "file_size": 1024 * 1024 * (2 + j)  # 2-4 MB
            }
            materials_data.append(material)
    
    materials = []
    for material_data in materials_data:
        material = models.StudyMaterial(**material_data)
        db.add(material)
        materials.append(material)
    
    db.commit()
    print(f"✓ Seeded {len(materials)} study materials")
    return materials


def seed_mock_exams(db: Session, students: list):
    """Seed mock exams table"""
    print("Seeding mock exams...")
    
    exams_data = []
    subjects = ["Mathematics", "Science", "English"]
    chapters = ["Chapter 1", "Chapter 2", "Chapter 3"]
    
    # Create 2-3 mock exams per student
    for i, student in enumerate(students[:10]):  # First 10 students
        for j in range(2):
            exam = {
                "student_id": student.id,
                "title": f"{subjects[j % len(subjects)]} Mock Test {j + 1}",
                "document_id": f"DOC-{student.id}-{j + 1}",
                "subject": subjects[j % len(subjects)],
                "chapter": chapters[j % len(chapters)],
                "class_level": "Grade 10",
                "created_by": student.id
            }
            exams_data.append(exam)
    
    exams = []
    for exam_data in exams_data:
        exam = models.MockExam(**exam_data)
        db.add(exam)
        exams.append(exam)
    
    db.commit()
    print(f"✓ Seeded {len(exams)} mock exams")
    return exams


def seed_mock_questions(db: Session, exams: list):
    """Seed mock questions table"""
    print("Seeding mock questions...")
    
    questions_data = []
    
    for exam in exams:
        # Create 5 questions per exam
        for q_num in range(5):
            question_type = "mcq" if q_num < 3 else ("tf" if q_num == 3 else "short_answer")
            
            question_data = {
                "exam_id": exam.id,
                "question_text": f"Question {q_num + 1}: What is the answer to this question?",
                "question_type": question_type,
                "answer": f"Answer {q_num + 1}" if question_type != "mcq" else None
            }
            
            # Add options for MCQ
            if question_type == "mcq":
                question_data["options"] = [
                    {"id": "A", "text": "Option A", "correct": q_num == 0},
                    {"id": "B", "text": "Option B", "correct": q_num == 1},
                    {"id": "C", "text": "Option C", "correct": q_num == 2},
                    {"id": "D", "text": "Option D", "correct": False}
                ]
            elif question_type == "tf":
                question_data["options"] = [
                    {"id": "True", "text": "True", "correct": True},
                    {"id": "False", "text": "False", "correct": False}
                ]
            
            questions_data.append(question_data)
    
    questions = []
    for question_data in questions_data:
        question = models.MockQuestion(**question_data)
        db.add(question)
        questions.append(question)
    
    db.commit()
    print(f"✓ Seeded {len(questions)} mock questions")
    return questions


def clear_all_tables(db: Session):
    """Clear all tables in reverse dependency order"""
    print("Clearing existing data...")
    
    # Delete in reverse order of dependencies
    db.query(models.MockQuestion).delete()
    db.query(models.MockExam).delete()
    db.query(models.StudyMaterial).delete()
    db.query(models.Parent).delete()
    db.query(models.Student).delete()
    db.query(models.Class).delete()
    db.query(models.Teacher).delete()
    db.query(models.Subject).delete()
    db.query(models.School).delete()
    
    db.commit()
    print("✓ Cleared all existing data")


def seed_database():
    """Main function to seed the database"""
    print("=" * 50)
    print("Starting database seeding...")
    print("=" * 50)
    
    # Initialize database
    init_db()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Clear existing data
        clear_all_tables(db)
        
        # Seed in dependency order
        schools = seed_schools(db)
        school_ids = [s["id"] for s in schools]
        
        subjects = seed_subjects(db, school_ids)
        teachers = seed_teachers(db, school_ids)
        classes = seed_classes(db, school_ids, teachers)
        students = seed_students(db, school_ids, classes)
        parents = seed_parents(db, students)
        materials = seed_study_materials(db, classes, subjects, teachers)
        exams = seed_mock_exams(db, students)
        questions = seed_mock_questions(db, exams)
        
        print("=" * 50)
        print("Database seeding completed successfully!")
        print("=" * 50)
        print(f"\nSummary:")
        print(f"  Schools: {len(schools)}")
        print(f"  Subjects: {len(subjects)}")
        print(f"  Teachers: {len(teachers)}")
        print(f"  Classes: {len(classes)}")
        print(f"  Students: {len(students)}")
        print(f"  Parents: {len(parents)}")
        print(f"  Study Materials: {len(materials)}")
        print(f"  Mock Exams: {len(exams)}")
        print(f"  Mock Questions: {len(questions)}")
        print(f"\nDefault password for all users: {DEFAULT_PASSWORD}")
        print("=" * 50)
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

