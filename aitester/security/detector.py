from typing import Any

from aitester.db.models.test_case import TestCase

# Keywords that indicate a potential vulnerability leaked in an error message
SQLI_ERROR_KEYWORDS = ["syntax error", "mysql", "postgresql", "ora-", "sql syntax"]
PATH_TRAVERSAL_KEYWORDS = ["root:x:", "etc/passwd", "[extensions]", "win.ini"]


class SecurityDetector:
    """
    Analyzes API responses to detect if a security vulnerability was successfully triggered.
    """

    @classmethod
    def is_vulnerable(
        cls,
        test_case: TestCase,
        status_code: int,
        response_text: str,
        response_headers: dict[str, Any],
    ) -> bool:
        """
        Determines if the endpoint is vulnerable based on the test case payload and response.
        Returns True if vulnerable, False otherwise.
        """
        # If it's a 500 Internal Server Error, it might have crashed due to our payload
        if status_code == 500:
            return True

        # Check for specific leaked information based on the vulnerability type
        if test_case.category == "SECURITY_SQLI":
            return cls._check_sqli(response_text)
        elif test_case.category == "SECURITY_XSS":
            return cls._check_xss(test_case, response_text)
        elif test_case.category == "SECURITY_PATH_TRAVERSAL":
            return cls._check_path_traversal(response_text)
        elif test_case.category == "SECURITY_COMMAND_INJECTION":
            # Very basic check - real detection would involve out-of-band checks or delays
            return "uid=" in response_text or "PING" in response_text

        # For JWT or others, if it was accepted (200 OK) when it shouldn't be, it's vulnerable
        return bool(test_case.category == "SECURITY_JWT" and status_code in (200, 201, 202, 204))

    @classmethod
    def _check_sqli(cls, response_text: str) -> bool:
        text_lower = response_text.lower()
        return any(keyword in text_lower for keyword in SQLI_ERROR_KEYWORDS)

    @classmethod
    def _check_xss(cls, test_case: TestCase, response_text: str) -> bool:
        # If the exact payload is reflected back without sanitization
        # We'd need to know the specific payload used.
        # We can extract it from the test case body or query params.
        payloads_used = []
        if test_case.query_params:
            payloads_used.extend(str(v) for v in test_case.query_params.values())
        if test_case.body:
            # Very simple extraction for MVP
            payloads_used.extend(str(v) for v in test_case.body.values())

        return any(p in response_text and "<script>" in p for p in payloads_used)

    @classmethod
    def _check_path_traversal(cls, response_text: str) -> bool:
        text_lower = response_text.lower()
        return any(keyword in text_lower for keyword in PATH_TRAVERSAL_KEYWORDS)
