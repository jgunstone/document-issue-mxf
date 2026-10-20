"""Map relational storage to the shared document presentation models."""

from document_issue.document import Document, FormatConfiguration
from document_issue.enums import RoleEnum
from document_issue.issue import Issue
from document_issue.project import ProjectBase
from document_issue.role import DocumentRole
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select

from document_issue_api import models
from document_issue_api.common import require, validate_patch
from document_issue_api.document import schemas


def document_data(row):
    """Read every persisted domain field explicitly, including nested formatting."""
    data = {
        name: getattr(row, name)
        for name in Document.model_fields
        if name != "format_configuration"
    }
    data["format_configuration"] = {
        name: getattr(row, name) for name in FormatConfiguration.model_fields
    }
    return data


def storage_data(document):
    data = document.model_dump(mode="json", by_alias=False)
    data.update(data.pop("format_configuration"))
    return data


def document_response(row):
    return schemas.DocumentBaseGet(
        **document_data(row), id=row.id, project_id=row.project_id, project=row.project,
    )


def post_document(db, document):
    require(db, models.Project, document.project_id)
    row = models.Document(**storage_data(document))
    db.add(row)
    db.flush()
    return document_response(row)


def get_document(db, document_id):
    return document_response(require(db, models.Document, document_id))


def get_documents(db, skip=0, limit=100):
    rows = db.scalars(select(models.Document).order_by(models.Document.id).offset(skip).limit(limit))
    return [document_response(row) for row in rows]


def patch_document(db, document_id, document):
    row = require(db, models.Document, document_id)
    validated = validate_patch(Document, document_data(row), document)
    for name, value in storage_data(validated).items():
        setattr(row, name, value)
    db.flush()
    return document_response(row)


def delete_document(db, document_id):
    row = require(db, models.Document, document_id)
    response = document_response(row)
    db.delete(row)
    db.flush()
    return response


def get_document_issue(db, document_id):
    row = require(db, models.Document, document_id)
    roles = []
    for selection in sorted(row.document_role, key=lambda item: item.role_id):
        assignment = db.get(models.ProjectRole, (row.project_id, selection.role_id))
        if assignment is None or assignment.person is None:
            raise HTTPException(409, f"Document role {selection.role_id} has no assigned person on this project")
        try:
            roles.append(DocumentRole(
                role_name=assignment.role.role_name, initials=assignment.person.initials,
            ))
        except ValidationError as exc:
            raise HTTPException(409, f"Role {selection.role_id} is not supported by DocumentIssue") from exc

    # DocumentIssue supplies its documented DR placeholder if no director is selected.
    # Put a real director first so the domain validator doesn't add a placeholder.
    roles.sort(key=lambda role: role.role_name != RoleEnum.director_in_charge.value)
    return schemas.DocumentIssueGet(
        **document_data(row),
        **ProjectBase.model_validate(row.project).model_dump(by_alias=False),
        document_role=roles,
        issue_history=[
            Issue.model_validate(issue)
            for issue in sorted(row.issue, key=lambda item: (item.date, item.id))
        ],
    )
