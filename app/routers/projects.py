from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])

def get_own_project_or_404(project_id: int,
                           current_user: models.User = Depends(get_current_user),
                           db: Session = Depends(get_db)) -> models.Project:
    project = crud.get_project(db, project_id)
    if project is None or project.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("/", response_model=schemas.ProjectRead,
status_code=status.HTTP_201_CREATED)
def create_project(data: schemas.ProjectCreate,
                   current_user: models.User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    return crud.create_project(db, data, owner_id=current_user.id)

@router.get("/", response_model=list[schemas.ProjectRead])
def list_projects(
        current_user: models.User = Depends(get_current_user),
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    return crud.get_projects(db, current_user.id, skip=skip, limit=limit)


@router.get("/{project_id}", response_model=schemas.ProjectWithTasks)
def retrieve_project(project: models.Project = Depends(get_own_project_or_404)) -> models.Project:
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project: models.Project = Depends(get_own_project_or_404),
                   db: Session = Depends(get_db)):
    crud.delete_project(db, project)

