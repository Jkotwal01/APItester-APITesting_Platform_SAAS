import pytest
from aitester.core.exceptions import SpecParseError, SpecValidationError
from aitester.parser.openapi import OpenAPIParser

SAMPLE_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Sample API", "version": "1.0.0"},
    "paths": {
        "/users": {
            "get": {
                "summary": "Get users",
                "operationId": "getUsers",
                "parameters": [
                    {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer"}}
                ],
                "responses": {
                    "200": {
                        "description": "A list of users",
                        "content": {
                            "application/json": {"schema": {"type": "array", "items": {"type": "object"}}}
                        }
                    }
                }
            },
            "post": {
                "summary": "Create user",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {"schema": {"type": "object", "properties": {"name": {"type": "string"}}}}
                    }
                },
                "responses": {
                    "201": {"description": "Created"}
                }
            }
        },
        "/users/{id}": {
            "parameters": [
                {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
            ],
            "get": {
                "summary": "Get a user by ID",
                "responses": {
                    "200": {"description": "Successful operation"}
                }
            }
        }
    }
}


def test_parser_invalid_spec():
    with pytest.raises(SpecParseError):
        OpenAPIParser([])  # type: ignore

    with pytest.raises(SpecValidationError, match="Missing 'openapi' or 'swagger'"):
        OpenAPIParser({"info": {}})

    with pytest.raises(SpecValidationError, match="Missing 'paths' field"):
        OpenAPIParser({"openapi": "3.0.0"})


def test_parser_extracts_endpoints():
    parser = OpenAPIParser(SAMPLE_SPEC)
    endpoints = parser.parse()
    
    assert len(endpoints) == 3
    
    get_users = next(e for e in endpoints if e.path == "/users" and e.method == "GET")
    assert get_users.operation_id == "getUsers"
    assert len(get_users.parameters) == 1
    assert get_users.parameters[0].name == "limit"
    assert get_users.parameters[0].in_ == "query"
    assert get_users.has_query_parameters is True
    assert get_users.has_path_parameters is False
    assert len(get_users.responses) == 1
    assert get_users.responses[0].status_code == "200"

    post_user = next(e for e in endpoints if e.path == "/users" and e.method == "POST")
    assert post_user.request_body is not None
    assert post_user.request_body.content_type == "application/json"
    assert post_user.request_body.required is True
    assert post_user.request_body.schema_["type"] == "object"

    get_user_by_id = next(e for e in endpoints if e.path == "/users/{id}" and e.method == "GET")
    assert len(get_user_by_id.parameters) == 1
    assert get_user_by_id.parameters[0].name == "id"
    assert get_user_by_id.parameters[0].in_ == "path"
    assert get_user_by_id.has_path_parameters is True
