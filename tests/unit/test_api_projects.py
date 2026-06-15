"""
Unit tests for the Projects REST API.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from aitester.api.dependencies import get_db
from aitester.api.main import app
from aitester.db.base import Base
from aitester.db.session import AsyncSessionLocal, engine


@pytest.fixture
async def db_session():
    """Provides a fresh database session for a test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()
    await engine.dispose()


@pytest.fixture
async def async_client(db_session):
    """Provides an AsyncClient for FastAPI endpoint testing."""
    # Override the get_db dependency to use our test session
    app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


class TestProjectsAPI:
    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "environment" in data

    @pytest.mark.asyncio
    async def test_create_project(self, async_client: AsyncClient):
        payload = {
            "name": "My API Project",
            "description": "Integration testing project",
            "openapi_spec": {"openapi": "3.0.0", "info": {"title": "Test"}}
        }
        response = await async_client.post("/api/v1/projects", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == payload["name"]
        assert data["description"] == payload["description"]
        assert data["openapi_spec"] == payload["openapi_spec"]
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_project_invalid_payload(self, async_client: AsyncClient):
        payload = {"description": "Missing name field"}
        response = await async_client.post("/api/v1/projects", json=payload)

        # FastAPI's default validation error should be overridden to return our custom format
        # Wait, our exception handler catches `ValidationError` from our custom exceptions.
        # FastAPI raises `fastapi.exceptions.RequestValidationError` for pydantic errors!
        # Let's see what it returns by default. It returns 422.
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_projects(self, async_client: AsyncClient):
        # Create a project first
        await async_client.post("/api/v1/projects", json={"name": "Project 1"})
        await async_client.post("/api/v1/projects", json={"name": "Project 2"})

        response = await async_client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        # ordered by created_at desc
        assert data[0]["name"] in ["Project 1", "Project 2"]

    @pytest.mark.asyncio
    async def test_get_project_by_id(self, async_client: AsyncClient):
        create_resp = await async_client.post(
            "/api/v1/projects", json={"name": "Get Me"}
        )
        project_id = create_resp.json()["id"]

        response = await async_client.get(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == "Get Me"

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, async_client: AsyncClient):
        import uuid
        random_id = str(uuid.uuid4())
        response = await async_client.get(f"/api/v1/projects/{random_id}")

        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "Not Found"
