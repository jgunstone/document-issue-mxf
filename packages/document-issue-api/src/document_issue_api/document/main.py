from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from document_issue_api.database import get_db
from document_issue_api.document import crud, schemas

router = APIRouter()


@router.post(
    "/document/",
    response_model=schemas.DocumentBaseGet,
    tags=["Document"],
    summary="Post Document.",
)
def post_document(document: schemas.DocumentBasePost, db: Session = Depends(get_db, scope="function")):
    return crud.post_document(db=db, document=document)


@router.get(
    "/document/{document_id}",
    response_model=schemas.DocumentBaseGet,
    tags=["Document"],
    summary="Get Document.",
)
def get_document(document_id: int, db: Session = Depends(get_db, scope="function")):
    return crud.get_document(db=db, document_id=document_id)


@router.get(
    "/document_issue/{document_id}",
    response_model=schemas.DocumentIssueGet,
    tags=["Document Issue"],
    summary="Get Document Issue.",
)
def get_document_issue(document_id: int, db: Session = Depends(get_db, scope="function")):
    return crud.get_document_issue(db=db, document_id=document_id)


@router.get(
    "/documents/",
    response_model=list[schemas.DocumentBaseGet],
    tags=["Document"],
    summary="Get Documents.",
)
def get_documents(db: Session = Depends(get_db, scope="function"), skip: int = 0, limit: int = 100):
    return crud.get_documents(db=db, skip=skip, limit=limit)


@router.patch(
    "/document/{document_id}",
    response_model=schemas.DocumentBaseGet,
    tags=["Document"],
    summary="Patch Document.",
)
def patch_document(
    document_id: int,
    document: schemas.DocumentBasePatch,
    db: Session = Depends(get_db, scope="function"),
):
    return crud.patch_document(db=db, document_id=document_id, document=document)


@router.delete(
    "/document/{document_id}",
    response_model=schemas.DocumentBaseGet,
    tags=["Document"],
    summary="Delete Document.",
)
def delete_document(document_id: int, db: Session = Depends(get_db, scope="function")):
    return crud.delete_document(db=db, document_id=document_id)
