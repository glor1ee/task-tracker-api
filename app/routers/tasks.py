from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def _validate_project_id(project_id: int | None, owner_id: int, db: Session):
    if project_id is None:
        return
    project = crud.get_project(db, project_id)
    if project is None or project.owner_id != owner_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Project not found")


def get_own_task_or_404(task_id: int,
                        current_user: models.User = Depends(get_current_user),
                        db: Session = Depends(get_db)) -> models.Task:
    task = crud.get_task(db, task_id)
    if task is None or task.owner_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post("/", response_model=schemas.TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(data: schemas.TaskCreate,
                current_user: models.User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    _validate_project_id(data.project_id, current_user.id, db)
    return crud.create_task(db, data, owner_id=current_user.id)


@router.get("/", response_model=list[schemas.TaskRead])
def list_tasks(db: Session = Depends(get_db),
              current_user: models.User = Depends(get_current_user),
              skip: int = Query(0, ge=0),
              limit: int = Query(20, ge=1, le=100),
              is_done: bool | None = None,
              project_id: int | None = None,):
    return crud.get_tasks(db, current_user.id, skip, limit, is_done, project_id)


@router.get("/{task_id}", response_model=schemas.TaskRead)
def retrieve_task(task: models.Task = Depends(get_own_task_or_404)):
    return task


@router.patch("/{task_id}", response_model=schemas.TaskRead)
def update_task(
        data: schemas.TaskUpdate,
        current_user : models.Task = Depends(get_current_user),
        task: models.Task = Depends(get_own_task_or_404),
        db: Session = Depends(get_db)):
    _validate_project_id(data.project_id, current_user.id, db)
    return crud.update_task(db, task, data)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task: models.Task = Depends(get_own_task_or_404), db: Session = Depends(get_db)):
    crud.delete_task(db, task)
