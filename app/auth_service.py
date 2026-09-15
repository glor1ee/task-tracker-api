import time
import uuid
from datetime import timedelta
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models, security
from app.config import settings

REVOKED_JTI_PREFIX = "revoked_jti:"

class InvalidRefreshToken(Exception):
    """The refresh token is invalid"""


async def issue_tokens(
    db: AsyncSession, user_id: int, family_id: str | None = None
) -> dict[str, str]:
    raw = security.generate_refresh_token()
    db.add(
        models.RefreshToken(
            user_id=user_id,
            token_hash=security.hash_token(raw),
            family_id=family_id or str(uuid.uuid4()),
            expires_at=security.utcnow() + timedelta(days=settings.refresh_token_expiry_days),
        ),
    )
    await db.commit()
    return {
        "access_token": security.create_access_token(str(user_id)),
        "refresh_token": raw,
        "token_type": "bearer",
    }


async def rotate(db: AsyncSession, raw: str) -> dict[str, str]:
    token = await _find(db, raw)
    if token is None:
        raise InvalidRefreshToken("Invalid refresh token")
    if token.revoked_at is not None:
        await revoke_family(db, token.family_id)
        raise InvalidRefreshToken()
    if token.expires_at <= security.utcnow() or not token.user.is_active:
        raise InvalidRefreshToken()

    token.revoked_at = security.utcnow()
    return await issue_tokens(db, token.user_id, family_id=token.family_id)


async def logout(db: AsyncSession, raw: str) -> None:
    token = await _find(db, raw)
    if token is not None:
        await revoke_family(db, token.family_id)


async def revoke_family(db: AsyncSession, family_id: str) -> None:
    await db.execute(
        update(models.RefreshToken)
        .where(
            models.RefreshToken.family_id == family_id,
            models.RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=security.utcnow())
    )
    await db.commit()


async def revoke_access_token(redis: Redis, payload: dict[str, Any]) -> None:
    ttl = int(payload["exp"] - time.time())
    if payload.get("jti") and ttl > 0:
        await redis.set(f"{REVOKED_JTI_PREFIX}{payload['jti']}", "1", ex=ttl)


async def is_access_token_revoked(redis: Redis, payload: dict[str, Any]) -> bool:
    jti = payload.get("jti")
    return bool(jti) and await redis.exists(f"{REVOKED_JTI_PREFIX}{jti}") == 1

async def _find(db: AsyncSession, raw: str) -> models.RefreshToken | None:
    stmt = (
        select(models.RefreshToken)
        .options(selectinload(models.RefreshToken.user))
        .where(
            models.RefreshToken.token_hash == security.hash_token(raw),
        )
    )
    return (await db.scalars(stmt)).first()
