from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from document_issue_api.database import (
    get_db,
)  # TODO: remove this dependency / make configurable
from document_issue_api.role import crud, schemas

router = APIRouter()


# ---------- /role/ -------------------
@router.post(
    "/role/",
    response_model=schemas.RoleGet,
    tags=["Role"],
    summary="Post Role.",
)
def post_role(role: schemas.RolePost, db: Session = Depends(get_db, scope="function")):
    return crud.post_role(db=db, role=role)


@router.get(
    "/role/{role_id}",
    response_model=schemas.RoleGet,
    tags=["Role"],
    summary="Get Role.",
)
def get_role(role_id: int, db: Session = Depends(get_db, scope="function")):
    return crud.get_role(db=db, role_id=role_id)


@router.get(
    "/roles",
    response_model=list[schemas.RoleGet],
    tags=["Role"],
    summary="Get Roles.",
)
def get_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db, scope="function")):
    return crud.get_roles(db=db, skip=skip, limit=limit)


@router.patch(
    "/role/{role_id}",
    response_model=schemas.RoleGet,
    tags=["Role"],
    summary="Patch Role.",
)
def patch_role(role_id: int, role: schemas.RolePatch, db: Session = Depends(get_db, scope="function")):
    return crud.patch_role(db=db, role_id=role_id, role=role)


@router.delete(
    "/role/{role_id}",
    response_model=schemas.RoleGet,
    tags=["Role"],
    summary="Delete Role.",
)
def delete_role(role_id: int, db: Session = Depends(get_db, scope="function")):
    return crud.delete_role(db=db, role_id=role_id)
