"""Read-only discovery of shared domain models, independent of API persistence.

Names are an explicit, case-sensitive public catalogue, not Python import paths.
``Project`` describes project metadata; ``ProjectCode`` is ``codes.Project``.
Schemas use canonical field names (``by_alias=False``) in validation mode.
They describe model input structure, not every constraint in custom validators.
"""

from typing import Any

from document_issue.codes import (
    Classification,
    CodeDefinitions,
    FunctionalBreakdown,
    InformationType,
    Level,
    Originator,
    Volume,
)
from document_issue.codes import Project as ProjectCode
from document_issue.document import Document, FormatConfiguration
from document_issue.document_issue import (
    DocumentIssue,
    DocumentIssueClassification,
    DocumentIssueV2,
)
from document_issue.issue import Issue
from document_issue.meta import DocumentCodesMap, DocumentMetadataMap, LookupData
from document_issue.person import Person
from document_issue.project import Project
from document_issue.project_role import PersonRole, ProjectRoles
from document_issue.role import DocumentRole, Role
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

SCHEMA_MODELS: dict[str, type[BaseModel]] = {
    "Document": Document,
    "FormatConfiguration": FormatConfiguration,
    "Project": Project,
    "Person": Person,
    "Role": Role,
    "DocumentRole": DocumentRole,
    "PersonRole": PersonRole,
    "ProjectRoles": ProjectRoles,
    "Issue": Issue,
    "DocumentIssue": DocumentIssue,
    "DocumentIssueClassification": DocumentIssueClassification,
    "DocumentIssueV2": DocumentIssueV2,
    "CodeDefinitions": CodeDefinitions,
    "ProjectCode": ProjectCode,
    "Originator": Originator,
    "FunctionalBreakdown": FunctionalBreakdown,
    "Level": Level,
    "Volume": Volume,
    "InformationType": InformationType,
    "Classification": Classification,
    "DocumentCodesMap": DocumentCodesMap,
    "DocumentMetadataMap": DocumentMetadataMap,
    "LookupData": LookupData,
}

router = APIRouter(prefix="/schemas", tags=["schemas"])


@router.get("/")
def list_schemas() -> list[str]:
    """List the registered, case-sensitive model names in alphabetical order."""
    return sorted(SCHEMA_MODELS)


@router.get("/{model_name}")
def get_schema(model_name: str) -> dict[str, Any]:
    """Return a validation JSON Schema using canonical field names, not aliases.

    Nested definitions are included in ``$defs`` with local ``$ref`` links.
    No database access or model instantiation is needed.
    """
    model = SCHEMA_MODELS.get(model_name)
    if model is None:
        raise HTTPException(status_code=404, detail="Unknown schema model")
    return model.model_json_schema(by_alias=False, mode="validation")
