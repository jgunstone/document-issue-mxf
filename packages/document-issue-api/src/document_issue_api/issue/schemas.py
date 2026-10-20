from document_issue.issue import Issue

from document_issue_api.common import partial_model


class IssueBasePost(Issue):
    """Issue post schema."""


IssueBasePatch = partial_model("IssueBasePatch", IssueBasePost)


class IssueBaseGet(Issue):
    """Issue get schema."""

    id: int
