import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aitester.api.dependencies import get_db
from aitester.api.schemas.project import ProjectCreate, ProjectResponse
from aitester.core.exceptions import DatabaseError, RecordNotFoundError
from aitester.db.models import Project

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Project",
)
async def create_project(project_in: ProjectCreate, db: AsyncSession = Depends(get_db)) -> Project:
    """
    Creates a new project record, optionally parsing and storing an OpenAPI spec.
    """
    try:
        new_project = Project(
            name=project_in.name,
            description=project_in.description,
            openapi_spec=project_in.openapi_spec,
        )
        db.add(new_project)
        await db.commit()
        await db.refresh(new_project)
        return new_project
    except Exception as e:
        await db.rollback()
        # In a real app, we might catch specific IntegrityErrors
        raise DatabaseError(f"Failed to create project: {str(e)}") from e


@router.get(
    "",
    response_model=list[ProjectResponse],
    summary="List all Projects",
)
async def list_projects(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
) -> list[Project]:
    """
    Retrieves a list of all projects with pagination.
    """
    stmt = select(Project).order_by(Project.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    projects = result.scalars().all()
    return list(projects)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get a Project by ID",
)
async def get_project(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Project:
    """
    Retrieves a single project by its UUID.
    """
    project = await db.get(Project, project_id)
    if not project:
        raise RecordNotFoundError(f"Project with id {project_id} not found.")
    return project
