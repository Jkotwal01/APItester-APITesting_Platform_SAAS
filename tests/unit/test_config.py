"""
Unit tests for Stage 02: Core Configuration & Logging.

Gate check: all tests must pass before moving to Stage 03.
Run with: pytest tests/unit/test_config.py -v
"""

import json
import logging

import pytest

# ─────────────────────────────────────────────────────────────────────────────
# Settings Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestSettings:
    def test_settings_loads_with_defaults(self):
        """Settings must load without raising even if .env has minimal values."""
        from aitester.core.config import Settings

        s = Settings()
        assert s.APP_NAME == "AITester"
        assert s.APP_VERSION == "1.0.0"

    def test_settings_singleton_returns_same_instance(self):
        """get_settings() must return the same cached object on repeated calls."""
        from aitester.core.config import get_settings

        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_settings_module_singleton(self):
        """The module-level `settings` object must be a Settings instance."""
        from aitester.core.config import Settings, settings

        assert isinstance(settings, Settings)

    def test_max_concurrent_tests_positive(self):
        """MAX_CONCURRENT_TESTS must be greater than zero."""
        from aitester.core.config import settings

        assert settings.MAX_CONCURRENT_TESTS > 0

    def test_request_timeout_positive(self):
        """REQUEST_TIMEOUT_SECONDS must be a positive float."""
        from aitester.core.config import settings

        assert settings.REQUEST_TIMEOUT_SECONDS > 0.0

    def test_log_level_is_valid(self):
        """LOG_LEVEL must be one of the standard Python log levels."""
        from aitester.core.config import settings

        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        assert settings.LOG_LEVEL.upper() in valid_levels

    def test_database_url_contains_postgresql(self):
        """DATABASE_URL must be a PostgreSQL connection string."""
        from aitester.core.config import settings

        assert "postgresql" in settings.DATABASE_URL

    def test_database_url_sync_strips_asyncpg(self):
        """database_url_sync property must replace asyncpg driver with psycopg2."""
        from aitester.core.config import settings

        sync_url = settings.database_url_sync
        assert "+asyncpg" not in sync_url
        assert "postgresql://" in sync_url

    def test_is_development_property(self):
        """is_development must return True when ENVIRONMENT=development."""
        from aitester.core.config import settings

        # .env sets ENVIRONMENT=development
        assert settings.is_development is True

    def test_is_production_property(self):
        """is_production must return False in development environment."""
        from aitester.core.config import settings

        assert settings.is_production is False

    def test_invalid_log_level_raises(self):
        """A bad LOG_LEVEL value must raise a validation error."""
        from pydantic import ValidationError

        from aitester.core.config import Settings

        with pytest.raises(ValidationError):
            Settings(LOG_LEVEL="VERBOSE")  # type: ignore[call-arg]

    def test_zero_concurrency_raises(self):
        """MAX_CONCURRENT_TESTS=0 must raise a validation error."""
        from pydantic import ValidationError

        from aitester.core.config import Settings

        with pytest.raises(ValidationError):
            Settings(MAX_CONCURRENT_TESTS=0)  # type: ignore[call-arg]

    def test_negative_timeout_raises(self):
        """A non-positive REQUEST_TIMEOUT_SECONDS must raise a validation error."""
        from pydantic import ValidationError

        from aitester.core.config import Settings

        with pytest.raises(ValidationError):
            Settings(REQUEST_TIMEOUT_SECONDS=-5.0)  # type: ignore[call-arg]


# ─────────────────────────────────────────────────────────────────────────────
# JSON Logger Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestJSONFormatter:
    def _make_record(
        self,
        message: str = "test message",
        level: int = logging.INFO,
        name: str = "test.logger",
    ) -> logging.LogRecord:
        return logging.LogRecord(
            name=name,
            level=level,
            pathname="",
            lineno=42,
            msg=message,
            args=(),
            exc_info=None,
        )

    def test_output_is_valid_json(self):
        """JSONFormatter must produce valid JSON for every log record."""
        from aitester.core.logging import JSONFormatter

        formatter = JSONFormatter()
        record = self._make_record("hello world")
        output = formatter.format(record)
        parsed = json.loads(output)  # raises if invalid JSON
        assert isinstance(parsed, dict)

    def test_required_fields_present(self):
        """JSON output must contain all required structured log fields."""
        from aitester.core.logging import JSONFormatter

        formatter = JSONFormatter()
        record = self._make_record("check fields")
        parsed = json.loads(formatter.format(record))
        assert "timestamp" in parsed
        assert "level" in parsed
        assert "logger" in parsed
        assert "message" in parsed
        assert "module" in parsed

    def test_message_preserved(self):
        """The log message must appear unchanged in the JSON output."""
        from aitester.core.logging import JSONFormatter

        formatter = JSONFormatter()
        record = self._make_record("important event occurred")
        parsed = json.loads(formatter.format(record))
        assert parsed["message"] == "important event occurred"

    def test_level_name_correct(self):
        """Level name must match the log record's level."""
        from aitester.core.logging import JSONFormatter

        formatter = JSONFormatter()
        record = self._make_record("warn msg", level=logging.WARNING)
        parsed = json.loads(formatter.format(record))
        assert parsed["level"] == "WARNING"

    def test_extra_fields_included(self):
        """Extra fields passed via `extra={}` must appear in the JSON output."""
        from aitester.core.logging import JSONFormatter

        formatter = JSONFormatter()
        record = self._make_record("run started")
        record.run_id = "abc-123"
        record.endpoint = "/api/v1/runs"
        parsed = json.loads(formatter.format(record))
        assert parsed["run_id"] == "abc-123"
        assert parsed["endpoint"] == "/api/v1/runs"

    def test_timestamp_is_iso_format(self):
        """Timestamp must be a valid ISO 8601 string ending with timezone info."""
        from aitester.core.logging import JSONFormatter

        formatter = JSONFormatter()
        record = self._make_record()
        parsed = json.loads(formatter.format(record))
        ts = parsed["timestamp"]
        assert "T" in ts  # ISO 8601 separator
        assert "+" in ts or ts.endswith("Z")  # timezone offset

    def test_exception_info_included(self):
        """Exception info must be serialized into the JSON when present."""
        from aitester.core.logging import JSONFormatter

        formatter = JSONFormatter()
        try:
            raise ValueError("test error for logging")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=1,
            msg="something failed",
            args=(),
            exc_info=exc_info,
        )
        parsed = json.loads(formatter.format(record))
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]


