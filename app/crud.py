from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app import models, schemas, security


def get_user(db: Session, user_id: int) -> models.User | None:
    return db.get(models.User, user_id)


def get_user_by_email(db: Session, email: str) -> models.User | None:
    stmt = select(models.User).where(models.User.email == email)
    return db.scalars(stmt).first()


def create_user(db: Session, data: schemas.UserCreate) -> models.User:
    user = models.User(
        email=data.email,
        hashed_password=security.hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_task(db: Session, task_id: int) -> models.Task | None:
    return db.get(models.Task, task_id)


def get_tasks(db: Session,
              owner_id: int,
              skip: int = 0,
              limit: int = 100,
              is_done: bool | None =  None,
              project_id: int | None = None) -> list[models.Task]:
    stmt = (select(models.Task)
            .options(selectinload(models.Task.project))
            .where(models.Task.owner_id == owner_id)
            .order_by(models.Task.id)
    )
    if is_done is not None:
        stmt = stmt.where(models.Task.is_done == is_done)
    if project_id is not None:
        stmt = stmt.where(models.Task.project_id == project_id)
    stmt = stmt.offset(skip).limit(limit)

    return list(db.scalars(stmt))


def create_task(db: Session, data: schemas.TaskCreate, owner_id: int) -> models.Task:
    task = models.Task(**data.model_dump(), owner_id=owner_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task: models.Task, data: schemas.TaskUpdate) -> models.Task:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: models.Task) -> None:
    db.delete(task)
    db.commit()


def get_project(db: Session, project_id: int) -> models.Project | None:
    return db.get(models.Project, project_id)


def get_projects(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> list[models.Project]:
    stmt = (select(models.Project)
        .order_by(models.Project.id)
        .where(models.Project.owner_id == owner_id)
        .offset(skip).limit(limit)
    )
    return list(db.scalars(stmt))


def get_project_with_tasks(db: Session, project_id: int) -> models.Project | None:
    stmt = (select(models.Project)
        .options(selectinload(models.Project.tasks))
        .where(models.Project.id == project_id)
    )
    return db.scalars(stmt).first()


def create_project(db: Session, data: schemas.ProjectCreate, owner_id: int) -> models.Project:
    project = models.Project(**data.model_dump(), owner_id=owner_id)
    db.add(project)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Project already exists")
    db.refresh(project)
    return project


def delete_project(db: Session, project: models.Project) -> None:
    db.delete(project)
    db.commit()