import logging

from sqlalchemy.orm import Session

from document_issue_api import models
from document_issue_api.common import require, validate_patch
from document_issue_api.issue import schemas

logger = logging.getLogger(__name__)


def storage_data(issue):
    # JSON mode normalizes enum defaults, but SQLAlchemy Date needs a Python date.
    return {**issue.model_dump(mode="json", by_alias=False), "date": issue.date}


# issue
def post_issue(db: Session, document_id: int, issue: schemas.IssueBasePost) -> models.Issue:
    """Create a new issue.

    Args:
        db (Session): The session linking to the database
        issue (schemas.IssueBasePost): The issue to post

    Returns:
        models.Issue: The postd issue

    """
    require(db, models.Document, document_id)
    db_issue = models.Issue(**storage_data(issue), document_id=document_id)
    db.add(db_issue)
    db.flush()
    db.refresh(db_issue)
    return db_issue


def get_issue(db: Session, issue_id: int) -> models.Issue:
    """Get an issue.

    Args:
        db (Session): The session linking to the database
        issue_id (int): The id of the issue to get

    Returns:
        models.Issue: The getd issue

    """
    return require(db, models.Issue, issue_id)


def patch_issue(db: Session, issue_id: int, issue: schemas.IssueBasePatch) -> models.Issue:
    """Patch an issue.

    Args:
        db (Session): The session linking to the database
        issue_id (int): The id of the issue to patch
        issue (schemas.IssueBasePatch): The issue patch

    Returns:
        models.Issue: The patched issue

    """
    db_issue = require(db, models.Issue, issue_id)
    current = {name: getattr(db_issue, name) for name in schemas.IssueBasePost.model_fields}
    validated = validate_patch(schemas.IssueBasePost, current, issue)
    for field, value in storage_data(validated).items():
        setattr(db_issue, field, value)
    db.flush()
    db.refresh(db_issue)
    return db_issue


def delete_issue(db: Session, issue_id: int) -> models.Issue:
    """Delete an issue.

    Args:
        db (Session): The session linking to the database
        issue_id (int): The id of the issue to delete

    Returns:
        models.Issue: The deleted issue

    """
    db_issue = require(db, models.Issue, issue_id)
    db.delete(db_issue)
    db.flush()
    return db_issue
