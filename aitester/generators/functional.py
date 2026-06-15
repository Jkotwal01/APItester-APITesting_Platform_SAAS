import uuid
from typing import Any

from faker import Faker

from aitester.db.models.test_case import TestCase
from aitester.generators.base import BaseGenerator
from aitester.parser.models import ParsedEndpoint

fake = Faker()


class FunctionalGenerator(BaseGenerator):
    """
    Generates standard 'happy path' functional tests based on the OpenAPI spec.
    """

    def generate(self) -> list[TestCase]:
        test_cases = []

        # Find the primary success response (e.g., 200 or 201)
        success_response = self._get_success_response()
        expected_status = int(success_response.status_code) if success_response else 200
        
        # If there's a response schema defined, we'll expect it
        expected_schema = None
        if success_response and success_response.content:
            json_content = success_response.content.get("application/json")
            if json_content:
                expected_schema = json_content.get("schema")

        # Generate fake query parameters
        query_params = self._generate_parameters_by_in("query")
        
        # Note: path parameters are technically part of the endpoint URL path in the DB model.
        # We replace {param} with fake data directly in the URL path for simplicity in this MVP,
        # or we could store them in query_params. For now, let's keep the raw endpoint string 
        # and replace them at execution time, or replace them now. Let's replace them now to 
        # make execution simpler.
        endpoint_path = self.endpoint.path
        path_params = self._generate_parameters_by_in("path")
        for k, v in path_params.items():
            endpoint_path = endpoint_path.replace(f"{{{k}}}", str(v))

        # Generate fake headers (if explicitly required by the API)
        headers = self._generate_parameters_by_in("header")
        
        # Generate fake request body
        body = None
        if self.endpoint.request_body and self.endpoint.request_body.schema_:
            body = self._generate_payload(self.endpoint.request_body.schema_)

        tc = self._create_test_case(
            category="FUNCTIONAL",
            expected_status=expected_status,
            headers=headers if headers else None,
            query_params=query_params if query_params else None,
            body=body,
            expected_schema=expected_schema,
        )
        # Override the endpoint with the path-injected one
        tc.endpoint = endpoint_path
        
        test_cases.append(tc)
        return test_cases

    def _get_success_response(self):
        """Returns the first 2xx response defined."""
        for resp in self.endpoint.responses:
            if resp.status_code.startswith("2"):
                return resp
        return None

    def _generate_parameters_by_in(self, in_loc: str) -> dict[str, Any]:
        """Generates dummy data for parameters in a specific location."""
        result = {}
        params = [p for p in self.endpoint.parameters if p.in_ == in_loc]
        for p in params:
            schema = p.schema_ or {"type": "string"}
            result[p.name] = self._generate_dummy_value(schema)
        return result

    def _generate_payload(self, schema: dict[str, Any]) -> Any:
        """Recursively generates a payload matching the JSON schema."""
        schema_type = schema.get("type", "object")

        if schema_type == "object":
            properties = schema.get("properties", {})
            return {k: self._generate_payload(v) for k, v in properties.items()}
        elif schema_type == "array":
            items = schema.get("items", {"type": "string"})
            return [self._generate_payload(items) for _ in range(2)]  # Generate 2 items
        else:
            return self._generate_dummy_value(schema)

    def _generate_dummy_value(self, schema: dict[str, Any]) -> Any:
        """Generates a scalar fake value based on OpenAPI type/format."""
        schema_type = schema.get("type", "string")
        schema_format = schema.get("format")

        if schema_type == "string":
            if schema_format == "uuid":
                return str(uuid.uuid4())
            elif schema_format == "email":
                return fake.email()
            elif schema_format == "date-time":
                return fake.iso8601()
            return fake.word()
        elif schema_type == "integer":
            return fake.random_int(min=1, max=1000)
        elif schema_type == "number":
            return fake.pyfloat(positive=True, min_value=1.0, max_value=100.0)
        elif schema_type == "boolean":
            return fake.boolean()
        return "dummy_value"
