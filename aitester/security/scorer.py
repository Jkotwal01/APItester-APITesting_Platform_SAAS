from typing import Literal

from pydantic import BaseModel


class SecurityFinding(BaseModel):
    vulnerability_type: str
    severity: Literal["low", "medium", "high", "critical"]
    cvss_score: float
    affected_endpoint: str
    evidence: str
    remediation: str
    cwe: str

def calculate_security_score(findings: list[SecurityFinding]) -> float:
    """
    Calculates a security score from 0.0 to 100.0 based on findings.
    Base score is 100.0. Each finding deducts points based on severity.
    """
    score = 100.0

    # Deduction weights based on severity
    weights = {
        "critical": 20.0,
        "high": 10.0,
        "medium": 5.0,
        "low": 1.0,
    }

    for finding in findings:
        deduction = weights.get(finding.severity, 1.0)
        score -= deduction

    return max(0.0, min(100.0, score))

def score_to_risk_level(score: float) -> str:
    """
    Converts a numerical score (0-100) to a risk level.
    """
    if score >= 90.0:
        return "low"
    elif score >= 70.0:
        return "medium"
    elif score >= 40.0:
        return "high"
    else:
        return "critical"
