from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.concurrency import run_in_threadpool

from app import models, schemas, security


async def get_user(db: AsyncSession, user_id: int) -> models.User | None:
    return await db.get(models.User, user_id)


async def get_user_by_email(db: AsyncSession, email: str) -> models.User | None:
    stmt = select(models.User).where(models.User.email == email)
    return (await db.scalars(stmt)).first()


async def create_user(db: AsyncSession, data: schemas.UserCreate) -> models.User:
    hashed_password = await run_in_threadpool(security.hash_password, data.password)
    user = models.User(
        email=data.email,
        hashed_password=hashed_password,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_task(db: AsyncSession, task_id: int) -> models.Task | None:
    return await db.get(models.Task, task_id)


async def get_tasks(
    db: AsyncSession,
    owner_id: int,
    skip: int = 0,
    limit: int = 100,
    is_done: bool | None = None,
    project_id: int | None = None,
) -> list[models.Task]:
    stmt = (
        select(models.Task)
        .options(selectinload(models.Task.project))
        .where(models.Task.owner_id == owner_id)
        .order_by(models.Task.id)
    )
    if is_done is not None:
        stmt = stmt.where(models.Task.is_done == is_done)
    if project_id is not None:
        stmt = stmt.where(models.Task.project_id == project_id)
    stmt = stmt.offset(skip).limit(limit)

    return list(await db.scalars(stmt))


async def create_task(db: AsyncSession, data: schemas.TaskCreate, owner_id: int) -> models.Task:
    task = models.Task(**data.model_dump(), owner_id=owner_id)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def update_task(db: AsyncSession, task: models.Task, data: schemas.TaskUpdate) -> models.Task:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task: models.Task) -> None:
    await db.delete(task)
    await db.commit()


async def get_project(db: AsyncSession, project_id: int) -> models.Project | None:
    return await db.get(models.Project, project_id)


async def get_projects(
    db: AsyncSession, owner_id: int, skip: int = 0, limit: int = 100
) -> list[models.Project]:
    stmt = (
        select(models.Project)
        .order_by(models.Project.id)
        .where(models.Project.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
    )
    return list(await db.scalars(stmt))


async def get_project_with_tasks(db: AsyncSession, project_id: int) -> models.Project | None:
    stmt = (
        select(models.Project)
        .options(selectinload(models.Project.tasks))
        .where(models.Project.id == project_id)
    )
    return (await db.scalars(stmt)).first()


async def create_project(
    db: AsyncSession, data: schemas.ProjectCreate, owner_id: int
) -> models.Project:
    project = models.Project(**data.model_dump(), owner_id=owner_id)
    db.add(project)
    try:
        await db.commit()
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Project already exists") from err
    await db.refresh(project)
    return project


async def delete_project(db: AsyncSession, project: models.Project) -> None:
    await db.delete(project)
    await db.commit()
