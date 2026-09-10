import uuid
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app import models, security
from app.config import settings


class InvalidRefreshToken(Exception):
    """The refresh token is invalid"""


def issue_tokens(db: Session, user_id: int, family_id: str | None = None) -> dict[str, str]:
    raw = security.generate_refresh_token()
    db.add(
        models.RefreshToken(
            user_id=user_id,
            token_hash=security.hash_token(raw),
            family_id=family_id or str(uuid.uuid4()),
            expires_at=security.utcnow() + timedelta(days=settings.refresh_token_expiry_days),
        ),
    )
    db.commit()
    return {
        "access_token": security.create_access_token(str(user_id)),
        "refresh_token": raw,
        "token_type": "bearer",
    }


def rotate(db: Session, raw: str) -> dict[str, str]:
    token = _find(db, raw)
    if token is None:
        raise InvalidRefreshToken("Invalid refresh token")
    if token.revoked_at is not None:
        revoke_family(db, token.family_id)
        raise InvalidRefreshToken()
    if token.expires_at <= security.utcnow() or not token.user.is_active:
        raise InvalidRefreshToken()

    token.revoked_at = security.utcnow()
    return issue_tokens(db, token.user_id, family_id=token.family_id)


def logout(db: Session, raw: str) -> None:
    token = _find(db, raw)
    if token is not None:
        revoke_family(db, token.family_id)


def revoke_family(db: Session, family_id: str) -> None:
    db.execute(
        update(models.RefreshToken)
        .where(
            models.RefreshToken.family_id == family_id,
            models.RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=security.utcnow())
    )
    db.commit()


def _find(db: Session, raw: str) -> models.RefreshToken | None:
    stmt = select(models.RefreshToken).where(
        models.RefreshToken.token_hash==security.hash_token(raw),
    )
    return db.scalars(stmt).first()