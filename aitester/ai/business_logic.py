import json
from typing import Any

from aitester.ai.client import GeminiClient
from aitester.ai.prompts import BUSINESS_LOGIC_PROMPT
from aitester.ai.validators import validate_business_logic_output
from aitester.db.models.test_case import TestCase
from aitester.generators.base import BaseGenerator


class BusinessLogicGenerator(BaseGenerator):
    """
    Generates business-logic specific test cases using the Gemini AI model.
    """

    def __init__(self, endpoint: Any, test_run_id: str, ai_client: GeminiClient | None = None):
        super().__init__(endpoint, test_run_id)
        self.ai_client = ai_client or GeminiClient()

    def generate(self) -> list[TestCase]:
        """
        Synchronous fallback - should ideally use generate_async.
        Raises NotImplementedError to force usage of async context.
        """
        raise NotImplementedError("Use generate_async() for AI Logic generation.")

    async def generate_async(self) -> list[TestCase]:
        """
        Generates test cases asynchronously using the Gemini API.
        """
        test_cases = []
        prompt = self._build_prompt()

        try:
            # We expect a JSON object matching BusinessLogicOutput schema
            payload = await self.ai_client.generate_with_retry(prompt, validate_business_logic_output)

            for item in payload:
                tc = self._create_test_case(
                    category=f"AI_LOGIC - {item.name[:35]}",
                    expected_status=item.expected_status,
                    headers={},
                    query_params=item.query_params,
                    body=item.request_body,
                )
                test_cases.append(tc)

        except Exception as e:
            # If AI generation fails, we return an empty list or log the error
            # In a real system, we might want to surface this warning.
            import logging

            logging.getLogger("aitester.generators").error(f"AI generation failed: {e}")

        return test_cases

    def _build_prompt(self) -> str:
        """Constructs the prompt for the Gemini model."""
        endpoint_info: dict[str, Any] = {
            "path": self.endpoint.path,
            "method": self.endpoint.method,
            "summary": self.endpoint.summary,
            "parameters": [
                {"name": p.name, "in": p.in_, "required": p.required}
                for p in self.endpoint.parameters
            ],
        }
        if self.endpoint.request_body and getattr(self.endpoint.request_body, "schema_", None):
            endpoint_info["body_schema"] = self.endpoint.request_body.schema_

        return BUSINESS_LOGIC_PROMPT.format(endpoint_info=json.dumps(endpoint_info, indent=2))
