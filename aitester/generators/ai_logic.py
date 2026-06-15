import json
from typing import Any

from aitester.ai.client import GeminiClient
from aitester.db.models.test_case import TestCase
from aitester.generators.base import BaseGenerator


class AILogicGenerator(BaseGenerator):
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
            # We expect a JSON array of objects with 'category', 'description', 'query_params', 'body', 'expected_status'
            payload = await self.ai_client.generate_test_payload(prompt)

            if not isinstance(payload, list):
                if isinstance(payload, dict) and "test_cases" in payload:
                    payload = payload["test_cases"]
                else:
                    payload = [payload]

            for item in payload:
                if not isinstance(item, dict):
                    continue

                tc = self._create_test_case(
                    category=f"AI_LOGIC - {item.get('category', 'Custom')}",
                    expected_status=item.get("expected_status", 200),
                    headers=item.get("headers"),
                    query_params=item.get("query_params"),
                    body=item.get("body"),
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
        endpoint_info = {
            "path": self.endpoint.path,
            "method": self.endpoint.method,
            "summary": self.endpoint.summary,
            "parameters": [
                {"name": p.name, "in": p.in_, "required": p.required}
                for p in self.endpoint.parameters
            ],
        }
        if self.endpoint.request_body and self.endpoint.request_body.schema_:
            endpoint_info["body_schema"] = self.endpoint.request_body.schema_

        prompt = f"""
You are an expert API QA Engineer. Analyze the following API endpoint specification:
{json.dumps(endpoint_info, indent=2)}

Generate 3 clever, business-logic-specific test cases that go beyond simple data validation.
Think about state manipulation, idempotency, realistic user flows, or common business logic flaws.

Return ONLY a JSON array of objects with the following schema:
[
  {{
    "category": "String (e.g., Idempotency, Concurrency, State, Flow)",
    "description": "String (What this test aims to prove)",
    "expected_status": Integer (HTTP status code),
    "headers": {{}} (Optional),
    "query_params": {{}} (Optional),
    "body": {{}} (Optional)
  }}
]
"""
        return prompt.strip()
