import logging
from typing import Any

from aitester.core.exceptions import SpecParseError, SpecValidationError
from aitester.parser.models import (
    ParsedEndpoint,
    ParsedParameter,
    ParsedRequestBody,
    ParsedResponse,
)

logger = logging.getLogger("aitester.parser")


class OpenAPIParser:
    """
    Parses and extracts endpoint definitions from an OpenAPI specification.
    """

    SUPPORTED_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}

    def __init__(self, spec: dict[str, Any]):
        self.spec = spec
        self._validate_basic_structure()

    def _validate_basic_structure(self) -> None:
        """Validates that the spec is a valid OpenAPI v3 dict."""
        if not isinstance(self.spec, dict):
            raise SpecParseError("OpenAPI spec must be a JSON object (dictionary).")
        if "openapi" not in self.spec and "swagger" not in self.spec:
            raise SpecValidationError("Missing 'openapi' or 'swagger' version field.")
        if "paths" not in self.spec:
            raise SpecValidationError("Missing 'paths' field in OpenAPI spec.")

    def parse(self) -> list[ParsedEndpoint]:
        """
        Parses the entire specification and returns a list of ParsedEndpoint objects.
        """
        endpoints = []
        paths = self.spec.get("paths", {})
        
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
                
            # Parse path-level parameters
            path_parameters = self._parse_parameters(path_item.get("parameters", []))

            for method, operation in path_item.items():
                method_lower = method.lower()
                if method_lower not in self.SUPPORTED_METHODS:
                    continue
                    
                if not isinstance(operation, dict):
                    continue

                operation_parameters = self._parse_parameters(operation.get("parameters", []))
                
                # Combine path-level and operation-level parameters
                # Operation-level parameters override path-level parameters with the same name and in
                merged_params = self._merge_parameters(path_parameters, operation_parameters)

                request_body = self._parse_request_body(operation.get("requestBody"))
                responses = self._parse_responses(operation.get("responses", {}))

                endpoint = ParsedEndpoint(
                    path=path,
                    method=method_lower.upper(),
                    operation_id=operation.get("operationId"),
                    summary=operation.get("summary"),
                    parameters=merged_params,
                    request_body=request_body,
                    responses=responses,
                )
                endpoints.append(endpoint)

        return endpoints

    def _parse_parameters(self, parameters_list: list[dict[str, Any]]) -> list[ParsedParameter]:
        parsed = []
        for param in parameters_list:
            # We currently skip $ref resolution for simplicity in this MVP
            if "$ref" in param:
                logger.warning("Skipping parameter $ref (not supported in MVP)")
                continue

            parsed.append(
                ParsedParameter(
                    name=param.get("name", ""),
                    in_=param.get("in", "query"),
                    required=param.get("required", False),
                    schema=param.get("schema"),
                )
            )
        return parsed

    def _merge_parameters(
        self, path_params: list[ParsedParameter], op_params: list[ParsedParameter]
    ) -> list[ParsedParameter]:
        """Merges parameters, preferring operation-level ones over path-level."""
        # Key by (name, in_)
        param_dict = {(p.name, p.in_): p for p in path_params}
        for p in op_params:
            param_dict[(p.name, p.in_)] = p
        return list(param_dict.values())

    def _parse_request_body(self, request_body: dict[str, Any] | None) -> ParsedRequestBody | None:
        if not request_body or "$ref" in request_body:
            return None
            
        content = request_body.get("content", {})
        if not content:
            return None
            
        # We prefer application/json
        if "application/json" in content:
            schema = content["application/json"].get("schema")
            if schema:
                return ParsedRequestBody(
                    content_type="application/json",
                    schema=schema,
                    required=request_body.get("required", False),
                )
        
        # Fallback to the first available content type
        for content_type, details in content.items():
            schema = details.get("schema")
            if schema:
                return ParsedRequestBody(
                    content_type=content_type,
                    schema=schema,
                    required=request_body.get("required", False),
                )
                
        return None

    def _parse_responses(self, responses_dict: dict[str, Any]) -> list[ParsedResponse]:
        parsed = []
        for status_code, details in responses_dict.items():
            if "$ref" in details:
                continue
            
            content = details.get("content")
            parsed.append(
                ParsedResponse(
                    status_code=str(status_code),
                    description=details.get("description"),
                    content=content,
                )
            )
        return parsed
