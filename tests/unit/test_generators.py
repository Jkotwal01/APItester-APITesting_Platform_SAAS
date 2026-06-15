import pytest

from aitester.generators.functional import FunctionalGenerator
from aitester.parser.models import ParsedEndpoint, ParsedParameter, ParsedRequestBody, ParsedResponse


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
    assert isinstance(tc.body["age"], int)
    assert "@" in tc.body["email"]  # faker email format
