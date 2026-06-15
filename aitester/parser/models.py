from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ParsedParameter(BaseModel):
    """Represents a parameter in an OpenAPI operation (query, path, header, cookie)."""
    model_config = ConfigDict(populate_by_name=True)

    name: str
    in_: str = Field(alias="in")
    required: bool = False
    schema_: dict[str, Any] | None = Field(None, alias="schema")


class ParsedRequestBody(BaseModel):
    """Represents the request body schema in an OpenAPI operation."""
    model_config = ConfigDict(populate_by_name=True)

    content_type: str
    schema_: dict[str, Any] = Field(alias="schema")
    required: bool = False


class ParsedResponse(BaseModel):
    """Represents a defined response in an OpenAPI operation."""
    status_code: str
    description: str | None = None
    content: dict[str, Any] | None = None


class ParsedEndpoint(BaseModel):
    """Represents a fully parsed API endpoint from an OpenAPI specification."""
    path: str
    method: str
    operation_id: str | None = None
    summary: str | None = None
    parameters: list[ParsedParameter] = Field(default_factory=list)
    request_body: ParsedRequestBody | None = None
    responses: list[ParsedResponse] = Field(default_factory=list)

    @property
    def has_path_parameters(self) -> bool:
        return any(p.in_ == "path" for p in self.parameters)

    @property
    def has_query_parameters(self) -> bool:
        return any(p.in_ == "query" for p in self.parameters)


class ParsedSpec(BaseModel):
    """Represents a fully parsed OpenAPI specification with metadata and endpoints."""
    title: str = "Unknown API"
    version: str = "1.0.0"
    endpoints: list[ParsedEndpoint] = Field(default_factory=list)
