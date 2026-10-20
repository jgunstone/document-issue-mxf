from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from document_issue_api.database import (
    get_db,
)  # TODO: remove this dependency / make configurable
from document_issue_api.person import crud, schemas

router = APIRouter()


# ---------- /person/ -------------------
@router.post(
    "/person/",
    response_model=schemas.PersonGet,
    tags=["Person"],
    summary="Post Person.",
)
def post_person(person: schemas.PersonPost, db: Session = Depends(get_db, scope="function")):
    return crud.post_person(db=db, person=person)


@router.get(
    "/person/{person_id}",
    response_model=schemas.PersonGet,
    tags=["Person"],
    summary="Get Person.",
)
def get_person(person_id: int, db: Session = Depends(get_db, scope="function")):
    return crud.get_person(db=db, person_id=person_id)


@router.get(
    "/person/",
    response_model=list[schemas.PersonGet],
    tags=["Person"],
    summary="Get People.",
)
def get_people(db: Session = Depends(get_db, scope="function"), limit: int = 100, skip: int = 0):
    return crud.get_people(db=db, limit=limit, skip=skip)


@router.patch(
    "/person/{person_id}",
    response_model=schemas.PersonGet,
    tags=["Person"],
    summary="Patch Person.",
)
def patch_person(
    person_id: int,
    person: schemas.PersonPatch,
    db: Session = Depends(get_db, scope="function"),
):
    return crud.patch_person(db=db, person_id=person_id, person=person)


@router.delete(
    "/person/{person_id}",
    response_model=schemas.PersonGet,
    tags=["Person"],
    summary="Delete Person.",
)
def delete_person(person_id: int, db: Session = Depends(get_db, scope="function")):
    return crud.delete_person(db=db, person_id=person_id)
