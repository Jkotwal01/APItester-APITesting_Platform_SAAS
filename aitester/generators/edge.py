import copy
from typing import Any

from aitester.db.models.test_case import TestCase
from aitester.generators.base import BaseGenerator
from aitester.generators.functional import FunctionalGenerator


class EdgeCaseGenerator(BaseGenerator):
    """
    Generates negative/edge-case tests based on the OpenAPI spec.
    """

    def generate(self) -> list[TestCase]:
        test_cases = []

        # We need a baseline happy-path request to mutate
        # We can leverage FunctionalGenerator to get a baseline
        functional_gen = FunctionalGenerator(endpoint=self.endpoint, test_run_id=self.test_run_id)
        baseline_tests = functional_gen.generate()
        if not baseline_tests:
            return []

        baseline = baseline_tests[0]

        # 1. Mutate query parameters
        for param in self.endpoint.parameters:
            if param.in_ == "query":
                # Test omission if required
                if param.required and baseline.query_params:
                    mutated_query = copy.deepcopy(baseline.query_params)
                    mutated_query.pop(param.name, None)
                    tc = self._create_edge_case(baseline, query_params=mutated_query)
                    test_cases.append(tc)

                # Test wrong type / boundary
                if baseline.query_params:
                    mutated_query = copy.deepcopy(baseline.query_params)
                    schema_type = (param.schema_ or {}).get("type", "string")
                    mutated_query[param.name] = self._get_invalid_value(schema_type)
                    tc = self._create_edge_case(baseline, query_params=mutated_query)
                    test_cases.append(tc)

        # 2. Mutate request body
        if self.endpoint.request_body and self.endpoint.request_body.schema_ and baseline.body:
            schema = self.endpoint.request_body.schema_
            properties = schema.get("properties", {})
            required_fields = schema.get("required", [])

            for field_name, field_schema in properties.items():
                # Omit required field
                if field_name in required_fields:
                    mutated_body = copy.deepcopy(baseline.body)
                    mutated_body.pop(field_name, None)
                    tc = self._create_edge_case(baseline, body=mutated_body)
                    test_cases.append(tc)

                # Send wrong type
                mutated_body = copy.deepcopy(baseline.body)
                field_type = field_schema.get("type", "string")
                mutated_body[field_name] = self._get_invalid_value(field_type)
                tc = self._create_edge_case(baseline, body=mutated_body)
                test_cases.append(tc)

            # Test empty body if body is required
            if self.endpoint.request_body.required:
                tc = self._create_edge_case(baseline, body={})
                test_cases.append(tc)

        return test_cases

    def _create_edge_case(
        self,
        baseline: TestCase,
        query_params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> TestCase:
        """Clones the baseline test case and applies mutations."""
        # Edge cases expect a 4xx response
        return self._create_test_case(
            category="EDGE",
            expected_status=400,
            headers=baseline.headers,
            query_params=query_params if query_params is not None else baseline.query_params,
            body=body if body is not None else baseline.body,
            expected_schema=None,  # We don't strictly validate error schemas in this MVP
        )

    def _get_invalid_value(self, expected_type: str) -> Any:
        """Returns a value that violates the expected type or boundaries."""
        invalid_map = {
            "string": 12345,
            "integer": "not_an_int",
            "boolean": "maybe",
            "array": "not_an_array",
        }
        return invalid_map.get(expected_type)
        return None
