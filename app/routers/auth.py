from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import auth_service, crud, schemas, security
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=schemas.UserRead,
status_code=status.HTTP_201_CREATED)
def register(data: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, data.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    return crud.create_user(db, data)


@router.post("/token", response_model=schemas.TokenPair)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, form.username)
    if user is None or not security.verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password",
                            headers={"WWW-Authenticate": "Bearer"},)
    return auth_service.issue_tokens(db, user.id)


@router.post("/refresh", response_model=schemas.TokenPair)
def refresh(data:schemas.RefreshRequest, db: Session = Depends(get_db)):
    try:
        return auth_service.rotate(db, data.refresh_token)
    except auth_service.InvalidRefreshToken:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid refresh token",
                            headers={"WWW-Authenticate": "Bearer"},
                            ) from None


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(data: schemas.RefreshRequest, db: Session = Depends(get_db)):
    auth_service.logout(db, data.refresh_token)