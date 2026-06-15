import uuid
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from aitester.api.dependencies import get_db
from aitester.api.schemas.test_run import TestRunCreate, TestRunResponse, TestRunStatusResponse
from aitester.db.models.project import Project
from aitester.db.models.test_run import TestRun
from aitester.db.models.test_case import TestCase
from aitester.db.models.test_result import TestResult
from aitester.parser.parser import parse_spec
from aitester.generators.coordinator import TestGenerationCoordinator
from aitester.executor.runner import AsyncTestRunner
from aitester.core.config import settings

router = APIRouter()
logger = logging.getLogger("aitester.api")


async def execute_test_run(
    test_run_id: uuid.UUID,
    project_id: uuid.UUID,
    base_url: str,
    spec_path: str,
    types: list[str],
    enable_ai: bool,
):
    """
    Background task to generate and execute test cases.
    We need to spawn a new DB session since this runs outside the request lifecycle.
    """
    from aitester.db.session import AsyncSessionLocal

    try:
        # Parse spec
        spec = parse_spec(spec_path)
        
        # Generate test cases
        coordinator = TestGenerationCoordinator(enable_ai=enable_ai, types=types)
        test_cases = await coordinator.generate_async(spec, str(test_run_id))
        
        if not test_cases:
            async with AsyncSessionLocal() as db:
                run = await db.get(TestRun, test_run_id)
                if run:
                    run.status = "COMPLETED"
                    await db.commit()
            return
            
        async with AsyncSessionLocal() as db:
            run = await db.get(TestRun, test_run_id)
            if run:
                run.status = "RUNNING"
                db.add_all(test_cases)
                await db.commit()
            
            # Reattach to session for relationships if needed, but we can just use the objects
        
        # Execute test cases
        runner = AsyncTestRunner(base_url=base_url)
        results = await runner.execute_all(test_cases)
        
        async with AsyncSessionLocal() as db:
            run = await db.get(TestRun, test_run_id)
            if run:
                db.add_all(results)
                run.status = "COMPLETED"
                await db.commit()
                
    except Exception as e:
        logger.error(f"Test run {test_run_id} failed: {e}", exc_info=True)
        async with AsyncSessionLocal() as db:
            run = await db.get(TestRun, test_run_id)
            if run:
                run.status = "FAILED"
                await db.commit()


@router.post("/projects/{project_id}/runs", response_model=TestRunResponse, status_code=202)
async def create_test_run(
    project_id: uuid.UUID,
    run_create: TestRunCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    new_run = TestRun(
        project_id=project_id,
        base_url=run_create.base_url,
        status="PENDING",
    )
    db.add(new_run)
    await db.commit()
    await db.refresh(new_run)

    background_tasks.add_task(
        execute_test_run,
        test_run_id=new_run.id,
        project_id=project_id,
        base_url=run_create.base_url,
        spec_path=run_create.spec_path,
        types=run_create.types,
        enable_ai=run_create.enable_ai,
    )

    return new_run


@router.get("/runs/{run_id}", response_model=TestRunResponse)
async def get_test_run(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    run = await db.get(TestRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    return run


@router.get("/runs/{run_id}/status", response_model=TestRunStatusResponse)
async def get_test_run_status(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    run = await db.get(TestRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
        
    result = await db.execute(select(TestResult).where(TestResult.test_run_id == run_id))
    results = result.scalars().all()
    
    return TestRunStatusResponse(
        status=run.status,
        completed_cases=len(results),
        # total_cases might be hard to calculate without counting TestCases, so we'll leave it as None for now
    )
