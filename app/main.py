from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import logging
import sys
from app import models
from app.database import engine, get_db, init_db, run_migrations

# Import routers
from app.api.auth.router import router as auth_router
from app.api.school_admin.router import router as school_admin_router
from app.api.teacher.router import router as teacher_router
from app.api.student.router import router as student_router
from app.api.parent.router import router as parent_router
from app.api.documents.router import router as documents_router
from app.api.revision.router import router as revision_router
from app.api.exam.router import router as exam_router
from app.api.evaluation.router import router as evaluation_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Output to console
    ]
)

# Set specific loggers to INFO level
logging.getLogger("app").setLevel(logging.INFO)
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)

# Initialize database extensions and triggers
init_db()

# Run database migrations automatically on startup
run_migrations()

app = FastAPI(
    title="Tuition Master API",
    description="FastAPI backend for Tuition Master application with PostgreSQL database",
    version="1.0.0"
)

# Enable CORS for all origins
# Note: To bypass ngrok browser warning page, clients should include header:
# "ngrok-skip-browser-warning: true" in their requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*", "ngrok-skip-browser-warning"],  # Allows all headers including ngrok bypass header
)

# Include routers
app.include_router(auth_router)
app.include_router(school_admin_router)
app.include_router(teacher_router)
app.include_router(student_router)
app.include_router(parent_router)
app.include_router(documents_router)
app.include_router(revision_router)
app.include_router(exam_router)
app.include_router(evaluation_router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Tuition Master API",
        "docs": "/docs",
        "health": "/health",
        "database": "PostgreSQL with 9 tables (no users table)"
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint to verify database connection"""
    try:
        # Try to execute a simple query
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )


@app.get("/tables")
async def list_tables(db: Session = Depends(get_db)):
    """List all database tables"""
    result = db.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """))
    tables = [row[0] for row in result]
    return {
        "tables": tables,
        "count": len(tables)
    }

