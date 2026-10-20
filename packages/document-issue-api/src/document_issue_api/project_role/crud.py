from fastapi import HTTPException
from sqlalchemy import select

from document_issue_api import models
from document_issue_api.common import require
from document_issue_api.project_role import schemas


def post_project_role(db, project_id, role_id, person_id=None):
    require(db, models.Project, project_id)
    require(db, models.Role, role_id)
    if person_id is not None:
        require(db, models.Person, person_id)
    row = models.ProjectRole(project_id=project_id, role_id=role_id, person_id=person_id)
    db.add(row)
    db.flush()
    return row


def get_project_roles(db, project_id):
    project = require(db, models.Project, project_id)
    return schemas.ProjectRolesGet(project=project, project_roles=project.project_role)


def delete_project_role(db, project_id, role_id):
    row = require(db, models.ProjectRole, (project_id, role_id))
    selected = db.scalar(
        select(models.DocumentRole)
        .join(models.Document)
        .where(models.Document.project_id == project_id, models.DocumentRole.role_id == role_id)
        .limit(1),
    )
    if selected is not None:
        raise HTTPException(409, "Remove this role from the project's documents before deleting its assignment")
    response = schemas.ProjectRoleGet.model_validate(row)
    db.delete(row)
    db.flush()
    return response
