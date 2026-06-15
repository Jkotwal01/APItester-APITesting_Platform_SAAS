import json
import logging
from typing import Any

from aitester.ai.client import GeminiClient
from aitester.ai.prompts import RISK_ASSESSMENT_PROMPT
from aitester.ai.validators import validate_risk_assessment_output

logger = logging.getLogger("aitester.ai.risk_scorer")

class RiskScorer:
    """
    Assesses overall security risk from a list of findings using Gemini.
    """

    def __init__(self, ai_client: GeminiClient | None = None):
        self.ai_client = ai_client or GeminiClient()

    async def assess(self, findings: list[str]) -> dict[str, Any] | None:
        """
        Takes a list of findings (e.g., from failed security tests) and
        returns a structured risk assessment.
        """
        if not findings:
            logger.info("No findings provided. Skipping risk assessment.")
            return None

        prompt = RISK_ASSESSMENT_PROMPT.format(
            findings=json.dumps(findings, indent=2)
        )

        try:
            assessment = await self.ai_client.generate_with_retry(prompt, validate_risk_assessment_output)
            return assessment
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            return None
