from fastapi import HTTPException

from document_issue_api import models
from document_issue_api.common import require
from document_issue_api.document_role.schemas import DocumentRoleDeleted, DocumentRoleGet
from document_issue_api.project_role.schemas import ProjectRoleGet


def assignment_for_document(db, document_id, role_id):
    document = require(db, models.Document, document_id)
    require(db, models.Role, role_id)
    assignment = db.get(models.ProjectRole, (document.project_id, role_id))
    if assignment is None:
        raise HTTPException(409, "Assign the role to this document's project first")
    return assignment


def role_response(db, selection):
    assignment = assignment_for_document(db, selection.document_id, selection.role_id)
    return DocumentRoleGet(
        **ProjectRoleGet.model_validate(assignment).model_dump(by_alias=False),
        document_id=selection.document_id,
    )


def post_document_role(db, role_id, document_id):
    assignment_for_document(db, document_id, role_id)
    row = models.DocumentRole(role_id=role_id, document_id=document_id)
    db.add(row)
    db.flush()
    return role_response(db, row)


def get_document_roles(db, document_id):
    document = require(db, models.Document, document_id)
    return [
        role_response(db, row)
        for row in sorted(document.document_role, key=lambda item: item.role_id)
    ]


def delete_document_role(db, role_id, document_id):
    row = require(db, models.DocumentRole, (document_id, role_id))
    assignment = db.get(models.ProjectRole, (row.document.project_id, role_id))
    response = (
        role_response(db, row) if assignment is not None
        else DocumentRoleDeleted(document_id=document_id, role_id=role_id)
    )
    db.delete(row)
    db.flush()
    return response
