from document_issue.project import ProjectBase

from document_issue_api.common import partial_model


class ProjectPost(ProjectBase):
    pass


class ProjectGet(ProjectPost):
    """Project get schema."""

    id: int


ProjectPatch = partial_model("ProjectPatch", ProjectPost)
