import uuid
from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from aitester.cli.app import app

runner = CliRunner()

DEMO_SPEC = """
openapi: 3.0.0
info:
  title: E2E Demo API
  version: 1.0.0
paths:
  /demo:
    get:
      summary: Get demo data
      responses:
        '200':
          description: OK
"""

@pytest.fixture
def temp_spec_file(tmp_path):
    spec_path = tmp_path / "demo_e2e_spec.yaml"
    spec_path.write_text(DEMO_SPEC)
    return str(spec_path)

def test_e2e_demo_flow(temp_spec_file):
    """
    Test the CLI workflow safely without hitting the real DB or network.
    """
    # 1. Analyze the spec
    result_analyze = runner.invoke(app, ["analyze", "--spec", temp_spec_file])
    assert result_analyze.exit_code == 0
    assert "E2E Demo API" in result_analyze.stdout

    # 2. Run the tests
    # We patch the httpx client and DB session so asyncio.run doesn't hit loop conflicts
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value.status_code = 200
        mock_req.return_value.elapsed.total_seconds = lambda: 0.1
        mock_req.return_value.text = '{"status": "ok"}'

        with patch("aitester.cli.commands.run.AsyncSessionLocal") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_project = AsyncMock()
            mock_project.id = uuid.uuid4()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()

            result_run = runner.invoke(app, ["run", "--spec", temp_spec_file, "--base-url", "http://localhost:8000"])

            assert result_run.exit_code == 0
            assert "Execution Summary" in result_run.stdout

