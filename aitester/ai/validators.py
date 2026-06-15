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

def validate_business_logic_output(raw_json: str) -> list[AITestCase]:
    """
    Validates a raw JSON string from Gemini and returns a list of AITestCase models.
    Strips markdown code fences if present.
    """
    raw_json = raw_json.strip()
    if raw_json.startswith("```json"):
        raw_json = raw_json[7:]
    if raw_json.startswith("```"):
        raw_json = raw_json[3:]
    if raw_json.endswith("```"):
        raw_json = raw_json[:-3]
        
    raw_json = raw_json.strip()

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise AIOutputValidationError(f"Invalid JSON returned by AI: {e}")

    try:
        output = BusinessLogicOutput.model_validate(data)
        return output.test_cases
    except ValidationError as e:
        raise AIOutputValidationError(f"AI Output does not match required schema: {e}")
