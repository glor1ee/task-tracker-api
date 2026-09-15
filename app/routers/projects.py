from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])


async def get_own_project_or_404(
    project_id: int,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> models.Project:
    project = await crud.get_project(db, project_id)
    if project is None or project.owner_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("/", response_model=schemas.ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: schemas.ProjectCreate,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await crud.create_project(db, data, owner_id=current_user.id)


@router.get("/", response_model=list[schemas.ProjectRead])
async def list_projects(
    current_user: models.User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await crud.get_projects(db, current_user.id, skip=skip, limit=limit)


@router.get("/{project_id}", response_model=schemas.ProjectWithTasks)
async def retrieve_project(
    project: models.Project = Depends(get_own_project_or_404), db: AsyncSession = Depends(get_db)
):
    return await crud.get_project_with_tasks(db, project.id)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project: models.Project = Depends(get_own_project_or_404),
    db: AsyncSession = Depends(get_db),
):
    await crud.delete_project(db, project)
