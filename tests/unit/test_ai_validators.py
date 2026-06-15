import json
import pytest

from aitester.ai.validators import (
    validate_business_logic_output,
    AITestCase,
)
from aitester.core.exceptions import AIOutputValidationError


class TestBusinessLogicValidation:
    def test_valid_output_passes(self):
        raw = json.dumps({
            "test_cases": [
                {
                    "name": "Test discount cannot exceed 100%",
                    "description": "Business rule: discounts must be 0-100%",
                    "priority": "high",
                    "method": "POST",
                    "path": "/discounts",
                    "path_params": {},
                    "query_params": {},
                    "request_body": {"amount": 150},
                    "expected_status": 400,
                    "assertions": [],
                    "business_rule": "Discount cannot exceed 100%"
                }
            ]
        })
        result = validate_business_logic_output(raw)
        assert len(result) == 1
        assert result[0].name == "Test discount cannot exceed 100%"
        assert result[0].priority == "high"

    def test_invalid_json_raises(self):
        with pytest.raises(AIOutputValidationError):
            validate_business_logic_output("not json at all")

    def test_wrong_schema_raises(self):
        raw = json.dumps({"wrong_key": []})
        with pytest.raises(AIOutputValidationError):
            validate_business_logic_output(raw)

    def test_markdown_fences_stripped(self):
        raw = '```json\n{"test_cases": []}\n```'
        result = validate_business_logic_output(raw)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_empty_test_cases_returns_empty_list(self):
        raw = json.dumps({"test_cases": []})
        result = validate_business_logic_output(raw)
        assert result == []

    def test_invalid_priority_caught(self):
        raw = json.dumps({
            "test_cases": [{
                "name": "test",
                "description": "desc",
                "priority": "INVALID_PRIORITY",  # not in enum
                "method": "GET",
                "path": "/",
                "path_params": {},
                "query_params": {},
                "request_body": None,
                "expected_status": 200,
                "assertions": [],
                "business_rule": "rule"
            }]
        })
        with pytest.raises(AIOutputValidationError):
            validate_business_logic_output(raw)


class TestAIClientMocked:
    @pytest.mark.asyncio
    async def test_client_retries_on_json_error(self, mocker):
        """Client should retry up to 3x before raising."""
        from aitester.ai.client import GeminiClient
        mocker.patch.dict("os.environ", {"GEMINI_API_KEY": "test_key"})
        client = GeminiClient()
        
        # Mock the underlying model to return invalid JSON twice, then valid
        valid_response = json.dumps({"test_cases": []})
        
        # We need to mock the generate_content_async method
        class MockResponse:
            def __init__(self, text):
                self.text = text
                
        mock_model = mocker.patch.object(
            client.model, 
            "generate_content_async",
            side_effect=[
                MockResponse("not json"), 
                MockResponse("still bad"), 
                MockResponse(valid_response)
            ]
        )
        
        result = await client.generate_with_retry("test prompt", validate_business_logic_output)
        
        assert mock_model.call_count == 3
        assert result == []

    @pytest.mark.asyncio
    async def test_client_raises_after_max_retries(self, mocker):
        from aitester.ai.client import GeminiClient
        from aitester.core.exceptions import AIOutputValidationError
        mocker.patch.dict("os.environ", {"GEMINI_API_KEY": "test_key"})
        client = GeminiClient()
        
        class MockResponse:
            def __init__(self, text):
                self.text = text
                
        mock_model = mocker.patch.object(
            client.model, 
            "generate_content_async",
            return_value=MockResponse("bad json")
        )
        
        with pytest.raises(AIOutputValidationError):
            await client.generate_with_retry("test prompt", validate_business_logic_output, max_retries=2)
            
        assert mock_model.call_count == 2
