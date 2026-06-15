import pytest
from httpx import AsyncClient, ASGITransport
from aitester.api.main import app
from aitester.db.models.project import Project
from aitester.db.session import AsyncSessionLocal

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url="http://test") as ac:
        yield ac

class TestAPIHardening:
    @pytest.mark.asyncio
    async def test_404_returns_json_error(self, client):
        resp = await client.get("/api/v1/nonexistent-endpoint")
        assert resp.status_code == 404
        data = resp.json()
        assert "error" in data or "detail" in data

    @pytest.mark.asyncio
    async def test_422_returns_validation_detail(self, client):
        resp = await client.post("/api/v1/projects", json={})
        assert resp.status_code == 422
        data = resp.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_request_id_in_response_headers(self, client):
        resp = await client.get("/health")
        assert "x-request-id" in resp.headers

    @pytest.mark.asyncio
    async def test_response_time_header_present(self, client):
        resp = await client.get("/health")
        assert "x-response-time" in resp.headers

    @pytest.mark.asyncio
    async def test_cors_headers_present(self, client):
        resp = await client.options("/api/v1/projects",
            headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"})
        assert resp.status_code in [200, 204]
        assert "access-control-allow-origin" in resp.headers

    @pytest.mark.asyncio
    async def test_openapi_docs_accessible(self, client):
        resp = await client.get("/docs")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_openapi_json_accessible(self, client):
        resp = await client.get("/openapi.json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["info"]["title"] == "AITester API"

    @pytest.mark.asyncio
    async def test_run_results_endpoint(self, client):
        # Create project + simulate a run
        proj = await client.post("/api/v1/projects",
            json={"name": "Results Test", "base_url": "http://test.com"})
        assert proj.status_code in [200, 201]
        project_id = proj.json()["id"]
        
        run = await client.post(f"/api/v1/projects/{project_id}/runs",
            json={"base_url": "http://test.com", "spec_path": "tests/fixtures/simple_api.yaml", "types": ["functional"], "enable_ai": False})
        assert run.status_code in [200, 202]
        run_id = run.json()["id"]
        
        # Get results
        resp = await client.get(f"/api/v1/runs/{run_id}/results")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_list_runs_endpoint(self, client):
        import asyncio
        for _ in range(3):
            proj = await client.post("/api/v1/projects",
                json={"name": "List Runs Test", "description": "Test"})
            if proj.status_code in [200, 201]:
                break
            await asyncio.sleep(0.5)
        
        assert proj.status_code in [200, 201], f"Failed to create project: {proj.text}"
        project_id = proj.json()["id"]
        
        # Get runs
        resp = await client.get(f"/api/v1/projects/{project_id}/runs")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
