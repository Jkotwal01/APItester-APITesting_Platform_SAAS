"""
Custom exception hierarchy for AITester.

All exceptions inherit from AITesterError so callers can catch
either the specific type or the base class as needed.

Usage:
    from aitester.core.exceptions import SpecLoadError
    raise SpecLoadError("Could not load spec from /path/to/file.yaml")
"""


class AITesterError(Exception):
    """
    Base exception for all AITester errors.
    Catch this to handle any AITester-specific failure generically.
    """

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, details={self.details!r})"


# ─── Parser Exceptions ────────────────────────────────────────────────────────


class SpecLoadError(AITesterError):
    """
    Failed to load an OpenAPI spec from a file path or URL.
    Raised by: parser/loader.py
    """


class SpecValidationError(AITesterError):
    """
    OpenAPI spec failed structural or semantic validation.
    Raised by: parser/validator.py
    """


class SpecParseError(AITesterError):
    """
    Failed to parse spec content (malformed YAML/JSON).
    Raised by: parser/loader.py
    """


# ─── Generator Exceptions ─────────────────────────────────────────────────────


class TestGenerationError(AITesterError):
    """
    Test case generation failed unexpectedly.
    Raised by: generators/
    """


# ─── Execution Exceptions ─────────────────────────────────────────────────────


class ExecutionError(AITesterError):
    """
    Test execution pipeline failed.
    Raised by: executor/runner.py
    """


class HTTPClientError(AITesterError):
    """
    HTTP client could not send a request (network, DNS, TLS issues).
    Raised by: executor/http_client.py
    """


# ─── AI Engine Exceptions ─────────────────────────────────────────────────────


class AIEngineError(AITesterError):
    """
    Gemini API call failed (network error, invalid API key, quota exceeded).
    Raised by: ai/client.py
    """


class AIOutputValidationError(AITesterError):
    """
    AI-generated output did not conform to the expected JSON schema
    after all retry attempts were exhausted.
    Raised by: ai/validators.py
    """


class AIRateLimitError(AIEngineError):
    """
    Gemini API rate limit was hit.
    Raised by: ai/client.py — triggers exponential backoff retry.
    """


# ─── Security Exceptions ──────────────────────────────────────────────────────


class SecurityScanError(AITesterError):
    """
    Security payload generation or detection failed.
    Raised by: security/
    """


# ─── Report Exceptions ────────────────────────────────────────────────────────


class ReportGenerationError(AITesterError):
    """
    HTML or JSON report generation failed.
    Raised by: reports/
    """


# ─── Database Exceptions ──────────────────────────────────────────────────────


class DatabaseError(AITesterError):
    """
    A database operation failed (connection, query, constraint violation).
    Raised by: db/
    """


class RecordNotFoundError(DatabaseError):
    """
    A requested record does not exist in the database.
    Raised by: db/crud.py — maps to HTTP 404 in API layer.
    """


# ─── Configuration Exceptions ─────────────────────────────────────────────────


class ConfigurationError(AITesterError):
    """
    Invalid or missing application configuration.
    Raised by: core/config.py
    """
