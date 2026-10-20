import logging
import typing as ty

from sqlalchemy.orm import Session

from document_issue_api import models
from document_issue_api.common import require, validate_patch
from document_issue_api.project import schemas

logger = logging.getLogger(__name__)


def post_project(db: Session, project: schemas.ProjectPost) -> models.Project:
    """Create a new project.

    Args:
        db (Session): The session linking to the database
        project (schemas.ProjectPost): The project to post

    Returns:
        models.Project: The postd project

    """
    db_ = models.Project(**project.model_dump(by_alias=False))
    db.add(db_)
    db.flush()
    db.refresh(db_)
    return db_


def get_project(db: Session, project_id: int) -> models.Project:
    """Get a project by ID.

    Args:
        db (Session): The session linking to the database
        project_id (int): The ID of the project to get

    Returns:
        models.Project: The project

    """
    return require(db, models.Project, project_id)


def get_projects(
    db: Session,
    limit: int = 100,
    skip: int = 0,
) -> ty.List[models.Project]:
    """Get all projects.

    Args:
        db (Session): The session linking to the database
        limit (int, optional): The maximum number of projects to return. Defaults to 100.
        skip (int, optional): The number of projects to skip. Defaults to 0.

    Returns:
        ty.List[models.Project]: The list of projects

    """
    db_ = db.query(models.Project).offset(skip).limit(limit).all()
    return db_


def delete_project(db: Session, project_id: int) -> models.Project:
    """Delete a project by ID.

    Args:
        db (Session): The session linking to the database
        project_id (int): The ID of the project to delete

    Returns:
        models.Project: The deleted project

    """
    db_ = require(db, models.Project, project_id)
    db.delete(db_)
    db.flush()
    return db_


def patch_project(
    db: Session,
    project_id: int,
    project: schemas.ProjectPatch,
) -> models.Project:
    """Patch a project by ID.

    Args:
        db (Session): The session linking to the database
        project (schemas.ProjectPatch): The project to patch

    Returns:
        models.Project: The patched project

    """
    db_ = require(db, models.Project, project_id)
    current = {name: getattr(db_, name) for name in schemas.ProjectPost.model_fields}
    validated = validate_patch(schemas.ProjectPost, current, project)
    for field, value in validated.model_dump(by_alias=False).items():
        setattr(db_, field, value)
    db.flush()
    db.refresh(db_)
    return db_
