"""
Stage 04 Database Models Tests.

Verifies table creation and SQLAlchemy relationships.
"""

import pytest

# Fixture to provide an async session for these tests
@pytest.fixture
async def db_session():
    from aitester.db.session import AsyncSessionLocal
    from aitester.db.base import Base
    from aitester.db.session import engine

    # Note: tests in this suite run against the real dev database
    # (aitester) which is fine for local dev gate checks.
    # In a real CI, we'd use a separate test DB.
    async with engine.begin() as conn:
        # For tests, we don't drop tables, we rely on rollbacks
        # but just to ensure tables exist:
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()
    await engine.dispose()


class TestDatabaseModels:
    @pytest.mark.asyncio
    async def test_create_project_and_test_run(self, db_session):
        """Test creating a Project and related TestRun."""
        from aitester.db.models import Project, TestRun

        # Create project
        project = Project(name="Test API", description="API for testing")
        db_session.add(project)
        await db_session.flush()

        # Create related test run
        run = TestRun(project_id=project.id, base_url="http://localhost:8000")
        db_session.add(run)
        await db_session.flush()

        assert project.id is not None
        assert run.id is not None
        assert run.project_id == project.id
        assert run.status == "PENDING"
        assert run.created_at is not None

    @pytest.mark.asyncio
    async def test_create_full_hierarchy(self, db_session):
        """Test creating Project -> TestRun -> TestCase -> TestResult."""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from aitester.db.models import Project, TestCase, TestResult, TestRun

        project = Project(name="Hierarchy Test", openapi_spec={"openapi": "3.0.0"})
        db_session.add(project)
        await db_session.flush()

        run = TestRun(project_id=project.id, base_url="http://api.com")
        db_session.add(run)
        await db_session.flush()

        tc = TestCase(
            test_run_id=run.id,
            category="FUNCTIONAL",
            endpoint="/users",
            method="GET",
            expected_status_code=200,
        )
        db_session.add(tc)
        await db_session.flush()

        result = TestResult(
            test_run_id=run.id,
            test_case_id=tc.id,
            passed=True,
            actual_status_code=200,
            latency_ms=15.5,
        )
        db_session.add(result)
        await db_session.flush()

        # Fetch with relationships
        stmt = (
            select(Project)
            .where(Project.id == project.id)
            .options(
                selectinload(Project.test_runs)
                .selectinload(TestRun.test_cases)
                .selectinload(TestCase.test_results)
            )
        )
        res = await db_session.execute(stmt)
        fetched_project = res.scalar_one()

        assert len(fetched_project.test_runs) == 1
        fetched_run = fetched_project.test_runs[0]
        assert len(fetched_run.test_cases) == 1
        fetched_tc = fetched_run.test_cases[0]
        assert len(fetched_tc.test_results) == 1
        assert fetched_tc.test_results[0].passed is True

    @pytest.mark.asyncio
    async def test_report_model(self, db_session):
        """Test creating a Report attached to a TestRun."""
        from aitester.db.models import Project, Report, TestRun

        project = Project(name="Report API")
        db_session.add(project)
        await db_session.flush()

        run = TestRun(project_id=project.id, base_url="http://test.com")
        db_session.add(run)
        await db_session.flush()

        report = Report(
            test_run_id=run.id,
            total_tests=10,
            passed_tests=8,
            failed_tests=2,
            security_score=95.5,
            ai_executive_summary={"summary": "Looks good", "risk_level": "LOW"}
        )
        db_session.add(report)
        await db_session.flush()

        assert report.id is not None
        assert report.security_score == 95.5
        assert report.ai_executive_summary["risk_level"] == "LOW"
