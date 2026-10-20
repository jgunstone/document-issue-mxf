from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from document_issue_api.database import (
    get_db,
)  # TODO: remove this dependency / make configurable
from document_issue_api.issue import crud, schemas

router = APIRouter()


# ---------- /issue/ -------------------
@router.post(
    "/issue/{document_id}",
    response_model=schemas.IssueBaseGet,
    tags=["Issue"],
    summary="Post an Issue onto a Document.",
)
def post_issue(
    issue: schemas.IssueBasePost,
    document_id: int,
    db: Session = Depends(get_db, scope="function"),
):
    return crud.post_issue(db, document_id, issue)


@router.get(
    "/issue/{issue_id}",
    response_model=schemas.IssueBaseGet,
    tags=["Issue"],
    summary="Get an Issue.",
)
def get_issue(issue_id: int, db: Session = Depends(get_db, scope="function")):
    return crud.get_issue(db, issue_id)


@router.patch(
    "/issue/{issue_id}",
    response_model=schemas.IssueBaseGet,
    tags=["Issue"],
    summary="Patch an Issue.",
)
def patch_issue(issue_id: int, issue: schemas.IssueBasePatch, db: Session = Depends(get_db, scope="function")):
    return crud.patch_issue(db, issue_id, issue)


@router.delete(
    "/issue/{issue_id}",
    response_model=schemas.IssueBaseGet,
    tags=["Issue"],
    summary="Delete an Issue.",
)
def delete_issue(issue_id: int, db: Session = Depends(get_db, scope="function")):
    return crud.delete_issue(db, issue_id)
