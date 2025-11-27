# ML/AI FastAPI Architecture Guide

This document describes the architecture, patterns, and conventions used in this FastAPI application.

## Overview

This stack is optimized for building ML/AI backends and data-intensive APIs:

| Component      | Purpose                               |
| -------------- | ------------------------------------- |
| **FastAPI**    | High-performance async web framework  |
| **SQLModel**   | Type-safe ORM (SQLAlchemy + Pydantic) |
| **PostgreSQL** | Production database                   |
| **Alembic**    | Database migrations                   |
| **Pydantic**   | Data validation and serialization     |
| **Uvicorn**    | ASGI server                           |

## Building From Scratch

This is a minimal scaffolding project. You'll create files from scratch following the patterns below.

### Adding a New Feature

1. **Database Model**: Create in `src/models/[feature].py` using SQLModel
2. **Migration**: Run `alembic revision --autogenerate -m "add [feature] table"` then `alembic upgrade head`
3. **Service Layer**: Create in `src/services/[feature].py` for business logic
4. **API Route**: Create in `src/api/routes/[feature].py` with FastAPI router
5. **Register Router**: Add to `src/main.py`: `app.include_router(feature.router, prefix="/api/v1", tags=["feature"])`
6. **Tests**: Create in `tests/unit/test_[feature].py`

### Quick Start Example

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Create your first model (src/models/user.py)
# 3. Generate migration
alembic revision --autogenerate -m "add user table"

# 4. Apply migration
alembic upgrade head

# 5. Create route and service, then run
uvicorn src.main:app --reload
```

## Architecture Decisions

### Decision 1: SQLModel for Database Layer

**What**: Use SQLModel instead of raw SQLAlchemy for all database models.

**Why**:

- Combines SQLAlchemy ORM with Pydantic validation
- Single class for both database model and API schema
- Type safety with full IDE support
- Reduces boilerplate significantly

**Trade-offs**:

- Less mature than SQLAlchemy alone
- Some advanced SQLAlchemy features require workarounds

**Usage**:

```python
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
```

**Implication**: Never use raw SQLAlchemy Table definitions or declarative base.

### Decision 2: Pydantic for Request/Response Schemas

**What**: Separate Pydantic models for API schemas, distinct from database models.

**Why**:

- Control over what fields are exposed in API
- Different validation rules for create vs update
- Clear separation of concerns

**Pattern**:

```python
# Database model
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str
    hashed_password: str  # Never expose this

# API schemas
class UserCreate(SQLModel):
    email: str
    password: str  # Plain password for creation

class UserResponse(SQLModel):
    id: int
    email: str
    # No password field
```

**Implication**: Always create separate schema classes for API input/output.

### Decision 3: Dependency Injection for Database Sessions

**What**: Use FastAPI's `Depends()` for database session management.

**Why**:

- Automatic session lifecycle management
- Easy to mock for testing
- Clean separation of concerns
- Connection pooling handled automatically

**Pattern**:

```python
from fastapi import Depends
from sqlmodel import Session

def get_db():
    with Session(engine) as session:
        yield session

@router.get("/users")
async def get_users(db: Session = Depends(get_db)):
    return db.exec(select(User)).all()
```

**Implication**: Never create database sessions manually in route handlers.

### Decision 4: Alembic for Migrations

**What**: All database schema changes go through Alembic migrations.

**Why**:

- Version-controlled schema changes
- Rollback capability
- Team collaboration on schema
- Production-safe deployments

**Implication**: Never modify database schema manually or via raw SQL.

### Decision 5: Virtual Environment Isolation

**What**: All Python code runs inside a virtual environment (`venv/`).

**Why**:

- Isolated dependencies per project
- Reproducible environments
- No conflicts with system Python

**Implication**: Always activate venv before running any Python command.

### Decision 6: Async-First Design

**What**: Use `async def` for all route handlers and I/O operations.

**Why**:

- Better performance under load
- Non-blocking I/O
- Native FastAPI pattern

**Pattern**:

```python
@router.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    # Even with sync SQLModel, use async def for routes
    return db.get(User, user_id)
