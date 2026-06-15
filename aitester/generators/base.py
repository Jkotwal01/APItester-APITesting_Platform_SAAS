import uuid
from abc import ABC, abstractmethod
from typing import Any

from aitester.db.models.test_case import TestCase
from aitester.parser.models import ParsedEndpoint


class BaseGenerator(ABC):
    """
    Base class for all test case generators.
    """

    def __init__(self, endpoint: ParsedEndpoint, test_run_id: str):
        self.endpoint = endpoint
        self.test_run_id = test_run_id

    @abstractmethod
    def generate(self) -> list[TestCase]:
        """
        Generate a list of TestCase objects for the given endpoint.
        """
        pass

    def _create_test_case(
        self,
        category: str,
        expected_status: int,
        headers: dict[str, Any] | None = None,
        query_params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        expected_schema: dict[str, Any] | None = None,
    ) -> TestCase:
        """Helper to instantiate a TestCase model."""
        return TestCase(
            id=uuid.uuid4(),
            test_run_id=self.test_run_id,
            category=category,
            endpoint=self.endpoint.path,
            method=self.endpoint.method,
            headers=headers,
            query_params=query_params,
            body=body,
            expected_status_code=expected_status,
            expected_schema=expected_schema,
        )
