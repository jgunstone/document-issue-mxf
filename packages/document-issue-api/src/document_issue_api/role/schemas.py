from document_issue.role import Role

from document_issue_api.common import partial_model


class RolePost(Role):
    """Role post schema."""

    is_archived: bool = False


class RoleGet(RolePost):
    """Role get schema."""

    id: int


RolePatch = partial_model("RolePatch", RolePost)
