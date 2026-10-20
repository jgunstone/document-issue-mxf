from document_issue.document import Document, FormatConfiguration
from document_issue.document_issue import DocumentIssue
from document_issue.project import ProjectBase

from document_issue_api.common import partial_model


class DocumentBasePost(Document):
    """Complete document metadata and its owning project."""

    project_id: int


FormatConfigurationPatch = partial_model("FormatConfigurationPatch", FormatConfiguration)
DocumentBasePatch = partial_model(
    "DocumentBasePatch", Document, format_configuration=FormatConfigurationPatch,
)


class DocumentBaseGet(DocumentBasePost):
    """Persisted document metadata."""

    id: int
    project: ProjectBase


class DocumentIssueGet(DocumentIssue):
    """Presentation model assembled from document, project, issues and roles."""
