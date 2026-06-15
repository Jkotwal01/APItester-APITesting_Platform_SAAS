import json

import pytest

from aitester.ai.validators import (
    validate_failure_analysis_output,
    validate_risk_assessment_output,
)
from aitester.core.exceptions import AIOutputValidationError


class TestFailureAnalysisValidation:
    def test_valid_analysis_passes(self):
        raw = json.dumps({
            "root_cause": "The API returns 400 when email format is invalid",
            "severity": "warning",
            "category": "validation",
            "explanation": "The request body contained an invalid email format.",
            "suggested_fix": "Validate email format before sending.",
            "is_security_concern": False
        })
        result = validate_failure_analysis_output(raw)
        assert result["severity"] == "warning"
        assert result["is_security_concern"] is False

    def test_invalid_severity_caught(self):
        raw = json.dumps({
            "root_cause": "Something",
            "severity": "super_critical",  # invalid
            "category": "validation",
            "explanation": "Explanation",
            "suggested_fix": "Fix it",
            "is_security_concern": False
        })
        with pytest.raises(AIOutputValidationError):
            validate_failure_analysis_output(raw)

    def test_missing_root_cause_caught(self):
        raw = json.dumps({
            "severity": "error",
            "category": "validation",
            "explanation": "Explanation",
            "suggested_fix": "Fix",
            "is_security_concern": False
        })
        with pytest.raises(AIOutputValidationError):
            validate_failure_analysis_output(raw)


class TestRiskScorerValidation:
    def test_valid_risk_assessment_passes(self):
        raw = json.dumps({
            "overall_risk_score": 72,
            "risk_level": "high",
            "executive_summary": "The API has several high-severity findings.",
            "findings": [],
            "remediation_priority": []
        })
        result = validate_risk_assessment_output(raw)
        assert result["overall_risk_score"] == 72
        assert result["risk_level"] == "high"

    def test_score_out_of_range_caught(self):
        raw = json.dumps({
            "overall_risk_score": 105,  # invalid, must be <= 100
            "risk_level": "critical",
            "executive_summary": "Bad",
            "findings": [],
            "remediation_priority": []
        })
        with pytest.raises(AIOutputValidationError):
            validate_risk_assessment_output(raw)

    def test_missing_risk_level_caught(self):
        raw = json.dumps({
            "overall_risk_score": 50,
            "executive_summary": "Medium",
            "findings": [],
            "remediation_priority": []
        })
        with pytest.raises(AIOutputValidationError):
            validate_risk_assessment_output(raw)
