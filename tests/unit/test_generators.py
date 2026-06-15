import pytest

from aitester.generators.functional import FunctionalGenerator
from aitester.parser.models import (
    ParsedEndpoint,
    ParsedParameter,
    ParsedRequestBody,
    ParsedResponse,
)


@pytest.fixture
def sample_endpoint() -> ParsedEndpoint:
    return ParsedEndpoint(
        path="/users/{id}",
        method="PUT",
        parameters=[
            ParsedParameter(name="id", in_="path", required=True, schema_={"type": "integer"}),
            ParsedParameter(name="role", in_="query", required=False, schema_={"type": "string"})
        ],
        request_body=ParsedRequestBody(
            content_type="application/json",
            schema_={
                "type": "object",
                "properties": {
                    "email": {"type": "string", "format": "email"},
                    "age": {"type": "integer"}
                }
            },
            required=True
        ),
        responses=[
            ParsedResponse(status_code="200", content={"application/json": {"schema": {"type": "object"}}}),
            ParsedResponse(status_code="400", description="Bad Request")
        ]
    )


def test_functional_generator(sample_endpoint):
    generator = FunctionalGenerator(endpoint=sample_endpoint, test_run_id="run-123")
    test_cases = generator.generate()

    assert len(test_cases) == 1
    tc = test_cases[0]

    assert tc.test_run_id == "run-123"
    assert tc.category == "FUNCTIONAL"
    assert tc.method == "PUT"
    assert tc.expected_status_code == 200
    assert tc.expected_schema == {"type": "object"}

    # Path parameter substitution
    assert "/users/" in tc.endpoint
    assert "{id}" not in tc.endpoint

    # Query parameters
    assert tc.query_params is not None
    assert "role" in tc.query_params

    # Body generation
    assert tc.body is not None
    assert "email" in tc.body
    assert "age" in tc.body
    assert "@" in tc.body["email"]  # faker email format


def test_edge_case_generator(sample_endpoint):
    from aitester.generators.edge import EdgeCaseGenerator

    # We make 'email' required in the sample_endpoint for testing
    sample_endpoint.request_body.schema_["required"] = ["email"]

    generator = EdgeCaseGenerator(endpoint=sample_endpoint, test_run_id="run-edge")
    test_cases = generator.generate()

    # Query 'role' omission is skipped since it's not required.
    # Query 'role' type mutation (string -> int) = 1 test
    # Body 'email' omission (required) = 1 test
    # Body 'email' type mutation (string -> int) = 1 test
    # Body 'age' type mutation (integer -> string) = 1 test
    # Empty body (since body is required) = 1 test

    assert len(test_cases) == 5
    for tc in test_cases:
        assert tc.category == "EDGE"
        assert tc.expected_status_code == 400
        assert tc.test_run_id == "run-edge"

    # Find the missing email test
    missing_email_tests = [tc for tc in test_cases if tc.body is not None and "email" not in tc.body and tc.body != {}]
    assert len(missing_email_tests) == 1

    # Find the wrong type for email
    wrong_type_email = [tc for tc in test_cases if tc.body is not None and tc.body.get("email") == 12345]
    assert len(wrong_type_email) == 1

    # Find empty body test
    empty_body_tests = [tc for tc in test_cases if tc.body == {}]
    assert len(empty_body_tests) == 1
