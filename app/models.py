from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, DateTime, 
    ForeignKey, CheckConstraint, UniqueConstraint, 
    BigInteger, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY as PG_ARRAY, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


# =====================================================
# 1. SCHOOLS TABLE
# =====================================================
class School(Base):
    __tablename__ = "schools"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)
    contact_phone = Column(String(20), nullable=False)
    contact_email = Column(String(255), nullable=False, unique=True)
    registration_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Additional fields from SchoolContext
    establishment_year = Column(Integer)
    board_affiliation = Column(String(50))  # CBSE, ICSE, State Board, IGCSE, IB, Other
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(20))
    
    # Administrative Details
    principal_name = Column(String(255))
    principal_email = Column(String(255))
    principal_phone = Column(String(20))
    admin_name = Column(String(255))
    admin_email = Column(String(255))
    admin_phone = Column(String(20))
    password_hash = Column(String(255))  # Optional for school login
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    subjects = relationship("Subject", back_populates="school", cascade="all, delete-orphan")
    classes = relationship("Class", back_populates="school", cascade="all, delete-orphan")


# =====================================================
# 2. SUBJECTS TABLE
# =====================================================
class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"))
    name = Column(String(255), nullable=False)
    code = Column(String(50))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    school = relationship("School", back_populates="subjects")
    study_materials = relationship("StudyMaterial", back_populates="subject", cascade="all, delete-orphan")


# =====================================================
# 3. CLASSES TABLE
# =====================================================
class Class(Base):
    __tablename__ = "classes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"))
    grade = Column(Integer, nullable=False)
    section = Column(String(10), nullable=False)
    class_teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("grade >= 1 AND grade <= 12", name='check_grade_range'),
        UniqueConstraint('school_id', 'grade', 'section', name='uq_class'),
    )
    
    # Relationships
    school = relationship("School", back_populates="classes")
    class_teacher = relationship("Teacher", foreign_keys=[class_teacher_id], back_populates="classes")
    students = relationship("Student", back_populates="class_", cascade="all, delete-orphan")
    study_materials = relationship("StudyMaterial", back_populates="class_", cascade="all, delete-orphan")


# =====================================================
# 4. TEACHERS TABLE
# =====================================================
class Teacher(Base):
    __tablename__ = "teachers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"))
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True)
    phone = Column(String(20), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    subjects = Column(PG_ARRAY(Text), nullable=False)
    qualification = Column(String(255))
    experience_years = Column(Integer)
    joining_date = Column(Date, nullable=False)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    school = relationship("School")
    classes = relationship("Class", foreign_keys="Class.class_teacher_id", back_populates="class_teacher")
    study_materials = relationship("StudyMaterial", back_populates="teacher", cascade="all, delete-orphan")


# =====================================================
# 5. STUDENTS TABLE
# =====================================================
class Student(Base):
    __tablename__ = "students"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"))
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="SET NULL"))
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True)
    phone = Column(String(20), unique=True)
    password_hash = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    roll_number = Column(String(50))
    admission_date = Column(Date, nullable=False)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    school = relationship("School")
    class_ = relationship("Class", back_populates="students")
    parent = relationship("Parent", back_populates="student", uselist=False, cascade="all, delete-orphan")
    mock_exams = relationship("MockExam", back_populates="student", cascade="all, delete-orphan")


# =====================================================
# 6. PARENTS TABLE
# =====================================================
class Parent(Base):
    __tablename__ = "parents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    student = relationship("Student", back_populates="parent")


# =====================================================
# 7. STUDY_MATERIALS TABLE
# =====================================================
class StudyMaterial(Base):
    __tablename__ = "study_materials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"))
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"))
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    file_url = Column(Text, nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(BigInteger)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    class_ = relationship("Class", back_populates="study_materials")
    subject = relationship("Subject", back_populates="study_materials")
    teacher = relationship("Teacher", back_populates="study_materials")


# =====================================================
# 8. MOCK_EXAMS TABLE
# =====================================================
class MockExam(Base):
    __tablename__ = "mock_exams"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    title = Column(Text)
    document_id = Column(Text)  # optional: source doc
    subject = Column(Text)
    chapter = Column(Text)
    class_level = Column(Text)
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    student = relationship("Student", back_populates="mock_exams")
    questions = relationship("MockQuestion", back_populates="exam", cascade="all, delete-orphan")


# =====================================================
# 9. MOCK_QUESTIONS TABLE
# =====================================================
class MockQuestion(Base):
    __tablename__ = "mock_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("mock_exams.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(Text, nullable=False)  # 'mcq'|'short_answer'|'tf'
    options = Column(JSONB)  # for mcq: [{"id":"A", "text":"...", "correct": false}, ...]
    answer = Column(Text)  # canonical answer
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    exam = relationship("MockExam", back_populates="questions")
