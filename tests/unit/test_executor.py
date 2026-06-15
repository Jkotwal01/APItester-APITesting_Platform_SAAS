from unittest.mock import AsyncMock, patch

import httpx
import pytest

from aitester.db.models.test_case import TestCase
from aitester.executor.runner import AsyncTestRunner


@pytest.fixture
def sample_test_cases():
    return [
        TestCase(
            id="1",
            test_run_id="run1",
            category="FUNCTIONAL",
            endpoint="/users",
            method="GET",
            expected_status_code=200,
        ),
        TestCase(
            id="2",
            test_run_id="run1",
            category="SECURITY_SQLI",
            endpoint="/login",
            method="POST",
            body={"username": "' OR 1=1--"},
            expected_status_code=400,
        ),
        TestCase(
            id="3",
            test_run_id="run1",
            category="EDGE",
            endpoint="/items",
            method="POST",
            body={},
            expected_status_code=422,
        ),
    ]


@pytest.mark.asyncio
async def test_runner_executes_batch(sample_test_cases):
    runner = AsyncTestRunner(base_url="http://test-api.local")

    # Mock the HTTP response
    mock_response_200 = httpx.Response(
        200, text='{"status": "ok"}', request=httpx.Request("GET", "http://test-api.local/users")
    )
    mock_response_500 = httpx.Response(
        500,
        text="internal server error sql syntax",
        request=httpx.Request("POST", "http://test-api.local/login"),
    )
    mock_response_422 = httpx.Response(
        422,
        text='{"detail": "validation error"}',
        request=httpx.Request("POST", "http://test-api.local/items"),
    )

    async def mock_request(method, url, **kwargs):
        if url == "http://test-api.local/users":
            return mock_response_200
        elif url == "http://test-api.local/login":
            return mock_response_500
        elif url == "http://test-api.local/items":
            return mock_response_422
        return httpx.Response(404, request=httpx.Request(method, url))

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.side_effect = mock_request

        results = await runner.execute_all(sample_test_cases)

        assert len(results) == 3

        # Test Case 1: Expected 200, got 200 -> PASSED
        res1 = next(r for r in results if r.test_case_id == "1")
        assert res1.actual_status_code == 200
        assert res1.passed is True

        # Test Case 2: Expected 400, got 500 (and vulnerable) -> FAILED
        res2 = next(r for r in results if r.test_case_id == "2")
        assert res2.actual_status_code == 500
        assert res2.passed is False
        assert "[VULNERABILITY DETECTED]" in res2.actual_body

        # Test Case 3: Expected 422, got 422 -> PASSED
        res3 = next(r for r in results if r.test_case_id == "3")
        assert res3.actual_status_code == 422
        assert res3.passed is True


@pytest.mark.asyncio
async def test_runner_handles_connection_error():
    runner = AsyncTestRunner(base_url="http://bad-url.local")
    tc = TestCase(id="1", test_run_id="run1", endpoint="/", method="GET", expected_status_code=200)

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.side_effect = httpx.ConnectError("Failed to connect")

        results = await runner.execute_all([tc])
        assert len(results) == 1
        assert results[0].passed is False
        assert results[0].actual_status_code == 0
        assert "Failed to connect" in results[0].actual_body
