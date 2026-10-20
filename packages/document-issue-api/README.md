# document-issue-api

[![PyPI - Version](https://img.shields.io/pypi/v/document-issue-api.svg)](https://pypi.org/project/document-issue-api)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/document-issue-api.svg)](https://pypi.org/project/document-issue-api)

-----

**Table of Contents**

- [document-issue-api](#document-issue-api)
  - [Installation](#installation)
  - [Development Install](#development-install)
  - [Model coverage](#model-coverage)
  - [Upgrade an existing SQLite database](#upgrade-an-existing-sqlite-database)
  - [Tests](#tests)
  - [License](#license)

## Installation

```console
pip install document-issue-api
```

## Development Install

From the repository root, with Python 3.11 or newer:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -e packages/bep -e packages/document-issue -e packages/document-issue-api pytest
```

Install the sibling `bep` package explicitly: the shared models load role/status
definitions from it, but `document-issue` does not yet declare that dependency.
The repository's Pixi environment supports Linux and Apple Silicon macOS and
already installs all three local packages.

### Try the seeded demo

```sh
pixi run demo-api
```

No database setup is required. The demo starts at <http://127.0.0.1:8000>,
redirecting `/` to Swagger UI at `/docs`. It creates its own temporary SQLite
database and preloads:

- Project **1**: Demo Community Library.
- People **1–2** and their director/project-engineer roles and assignments.
- Documents **1–2**: equipment and plantroom schedules.
- Issues **1–4**: two revisions per document.

Try `/document_issue/1`, `/document_issue/2`, `/documents/` or
`/project_roles/1/`. The regular create/update/delete endpoints work against this
demo data. **Edits reset on restart or code reload.** The configured database,
including the bundled legacy `app.db`, is not opened for demo requests, modified,
or migrated.

If an older server is already running, stop it with Ctrl+C and run the command
again; code reload alone does not switch Uvicorn to the new demo entry point.
For data that must survive a restart, use the normal API below instead.

### Start a new database

Set `DOCUMENTISSUE_DATABASE_URL` explicitly (otherwise the package's `api-dev.env`
is used when available, falling back to `sqlite:///./document-issue.db`).

```sh
export DOCUMENTISSUE_DATABASE_URL=sqlite:///./development.db
python -c "from document_issue_api.database import get_engine; from document_issue_api.models import Base; Base.metadata.create_all(get_engine())"
uvicorn document_issue_api.main:app --reload
```

Use `create_all` only for a new database. It does **not** upgrade existing tables.
Neither importing the API nor starting it performs a migration.

## Model coverage

`document-issue` owns domain fields, aliases, enums, defaults and validation.
API schemas only add identifiers, relationship references and partial-update
contracts. SQLAlchemy models are storage models, not alternate API contracts.

| Shared model | HTTP exposure |
| --- | --- |
| Project | POST/list `/project/`; GET/PATCH/DELETE `/project/{id}` |
| Person | POST/list `/person/`; GET/PATCH/DELETE `/person/{id}` |
| Role | POST `/role/`; list `/roles`; GET/PATCH/DELETE `/role/{id}` |
| Document, FormatConfiguration | POST `/document/`; list `/documents/`; GET/PATCH/DELETE `/document/{id}` |
| Issue | POST `/issue/{document_id}`; GET/PATCH/DELETE `/issue/{issue_id}` |
| PersonRole, ProjectRoles | POST/DELETE `/project_role/{project_id}/{role_id}?person_id=...`; GET `/project_roles/{project_id}/` |
| DocumentRole | POST/DELETE `/document_role/{document_id}/{role_id}`; GET `/document_roles/{document_id}/` |
| DocumentIssue | GET `/document_issue/{document_id}`; assembled from the resources above |
| Classification/V2, codes and lookup models | JSON Schema discovery only; no new persistence or aggregate-write endpoints |

See `/docs` for interactive endpoint documentation and `/openapi.json` for the
request/response contracts. Existing route URLs and successful status `200` are retained.

### JSON Schema discovery

- `GET /schemas/` returns a sorted JSON array of supported, case-sensitive names.
- `GET /schemas/Document` returns the shared model's validation JSON Schema with
  canonical field names (`by_alias=False`), including nested `$defs`.
- `Project` is project metadata; `ProjectCode` is the classification code model.
- Unknown names return `404`. The catalogue uses an explicit allowlist, not dynamic imports.

Catalogue schemas describe the domain models, **not** database IDs, PATCH requests
or the API's aliased response encoding. Use OpenAPI for those HTTP details.

### Aliases, partial updates and derived fields

Requests accept shared-model aliases and canonical names. Responses retain the
existing aliases: `document_name`, `doc_source`, `size`, `roles` and `issue`, rather
than silently switching to `document_code`, `document_source`, `paper_size`,
`document_role` and `issue_history`. Project metadata is flat in `DocumentIssue`.
The `Document` resource also has `id`, `project_id` and nested `project` metadata.

PATCH changes only supplied fields. Nested formatting updates merge with the
stored configuration; lists replace the corresponding list. Explicit `null` is
accepted only for nullable fields. Unknown PATCH fields (including document
`project_id`) return `422`; moving documents between projects is not supported.
The complete merged model is validated before saving, so issue status/revision
and document paper size follow the domain's derivation rules.

Document-role resource responses retain project-assignment fields and add
`document_id`. The aggregate projects them into shared `DocumentRole` entries
containing `role_name` and `initials`, resolving people within the document's own
project. An unassigned person or custom role unsupported by the presentation enum
returns `409` when reading the aggregate. When no director is selected, the
shared model's `DR` director placeholder is retained; this is **not** an assigned
person. A real selected director takes precedence.

Delete document selections before removing their project-role assignment.
Deleting an in-use person or role returns `409`. Deleting a project cascades its
documents, issues and selections. A legacy document-role selection with no
project assignment can still be deleted: its response contains only
`document_id` and `role_id`, rather than fabricating assignment data.

### Example workflow

The following uses a fresh database and validates the final response against the
shared model:

```python
import httpx
from document_issue import DocumentIssue
from document_issue.enums import RoleEnum

with httpx.Client(base_url="http://127.0.0.1:8000") as client:
    def post(path, payload=None, **kwargs):
        response = client.post(path, json=payload, **kwargs)
        response.raise_for_status()
        return response.json()

    project = post("/project/", {"project_number": 1234, "project_name": "Example"})
    person = post("/person/", {"initials": "AB", "full_name": "A Person"})
    role = post("/role/", {"role_name": RoleEnum.director_in_charge.value})
    post(f"/project_role/{project['id']}/{role['id']}",
         params={"person_id": person["id"]})
    document = post("/document/", {
        "project_id": project["id"],
        "document_code": "01234-MXF-XX-XX-SH-M-20003",
        "document_type": "Equipment Schedule",
        "format_configuration": {"output_author": True},
    })
    post(f"/document_role/{document['id']}/{role['id']}")
    post(f"/issue/{document['id']}", {"date": "2025-02-01", "revision_number": 1})
    response = client.get(f"/document_issue/{document['id']}")
    response.raise_for_status()
    aggregate = DocumentIssue.model_validate(response.json())
    assert aggregate.document_role[0].initials == "AB"
    assert len(aggregate.issue_history) == 1
```

Missing resources return `404`, invalid requests `422`, and database/relationship
conflicts `409`. Unexpected failures remain server errors, not misleading `404`s.
Database errors do not expose SQL statements or stored values.

## Upgrade an existing SQLite database

The new document table stores codes as strings, persists `document_type`, and
requires an owning project and explicit formatting settings. The offline
migration is restricted to file-backed SQLite databases with the known table
shape. For other engines or custom schemas, use a reviewed backend-specific migration.

1. Stop API writers and create/verify a SQLite backup (use SQLite's backup
   mechanism, not a live file copy).
2. Run read-only preflight, choosing the actual type of the legacy documents:

   ```sh
   python -m document_issue_api.migrate \
     --database-url sqlite:///./existing.db \
     --document-type "Equipment Schedule"
   ```

3. Resolve reported invalid data, then repeat preflight. Apply explicitly:

   ```sh
   python -m document_issue_api.migrate \
     --database-url sqlite:///./existing.db \
     --document-type "Equipment Schedule" \
     --apply --backup-confirmed
   ```

The backfill applies only when the type column is absent. A mixed-type legacy
database needs a reviewed per-document backfill, not one blanket type. Already
current databases and empty legacy tables do not need `--document-type`.

The migration preserves document IDs, explicit indexes and foreign-key
relationships, and rolls back on failure. It refuses numeric stored codes whose
leading zeros may already be lost; recover these from an authoritative source
into a text column rather than blindly casting them. It also refuses invalid
document metadata, NULL required formatting, duplicates, foreign-key violations,
and unsupported custom constraints/triggers/views rather than inventing data.
It migrates the document table only: existing project/person/issue data and
role assignments still need to satisfy their domain contracts.

## Tests

On Linux or Apple Silicon macOS:

```sh
pixi run -e document-issue test-document-issue
pixi run test-document-issue-api
```

After dependency metadata changes, regenerate `pixi.lock` with `pixi lock` on
a supported host before using locked CI. The repository supports `linux-64`
and `osx-arm64`.

With the source-development installation above:

```sh
python -m pytest packages/document-issue/tests
python -m pytest packages/document-issue-api/tests
```

API tests use fresh temporary databases per test, including migration tests.
They neither delete a configured database on import nor copy test data over the
application database.

## License

`document-issue-api` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.