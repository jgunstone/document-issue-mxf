from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from document_issue_api.database import get_db
from document_issue_api.project_role import crud, schemas

router = APIRouter(tags=["Project Role"])


@router.post("/project_role/{project_id}/{role_id}", response_model=schemas.ProjectRoleGet)
def post_project_role(
    project_id: int, role_id: int, person_id: int | None = None, db: Session = Depends(get_db, scope="function"),
):
    return crud.post_project_role(db, project_id, role_id, person_id)


@router.get("/project_roles/{project_id}/", response_model=schemas.ProjectRolesGet)
def get_project_roles(project_id: int, db: Session = Depends(get_db, scope="function")):
    return crud.get_project_roles(db, project_id)


@router.delete("/project_role/{project_id}/{role_id}", response_model=schemas.ProjectRoleGet)
def delete_project_role(project_id: int, role_id: int, db: Session = Depends(get_db, scope="function")):
    return crud.delete_project_role(db, project_id, role_id)
