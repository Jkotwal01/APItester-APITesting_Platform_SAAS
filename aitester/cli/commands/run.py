import asyncio
import uuid
import typer
from rich.console import Console
from rich.progress import track

from aitester.parser.parser import parse_spec
from aitester.generators.coordinator import TestGenerationCoordinator
from aitester.executor.runner import AsyncTestRunner
from aitester.db.session import AsyncSessionLocal
from aitester.db.models.project import Project
from aitester.db.models.test_run import TestRun

console = Console()


async def execute_pipeline(spec_path: str, base_url: str, enable_ai: bool):
    try:
        # Parse spec
        with console.status("[bold blue]Parsing OpenAPI Spec..."):
            spec = parse_spec(spec_path)
        console.print(f"[green][OK][/green] Parsed spec: {spec.title} v{spec.version} ({len(spec.endpoints)} endpoints)")

        # Generate Tests
        with console.status("[bold blue]Generating test cases..."):
            coordinator = TestGenerationCoordinator(enable_ai=enable_ai)
            # Create a dummy run ID for CLI (or save to DB)
            test_run_id = str(uuid.uuid4())
            test_cases = await coordinator.generate_async(spec, test_run_id)
        
        console.print(f"[green][OK][/green] Generated {len(test_cases)} test cases.")

        if not test_cases:
            console.print("[yellow]No test cases generated.[/yellow]")
            return

        # Execute Tests
        console.print("[bold blue]Executing tests against target API...[/bold blue]")
        runner = AsyncTestRunner(base_url=base_url)
        
        # We don't use track for the async execution because it runs concurrently.
        # We just await it.
        with console.status("[bold blue]Running tests concurrently..."):
            results = await runner.execute_all(test_cases)
            
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        
        console.print("\n[bold]Execution Summary[/bold]")
        console.print(f"Total: {len(results)}")
        console.print(f"Passed: [green]{passed}[/green]")
        console.print(f"Failed: [red]{failed}[/red]")
        
        # Save to DB
        with console.status("[bold blue]Saving results to database..."):
            async with AsyncSessionLocal() as db:
                project = Project(name="CLI Project")
                db.add(project)
                await db.commit()
                await db.refresh(project)
                
                run = TestRun(
                    id=uuid.UUID(test_run_id),
                    project_id=project.id,
                    base_url=base_url,
                    status="COMPLETED"
                )
                db.add(run)
                db.add_all(test_cases)
                db.add_all(results)
                await db.commit()
                
        console.print(f"[green][OK][/green] Results saved! Project ID: {project.id}")

    except Exception as e:
        console.print(f"[bold red]Pipeline failed: {e}[/bold red]")


def run(
    spec: str = typer.Option(..., "--spec", help="Path or URL to OpenAPI spec"),
    base_url: str = typer.Option(..., "--base-url", help="Target API Base URL"),
    ai: bool = typer.Option(False, "--ai", help="Enable Gemini AI logic generation")
):
    """Run the complete AITester pipeline against an API."""
    asyncio.run(execute_pipeline(spec, base_url, ai))
