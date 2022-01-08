from datetime import datetime,timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, status, HTTPException, Security
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer, HTTPAuthorizationCredentials, HTTPBearer

from fastapi_login.exceptions import InvalidCredentialsException
from app.internal.utilities import sanity_check
from app.models.models import query_user, create_user

from passlib.context import CryptContext
from pydantic import BaseModel

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    user_id: str
    username: str
    password: str
    last_logged_in: str
    role: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        # token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    # user = get_user(fake_users_db, username=token_data.username)
    user = query_user(username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_seller(current_user:User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    elif current_user.role != "seller":
        raise HTTPException(status_code=400, detail="Unauthorized seller")
    return current_user

async def get_current_active_user(current_user:User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(username,password):
    print(username,password)
    user = query_user(username)
    print(user)
    if not user:
        return False
    if not verify_password(password,user.password):
        return False
    return user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post('/signup',status_code=status.HTTP_201_CREATED)
def signup(form_data: OAuth2PasswordRequestForm=Depends()):
    if query_user(form_data.username) != None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account already exists",
            headers={"WWW-Authenticate": "Bearer"}
        )
    try:
        hashed_password = get_password_hash(form_data.password)
        user = {'key': form_data.username, 'password': hashed_password}
        if create_user(user,hashed_password):
            return {"msg":"User created"}
    except:
        error_msg = 'Failed to signup user'
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
            headers={"WWW-Authenticate": "Bearer"}
        )

@router.post("/login",status_code=status.HTTP_202_ACCEPTED)
def login(form_data: OAuth2PasswordRequestForm=Depends()):
    username = form_data.username
    password = form_data.password

    user = authenticate_user(username,password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
    
    


@router.get("/sanity_check",status_code=status.HTTP_200_OK)
def checkmarks():
    print("Performing Sanity Check")
    sanity_check()
    print("Tables created if not existed")
    return {"msg":"Sanity check performed"}
