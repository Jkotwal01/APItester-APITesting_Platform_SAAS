import json
import logging
from typing import Any

from aitester.ai.client import GeminiClient
from aitester.ai.prompts import FAILURE_ANALYSIS_PROMPT
from aitester.ai.validators import validate_failure_analysis_output
from aitester.db.models.test_result import TestResult

logger = logging.getLogger("aitester.ai.failure_analyzer")

class FailureAnalyzer:
    """
    Analyzes failed test results using Gemini to determine root causes
    and suggest fixes.
    """

    def __init__(self, ai_client: GeminiClient | None = None):
        self.ai_client = ai_client or GeminiClient()

    async def analyze(self, test_result: TestResult) -> dict[str, Any] | None:
        """
        Analyzes a single failed test result.
        Returns a dictionary with the structured analysis or None if it fails.
        """
        if test_result.passed:
            logger.info("Test passed. No failure analysis needed.")
            return None

        # Build context from the test result and test case
        tc = test_result.test_case
        test_case_info = {
            "category": tc.category,
            "endpoint": tc.endpoint,
            "method": tc.method,
            "expected_status_code": tc.expected_status_code,
            "headers": tc.headers,
            "query_params": tc.query_params,
            "body": tc.body,
        }

        prompt = FAILURE_ANALYSIS_PROMPT.format(
            test_case=json.dumps(test_case_info, indent=2),
            status_code=test_result.actual_status_code or "Unknown",
            response_body=test_result.actual_body or "None",
        )

        try:
            analysis: dict[str, Any] = await self.ai_client.generate_with_retry(prompt, validate_failure_analysis_output)
            return analysis
        except Exception as e:
            logger.error(f"Failure analysis failed for test {tc.id}: {e}")
            return None
