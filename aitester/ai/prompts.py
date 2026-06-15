BUSINESS_LOGIC_PROMPT = """
You are an expert API QA Engineer. Analyze the following API endpoint specification:
{endpoint_info}

Generate 3 clever, business-logic-specific test cases that go beyond simple data validation.
Think about state manipulation, idempotency, realistic user flows, or common business logic flaws.

Return ONLY a JSON object exactly matching the following format:
```json
{{
  "test_cases": [
    {{
      "name": "Test discount cannot exceed 100%",
      "description": "Business rule: discounts must be 0-100%",
      "priority": "high",
      "method": "POST",
      "path": "/discounts",
      "path_params": {{}},
      "query_params": {{}},
      "request_body": {{"amount": 150}},
      "expected_status": 400,
      "assertions": [],
      "business_rule": "Discount cannot exceed 100%"
    }}
  ]
}}
```
"""

FAILURE_ANALYSIS_PROMPT = """
You are an expert QA and Security engineer. The following test case just failed against the target API.
Analyze the request and the actual response to determine why it failed.

Test Case:
{test_case}

Actual Response Status: {status_code}
Actual Response Body: {response_body}

Determine if this is a bug in the API, a flaky test, an environment issue, or a security vulnerability.
Return ONLY a JSON object exactly matching the following format:
```json
{{
  "failure_category": "bug" | "security" | "flaky" | "environment",
  "root_cause_analysis": "Detailed explanation of why it failed",
  "suggested_fix": "How the developer should fix the API",
  "confidence_score": 0.95
}}
```
"""

RISK_ASSESSMENT_PROMPT = """
You are an expert Security Engineer and CISO. Analyze the following list of security and test findings.

Findings:
{findings}

Determine the overall security posture and risk to the application.
Return ONLY a JSON object exactly matching the following format:
```json
{{
  "overall_risk_score": 75,
  "risk_level": "low" | "medium" | "high" | "critical",
  "executive_summary": "A 2-3 sentence summary of the security posture",
  "findings": ["List of key findings summarized"],
  "remediation_priority": ["List of what to fix first"]
}}
```
"""
