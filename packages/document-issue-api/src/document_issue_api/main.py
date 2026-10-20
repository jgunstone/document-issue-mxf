from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.exc import IntegrityError
from starlette.types import Lifespan

import document_issue_api.document.main as document_main
import document_issue_api.document_role.main as document_role_main
import document_issue_api.issue.main as issue_main
import document_issue_api.person.main as person_main
import document_issue_api.project.main as project_main
import document_issue_api.project_role.main as project_role_main
import document_issue_api.role.main as role_main
from document_issue_api.schema_catalogue import router as schemas_router

description = """API and database for managing document issue and revision control
 within the AEC Industry."""


async def integrity_error_handler(request, exc):
    """Do not expose SQL statements or private database values to clients."""
    return JSONResponse(
        status_code=409,
        content={"detail": "The operation conflicts with an existing record or relationship"},
    )


def create_app(*, lifespan: Lifespan[FastAPI] | None = None) -> FastAPI:
    """Build independent normal/demo apps with the same routes and error handling."""
    application = FastAPI(
        title="document-issue",
        description=description,
        version="0.3.0",
        contact={"name": "John Gunstone", "email": "j.gunstone@maxfordham.com"},
        lifespan=lifespan,
    )
    for router in (
        project_main.router, person_main.router, role_main.router, issue_main.router,
        document_main.router, project_role_main.router, document_role_main.router, schemas_router,
    ):
        application.include_router(router)
    application.add_exception_handler(IntegrityError, integrity_error_handler)

    @application.get("/", include_in_schema=False)
    def index():
        return RedirectResponse("/docs")

    return application


app = create_app()
