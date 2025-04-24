from fastapi import Depends, HTTPException,FastAPI
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from . import models
from . import schemas
from .deps import get_db
from datetime import datetime, timedelta
from jose import JWTError, jwt

app = FastAPI()

SECRET_KEY = "b7e225963ef9fcf557cd614ac1944cf1034e398a3d5e9a27a921bf8a3a899d77"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email = email)
    except JWTError:
        raise credentials_exception

#Oauth 2 part
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == payload.get("sub")).first()
    if not user:
        raise credentials_exception
    return user