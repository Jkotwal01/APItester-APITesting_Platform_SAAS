import typer

from aitester.cli.commands import analyze, run

app = typer.Typer(
    name="aitester",
    help="AI-Powered Universal API Testing Platform",
    add_completion=False,
)

app.command("analyze")(analyze.analyze)
app.command("run")(run.run)

def app_runner():
    app()

if __name__ == "__main__":
    app_runner()
