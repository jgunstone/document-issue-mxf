from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from document_issue_api.database import get_db
from document_issue_api.document_role import crud, schemas

router = APIRouter(tags=["Document Role"])


@router.post("/document_role/{document_id}/{role_id}", response_model=schemas.DocumentRoleGet)
def post_document_role(document_id: int, role_id: int, db: Session = Depends(get_db, scope="function")):
    return crud.post_document_role(db, role_id, document_id)


@router.get("/document_roles/{document_id}/", response_model=list[schemas.DocumentRoleGet])
def get_document_roles(document_id: int, db: Session = Depends(get_db, scope="function")):
    return crud.get_document_roles(db, document_id)


@router.delete(
    "/document_role/{document_id}/{role_id}",
    response_model=schemas.DocumentRoleGet | schemas.DocumentRoleDeleted,
)
def delete_document_role(document_id: int, role_id: int, db: Session = Depends(get_db, scope="function")):
    return crud.delete_document_role(db, role_id, document_id)
