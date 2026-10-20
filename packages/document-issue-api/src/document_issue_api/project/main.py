from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from document_issue_api.database import (
    get_db,
)  # TODO: remove this dependency / make configurable
from document_issue_api.project import crud, schemas

router = APIRouter()


# project base
@router.post(
    "/project/",
    response_model=schemas.ProjectGet,
    tags=["Project"],
    summary="Post Project.",
)
def post_project(project: schemas.ProjectPost, db: Session = Depends(get_db, scope="function")):
    return crud.post_project(db=db, project=project)


@router.get(
    "/project/{project_id}",
    response_model=schemas.ProjectGet,
    tags=["Project"],
    summary="Get Project.",
)
def get_project(project_id: int, db: Session = Depends(get_db, scope="function")):
    return crud.get_project(db=db, project_id=project_id)


@router.get(
    "/project/",
    response_model=list[schemas.ProjectGet],
    tags=["Project"],
    summary="Get Projects.",
)
def get_projects(db: Session = Depends(get_db, scope="function"), limit: int = 100, skip: int = 0):
    return crud.get_projects(db=db, limit=limit, skip=skip)


@router.delete(
    "/project/{project_id}",
    response_model=schemas.ProjectGet,
    tags=["Project"],
    summary="Delete Project.",
)
def delete_project(project_id: int, db: Session = Depends(get_db, scope="function")):
    return crud.delete_project(db=db, project_id=project_id)


@router.patch(
    "/project/{project_id}",
    response_model=schemas.ProjectGet,
    tags=["Project"],
    summary="Patch Project.",
)
def patch_project(
    project_id: int,
    project: schemas.ProjectPatch,
    db: Session = Depends(get_db, scope="function"),
):
    return crud.patch_project(db=db, project_id=project_id, project=project)