# ─────────────────────────────────────────────────────────────────────────────
# setup_logging & get_logger Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestLoggingSetup:
    def test_get_logger_returns_logger_instance(self):
        """get_logger must return a standard logging.Logger."""
        from aitester.core.logging import get_logger

        logger = get_logger("aitester.test_module")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_name_matches(self):
        """Logger name must match the name passed to get_logger."""
        from aitester.core.logging import get_logger

        logger = get_logger("aitester.parser")
        assert logger.name == "aitester.parser"

    def test_setup_logging_sets_level(self):
        """setup_logging must configure the aitester logger to the given level."""
        import io

        from aitester.core.logging import setup_logging

        buf = io.StringIO()
        setup_logging(level="DEBUG", use_json=True, stream=buf)
        logger = logging.getLogger("aitester")
        assert logger.level == logging.DEBUG

    def test_setup_logging_json_output(self):
        """After setup_logging, log messages must produce valid JSON lines."""
        import io

        from aitester.core.logging import get_logger, setup_logging

        buf = io.StringIO()
        setup_logging(level="INFO", use_json=True, stream=buf)
        logger = get_logger("aitester.stage02_test")
        logger.info("gate check log line")

        output = buf.getvalue().strip()
        assert output != ""
        parsed = json.loads(output)
        assert parsed["message"] == "gate check log line"
        assert parsed["level"] == "INFO"


# ─────────────────────────────────────────────────────────────────────────────
# Exception Hierarchy Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestExceptions:
    def test_all_exceptions_inherit_from_base(self):
        """Every custom exception must be a subclass of AITesterError."""
        from aitester.core.exceptions import (
            AIEngineError,
            AIOutputValidationError,
            AIRateLimitError,
            AITesterError,
            ConfigurationError,
            DatabaseError,
            ExecutionError,
            HTTPClientError,
            RecordNotFoundError,
            ReportGenerationError,
            SecurityScanError,
            SpecLoadError,
            SpecParseError,
            SpecValidationError,
            TestGenerationError,
        )

        subclasses = [
            SpecLoadError,
            SpecValidationError,
            SpecParseError,
            TestGenerationError,
            ExecutionError,
            HTTPClientError,
            AIEngineError,
            AIOutputValidationError,
            AIRateLimitError,
            SecurityScanError,
            ReportGenerationError,
            DatabaseError,
            RecordNotFoundError,
            ConfigurationError,
        ]
        for exc_class in subclasses:
            assert issubclass(exc_class, AITesterError), (
                f"{exc_class.__name__} does not inherit from AITesterError"
            )

    def test_base_exception_catchable(self):
        """Raising a specific exception must be catchable via the base class."""
        from aitester.core.exceptions import AITesterError, SpecLoadError

        with pytest.raises(AITesterError):
            raise SpecLoadError("spec not found")

    def test_exception_message_stored(self):
        """Exception message must be accessible via .message attribute."""
        from aitester.core.exceptions import SpecLoadError

        exc = SpecLoadError("file not found: /path/to/spec.yaml")
        assert exc.message == "file not found: /path/to/spec.yaml"
        assert str(exc) == "file not found: /path/to/spec.yaml"

    def test_exception_details_stored(self):
        """Optional details dict must be accessible on the exception."""
        from aitester.core.exceptions import ExecutionError

        exc = ExecutionError("timeout", details={"url": "/api/users", "ms": 30000})
        assert exc.details["url"] == "/api/users"
        assert exc.details["ms"] == 30000

    def test_exception_default_details_empty_dict(self):
        """Details must default to an empty dict when not provided."""
        from aitester.core.exceptions import AIEngineError

        exc = AIEngineError("API error")
        assert exc.details == {}

    def test_record_not_found_is_database_error(self):
        """RecordNotFoundError must be a subclass of DatabaseError."""
        from aitester.core.exceptions import DatabaseError, RecordNotFoundError

        assert issubclass(RecordNotFoundError, DatabaseError)

    def test_rate_limit_is_ai_engine_error(self):
        """AIRateLimitError must be a subclass of AIEngineError."""
        from aitester.core.exceptions import AIEngineError, AIRateLimitError

        assert issubclass(AIRateLimitError, AIEngineError)

    def test_repr_contains_class_name(self):
        """repr() must include the exception class name and message."""
        from aitester.core.exceptions import SpecValidationError

        exc = SpecValidationError("invalid spec")
        r = repr(exc)
        assert "SpecValidationError" in r
        assert "invalid spec" in r
