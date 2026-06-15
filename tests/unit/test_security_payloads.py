import pytest

from aitester.db.models.test_case import TestCase
from aitester.parser.models import ParsedEndpoint, ParsedParameter, ParsedRequestBody
from aitester.security.detector import SecurityDetector
from aitester.security.generator import SecurityGenerator
from aitester.security.payloads.command_injection import COMMAND_INJECTION_PAYLOADS
from aitester.security.payloads.jwt_attacks import JWT_PAYLOADS
from aitester.security.payloads.path_traversal import PATH_TRAVERSAL_PAYLOADS
from aitester.security.payloads.sqli import SQLI_PAYLOADS
from aitester.security.payloads.xss import XSS_PAYLOADS


@pytest.fixture
def sample_endpoint():
    return ParsedEndpoint(
        path="/search",
        method="POST",
        parameters=[
            ParsedParameter(name="q", in_="query", required=True, schema_={"type": "string"})
        ],
        request_body=ParsedRequestBody(
            content_type="application/json",
            schema_={
                "type": "object",
                "properties": {
                    "username": {"type": "string"},
                }
            },
            required=True
        )
    )


def test_security_generator(sample_endpoint):
    generator = SecurityGenerator(endpoint=sample_endpoint, test_run_id="run-sec")
    test_cases = generator.generate()

    # Calculate expected number of tests:
    # Query param 'q' gets: SQLI, XSS, Path traversal, Command injection
    # Body field 'username' gets: SQLI, XSS, Path traversal, Command injection
    # Plus JWT payloads as headers
    
    expected_sqli = len(SQLI_PAYLOADS) * 2  # Once for query, once for body
    expected_xss = len(XSS_PAYLOADS) * 2
    expected_path = len(PATH_TRAVERSAL_PAYLOADS) * 2
    expected_cmd = len(COMMAND_INJECTION_PAYLOADS) * 2
    expected_jwt = len(JWT_PAYLOADS)
    
    total_expected = expected_sqli + expected_xss + expected_path + expected_cmd + expected_jwt
    
    assert len(test_cases) == total_expected
    
    sqli_cases = [tc for tc in test_cases if tc.category == "SECURITY_SQLI"]
    assert len(sqli_cases) == expected_sqli


def test_security_detector_sqli():
    tc = TestCase(category="SECURITY_SQLI")
    
    # Positive detection
    assert SecurityDetector.is_vulnerable(tc, 200, "you have an error in your sql syntax", {}) is True
    # 500 error assumes vulnerable crash
    assert SecurityDetector.is_vulnerable(tc, 500, "internal server error", {}) is True
    # Negative detection
    assert SecurityDetector.is_vulnerable(tc, 400, "invalid input", {}) is False


def test_security_detector_xss():
    tc = TestCase(category="SECURITY_XSS", query_params={"q": "<script>alert(1)</script>"})
    
    # Reflected XSS
    assert SecurityDetector.is_vulnerable(tc, 200, "<html>Hello <script>alert(1)</script></html>", {}) is True
    # Sanitized
    assert SecurityDetector.is_vulnerable(tc, 200, "<html>Hello &lt;script&gt;alert(1)&lt;/script&gt;</html>", {}) is False


def test_security_detector_path_traversal():
    tc = TestCase(category="SECURITY_PATH_TRAVERSAL")
    assert SecurityDetector.is_vulnerable(tc, 200, "root:x:0:0:root:/root:/bin/bash", {}) is True
    assert SecurityDetector.is_vulnerable(tc, 404, "not found", {}) is False


def test_security_detector_jwt():
    tc = TestCase(category="SECURITY_JWT")
    assert SecurityDetector.is_vulnerable(tc, 200, "welcome admin", {}) is True
    assert SecurityDetector.is_vulnerable(tc, 401, "unauthorized", {}) is False
