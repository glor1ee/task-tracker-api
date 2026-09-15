from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])


async def _validate_project_id(project_id: int | None, owner_id: int, db: AsyncSession):
    if project_id is None:
        return
    project = await crud.get_project(db, project_id)
    if project is None or project.owner_id != owner_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Project not found")


async def get_own_task_or_404(
    task_id: int,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> models.Task:
    task = await crud.get_task(db, task_id)
    if task is None or task.owner_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post("/", response_model=schemas.TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: schemas.TaskCreate,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _validate_project_id(data.project_id, current_user.id, db)
    return await crud.create_task(db, data, owner_id=current_user.id)


@router.get("/", response_model=list[schemas.TaskRead])
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_done: bool | None = None,
    project_id: int | None = None,
):
    return await crud.get_tasks(db, current_user.id, skip, limit, is_done, project_id)


@router.get("/{task_id}", response_model=schemas.TaskRead)
async def retrieve_task(task: models.Task = Depends(get_own_task_or_404)):
    return task


@router.patch("/{task_id}", response_model=schemas.TaskRead)
async def update_task(
    data: schemas.TaskUpdate,
    current_user: models.User = Depends(get_current_user),
    task: models.Task = Depends(get_own_task_or_404),
    db: AsyncSession = Depends(get_db),
):
    await _validate_project_id(data.project_id, current_user.id, db)
    return await crud.update_task(db, task, data)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task: models.Task = Depends(get_own_task_or_404), db: AsyncSession = Depends(get_db)
):
    await crud.delete_task(db, task)
