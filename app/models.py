from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(200), nullable=False, unique=True, index=True)
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="owner",
                            cascade="all, delete-orphan")

    refresh_tokens = relationship("RefreshToken", back_populates="user",
                                  cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_projects_owner_id_name"),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                      nullable=True, index=True)

    owner = relationship("User", back_populates="projects")
    tasks = relationship(
"Task",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Project id:  {self.id} ({self.name})>"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), index=True, nullable=False)
    description = Column(String(500))
    is_done = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    project = relationship("Project", back_populates="tasks")

    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                      nullable=True, index=True)
    owner = relationship("User", back_populates="tasks")

    def __repr__(self):
        return f"<Task id:  {self.id} ({self.title})>"


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer,
                     ForeignKey("users.id",
                                ondelete="CASCADE",
                                name="fk_refresh_tokens_user_id_users"
                     ),
                     nullable=False,
                     index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    family_id = Column(String(36), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="refresh_tokens")