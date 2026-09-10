"""Entry point for `uvicorn main:app`; the application itself lives in app/main.py."""

from app.main import app

__all__ = ["app"]
