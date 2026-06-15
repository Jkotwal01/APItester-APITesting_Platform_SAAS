import asyncio
from typing import Any

from aitester.db.models.test_case import TestCase
from aitester.parser.models import ParsedSpec
from aitester.generators.functional import FunctionalGenerator
from aitester.generators.edge import EdgeCaseGenerator
from aitester.security.generator import SecurityGenerator
from aitester.generators.ai_logic import AILogicGenerator


class TestGenerationCoordinator:
    """
    Coordinates all test generators to produce a unified suite of test cases.
    """

    def __init__(self, enable_ai: bool = False, types: list[str] | None = None):
        self.enable_ai = enable_ai
        self.types = types or ["functional", "edge", "security"]

    async def generate_async(self, spec: ParsedSpec, test_run_id: str) -> list[TestCase]:
        """
        Generates all requested test cases for the given spec asynchronously.
        """
        all_tests = []
        ai_tasks = []

        for endpoint in spec.endpoints:
            # Functional Tests
            if "functional" in self.types:
                gen = FunctionalGenerator(endpoint, test_run_id)
                all_tests.extend(gen.generate())

            # Edge Case Tests
            if "edge" in self.types:
                gen = EdgeCaseGenerator(endpoint, test_run_id)
                all_tests.extend(gen.generate())

            # Security Tests
            if "security" in self.types:
                gen = SecurityGenerator(endpoint, test_run_id)
                all_tests.extend(gen.generate())

            # AI Logic Tests
            if self.enable_ai and "ai" in self.types:
                gen = AILogicGenerator(endpoint, test_run_id)
                # We append the coroutine to a list to run them concurrently
                ai_tasks.append(gen.generate_async())

        # Gather all AI generation tasks concurrently if any
        if ai_tasks:
            ai_results = await asyncio.gather(*ai_tasks, return_exceptions=True)
            for res in ai_results:
                if isinstance(res, list):
                    all_tests.extend(res)
                elif isinstance(res, Exception):
                    import logging
                    logging.getLogger("aitester.generators").error(f"AI Generator failed: {res}")

        return all_tests

    def generate(self, spec: ParsedSpec, test_run_id: str) -> list[TestCase]:
        """
        Synchronous wrapper for test generation.
        Will use an existing event loop or create a new one.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # We are inside an async context (e.g. FastAPI), cannot use asyncio.run
            raise RuntimeError("Called synchronous generate() from an async context. Use generate_async().")
        else:
            return asyncio.run(self.generate_async(spec, test_run_id))
