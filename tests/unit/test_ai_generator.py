from unittest.mock import AsyncMock, patch

import pytest

from aitester.ai.business_logic import BusinessLogicGenerator
from aitester.ai.validators import AITestCase
from aitester.parser.models import ParsedEndpoint, ParsedParameter


@pytest.fixture
def simple_endpoint():
    return ParsedEndpoint(
        path="/orders",
        method="POST",
        parameters=[
            ParsedParameter.model_validate(
                {"name": "user_id", "in": "query", "required": True, "schema": {"type": "integer"}}
            )
        ],
        summary="Create a new order"
    )

@pytest.mark.asyncio
async def test_ai_generator_success(simple_endpoint):
    # Mock AI response
    mock_payload = [
        AITestCase(
            name="Idempotency",
            description="Test idempotency",
            method="POST",
            path="/orders",
            expected_status=409,
            query_params={"user_id": 123},
            request_body={"item": "apple"}
        ),
        AITestCase(
            name="State Flow",
            description="Test state flow",
            method="POST",
            path="/orders",
            expected_status=422,
            query_params={"user_id": 123},
            request_body={"item": "apple", "quantity": -5}
        )
    ]

    generator = BusinessLogicGenerator(endpoint=simple_endpoint, test_run_id="run-ai")

    with patch.object(generator.ai_client, "generate_with_retry", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = mock_payload

        test_cases = await generator.generate_async()

        assert len(test_cases) == 2

        # Verify first test case
        assert test_cases[0].category == "AI_LOGIC - Idempotency"
        assert test_cases[0].expected_status_code == 409
        assert test_cases[0].query_params == {"user_id": 123}
        assert test_cases[0].body == {"item": "apple"}

        # Verify second test case
        assert test_cases[1].category == "AI_LOGIC - State Flow"
        assert test_cases[1].expected_status_code == 422

        # Verify prompt contained necessary endpoint info
        mock_generate.assert_called_once()
        prompt = mock_generate.call_args[0][0]
        assert "/orders" in prompt
        assert "Create a new order" in prompt

@pytest.mark.asyncio
async def test_ai_generator_failure_returns_empty(simple_endpoint):
    generator = BusinessLogicGenerator(endpoint=simple_endpoint, test_run_id="run-ai")

    with patch.object(generator.ai_client, "generate_with_retry", new_callable=AsyncMock) as mock_generate:
        mock_generate.side_effect = Exception("AI API down")

        test_cases = await generator.generate_async()

        # Should gracefully handle failure and return empty list
        assert len(test_cases) == 0

