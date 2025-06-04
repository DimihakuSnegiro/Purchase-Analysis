from fastapi import FastAPI, HTTPException, Form, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import update
from kafka import KafkaProducer
from passlib.context import CryptContext
from .models import User, Session as UserSession
from typing import Literal
from . import database, models
from .database import get_db, verify_session
from .external_db import get_external_db
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, timedelta
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RegisterUserRequest(BaseModel):
    user_login: str
    user_password: str
    user_role: Literal['admin', 'seller', 'customer']

class LoginUserRequest(BaseModel):
    user_login: str
    user_password: str

@app.on_event("startup")
async def startup():
    db = next(get_db())
    database.init_db(db) 

@app.post("/register/")
async def register_user(request: RegisterUserRequest, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(request.user_password)
    expected_roles = ['seller', 'customer']
    
    if request.user_role not in expected_roles:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'seller' or 'customer'")

    if db.query(User).filter(User.user_login == request.user_login).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        user_login=request.user_login,
        user_password=hashed_password,
        user_role=request.user_role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    ext_id = None

    try:
        with get_external_db() as ext_conn, ext_conn.cursor() as cursor:
            email = f"{new_user.user_login}@example.com"
            
            if request.user_role == 'customer':
                cursor.execute("""
                    INSERT INTO customers (username, email)
                    VALUES (%s, %s)
                    ON CONFLICT (username) DO UPDATE
                    SET email = EXCLUDED.email
                    RETURNING customer_id
                    """,
                    (new_user.user_login, email)
                )
            else:
                cursor.execute("""
                    INSERT INTO sellers (username, email)
                    VALUES (%s, %s)
                    ON CONFLICT (username) DO UPDATE
                    SET email = EXCLUDED.email
                    RETURNING seller_id
                    """,
                    (new_user.user_login, email)
                )
            
            ext_id = cursor.fetchone()[0]
            ext_conn.commit()

            stmt = update(User).where(User.id == new_user.id).values(external_id=ext_id)
            db.execute(stmt)
            db.commit()

    except Exception as e:
        db.rollback()
        db.query(User).filter(User.id == new_user.id).delete()
        db.commit()
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync with external DB: {str(e)}"
        )

    return {
        "message": "User registered successfully",
        "internal_id": new_user.id,
        "external_id": ext_id,
        "role": request.user_role
    }

@app.post("/login/")
async def login(response: Response, request: LoginUserRequest, db: Session = Depends(get_db)):
    user = database.get_user_by_login(db, request.user_login)
    if user is None or not database.verify_password(request.user_password, user.user_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    session_token = uuid.uuid4()

    session = models.Session(
        session_token=session_token,
        user_id=user.user_id,
        session_start=datetime.utcnow(),
    )
    db.add(session)
    db.commit()

    response.set_cookie(key="session_token", value=str(session_token), max_age=86400, httponly=True)

    return {"message": "Login successful"}

@app.get("/check_session/")
async def check_session(request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    user_id = verify_session(session_token, db)
    return {
        "message": "Session is active",
        "user_id": user_id
    }

@app.post("/logout/")
async def logout(response: Response, request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")

    if not session_token:
        raise HTTPException(status_code=400, detail="No session found")

    session = database.get_session_by_token(db, session_token)
    if session:
        session.session_end = datetime.utcnow()
        db.commit()

    response.delete_cookie(key="session_token")

    return {"message": "Logged out successfully"}

@app.get("/api/get_user_role")
async def get_user_role(request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Не авторизован")

    session = db.query(UserSession).filter(UserSession.session_token == session_token).first()
    if not session:
        raise HTTPException(status_code=401, detail="Сессия недействительна")

    user = db.query(User).filter(User.user_id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return {"role": user.user_role}