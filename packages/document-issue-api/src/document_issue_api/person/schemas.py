from document_issue.person import Person

from document_issue_api.common import partial_model


class PersonPost(Person):
    pass


PersonPatch = partial_model("PersonPatch", PersonPost)


class PersonGet(PersonPost):
    id: int
