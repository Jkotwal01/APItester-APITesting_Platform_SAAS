import copy

from aitester.db.models.test_case import TestCase
from aitester.generators.base import BaseGenerator
from aitester.generators.functional import FunctionalGenerator
from aitester.security.payloads.command_injection import COMMAND_INJECTION_PAYLOADS
from aitester.security.payloads.jwt_attacks import JWT_PAYLOADS
from aitester.security.payloads.path_traversal import PATH_TRAVERSAL_PAYLOADS
from aitester.security.payloads.sqli import SQLI_PAYLOADS
from aitester.security.payloads.xss import XSS_PAYLOADS


class SecurityGenerator(BaseGenerator):
    """
    Generates security-focused test cases (SQLi, XSS, etc.) based on the OpenAPI spec.
    """

    def generate(self) -> list[TestCase]:
        test_cases = []

        # Get a baseline happy-path request to mutate
        functional_gen = FunctionalGenerator(endpoint=self.endpoint, test_run_id=self.test_run_id)
        baseline_tests = functional_gen.generate()
        if not baseline_tests:
            return []

        baseline = baseline_tests[0]

        # Apply payloads to query parameters
        if baseline.query_params:
            for param_name in baseline.query_params:
                test_cases.extend(
                    self._inject_payloads_into_query(
                        baseline, param_name, "SECURITY_SQLI", SQLI_PAYLOADS
                    )
                )
                test_cases.extend(
                    self._inject_payloads_into_query(
                        baseline, param_name, "SECURITY_XSS", XSS_PAYLOADS
                    )
                )
                test_cases.extend(
                    self._inject_payloads_into_query(
                        baseline, param_name, "SECURITY_PATH_TRAVERSAL", PATH_TRAVERSAL_PAYLOADS
                    )
                )
                test_cases.extend(
                    self._inject_payloads_into_query(
                        baseline,
                        param_name,
                        "SECURITY_COMMAND_INJECTION",
                        COMMAND_INJECTION_PAYLOADS,
                    )
                )

        # Apply payloads to JSON body fields (string fields only)
        if baseline.body:
            for field_name, value in baseline.body.items():
                if isinstance(value, str):
                    test_cases.extend(
                        self._inject_payloads_into_body(
                            baseline, field_name, "SECURITY_SQLI", SQLI_PAYLOADS
                        )
                    )
                    test_cases.extend(
                        self._inject_payloads_into_body(
                            baseline, field_name, "SECURITY_XSS", XSS_PAYLOADS
                        )
                    )
                    test_cases.extend(
                        self._inject_payloads_into_body(
                            baseline, field_name, "SECURITY_PATH_TRAVERSAL", PATH_TRAVERSAL_PAYLOADS
                        )
                    )
                    test_cases.extend(
                        self._inject_payloads_into_body(
                            baseline,
                            field_name,
                            "SECURITY_COMMAND_INJECTION",
                            COMMAND_INJECTION_PAYLOADS,
                        )
                    )

        # Apply JWT payloads if Authorization header exists or we force it
        # For MVP, we will inject a fake auth header to test for blind JWT acceptance
        for jwt in JWT_PAYLOADS:
            mutated_headers = copy.deepcopy(baseline.headers) or {}
            mutated_headers["Authorization"] = f"Bearer {jwt}"
            tc = self._create_test_case(
                category="SECURITY_JWT",
                expected_status=401,  # We expect unauthorized
                headers=mutated_headers,
                query_params=baseline.query_params,
                body=baseline.body,
            )
            test_cases.append(tc)

        return test_cases

    def _inject_payloads_into_query(
        self, baseline: TestCase, param_name: str, category: str, payloads: list[str]
    ) -> list[TestCase]:
        cases = []
        for payload in payloads:
            mutated_query = copy.deepcopy(baseline.query_params)
            if mutated_query:
                mutated_query[param_name] = payload
            tc = self._create_test_case(
                category=category,
                expected_status=400,  # Security tests generally expect 4xx
                headers=baseline.headers,
                query_params=mutated_query,
                body=baseline.body,
            )
            cases.append(tc)
        return cases

    def _inject_payloads_into_body(
        self, baseline: TestCase, field_name: str, category: str, payloads: list[str]
    ) -> list[TestCase]:
        cases = []
        for payload in payloads:
            mutated_body = copy.deepcopy(baseline.body)
            if mutated_body:
                mutated_body[field_name] = payload
            tc = self._create_test_case(
                category=category,
                expected_status=400,
                headers=baseline.headers,
                query_params=baseline.query_params,
                body=mutated_body,
            )
            cases.append(tc)
        return cases
