import asyncio
import time

from aitester.core.config import settings
from aitester.core.exceptions import HTTPClientError
from aitester.db.models.test_case import TestCase
from aitester.db.models.test_result import TestResult
from aitester.executor.http_client import ExecutorHTTPClient
from aitester.security.detector import SecurityDetector


class AsyncTestRunner:
    """
    Executes a batch of test cases concurrently against a target API.
    """

    def __init__(self, base_url: str):
        self.client = ExecutorHTTPClient(base_url)
        # Limit concurrency to avoid overloading the target or the local machine
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_TESTS)

    async def execute_all(self, test_cases: list[TestCase]) -> list[TestResult]:
        """
        Runs all provided test cases concurrently, up to MAX_CONCURRENT_TESTS at a time.
        """
        tasks = [self.execute_single(tc) for tc in test_cases]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out any unexpected exceptions from gather itself, though execute_single handles most
        valid_results = []
        for res in results:
            if isinstance(res, TestResult):
                valid_results.append(res)
            elif isinstance(res, Exception):
                # This happens if execute_single itself crashes unexpectedly
                import logging

                logging.getLogger("aitester.executor").error(f"Unexpected runner error: {res}")

        return valid_results

    async def execute_single(self, test_case: TestCase) -> TestResult:
        """
        Executes a single test case within the bounds of the concurrency semaphore.
        """
        async with self.semaphore:
            start_time = time.monotonic()

            try:
                response = await self.client.request(
                    method=test_case.method,
                    path=test_case.endpoint,
                    headers=test_case.headers,
                    query_params=test_case.query_params,
                    body=test_case.body,
                )

                execution_time = time.monotonic() - start_time
                status_code = response.status_code
                response_text = response.text
                response_headers = dict(response.headers)

                # Determine pass/fail based on status code
                passed = status_code == test_case.expected_status_code

                # If it's a security test, run it through the security detector
                if test_case.category.startswith("SECURITY_"):
                    # For security tests, if the detector says it's vulnerable, it FAILED the test (from our perspective, finding a vuln means the API failed to block it).
                    # Wait, if we WANT to find vulnerabilities, the platform detects them.
                    # Usually, passed = False means we found a vulnerability or an error.
                    # We will mark it as failed if it IS vulnerable.
                    is_vuln = SecurityDetector.is_vulnerable(
                        test_case, status_code, response_text, response_headers
                    )
                    if is_vuln:
                        passed = False
                        response_text = f"[VULNERABILITY DETECTED]\n{response_text}"

                return TestResult(
                    test_run_id=test_case.test_run_id,
                    test_case_id=test_case.id,
                    actual_status_code=status_code,
                    latency_ms=execution_time * 1000.0,
                    actual_body=response_text,
                    passed=passed,
                    ai_failure_analysis=None,
                )

            except HTTPClientError as e:
                execution_time = time.monotonic() - start_time
                return TestResult(
                    test_run_id=test_case.test_run_id,
                    test_case_id=test_case.id,
                    actual_status_code=0,  # 0 means network error
                    latency_ms=execution_time * 1000.0,
                    actual_body=str(e),
                    passed=False,
                    ai_failure_analysis={"error": "network_error"},
                )
            except Exception as e:
                execution_time = time.monotonic() - start_time
                return TestResult(
                    test_run_id=test_case.test_run_id,
                    test_case_id=test_case.id,
                    actual_status_code=0,
                    latency_ms=execution_time * 1000.0,
                    actual_body=str(e),
                    passed=False,
                    ai_failure_analysis={"error": "unhandled_exception"},
                )
