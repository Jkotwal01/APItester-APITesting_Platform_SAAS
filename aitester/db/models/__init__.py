"""
Export all models for Alembic to discover via Base.metadata
"""

from aitester.db.models.project import Project
from aitester.db.models.report import Report
from aitester.db.models.test_case import TestCase
from aitester.db.models.test_result import TestResult
from aitester.db.models.test_run import TestRun

__all__ = [
    "Project",
    "TestRun",
    "TestCase",
    "TestResult",
    "Report",
]
