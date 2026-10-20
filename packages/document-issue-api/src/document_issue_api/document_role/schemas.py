from document_issue.basemodel import BaseModel

from document_issue_api.project_role.schemas import ProjectRoleGet


class DocumentRoleGet(ProjectRoleGet):
    """A selected document role and its project-scoped assignment.

    Retains the existing assignment fields while explicitly identifying the document.
    The aggregate DocumentIssue projects this into the domain's role/initials pair.
    """

    document_id: int


class DocumentRoleDeleted(BaseModel):
    """Identity-only deletion receipt for a legacy selection with no assignment."""

    document_id: int
    role_id: int
