import logging
import typing as ty

from sqlalchemy.orm import Session

from document_issue_api import models
from document_issue_api.common import require, validate_patch
from document_issue_api.role import schemas

logger = logging.getLogger(__name__)


# role
def post_role(db: Session, role: schemas.RolePost) -> models.Role:
    """Create a new role.

    Args:
        db (Session): The session linking to the database
        role (schemas.RolePost): The role to post

    Returns:
        models.Role: The postd role

    """
    db_ = models.Role(**role.model_dump(by_alias=False))
    db.add(db_)
    db.flush()
    db.refresh(db_)
    return db_


def get_role(db: Session, role_id: int) -> models.Role:
    """Get a role.

    Args:
        db (Session): The session linking to the database
        role_id (int): The id of the role to get

    Returns:
        models.Role: The getd role

    """
    return require(db, models.Role, role_id)


def get_roles(db: Session, skip: int = 0, limit: int = 100) -> ty.List[models.Role]:
    """Get all roles.

    Args:
        db (Session): The session linking to the database
        skip (int, optional): The number of roles to skip. Defaults to 0.
        limit (int, optional): The number of roles to return. Defaults to 100.

    Returns:
        ty.List[models.Role]: The getd roles

    """
    db_ = db.query(models.Role).offset(skip).limit(limit).all()
    return db_


def patch_role(db: Session, role_id: int, role: schemas.RolePatch) -> models.Role:
    """Patch a role.

    Args:
        db (Session): The session linking to the database
        role_id (int): The id of the role to patch
        role (schemas.RolePatch): The role patch

    Returns:
        models.Role: The patched role

    """
    db_ = require(db, models.Role, role_id)
    current = {name: getattr(db_, name) for name in schemas.RolePost.model_fields}
    validated = validate_patch(schemas.RolePost, current, role)
    for field, value in validated.model_dump(by_alias=False).items():
        setattr(db_, field, value)
    db.flush()
    db.refresh(db_)
    return db_


def delete_role(db: Session, role_id: int) -> models.Role:
    """Delete a role.

    Args:
        db (Session): The session linking to the database
        role_id (int): The id of the role to delete

    Returns:
        models.Role: The deleted role

    """
    db_ = require(db, models.Role, role_id)
    db.delete(db_)
    db.flush()
    return db_
