import typer
from rich.console import Console
from rich.table import Table

from aitester.parser.parser import parse_spec

console = Console()

def analyze(spec: str = typer.Argument(..., help="Path or URL to OpenAPI spec")):
    """Parse and display a summary of the OpenAPI specification."""
    with console.status("[bold green]Loading spec..."):
        parsed = parse_spec(spec)
        
    table = Table(title=f"{parsed.title} v{parsed.version}")
    table.add_column("Method", style="cyan")
    table.add_column("Path", style="white")
    table.add_column("Operation ID", style="dim")
    
    for ep in parsed.endpoints:
        table.add_row(ep.method, ep.path, str(ep.operation_id))
        
    console.print(table)
    console.print(f"\n[green][OK][/green] {len(parsed.endpoints)} endpoints found")
