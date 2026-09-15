from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app import auth_service, crud, schemas, security
from app.database import get_db
from app.dependencies import oauth2_scheme
from app.rate_limit import limit_login_attempts
from app.redis_client import get_redis

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    if await crud.get_user_by_email(db, data.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    return await crud.create_user(db, data)


@router.post("/token",
             response_model=schemas.TokenPair,
             dependencies=[Depends(limit_login_attempts)])
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await crud.get_user_by_email(db, form.username)
    password_ok = user is not None and await run_in_threadpool(
        security.verify_password, form.password, user.hashed_password
    )
    if not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await auth_service.issue_tokens(db, user.id)


@router.post("/refresh", response_model=schemas.TokenPair)
async def refresh(data: schemas.RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await auth_service.rotate(db, data.refresh_token)
    except auth_service.InvalidRefreshToken:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(data: schemas.RefreshRequest,
                 access_token: str = Depends(oauth2_scheme),
                 db: AsyncSession = Depends(get_db),
                 redis: Redis = Depends(get_redis)):
    await auth_service.logout(db, data.refresh_token)
    payload = security.decode_token(access_token)
    if payload is not None:
        await auth_service.revoke_access_token(redis, payload)
