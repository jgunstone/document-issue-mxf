import logging
import typing as ty

from sqlalchemy.orm import Session

from document_issue_api import models
from document_issue_api.common import require, validate_patch
from document_issue_api.person import schemas

logger = logging.getLogger(__name__)


# role
def post_person(db: Session, person: schemas.PersonPost) -> models.Person:
    """Create a new role.

    Args:
        db (Session): The session linking to the database
        role (schemas.RolePost): The role to post

    Returns:
        models.Role: The postd role

    """
    db_ = models.Person(**person.model_dump(by_alias=False))
    db.add(db_)
    db.flush()
    db.refresh(db_)
    return db_


def get_person(db: Session, person_id: int) -> models.Person:
    """Get a role by ID.

    Args:
        db (Session): The session linking to the database
        role_id (int): The ID of the role to get

    Returns:
        models.Role: The role

    """
    return require(db, models.Person, person_id)


def get_people(db: Session, limit: int = 100, skip: int = 0) -> ty.List[models.Person]:
    """Get all roles.

    Args:
        db (Session): The session linking to the database
        limit (int, optional): The maximum number of roles to return. Defaults to 100.
        skip (int, optional): The number of roles to skip. Defaults to 0.

    Returns:
        ty.List[models.Role]: The list of roles

    """
    db_ = db.query(models.Person).offset(skip).limit(limit).all()
    return db_


def delete_person(db: Session, person_id: int) -> models.Person:
    """Delete a role by ID.

    Args:
        db (Session): The session linking to the database
        role_id (int): The ID of the role to delete

    Returns:
        models.Role: The deleted role

    """
    db_ = require(db, models.Person, person_id)
    db.delete(db_)
    db.flush()
    return db_


def patch_person(
    db: Session,
    person_id: int,
    person: schemas.PersonPatch,
) -> models.Person:
    """Patch a person by ID.

    Args:
        db (Session): The session linking to the database
        person_id (int): The ID of the person to patch
        person (schemas.RolePatch): The person to patch

    Returns:
        models.Role: The patched person

    """
    db_ = require(db, models.Person, person_id)
    current = {name: getattr(db_, name) for name in schemas.PersonPost.model_fields}
    validated = validate_patch(schemas.PersonPost, current, person)
    for field, value in validated.model_dump(by_alias=False).items():
        setattr(db_, field, value)
    db.flush()
    db.refresh(db_)
    return db_
