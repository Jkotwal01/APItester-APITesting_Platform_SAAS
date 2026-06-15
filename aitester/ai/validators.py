import json
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from aitester.core.exceptions import AIOutputValidationError


class AITestCase(BaseModel):
    name: str = Field(..., description="Short name of the test case")
    description: str = Field(..., description="What this test aims to prove")
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    method: str
    path: str
    path_params: dict[str, Any] = Field(default_factory=dict)
    query_params: dict[str, Any] = Field(default_factory=dict)
    request_body: dict[str, Any] | None = None
    expected_status: int
    assertions: list[dict[str, Any]] = Field(default_factory=list)
    business_rule: str | None = None

class BusinessLogicOutput(BaseModel):
    test_cases: list[AITestCase]

class FailureAnalysisOutput(BaseModel):
    root_cause: str = Field(..., description="The root cause of the failure")
    severity: Literal["info", "warning", "error", "critical"]
    category: str = Field(..., description="Category of failure e.g., validation, security, logical")
    explanation: str = Field(..., description="Detailed explanation")
    suggested_fix: str = Field(..., description="Suggested remediation")
    is_security_concern: bool = False

class RiskAssessmentOutput(BaseModel):
    overall_risk_score: int = Field(..., ge=0, le=100)
    risk_level: Literal["low", "medium", "high", "critical"]
    executive_summary: str
    findings: list[str] = Field(default_factory=list)
    remediation_priority: list[str] = Field(default_factory=list)

def _extract_json_string(raw_json: str) -> str:
    raw_json = raw_json.strip()
    if raw_json.startswith("```json"):
        raw_json = raw_json[7:]
    if raw_json.startswith("```"):
        raw_json = raw_json[3:]
    if raw_json.endswith("```"):
        raw_json = raw_json[:-3]
    return raw_json.strip()

def validate_business_logic_output(raw_json: str) -> list[AITestCase]:
    """
    Validates a raw JSON string from Gemini and returns a list of AITestCase models.
    Strips markdown code fences if present.
    """
    raw_json = _extract_json_string(raw_json)

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise AIOutputValidationError(f"Invalid JSON returned by AI: {e}") from e

    try:
        output = BusinessLogicOutput.model_validate(data)
        return output.test_cases
    except ValidationError as e:
        raise AIOutputValidationError(f"AI Output does not match required schema: {e}") from e

def validate_failure_analysis_output(raw_json: str) -> dict[str, Any]:
    raw_json = _extract_json_string(raw_json)
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise AIOutputValidationError(f"Invalid JSON returned by AI: {e}") from e
    try:
        output = FailureAnalysisOutput.model_validate(data)
        return output.model_dump()
    except ValidationError as e:
        raise AIOutputValidationError(f"Failure Analysis Output does not match required schema: {e}") from e

def validate_risk_assessment_output(raw_json: str) -> dict[str, Any]:
    raw_json = _extract_json_string(raw_json)
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise AIOutputValidationError(f"Invalid JSON returned by AI: {e}") from e
    try:
        output = RiskAssessmentOutput.model_validate(data)
        return output.model_dump()
    except ValidationError as e:
        raise AIOutputValidationError(f"Risk Assessment Output does not match required schema: {e}") from e
