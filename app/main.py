from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from app import models
from app.database import engine, get_db, init_db

# Initialize database extensions and triggers
init_db()

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Tuition Master API",
    description="FastAPI backend for Tuition Master application with PostgreSQL database",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Tuition Master API",
        "docs": "/docs",
        "health": "/health",
        "database": "PostgreSQL with 7 tables (no users table)"
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

