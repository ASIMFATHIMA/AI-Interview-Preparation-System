import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.student import Student
from app.schemas.student import StudentRegisterRequest, StudentLoginRequest, TokenData

load_dotenv()

# JWT Settings from environment
SECRET_KEY = os.getenv("SECRET_KEY", "ai_career_companion_dev_secret_key_change_in_production_123456789")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    """
    Hashes a plain text password using bcrypt.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain text password against a bcrypt hash.
    """
    try:
        password_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a signed JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    """
    Decodes and validates a JWT access token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        student_id: Optional[int] = payload.get("student_id")
        if email is None:
            raise credentials_exception
        return TokenData(email=email, student_id=student_id)
    except JWTError:
        raise credentials_exception


def register_student(db: Session, student_data: StudentRegisterRequest) -> Student:
    """
    Registers a new student account after validating email uniqueness and hashing the password.
    """
    # Check whether the email already exists
    normalized_email = str(student_data.email).strip().lower()
    existing_student = db.query(Student).filter(Student.email == normalized_email).first()
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    # Hash the password securely
    hashed_password = hash_password(student_data.password)

    # Create new student model instance
    new_student = Student(
        name=student_data.name.strip(),
        email=normalized_email,
        password_hash=hashed_password,
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student


def authenticate_student(db: Session, login_data: StudentLoginRequest) -> Student:
    """
    Authenticates student credentials and returns student instance if valid.
    """
    student = db.query(Student).filter(Student.email == login_data.email.strip().lower()).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(login_data.password, student.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return student


def get_current_student(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Student:
    """
    Reusable FastAPI dependency that reads Bearer token, validates JWT,
    and returns the authenticated Student model from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = decode_access_token(token)
    student = db.query(Student).filter(Student.email == token_data.email).first()
    
    if student is None:
        raise credentials_exception
        
    return student
