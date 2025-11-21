# Tuition Master FastAPI Backend

A FastAPI application with PostgreSQL database connection for the Tuition Master platform. Automatically creates all 7 database tables on startup. **Note: No users table - authentication fields are directly in students and teachers tables.**

## Features

- FastAPI framework with automatic API documentation
- PostgreSQL database connection using SQLAlchemy
- **7 database tables** automatically created on startup:
  - Schools, Subjects, Classes, Teachers, Students, Parents, Study Materials
- Database health check endpoint
- Environment-based configuration
- Type validation with Pydantic
- UUID support with PostgreSQL extensions
- Automatic `updated_at` timestamp triggers

## Prerequisites

- **Python 3.9 - 3.13** (Python 3.14 may have compatibility issues with some packages)
- PostgreSQL database running locally
- pip (Python package manager)

## Setup Instructions

### 1. Install PostgreSQL

Make sure PostgreSQL is installed and running on your local machine.

### 2. Create Database

Create a database for the application:

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE tuition_master_db;

# Exit psql
\q
```

### 3. Install Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and update with your database credentials:

```bash
cp .env.example .env
```

Edit `.env` file with your PostgreSQL credentials:

```
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=tuition_master_db
```

**Note:** If you encounter build errors with Python 3.14, try using Python 3.11 or 3.12 instead:

```bash
# Using pyenv or similar
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Run the Application

```bash
uvicorn app.main:app --reload
```

The application will be available at:

- API: http://localhost:8000
- Interactive API docs (Swagger UI): http://localhost:8000/docs
- Alternative API docs (ReDoc): http://localhost:8000/redoc

## API Endpoints

### Health Check

- `GET /health` - Check database connection status
- `GET /tables` - List all database tables

### Database Tables

The application automatically creates the following 7 tables on startup:

1. **schools** - School information
2. **subjects** - Subject catalog
3. **classes** - Class/grade information
4. **teachers** - Teacher profiles (with authentication fields directly in table)
5. **students** - Student profiles (with authentication fields directly in table)
6. **parents** - Parent/Guardian information (linked to students via student_id)
7. **study_materials** - Study materials

## Example Usage

### Check Database Health

```bash
curl "http://localhost:8000/health"
```

### List All Tables

```bash
curl "http://localhost:8000/tables"
```

### View API Documentation

Visit http://localhost:8000/docs for interactive API documentation (Swagger UI) or http://localhost:8000/redoc for ReDoc.

## Project Structure

```
fastapi-postgres-app/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application and routes
│   ├── database.py      # Database connection and session
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   └── config.py        # Configuration settings
├── .env.example         # Example environment variables
├── .gitignore
├── requirements.txt     # Python dependencies
└── README.md
```

## Database Schema

The database schema matches the Tuition Master requirements with 7 tables. All tables use UUID as primary keys and include automatic timestamp management. **Authentication fields (email, phone, password_hash) are stored directly in students and teachers tables** - there is no separate users table. Parents are stored in a separate **parents** table with a foreign key to students.

### Key Features:

- **UUID Primary Keys** - All tables use UUID for primary keys
- **Automatic Timestamps** - `created_at` and `updated_at` are automatically managed
- **Foreign Key Relationships** - Proper relationships between all entities
- **PostgreSQL Extensions** - UUID and crypto extensions enabled automatically
- **Triggers** - Automatic `updated_at` timestamp updates via database triggers

Refer to `app/models.py` for the complete SQLAlchemy model definitions.

## Troubleshooting

### Database Connection Error

If you encounter connection errors:

1. Verify PostgreSQL is running: `pg_isready` or `psql -U postgres`
2. Check your `.env` file has correct credentials
3. Ensure the database exists: `psql -U postgres -l`
4. Verify PostgreSQL is listening on the correct port (default: 5432)

### Port Already in Use

If port 8000 is already in use, run with a different port:

```bash
uvicorn app.main:app --reload --port 8001
```

## License

MIT
