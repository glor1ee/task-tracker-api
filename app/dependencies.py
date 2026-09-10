from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app import crud, models, security
from app.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> models.User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id = security.decode_token(token)
    if user_id is None:
        raise credentials_error

    user = crud.get_user(db, int(user_id))
    if user is None or not user.is_active:
        raise credentials_error
    return user