```

## Project Structure

```
.
├── alembic/                      # Database migrations
│   ├── versions/                 # Migration files
│   └── env.py                    # Alembic configuration
│
├── src/                          # Application source code
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py      # Dependency injection (get_db, etc.)
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── health.py        # Health check endpoint
│   │
│   ├── models/                   # SQLModel database models
│   │   └── __init__.py
│   │
│   ├── services/                 # Business logic layer
│   │   └── __init__.py
│   │
│   ├── core/                     # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py            # Settings management
│   │   └── database.py          # Database engine and session
│   │
│   └── main.py                   # FastAPI application entry
│
├── alembic.ini                   # Alembic configuration
├── pyproject.toml                # Project dependencies
├── requirements.txt              # Pinned dependencies
└── .python-version               # Python version specification
```

This is minimal scaffolding - you'll create models, routes, and services following the patterns below.

## Key Files Reference

| File                      | Purpose                     | When to Modify                    |
| ------------------------- | --------------------------- | --------------------------------- |
| `src/main.py`             | FastAPI app initialization  | Adding middleware, startup events |
| `src/core/database.py`    | Database engine and session | Rarely (connection settings)      |
| `src/core/config.py`      | Settings management         | Adding new config options         |
| `src/api/dependencies.py` | Dependency injection        | Adding new dependencies           |
| `src/api/routes/*.py`     | API endpoints               | Adding new routes                 |
| `src/models/*.py`         | Database models             | Adding/changing tables            |
| `src/services/*.py`       | Business logic              | Adding business rules             |
| `alembic/env.py`          | Migration config            | Rarely                            |

## Code Patterns

### Creating a Database Model

```python
# src/models/user.py
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str
    name: str = Field(max_length=100)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    posts: list["Post"] = Relationship(back_populates="author")
```

### Creating API Schemas

```python
# src/schemas/user.py
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # Enable ORM mode
```

### Creating an API Route

```python
# src/api/routes/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from src.api.dependencies import get_db
from src.models.user import User
from src.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    statement = select(User).offset(skip).limit(limit)
    return db.exec(statement).all()

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check for existing user
    existing = db.exec(
        select(User).where(User.email == user_in.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user (hash password in real app)
    user = User(
        email=user_in.email,
        name=user_in.name,
        hashed_password=hash_password(user_in.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db)
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update only provided fields
    for key, value in user_in.model_dump(exclude_unset=True).items():
        setattr(user, key, value)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

### Service Layer Pattern

```python
# src/services/user_service.py
from sqlmodel import Session, select
from src.models.user import User
from src.schemas.user import UserCreate

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.db.exec(statement).first()

    def create(self, user_in: UserCreate) -> User:
        user = User(
            email=user_in.email,
            name=user_in.name,
            hashed_password=hash_password(user_in.password)
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

# Usage in routes
def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)

@router.post("/users")
async def create_user(
    user_in: UserCreate,
    service: UserService = Depends(get_user_service)
):
    return service.create(user_in)
```

### Database Session Management

```python
# src/core/database.py
from sqlmodel import SQLModel, create_engine, Session
from src.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL in debug mode
    pool_pre_ping=True,   # Verify connections
)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_db():
    with Session(engine) as session:
        yield session
```

## Database Workflow

### Creating Migrations

```bash
# Activate virtual environment first!
source venv/bin/activate

# Create a new migration (auto-generates from model changes)
alembic revision --autogenerate -m "add posts table"

# Create an empty migration (for manual SQL)
alembic revision -m "add custom index"
```

### Applying Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade +1

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade abc123
```

### Migration Best Practices

```python
# alembic/versions/xxx_add_posts_table.py
def upgrade():
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('author_id', sa.Integer(), sa.ForeignKey('users.id')),
    )
    op.create_index('ix_posts_author_id', 'posts', ['author_id'])

def downgrade():
    op.drop_index('ix_posts_author_id')
    op.drop_table('posts')
```

### Database Inspection

```bash
# View current migration state
alembic current

# View migration history
alembic history

# Check what migrations would run
alembic upgrade head --sql
```

## Testing Patterns

### Test Configuration

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool

from src.main import app
from src.api.dependencies import get_db

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_db] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
```

### Writing Tests

```python
# tests/test_users.py
from fastapi.testclient import TestClient

def test_create_user(client: TestClient):
    response = client.post(
        "/users",
        json={"email": "test@example.com", "password": "secret", "name": "Test"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_get_user_not_found(client: TestClient):
    response = client.get("/users/999")
    assert response.status_code == 404
```

## Troubleshooting

### Virtual Environment Issues

**Symptom**: `ModuleNotFoundError` or wrong Python version

**Solutions**:

1. Ensure venv is activated: `source venv/bin/activate`
2. Verify Python version: `python --version`
3. Reinstall dependencies: `pip install -r requirements.txt`

### Database Connection Errors

**Symptom**: Cannot connect to PostgreSQL

**Solutions**:

1. Verify PostgreSQL is running
2. Check `DATABASE_URL` format: `postgresql://user:pass@host:5432/dbname`
3. Ensure database exists: `createdb mydb`
4. Check firewall/network settings

### Migration Conflicts

**Symptom**: Alembic heads out of sync

**Solutions**:

1. Check current state: `alembic current`
2. Merge heads if needed: `alembic merge heads`
3. Reset for development: `alembic downgrade base && alembic upgrade head`

### Type Errors with SQLModel

**Symptom**: Pydantic/SQLModel validation errors

**Solutions**:

1. Use `Optional[int]` for nullable fields with default None
2. Use `Field(default=None)` for primary keys
3. Check `from_attributes = True` in response schemas

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Uvicorn Documentation](https://www.uvicorn.org/)
