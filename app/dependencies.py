import os

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session, sessionmaker

from database import engine
from models.user import UserModel

SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
AUDIENCE = os.getenv('AUDIENCE', 'PP-CGA-BE')


def get_db():
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield db
    finally:
        db.close()


def verify_jwt(
        db: Session = Depends(get_db),
        token: str = Depends(APIKeyHeader(name='Authorization'))
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], audience=AUDIENCE)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid Token")

    user = db.query(UserModel).filter_by(id=payload.get("sub")).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user
