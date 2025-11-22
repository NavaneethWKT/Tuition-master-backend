"""Initial migration with all tables including mock_exams and mock_questions

Revision ID: 9b23d9c281a2
Revises: 
Create Date: 2025-11-22 03:38:48.263795

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9b23d9c281a2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    
    # Create trigger function for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # 1. Schools table (no dependencies)
    op.create_table('schools',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('address', sa.Text(), nullable=False),
    sa.Column('contact_phone', sa.String(length=20), nullable=False),
    sa.Column('contact_email', sa.String(length=255), nullable=False),
    sa.Column('registration_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('establishment_year', sa.Integer(), nullable=True),
    sa.Column('board_affiliation', sa.String(length=50), nullable=True),
    sa.Column('city', sa.String(length=100), nullable=True),
    sa.Column('state', sa.String(length=100), nullable=True),
    sa.Column('pincode', sa.String(length=20), nullable=True),
    sa.Column('principal_name', sa.String(length=255), nullable=True),
    sa.Column('principal_email', sa.String(length=255), nullable=True),
    sa.Column('principal_phone', sa.String(length=20), nullable=True),
    sa.Column('admin_name', sa.String(length=255), nullable=True),
    sa.Column('admin_email', sa.String(length=255), nullable=True),
    sa.Column('admin_phone', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('contact_email')
    )
    
    # 2. Subjects table (depends on schools)
    op.create_table('subjects',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('school_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    
    # 3. Teachers table (depends on schools)
    op.create_table('teachers',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('school_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('full_name', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('phone', sa.String(length=20), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('subjects', postgresql.ARRAY(sa.Text()), nullable=False),
    sa.Column('qualification', sa.String(length=255), nullable=True),
    sa.Column('experience_years', sa.Integer(), nullable=True),
    sa.Column('joining_date', sa.Date(), nullable=False),
    sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('phone')
    )
    
    # 4. Classes table (depends on schools and teachers)
    op.create_table('classes',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('school_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('grade', sa.Integer(), nullable=False),
    sa.Column('section', sa.String(length=10), nullable=False),
    sa.Column('class_teacher_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['class_teacher_id'], ['teachers.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.CheckConstraint('grade >= 1 AND grade <= 12', name='check_grade_range'),
    sa.UniqueConstraint('school_id', 'grade', 'section', name='uq_class')
    )
    
    # 5. Students table (depends on schools and classes)
    op.create_table('students',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('school_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('class_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('full_name', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('date_of_birth', sa.Date(), nullable=False),
    sa.Column('roll_number', sa.String(length=50), nullable=True),
    sa.Column('admission_date', sa.Date(), nullable=False),
    sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('phone')
    )
    
    # 6. Parents table (depends on students)
    op.create_table('parents',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('full_name', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('student_id')
    )
    
    # 7. Study materials table (depends on classes, subjects, teachers)
    op.create_table('study_materials',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('class_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('subject_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('teacher_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('file_url', sa.Text(), nullable=False),
    sa.Column('file_type', sa.String(length=50), nullable=False),
    sa.Column('file_size', sa.BigInteger(), nullable=True),
    sa.Column('upload_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    
    # 8. Mock exams table (depends on students)
    op.create_table('mock_exams',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('title', sa.Text(), nullable=True),
    sa.Column('document_id', sa.Text(), nullable=True),
    sa.Column('subject', sa.Text(), nullable=True),
    sa.Column('chapter', sa.Text(), nullable=True),
    sa.Column('class_level', sa.Text(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    
    # 9. Mock questions table (depends on mock_exams)
    op.create_table('mock_questions',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('exam_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('question_text', sa.Text(), nullable=False),
    sa.Column('question_type', sa.Text(), nullable=False),
    sa.Column('options', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('answer', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['exam_id'], ['mock_exams.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('mock_questions')
    op.drop_table('mock_exams')
    op.drop_table('study_materials')
    op.drop_table('parents')
    op.drop_table('students')
    op.drop_table('classes')
    op.drop_table('teachers')
    op.drop_table('subjects')
    op.drop_table('schools')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')
